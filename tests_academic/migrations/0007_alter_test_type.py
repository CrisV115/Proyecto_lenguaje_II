from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tests_academic", "0006_test_available_date_test_closing_time_test_course_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="test",
            name="type",
            field=models.CharField(
                choices=[
                    ("conocimientos", "Conocimientos"),
                    ("vocacional", "Vocacional"),
                    ("curso", "Curso"),
                ],
                default="conocimientos",
                max_length=50,
            ),
        ),
    ]
