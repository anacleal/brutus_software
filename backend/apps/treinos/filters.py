from django.utils import timezone #timezone.now() ja vem com o fuso de brasilia, o datetime.now() da aviso de naive datetime

from .models import Treino


def proximos_treinos(usuario): #devolve os treinos futuros em que o usuario ta inscrito, pra usar no dashboard
    return Treino.objects.filter(
        inscricoes__usuario=usuario, #o __ atravessa a relacao, entao so treinos que tem inscricao desse usuario
        data_hora__gt=timezone.now(), #gt = maior que, entao so treinos que ainda nao aconteceram
    ).order_by('data_hora') #a ordem do mais proximo pro mais longe ja vem do ordering = ['data_hora'] do model


def treinos_disponiveis():
    return (
        Treino.objects.filter(data_hora__gt=timezone.now())
        .select_related('modalidade', 'criador')
        .prefetch_related('inscricoes')
        .order_by('data_hora')
    )


def treinos_encerrados():
    return (
        Treino.objects.filter(data_hora__lte=timezone.now())
        .select_related('modalidade', 'criador')
        .prefetch_related('inscricoes')
        .order_by('-data_hora')
    )
