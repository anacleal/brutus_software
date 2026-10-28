from django.utils import timezone

from .models import Notificacao


def _validar_url(url: str) -> None:
    """A url vira um link na tela: só aceitamos caminhos internos (ex.: /treinos/)."""
    if url and (not url.startswith("/") or url.startswith("//")):
        raise ValueError("A url da notificação deve ser um caminho interno, como /treinos/.")


def criar_notificacao(usuario, titulo: str, mensagem: str = "", url: str = "") -> Notificacao:
    """Cria uma notificação para um usuário. É esta função que o resto do projeto deve chamar."""
    _validar_url(url)
    return Notificacao.objects.create(usuario=usuario, titulo=titulo, mensagem=mensagem, url=url)


def notificar_varios(usuarios, titulo: str, mensagem: str = "", url: str = "") -> list[Notificacao]:
    """Mesma notificação para vários usuários (ex.: todos os inscritos em um treino), numa só consulta."""
    _validar_url(url)
    return Notificacao.objects.bulk_create(
        [Notificacao(usuario=u, titulo=titulo, mensagem=mensagem, url=url) for u in usuarios]
    )


def listar_recentes(usuario, limite: int = 5) -> list[Notificacao]:
    """As notificações mais recentes do usuário (lidas e não lidas)."""
    return list(Notificacao.objects.filter(usuario=usuario)[:limite])


def listar_todas(usuario) -> list[Notificacao]:
    return list(Notificacao.objects.filter(usuario=usuario))


def contar_nao_lidas(usuario) -> int:
    return Notificacao.objects.filter(usuario=usuario, lida_em__isnull=True).count()


def marcar_todas_como_lidas(usuario) -> int:
    """Marca como lidas todas as pendentes do usuário. Devolve quantas foram marcadas."""
    return Notificacao.objects.filter(usuario=usuario, lida_em__isnull=True).update(
        lida_em=timezone.now()
    )