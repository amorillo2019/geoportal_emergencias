from django.test import TestCase

from .models import User


class UserModelTests(TestCase):
    def test_user_uses_email_as_identifier(self):
        user = User.objects.create_user("Citizen@example.com", "Strong-password-123")
        self.assertEqual(user.email, "Citizen@example.com")
        self.assertEqual(user.USERNAME_FIELD, "email")
        self.assertTrue(user.check_password("Strong-password-123"))
        self.assertEqual(user.role, User.Role.CITIZEN)

    def test_superuser_gets_administrator_role(self):
        user = User.objects.create_superuser("admin@example.com", "Strong-password-123")
        self.assertEqual(user.role, User.Role.ADMINISTRATOR)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_has_role_allows_superuser_and_matching_role(self):
        operator = User.objects.create_user("operator@example.com", role=User.Role.OPERATOR)
        administrator = User.objects.create_superuser("admin2@example.com", "Strong-password-123")
        self.assertTrue(operator.has_role(User.Role.OPERATOR))
        self.assertFalse(operator.has_role(User.Role.RESCUER))
        self.assertTrue(administrator.has_role(User.Role.RESCUER))
