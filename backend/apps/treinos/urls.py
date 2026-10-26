from django.urls import path

from . import views

urlpatterns = [ #lista de rotas
    path('treinos/', views.treinos_view, name='treinos'),
    path('treinos/criar/', views.criar_treino_view, name='criar_treino'),
]
#criar fica dentro de treinos/ pra agrupar as paginas de treino
