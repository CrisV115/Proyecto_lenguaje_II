from django.contrib import admin

from .models import Course, CourseActivity, CourseActivitySubmission


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "teachers_count",
        "students_count",
        "updated_at",
    )
    search_fields = ("name", "description")
    filter_horizontal = ("teachers", "students")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Informacion del curso",
            {
                "fields": (
                    "name",
                    "description",
                    "welcome_message",
                )
            },
        ),
        ("Asignaciones", {"fields": ("teachers", "students")}),
        ("Tiempos", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Profesores")
    def teachers_count(self, obj):
        return obj.teachers.count()

    @admin.display(description="Estudiantes")
    def students_count(self, obj):
        return obj.students.count()


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
