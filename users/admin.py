from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "cedula", "email", "tipo_usuario", "is_staff", "is_active")
    list_filter = ("tipo_usuario", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Informacion adicional",
            {
                "fields": (
                    "cedula",
                    "carrera",
                    "telefono",
                    "tipo_usuario",
                    "pregunta_seguridad",
                    "respuesta_seguridad",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Informacion adicional",
            {
                "fields": (
                    "email",
                    "cedula",
                    "carrera",
                    "telefono",
                    "tipo_usuario",
                    "pregunta_seguridad",
                    "respuesta_seguridad",
                )
            },
        ),
    )
    search_fields = ("username", "cedula", "email", "first_name", "last_name")
    ordering = ("username",)
