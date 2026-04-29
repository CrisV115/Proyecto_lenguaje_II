from django.conf import settings
from django.db import models


class Progress(models.Model):
    class Phases(models.TextChoices):
        TEST = "test", "Test"
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
