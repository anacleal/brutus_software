import hashlib
import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from ..models import PasswordResetToken

# No teste, o Django troca o backend de e-mail por um em memória (mail.outbox):
# nada é enviado de verdade.


class EmailRedefinicaoTests(TestCase):
    def setUp(self):
        self.url = reverse("senha-esqueci")
        self.usuario = get_user_model().objects.create_user(
            email="ana@exemplo.com", username="ana", first_name="Ana"
        )

    def test_envia_email_com_link_valido(self):
        self.client.post(self.url, {"email": "ana@exemplo.com"})

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["ana@exemplo.com"])

        # o token do link tem que ser o mesmo cujo hash ficou no banco
        achado = re.search(r"/redefinir-senha/\?token=([\w-]+)", msg.body)
        self.assertIsNotNone(achado)
        token_hash = hashlib.sha256(achado.group(1).encode()).hexdigest()
        self.assertTrue(
            PasswordResetToken.objects.filter(
                usuario=self.usuario, token_hash=token_hash, used_at__isnull=True
            ).exists()
        )

    def test_email_inexistente_nao_envia_nada(self):
        self.client.post(self.url, {"email": "naoexiste@exemplo.com"})
        self.assertEqual(len(mail.outbox), 0)

    def test_falha_no_envio_nao_muda_a_resposta(self):
        ok = self.client.post(self.url, {"email": "naoexiste@exemplo.com"})
        with mock.patch(
            "apps.users.services.enviar_email_redefinicao", side_effect=Exception("smtp fora do ar")
        ):
            with self.assertLogs("apps.users.services", level="ERROR"):
                falhou = self.client.post(self.url, {"email": "ana@exemplo.com"})
        # mesma resposta de antes: quem olha de fora não percebe que a conta existe
        self.assertEqual(falhou.status_code, ok.status_code)
        self.assertEqual(falhou.json(), ok.json())