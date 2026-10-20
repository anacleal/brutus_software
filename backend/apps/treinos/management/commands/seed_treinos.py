from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.modalidades.models import ModalidadeEsportiva
from apps.treinos.models import InscricaoTreino, Treino
from apps.users.models import Usuario

MODALIDADES = ["Futsal", "Vôlei", "Basquete", "Handebol", "Natação"]

# (usuario, nome, sobrenome, e_socio)
USUARIOS = [
    ("seed_ana", "Ana", "Souza", True),
    ("seed_bruno", "Bruno", "Lima", True),
    ("seed_carla", "Carla", "Mendes", False),
    ("seed_diego", "Diego", "Rocha", True),
    ("seed_elisa", "Elisa", "Nunes", False),
    ("seed_felipe", "Felipe", "Alves", True),
    ("seed_gabi", "Gabriela", "Costa", False),
    ("seed_hugo", "Hugo", "Pires", True),
    ("seed_iris", "Íris", "Duarte", False),
    ("seed_joao", "João", "Teixeira", True),
]

# dias: deslocamento a partir de hoje | custo: None = sem valor cadastrado
# limite: None = sem limite | inscritos: quantos usuários seed se inscrevem
TREINOS = [
    dict(nome="Treino de Futsal Masculino", modalidade="Futsal", dias=2, hora=(19, 0),
         local="Ginásio Municipal", duracao=90, custo=10, limite=20, inscritos=8),
    dict(nome="Treino de Vôlei Feminino", modalidade="Vôlei", dias=3, hora=(18, 30),
         local="Quadra da Atlética", duracao=120, custo=None, limite=14, inscritos=5),
    dict(nome="Treino Aberto de Basquete", modalidade="Basquete", dias=5, hora=(20, 0),
         local="Quadra Coberta do Campus", duracao=60, custo=0, limite=None, inscritos=3),
    dict(nome="Treino de Handebol (lotado)", modalidade="Handebol", dias=1, hora=(17, 0),
         local="Ginásio Municipal", duracao=90, custo=15, limite=4, inscritos=4),
    dict(nome="Treino Técnico de Natação", modalidade="Natação", dias=7, hora=(7, 0),
        local="Piscina do Clube", duracao=60, custo=25, limite=10, inscritos=6),
    dict(nome="Treino sem inscritos", modalidade="Futsal", dias=4, hora=(21, 15),
         local="Quadra Externa", duracao=45, custo=5, limite=12, inscritos=0),
    dict(nome="Treino Preparatório Intercursos de Vôlei Misto com Nome Bem Longo",
         modalidade="Vôlei", dias=10, hora=(9, 0),
         local="Complexo Esportivo Universitário, Bloco C, Quadra 2", duracao=180,
         custo=30, limite=30, inscritos=10),
    dict(nome="Treino que já passou", modalidade="Basquete", dias=-1, hora=(19, 0),
         local="Quadra Coberta do Campus", duracao=60, custo=10, limite=15, inscritos=2),
]


class Command(BaseCommand):
    help = "Popula o banco com modalidades, usuários e treinos de teste (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        modalidades = {
            nome: ModalidadeEsportiva.objects.get_or_create(nome=nome)[0]
            for nome in MODALIDADES
        }

        usuarios = []
        for usuario, nome, sobrenome, e_socio in USUARIOS:
            obj, criado = Usuario.objects.get_or_create(
                usuario=usuario,
                defaults=dict(
                    nome=nome,
                    sobrenome=sobrenome,
                    email=f"{usuario}@seed.brutus",
                    e_socio=e_socio,
                ),
            )
            if criado:
                obj.set_password("senha12345")  # somente desenvolvimento
                obj.save()
            usuarios.append(obj)
        criador = usuarios[0]

        agora = timezone.localtime()
        self.stdout.write("\nTreinos para conferir com o card do dashboard:\n")
        for t in TREINOS:
            data_hora = (agora + timedelta(days=t["dias"])).replace(
                hour=t["hora"][0], minute=t["hora"][1], second=0, microsecond=0
            )
            treino, _ = Treino.objects.get_or_create(
                nome=t["nome"],
                modalidade=modalidades[t["modalidade"]],
                defaults=dict(
                    criador=criador,
                    local=t["local"],
                    data_hora=data_hora,
                    duracao=t["duracao"],
                    custo=t["custo"],
                    limite_participantes=t["limite"],
                ),
            )
            for u in usuarios[: t["inscritos"]]:
                InscricaoTreino.objects.get_or_create(
                    treino=treino, usuario=u, defaults=dict(presenca=False)
                )

            limite = treino.limite_participantes or "sem limite"
            inscritos = InscricaoTreino.objects.filter(treino=treino).count()
            self.stdout.write(
                f"- {treino.nome} | {treino.modalidade.nome} | "
                f"{timezone.localtime(treino.data_hora):%d/%m/%Y %H:%M} | "
                f"{treino.local} | {inscritos}/{limite} | custo: {treino.custo}"
            )

        self.stdout.write(self.style.SUCCESS("\nSeed concluído."))