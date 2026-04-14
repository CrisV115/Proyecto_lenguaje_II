from django.conf import settings
from django.db import models


class LevelingRecord(models.Model):
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leveling_record",
    )
    synchronous_sessions_attended = models.PositiveIntegerField(default=0)
    synchronous_sessions_total = models.PositiveIntegerField(default=3)
    asynchronous_activities_completed = models.PositiveIntegerField(default=0)
    asynchronous_activities_total = models.PositiveIntegerField(default=4)
    final_exam_score = models.FloatField(default=0)
    minimum_attendance_percentage = models.PositiveIntegerField(default=70)
    minimum_exam_score = models.PositiveIntegerField(default=70)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student__username"]

    def __str__(self):
        return f"{self.student} - Nivelacion"

    @property
    def synchronous_percentage(self):
        if not self.synchronous_sessions_total:
            return 0
        return round((self.synchronous_sessions_attended / self.synchronous_sessions_total) * 100, 2)

    @property
    def asynchronous_percentage(self):
        if not self.asynchronous_activities_total:
            return 0
        return round((self.asynchronous_activities_completed / self.asynchronous_activities_total) * 100, 2)

    @property
    def participation_percentage(self):
        total_items = self.synchronous_sessions_total + self.asynchronous_activities_total
        completed_items = self.synchronous_sessions_attended + self.asynchronous_activities_completed
        if not total_items:
            return 0
        return round((completed_items / total_items) * 100, 2)

    @property
    def attendance_requirement_met(self):
        return self.participation_percentage >= self.minimum_attendance_percentage

    @property
    def final_exam_passed(self):
        return self.final_exam_score >= self.minimum_exam_score

    @property
    def ready_for_completion(self):
        return self.attendance_requirement_met and self.final_exam_passed
