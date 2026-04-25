from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.core.exceptions import ValidationError
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


class CourseActivity(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    title = models.CharField(max_length=180)
    description = models.TextField()
    url = models.URLField(blank=True)
    attachment = models.FileField(
        upload_to="course_activities/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "docx", "pptx"])],
    )
    due_date = models.DateField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_course_activities",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "opening_time", "id"]
        verbose_name = "Actividad de curso"
        verbose_name_plural = "Actividades de cursos"

    def clean(self):
        super().clean()
        if (
            self.opening_time
            and self.closing_time
            and self.opening_time >= self.closing_time
        ):
            raise ValidationError(
                {"closing_time": "La hora de cierre debe ser posterior a la hora de apertura."}
            )

    def __str__(self):
        return f"{self.course.name} - {self.title}"
