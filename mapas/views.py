from django.shortcuts import render

from usuarios.decorators import role_required
from usuarios.models import User


@role_required(
    User.Role.OPERATOR,
    User.Role.RESCUER,
    User.Role.COORDINATOR,
    User.Role.ADMINISTRATOR,
)
def operations_map(request):
    return render(request, "mapas/operations_map.html")
