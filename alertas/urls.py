from django.urls import path

from .views import (
    add_alert_note, alert_confirmation, alert_tracking, operations_dashboard,
    operations_detail, public_alert_create, update_alert_priority,
    update_alert_status, verify_alert,
)


app_name = "alertas"

urlpatterns = [
    path("nueva/", public_alert_create, name="public_create"),
    path("confirmacion/<str:code>/", alert_confirmation, name="confirmation"),
    path("seguimiento/<str:code>/", alert_tracking, name="tracking"),
    path("operaciones/", operations_dashboard, name="operations_dashboard"),
    path("operaciones/alertas/<int:pk>/", operations_detail, name="operations_detail"),
    path("operaciones/alertas/<int:pk>/verificar/", verify_alert, name="verify_alert"),
    path("operaciones/alertas/<int:pk>/estado/", update_alert_status, name="update_status"),
    path("operaciones/alertas/<int:pk>/prioridad/", update_alert_priority, name="update_priority"),
    path("operaciones/alertas/<int:pk>/observacion/", add_alert_note, name="add_note"),
]
