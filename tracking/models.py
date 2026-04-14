import uuid

from django.conf import settings
from django.db import models


class Progress(models.Model):
    class Phases(models.TextChoices):
        TEST = "test", "Test"
        INDUCTION = "induction", "Induccion"
        LEVELING = "leveling", "Nivelacion"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_entries",
    )
    phase = models.CharField(max_length=50, choices=Phases.choices)
    completed = models.BooleanField(default=False)
    percentage = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student", "phase"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "phase"],
                name="unique_progress_per_phase",
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.get_phase_display()}"


class InductionModule(models.Model):
    class Modalities(models.TextChoices):
        SYNCHRONOUS = "synchronous", "Sincronica"
        ASYNCHRONOUS = "asynchronous", "Asincronica"

    title = models.CharField(max_length=120)
    description = models.TextField()
    modality = models.CharField(max_length=20, choices=Modalities.choices)
    order = models.PositiveIntegerField(default=1)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class InductionParticipation(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="induction_participations",
    )
    module = models.ForeignKey(
        InductionModule,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    attended = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    attended_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["student", "module__order", "module_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "module"],
                name="unique_induction_participation",
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.module}"


class InductionConstancy(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="induction_constancies",
    )
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    valid = models.BooleanField(default=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.student} - {self.code}"
