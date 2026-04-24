from django.conf import settings
from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    welcome_message = models.TextField(
        default="Bienvenido a este curso.",
        help_text="Mensaje inicial que veran los usuarios asignados.",
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="courses_enrolled",
        limit_choices_to={"tipo_usuario": "estudiante"},
    )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="courses_taught",
        limit_choices_to={"tipo_usuario": "profesor"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def __str__(self):
        return self.name
