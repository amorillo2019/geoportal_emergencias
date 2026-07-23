import json
from datetime import datetime

from django.contrib.gis.db.models.functions import AsGeoJSON
from django.contrib.gis.db.models.functions import Distance
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.core.serializers import serialize
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from alertas.models import Alert
from infraestructura.models import (
    AffectedBuilding, AdministrativeSector, BlockedRoadSegment,
    EmergencyZone, Hospital, Road, Shelter,
)
from rescates.models import RescueAssignment, RescueTeam
from rescates.models import Victim

from .permissions import OperationsMapPermission
from .spatial_queries import (
    alerts_in_emergency_zone, alerts_in_sector, alerts_within,
    available_teams_within, blocked_roads_near, nearest_hospital,
    nearest_shelter, point_from_coordinates, emergency_zone_for_point,
)


def _filtered_alerts(request):
    queryset = Alert.objects.all()
    valid_filters = {
        "status": {value for value, _ in Alert.Status.choices},
        "priority": {value for value, _ in Alert.Priority.choices},
        "emergency_type": {value for value, _ in Alert.EmergencyType.choices},
    }
    for field, valid_values in valid_filters.items():
        value = request.GET.get(field)
        if value in valid_values:
            queryset = queryset.filter(**{field: value})
    for param, lookup in (("date_from", "created_at__date__gte"), ("date_to", "created_at__date__lte")):
        value = request.GET.get(param)
        if value:
            try:
                queryset = queryset.filter(**{lookup: datetime.strptime(value, "%Y-%m-%d").date()})
            except ValueError:
                pass
    zone_id = request.GET.get("zone_id")
    if zone_id:
        try:
            zone = EmergencyZone.objects.get(pk=int(zone_id), is_active=True)
            queryset = queryset.filter(point__within=zone.geometry)
        except (ValueError, EmergencyZone.DoesNotExist):
            queryset = queryset.none()
    return queryset


def _feature(alert, geometry):
    return {
        "type": "Feature",
        "id": alert["id"],
        "geometry": json.loads(geometry),
        "properties": {
            "tracking_code": alert["public_tracking_code"],
            "emergency_type": alert["emergency_type"],
            "emergency_type_label": alert["emergency_type_label"],
            "priority": alert["priority"],
            "priority_label": alert["priority_label"],
            "status": alert["status"],
            "status_label": alert["status_label"],
            "created_at": alert["created_at"].isoformat(),
            "address_reference": alert["address_reference"],
            "description": alert["description"],
        },
    }


@api_view(["GET"])
@permission_classes([OperationsMapPermission])
def alerts_geojson(request):
    queryset = _filtered_alerts(request).annotate(geometry_json=AsGeoJSON("point", precision=6)).values(
        "id", "public_tracking_code", "emergency_type", "priority", "status",
        "created_at", "address_reference", "description", "geometry_json",
    )
    features = []
    for alert in queryset:
        alert["emergency_type_label"] = dict(Alert.EmergencyType.choices).get(alert["emergency_type"], "")
        alert["priority_label"] = dict(Alert.Priority.choices).get(alert["priority"], "")
        alert["status_label"] = dict(Alert.Status.choices).get(alert["status"], "")
        features.append(_feature(alert, alert.pop("geometry_json")))
    return Response({"type": "FeatureCollection", "features": features})


@api_view(["GET"])
@permission_classes([OperationsMapPermission])
def resource_layer_geojson(request):
    if request.GET.get("layer") == "victims":
        features = []
        for victim in Victim.objects.select_related("alert", "transfer_hospital", "transfer_shelter"):
            destination = victim.transfer_hospital or victim.transfer_shelter
            point = destination.point if destination else victim.location or (victim.alert.point if victim.alert else None)
            if point is None:
                continue
            destination_type = "Hospital" if victim.transfer_hospital else "Refugio" if victim.transfer_shelter else "Ubicacion registrada" if victim.location else "Ubicacion del reporte"
            destination_name = destination.name if destination else "Sin destino asignado"
            features.append({
                "type": "Feature",
                "id": victim.pk,
                "geometry": json.loads(point.geojson),
                "properties": {
                    "rescue_status": victim.rescue_status,
                    "rescue_status_label": victim.get_rescue_status_display(),
                    "destination_type": destination_type,
                    "destination_name": destination_name,
                },
            })
        return Response({"type": "FeatureCollection", "features": features})
    layers = {
        "hospitals": (Hospital, "point", ["name", "hospital_type", "address", "is_operational", "available_capacity"]),
        "shelters": (Shelter, "point", ["name", "address", "is_operational", "total_capacity", "registered_people"]),
        "teams": (RescueTeam, "current_location", ["name", "code", "institution", "operational_status", "specialty"]),
        "roads": (Road, "geometry", ["name", "is_open"]),
        "blocked_roads": (BlockedRoadSegment, "geometry", ["road_name", "reason", "is_active"]),
        "buildings": (AffectedBuilding, "geometry", ["reference", "damage_level"]),
        "emergency_zones": (EmergencyZone, "geometry", ["name", "level", "is_active"]),
        "sectors": (AdministrativeSector, "geometry", ["name", "sector_type"]),
    }
    layer_name = request.GET.get("layer")
    if layer_name not in layers:
        return Response({"detail": "Capa no valida."}, status=status.HTTP_400_BAD_REQUEST)
    model, geometry_field, fields = layers[layer_name]
    queryset = model.objects.all()
    if layer_name == "hospitals":
        queryset = queryset.filter(is_operational=True)
    elif layer_name == "shelters":
        queryset = queryset.filter(is_operational=True)
    elif layer_name == "blocked_roads":
        queryset = queryset.filter(is_active=True)
    elif layer_name == "emergency_zones":
        queryset = queryset.filter(is_active=True)
    return Response(json.loads(serialize("geojson", queryset, geometry_field=geometry_field, fields=fields)))


def _alert_result(alert):
    return {"tracking_code": alert.public_tracking_code, "status": alert.status, "priority": alert.priority, "latitude": float(alert.latitude), "longitude": float(alert.longitude)}


@api_view(["GET"])
@permission_classes([OperationsMapPermission])
def nearby_resources(request):
    try:
        point = point_from_coordinates(request.GET["latitude"], request.GET["longitude"])
        radius_km = float(request.GET.get("radius_km", 5))
        if radius_km <= 0 or radius_km > 100:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        return Response({"detail": "Indique coordenadas validas y un radio entre 0 y 100 km."}, status=status.HTTP_400_BAD_REQUEST)
    resource = request.GET.get("resource", "hospitals")
    if resource == "hospitals":
        queryset = [nearest_hospital(point)]
    elif resource == "shelters":
        queryset = [nearest_shelter(point)]
    elif resource == "teams":
        queryset = list(available_teams_within(point, radius_km))
    elif resource == "blocked_roads":
        queryset = list(blocked_roads_near(point, radius_km))
    else:
        return Response({"detail": "Recurso no valido."}, status=status.HTTP_400_BAD_REQUEST)
    queryset = [item for item in queryset if item is not None]
    return Response({"resource": resource, "results": [{"id": item.pk, "name": getattr(item, "name", getattr(item, "road_name", "")), "distance_m": round(item.distance.m, 2)} for item in queryset]})


@api_view(["GET"])
@permission_classes([OperationsMapPermission])
def nearby_alerts(request):
    try:
        point = point_from_coordinates(request.GET["latitude"], request.GET["longitude"])
        radius_km = float(request.GET.get("radius_km", 5))
        results = alerts_within(point, radius_km)
    except (KeyError, TypeError, ValueError):
        return Response({"detail": "Indique coordenadas validas."}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"results": [{**_alert_result(alert), "distance_m": round(alert.distance.m, 2)} for alert in results]})


@api_view(["GET"])
@permission_classes([OperationsMapPermission])
def alerts_in_zone(request):
    zone_type = request.GET.get("zone_type", "emergency")
    try:
        zone_id = int(request.GET["zone_id"])
        results = alerts_in_emergency_zone(zone_id) if zone_type == "emergency" else alerts_in_sector(zone_id)
    except (KeyError, TypeError, ValueError, EmergencyZone.DoesNotExist, AdministrativeSector.DoesNotExist):
        return Response({"detail": "Zona no valida."}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"results": [_alert_result(alert) for alert in results]})


@api_view(["GET"])
@permission_classes([OperationsMapPermission])
def operational_summary(request):
    return Response({
        "critical_alerts": Alert.objects.filter(priority=Alert.Priority.CRITICAL).count(),
        "pending_alerts": Alert.objects.exclude(status__in=[Alert.Status.CLOSED, Alert.Status.CANCELLED, Alert.Status.FALSE_ALERT]).count(),
        "available_teams": RescueTeam.objects.filter(operational_status=RescueTeam.OperationalStatus.AVAILABLE).count(),
        "operational_hospitals": Hospital.objects.filter(is_operational=True).count(),
        "shelters_with_capacity": Shelter.objects.filter(is_operational=True, total_capacity__gt=0).filter(registered_people__lt=F("total_capacity")).count(),
    })


@api_view(["GET"])
@permission_classes([OperationsMapPermission])
def alert_operational_detail(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    hospital = nearest_hospital(alert.point)
    shelter = nearest_shelter(alert.point)
    zone = emergency_zone_for_point(alert.point)
    assignment = RescueAssignment.objects.filter(alert=alert).select_related("team").order_by("-assigned_at").first()

    def resource_data(resource):
        if not resource:
            return None
        distance = getattr(resource, "distance", None)
        return {"name": resource.name, "distance_m": round(distance.m, 2) if distance else None}

    return Response({
        "id": alert.pk,
        "tracking_code": alert.public_tracking_code,
        "emergency_type": alert.get_emergency_type_display(),
        "priority": alert.get_priority_display(),
        "status": alert.get_status_display(),
        "created_at": alert.created_at.isoformat(),
        "assigned_team": {"code": assignment.team.code, "name": assignment.team.name, "status": assignment.get_status_display()} if assignment else None,
        "nearest_hospital": resource_data(hospital),
        "nearest_shelter": resource_data(shelter),
        "emergency_zone": zone.name if zone else None,
    })
