from django.http import HttpResponse #usando httpsresponse so pra view temporaria
from django.shortcuts import render

# view provisória do dashboard, dps vai usar template
def dashboard(request):
    return HttpResponse("dashteste")