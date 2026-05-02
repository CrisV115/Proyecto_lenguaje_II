from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    CAREER_GROUP_PREFIX = "Carrera - "
    CARRERAS = [
        "Enfermeria",
        "Desarrollo de software",
        "Contabilidad",
        "Educacion Inicial",
        "Gestion del Talento Humano",
        "Marketing",
        "Estetica Integral",
        "Mecanica Automotriz",
        "Inteligencia Artificial",
    ]
    CARRERA_CHOICES = [(career, career) for career in CARRERAS]
    CARRERA_ALIASES = {
        "enfermeria": "Enfermeria",
        "desarrollo de software": "Desarrollo de software",
        "desarrollo software": "Desarrollo de software",
        "software": "Desarrollo de software",
        "contabilidad": "Contabilidad",
        "educacion inicial": "Educacion Inicial",
        "gestion del talento humano": "Gestion del Talento Humano",
        "marketing": "Marketing",
        "estetica integral": "Estetica Integral",
        "mecanica automotriz": "Mecanica Automotriz",
        "inteligencia artificial": "Inteligencia Artificial",
    }

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
    cedula = models.CharField(max_length=10, unique=True, blank=True, null=True)
    carrera = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=10)
    debe_cambiar_password = models.BooleanField(default=False)
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

    @property
    def is_student(self):
        return self.tipo_usuario == "estudiante"

    @property
    def is_professor(self):
        return self.tipo_usuario == "profesor"

    @property
    def display_name(self):
        first_name = (self.first_name or "").strip().split()
        last_name = (self.last_name or "").strip().split()
        short_name = " ".join(part for part in [first_name[0] if first_name else "", last_name[0] if last_name else ""] if part)
        return short_name or self.username

    @classmethod
    def normalize_carrera(cls, value):
        cleaned = " ".join((value or "").strip().split())
        if not cleaned:
            return ""
        return cls.CARRERA_ALIASES.get(cleaned.casefold(), cleaned)

    def save(self, *args, **kwargs):
        self.carrera = self.normalize_carrera(self.carrera)
        super().save(*args, **kwargs)
        self.sync_career_group()

    def sync_career_group(self):
        from django.contrib.auth.models import Group

        existing_groups = self.groups.filter(name__startswith=self.CAREER_GROUP_PREFIX)
        if existing_groups.exists():
            self.groups.remove(*existing_groups)

        if not self.carrera:
            return

        career_group, _ = Group.objects.get_or_create(
            name=f"{self.CAREER_GROUP_PREFIX}{self.carrera}"
        )
        self.groups.add(career_group)

    def __str__(self):
        return self.username
