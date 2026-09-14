from django.http import HttpResponse #usando httpsresponse so pra view temporaria
from django.contrib.auth.decorators import login_required 
from django.shortcuts import render

# view provisória do dashboard, dps vai usar template
@login_required #exige que o usuario esteja logado pra acessar
def dashboard(request):
    return HttpResponse("dashteste")