from datetime import timedelta

from django import template
from django.utils import timezone
from django.utils.timesince import timesince

from ..services import contar_nao_lidas, listar_recentes

register = template.Library()


@register.filter
def tempo_atras(data):
    """'agora mesmo' no primeiro minuto; depois 'há 5 minutos', 'há 2 horas'..."""
    if timezone.now() - data < timedelta(minutes=1):
        return "agora mesmo"
    return f"há {timesince(data)}"


@register.simple_tag(takes_context=True)
def notificacoes_nao_lidas(context):
    """
    Quantas notificações não lidas o usuário logado tem (0 se não estiver logado).
    Uso: {% notificacoes_nao_lidas as total %} e depois {% if total %}...{% endif %}
    """
    request = context.get("request")
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return 0
    return contar_nao_lidas(usuario)


@register.inclusion_tag("notificacoes/painel.html", takes_context=True)
def painel_notificacoes(context, limite=5):
    """
    Desenha o painel de notificações do usuário logado.
    Uso no template: {% load notificacoes_tags %} ... {% painel_notificacoes %}
    (ou {% painel_notificacoes limite=3 %} para mostrar menos itens)

    A tag busca os próprios dados, então a view da tela não precisa mudar.
    """
    request = context.get("request")
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {"autenticado": False}
    return {
        "autenticado": True,
        "notificacoes": listar_recentes(usuario, limite),
        "nao_lidas": contar_nao_lidas(usuario),
        "csrf_token": context.get("csrf_token"),  # o form de "marcar como lidas" precisa dele
    }