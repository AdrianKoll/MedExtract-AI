from __future__ import annotations

import os

from PIL import Image, ImageOps
import pytesseract

from .providers import ProviderError, post_file


def _local_ocr(uploaded_file) -> str:
    image = Image.open(uploaded_file)
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    return pytesseract.image_to_string(image, lang='por+eng').strip()


def _external_ocr(uploaded_file, api_key: str) -> str:
    uploaded_file.seek(0)
    response = post_file(
        os.environ.get('OCR_API_URL', 'https://api.ocr.space/parse/image'),
        headers={'apikey': api_key},
        files={'file': (uploaded_file.name, uploaded_file, uploaded_file.content_type or 'application/octet-stream')},
        data={'language': 'por', 'OCREngine': '2', 'isOverlayRequired': 'false'},
    )
    payload = response.json()
    if payload.get('IsErroredOnProcessing'):
        raise ProviderError('O provedor de OCR não conseguiu processar a imagem.')
    results = payload.get('ParsedResults') or []
    text = '\n'.join(item.get('ParsedText', '') for item in results).strip()
    if not text:
        raise ProviderError('O provedor de OCR não retornou texto.')
    return text


def extract_text_from_image(uploaded_file) -> str:
    api_key = os.environ.get('OCR_SPACE_API_KEY', '').strip()
    if api_key:
        try:
            return _external_ocr(uploaded_file, api_key)
        except (ProviderError, ValueError, KeyError):
            uploaded_file.seek(0)
    return _local_ocr(uploaded_file)
