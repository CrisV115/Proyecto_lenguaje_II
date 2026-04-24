from django.contrib import admin

from .models import Course


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
