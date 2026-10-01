from django.http import HttpResponse 
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.users.models import Usuario



def login_view(request):
    return HttpResponse("Login")


def cadastro_view(request):
    return HttpResponse("Cadastro")

# @login_required #exige que o usuario esteja logado pra acessar perfil, mas so no perfil pq os outros ele precisa de acesso
def perfil_view(request):

    usuario = Usuario.objects.get(usuario='teste')

    return render(request, 'users/perfil.html', {
        #'profile_user': request.user,
        'profile_user': usuario,
        'completed_trainings_count': 0,
        'created_trainings_count': 0,
        'upcoming_trainings_count': 0
    })