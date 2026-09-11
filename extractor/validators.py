from pathlib import Path

from django.core.exceptions import ValidationError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.webm', '.ogg'}


def validate_upload(uploaded_file, source_type: str) -> None:
    if uploaded_file.size > MAX_UPLOAD_BYTES:
        raise ValidationError('O arquivo excede o limite de 10 MB.')

    suffix = Path(uploaded_file.name).suffix.lower()
    allowed = ALLOWED_IMAGE_EXTENSIONS if source_type == 'image' else ALLOWED_AUDIO_EXTENSIONS
    if suffix not in allowed:
        raise ValidationError('Formato de arquivo não permitido para este tipo de entrada.')
