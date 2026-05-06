from django.db import migrations


DEFAULT_LEVELING_COURSE_NAMES = (
    "Logica Matematica",
    "Linguistica",
    "Geometria",
    "Abstracto",
)


def seed_default_leveling_courses(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Usuario = apps.get_model("users", "Usuario")

    student_ids = list(
        Usuario.objects.filter(tipo_usuario="estudiante").values_list("id", flat=True)
    )
    for course_name in DEFAULT_LEVELING_COURSE_NAMES:
        course, _ = Course.objects.get_or_create(
            name=course_name,
            defaults={
                "career": "",
                "description": "",
                "is_training": False,
                "welcome_message": "Bienvenido a este curso.",
            },
        )
        updated_fields = []
        if course.is_training:
            course.is_training = False
            updated_fields.append("is_training")
        if course.career:
            course.career = ""
            updated_fields.append("career")
        if updated_fields:
            course.save(update_fields=updated_fields)
        if student_ids:
            course.students.add(*student_ids)


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0007_course_career_and_induction_defaults"),
    ]

    operations = [
        migrations.RunPython(
            seed_default_leveling_courses,
            migrations.RunPython.noop,
        ),
    ]
