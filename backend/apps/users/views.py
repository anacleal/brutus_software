from django.http import HttpResponse, JsonResponse
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import redirect, render
from django import forms
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache

from apps.modalidades.models import ModalidadeEsportiva
from apps.treinos.models import Treino

from .forms import UsuarioPerfilForm
from .services import SenhaInvalidaError, TokenInvalidoError, redefinir_senha, solicitar_reset_senha, token_esta_valido
from .validators import validar_dados_cadastro


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("dashboard")
        return render(request, "users/login.html", {"form": form}, status=401)

    form = AuthenticationForm(request)
    return render(request, "users/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def cadastro_view(request):
    modalidades = ModalidadeEsportiva.objects.order_by("nome")
    valores = request.POST if request.method == "POST" else {}

    if request.method == "GET":
        return render(
            request,
            "users/cadastro.html",
            {"modalidades": modalidades, "valores": valores},
        )

    dados = request.POST.dict()
    for campo in ("nome", "sobrenome", "email", "usuario"):
        dados[campo] = dados.get(campo, "").strip()
    dados["usuario"] = dados["usuario"].removeprefix("@")

    erros = validar_dados_cadastro(dados)
    modalidade = None
    if not any("modalidade_preferida" in erro for erro in erros):
        modalidade = modalidades.filter(
            pk=int(dados["modalidade_preferida"])
        ).first()
        if modalidade is None:
            erros.append("A modalidade selecionada não existe.")

    Usuario = get_user_model()
    email = Usuario.objects.normalize_email(dados.get("email", ""))
    if email and Usuario.objects.filter(email__iexact=email).exists():
        erros.append("Este e-mail já está cadastrado.")
    if dados.get("usuario") and Usuario.objects.filter(
        usuario__iexact=dados["usuario"]
    ).exists():
        erros.append("Este nome de usuário já está em uso.")

    foto = request.FILES.get("foto")
    foto_path = None
    foto_url = None
    if foto:
        extensao = Path(foto.name).suffix.lower()
        if extensao not in {".jpg", ".jpeg", ".png", ".webp"}:
            erros.append("Use uma foto JPG, JPEG, PNG ou WebP.")
        elif foto.size == 0:
            erros.append("O arquivo da foto está vazio.")
        elif foto.size > 5 * 1024 * 1024:
            erros.append("A foto deve ter no máximo 5 MB.")

    if erros:
        return render(
            request,
            "users/cadastro.html",
            {
                "modalidades": modalidades,
                "valores": valores,
                "erros": erros,
                "modalidade_selecionada": dados.get(
                    "modalidade_preferida", ""
                ),
            },
            status=400,
        )

    try:
        with transaction.atomic():
            if foto:
                foto_path = default_storage.save(
                    f"users/profile/{uuid4().hex}{extensao}",
                    foto,
                )
                foto_url = default_storage.url(foto_path)

            usuario = Usuario(
                nome=dados["nome"],
                sobrenome=dados["sobrenome"],
                email=email,
                usuario=dados["usuario"],
                cargo="atleta",
                e_socio=False,
                foto_perfil=foto_url,
            )
            usuario.set_password(dados["senha"])
            usuario.save()
            usuario.modalidades.add(modalidade)
    except Exception:
        if foto_path:
            default_storage.delete(foto_path)
        raise

    return redirect("login")


@login_required
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
    if request.method == "POST":
        form = UsuarioPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("perfil")
    else:
        form = UsuarioPerfilForm(instance=request.user)

    treinos_criados = request.user.treinos_criados.all()

    treinos_participados = Treino.objects.filter(
        inscricoes__usuario=request.user,
        inscricoes__presenca=True,
    )
    proximos_treinos = Treino.objects.filter(
        inscricoes__usuario=request.user,
        data_hora__gte=datetime.now(),
    )

    return render(
        request,
        "users/perfil.html",
        {
            "profile_user": request.user,
            "form": form,
            "created_trainings": treinos_criados,
            "participated_trainings": treinos_participados,
            "upcoming_trainings": proximos_treinos,
        },
    )
