# Generated manually for first-login password update.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_usuario_cedula_usuario_carrera"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="debe_cambiar_password",
            field=models.BooleanField(default=False),
        ),
    ]
