from django.db import migrations


DEFAULT_LEVELING_COURSE_NAMES = (
    "Geometria",
    "Logica Matematica",
    "Linguistica",
    "Abstracto",
)


def reset_leveling_courses(apps, schema_editor):
    Course = apps.get_model("courses", "Course")

    Course.objects.filter(is_training=False).delete()

    for course_name in DEFAULT_LEVELING_COURSE_NAMES:
        Course.objects.create(
            name=course_name,
            career="",
            classroom=None,
            description="",
            is_training=False,
            welcome_message="Bienvenido a este curso.",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0010_inductioncourse_alter_course_name_classroom_and_more"),
    ]

    operations = [
        migrations.RunPython(
            reset_leveling_courses,
            migrations.RunPython.noop,
        ),
    ]
