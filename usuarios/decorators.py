from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if not request.user.has_role(*roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
