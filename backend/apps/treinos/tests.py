import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import InscricaoTreino, ModalidadeEsportiva, Treino


class TreinosListagemPageTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            usuario="atleta",
            email="atleta@exemplo.com",
            nome="Atleta",
            sobrenome="Teste",
            e_socio=False,
            password="BrutusTestPassword123!",
        )
        self.modalidade = ModalidadeEsportiva.objects.get_or_create(nome="Futebol")[0]
        self.client.force_login(self.usuario)

    def criar_treino(self, nome):
        return Treino.objects.create(
            criador=self.usuario,
            modalidade=self.modalidade,
            nome=nome,
            local="Quadra principal",
            data_hora=timezone.now() + timedelta(days=1),
            duracao=90,
        )

    def test_pagina_treinos_exibe_busca_e_lista_completa(self):
        self.criar_treino("Treino de futebol")
        self.criar_treino("Treino de vôlei")

        response = self.client.get(
            reverse("treinos"),
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="q"')
        self.assertNotContains(response, "Aplicar filtros")
        self.assertContains(response, "Treino de futebol")
        self.assertContains(response, "Treino de vôlei")

    def test_pesquisa_na_pagina_filtra_por_nome_parcial_sem_diferenciar_caixa(self):
        for nome, modalidade in (
            ("Treino de futebol", self.modalidade),
            ("FUTEBOL na areia", self.modalidade),
            (
                "Treino de vôlei",
                ModalidadeEsportiva.objects.get_or_create(nome="Vôlei")[0],
            ),
        ):
            Treino.objects.create(
                criador=self.usuario,
                modalidade=modalidade,
                nome=nome,
                local="Quadra principal",
                data_hora=timezone.now() + timedelta(days=1),
                duracao=90,
            )

        response = self.client.get(
            reverse("treinos"),
            {"q": "fUtEbOl"},
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="fUtEbOl"')
        self.assertContains(response, "Treino de futebol")
        self.assertContains(response, "FUTEBOL na areia")
        self.assertNotContains(response, "Treino de vôlei")

    def test_pesquisa_sem_correspondencia_mostra_estado_vazio(self):
        self.criar_treino("Treino de vôlei")

        response = self.client.get(
            reverse("treinos"),
            {"q": "basquete"},
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhum treino encontrado com esse nome.")
        self.assertNotContains(response, "Treino de vôlei")

    def test_pesquisa_considera_modalidade_e_local(self):
        outra_modalidade = ModalidadeEsportiva.objects.get_or_create(nome="Basquete")[0]
        treino_modalidade = self.criar_treino("Treino da equipe")
        treino_local = Treino.objects.create(
            criador=self.usuario,
            modalidade=self.modalidade,
            nome="Partida de sábado",
            local="Ginásio Central",
            data_hora=timezone.now() + timedelta(days=1),
            duracao=90,
        )
        Treino.objects.filter(pk=treino_modalidade.pk).update(modalidade=outra_modalidade)

        for termo in ("basquete", "central"):
            with self.subTest(termo=termo):
                response = self.client.get(
                    reverse("treinos"),
                    {"q": termo},
                    HTTP_ACCEPT="text/html",
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    "Treino da equipe" if termo == "basquete" else "Partida de sábado",
                )

    def test_filtros_de_modalidade_gratuito_e_com_vagas(self):
        modalidade_basket = ModalidadeEsportiva.objects.get_or_create(nome="Basquete")[0]
        disponivel = self.criar_treino("Treino disponível")
        indisponivel = Treino.objects.create(
            criador=self.usuario,
            modalidade=modalidade_basket,
            nome="Treino lotado",
            limite_participantes=1,
            local="Ginásio",
            data_hora=timezone.now() + timedelta(days=1),
            duracao=90,
            custo=Decimal("10.00"),
        )
        InscricaoTreino.objects.create(usuario=self.usuario, treino=indisponivel)

        response = self.client.get(
            reverse("treinos"),
            {
                "modalidade": str(self.modalidade.id),
                "gratuito": "1",
                "com_vagas": "1",
            },
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Treino disponível")
        self.assertNotContains(response, "Treino lotado")
        self.assertContains(response, "Gratuito")


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
        self.modalidade = ModalidadeEsportiva.objects.get_or_create(nome="Futebol")[0]
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

    def test_lista_treinos_sem_filtro(self):
        outros_dados = {**self.dados, "nome": "Treino de vôlei"}
        self.client.post(
            self.url,
            data=json.dumps(self.dados),
            content_type="application/json",
        )
        self.client.post(
            self.url,
            data=json.dumps(outros_dados),
            content_type="application/json",
        )

        response = self.client.get("/treinos/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [treino["nome"] for treino in response.json()["treinos"]],
            ["Treino de futebol", "Treino de vôlei"],
        )

    def test_filtra_treinos_por_nome_parcial_sem_diferenciar_maiusculas(self):
        for nome in ("Treino de futebol", "FUTEBOL na areia", "Treino de vôlei"):
            Treino.objects.create(
                criador=self.criador,
                modalidade=self.modalidade,
                nome=nome,
                local="Quadra principal",
                data_hora=timezone.now() + timedelta(days=1),
                duracao=90,
            )

        response = self.client.get("/treinos/?nome=fUtEbOl")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [treino["nome"] for treino in response.json()["treinos"]],
            ["Treino de futebol", "FUTEBOL na areia"],
        )

    def test_filtro_sem_correspondencia_retorna_lista_vazia(self):
        Treino.objects.create(
            criador=self.criador,
            modalidade=self.modalidade,
            nome="Treino de vôlei",
            local="Quadra principal",
            data_hora=timezone.now() + timedelta(days=1),
            duracao=90,
        )

        response = self.client.get("/treinos/?nome=basquete")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["treinos"], [])

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
