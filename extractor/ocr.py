from __future__ import annotations

from PIL import Image, ImageOps
import pytesseract


def extract_text_from_image(uploaded_file) -> str:
    image = Image.open(uploaded_file)
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    return pytesseract.image_to_string(image, lang='por+eng').strip()
