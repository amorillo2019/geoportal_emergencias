from django.contrib.gis.geos import LineString, MultiPolygon, Point, Polygon
from django.core.management.base import BaseCommand

from alertas.models import Alert
from infraestructura.models import (
    AffectedBuilding, AdministrativeSector, BlockedRoadSegment,
    EmergencyZone, Hospital, Road, Shelter,
)
from rescates.models import RescueTeam
from usuarios.models import User


class Command(BaseCommand):
    help = "Carga datos ficticios e idempotentes alrededor de El Empalme."

    def handle(self, *args, **options):
        center_latitude = -1.0427954
        center_longitude = -79.6386715
        operator = User.objects.filter(role=User.Role.OPERATOR).first()

        Alert.objects.update_or_create(
            public_tracking_code="DEMO-ALERTA-01",
            defaults={
                "person_name": "Persona demo 1",
                "phone": "",
                "emergency_type": Alert.EmergencyType.TRAPPED_PERSON,
                "description": "Datos ficticios para demostracion del mapa.",
                "latitude": center_latitude + 0.002,
                "longitude": center_longitude - 0.002,
                "priority": Alert.Priority.CRITICAL,
                "status": Alert.Status.RECEIVED,
                "estimated_affected_people": 2,
                "injured_people": 1,
                "building_condition": Alert.BuildingCondition.DAMAGED,
                "created_by": operator,
            },
        )
        Alert.objects.update_or_create(
            public_tracking_code="DEMO-ALERTA-02",
            defaults={
                "person_name": "Persona demo 2",
                "phone": "",
                "emergency_type": Alert.EmergencyType.INJURED_PERSON,
                "description": "Alerta ficticia de prioridad alta.",
                "latitude": center_latitude - 0.002,
                "longitude": center_longitude + 0.003,
                "priority": Alert.Priority.HIGH,
                "status": Alert.Status.VERIFIED,
                "estimated_affected_people": 1,
                "injured_people": 1,
                "created_by": operator,
            },
        )
        Alert.objects.update_or_create(
            public_tracking_code="DEMO-ALERTA-03",
            defaults={
                "person_name": "Persona demo 3",
                "phone": "",
                "emergency_type": Alert.EmergencyType.BLOCKED_ROAD,
                "description": "Via bloqueada ficticia para demostracion.",
                "latitude": center_latitude + 0.004,
                "longitude": center_longitude + 0.004,
                "priority": Alert.Priority.MEDIUM,
                "status": Alert.Status.ASSIGNED,
                "estimated_affected_people": 1,
                "created_by": operator,
            },
        )

        Hospital.objects.update_or_create(
            name="Hospital Demo El Empalme",
            defaults={
                "hospital_type": "General",
                "point": Point(center_longitude + 0.001, center_latitude + 0.001, srid=4326),
                "address": "Zona urbana de El Empalme",
                "total_capacity": 100,
                "available_capacity": 35,
                "is_operational": True,
            },
        )
        Shelter.objects.update_or_create(
            name="Refugio Demo El Empalme",
            defaults={
                "point": Point(center_longitude - 0.003, center_latitude + 0.003, srid=4326),
                "address": "Zona urbana de El Empalme",
                "total_capacity": 200,
                "registered_people": 80,
                "is_operational": True,
            },
        )
        RescueTeam.objects.update_or_create(
            code="DEMO-EQ-01",
            defaults={
                "name": "Equipo Demo El Empalme",
                "institution": "Institucion demo",
                "current_location": Point(center_longitude + 0.002, center_latitude - 0.001, srid=4326),
                "operational_status": RescueTeam.OperationalStatus.AVAILABLE,
                "specialty": "Busqueda y rescate",
                "vehicle_available": True,
                "member_count": 5,
            },
        )

        zone_polygon = Polygon.from_bbox((center_longitude - 0.012, center_latitude - 0.012, center_longitude + 0.012, center_latitude + 0.012))
        EmergencyZone.objects.update_or_create(
            name="Zona Demo Centro Urbano",
            defaults={"geometry": MultiPolygon(zone_polygon, srid=4326), "level": "Alta", "is_active": True},
        )
        sector_polygon = Polygon.from_bbox((center_longitude - 0.02, center_latitude - 0.02, center_longitude + 0.02, center_latitude + 0.02))
        AdministrativeSector.objects.update_or_create(
            name="Sector Demo El Empalme",
            defaults={"geometry": MultiPolygon(sector_polygon, srid=4326), "sector_type": "Urbano"},
        )
        road_geometry = LineString(
            (center_longitude - 0.01, center_latitude - 0.005),
            (center_longitude + 0.01, center_latitude + 0.005),
            srid=4326,
        )
        Road.objects.update_or_create(
            name="Via Demo Principal",
            defaults={"geometry": road_geometry, "is_open": True},
        )
        BlockedRoadSegment.objects.update_or_create(
            road_name="Via Demo Bloqueada",
            defaults={
                "geometry": LineString(
                    (center_longitude - 0.006, center_latitude + 0.006),
                    (center_longitude + 0.006, center_latitude + 0.006),
                    srid=4326,
                ),
                "reason": "Obstruccion ficticia",
                "is_active": True,
            },
        )
        building_polygon = Polygon.from_bbox((center_longitude - 0.003, center_latitude - 0.003, center_longitude - 0.001, center_latitude - 0.001))
        AffectedBuilding.objects.update_or_create(
            reference="Edificacion Demo 01",
            defaults={"geometry": building_polygon, "damage_level": "Dano moderado"},
        )

        self.stdout.write(self.style.SUCCESS("Datos demo cargados alrededor de El Empalme."))
