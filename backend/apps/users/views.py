from django.http import HttpResponse 
from django.shortcuts import render


def login_view(request):
    return HttpResponse("Login")


def cadastro_view(request):
    return HttpResponse("Cadastro")


def perfil_view(request):
    return HttpResponse("Perfil")