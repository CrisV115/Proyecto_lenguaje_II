from django.contrib import admin

from tests_academic.utils import sync_course_student_assignments

from .forms import CourseAdminForm
from .models import (
    Course,
    CourseActivity,
    CourseActivitySubmission,
    CourseClassAttendance,
    CourseClassSession,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    list_display = (
        "name",
        "course_type",
        "course_audience",
        "teachers_count",
        "students_count",
        "updated_at",
    )
    search_fields = ("name", "description", "career")
    list_filter = ("is_training", "career")
    filter_horizontal = ("teachers",)
    readonly_fields = ("created_at", "updated_at", "category_label")

    def get_fieldsets(self, request, obj=None):
        info_fields = ["name", "career", "description", "welcome_message"]
        if obj and obj.is_training:
            info_fields = ["name", "category_label", "description", "welcome_message"]

        return (
            (
                "Informacion del curso",
                {
                    "fields": tuple(info_fields),
                },
            ),
            ("Asignaciones", {"fields": ("teachers",)}),
            ("Tiempos", {"fields": ("created_at", "updated_at")}),
        )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_training:
            readonly_fields.append("name")
        return tuple(readonly_fields)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_training = False
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sync_course_student_assignments(form.instance)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_training:
            return False
        return super().has_delete_permission(request, obj)

    @admin.display(description="Profesores")
    def teachers_count(self, obj):
        return obj.teachers.count()

    @admin.display(description="Estudiantes")
    def students_count(self, obj):
        return obj.students.count()

    @admin.display(description="Tipo")
    def course_type(self, obj):
        return obj.category_label

    @admin.display(description="Alcance")
    def course_audience(self, obj):
        return obj.audience_label


@admin.register(CourseActivity)
class CourseActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "due_date", "opening_time", "closing_time")
    list_filter = ("course", "due_date")
    search_fields = ("title", "description", "course__name")
    autocomplete_fields = ("course", "created_by")


@admin.register(CourseActivitySubmission)
class CourseActivitySubmissionAdmin(admin.ModelAdmin):
    list_display = ("activity", "student", "grade", "graded_by", "submitted_at")
    list_filter = ("activity__course", "submitted_at")
    search_fields = ("activity__title", "student__username", "student__email")
    autocomplete_fields = ("activity", "student", "graded_by")


@admin.register(CourseClassSession)
class CourseClassSessionAdmin(admin.ModelAdmin):
    list_display = ("course", "session_number", "class_date", "created_by")
    list_filter = ("course", "class_date")
    search_fields = ("course__name",)
    autocomplete_fields = ("course", "created_by")


@admin.register(CourseClassAttendance)
class CourseClassAttendanceAdmin(admin.ModelAdmin):
    list_display = ("class_session", "student", "present", "marked_by", "marked_at")
    list_filter = ("class_session__course", "present", "marked_at")
    search_fields = (
        "class_session__course__name",
        "student__username",
        "student__first_name",
        "student__last_name",
    )
    autocomplete_fields = ("class_session", "student", "marked_by")
