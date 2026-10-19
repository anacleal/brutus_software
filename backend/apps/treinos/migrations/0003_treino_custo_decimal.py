from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("treinos", "0002_treino_nome"),
    ]

    operations = [
        migrations.AlterField(
            model_name="treino",
            name="custo",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
            ),
        ),
    ]
