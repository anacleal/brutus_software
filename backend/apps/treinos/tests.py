import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.modalidades.models import ModalidadeEsportiva

from .models import InscricaoTreino, Treino


class CriarTreinoEndpointTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.criador = user_model.objects.create_user(
            usuario="criador",
            email="criador@exemplo.com",
            nome="Criador",
            sobrenome="Teste",
            e_socio=False,
            password="senha-segura",
        )
        self.outro_usuario = user_model.objects.create_user(
            usuario="outro",
            email="outro@exemplo.com",
            nome="Outro",
            sobrenome="Teste",
            e_socio=False,
            password="senha-segura",
        )
        self.modalidade = ModalidadeEsportiva.objects.create(nome="Futebol")
        self.client.force_login(self.criador)
        self.url = "/treinos/criar/"
        self.dados = {
            "nome": "Treino de futebol",
            "modalidade_id": self.modalidade.id,
            "limite_participantes": 10,
            "local": "Quadra principal",
            "data_hora": (timezone.now() + timedelta(days=1)).isoformat(),
            "duracao": 90,
            "custo": 0,
            "observacoes": "Levar chuteira",
        }

    def test_cria_treino_e_vincula_usuario_autenticado(self):
        dados = {**self.dados, "criador": self.outro_usuario.id}

        response = self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        treino = Treino.objects.get()
        self.assertEqual(treino.criador, self.criador)
        self.assertEqual(treino.modalidade, self.modalidade)
        self.assertEqual(treino.nome, "Treino de futebol")
        self.assertEqual(treino.limite_participantes, 10)
        self.assertEqual(treino.local, "Quadra principal")
        self.assertEqual(treino.duracao, 90)
        self.assertEqual(treino.custo, 0)
        self.assertEqual(treino.observacoes, "Levar chuteira")
        self.assertEqual(response.json()["treino"]["criador"], self.criador.id)
        self.assertEqual(response.json()["treino"]["custo"], 0)

    def test_aceita_dados_de_formulario_e_valores_opcionais_ausentes(self):
        dados = {
            "nome": "Treino de futebol",
            "modalidade_id": self.modalidade.id,
            "local": "Quadra principal",
            "data_hora": self.dados["data_hora"],
            "duracao": 60,
        }

        response = self.client.post(self.url, data=dados)

        self.assertEqual(response.status_code, 201)
        treino = Treino.objects.get()
        self.assertIsNone(treino.limite_participantes)
        self.assertIsNone(treino.custo)
        self.assertIsNone(treino.observacoes)

    def test_aceita_valores_nulos_para_custo_e_limite_opcionais(self):
        dados = {
            **self.dados,
            "limite_participantes": None,
            "custo": None,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        treino = Treino.objects.get()
        self.assertIsNone(treino.limite_participantes)
        self.assertIsNone(treino.custo)

    def test_retorna_erros_claros_para_campos_obrigatorios_ausentes(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"modalidade_id": self.modalidade.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("local", errors)
        self.assertIn("data_hora", errors)
        self.assertIn("duracao", errors)
        self.assertEqual(Treino.objects.count(), 0)

    def test_rejeita_modalidade_inexistente_e_valores_invalidos(self):
        dados = {
            **self.dados,
            "modalidade_id": 9999,
            "duracao": 0,
            "custo": -1,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("modalidade_id", errors)
        self.assertIn("duracao", errors)
        self.assertIn("custo", errors)
        self.assertEqual(Treino.objects.count(), 0)

    def test_rejeita_limite_negativo(self):
        dados = {**self.dados, "limite_participantes": -1}

        response = self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("limite_participantes", response.json()["errors"])
        self.assertEqual(Treino.objects.count(), 0)

    def test_rejeita_duracao_negativa_ou_nula(self):
        for duracao in (-1, 0, None):
            with self.subTest(duracao=duracao):
                response = self.client.post(
                    self.url,
                    data=json.dumps({**self.dados, "duracao": duracao}),
                    content_type="application/json",
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn("duracao", response.json()["errors"])
                self.assertEqual(Treino.objects.count(), 0)

    def test_rejeita_data_passada(self):
        dados = {
            **self.dados,
            "data_hora": (timezone.now() - timedelta(minutes=1)).isoformat(),
        }

        response = self.client.post(
            self.url,
            data=json.dumps(dados),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("data_hora", response.json()["errors"])
        self.assertIn("futuras", response.json()["errors"]["data_hora"][0])
        self.assertEqual(Treino.objects.count(), 0)

    def test_rejeita_solicitacao_sem_autenticacao(self):
        self.client.logout()

        response = self.client.post(self.url, data=self.dados)

        self.assertEqual(response.status_code, 401)
        self.assertIn("autenticado", response.json()["message"])
        self.assertEqual(Treino.objects.count(), 0)

    def test_rejeita_json_malformado(self):
        response = self.client.post(
            self.url,
            data="{",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("body", response.json()["errors"])
        self.assertEqual(Treino.objects.count(), 0)

    def test_exibe_formulario_para_usuario_autenticado(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "desktop-main-nav")
        self.assertContains(response, "Criar novo treino")
        self.assertContains(response, "Número de vagas")
        self.assertContains(response, 'pattern="(?:[01][0-9]|2[0-3]):[0-5][0-9]"')
        self.assertContains(response, "Futebol")

    def test_redireciona_usuario_nao_autenticado_ao_login_no_formulario(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/login/?next="))

    def test_cria_treino_a_partir_do_formulario(self):
        dados = {
            "_form_submission": "1",
            "nome": "Treino da equipe",
            "modalidade_id": self.modalidade.id,
            "data": (timezone.now() + timedelta(days=1)).date().isoformat(),
            "horario": "18:30",
            "local": "Quadra principal",
            "limite_participantes": 12,
            "duracao": 75,
            "acesso": "pago",
            "custo": 25,
        }

        response = self.client.post(self.url, data=dados)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "desktop-main-nav")
        self.assertContains(response, "Treino criado!")
        self.assertContains(response, ">Voltar</a>")
        self.assertNotContains(response, "Voltar ao início")
        treino = Treino.objects.get()
        self.assertEqual(treino.nome, "Treino da equipe")
        self.assertEqual(treino.limite_participantes, 12)
        self.assertEqual(treino.custo, 25)

    def test_formulario_aceita_valor_com_meio_real(self):
        response = self.client.post(
            self.url,
            data={
                "_form_submission": "1",
                "nome": "Treino da equipe",
                "modalidade_id": self.modalidade.id,
                "data": (timezone.now() + timedelta(days=1)).date().isoformat(),
                "horario": "18:30",
                "local": "Quadra principal",
                "limite_participantes": 12,
                "duracao": 75,
                "acesso": "pago",
                "custo": "25.50",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Treino.objects.get().custo, Decimal("25.50"))

    def test_formulario_rejeita_data_passada(self):
        response = self.client.post(
            self.url,
            data={
                "_form_submission": "1",
                "nome": "Treino da equipe",
                "modalidade_id": self.modalidade.id,
                "data": (timezone.localdate() - timedelta(days=1)).isoformat(),
                "horario": "18:30",
                "local": "Quadra principal",
                "limite_participantes": 12,
                "duracao": 75,
                "acesso": "gratuito",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "não pode estar no passado", status_code=400)
        self.assertEqual(Treino.objects.count(), 0)

    def test_formulario_rejeita_horario_passado_na_data_de_hoje(self):
        horario_passado = (timezone.localtime() - timedelta(minutes=1)).strftime("%H:%M")
        response = self.client.post(
            self.url,
            data={
                "_form_submission": "1",
                "nome": "Treino da equipe",
                "modalidade_id": self.modalidade.id,
                "data": timezone.localdate().isoformat(),
                "horario": horario_passado,
                "local": "Quadra principal",
                "limite_participantes": 12,
                "duracao": 75,
                "acesso": "gratuito",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "devem ser futuras", status_code=400)
        self.assertEqual(Treino.objects.count(), 0)

    def test_formulario_rejeita_horarios_fora_do_formato_24_horas(self):
        for horario in ("6:30", "06:30 PM", "24:00", "18:60"):
            with self.subTest(horario=horario):
                response = self.client.post(
                    self.url,
                    data={
                        "_form_submission": "1",
                        "nome": "Treino da equipe",
                        "modalidade_id": self.modalidade.id,
                        "data": (timezone.localdate() + timedelta(days=1)).isoformat(),
                        "horario": horario,
                        "local": "Quadra principal",
                        "limite_participantes": 12,
                        "duracao": 75,
                        "acesso": "gratuito",
                    },
                )

                self.assertEqual(response.status_code, 400)
                self.assertContains(response, "formato 00:00 a 23:59", status_code=400)
                self.assertEqual(Treino.objects.count(), 0)

    def test_formulario_exibe_erros_e_nao_cria_treino_invalido(self):
        response = self.client.post(
            self.url,
            data={
                "_form_submission": "1",
                "nome": "",
                "modalidade_id": self.modalidade.id,
                "data": "",
                "horario": "",
                "local": "",
                "limite_participantes": 0,
                "duracao": 0,
                "acesso": "pago",
                "custo": 0,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Informe o nome", status_code=400)
        self.assertContains(
            response,
            "Informe um valor válido",
            status_code=400,
        )
        self.assertEqual(Treino.objects.count(), 0)


class ListarTreinosTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.usuario = user_model.objects.create_user(
            usuario="atleta",
            email="atleta@exemplo.com",
            nome="Ana",
            sobrenome="Silva",
            e_socio=False,
            password="senha-segura",
        )
        self.modalidade = ModalidadeEsportiva.objects.create(nome="Vôlei")
        self.url = reverse("treinos")
        self.client.force_login(self.usuario)

    def criar_treino(self, nome, dias, **extra):
        dados = {
            "criador": self.usuario,
            "modalidade": self.modalidade,
            "nome": nome,
            "local": "Ginásio",
            "data_hora": timezone.now() + timedelta(days=dias),
            "duracao": 60,
        }
        dados.update(extra)
        return Treino.objects.create(**dados)

    def test_exige_login(self):
        self.client.logout()

        response = self.client.get(self.url)

        self.assertRedirects(response, f'{reverse("login")}?next={self.url}')

    def test_lista_treinos_disponiveis_por_data(self):
        depois = self.criar_treino("Treino depois", 5)
        antes = self.criar_treino("Treino antes", 1)

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["treinos"]), [antes, depois])
        self.assertContains(response, "2 treinos disponíveis")

    def test_treino_encerrado_fica_separado(self):
        futuro = self.criar_treino("Treino futuro", 1)
        encerrado_antigo = self.criar_treino("Treino antigo", -5)
        encerrado_recente = self.criar_treino("Treino recente", -1)

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["treinos"]), [futuro])
        self.assertEqual(
            list(response.context["treinos_encerrados"]),
            [encerrado_recente, encerrado_antigo],
        )
        self.assertContains(response, "Encerrados")
        self.assertContains(response, "training-card--encerrado", count=2)
        self.assertContains(response, "1 treino disponível")

    def test_mostra_selo_de_lotado(self):
        treino = self.criar_treino("Treino cheio", 1, limite_participantes=1)
        InscricaoTreino.objects.create(usuario=self.usuario, treino=treino)

        response = self.client.get(self.url)

        self.assertTrue(treino.lotado)
        self.assertContains(response, "Lotado")

    def test_card_mostra_dados_do_treino(self):
        self.criar_treino(
            "Treino de saque",
            2,
            limite_participantes=10,
            custo=Decimal("15.50"),
        )

        response = self.client.get(self.url)

        self.assertContains(response, "Treino de saque")
        self.assertContains(response, "Vôlei")
        self.assertContains(response, "Ginásio")
        self.assertContains(response, "R$ 15,50")
        self.assertContains(response, "0/10 participantes")
        self.assertContains(response, "Ana")

    def test_card_leva_para_o_detalhe_do_treino(self):
        treino = self.criar_treino("Treino de saque", 2)

        response = self.client.get(self.url)
        detalhe = self.client.get(reverse("treino_detalhe", args=[treino.id]))

        self.assertContains(
            response,
            f'href="{reverse("treino_detalhe", args=[treino.id])}"',
        )
        self.assertContains(detalhe, "Treino de saque")

    def test_detalhe_de_treino_inexistente_retorna_404(self):
        response = self.client.get(reverse("treino_detalhe", args=[999]))

        self.assertEqual(response.status_code, 404)

    def test_mostra_mensagem_quando_nao_ha_treinos(self):
        response = self.client.get(self.url)

        self.assertContains(response, "Nenhum treino disponível no momento")
        self.assertContains(response, "0 treinos disponíveis")
        self.assertNotContains(response, "Encerrados")

    def test_quantidade_de_queries_nao_cresce_com_os_treinos(self):
        outro = get_user_model().objects.create_user(
            usuario="outro",
            email="outro@exemplo.com",
            nome="Outro",
            sobrenome="Teste",
            e_socio=False,
        )
        for dia in range(1, 6):
            treino = self.criar_treino(f"Treino {dia}", dia, limite_participantes=5)
            InscricaoTreino.objects.create(usuario=self.usuario, treino=treino)
            InscricaoTreino.objects.create(usuario=outro, treino=treino)

        with self.assertNumQueries(5):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
