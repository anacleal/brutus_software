from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOuUsuarioBackend(ModelBackend): #herda do backend padrao e so troca o authenticate
    def authenticate(self, request, username=None, password=None, **kwargs): #username aqui e o que a pessoa digitou, pode ser usuario ou e-mail
        User = get_user_model() #pega o modelo de usuario que o projeto usa
        usuario = User.objects.filter(
            Q(username=username) | Q(email__iexact=username) #procura pelo username ou pelo e-mail, o iexact ignora maiuscula e minuscula
        ).first() #se tiver duas contas com o mesmo e-mail pega so a primeira
        if usuario and usuario.check_password(password) and self.user_can_authenticate(usuario): #confere a senha e se a conta ta ativa
            return usuario
        return None #none faz a login_view mostrar a mensagem de erro
