from pathlib import Path

_model = None


def transcribe_audio(uploaded_file):
    global _model
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError('O transcritor local não está instalado. Execute pip install -r requirements.txt.') from exc
    temporary_path = Path('media') / uploaded_file.name
    temporary_path.parent.mkdir(exist_ok=True)
    with temporary_path.open('wb') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    try:
        if _model is None:
            _model = WhisperModel('base', device='cpu', compute_type='int8')
        segments, _ = _model.transcribe(str(temporary_path), language='pt', vad_filter=True)
        return ' '.join(segment.text.strip() for segment in segments).strip()
    finally:
        temporary_path.unlink(missing_ok=True)
