import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import ApiToken, Prescription
from .services import extract_prescription


class ExtractionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='alice', password='Strong-test-pass-123')
        self.other_user = get_user_model().objects.create_user(username='bob', password='Strong-test-pass-456')

    def test_extracts_basic_prescription_fields(self):
        result = extract_prescription('Amoxicilina 500 mg, tomar 1 cápsula por 7 dias.')
        self.assertEqual(result['medicine'], 'Amoxicilina')
        self.assertEqual(result['strength'], '500 mg')
        self.assertEqual(result['duration'], 'por 7 dias')

    def test_dashboard_public_demo_does_not_persist(self):
        response = self.client.post(reverse('dashboard'), {'source_type': 'text', 'source_text': 'Dipirona 500 mg por 3 dias.'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.count(), 0)
        self.assertContains(response, 'Dados extraídos')

    def test_authenticated_dashboard_persists_only_for_current_user(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('dashboard'), {'source_type': 'text', 'source_text': 'Dipirona 500 mg por 3 dias.'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.filter(owner=self.user).count(), 1)
        self.assertEqual(Prescription.objects.filter(owner=self.other_user).count(), 0)

    def test_dashboard_rejects_disallowed_upload_extension(self):
        upload = SimpleUploadedFile('payload.exe', b'not allowed')
        response = self.client.post(reverse('dashboard'), {'source_type': 'image', 'source_file': upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.count(), 0)
        self.assertContains(response, 'Não foi possível processar a entrada')

    def test_clear_history_only_deletes_current_users_records(self):
        self.client.force_login(self.user)
        Prescription.objects.create(owner=self.user, source_text='Meu registro')
        Prescription.objects.create(owner=self.other_user, source_text='Outro registro')
        self.client.post(reverse('clear_history'))
        self.assertEqual(Prescription.objects.filter(owner=self.user).count(), 0)
        self.assertEqual(Prescription.objects.filter(owner=self.other_user).count(), 1)

    def test_api_requires_bearer_token(self):
        response = self.client.get(reverse('api-prescriptions'))
        self.assertEqual(response.status_code, 401)

    def test_api_token_scopes_data_to_owner(self):
        token = ApiToken.issue_for_user(self.user)
        own = self.client.post(reverse('api-prescriptions'), data=json.dumps({'source_text': 'Amoxicilina 500 mg'}), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(own.status_code, 201)
        other = Prescription.objects.create(owner=self.other_user, source_text='Privado')
        listing = self.client.get(reverse('api-prescriptions'), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()['results']), 1)
        self.assertEqual(listing.json()['results'][0]['id'], own.json()['id'])
        forbidden = self.client.get(reverse('api-prescription-detail', kwargs={'pk': other.pk}), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(forbidden.status_code, 404)

