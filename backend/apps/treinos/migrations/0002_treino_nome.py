from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("treinos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="treino",
            name="nome",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
    ]
