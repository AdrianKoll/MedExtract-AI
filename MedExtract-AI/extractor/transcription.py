from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .providers import ProviderError, post_file

_model = None


def _external_transcription(uploaded_file, token: str) -> str:
    uploaded_file.seek(0)
    model_url = os.environ.get(
        'HF_AUDIO_API_URL',
        'https://router.huggingface.co/hf-inference/models/openai/whisper-small',
    )
    response = post_file(
        model_url,
        headers={'Authorization': f'Bearer {token}'},
        files={'file': (uploaded_file.name, uploaded_file, uploaded_file.content_type or 'audio/mpeg')},
        timeout=(10, 120),
    )
    payload = response.json()
    text = payload.get('text', '').strip() if isinstance(payload, dict) else ''
    if not text:
        raise ProviderError('O provedor de transcrição não retornou texto.')
    return text


def _local_transcription(uploaded_file) -> str:
    global _model
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError('O transcritor local não está instalado.') from exc

    with NamedTemporaryFile(
        prefix='medextract_', suffix=Path(uploaded_file.name).suffix, delete=False
    ) as destination:
        temporary_path = Path(destination.name)
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    try:
        if _model is None:
            _model = WhisperModel('base', device='cpu', compute_type='int8')
        segments, _ = _model.transcribe(str(temporary_path), language='pt', vad_filter=True)
        return ' '.join(segment.text.strip() for segment in segments).strip()
    finally:
        temporary_path.unlink(missing_ok=True)


def transcribe_audio(uploaded_file) -> str:
    token = os.environ.get('HF_TOKEN', '').strip()
    if token:
        try:
            return _external_transcription(uploaded_file, token)
        except (ProviderError, ValueError, KeyError):
            uploaded_file.seek(0)
    return _local_transcription(uploaded_file)
