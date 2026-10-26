from django.urls import path #

from . import views

urlpatterns = [ #lista de rotas
    path('dashboard/', views.dashboard, name='dashboard'),
]
#dashboard/ -> endereço na url
#views.dashboard -> é a funcao
#name -> apelido da rota