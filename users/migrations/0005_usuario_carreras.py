from django.db import migrations, models


def migrate_existing_careers(apps, schema_editor):
    Usuario = apps.get_model("users", "Usuario")
    for usuario in Usuario.objects.all():
        usuario.carreras = [usuario.carrera] if usuario.carrera else []
        usuario.save(update_fields=["carreras"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_usuario_debe_cambiar_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="carreras",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(migrate_existing_careers, migrations.RunPython.noop),
    ]
