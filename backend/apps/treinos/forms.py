from datetime import datetime, time
import re

from django import forms
from django.utils import timezone


class TreinoCreateForm(forms.Form):
    nome = forms.CharField(
        max_length=100,
        error_messages={"required": "Informe o nome do treino."},
    )
    modalidade_id = forms.IntegerField(
        error_messages={"required": "Selecione uma modalidade."},
    )
    limite_participantes = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=200,
        error_messages={"required": "Informe o número de vagas."},
    )
    local = forms.CharField(
        max_length=100,
        error_messages={"required": "Informe o local do treino."},
    )
    data = forms.DateField(
        required=False,
        error_messages={"required": "Selecione a data do treino."},
    )
    horario = forms.CharField(
        required=False,
        max_length=5,
        error_messages={"required": "Informe o horário do treino."},
    )
    data_hora = forms.DateTimeField(required=False)
    duracao = forms.IntegerField(
        min_value=1,
        error_messages={"required": "Informe a duração do treino."},
    )
    custo = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=8,
        decimal_places=2,
    )
    observacoes = forms.CharField(required=False)
    acesso = forms.ChoiceField(
        required=False,
        choices=(("gratuito", "Gratuito"), ("pago", "Pago")),
        error_messages={"required": "Selecione o tipo de acesso."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get("_form_submission") == "1":
            self.fields["data"].required = True
            self.fields["horario"].required = True
            self.fields["limite_participantes"].required = True
            self.fields["acesso"].required = True

    def clean(self):
        cleaned_data = super().clean()
        data = cleaned_data.get("data")
        horario_texto = cleaned_data.get("horario")
        horario = None
        if horario_texto:
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", horario_texto):
                self.add_error(
                    "horario",
                    "Informe o horário no formato 00:00 a 23:59.",
                )
            else:
                horario = time.fromisoformat(horario_texto)
        data_hora = cleaned_data.get("data_hora")

        if data and horario:
            data_hora = datetime.combine(data, horario)
            if timezone.is_naive(data_hora):
                data_hora = timezone.make_aware(data_hora)
            cleaned_data["data_hora"] = data_hora
        elif data or horario_texto:
            if not data:
                self.add_error("data", "Selecione a data do treino.")
            if not horario_texto:
                self.add_error("horario", "Informe o horário do treino.")
        elif not data_hora:
            self.add_error("data_hora", "Informe a data e o horário do treino.")

        if data and data < timezone.localdate():
            self.add_error("data", "A data do treino não pode estar no passado.")

        if data_hora and data_hora <= timezone.now():
            erro_data_hora = "A data e hora do treino devem ser futuras."
            if data and data == timezone.localdate():
                self.add_error("horario", erro_data_hora)
            elif not data:
                self.add_error("data_hora", erro_data_hora)

        acesso = cleaned_data.get("acesso")
        custo = cleaned_data.get("custo")
        if acesso == "gratuito":
            cleaned_data["custo"] = 0
        elif acesso == "pago" and (custo is None or custo <= 0):
            self.add_error("custo", "Informe um valor válido.")

        return cleaned_data
