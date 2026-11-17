from __future__ import annotations

import logging

from PIL import Image, ImageOps
import pytesseract

logger = logging.getLogger(__name__)

MAX_IMAGE_PIXELS_FOR_OCR = 8_000_000
MAX_OCR_DIMENSION = 1400
# Instâncias econômicas podem demorar mais para iniciar o Tesseract em imagens
# complexas; 20 s provocava falsos erros mesmo com imagens válidas.
OCR_TIMEOUT_SECONDS = 60
OCR_LANGUAGE = 'por'
OCR_CONFIG = '--psm 6'


def extract_text_from_image(uploaded_file) -> str:
    # Abre a imagem enviada e confirma que o conteúdo é realmente uma imagem.
    # A extensão/MIME ajudam na triagem, mas não substituem esta validação.
    try:
        image = Image.open(uploaded_file)
        # Ler width/height usa apenas o cabeçalho. Faça esta checagem antes de
        # verify(), pois fotos com muitos megapixels podem derrubar o worker.
        if image.width * image.height > MAX_IMAGE_PIXELS_FOR_OCR:
            too_large = True
        else:
            too_large = False
            image.verify()
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError('O arquivo enviado não contém uma imagem válida.') from exc

    if too_large:
        raise ValueError('A imagem é grande demais para o processamento automático.')

    # Reabre após verify(), que deixa o ponteiro no fim do arquivo.
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)

    # Tons de cinza e contraste automático reduzem ruídos antes do Tesseract.
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image.thumbnail((MAX_OCR_DIMENSION, MAX_OCR_DIMENSION), Image.Resampling.LANCZOS)

    # Uma receita costuma ser um bloco único de texto. O modo 6 e apenas o
    # idioma português reduzem bastante o tempo e a memória do Tesseract.
    try:
        return pytesseract.image_to_string(
            image,
            lang=OCR_LANGUAGE,
            config=OCR_CONFIG,
            timeout=OCR_TIMEOUT_SECONDS,
        ).strip()
    except (pytesseract.TesseractError, RuntimeError, OSError) as exc:
        # Converte falha do binário/idioma ou timeout em erro tratável pela view.
        logger.exception('Falha controlada no OCR: %s', exc.__class__.__name__)
        raise ValueError('O OCR não conseguiu processar esta imagem no tempo limite.') from exc
