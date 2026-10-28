from django.urls import path

from . import views

urlpatterns = [
    path('notificacoes/', views.listar_notificacoes_view, name='notificacoes'),
    path('notificacoes/lidas/', views.marcar_todas_lidas_view, name='notificacoes-marcar-lidas'),
]
