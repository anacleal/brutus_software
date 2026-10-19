from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthenticationSessionTests(TestCase):
    def setUp(self):
        self.password = 'BrutusTestPassword123!'
        self.user = get_user_model().objects.create_user(
            username='atleta',
            email='atleta@example.com',
            password=self.password,
        )

    def test_session_persists_and_logout_ends_it(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.user.username, 'password': self.password},
        )
        self.assertRedirects(response, reverse('dashboard'))

        session_cookie = response.cookies['sessionid']
        self.assertTrue(session_cookie['httponly'])
        self.assertEqual(session_cookie['samesite'], 'Lax')

        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'action="/logout/"')
        self.assertContains(dashboard_response, 'name="csrfmiddlewaretoken"', count=2)
        self.assertEqual(self.client.get(reverse('perfil')).status_code, 200)

        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

        for url_name in ('dashboard', 'treinos', 'criar_treino', 'perfil'):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertRedirects(
                    response,
                    f'{reverse("login")}?next={reverse(url_name)}',
                )

    def test_protected_pages_redirect_to_login_without_session(self):
        for session_id in (None, 'invalid-session-id'):
            if session_id is not None:
                self.client.cookies['sessionid'] = session_id

            for url_name in ('dashboard', 'treinos', 'criar_treino', 'perfil'):
                with self.subTest(session_id=session_id, url_name=url_name):
                    response = self.client.get(reverse(url_name))
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response.url.split('?')[0], reverse('login'))

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('logout'))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)

    def test_login_does_not_redirect_to_an_external_next_url(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': self.user.username,
                'password': self.password,
                'next': 'https://example.com/',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
