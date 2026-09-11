from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Prescription
from .services import extract_prescription


class ExtractionTests(TestCase):
    def test_extracts_basic_prescription_fields(self):
        result = extract_prescription(
            'Amoxicilina 500 mg, tomar 1 cápsula por 7 dias.'
        )
        self.assertEqual(result['medicine'], 'Amoxicilina')
        self.assertEqual(result['strength'], '500 mg')
        self.assertEqual(result['duration'], 'por 7 dias')

    def test_dashboard_accepts_text_and_persists_result(self):
        response = self.client.post(
            reverse('dashboard'),
            {'source_type': 'text', 'source_text': 'Dipirona 500 mg por 3 dias.'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.count(), 1)

    def test_dashboard_rejects_disallowed_upload_extension(self):
        upload = SimpleUploadedFile('payload.exe', b'not allowed')
        response = self.client.post(
            reverse('dashboard'),
            {'source_type': 'image', 'source_file': upload},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Prescription.objects.count(), 0)
        self.assertContains(response, 'Não foi possível processar a entrada')

    def test_clear_history_requires_post(self):
        Prescription.objects.create(source_text='Teste')
        self.client.get(reverse('clear_history'))
        self.assertEqual(Prescription.objects.count(), 1)
        self.client.post(reverse('clear_history'))
        self.assertEqual(Prescription.objects.count(), 0)

    @patch('extractor.ocr.post_file')
    def test_external_ocr_provider_returns_text(self, post_file):
        response = Mock()
        response.json.return_value = {
            'IsErroredOnProcessing': False,
            'ParsedResults': [{'ParsedText': 'Amoxicilina 500 mg'}],
        }
        post_file.return_value = response

        from .ocr import _external_ocr

        upload = SimpleUploadedFile('receita.png', b'image', content_type='image/png')
        self.assertEqual(_external_ocr(upload, 'test-token'), 'Amoxicilina 500 mg')
        post_file.assert_called_once()

    @patch('extractor.transcription.post_file')
    def test_external_transcription_provider_returns_text(self, post_file):
        response = Mock()
        response.json.return_value = {'text': 'Tomar uma cápsula por sete dias'}
        post_file.return_value = response

        from .transcription import _external_transcription

        upload = SimpleUploadedFile('audio.wav', b'audio', content_type='audio/wav')
        self.assertEqual(
            _external_transcription(upload, 'test-token'),
            'Tomar uma cápsula por sete dias',
        )
        post_file.assert_called_once()
