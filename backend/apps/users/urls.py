from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("senha/esqueci/", views.solicitar_reset_senha_view, name="senha-esqueci"),
    path("esqueci-senha/", views.esqueci_senha_view, name="esqueci-senha"),
    path("redefinir-senha/", views.redefinir_senha_view, name="redefinir-senha"),
    path("senha/redefinir/", views.confirmar_reset_senha_view, name="senha-redefinir"),
]
#declarando a rota de cada pagina