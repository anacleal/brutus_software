from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django import forms
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from .services import SenhaInvalidaError, TokenInvalidoError, redefinir_senha, solicitar_reset_senha, token_esta_valido


def login_view(request):
    if request.method == 'POST': #GET mostra o formulario, POST confere usuario e senha
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid(): #confere se o usuario existe e se a senha bate
            login(request, form.get_user()) #cria a sessao que o @login_required confere depois
            next_url = request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('dashboard')
        return render(request, 'users/login.html', {'form': form}, status=401) #login errado volta a mesma pagina com a mensagem, mas com status 401 (nao autorizado)
    else:
        form = AuthenticationForm(request)
    return render(request, 'users/login.html', {'form': form})


def cadastro_view(request):
    return HttpResponse("Cadastro")

@login_required #exige que o usuario esteja logado pra acessar perfil, mas so no perfil pq os outros ele precisa de acesso
def perfil_view(request):
    return HttpResponse("Perfil")


#redefinir senha

MENSAGEM_GENERICA = (
    "Se o e-mail estiver cadastrado, voce recebera as instrucoes "
    "para redefinir sua senha."
)

class SolicitarResetSenhaForm(forms.Form):
    email = forms.EmailField()


@require_POST #so aceita POST: pedir reset gera um token, nao deve ser feito via GET
def solicitar_reset_senha_view(request):
    form = SolicitarResetSenhaForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'detail': 'E-mail invalido.'}, status=400) #formato invalido nao revela se o usuario existe
    solicitar_reset_senha(form.cleaned_data['email']) #gera e loga o token; o retorno nunca vai pra resposta
    return JsonResponse({'detail': MENSAGEM_GENERICA}) #mesma resposta exista o e-mail ou nao (anti-enumeracao)

def esqueci_senha_view(request):
    return render(request, 'users/esqueci_senha.html') #so mostra a tela; quem processa o e-mail e o endpoint solicitar_reset_senha_view

MENSAGEM_TOKEN_INVALIDO = "Link inválido ou expirado. Peça um novo link de redefinição."
 
 
class RedefinirSenhaForm(forms.Form):
    token = forms.CharField()
    nova_senha = forms.CharField(strip=False) #strip=False: espaco no comeco/fim faz parte da senha
    confirmacao = forms.CharField(strip=False)
 
    def clean(self):
        dados = super().clean()
        nova, confirmacao = dados.get('nova_senha'), dados.get('confirmacao')
        if nova and confirmacao and nova != confirmacao:
            self.add_error('confirmacao', 'As senhas não coincidem.')
        return dados
 
 
@never_cache #a URL carrega o token: a pagina nao pode ficar guardada em cache
def redefinir_senha_view(request):
    token = request.GET.get('token', '')
    return render(request, 'users/redefinir_senha.html', {
        'token': token,
        'token_valido': token_esta_valido(token), #se for invalido, a tela mostra o aviso em vez do formulario
    })
 
 
@require_POST
def confirmar_reset_senha_view(request):
    form = RedefinirSenhaForm(request.POST)
    if not form.is_valid():
        mensagens = [msg for erros in form.errors.values() for msg in erros]
        return JsonResponse({'detail': ' '.join(mensagens)}, status=400)
 
    try:
        redefinir_senha(form.cleaned_data['token'], form.cleaned_data['nova_senha'])
    except TokenInvalidoError:
        return JsonResponse({'detail': MENSAGEM_TOKEN_INVALIDO}, status=400) #mesma mensagem para inexistente, expirado e usado
    except SenhaInvalidaError as erro:
        return JsonResponse({'detail': ' '.join(erro.mensagens)}, status=400) #regras de senha do Django (tamanho, muito comum...)
 
    return JsonResponse({'detail': 'Senha alterada com sucesso! Você já pode entrar com a nova senha.'})