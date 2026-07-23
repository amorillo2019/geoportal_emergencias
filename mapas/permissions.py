from rest_framework.permissions import BasePermission

from usuarios.models import User


class OperationsMapPermission(BasePermission):
    message = "No tiene permisos para consultar el mapa operativo."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role(
            User.Role.OPERATOR,
            User.Role.RESCUER,
            User.Role.COORDINATOR,
            User.Role.ADMINISTRATOR,
        )
