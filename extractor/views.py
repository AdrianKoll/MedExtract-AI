import logging
from pathlib import Path

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from .models import Prescription
from .ocr import extract_text_from_image
from .security import audit, login_with_protection
from .services import extract_prescription
from .transcription import transcribe_audio
from .validators import ALLOWED_AUDIO_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS, validate_upload

logger = logging.getLogger(__name__)


def dashboard(request):
    # A mesma tela atende o demo público e a área autenticada; só a segunda
    # persiste o resultado no histórico privado do usuário.
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
            if len(source_text) > 20000:
                raise ValidationError('O texto excede o limite permitido.')
            if uploaded_file:
                if source_type == 'text':
                    # Se o usuário escolheu um arquivo mas esqueceu o seletor,
                    # identifica o tipo pela extensão antes de validar o conteúdo.
                    suffix = Path(uploaded_file.name).suffix.lower()
                    if suffix in ALLOWED_IMAGE_EXTENSIONS:
                        source_type = 'image'
                    elif suffix in ALLOWED_AUDIO_EXTENSIONS:
                        source_type = 'audio'
                    else:
                        raise ValidationError('Selecione imagem ou áudio para enviar um arquivo.')
                validate_upload(uploaded_file, source_type)
                # Imagem passa pelo Tesseract; áudio passa pelo mecanismo local
                # configurado em transcription.py, sem envio automático externo.
                source_text = extract_text_from_image(uploaded_file) if source_type == 'image' else transcribe_audio(uploaded_file)
            if not source_text:
                raise ValidationError('Informe um texto ou envie um arquivo com conteúdo legível.')
            result = extract_prescription(source_text)
            if request.user.is_authenticated:
                item = Prescription.objects.create(owner=request.user, source_text=source_text, source_type=source_type, source_name=uploaded_file.name if uploaded_file else '', **result)
                audit(request, 'prescription.create', metadata={'id': item.pk})
            else:
                audit(request, 'demo.extract')
        except (ValidationError, ValueError, RuntimeError) as exc:
            # Mostra apenas mensagens controladas pelo aplicativo; nunca devolve
            # traceback nem dados do arquivo para o navegador.
            safe_errors = {
                'A imagem é grande demais para o processamento automático.',
                'O arquivo enviado não contém uma imagem válida.',
                'O OCR não conseguiu processar esta imagem no tempo limite.',
            }
            error = str(exc) if str(exc) in safe_errors else 'Não foi possível processar a entrada. Verifique o formato e tente novamente.'
            logger.warning('Entrada rejeitada: tipo=%s erro=%s', source_type, exc.__class__.__name__)
            audit(request, 'prescription.create', 'failure')
    history = Prescription.objects.filter(owner=request.user)[:8] if request.user.is_authenticated else []
    return render(request, 'extractor/dashboard.html', {'result': result, 'source_text': source_text, 'history': history, 'source_type': source_type, 'error': error})


def clear_history(request):
    # A exclusão sempre é limitada ao usuário autenticado atual.
    if request.method == 'POST' and request.user.is_authenticated:
        count, _ = Prescription.objects.filter(owner=request.user).delete()
        audit(request, 'history.clear', metadata={'count': count})
    return redirect('dashboard')


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        audit(request, 'signup', user=user)
        return redirect('dashboard')
    return render(request, 'registration/signup.html', {'form': form})
