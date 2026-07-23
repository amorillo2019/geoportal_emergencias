from django.shortcuts import render

from usuarios.decorators import role_required

from .models import (
    AffectedBuilding, AdministrativeSector, BlockedRoadSegment,
    EmergencyZone, Hospital, Road, Shelter,
)


@role_required("operator", "coordinator", "administrator")
def resource_catalog(request):
    resources = [
        ("Hospitales", Hospital, "mapas:resource_layers_geojson", "hospitals"),
        ("Refugios", Shelter, "mapas:resource_layers_geojson", "shelters"),
        ("Vias", Road, "mapas:resource_layers_geojson", "roads"),
        ("Tramos bloqueados", BlockedRoadSegment, "mapas:resource_layers_geojson", "blocked_roads"),
        ("Edificaciones afectadas", AffectedBuilding, "mapas:resource_layers_geojson", "buildings"),
        ("Zonas de emergencia", EmergencyZone, "mapas:resource_layers_geojson", "emergency_zones"),
        ("Sectores administrativos", AdministrativeSector, "mapas:resource_layers_geojson", "sectors"),
    ]
    return render(request, "infraestructura/catalog.html", {
        "resources": [{"label": label, "count": model.objects.count(), "layer": layer} for label, model, _, layer in resources],
    })
