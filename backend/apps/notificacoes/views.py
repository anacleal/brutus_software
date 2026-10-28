from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST

from .services import contar_nao_lidas, listar_todas, marcar_todas_como_lidas


@require_GET
def listar_notificacoes_view(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'message': 'É necessário estar autenticado para ver as notificações.'},
            status=401,
        )
    notificacoes = [
        {
            'id': n.id,
            'titulo': n.titulo,
            'mensagem': n.mensagem,
            'url': n.url,
            'criada_em': n.criada_em.isoformat(),
            'lida': n.lida,
        }
        for n in listar_todas(request.user)
    ]
    return JsonResponse({
        'nao_lidas': contar_nao_lidas(request.user),
        'notificacoes': notificacoes,
    })


@login_required #so quem esta logado marca as proprias notificacoes
@require_POST #muda dados, entao nao pode ser feito por GET
def marcar_todas_lidas_view(request):
    marcadas = marcar_todas_como_lidas(request.user)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest': #chamado pelo JavaScript do painel: responde JSON, sem recarregar a pagina
        return JsonResponse({'marcadas': marcadas})
    return redirect('dashboard') #sem JavaScript: volta para a tela inicial