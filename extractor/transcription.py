from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

_model = None


def transcribe_audio(uploaded_file) -> str:
    global _model
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError('O transcritor local não está instalado.') from exc

    with NamedTemporaryFile(prefix='medextract_', suffix=Path(uploaded_file.name).suffix, delete=False) as destination:
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
