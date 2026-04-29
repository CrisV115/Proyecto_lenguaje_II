from django.db import migrations, models


def delete_induction_progress(apps, schema_editor):
    Progress = apps.get_model("tracking", "Progress")
    Progress.objects.filter(phase="induction").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0003_inductionmodule_inductionconstancy_and_more"),
    ]

    operations = [
        migrations.RunPython(delete_induction_progress, migrations.RunPython.noop),
        migrations.DeleteModel(
            name="InductionParticipation",
        ),
        migrations.DeleteModel(
            name="InductionConstancy",
        ),
        migrations.DeleteModel(
            name="InductionModule",
        ),
        migrations.AlterField(
            model_name="progress",
            name="phase",
            field=models.CharField(
                choices=[("test", "Test"), ("leveling", "Nivelacion")],
                max_length=50,
            ),
        ),
    ]
