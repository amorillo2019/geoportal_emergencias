from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import PublicAlertForm
from usuarios.models import User

from .models import Alert, AlertHistory


class AlertModelTests(TestCase):
    def test_alert_builds_point_from_coordinates(self):
        alert = Alert.objects.create(
            emergency_type=Alert.EmergencyType.TRAPPED_PERSON,
            latitude=Decimal("-0.180653"),
            longitude=Decimal("-78.467834"),
        )
        self.assertEqual(alert.point.srid, 4326)
        self.assertEqual(alert.point.x, -78.467834)
        self.assertEqual(alert.point.y, -0.180653)
        self.assertTrue(alert.public_tracking_code.startswith("GE-"))

    def test_form_rejects_missing_location_or_consent(self):
        form = PublicAlertForm(data={"emergency_type": Alert.EmergencyType.FIRE})
        self.assertFalse(form.is_valid())
        self.assertIn("consent_location", form.errors)
        self.assertIn("latitude", form.errors)


class PublicAlertViewTests(TestCase):
    def test_public_form_creates_alert_and_redirects_to_confirmation(self):
        response = self.client.post(reverse("alertas:public_create"), {
            "person_name": "Persona de prueba",
            "phone": "0990000000",
            "latitude": "-0.180653",
            "longitude": "-78.467834",
            "emergency_type": Alert.EmergencyType.INJURED_PERSON,
            "description": "Necesita ayuda.",
            "estimated_affected_people": "1",
            "injured_people": "1",
            "building_condition": Alert.BuildingCondition.UNKNOWN,
            "consent_location": "on",
        })
        alert = Alert.objects.get()
        self.assertRedirects(
            response,
            reverse("alertas:confirmation", kwargs={"code": alert.public_tracking_code}),
        )

    def test_tracking_page_does_not_expose_sensitive_identification(self):
        alert = Alert.objects.create(
            person_name="Persona de prueba",
            identification_number="PRIVATE-123",
            phone="0990000000",
            emergency_type=Alert.EmergencyType.OTHER,
            latitude=Decimal("-0.180653"),
            longitude=Decimal("-78.467834"),
        )
        response = self.client.get(reverse("alertas:tracking", kwargs={"code": alert.public_tracking_code}))
        self.assertContains(response, alert.public_tracking_code)
        self.assertContains(response, "Recibida")
        self.assertNotContains(response, "PRIVATE-123")
        self.assertNotContains(response, "0990000000")

    def test_public_form_rejects_unsupported_file_type(self):
        form = PublicAlertForm(
            data={"latitude": "-0.1", "longitude": "-78.4", "emergency_type": Alert.EmergencyType.FIRE, "consent_location": "on"},
            files={"image": SimpleUploadedFile("script.txt", b"not an image", content_type="text/plain")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)


class OperationsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = User.objects.create_user(
            "operator-alerts@example.com", "Strong-password-123", role=User.Role.OPERATOR
        )
        cls.citizen = User.objects.create_user(
            "citizen-alerts@example.com", "Strong-password-123", role=User.Role.CITIZEN
        )
        cls.alert = Alert.objects.create(
            emergency_type=Alert.EmergencyType.FIRE,
            latitude=Decimal("-0.180653"),
            longitude=Decimal("-78.467834"),
        )

    def test_operator_can_view_dashboard_and_detail(self):
        self.client.force_login(self.operator)
        dashboard = self.client.get(reverse("alertas:operations_dashboard"))
        detail = self.client.get(reverse("alertas:operations_detail", kwargs={"pk": self.alert.pk}))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, self.alert.public_tracking_code)
        self.assertEqual(detail.status_code, 200)

    def test_citizen_cannot_view_operations_dashboard(self):
        self.client.force_login(self.citizen)
        response = self.client.get(reverse("alertas:operations_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_verify_and_change_priority_create_history(self):
        self.client.force_login(self.operator)
        response = self.client.post(reverse("alertas:verify_alert", kwargs={"pk": self.alert.pk}))
        self.assertEqual(response.status_code, 302)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.VERIFIED)
        self.assertTrue(AlertHistory.objects.filter(alert=self.alert, change_type=AlertHistory.ChangeType.STATUS).exists())

        self.client.post(
            reverse("alertas:update_priority", kwargs={"pk": self.alert.pk}),
            {"priority": Alert.Priority.CRITICAL},
        )
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.priority, Alert.Priority.CRITICAL)
        self.assertTrue(AlertHistory.objects.filter(alert=self.alert, change_type=AlertHistory.ChangeType.PRIORITY).exists())

    def test_internal_observation_is_recorded(self):
        self.client.force_login(self.operator)
        self.client.post(
            reverse("alertas:add_note", kwargs={"pk": self.alert.pk}),
            {"observation": "Se contacto al equipo de turno."},
        )
        self.alert.refresh_from_db()
        self.assertIn("Se contacto al equipo de turno.", self.alert.internal_notes)
        self.assertTrue(AlertHistory.objects.filter(alert=self.alert, change_type=AlertHistory.ChangeType.OBSERVATION).exists())
