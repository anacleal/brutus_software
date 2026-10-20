# urls.py (users):
#   path("senha/esqueci/", views.solicitar_reset_senha_view, name="senha-esqueci")

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from ..models import PasswordResetToken


class SolicitarResetSenhaTests(TestCase):
    def setUp(self):
        self.url = reverse("senha-esqueci")
        # Ajuste a criação conforme o seu modelo `usuarios`
        self.usuario = get_user_model().objects.create_user(
            email="ana@exemplo.com", username="ana", first_name="Ana", last_name="S"
        )

    def test_email_existente_gera_token_vinculado(self):
        resp = self.client.post(self.url, {"email": "ana@exemplo.com"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(PasswordResetToken.objects.filter(usuario=self.usuario).count(), 1)

    def test_email_inexistente_retorna_mesma_resposta(self):
        ok = self.client.post(self.url, {"email": "ana@exemplo.com"})
        nok = self.client.post(self.url, {"email": "naoexiste@exemplo.com"})
        self.assertEqual(nok.status_code, ok.status_code)
        self.assertEqual(nok.json(), ok.json())
        self.assertEqual(PasswordResetToken.objects.count(), 1)

    def test_email_invalido_retorna_400(self):
        resp = self.client.post(self.url, {"email": "isso-nao-e-email"})
        self.assertEqual(resp.status_code, 400)

    def test_get_nao_permitido(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_novo_pedido_invalida_token_anterior(self):
        for _ in range(2):
            self.client.post(self.url, {"email": "ana@exemplo.com"})
        validos = PasswordResetToken.objects.filter(used_at__isnull=True).count()
        self.assertEqual(validos, 1)