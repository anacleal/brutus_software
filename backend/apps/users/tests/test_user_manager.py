from django.contrib.auth import get_user_model
from django.test import TestCase


class UsuarioManagerTests(TestCase):
    def test_create_superuser_define_defaults_and_required_permissions(self):
        user = get_user_model().objects.create_superuser(
            usuario='admin',
            email='admin@example.com',
            nome='Admin',
            sobrenome='Brutus',
            password='secure-test-password',
        )

        self.assertEqual(user.cargo, 'administrador')
        self.assertFalse(user.e_socio)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_superuser_rejects_non_staff(self):
        with self.assertRaisesMessage(ValueError, 'is_staff=True'):
            get_user_model().objects.create_superuser(
                usuario='admin',
                email='admin@example.com',
                nome='Admin',
                sobrenome='Brutus',
                password='secure-test-password',
                is_staff=False,
            )

    def test_create_superuser_rejects_non_superuser(self):
        with self.assertRaisesMessage(ValueError, 'is_superuser=True'):
            get_user_model().objects.create_superuser(
                usuario='admin',
                email='admin@example.com',
                nome='Admin',
                sobrenome='Brutus',
                password='secure-test-password',
                is_superuser=False,
            )
