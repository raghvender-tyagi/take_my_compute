from django.test import SimpleTestCase
from django.urls import resolve, reverse

from .views import RegisterView
from .urls import urlpatterns


class AccountsAppTests(SimpleTestCase):
    def test_auth_urls_are_registered(self):
        self.assertTrue(any(url.pattern.name == 'auth_register' for url in urlpatterns))
        self.assertTrue(any(url.pattern.name == 'auth_me' for url in urlpatterns))

    def test_register_view_is_resolvable(self):
        resolved = resolve('/api/auth/api/register/')
        self.assertEqual(resolved.view_name, 'auth_register')
        self.assertEqual(resolved.func.view_class, RegisterView)

    def test_auth_reverse_lookup(self):
        self.assertEqual(reverse('auth_register'), '/api/auth/api/register/')
        self.assertEqual(reverse('auth_me'), '/api/auth/api/me/')
