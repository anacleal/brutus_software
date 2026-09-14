from django.http import HttpResponse 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def login_view(request):
    return HttpResponse("Login")


def cadastro_view(request):
    return HttpResponse("Cadastro")

@login_required #exige que o usuario esteja logado pra acessar perfil, mas so no perfil pq os outros ele precisa de acesso
def perfil_view(request):
    return HttpResponse("Perfil")