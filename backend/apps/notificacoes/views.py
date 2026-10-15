from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from .services import marcar_todas_como_lidas


@login_required #so quem esta logado marca as proprias notificacoes
@require_POST #muda dados, entao nao pode ser feito por GET
def marcar_todas_lidas_view(request):
    marcadas = marcar_todas_como_lidas(request.user)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest': #chamado pelo JavaScript do painel: responde JSON, sem recarregar a pagina
        return JsonResponse({'marcadas': marcadas})
    return redirect('dashboard') #sem JavaScript: volta para a tela inicial