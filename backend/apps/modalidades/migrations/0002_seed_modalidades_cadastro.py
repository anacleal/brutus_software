from django.db import migrations


NOMES_MODALIDADES = (
    "Musculação",
    "Futebol",
    "Basquete",
    "Vôlei",
    "Natação",
    "Judô",
    "Atletismo",
    "Handebol",
    "Tênis",
    "CrossFit",
)


def criar_modalidades(apps, schema_editor):
    modalidade = apps.get_model("modalidades", "ModalidadeEsportiva")
    for nome in NOMES_MODALIDADES:
        modalidade.objects.get_or_create(nome=nome)


class Migration(migrations.Migration):

    dependencies = [
        ("modalidades", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(criar_modalidades, migrations.RunPython.noop),
    ]
