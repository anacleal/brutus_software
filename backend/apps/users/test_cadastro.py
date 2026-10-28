import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.modalidades.models import ModalidadeEsportiva


class CadastroViewTests(TestCase):
    def setUp(self):
        self.modalidade = ModalidadeEsportiva.objects.get(nome="Futebol")
        self.dados = {
            "nome": "Ana",
            "sobrenome": "Silva",
            "email": "ana@example.com",
            "usuario": "ana.silva",
            "senha": "SenhaSegura123!",
            "confirmacao_senha": "SenhaSegura123!",
            "modalidade_preferida": str(self.modalidade.pk),
            "_form_submission": "1",
        }

    def test_get_renders_form_with_csrf_and_static_css(self):
        response = self.client.get(reverse("cadastro"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "name=\"csrfmiddlewaretoken\"")
        self.assertContains(response, "users/css/cadastro.css")
        self.assertContains(response, "Futebol")

    def test_valid_post_creates_user_with_hashed_password_and_modality(self):
        response = self.client.post(reverse("cadastro"), self.dados)

        self.assertRedirects(response, reverse("login"))
        usuario = get_user_model().objects.get(usuario="ana.silva")
        self.assertTrue(usuario.check_password(self.dados["senha"]))
        self.assertEqual(list(usuario.modalidades.all()), [self.modalidade])
        self.assertEqual(usuario.cargo, "atleta")
        self.assertFalse(usuario.e_socio)

        login_response = self.client.post(
            reverse("login"),
            {
                "username": "ana.silva",
                "password": self.dados["senha"],
            },
        )
        self.assertRedirects(login_response, reverse("dashboard"))

    def test_invalid_password_confirmation_does_not_create_user(self):
        dados = self.dados | {"confirmacao_senha": "OutraSenha123!"}

        response = self.client.post(reverse("cadastro"), dados)

        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "A senha e a confirmação de senha não são iguais.",
            status_code=400,
        )
        self.assertFalse(
            get_user_model().objects.filter(usuario="ana.silva").exists()
        )

    def test_duplicate_email_is_rejected(self):
        self.client.post(reverse("cadastro"), self.dados)
        dados = self.dados | {"usuario": "outro.usuario"}

        response = self.client.post(reverse("cadastro"), dados)

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Este e-mail já está cadastrado.", status_code=400)

    def test_optional_profile_photo_is_saved_to_media_storage(self):
        foto = SimpleUploadedFile(
            "perfil.jpg",
            b"\xff\xd8\xff\xe0conteudo da foto",
            content_type="image/jpeg",
        )
        dados = self.dados | {"foto": foto}

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(reverse("cadastro"), dados)
                usuario = get_user_model().objects.get(usuario="ana.silva")
                caminho_foto = Path(
                    media_root,
                    usuario.foto_perfil.removeprefix("/media/"),
                )

                self.assertRedirects(response, reverse("login"))
                self.assertTrue(caminho_foto.is_file())


class CadastroEndpointTests(TestCase):
    def setUp(self):
        self.modalidade = ModalidadeEsportiva.objects.get(nome="Futebol")
        self.dados = {
            "nome": "Ana",
            "sobrenome": "Silva",
            "email": "ana@example.com",
            "usuario": "ana.silva",
            "senha": "SenhaSegura123!",
            "confirmacao_senha": "SenhaSegura123!",
            "modalidade_preferida": self.modalidade.pk,
        }

    def enviar_json(self, dados):
        return self.client.post(
            reverse("cadastro"),
            json.dumps(dados),
            content_type="application/json",
        )

    def test_valid_json_returns_201_with_created_user(self):
        response = self.enviar_json(self.dados)

        self.assertEqual(response.status_code, 201)
        usuario = get_user_model().objects.get(usuario="ana.silva")
        self.assertEqual(response.json()["usuario"]["id"], usuario.id)
        self.assertEqual(
            response.json()["usuario"]["modalidade_preferida"],
            self.modalidade.pk,
        )
        self.assertNotEqual(usuario.password, self.dados["senha"])
        self.assertTrue(usuario.check_password(self.dados["senha"]))

    def test_duplicate_email_and_username_return_400(self):
        self.enviar_json(self.dados)

        response = self.enviar_json(self.dados)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Este e-mail já está cadastrado.", response.json()["errors"])
        self.assertIn(
            "Este nome de usuário já está em uso.",
            response.json()["errors"],
        )
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_incomplete_data_returns_400_and_does_not_create_user(self):
        response = self.enviar_json({"nome": "Ana"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("O campo 'email' é obrigatório.", response.json()["errors"])
        self.assertFalse(get_user_model().objects.exists())

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            reverse("cadastro"),
            "{nao e json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["errors"],
            ["O corpo da requisição deve conter um JSON válido."],
        )

    def test_multipart_without_form_flag_returns_201(self):
        dados = self.dados | {"modalidade_preferida": str(self.modalidade.pk)}

        response = self.client.post(reverse("cadastro"), dados)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["usuario"]["usuario"], "ana.silva")
