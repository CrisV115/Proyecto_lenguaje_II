from django.contrib import admin

from .models import Progress


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "phase", "completed", "percentage", "updated_at")
    list_filter = ("phase", "completed")
    search_fields = ("student__username",)
