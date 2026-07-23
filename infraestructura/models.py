from django.contrib.gis.db import models


class Hospital(models.Model):
    name = models.CharField("nombre", max_length=200)
    hospital_type = models.CharField("tipo", max_length=100, blank=True)
    point = models.PointField("ubicacion", srid=4326, spatial_index=True)
    address = models.CharField("direccion", max_length=300, blank=True)
    phone = models.CharField("telefono", max_length=30, blank=True)
    total_capacity = models.PositiveIntegerField("capacidad total", default=0)
    available_capacity = models.PositiveIntegerField("capacidad disponible", default=0)
    is_operational = models.BooleanField("operativo", default=True)
    notes = models.TextField("observaciones", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "hospital"
        verbose_name_plural = "hospitales"

    def __str__(self):
        return self.name


class Shelter(models.Model):
    name = models.CharField("nombre", max_length=200)
    point = models.PointField("ubicacion", srid=4326, spatial_index=True)
    address = models.CharField("direccion", max_length=300, blank=True)
    manager = models.CharField("responsable", max_length=200, blank=True)
    phone = models.CharField("telefono", max_length=30, blank=True)
    total_capacity = models.PositiveIntegerField("capacidad total", default=0)
    registered_people = models.PositiveIntegerField("personas registradas", default=0)
    is_operational = models.BooleanField("operativo", default=True)
    notes = models.TextField("observaciones", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "refugio"
        verbose_name_plural = "refugios"

    def __str__(self):
        return self.name


class Road(models.Model):
    name = models.CharField("nombre", max_length=200)
    geometry = models.LineStringField("geometria", srid=4326, spatial_index=True)
    is_open = models.BooleanField("abierta", default=True)
    notes = models.TextField("observaciones", blank=True)

    def __str__(self):
        return self.name


class BlockedRoadSegment(models.Model):
    road_name = models.CharField("via", max_length=200)
    geometry = models.LineStringField("geometria", srid=4326, spatial_index=True)
    reason = models.CharField("motivo", max_length=200, blank=True)
    is_active = models.BooleanField("bloqueo activo", default=True)

    def __str__(self):
        return self.road_name


class AffectedBuilding(models.Model):
    reference = models.CharField("referencia", max_length=200)
    geometry = models.PolygonField("geometria", srid=4326, spatial_index=True)
    damage_level = models.CharField("nivel de dano", max_length=100, blank=True)
    notes = models.TextField("observaciones", blank=True)

    def __str__(self):
        return self.reference


class EmergencyZone(models.Model):
    name = models.CharField("nombre", max_length=200)
    geometry = models.MultiPolygonField("geometria", srid=4326, spatial_index=True)
    level = models.CharField("nivel", max_length=50, blank=True)
    is_active = models.BooleanField("activa", default=True)
    notes = models.TextField("observaciones", blank=True)

    def __str__(self):
        return self.name


class AdministrativeSector(models.Model):
    name = models.CharField("nombre", max_length=200)
    geometry = models.MultiPolygonField("geometria", srid=4326, spatial_index=True)
    sector_type = models.CharField("tipo", max_length=100, blank=True)

    def __str__(self):
        return self.name
