from django.db import models


class Treino(models.Model):
    id = models.BigAutoField(primary_key=True)

    criador = models.ForeignKey(
        'users.Usuario',
        on_delete=models.CASCADE,
        related_name='treinos_criados'
    )

    modalidade = models.ForeignKey(
        'modalidades.ModalidadeEsportiva',
        on_delete=models.CASCADE,
        related_name='treinos'
    )

    fechado = models.BooleanField(default=False)

    limite_participantes = models.IntegerField(
        null=True,
        blank=True
    )

    local = models.CharField(max_length=100)

    data_hora = models.DateTimeField()

    duracao = models.IntegerField()

    custo = models.IntegerField(
        null=True,
        blank=True
    )

    observacoes = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.modalidade} - {self.local} - {self.data_hora}'

    class Meta:
        db_table = 'treinos'
        ordering = ['data_hora']


class InscricaoTreino(models.Model):
    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.CASCADE,
        related_name='inscricoes_treino'
    )

    treino = models.ForeignKey(
        Treino,
        on_delete=models.CASCADE,
        related_name='inscricoes'
    )

    presenca = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'inscricao_treino'

        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'treino'],
                name='usuario_treino_unico'
            )
        ]

    def __str__(self):
        return f'{self.usuario} - {self.treino}'