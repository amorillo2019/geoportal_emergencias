from django.urls import path

from .views import create_assignment, create_victim, create_victim_general, update_assignment


app_name = "rescates"

urlpatterns = [
    path("victimas/nueva/", create_victim_general, name="create_victim_general"),
    path("alertas/<int:alert_id>/asignar/", create_assignment, name="create_assignment"),
    path("asignaciones/<int:pk>/actualizar/", update_assignment, name="update_assignment"),
    path("alertas/<int:alert_id>/victimas/nueva/", create_victim, name="create_victim"),
]
