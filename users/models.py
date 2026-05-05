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
    carreras = models.JSONField(default=list, blank=True)
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

    @classmethod
    def normalize_carreras(cls, values):
        normalized = []
        seen = set()
        for value in values or []:
            cleaned = cls.normalize_carrera(value)
            if cleaned and cleaned not in seen:
                normalized.append(cleaned)
                seen.add(cleaned)
        return normalized

    def get_carreras(self):
        normalized = self.normalize_carreras(self.carreras)
        if self.carrera and self.carrera not in normalized:
            normalized.insert(0, self.carrera)
        if self.tipo_usuario != "profesor":
            return [self.carrera] if self.carrera else []
        return normalized

    def set_carreras(self, values):
        normalized = self.normalize_carreras(values)
        self.carreras = normalized
        self.carrera = normalized[0] if normalized else ""

    def has_career(self, career):
        normalized = self.normalize_carrera(career)
        return normalized in self.get_carreras()

    def save(self, *args, **kwargs):
        self.carrera = self.normalize_carrera(self.carrera)
        if self.tipo_usuario == "profesor":
            normalized_careers = self.normalize_carreras(self.carreras)
            if self.carrera and self.carrera not in normalized_careers:
                normalized_careers.insert(0, self.carrera)
            if normalized_careers and not self.carrera:
                self.carrera = normalized_careers[0]
            self.carreras = normalized_careers
        else:
            self.carreras = [self.carrera] if self.carrera else []
        super().save(*args, **kwargs)
        self.sync_career_groups()

    def sync_career_groups(self):
        from django.contrib.auth.models import Group

        existing_groups = self.groups.filter(name__startswith=self.CAREER_GROUP_PREFIX)
        if existing_groups.exists():
            self.groups.remove(*existing_groups)

        careers = self.get_carreras()
        if not careers:
            return

        for career in careers:
            career_group, _ = Group.objects.get_or_create(
                name=f"{self.CAREER_GROUP_PREFIX}{career}"
            )
            self.groups.add(career_group)

    def __str__(self):
        return self.username
