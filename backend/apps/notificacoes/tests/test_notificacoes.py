from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template import RequestContext, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .. import services
from ..models import Notificacao
from ..templatetags.notificacoes_tags import tempo_atras


def criar_usuario(nome):
    return get_user_model().objects.create_user(
        usuario=nome,
        email=f"{nome}@exemplo.com",
        nome=nome,
        sobrenome="Teste",
        e_socio=False,
        password="Senha#12345",
    )


class BaseNotificacoes(TestCase):
    def setUp(self):
        self.ana = criar_usuario("ana")
        self.bia = criar_usuario("bia")


class ServicesTests(BaseNotificacoes):
    def test_notificacao_nasce_nao_lida(self):
        n = services.criar_notificacao(self.ana, "Treino confirmado", "Sábado, 8h", url="/treinos/")
        self.assertFalse(n.lida)
        self.assertEqual(services.contar_nao_lidas(self.ana), 1)

    def test_url_externa_e_recusada(self):
        for url in ("https://exemplo.com", "//exemplo.com", "javascript:alert(1)"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    services.criar_notificacao(self.ana, "x", url=url)
        self.assertEqual(Notificacao.objects.count(), 0)

    def test_listar_recentes_vem_do_mais_novo_com_limite(self):
        for i in range(7):
            services.criar_notificacao(self.ana, f"n{i}")
        titulos = [n.titulo for n in services.listar_recentes(self.ana, limite=5)]
        self.assertEqual(titulos, ["n6", "n5", "n4", "n3", "n2"])

    def test_so_lista_as_do_proprio_usuario(self):
        services.criar_notificacao(self.ana, "da ana")
        services.criar_notificacao(self.bia, "da bia")
        self.assertEqual([n.titulo for n in services.listar_recentes(self.ana)], ["da ana"])

    def test_marcar_todas_como_lidas_so_afeta_o_usuario(self):
        services.criar_notificacao(self.ana, "a1")
        services.criar_notificacao(self.ana, "a2")
        services.criar_notificacao(self.bia, "b1")

        marcadas = services.marcar_todas_como_lidas(self.ana)

        self.assertEqual(marcadas, 2)
        self.assertEqual(services.contar_nao_lidas(self.ana), 0)
        self.assertEqual(services.contar_nao_lidas(self.bia), 1)

    def test_notificar_varios(self):
        services.notificar_varios([self.ana, self.bia], "Treino cancelado")
        self.assertEqual(Notificacao.objects.filter(titulo="Treino cancelado").count(), 2)


class PainelTests(BaseNotificacoes):
    def renderizar(self, usuario):
        request = RequestFactory().get("/")
        request.user = usuario
        modelo = Template("{% load notificacoes_tags %}{% painel_notificacoes %}")
        return modelo.render(RequestContext(request))

    def test_sem_notificacoes_informa_que_esta_vazio(self):  # critério 4
        html = self.renderizar(self.ana)
        self.assertIn("Você não tem notificações no momento.", html)
        self.assertNotIn("Marcar todas como lidas", html)
        self.assertNotIn("notificacoes__contador", html)

    def test_mostra_notificacoes_e_indicador(self):  # critérios 1 e 2
        services.criar_notificacao(self.ana, "Treino de sábado confirmado", "Quadra 2, 8h")
        services.criar_notificacao(self.ana, "Vaga liberada no treino de quinta")
        html = self.renderizar(self.ana)
        self.assertIn("Treino de sábado confirmado", html)
        self.assertIn("Quadra 2, 8h", html)
        self.assertIn("Vaga liberada no treino de quinta", html)
        self.assertIn('class="notificacoes__contador"', html)
        self.assertIn("Marcar todas como lidas", html)
        self.assertNotIn("Você não tem notificações", html)

    def test_so_mostra_as_do_proprio_usuario(self):  # critério 3
        services.criar_notificacao(self.ana, "Aviso da Ana")
        services.criar_notificacao(self.bia, "Aviso da Bia")
        html = self.renderizar(self.ana)
        self.assertIn("Aviso da Ana", html)
        self.assertNotIn("Aviso da Bia", html)

    def test_lidas_continuam_visiveis_mas_nao_contam_no_indicador(self):
        services.criar_notificacao(self.ana, "Aviso antigo")
        services.marcar_todas_como_lidas(self.ana)
        html = self.renderizar(self.ana)
        self.assertIn("Aviso antigo", html)
        self.assertNotIn("notificacoes__contador", html)
        self.assertNotIn("notificacao--nova", html)

    def test_titulo_e_escapado(self):
        services.criar_notificacao(self.ana, "<script>alert(1)</script>")
        html = self.renderizar(self.ana)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_titulo_vira_link_quando_tem_url(self):
        services.criar_notificacao(self.ana, "Ver treino", url="/treinos/")
        self.assertIn('<a href="/treinos/">Ver treino</a>', self.renderizar(self.ana))

    def test_usuario_anonimo_nao_ve_painel(self):
        self.assertEqual(self.renderizar(AnonymousUser()).strip(), "")

    def test_painel_vem_fechado_e_com_os_ganchos_do_javascript(self):
        services.criar_notificacao(self.ana, "a1")
        html = self.renderizar(self.ana)
        self.assertRegex(html, r'<section[^>]*id="notificacoes-painel"[^>]*\bhidden\b')
        self.assertIn("data-notificacoes-marcar-lidas", html)
        self.assertIn("notificacoes/js/notificacoes.js", html)

    def test_tempo_atras(self):
        from datetime import timedelta
        agora = timezone.now()
        self.assertEqual(tempo_atras(agora), "agora mesmo")
        self.assertEqual(tempo_atras(agora - timedelta(minutes=5, seconds=1)).replace("\xa0", " "), "há 5 minutos")
        self.assertEqual(tempo_atras(agora - timedelta(hours=2, seconds=1)).replace("\xa0", " "), "há 2 horas")

    def test_tag_nao_lidas_conta_so_as_pendentes_do_usuario(self):
        services.criar_notificacao(self.ana, "a1")
        services.criar_notificacao(self.ana, "a2")
        services.criar_notificacao(self.bia, "b1")
        modelo = Template("{% load notificacoes_tags %}{% notificacoes_nao_lidas as total %}[{{ total }}]")

        def renderizar(usuario):
            request = RequestFactory().get("/")
            request.user = usuario
            return modelo.render(RequestContext(request))

        self.assertEqual(renderizar(self.ana), "[2]")
        services.marcar_todas_como_lidas(self.ana)
        self.assertEqual(renderizar(self.ana), "[0]")
        self.assertEqual(renderizar(AnonymousUser()), "[0]")


class MarcarLidasViewTests(BaseNotificacoes):
    def setUp(self):
        super().setUp()
        self.url = reverse("notificacoes-marcar-lidas")

    def test_exige_login(self):
        services.criar_notificacao(self.ana, "a1")
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith(reverse("login")))
        self.assertEqual(services.contar_nao_lidas(self.ana), 1)

    def test_post_marca_as_do_usuario_logado_e_volta_para_a_tela_inicial(self):
        services.criar_notificacao(self.ana, "a1")
        services.criar_notificacao(self.bia, "b1")
        self.client.force_login(self.ana)

        resp = self.client.post(self.url)

        self.assertRedirects(resp, reverse("dashboard"), fetch_redirect_response=False)
        self.assertEqual(services.contar_nao_lidas(self.ana), 0)
        self.assertEqual(services.contar_nao_lidas(self.bia), 1)

    def test_chamada_por_javascript_recebe_json_e_nao_redireciona(self):
        services.criar_notificacao(self.ana, "a1")
        services.criar_notificacao(self.ana, "a2")
        self.client.force_login(self.ana)

        resp = self.client.post(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"marcadas": 2})
        self.assertEqual(services.contar_nao_lidas(self.ana), 0)

    def test_get_nao_permitido(self):
        self.client.force_login(self.ana)
        self.assertEqual(self.client.get(self.url).status_code, 405)


class TelaInicialTests(BaseNotificacoes):
    def test_tela_inicial_tem_a_area_de_notificacoes(self):  # critério 1
        # Este teste só passa depois que você incluir {% painel_notificacoes %}
        # no template da tela inicial (veja as instruções de integração).
        self.client.force_login(self.ana)
        resp = self.client.get(reverse("dashboard"))
        self.assertContains(resp, 'id="titulo-notificacoes"')
        self.assertContains(resp, "Você não tem notificações no momento.")