from django.db import migrations, models


def replace_induction_source_phase(apps, schema_editor):
    Certificate = apps.get_model("certifications", "Certificate")
    Certificate.objects.filter(source_phase="induction").update(source_phase="completion")


class Migration(migrations.Migration):
    dependencies = [
        ("certifications", "0002_alter_certificate_source_phase"),
    ]

    operations = [
        migrations.RunPython(replace_induction_source_phase, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="certificate",
            name="source_phase",
            field=models.CharField(
                blank=True,
                choices=[
                    ("leveling", "Nivelacion"),
                    ("completion", "Ruta academica completa"),
                ],
                max_length=50,
            ),
        ),
    ]
