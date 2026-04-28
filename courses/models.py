from django.core.validators import FileExtensionValidator
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
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


class CourseActivitySubmission(models.Model):
    activity = models.ForeignKey(
        CourseActivity,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_submissions",
    )
    submission_text = models.TextField(blank=True)
    submission_url = models.URLField(blank=True)
    attachment = models.FileField(
        upload_to="course_submissions/",
        blank=True,
        validators=[
            FileExtensionValidator(
                ["pdf", "doc", "docx", "ppt", "pptx", "zip", "rar", "txt", "jpg", "png"]
            )
        ],
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    teacher_comment = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_activity_submissions",
        limit_choices_to={"tipo_usuario": "profesor"},
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Entrega de actividad"
        verbose_name_plural = "Entregas de actividades"
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "student"],
                name="unique_activity_submission_per_student",
            )
        ]

    def clean(self):
        super().clean()
        if not self.submission_text and not self.submission_url and not self.attachment:
            raise ValidationError(
                "Debes cargar un archivo, URL o comentario para registrar la entrega."
            )

    def __str__(self):
        return f"{self.activity.title} - {self.student.username}"
