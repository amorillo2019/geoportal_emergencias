from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Creates users using email as the authentication identifier."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electronico es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMINISTRATOR)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Ciudadano o victima"
        OPERATOR = "operator", "Operador de emergencias"
        RESCUER = "rescuer", "Rescatista"
        COORDINATOR = "coordinator", "Coordinador"
        ADMINISTRATOR = "administrator", "Administrador"

    email = models.EmailField("correo electronico", unique=True)
    first_name = models.CharField("nombres", max_length=150, blank=True)
    last_name = models.CharField("apellidos", max_length=150, blank=True)
    phone = models.CharField("telefono", max_length=30, blank=True)
    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.CITIZEN)
    is_staff = models.BooleanField("personal administrativo", default=False)
    is_active = models.BooleanField("activo", default=True)
    date_joined = models.DateTimeField("fecha de registro", auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["last_name", "first_name", "email"]
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.email

    def has_role(self, *roles):
        return self.is_superuser or self.role in roles
