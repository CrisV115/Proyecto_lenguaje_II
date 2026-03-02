from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    telefono = models.CharField(max_length=10)

    PREGUNTAS = [
        ('mascota', '¿Cómo se llama tu primera mascota?'),
        ('madre', '¿Cuál es el segundo nombre de tu madre?'),
        ('ciudad', '¿En qué ciudad naciste?'),
    ]

    ROLES = [
        ('estudiante', 'Estudiante'),
        ('profesor', 'Profesor'),
    ]

    tipo_usuario = models.CharField(max_length=20, choices=ROLES, default='estudiante')
    pregunta_seguridad = models.CharField(max_length=50, choices=PREGUNTAS)
    respuesta_seguridad = models.CharField(max_length=100)

    def __str__(self):
        return self.username
