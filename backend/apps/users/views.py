from datetime import datetime

from .forms import UsuarioPerfilForm

from django.http import HttpResponse 
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect

from apps.users.models import Usuario
from apps.treinos.models import Treino


def login_view(request):
    if request.method == 'POST': #GET mostra o formulario, POST confere usuario e senha
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid(): #confere se o usuario existe e se a senha bate
            login(request, form.get_user()) #cria a sessao que o @login_required confere depois
            return redirect('dashboard')
        return render(request, 'users/login.html', {'form': form}, status=401) #login errado volta a mesma pagina com a mensagem, mas com status 401 (nao autorizado)
    else:
        form = AuthenticationForm(request)
    return render(request, 'users/login.html', {'form': form})


def cadastro_view(request):
    return HttpResponse("Cadastro")

@login_required #exige que o usuario esteja logado pra acessar perfil, mas so no perfil pq os outros ele precisa de acesso
def perfil_view(request):

    if request.method == 'POST':
            form = UsuarioPerfilForm(
                request.POST,
                instance=request.user
            )

            if form.is_valid():
                form.save()

                return redirect('perfil')

    else:
        form = UsuarioPerfilForm(instance=request.user)

    treinos_criados = request.user.treinos_criados.all()
    
    treinos_participados = Treino.objects.filter(
        inscricoes__usuario=request.user,
        inscricoes__presenca=True
    )
    proximos_treinos = Treino.objects.filter(
        inscricoes__usuario=request.user,
        data_hora__gte=datetime.now()
    )

    return render(request, 'users/perfil.html', {
        'profile_user': request.user,
        
        
        'form': form,
        
        'created_trainings': treinos_criados,
        'participated_trainings': treinos_participados,
        'upcoming_trainings': proximos_treinos
    })