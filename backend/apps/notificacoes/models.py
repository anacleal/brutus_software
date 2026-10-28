from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


class Notificacao(models.Model):
    """Aviso para um usuário. Fica 'não lida' enquanto lida_em estiver vazio."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    titulo = models.CharField(max_length=120)
    mensagem = models.CharField(max_length=255, blank=True)
    url = models.CharField(
        max_length=200,
        blank=True,
        help_text="Caminho interno (começa com /) aberto ao clicar no título.",
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notificacoes"
        verbose_name = "notificação"
        verbose_name_plural = "notificações"
        ordering = ["-criada_em", "-id"]  # mais recentes primeiro; o id desempata
        indexes = [models.Index(fields=["usuario", "lida_em"])]

    @property
    def lida(self) -> bool:
        return self.lida_em is not None

    def __str__(self):
        return f"{self.titulo} (usuário {self.usuario_id})"


@receiver(post_save, sender="treinos.InscricaoTreino")
def notificar_novo_participante(sender, instance, created, **kwargs):
    treino = instance.treino
    if not created or treino.criador_id == instance.usuario_id:
        return
    Notificacao.objects.create(
        usuario=treino.criador,
        titulo="Novo participante no seu treino",
        mensagem=f"{instance.usuario.nome} se inscreveu em {treino.nome}"[:255],
        url=reverse("treinos"),
    )