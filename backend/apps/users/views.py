from django.http import HttpResponse 
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


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