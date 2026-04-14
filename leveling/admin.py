from django.contrib import admin

from .models import LevelingRecord


@admin.register(LevelingRecord)
class LevelingRecordAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "synchronous_sessions_attended",
        "synchronous_sessions_total",
        "asynchronous_activities_completed",
        "asynchronous_activities_total",
        "final_exam_score",
        "updated_at",
    )
    search_fields = ("student__username",)
