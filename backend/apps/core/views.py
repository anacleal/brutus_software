from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.treinos.filters import proximos_treinos #funcao da BR-64 que separa os treinos futuros do usuario

# view do dashboard (tela inicial), monta a pagina com os dados do usuario logado
@login_required #exige que o usuario esteja logado pra acessar
def dashboard(request):
    return render(request, 'core/dashboard.html', {
        'proximos_treinos': proximos_treinos(request.user), #request.user e quem ta logado, no template vira a variavel proximos_treinos
    })
