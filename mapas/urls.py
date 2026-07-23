from django.urls import path

from .api import (
    alert_operational_detail, alerts_geojson, alerts_in_zone, nearby_alerts,
    nearby_resources, operational_summary, resource_layer_geojson,
)
from .views import operations_map


app_name = "mapas"

urlpatterns = [
    path("", operations_map, name="operations_map"),
    path("api/alertas/", alerts_geojson, name="alerts_geojson"),
    path("api/capas/", resource_layer_geojson, name="resource_layers_geojson"),
    path("api/espacial/recursos-cercanos/", nearby_resources, name="nearby_resources"),
    path("api/espacial/alertas-cercanas/", nearby_alerts, name="nearby_alerts"),
    path("api/espacial/alertas-zona/", alerts_in_zone, name="alerts_in_zone"),
    path("api/resumen/", operational_summary, name="operational_summary"),
    path("api/alertas/<int:pk>/detalle-operativo/", alert_operational_detail, name="alert_operational_detail"),
]
