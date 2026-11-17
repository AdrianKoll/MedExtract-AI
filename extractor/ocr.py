from __future__ import annotations

from PIL import Image, ImageOps
import pytesseract


def extract_text_from_image(uploaded_file) -> str:
    # Abre a imagem enviada e confirma que o conteúdo é realmente uma imagem.
    # A extensão/MIME ajudam na triagem, mas não substituem esta validação.
    try:
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
    except (OSError, ValueError) as exc:
        raise ValueError('O arquivo enviado não contém uma imagem válida.') from exc

    # Tons de cinza e contraste automático reduzem ruídos antes do Tesseract.
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)

    # O idioma português é prioritário; inglês cobre abreviações e nomes comuns.
    return pytesseract.image_to_string(image, lang='por+eng').strip()
