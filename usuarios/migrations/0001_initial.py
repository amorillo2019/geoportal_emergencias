import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models

import usuarios.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designa que este usuario tiene todos los permisos sin asignarlos explícitamente.", verbose_name="superuser status")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="correo electronico")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="nombres")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="apellidos")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="telefono")),
                ("role", models.CharField(choices=[("citizen", "Ciudadano o victima"), ("operator", "Operador de emergencias"), ("rescuer", "Rescatista"), ("coordinator", "Coordinador"), ("administrator", "Administrador")], default="citizen", max_length=20, verbose_name="rol")),
                ("is_staff", models.BooleanField(default=False, verbose_name="personal administrativo")),
                ("is_active", models.BooleanField(default=True, verbose_name="activo")),
                ("date_joined", models.DateTimeField(auto_now_add=True, verbose_name="fecha de registro")),
                ("groups", models.ManyToManyField(blank=True, help_text="Los grupos a los que pertenece este usuario. Un usuario obtendra todos los permisos otorgados a cada uno de sus grupos.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Permisos especificos para este usuario.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "verbose_name": "usuario",
                "verbose_name_plural": "usuarios",
                "ordering": ["last_name", "first_name", "email"],
            },
            managers=[("objects", usuarios.models.UserManager())],
        ),
    ]
