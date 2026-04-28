from django.conf import settings
from django.db import models

from courses.models import Course


class Test(models.Model):
    TIPO_CHOICES = [
        ("conocimientos", "Conocimientos"),
        ("vocacional", "Vocacional"),
        ("curso", "Curso"),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        default="conocimientos",
    )
    duration = models.PositiveIntegerField(help_text="Duracion en minutos")
    passing_score = models.PositiveIntegerField(default=70)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="tests",
        null=True,
        blank=True,
    )
    available_date = models.DateField(null=True, blank=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_course_test(self):
        return bool(self.course_id) or self.type == "curso"

    @property
    def is_managed_test(self):
        return not self.course_id and self.type in {"conocimientos", "vocacional"}

    @property
    def management_type_label(self):
        if self.is_course_test:
            return "Curso"
        if self.type == "conocimientos":
            return "Diagnostico"
        if self.type == "vocacional":
            return "Vocacional"
        return self.get_type_display() or self.type

    @property
    def student_type_label(self):
        if self.is_course_test:
            return "Curso"
        return self.get_type_display() or self.type


class Question(models.Model):
    QUESTION_TYPES = [
        ("short_text", "Respuesta corta"),
        ("long_text", "Respuesta larga"),
        ("multiple_choice", "Seleccion multiple"),
        ("checkboxes", "Casillas de verificacion"),
        ("dropdown", "Lista desplegable"),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default="multiple_choice",
    )
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["test", "order", "id"]

    def __str__(self):
        return f"{self.test.name} - Pregunta {self.order}"


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["question", "order", "id"]

    def __str__(self):
        return self.text


class Result(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="results",
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="results")
    score = models.FloatField()
    passed = models.BooleanField()
    attempt_number = models.PositiveIntegerField(default=1)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "test"],
                name="unique_student_test_attempt",
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.test} - {self.score:.2f}"


class StudentAnswer(models.Model):
    result = models.ForeignKey(
        Result,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    text_response = models.TextField(blank=True)
    selected_answer_ids = models.JSONField(default=list, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["answered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["result", "question"],
                name="unique_question_per_result",
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.question}"
