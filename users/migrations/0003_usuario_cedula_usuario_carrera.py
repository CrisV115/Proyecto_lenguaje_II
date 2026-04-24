# Generated manually for CSV user import support.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_usuario_pregunta_seguridad_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="carrera",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="usuario",
            name="cedula",
            field=models.CharField(blank=True, default=None, max_length=10, null=True, unique=True),
            preserve_default=False,
        ),
    ]
