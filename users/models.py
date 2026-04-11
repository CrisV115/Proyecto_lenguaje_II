from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    PREGUNTAS_SEGURIDAD = [
        ("mascota", "Como se llama tu primera mascota?"),
        ("madre", "Cual es el segundo nombre de tu madre?"),
        ("ciudad", "En que ciudad naciste?"),
    ]

    ROLES = [
        ("estudiante", "Estudiante"),
        ("profesor", "Profesor"),
        ("admin_academico", "Administrador academico"),
    ]

    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=10)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=ROLES,
        default="estudiante",
    )
    pregunta_seguridad = models.CharField(
        max_length=50,
        choices=PREGUNTAS_SEGURIDAD,
    )
    respuesta_seguridad = models.CharField(max_length=100)

    def __str__(self):
        return self.username
