from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .models import Prescription
from .ocr import extract_text_from_image
from .services import extract_prescription
from .transcription import transcribe_audio
from .validators import validate_upload


def dashboard(request):
    result = None
    source_text = ''
    source_type = 'text'
    error = ''

    if request.method == 'POST':
        source_text = request.POST.get('source_text', '').strip()
        source_type = request.POST.get('source_type', 'text')
        uploaded_file = request.FILES.get('source_file')

        try:
            if source_type not in {'text', 'image', 'audio'}:
                raise ValidationError('Tipo de entrada inválido.')
            if uploaded_file:
                if source_type == 'text':
                    raise ValidationError('Selecione imagem ou áudio para enviar um arquivo.')
                validate_upload(uploaded_file, source_type)
                source_text = (
                    extract_text_from_image(uploaded_file)
                    if source_type == 'image'
                    else transcribe_audio(uploaded_file)
                )
            if not source_text:
                raise ValidationError('Informe um texto ou envie um arquivo com conteúdo legível.')

            result = extract_prescription(source_text)
            Prescription.objects.create(
                source_text=source_text,
                source_type=source_type,
                source_name=uploaded_file.name if uploaded_file else '',
                **result,
            )
        except (ValidationError, ValueError, RuntimeError):
            error = 'Não foi possível processar a entrada. Verifique o formato e tente novamente.'

    history = Prescription.objects.all()[:8]
    return render(
        request,
        'extractor/dashboard.html',
        {
            'result': result,
            'source_text': source_text,
            'history': history,
            'source_type': source_type,
            'error': error,
        },
    )


def clear_history(request):
    if request.method == 'POST':
        Prescription.objects.all().delete()
    return redirect('dashboard')
