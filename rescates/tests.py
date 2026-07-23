from decimal import Decimal

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse

from alertas.models import Alert
from infraestructura.models import Hospital
from usuarios.models import User

from .models import AssignmentHistory, RescueAssignment, RescueTeam, Victim
from .forms import VictimForm


class RescueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = User.objects.create_user("rescue-operator@example.com", "Strong-password-123", role=User.Role.OPERATOR)
        cls.citizen = User.objects.create_user("rescue-citizen@example.com", "Strong-password-123", role=User.Role.CITIZEN)
        cls.alert = Alert.objects.create(
            emergency_type=Alert.EmergencyType.TRAPPED_PERSON,
            latitude=Decimal("-0.180653"), longitude=Decimal("-78.467834"),
        )
        cls.team = RescueTeam.objects.create(
            name="Equipo prueba", code="EQ-TEST", current_location=Point(-78.46, -0.18, srid=4326),
        )

    def test_operator_can_assign_team_and_record_victim(self):
        self.client.force_login(self.operator)
        response = self.client.post(reverse("rescates:create_assignment", kwargs={"alert_id": self.alert.pk}), {"team": self.team.pk, "notes": "Salida inmediata"})
        self.assertEqual(response.status_code, 302)
        assignment = RescueAssignment.objects.get(alert=self.alert)
        self.assertEqual(assignment.assigned_by, self.operator)
        self.team.refresh_from_db()
        self.assertEqual(self.team.operational_status, RescueTeam.OperationalStatus.ASSIGNED)

        response = self.client.post(reverse("rescates:create_victim", kwargs={"alert_id": self.alert.pk}), {"first_names": "Persona", "last_names": "Prueba", "rescue_status": Victim.RescueStatus.REPORTED})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Victim.objects.filter(alert=self.alert).count(), 1)

    def test_victim_location_is_saved_from_form_coordinates(self):
        self.client.force_login(self.operator)
        response = self.client.post(
            reverse("rescates:create_victim", kwargs={"alert_id": self.alert.pk}),
            {
                "first_names": "Persona ubicada",
                "rescue_status": Victim.RescueStatus.LOCATED,
                "latitude": "-0.181000",
                "longitude": "-78.468000",
            },
        )
        self.assertEqual(response.status_code, 302)
        victim = Victim.objects.get(first_names="Persona ubicada")
        self.assertAlmostEqual(victim.location.y, -0.181, places=6)
        self.assertAlmostEqual(victim.location.x, -78.468, places=6)

    def test_assignment_status_change_is_audited(self):
        assignment = RescueAssignment.objects.create(alert=self.alert, team=self.team, assigned_by=self.operator)
        self.client.force_login(self.operator)
        self.client.post(reverse("rescates:update_assignment", kwargs={"pk": assignment.pk}), {"status": RescueAssignment.Status.EN_ROUTE, "notes": "En camino", "outcome": ""})
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, RescueAssignment.Status.EN_ROUTE)
        self.assertTrue(AssignmentHistory.objects.filter(assignment=assignment).exists())

    def test_citizen_cannot_manage_rescues(self):
        self.client.force_login(self.citizen)
        response = self.client.get(reverse("rescates:create_victim", kwargs={"alert_id": self.alert.pk}))
        self.assertEqual(response.status_code, 403)

    def test_victim_can_have_one_protected_destination(self):
        hospital = Hospital.objects.create(name="Hospital destino", point=Point(-78.46, -0.18, srid=4326))
        form = VictimForm(data={"first_names": "Persona", "rescue_status": Victim.RescueStatus.TRANSFERRED, "transfer_hospital": hospital.pk})
        self.assertTrue(form.is_valid(), form.errors)
        invalid = VictimForm(data={"first_names": "Persona", "transfer_hospital": hospital.pk, "safe_place": "Lugar seguro demo"})
        self.assertFalse(invalid.is_valid())

    def test_operator_can_open_general_victim_registration(self):
        self.client.force_login(self.operator)
        response = self.client.get(reverse("rescates:create_victim_general"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alerta relacionada")
