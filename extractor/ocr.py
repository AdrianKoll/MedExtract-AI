from __future__ import annotations

from PIL import Image, ImageOps
import pytesseract

MAX_IMAGE_PIXELS_FOR_OCR = 20_000_000
MAX_OCR_DIMENSION = 2400
OCR_TIMEOUT_SECONDS = 25


def extract_text_from_image(uploaded_file) -> str:
    # Abre a imagem enviada e confirma que o conteúdo é realmente uma imagem.
    # A extensão/MIME ajudam na triagem, mas não substituem esta validação.
    try:
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError('O arquivo enviado não contém uma imagem válida.') from exc

    # Fotos de celular podem ter muitos megapixels e consumir toda a memória
    # do plano gratuito. Recusar imagens excessivas é mais seguro que travar o worker.
    if image.width * image.height > MAX_IMAGE_PIXELS_FOR_OCR:
        raise ValueError('A imagem é grande demais para o processamento automático.')

    # Tons de cinza e contraste automático reduzem ruídos antes do Tesseract.
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image.thumbnail((MAX_OCR_DIMENSION, MAX_OCR_DIMENSION), Image.Resampling.LANCZOS)

    # O idioma português é prioritário; inglês cobre abreviações e nomes comuns.
    try:
        return pytesseract.image_to_string(image, lang='por+eng', timeout=OCR_TIMEOUT_SECONDS).strip()
    except (pytesseract.TesseractError, RuntimeError, OSError) as exc:
        # Converte falha do binário/idioma ou timeout em erro tratável pela view.
        raise ValueError('O OCR não conseguiu processar esta imagem no tempo limite.') from exc
