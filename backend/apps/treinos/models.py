from django.conf import settings
from django.db import models


class ModalidadeEsportiva(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "modalidades_esportivas"

    def __str__(self):
        return self.nome


class Treino(models.Model):
    id = models.AutoField(primary_key=True)
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="criador",
        on_delete=models.PROTECT,
        related_name="treinos_criados",
    )
    modalidade = models.ForeignKey(
        ModalidadeEsportiva,
        db_column="modalidade_id",
        on_delete=models.PROTECT,
        related_name="treinos",
    )
    nome = models.CharField(max_length=100)
    limite_participantes = models.IntegerField(blank=True, null=True)
    local = models.CharField(max_length=100)
    data_hora = models.DateTimeField()
    duracao = models.IntegerField()
    custo = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    observacoes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "treinos"

    def __str__(self):
        return self.nome
