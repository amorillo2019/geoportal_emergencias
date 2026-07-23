import secrets

from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import Point


def generate_tracking_code():
    return f"GE-{secrets.token_hex(6).upper()}"


class Alert(models.Model):
    class EmergencyType(models.TextChoices):
        TRAPPED_PERSON = "trapped_person", "Persona atrapada"
        INJURED_PERSON = "injured_person", "Persona herida"
        COLLAPSED_BUILDING = "collapsed_building", "Edificacion colapsada"
        FIRE = "fire", "Incendio"
        BLOCKED_ROAD = "blocked_road", "Via bloqueada"
        GAS_LEAK = "gas_leak", "Fuga de gas"
        ELECTRICAL_RISK = "electrical_risk", "Riesgo electrico"
        MISSING_PERSON = "missing_person", "Persona desaparecida"
        OTHER = "other", "Otra emergencia"

    class Priority(models.TextChoices):
        LOW = "low", "Baja"
        MEDIUM = "medium", "Media"
        HIGH = "high", "Alta"
        CRITICAL = "critical", "Critica"

    class Status(models.TextChoices):
        RECEIVED = "received", "Recibida"
        VERIFYING = "verifying", "En verificacion"
        VERIFIED = "verified", "Verificada"
        ASSIGNED = "assigned", "Asignada"
        IN_PROGRESS = "in_progress", "En atencion"
        RESCUED = "rescued", "Rescatada"
        TRANSFERRED = "transferred", "Trasladada"
        CLOSED = "closed", "Cerrada"
        FALSE_ALERT = "false_alert", "Falsa alerta"
        CANCELLED = "cancelled", "Cancelada"

    class BuildingCondition(models.TextChoices):
        UNKNOWN = "unknown", "No informado"
        STABLE = "stable", "Estable"
        DAMAGED = "damaged", "Danada"
        PARTIALLY_COLLAPSED = "partially_collapsed", "Colapso parcial"
        COLLAPSED = "collapsed", "Colapsada"

    public_tracking_code = models.CharField(
        max_length=15, unique=True, default=generate_tracking_code, editable=False
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    last_updated = models.DateTimeField(auto_now=True)
    person_name = models.CharField("nombre de la persona", max_length=200, blank=True)
    identification_number = models.CharField("identificacion", max_length=30, blank=True)
    phone = models.CharField("telefono", max_length=30, blank=True)
    alternative_phone = models.CharField("telefono alternativo", max_length=30, blank=True)
    email = models.EmailField("correo electronico", blank=True)
    point = models.PointField("ubicacion", srid=4326, spatial_index=True)
    latitude = models.DecimalField(
        "latitud", max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        "longitud", max_digits=9, decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    address_reference = models.CharField("direccion o referencia", max_length=300, blank=True)
    emergency_type = models.CharField(
        "tipo de emergencia", max_length=30, choices=EmergencyType.choices
    )
    description = models.TextField("descripcion", blank=True)
    estimated_affected_people = models.PositiveIntegerField("personas afectadas", default=1)
    injured_people = models.PositiveIntegerField("personas heridas", default=0)
    has_children = models.BooleanField("hay ninos", default=False)
    has_older_adults = models.BooleanField("hay adultos mayores", default=False)
    has_people_with_disabilities = models.BooleanField("hay personas con discapacidad", default=False)
    building_condition = models.CharField(
        "estado de la edificacion", max_length=30,
        choices=BuildingCondition.choices, default=BuildingCondition.UNKNOWN,
    )
    priority = models.CharField(
        "prioridad", max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.RECEIVED
    )
    audio_storage_path = models.CharField(max_length=500, blank=True)
    image_storage_path = models.CharField(max_length=500, blank=True)
    internal_notes = models.TextField("observaciones internas", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="created_alerts",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "alerta"
        verbose_name_plural = "alertas"
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estimated_affected_people__gte=1),
                name="alert_affected_people_positive",
            ),
        ]

    def __str__(self):
        return f"{self.public_tracking_code} - {self.get_emergency_type_display()}"

    def clean(self):
        super().clean()
        missing_coordinates = {}
        if self.latitude is None:
            missing_coordinates["latitude"] = _("La latitud es obligatoria.")
        if self.longitude is None:
            missing_coordinates["longitude"] = _("La longitud es obligatoria.")
        if missing_coordinates:
            raise ValidationError(missing_coordinates)
        if not (-90 <= self.latitude <= 90):
            raise ValidationError({"latitude": _("La latitud debe estar entre -90 y 90.")})
        if not (-180 <= self.longitude <= 180):
            raise ValidationError({"longitude": _("La longitud debe estar entre -180 y 180.")})

    def save(self, *args, **kwargs):
        self.point = Point(float(self.longitude), float(self.latitude), srid=4326)
        return super().save(*args, **kwargs)


class AlertHistory(models.Model):
    class ChangeType(models.TextChoices):
        STATUS = "status", "Cambio de estado"
        PRIORITY = "priority", "Cambio de prioridad"
        OBSERVATION = "observation", "Observacion interna"

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="alert_changes",
    )
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    old_value = models.CharField(max_length=100, blank=True)
    new_value = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "historial de alerta"
        verbose_name_plural = "historial de alertas"

    def __str__(self):
        return f"{self.alert.public_tracking_code} - {self.get_change_type_display()}"
