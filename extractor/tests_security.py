import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import ApiToken, Integration


class SecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='security-user', password='Strong-test-pass-123')
        self.other = get_user_model().objects.create_user(username='other-user', password='Strong-test-pass-456')

    def auth(self, token):
        return {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    def test_expired_token_is_rejected(self):
        token = ApiToken.issue_for_user(self.user)
        credential = ApiToken.objects.get(user=self.user)
        credential.expires_at = timezone.now() - timedelta(seconds=1)
        credential.save(update_fields=['expires_at'])
        response = self.client.get(reverse('api-prescriptions'), **self.auth(token))
        self.assertEqual(response.status_code, 401)

    def test_token_can_be_revoked(self):
        token = ApiToken.issue_for_user(self.user)
        response = self.client.post(reverse('api-token-revoke'), **self.auth(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse('api-prescriptions'), **self.auth(token)).status_code, 401)

    def test_integrations_are_isolated(self):
        token = ApiToken.issue_for_user(self.user)
        response = self.client.post(reverse('api-integrations'), data=json.dumps({'provider': 'ocr', 'name': 'private', 'secret': 'secret'}), content_type='application/json', **self.auth(token))
        self.assertEqual(response.status_code, 201)
        other_token = ApiToken.issue_for_user(self.other)
        listing = self.client.get(reverse('api-integrations'), **self.auth(other_token))
        self.assertEqual(listing.json()['results'], [])

    def test_healthcheck_is_available(self):
        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
