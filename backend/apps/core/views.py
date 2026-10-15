from django.contrib.auth.decorators import login_required 
from django.shortcuts import render

from .filters import treinos_recomendados

# view provisória do dashboard, dps vai usar template
@login_required
def dashboard(request):
    usuario = request.user

    context = {
        'treinos_recomendados': treinos_recomendados(usuario),
    }

    return render(request,'core/dashboard.html',context)