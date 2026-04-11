from django.conf import settings
from django.db import models


class Test(models.Model):
    TIPO_CHOICES = [
        ("conocimientos", "Conocimientos"),
        ("vocacional", "Vocacional"),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=TIPO_CHOICES)
    duration = models.PositiveIntegerField(help_text="Duracion en minutos")
    passing_score = models.PositiveIntegerField(default=70)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
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
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
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
