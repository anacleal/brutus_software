from django import forms

from .models import Usuario
from apps.modalidades.models import ModalidadeEsportiva


class UsuarioPerfilForm(forms.ModelForm):

    modalidades = forms.ModelMultipleChoiceField(
        queryset=ModalidadeEsportiva.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Usuario
        fields = [
            'nome',
            'sobrenome',
            'email',
            'usuario',
            'modalidades',
        ]