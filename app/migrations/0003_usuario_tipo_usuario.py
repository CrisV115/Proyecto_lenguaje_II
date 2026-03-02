from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_usuario_telefono_alter_usuario_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='tipo_usuario',
            field=models.CharField(choices=[('estudiante', 'Estudiante'), ('profesor', 'Profesor')], default='estudiante', max_length=20),
        ),
    ]
