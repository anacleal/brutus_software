from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import PasswordResetToken
from ..services import solicitar_reset_senha

SENHA_ANTIGA = "SenhaAntiga#123"
SENHA_NOVA = "NovaSenhaBrutus#2026"


class RedefinirSenhaBase(TestCase):
    def setUp(self):
        self.url_tela = reverse("redefinir-senha")
        self.url_endpoint = reverse("senha-redefinir")
        self.usuario = get_user_model().objects.create_user(
            usuario="ana", email="ana@exemplo.com", nome="Ana", sobrenome="S", e_socio=False, password=SENHA_ANTIGA
        )
        # o service devolve o token em texto puro (o banco guarda só o hash)
        self.token = solicitar_reset_senha("ana@exemplo.com")

    def enviar(self, token=None, nova=SENHA_NOVA, confirmacao=None):
        return self.client.post(
            self.url_endpoint,
            {
                "token": self.token if token is None else token,
                "nova_senha": nova,
                "confirmacao": nova if confirmacao is None else confirmacao,
            },
        )

    def senha_atual_e(self, senha):
        self.usuario.refresh_from_db()
        return self.usuario.check_password(senha)


class TelaRedefinirSenhaTests(RedefinirSenhaBase):
    def test_token_valido_mostra_formulario(self):
        resp = self.client.get(self.url_tela, {"token": self.token})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "users/redefinir_senha.html")
        self.assertContains(resp, f'action="{self.url_endpoint}"')
        self.assertContains(resp, 'name="nova_senha"')
        self.assertContains(resp, f'name="token" value="{self.token}"')
        self.assertContains(resp, "csrfmiddlewaretoken")

    def test_token_invalido_mostra_aviso_sem_formulario(self):
        resp = self.client.get(self.url_tela, {"token": "token-que-nao-existe"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Link inválido ou expirado")
        self.assertNotContains(resp, 'name="nova_senha"')

    def test_sem_token_mostra_aviso_sem_formulario(self):
        resp = self.client.get(self.url_tela)
        self.assertContains(resp, "Link inválido ou expirado")
        self.assertNotContains(resp, 'name="nova_senha"')

    def test_token_expirado_mostra_aviso(self):
        PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        resp = self.client.get(self.url_tela, {"token": self.token})
        self.assertContains(resp, "Link inválido ou expirado")
        self.assertNotContains(resp, 'name="nova_senha"')


class ConfirmarResetSenhaTests(RedefinirSenhaBase):
    def test_troca_a_senha_e_consome_o_token(self):
        resp = self.enviar()
        self.assertEqual(resp.status_code, 200)

        self.assertTrue(self.senha_atual_e(SENHA_NOVA))
        self.assertFalse(self.senha_atual_e(SENHA_ANTIGA))
        self.assertFalse(PasswordResetToken.objects.filter(used_at__isnull=True).exists())
        # e dá para entrar com a senha nova pela tela de login (backend por usuário ou e-mail)
        self.assertTrue(Client().login(username="ana", password=SENHA_NOVA))

    def test_token_nao_pode_ser_reutilizado(self):
        self.enviar()
        resp = self.enviar(nova="OutraSenhaBrutus#2026")
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(self.senha_atual_e(SENHA_NOVA))  # continua a primeira troca

    def test_token_expirado_e_recusado(self):
        PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        resp = self.enviar()
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(self.senha_atual_e(SENHA_ANTIGA))

    def test_token_inexistente_e_recusado(self):
        resp = self.enviar(token="token-que-nao-existe")
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(self.senha_atual_e(SENHA_ANTIGA))

    def test_senha_fraca_e_recusada_sem_gastar_o_token(self):
        resp = self.enviar(nova="123")
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(self.senha_atual_e(SENHA_ANTIGA))
        # o token continua valendo: a pessoa pode tentar de novo
        self.assertTrue(PasswordResetToken.objects.filter(used_at__isnull=True).exists())
        self.assertEqual(self.enviar().status_code, 200)

    def test_confirmacao_diferente_e_recusada(self):
        resp = self.enviar(confirmacao="OutraCoisa#123")
        self.assertEqual(resp.status_code, 400)
        self.assertTrue(self.senha_atual_e(SENHA_ANTIGA))
        self.assertTrue(PasswordResetToken.objects.filter(used_at__isnull=True).exists())

    def test_get_nao_permitido(self):
        self.assertEqual(self.client.get(self.url_endpoint).status_code, 405)

    def test_sessoes_abertas_caem_depois_da_troca(self):
        outro_aparelho = Client()
        outro_aparelho.force_login(self.usuario)
        self.assertEqual(outro_aparelho.get(reverse("perfil")).status_code, 200)

        self.enviar()

        # o hash da sessão depende do hash da senha: trocar a senha derruba as sessões antigas
        resp = outro_aparelho.get(reverse("perfil"))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith(reverse("login")))