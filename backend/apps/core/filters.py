from django.db.models import Count, F, Q
from django.utils import timezone

from apps.treinos.models import Treino


def treinos_recomendados(usuario):
    modalidades_usuario = usuario.modalidades.all()

    return (
        Treino.objects
        .filter(
            modalidade__in=modalidades_usuario,
            data_hora__gt=timezone.now(),
        )
        .annotate(
            total_participantes=Count("inscricoes", distinct=True),
        )
        .annotate(
            vagas_restantes=F("limite_participantes") - F("total_participantes"),
        )
        .filter(
            Q(limite_participantes__isnull=True)
            | Q(total_participantes__lt=F("limite_participantes"))
        )
        .exclude(inscricoes__usuario=usuario)
        .distinct()
    )