from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if request.user.tipo_usuario not in allowed_roles:
                messages.warning(
                    request,
                    "No tienes permisos para acceder a esa seccion.",
                )
                return redirect("role_dashboard")
            return view_func(request, *args, **kwargs)

        return wrapped_view

    return decorator
