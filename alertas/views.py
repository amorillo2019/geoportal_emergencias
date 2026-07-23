from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from usuarios.decorators import role_required

from .forms import PublicAlertForm
from .operations_forms import AlertPriorityForm, AlertStatusForm, InternalNoteForm
from .models import Alert, AlertHistory
from infraestructura.models import EmergencyZone
from services.supabase_storage import StorageError, SupabaseStorage


def public_alert_create(request):
    if request.method == "POST" and _public_alert_rate_limited(request):
        return HttpResponse("Demasiadas alertas desde esta direccion. Intente mas tarde.", status=429)
    if request.method == "POST":
        form = PublicAlertForm(request.POST, request.FILES)
        if form.is_valid():
            if request.FILES and (not settings.SUPABASE_SERVICE_ROLE_KEY or not settings.SUPABASE_URL):
                form.add_error(None, "El almacenamiento de archivos no esta configurado.")
            else:
                return _save_public_alert(request, form)
    else:
        form = PublicAlertForm()
    return render(request, "alertas/public_create.html", {"form": form})


def _save_public_alert(request, form):
    alert = form.save(commit=False)
    if request.user.is_authenticated:
        alert.created_by = request.user
    alert.save()
    if not form.cleaned_data.get("audio") and not form.cleaned_data.get("image"):
        return redirect("alertas:confirmation", code=alert.public_tracking_code)
    try:
        storage = SupabaseStorage()
        if form.cleaned_data.get("audio"):
            alert.audio_storage_path = storage.upload(form.cleaned_data["audio"], f"alerts/{alert.public_tracking_code}", "audio")
        if form.cleaned_data.get("image"):
            alert.image_storage_path = storage.upload(form.cleaned_data["image"], f"alerts/{alert.public_tracking_code}", "image")
        if alert.audio_storage_path or alert.image_storage_path:
            alert.save(update_fields=["audio_storage_path", "image_storage_path", "last_updated"])
    except StorageError:
        form.add_error(None, "No fue posible almacenar los archivos. Intente nuevamente.")
        alert.delete()
        return render(request, "alertas/public_create.html", {"form": form}, status=503)
    return redirect("alertas:confirmation", code=alert.public_tracking_code)


def _public_alert_rate_limited(request):
    key = f"public-alert:{request.META.get('REMOTE_ADDR', 'unknown')}"
    count = cache.get(key, 0)
    if count >= settings.PUBLIC_ALERT_RATE_LIMIT:
        return True
    cache.set(key, count + 1, settings.PUBLIC_ALERT_RATE_WINDOW_SECONDS)
    return False


def alert_confirmation(request, code):
    alert = _get_public_alert(code)
    return render(request, "alertas/confirmation.html", {"alert": alert})


def alert_tracking(request, code):
    alert = _get_public_alert(code)
    return render(request, "alertas/tracking.html", {"alert": alert})


def _get_public_alert(code):
    try:
        return Alert.objects.get(public_tracking_code=code.upper())
    except Alert.DoesNotExist as exc:
        raise Http404("No se encontro la alerta.") from exc


OPERATIONS_ROLES = (
    "operator", "coordinator", "administrator",
)


@role_required(*OPERATIONS_ROLES)
def operations_dashboard(request):
    alerts = Alert.objects.select_related("created_by")
    filters = {
        "status": request.GET.get("status", ""),
        "priority": request.GET.get("priority", ""),
        "emergency_type": request.GET.get("emergency_type", ""),
        "zone_id": request.GET.get("zone_id", ""),
    }
    valid_values = {
        "status": {value for value, _ in Alert.Status.choices},
        "priority": {value for value, _ in Alert.Priority.choices},
        "emergency_type": {value for value, _ in Alert.EmergencyType.choices},
    }
    for field, value in filters.items():
        if field in valid_values and value in valid_values[field]:
            alerts = alerts.filter(**{field: value})
    if filters["zone_id"]:
        try:
            zone = EmergencyZone.objects.get(pk=int(filters["zone_id"]), is_active=True)
            alerts = alerts.filter(point__within=zone.geometry)
        except (ValueError, EmergencyZone.DoesNotExist):
            alerts = alerts.none()
    search = request.GET.get("q", "").strip()
    if search:
        alerts = alerts.filter(
            Q(public_tracking_code__icontains=search)
            | Q(person_name__icontains=search)
            | Q(phone__icontains=search)
        )
    if request.GET.get("date_from"):
        try:
            alerts = alerts.filter(created_at__date__gte=datetime.strptime(request.GET["date_from"], "%Y-%m-%d").date())
        except ValueError:
            pass
    if request.GET.get("date_to"):
        try:
            alerts = alerts.filter(created_at__date__lte=datetime.strptime(request.GET["date_to"], "%Y-%m-%d").date())
        except ValueError:
            pass
    priority_order = Case(
        When(priority=Alert.Priority.CRITICAL, then=Value(0)),
        When(priority=Alert.Priority.HIGH, then=Value(1)),
        When(priority=Alert.Priority.MEDIUM, then=Value(2)),
        When(priority=Alert.Priority.LOW, then=Value(3)),
        output_field=IntegerField(),
    )
    sort = request.GET.get("sort", "priority")
    sort_fields = {
        "date": "-created_at", "priority": "priority_order", "status": "status", "type": "emergency_type",
    }
    alerts = alerts.annotate(priority_order=priority_order).order_by(sort_fields.get(sort, "priority_order"), "-created_at")
    paginator = Paginator(alerts, int(request.GET.get("page_size", 10)) if request.GET.get("page_size", "10") in {"10", "25", "50"} else 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    today = timezone.localdate()
    context = {
        "alerts": page_obj,
        "page_obj": page_obj,
        "filters": filters,
        "search": search,
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
        "sort": sort,
        "page_size": paginator.per_page,
        "pagination_query": (lambda params: (params.pop("page", None), params.urlencode())[1])(request.GET.copy()),
        "zones": EmergencyZone.objects.filter(is_active=True).order_by("name"),
        "total_alerts": Alert.objects.count(),
        "today_alerts": Alert.objects.filter(created_at__date=today).count(),
        "pending_alerts": Alert.objects.exclude(status__in=[Alert.Status.CLOSED, Alert.Status.CANCELLED, Alert.Status.FALSE_ALERT]).count(),
        "in_attention_alerts": Alert.objects.filter(status=Alert.Status.IN_PROGRESS).count(),
        "resolved_alerts": Alert.objects.filter(status__in=[Alert.Status.RESCUED, Alert.Status.TRANSFERRED, Alert.Status.CLOSED]).count(),
        "status_counts": Alert.objects.values("status").annotate(total=Count("id")),
        "priority_counts": Alert.objects.values("priority").annotate(total=Count("id")),
        "alert_status_choices": Alert.Status.choices,
        "alert_priority_choices": Alert.Priority.choices,
        "alert_type_choices": Alert.EmergencyType.choices,
    }
    return render(request, "alertas/operations_dashboard.html", context)


@role_required(*OPERATIONS_ROLES)
def operations_detail(request, pk):
    alert = get_object_or_404(Alert.objects.select_related("created_by"), pk=pk)
    return render(request, "alertas/operations_detail.html", {
        "alert": alert,
        "status_form": AlertStatusForm(instance=alert),
        "priority_form": AlertPriorityForm(instance=alert),
        "note_form": InternalNoteForm(),
        "history": alert.history.select_related("changed_by"),
        "assignments": alert.rescue_assignments.select_related("team"),
        "victims": alert.victims.all(),
    })


@require_POST
@role_required(*OPERATIONS_ROLES)
def verify_alert(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if alert.status != Alert.Status.VERIFIED:
        old_status = alert.get_status_display()
        alert.status = Alert.Status.VERIFIED
        alert.save(update_fields=["status", "last_updated"])
        AlertHistory.objects.create(
            alert=alert, changed_by=request.user, change_type=AlertHistory.ChangeType.STATUS,
            old_value=old_status, new_value=alert.get_status_display(),
        )
        messages.success(request, "Alerta marcada como verificada.")
    return redirect("alertas:operations_detail", pk=alert.pk)


@require_POST
@role_required(*OPERATIONS_ROLES)
def update_alert_status(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    old_status_value = alert.status
    old_status_display = alert.get_status_display()
    form = AlertStatusForm(request.POST, instance=alert)
    if form.is_valid() and form.cleaned_data["status"] != old_status_value:
        alert.status = form.cleaned_data["status"]
        alert.save(update_fields=["status", "last_updated"])
        AlertHistory.objects.create(
            alert=alert, changed_by=request.user, change_type=AlertHistory.ChangeType.STATUS,
            old_value=old_status_display, new_value=alert.get_status_display(),
        )
        messages.success(request, "Estado actualizado.")
    return redirect("alertas:operations_detail", pk=alert.pk)


@require_POST
@role_required(*OPERATIONS_ROLES)
def update_alert_priority(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    old_priority_value = alert.priority
    old_priority_display = alert.get_priority_display()
    form = AlertPriorityForm(request.POST, instance=alert)
    if form.is_valid() and form.cleaned_data["priority"] != old_priority_value:
        alert.priority = form.cleaned_data["priority"]
        alert.save(update_fields=["priority", "last_updated"])
        AlertHistory.objects.create(
            alert=alert, changed_by=request.user, change_type=AlertHistory.ChangeType.PRIORITY,
            old_value=old_priority_display, new_value=alert.get_priority_display(),
        )
        messages.success(request, "Prioridad actualizada.")
    return redirect("alertas:operations_detail", pk=alert.pk)


@require_POST
@role_required(*OPERATIONS_ROLES)
def add_alert_note(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    form = InternalNoteForm(request.POST)
    if form.is_valid():
        note = form.cleaned_data["observation"]
        alert.internal_notes = f"{alert.internal_notes}\n{note}".strip()
        alert.save(update_fields=["internal_notes", "last_updated"])
        AlertHistory.objects.create(
            alert=alert, changed_by=request.user, change_type=AlertHistory.ChangeType.OBSERVATION,
            note=note,
        )
        messages.success(request, "Observacion interna agregada.")
    return redirect("alertas:operations_detail", pk=alert.pk)
