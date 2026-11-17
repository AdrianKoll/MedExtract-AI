import json
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import ApiToken, Prescription
from .ocr import extract_text_from_image
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

    def test_extracts_medicine_from_full_ocr_prescription(self):
        text = (
            '**CLÍNICA SANTA VIDA** **PRESCRIÇÃO** '
            '**1. Paracetamol 750 mg** - Quantidade: 20 comprimidos - '
            'Posologia: Tomar 1 comprimido a cada 6 horas, por 5 dias. '
            '**2. Loratadina 10 mg** - Quantidade: 7 comprimidos.'
        )
        result = extract_prescription(text)
        self.assertEqual(result['medicine'], 'Paracetamol')
        self.assertEqual(result['strength'], '750 mg')
        self.assertEqual(result['quantity'], '20 comprimidos')
        self.assertEqual(result['duration'], 'por 5 dias')
        self.assertEqual([item['medicine'] for item in result['medications']], ['Paracetamol', 'Loratadina'])
        self.assertEqual(result['medications'][0]['quantity'], '20 comprimidos')
        self.assertEqual(result['medications'][1]['quantity'], '7 comprimidos')
        self.assertEqual(result['notes'], '')

    def test_extracts_any_number_of_medicines_with_independent_fields(self):
        result = extract_prescription(
            '1. Paracetamol 750 mg - Quantidade: 20 comprimidos - '
            'Tomar 1 comprimido a cada 6 horas por 5 dias. '
            '2. Loratadina 10 mg - Quantidade: 7 comprimidos - Tomar 1 comprimido à noite por 7 dias. '
            '3. Omeprazol 20 mg - Quantidade: 14 cápsulas - Tomar 1 cápsula pela manhã por 14 dias. '
            '4. Dipirona 500 mg - Quantidade: 10 comprimidos.'
        )
        medications = result['medications']
        self.assertEqual(len(medications), 4)
        self.assertEqual([item['medicine'] for item in medications], ['Paracetamol', 'Loratadina', 'Omeprazol', 'Dipirona'])
        self.assertEqual([item['quantity'] for item in medications], ['20 comprimidos', '7 comprimidos', '14 cápsulas', '10 comprimidos'])
        self.assertEqual(medications[0]['duration'], 'por 5 dias')
        self.assertEqual(medications[1]['duration'], 'por 7 dias')
        self.assertEqual(medications[2]['duration'], 'por 14 dias')

    def test_dashboard_public_demo_does_not_persist(self):
        response = self.client.post(reverse('dashboard'), {'source_type': 'text', 'source_text': 'Dipirona 500 mg por 3 dias.'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.count(), 0)
        self.assertContains(response, 'Dados extraídos')
        self.assertContains(response, 'Medicamento 1: Dipirona')
        self.assertContains(response, 'Quantidade')
        self.assertNotContains(response, 'QUANTITY')

    def test_authenticated_dashboard_persists_only_for_current_user(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('dashboard'), {'source_type': 'text', 'source_text': 'Dipirona 500 mg por 3 dias.'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.filter(owner=self.user).count(), 1)
        self.assertEqual(Prescription.objects.filter(owner=self.other_user).count(), 0)
        self.assertEqual(Prescription.objects.get(owner=self.user).medications[0]['medicine'], 'Dipirona')

    def test_history_displays_all_medicines_from_one_prescription(self):
        self.client.force_login(self.user)
        Prescription.objects.create(
            owner=self.user,
            source_text='Receita com três medicamentos',
            medicine='Amoxicilina',
            strength='500 mg',
            medications=[
                {'medicine': 'Amoxicilina', 'strength': '500 mg', 'quantity': '21 cápsulas'},
                {'medicine': 'Loratadina', 'strength': '10 mg', 'quantity': '7 comprimidos'},
                {'medicine': 'Omeprazol', 'strength': '20 mg', 'quantity': '14 cápsulas'},
            ],
        )
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Amoxicilina')
        self.assertContains(response, 'Loratadina')
        self.assertContains(response, 'Omeprazol')
        self.assertContains(response, '14 cápsulas')

    def test_dashboard_rejects_disallowed_upload_extension(self):
        upload = SimpleUploadedFile('payload.exe', b'not allowed')
        response = self.client.post(reverse('dashboard'), {'source_type': 'image', 'source_file': upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.count(), 0)
        self.assertContains(response, 'Não foi possível processar a entrada')

    def test_ocr_rejects_file_that_is_not_a_real_image(self):
        # A extensão e o MIME podem ser falsificados; Pillow precisa confirmar o conteúdo.
        upload = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
        with self.assertRaises(ValueError):
            extract_text_from_image(upload)

    def test_ocr_rejects_images_with_too_many_pixels(self):
        # O cabeçalho é analisado antes de verify() para evitar OOM no servidor.
        buffer = BytesIO()
        Image.new('RGB', (4000, 3000), 'white').save(buffer, format='PNG')
        upload = SimpleUploadedFile('large.png', buffer.getvalue(), content_type='image/png')
        with self.assertRaisesMessage(ValueError, 'grande demais'):
            extract_text_from_image(upload)

    @patch('extractor.ocr.pytesseract.image_to_string', return_value='Amoxicilina 500 mg')
    def test_ocr_uses_longer_timeout_for_slow_instances(self, image_to_string):
        buffer = BytesIO()
        Image.new('RGB', (400, 300), 'white').save(buffer, format='PNG')
        upload = SimpleUploadedFile('recipe.png', buffer.getvalue(), content_type='image/png')
        self.assertEqual(extract_text_from_image(upload), 'Amoxicilina 500 mg')
        self.assertEqual(image_to_string.call_args.kwargs['timeout'], 60)

    @patch('extractor.views.extract_text_from_image', return_value='Dipirona 500 mg por 3 dias.')
    def test_image_upload_is_detected_when_type_remains_text(self, extract_text):
        upload = SimpleUploadedFile('recipe.png', b'fake image', content_type='image/png')
        response = self.client.post(reverse('dashboard'), {'source_type': 'text', 'source_file': upload})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dipirona')
        extract_text.assert_called_once()

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
        self.assertEqual(own.json()['medications'][0]['medicine'], 'Amoxicilina')
        forbidden = self.client.get(reverse('api-prescription-detail', kwargs={'pk': other.pk}), HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(forbidden.status_code, 404)
