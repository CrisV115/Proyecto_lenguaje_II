import uuid

from django.conf import settings
from django.db import models


class Certificate(models.Model):
    SOURCE_PHASE_CHOICES = [
        ("leveling", "Nivelacion"),
        ("completion", "Ruta academica completa"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    issue_date = models.DateTimeField(auto_now_add=True)
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    valid = models.BooleanField(default=True)
    source_phase = models.CharField(
        max_length=50,
        blank=True,
        choices=SOURCE_PHASE_CHOICES,
    )

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.student} - {self.code}"
