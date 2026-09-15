from pathlib import Path

from django.core.exceptions import ValidationError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.webm', '.ogg'}
ALLOWED_CONTENT_TYPES = {'image': {'image/jpeg', 'image/png', 'image/webp'}, 'audio': {'audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/webm', 'audio/ogg', 'application/ogg'}}


def validate_upload(uploaded_file, source_type: str) -> None:
    if uploaded_file.size > MAX_UPLOAD_BYTES:
        raise ValidationError('O arquivo excede o limite de 10 MB.')
    suffix = Path(uploaded_file.name).suffix.lower()
    allowed = ALLOWED_IMAGE_EXTENSIONS if source_type == 'image' else ALLOWED_AUDIO_EXTENSIONS
    if suffix not in allowed:
        raise ValidationError('Formato de arquivo não permitido para este tipo de entrada.')
    content_type = (uploaded_file.content_type or '').lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES[source_type]:
        raise ValidationError('O tipo MIME do arquivo não corresponde ao formato permitido.')
