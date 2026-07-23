from django.conf import settings
from django.contrib.gis.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from alertas.models import Alert
from infraestructura.models import Hospital, Shelter


class RescueTeam(models.Model):
    class OperationalStatus(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        ASSIGNED = "assigned", "Asignado"
        IN_OPERATION = "in_operation", "En operacion"
        OUT_OF_SERVICE = "out_of_service", "Fuera de servicio"

    name = models.CharField("nombre", max_length=200)
    code = models.CharField("codigo", max_length=50, unique=True)
    institution = models.CharField("institucion", max_length=200, blank=True)
    responsible = models.CharField("responsable", max_length=200, blank=True)
    phone = models.CharField("telefono", max_length=30, blank=True)
    member_count = models.PositiveIntegerField("integrantes", default=0)
    current_location = models.PointField("ubicacion actual", srid=4326, spatial_index=True)
    operational_status = models.CharField("estado operativo", max_length=50, choices=OperationalStatus.choices, default=OperationalStatus.AVAILABLE)
    specialty = models.CharField("capacidad o especialidad", max_length=150, blank=True)
    vehicle_available = models.BooleanField("vehiculo disponible", default=False)
    notes = models.TextField("observaciones", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "equipo de rescate"
        verbose_name_plural = "equipos de rescate"

    def __str__(self):
        return f"{self.code} - {self.name}"


class RescueAssignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Asignada"
        ACCEPTED = "accepted", "Aceptada"
        EN_ROUTE = "en_route", "En ruta"
        ON_SITE = "on_site", "En sitio"
        RESCUING = "rescuing", "En rescate"
        COMPLETED = "completed", "Completada"
        CANCELLED = "cancelled", "Cancelada"

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="rescue_assignments")
    team = models.ForeignKey(RescueTeam, on_delete=models.PROTECT, related_name="assignments")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="rescue_assignments_created")
    assigned_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSIGNED)
    notes = models.TextField("observaciones", blank=True)
    departure_at = models.DateTimeField(null=True, blank=True)
    arrival_at = models.DateTimeField(null=True, blank=True)
    outcome = models.TextField("resultado", blank=True)

    class Meta:
        ordering = ["-assigned_at"]
        verbose_name = "asignacion de rescate"
        verbose_name_plural = "asignaciones de rescate"

    def __str__(self):
        return f"{self.alert.public_tracking_code} - {self.team.code}"


class AssignmentHistory(models.Model):
    assignment = models.ForeignKey(RescueAssignment, on_delete=models.CASCADE, related_name="history")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Victim(models.Model):
    class RescueStatus(models.TextChoices):
        REPORTED = "reported", "Reportada"
        LOCATED = "located", "Localizada"
        IN_CARE = "in_care", "En atencion"
        RESCUED = "rescued", "Rescatada"
        TRANSFERRED = "transferred", "Trasladada"
        REUNITED = "reunited", "Reunificada"
        NOT_LOCATED = "not_located", "No localizada"
        DECEASED = "deceased", "Fallecida"

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, null=True, blank=True, related_name="victims")
    location = models.PointField("ubicacion de la victima", srid=4326, null=True, blank=True, spatial_index=True)
    first_names = models.CharField("nombres", max_length=150)
    last_names = models.CharField("apellidos", max_length=150, blank=True)
    identification_number = models.CharField("identificacion", max_length=30, blank=True)
    approximate_age = models.PositiveIntegerField("edad aproximada", null=True, blank=True, validators=[MinValueValidator(0)])
    sex = models.CharField("sexo", max_length=30, blank=True)
    phone = models.CharField("telefono", max_length=30, blank=True)
    health_status = models.CharField("estado de salud", max_length=100, blank=True)
    rescue_status = models.CharField(max_length=20, choices=RescueStatus.choices, default=RescueStatus.REPORTED)
    transfer_location = models.CharField("lugar de traslado", max_length=250, blank=True)
    transfer_hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name="transferred_victims")
    transfer_shelter = models.ForeignKey(Shelter, on_delete=models.SET_NULL, null=True, blank=True, related_name="sheltered_victims")
    safe_place = models.CharField("otro lugar seguro", max_length=250, blank=True)
    rescued_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField("observaciones", blank=True)
    photo_storage_path = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["last_names", "first_names"]
        verbose_name = "victima"
        verbose_name_plural = "victimas"

    def __str__(self):
        return f"{self.first_names} {self.last_names}".strip()
