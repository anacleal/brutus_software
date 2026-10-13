import hashlib
import logging
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import PasswordResetToken

from .emails import enviar_email_redefinicao

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

    try:
        enviar_email_redefinicao(usuario, token)
    except Exception:
        # falha de envio nao pode virar erro 500: a resposta seria diferente da do
        # e-mail inexistente e revelaria que a conta existe
        logger.exception("Falha ao enviar e-mail de redefinição para usuario_id=%s", usuario.pk)
    return token

class TokenInvalidoError(Exception):
    """Token inexistente, expirado ou já usado (de propósito, sem dizer qual dos três)."""
 
 
class SenhaInvalidaError(Exception):
    """A nova senha não passou nos validadores de senha do Django."""
 
    def __init__(self, mensagens: list[str]):
        super().__init__(" ".join(mensagens))
        self.mensagens = mensagens
 
 
def _tokens_validos(token: str):
    """Tokens que ainda valem: o hash confere, não foi usado e não expirou."""
    return PasswordResetToken.objects.filter(
        token_hash=_hash_token(token),
        used_at__isnull=True,
        expires_at__gt=timezone.now(),
    )
 
 
def token_esta_valido(token: str) -> bool:
    """Usado pela tela para decidir entre mostrar o formulário ou o aviso de link inválido."""
    return bool(token) and _tokens_validos(token).exists()
 
 
def redefinir_senha(token: str, nova_senha: str) -> None:
    """
    Troca a senha do dono do token.
    Levanta TokenInvalidoError (token inexistente/expirado/usado) ou SenhaInvalidaError.
    """
    with transaction.atomic():
        # select_for_update trava a linha do token até o fim da transação: se dois
        # pedidos usarem o mesmo link ao mesmo tempo, só um passa (no SQLite é ignorado).
        registro = _tokens_validos(token).select_for_update().first() if token else None
        if registro is None:
            raise TokenInvalidoError
 
        usuario = registro.usuario
        try:
            validate_password(nova_senha, user=usuario)
        except ValidationError as erro:
            # sai sem consumir o token: a pessoa pode tentar de novo com outra senha
            raise SenhaInvalidaError(erro.messages) from erro
 
        usuario.set_password(nova_senha)  # guarda o hash, nunca a senha em texto puro
        usuario.save(update_fields=["password"])
 
        # consome este token e qualquer outro que ainda esteja pendente
        PasswordResetToken.objects.filter(
            usuario=usuario, used_at__isnull=True
        ).update(used_at=timezone.now())
 
    logger.info("Senha redefinida para usuario_id=%s", usuario.pk)