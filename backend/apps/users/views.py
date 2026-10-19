from datetime import datetime

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.treinos.models import Treino

from .forms import UsuarioPerfilForm


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("dashboard")
        return render(request, "users/login.html", {"form": form}, status=401)

    form = AuthenticationForm(request)
    return render(request, "users/login.html", {"form": form})


def cadastro_view(request):
    return HttpResponse("Cadastro")


@login_required
def perfil_view(request):
    if request.method == "POST":
        form = UsuarioPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("perfil")
    else:
        form = UsuarioPerfilForm(instance=request.user)

    treinos_criados = request.user.treinos_criados.all()

    treinos_participados = Treino.objects.filter(
        inscricoes__usuario=request.user,
        inscricoes__presenca=True,
    )
    proximos_treinos = Treino.objects.filter(
        inscricoes__usuario=request.user,
        data_hora__gte=datetime.now(),
    )

    return render(
        request,
        "users/perfil.html",
        {
            "profile_user": request.user,
            "form": form,
            "created_trainings": treinos_criados,
            "participated_trainings": treinos_participados,
            "upcoming_trainings": proximos_treinos,
        },
    )