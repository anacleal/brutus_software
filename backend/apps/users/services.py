import hashlib
import logging
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import PasswordResetToken

logger = logging.getLogger(__name__)

TOKEN_TTL = timedelta(minutes=30)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def solicitar_reset_senha(email: str) -> str | None:
    """
    Gera um token de redefinição para o usuário dono do e-mail.
    Retorna o token (texto puro) ou None se o e-mail não existir.
    O chamador NUNCA deve expor esse retorno ao cliente.
    """
    User = get_user_model()
    usuario = User.objects.filter(email__iexact=email).first()
    if usuario is None:
        return None

    # Invalida tokens anteriores ainda não usados: só o mais recente vale.
    PasswordResetToken.objects.filter(
        usuario=usuario, used_at__isnull=True
    ).update(used_at=timezone.now())

    token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(
        usuario=usuario,
        token_hash=_hash_token(token),
        expires_at=timezone.now() + TOKEN_TTL,
    )

    # TODO (sprint futura): trocar o log pelo envio real de e-mail.
    logger.info("Token de redefinição para usuario_id=%s: %s", usuario.pk, token)
    return token