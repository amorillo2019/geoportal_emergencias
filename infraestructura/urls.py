from django.urls import path

from .views import resource_catalog


app_name = "infraestructura"

urlpatterns = [
    path("", resource_catalog, name="catalog"),
]
