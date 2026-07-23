from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path("", RedirectView.as_view(pattern_name="mapas:operations_map", permanent=False), name="home"),
    path("admin/", admin.site.urls),
    path("", include("usuarios.urls")),
    path("alertas/", include("alertas.urls")),
    path("mapa/", include("mapas.urls")),
    path("rescates/", include("rescates.urls")),
    path("infraestructura/", include("infraestructura.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
