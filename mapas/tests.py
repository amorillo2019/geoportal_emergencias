from decimal import Decimal

from django.urls import reverse
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from rest_framework.test import APITestCase

from alertas.models import Alert
from infraestructura.models import EmergencyZone, Hospital
from rescates.models import RescueAssignment, RescueTeam
from rescates.models import Victim
from usuarios.models import User


class AlertGeoJSONTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = User.objects.create_user(
            "operator-map@example.com", "Strong-password-123", role=User.Role.OPERATOR
        )
        cls.citizen = User.objects.create_user(
            "citizen-map@example.com", "Strong-password-123", role=User.Role.CITIZEN
        )
        Alert.objects.create(
            emergency_type=Alert.EmergencyType.FIRE,
            priority=Alert.Priority.CRITICAL,
            status=Alert.Status.RECEIVED,
            latitude=Decimal("-0.180653"),
            longitude=Decimal("-78.467834"),
            description="Incendio de prueba",
        )
        Alert.objects.create(
            emergency_type=Alert.EmergencyType.BLOCKED_ROAD,
            priority=Alert.Priority.LOW,
            status=Alert.Status.CLOSED,
            latitude=Decimal("-0.200000"),
            longitude=Decimal("-78.480000"),
        )

    def test_operator_receives_geojson_without_sensitive_data(self):
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:alerts_geojson"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "FeatureCollection")
        self.assertEqual(len(response.data["features"]), 2)
        feature = response.data["features"][0]
        self.assertEqual(feature["geometry"]["type"], "Point")
        self.assertIn("tracking_code", feature["properties"])
        self.assertNotIn("phone", feature["properties"])
        self.assertNotIn("identification_number", feature["properties"])

    def test_filter_by_priority_is_applied_in_database(self):
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:alerts_geojson"), {"priority": "critical"})
        self.assertEqual(len(response.data["features"]), 1)
        self.assertEqual(response.data["features"][0]["properties"]["priority"], "critical")

    def test_citizen_cannot_access_operational_geojson(self):
        self.client.force_authenticate(self.citizen)
        response = self.client.get(reverse("mapas:alerts_geojson"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_cannot_access_operational_map(self):
        response = self.client.get(reverse("mapas:operations_map"))
        self.assertEqual(response.status_code, 302)

    def test_operator_can_render_integrated_map(self):
        self.client.force_login(self.operator)
        response = self.client.get(reverse("mapas:operations_map"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "map-layers-panel")
        self.assertContains(response, "Capas visibles")

    def test_operator_receives_resource_layer_geojson(self):
        Hospital.objects.create(name="Hospital de prueba", point=Point(-78.46, -0.18, srid=4326))
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:resource_layers_geojson"), {"layer": "hospitals"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["features"][0]["properties"]["name"], "Hospital de prueba")

    def test_invalid_resource_layer_is_rejected(self):
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:resource_layers_geojson"), {"layer": "unknown"})
        self.assertEqual(response.status_code, 400)

    def test_each_operational_layer_can_be_loaded(self):
        self.client.force_authenticate(self.operator)
        for layer in ("hospitals", "shelters", "teams", "roads", "blocked_roads", "buildings", "emergency_zones", "sectors"):
            with self.subTest(layer=layer):
                response = self.client.get(reverse("mapas:resource_layers_geojson"), {"layer": layer})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["type"], "FeatureCollection")

    def test_victim_layer_uses_destination_and_hides_sensitive_fields(self):
        hospital = Hospital.objects.create(name="Hospital víctima demo", point=Point(-78.46, -0.18, srid=4326))
        Victim.objects.create(alert=Alert.objects.first(), first_names="Persona privada", phone="0999999999", transfer_hospital=hospital)
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:resource_layers_geojson"), {"layer": "victims"})
        self.assertEqual(response.status_code, 200)
        feature = response.data["features"][0]
        self.assertEqual(feature["properties"]["destination_name"], "Hospital víctima demo")
        self.assertNotIn("first_names", feature["properties"])
        self.assertNotIn("phone", feature["properties"])

    def test_nearby_hospital_query_returns_distance(self):
        Hospital.objects.create(name="Hospital cercano", point=Point(-78.468, -0.181, srid=4326))
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:nearby_resources"), {"resource": "hospitals", "latitude": "-0.180653", "longitude": "-78.467834"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["name"], "Hospital cercano")
        self.assertGreaterEqual(response.data["results"][0]["distance_m"], 0)

    def test_alerts_inside_emergency_zone_are_filtered_in_database(self):
        polygon = Polygon.from_bbox((-78.50, -0.21, -78.44, -0.15))
        zone = EmergencyZone.objects.create(name="Zona prueba", geometry=MultiPolygon(polygon, srid=4326))
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:alerts_in_zone"), {"zone_id": zone.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_global_date_filter_is_applied_to_alerts(self):
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:alerts_geojson"), {"date_from": "2099-01-01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["features"], [])

    def test_operational_detail_contains_resources_but_not_sensitive_data(self):
        team = RescueTeam.objects.create(name="Equipo detalle", code="EQ-DETAIL", current_location=Point(-78.46, -0.18, srid=4326))
        RescueAssignment.objects.create(alert=Alert.objects.first(), team=team, assigned_by=self.operator)
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:alert_operational_detail", kwargs={"pk": Alert.objects.first().pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["assigned_team"]["code"], "EQ-DETAIL")
        self.assertNotIn("phone", response.data)
        self.assertNotIn("identification_number", response.data)

    def test_operational_summary_returns_required_indicators(self):
        self.client.force_authenticate(self.operator)
        response = self.client.get(reverse("mapas:operational_summary"))
        self.assertEqual(response.status_code, 200)
        for key in ("critical_alerts", "pending_alerts", "available_teams", "operational_hospitals", "shelters_with_capacity"):
            self.assertIn(key, response.data)
