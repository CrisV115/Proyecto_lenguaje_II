from django.contrib import admin

from .models import (
    InductionConstancy,
    InductionModule,
    InductionParticipation,
    Progress,
)


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "phase", "completed", "percentage", "updated_at")
    list_filter = ("phase", "completed")
    search_fields = ("student__username",)


@admin.register(InductionModule)
class InductionModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "modality", "order", "required")
    list_filter = ("modality", "required")
    search_fields = ("title",)


@admin.register(InductionParticipation)
class InductionParticipationAdmin(admin.ModelAdmin):
    list_display = ("student", "module", "attended", "completed", "attended_at", "completed_at")
    list_filter = ("attended", "completed", "module__modality")
    search_fields = ("student__username", "module__title")


@admin.register(InductionConstancy)
class InductionConstancyAdmin(admin.ModelAdmin):
    list_display = ("student", "code", "valid", "issued_at")
    list_filter = ("valid",)
    search_fields = ("student__username", "code")
