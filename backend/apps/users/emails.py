from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

def montar_link_redefinicao(token: str) -> str:
    return f"{settings.SITE_URL}{reverse('redefinir-senha')}?token={token}"

def enviar_email_redefinicao(usuario, token: str) -> None:
    """Envia ao usuário o link para redefinir a senha. Levanta exceção se o envio falhar."""
    corpo = render_to_string(
        "users/email/redefinir_senha.txt",
        {"usuario": usuario, "link": montar_link_redefinicao(token)},
    )
    if settings.DEBUG:  # só em desenvolvimento: o console mostra o e-mail codificado
        logger.warning("Link de redefinição (só em DEBUG): %s", montar_link_redefinicao(token))
    EmailMessage(
        subject="Redefinição de senha - Brutus",
        body=corpo,
        to=[usuario.email],  # from_email omitido: usa DEFAULT_FROM_EMAIL
    ).send()