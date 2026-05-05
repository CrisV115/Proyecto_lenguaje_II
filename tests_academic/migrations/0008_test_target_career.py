from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tests_academic", "0007_alter_test_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="test",
            name="target_career",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
