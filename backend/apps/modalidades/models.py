from django.db import models


class ModalidadeEsportiva(models.Model):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        db_table = 'modalidades_esportivas'
        

class TimeXModalidade(models.Model):
    id = models.BigAutoField(primary_key=True)

    jogador = models.ForeignKey(
        'users.Usuario',
        on_delete=models.CASCADE,
        related_name='times'
    )

    modalidade = models.ForeignKey(
        'ModalidadeEsportiva',
        on_delete=models.CASCADE,
        related_name='jogadores'
    )

    masculino_ou_feminino = models.CharField(max_length=10)

    class Meta:
        db_table = 'timexjogador'
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'jogador',
                    'modalidade',
                    'masculino_ou_feminino'
                ],
                name='jogador_modalidade_sexo_unico'
            )
        ]

    def __str__(self):
        return f'{self.jogador} - {self.modalidade} - {self.masculino_ou_feminino}'