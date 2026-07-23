from django.test import TestCase
from django.urls import reverse

from usuarios.models import User

from .models import Hospital


class InfrastructureCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = User.objects.create_user("infra-operator@example.com", "Strong-password-123", role=User.Role.OPERATOR)
        cls.citizen = User.objects.create_user("infra-citizen@example.com", "Strong-password-123", role=User.Role.CITIZEN)

    def test_operator_can_view_catalog(self):
        self.client.force_login(self.operator)
        response = self.client.get(reverse("infraestructura:catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hospitales")
        self.assertContains(response, "Sectores administrativos")

    def test_citizen_cannot_view_catalog(self):
        self.client.force_login(self.citizen)
        response = self.client.get(reverse("infraestructura:catalog"))
        self.assertEqual(response.status_code, 403)
