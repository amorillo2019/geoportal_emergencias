from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point

from alertas.models import Alert
from infraestructura.models import AdministrativeSector, BlockedRoadSegment, EmergencyZone, Hospital, Shelter
from rescates.models import RescueTeam


def point_from_coordinates(latitude, longitude):
    latitude = float(latitude)
    longitude = float(longitude)
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordenadas fuera de rango.")
    return Point(longitude, latitude, srid=4326)


def nearest_hospital(point):
    return Hospital.objects.filter(is_operational=True).annotate(distance=Distance("point", point)).order_by("distance").first()


def nearest_shelter(point):
    return Shelter.objects.filter(is_operational=True).annotate(distance=Distance("point", point)).order_by("distance").first()


def available_teams_within(point, radius_km):
    return RescueTeam.objects.filter(
        operational_status=RescueTeam.OperationalStatus.AVAILABLE,
        current_location__distance_lte=(point, D(km=radius_km)),
    ).annotate(distance=Distance("current_location", point)).order_by("distance")


def alerts_within(point, radius_km):
    return Alert.objects.filter(point__distance_lte=(point, D(km=radius_km))).annotate(distance=Distance("point", point)).order_by("distance")


def alerts_in_geometry(geometry):
    return Alert.objects.filter(point__within=geometry)


def alerts_in_emergency_zone(zone_id):
    zone = EmergencyZone.objects.get(pk=zone_id)
    return alerts_in_geometry(zone.geometry)


def alerts_in_sector(sector_id):
    sector = AdministrativeSector.objects.get(pk=sector_id)
    return alerts_in_geometry(sector.geometry)


def emergency_zone_for_point(point):
    return EmergencyZone.objects.filter(is_active=True, geometry__contains=point).first()


def blocked_roads_near(point, radius_km):
    return BlockedRoadSegment.objects.filter(
        is_active=True, geometry__distance_lte=(point, D(km=radius_km))
    ).annotate(distance=Distance("geometry", point)).order_by("distance")
