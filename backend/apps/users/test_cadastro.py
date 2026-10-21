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
            b"conteudo da foto",
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
