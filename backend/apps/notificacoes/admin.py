from django.contrib import admin

from .models import Notificacao


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "criada_em", "lida_em")
    list_filter = ("criada_em",)
    search_fields = ("titulo", "usuario__username", "usuario__email")
    raw_id_fields = ("usuario",)  # evita carregar todos os usuários num select