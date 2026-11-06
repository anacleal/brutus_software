from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardSearchUiTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            usuario="atleta",
            email="atleta@example.com",
            nome="Atleta",
            sobrenome="Teste",
            e_socio=False,
            password="BrutusTestPassword123!",
        )
        self.client.force_login(user)

    def test_dashboard_nao_exibe_pesquisa_de_treinos(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="nome"')
        self.assertContains(response, "Nenhum treino agendado")
