from django.http import HttpResponse #httpresponse so pra view temporaria
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required #exige que o usuario esteja logado pra acessar
def treinos_view(request):
    return HttpResponse("Treinos")

@login_required #exige que o usuario esteja logado pra acessar
def criar_treino_view(request):
    return HttpResponse("Criar treino")
#views provisorias de treinos, dps vai usar template
