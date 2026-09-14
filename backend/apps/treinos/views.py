from django.http import HttpResponse #httpresponse so pra view temporaria
from django.shortcuts import render


def treinos_view(request):
    return HttpResponse("Treinos")


def criar_treino_view(request):
    return HttpResponse("Criar treino")
#views provisorias de treinos, dps vai usar template
