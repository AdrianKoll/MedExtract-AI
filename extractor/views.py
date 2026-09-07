from django.shortcuts import redirect, render

from .models import Prescription
from .ocr import extract_text_from_image
from .services import extract_prescription
from .transcription import transcribe_audio


def dashboard(request):
    result = None
    source_text = ''
    source_type = 'text'
    error = ''
    if request.method == 'POST':
        source_text = request.POST.get('source_text', '').strip()
        uploaded_file = request.FILES.get('source_file')
        if uploaded_file:
            source_type = request.POST.get('source_type', 'image')
            try:
                if source_type == 'image':
                    source_text = extract_text_from_image(uploaded_file)
                elif source_type == 'audio':
                    source_text = transcribe_audio(uploaded_file)
            except Exception as exc:
                error = str(exc)
        if source_text:
            result = extract_prescription(source_text)
            Prescription.objects.create(source_text=source_text, source_type=source_type, source_name=uploaded_file.name if uploaded_file else '', **result)
    history = Prescription.objects.all()[:8]
    return render(request, 'extractor/dashboard.html', {'result': result, 'source_text': source_text, 'history': history, 'source_type': source_type, 'error': error})


def clear_history(request):
    if request.method == 'POST':
        Prescription.objects.all().delete()
    return redirect('dashboard')
