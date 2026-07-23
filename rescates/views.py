from django.contrib import messages
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from alertas.models import Alert
from usuarios.decorators import role_required

from .forms import AssignmentStatusForm, GeneralVictimForm, RescueAssignmentForm, VictimForm
from .models import AssignmentHistory, RescueAssignment, RescueTeam, Victim


OPERATIONS_ROLES = ("operator", "coordinator", "administrator")


def _set_victim_location(victim, form):
    latitude = form.cleaned_data.get("latitude")
    longitude = form.cleaned_data.get("longitude")
    if latitude is not None and longitude is not None:
        victim.location = Point(float(longitude), float(latitude), srid=4326)


@role_required(*OPERATIONS_ROLES)
def create_assignment(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    if request.method == "POST":
        form = RescueAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.alert = alert
            assignment.assigned_by = request.user
            assignment.save()
            assignment.team.operational_status = RescueTeam.OperationalStatus.ASSIGNED
            assignment.team.save(update_fields=["operational_status"])
            alert.status = Alert.Status.ASSIGNED
            alert.save(update_fields=["status", "last_updated"])
            messages.success(request, "Equipo asignado correctamente.")
            return redirect("alertas:operations_detail", pk=alert.pk)
    else:
        form = RescueAssignmentForm()
    return render(request, "rescates/assignment_form.html", {"form": form, "alert": alert})


@require_POST
@role_required(*OPERATIONS_ROLES)
def update_assignment(request, pk):
    assignment = get_object_or_404(RescueAssignment, pk=pk)
    old_status = assignment.status
    form = AssignmentStatusForm(request.POST, instance=assignment)
    if form.is_valid():
        assignment.status = form.cleaned_data["status"]
        assignment.notes = form.cleaned_data["notes"]
        assignment.outcome = form.cleaned_data["outcome"]
        assignment.save(update_fields=["status", "notes", "outcome"])
        if old_status != assignment.status:
            AssignmentHistory.objects.create(
                assignment=assignment, changed_by=request.user,
                old_status=old_status, new_status=assignment.status,
                notes=assignment.notes,
            )
        messages.success(request, "Asignacion actualizada.")
    return redirect("alertas:operations_detail", pk=assignment.alert_id)


@role_required(*OPERATIONS_ROLES)
def create_victim(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    if request.method == "POST":
        form = VictimForm(request.POST)
        if form.is_valid():
            victim = form.save(commit=False)
            victim.alert = alert
            _set_victim_location(victim, form)
            victim.save()
            messages.success(request, "Victima registrada de forma protegida.")
            return redirect("alertas:operations_detail", pk=alert.pk)
    else:
        form = VictimForm()
    return render(request, "rescates/victim_form.html", {"form": form, "alert": alert})


@role_required(*OPERATIONS_ROLES)
def create_victim_general(request):
    if request.method == "POST":
        form = GeneralVictimForm(request.POST)
        if form.is_valid():
            victim = form.save(commit=False)
            victim.alert = form.cleaned_data["alert"]
            _set_victim_location(victim, form)
            victim.save()
            messages.success(request, "Victima registrada de forma protegida.")
            return redirect("alertas:operations_detail", pk=victim.alert_id) if victim.alert_id else redirect("mapas:operations_map")
    else:
        form = GeneralVictimForm()
    return render(request, "rescates/victim_form.html", {"form": form, "alert": None})
