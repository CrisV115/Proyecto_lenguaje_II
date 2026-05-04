from django.db import migrations, models


INDUCTION_COURSE_NAMES = (
    "Microsoft Teams",
    "SGA",
    "PAO",
)


def _normalize_career(value):
    return " ".join((value or "").strip().split())


def seed_course_careers_and_induction(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Usuario = apps.get_model("users", "Usuario")

    for course in Course.objects.filter(is_training=True):
        updated_fields = []
        if course.career:
            course.career = ""
            updated_fields.append("career")
        if updated_fields:
            course.save(update_fields=updated_fields)

    for course in Course.objects.filter(is_training=False):
        normalized_career = _normalize_career(getattr(course, "career", ""))
        if normalized_career:
            if normalized_career != course.career:
                course.career = normalized_career
                course.save(update_fields=["career"])
            continue

        student_careers = sorted(
            {
                _normalize_career(career)
                for career in course.students.exclude(carrera="")
                .values_list("carrera", flat=True)
                if _normalize_career(career)
            },
            key=str.casefold,
        )
        teacher_careers = sorted(
            {
                _normalize_career(career)
                for career in course.teachers.exclude(carrera="")
                .values_list("carrera", flat=True)
                if _normalize_career(career)
            },
            key=str.casefold,
        )

        inferred_career = ""
        if len(student_careers) == 1:
            inferred_career = student_careers[0]
        elif len(teacher_careers) == 1:
            inferred_career = teacher_careers[0]

        if inferred_career:
            course.career = inferred_career
            course.save(update_fields=["career"])

    student_ids = list(
        Usuario.objects.filter(tipo_usuario="estudiante").values_list("id", flat=True)
    )
    for course_name in INDUCTION_COURSE_NAMES:
        course, _ = Course.objects.get_or_create(
            name=course_name,
            defaults={
                "career": "",
                "description": "",
                "is_training": True,
                "welcome_message": "Bienvenido a este curso.",
            },
        )
        updated_fields = []
        if not course.is_training:
            course.is_training = True
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
        ("courses", "0006_course_is_training"),
        ("users", "0004_usuario_debe_cambiar_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="career",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Selecciona la carrera para las nivelaciones. "
                    "Los cursos de induccion aplican a todos."
                ),
                max_length=120,
                verbose_name="Carrera",
            ),
        ),
        migrations.RunPython(
            seed_course_careers_and_induction,
            migrations.RunPython.noop,
        ),
    ]
