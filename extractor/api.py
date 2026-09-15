import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ApiToken, Prescription
from .security import audit, login_with_protection
from .services import extract_prescription


def _user_from_token(request):
    authorization = request.headers.get('Authorization', '')
    if not authorization.startswith('Bearer '):
        return None, None
    credential = ApiToken.find_credential(authorization.removeprefix('Bearer ').strip())
    return (credential.user, credential) if credential else (None, None)


def _json_error(message, status):
    return JsonResponse({'error': message}, status=status)


def _serialize(prescription):
    return {'id': prescription.pk, 'source_type': prescription.source_type, 'source_name': prescription.source_name, 'medicine': prescription.medicine, 'strength': prescription.strength, 'quantity': prescription.quantity, 'dosage': prescription.dosage, 'duration': prescription.duration, 'notes': prescription.notes, 'created_at': prescription.created_at.isoformat()}


@csrf_exempt
@require_http_methods(['POST'])
def token(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return _json_error('JSON inválido.', 400)
    user, blocked = login_with_protection(request, str(payload.get('username', '')), str(payload.get('password', '')))
    if blocked:
        return _json_error('Muitas tentativas. Tente novamente mais tarde.', 429)
    if user is None or not user.is_active:
        return _json_error('Credenciais inválidas.', 401)
    raw = ApiToken.issue_for_user(user, str(payload.get('name', 'API token')))
    credential = ApiToken.find_credential(raw)
    return JsonResponse({'token': raw, 'expires_at': credential.expires_at.isoformat(), 'user': user.get_username()})


@csrf_exempt
@require_http_methods(['POST'])
def revoke_token(request):
    user, credential = _user_from_token(request)
    if user is None:
        return _json_error('Token Bearer obrigatório.', 401)
    credential.revoked_at = timezone.now()
    credential.save(update_fields=['revoked_at'])
    audit(request, 'token.revoke', user=user)
    return JsonResponse({'revoked': True})


@require_http_methods(['GET', 'POST'])
def prescriptions(request):
    user, _ = _user_from_token(request)
    if user is None:
        return _json_error('Token Bearer obrigatório.', 401)
    if request.method == 'GET':
        items = Prescription.objects.filter(owner=user)[:50]
        return JsonResponse({'results': [_serialize(item) for item in items]})
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return _json_error('JSON inválido.', 400)
    source_text = str(payload.get('source_text', '')).strip()
    if not source_text or len(source_text) > 20000:
        return _json_error('source_text é obrigatório e deve ter no máximo 20.000 caracteres.', 400)
    if payload.get('source_type', 'text') != 'text':
        return _json_error('A API aceita texto; use o endpoint web para uploads.', 400)
    result = extract_prescription(source_text)
    item = Prescription.objects.create(owner=user, source_text=source_text, source_type='text', **result)
    audit(request, 'prescription.create', user=user, metadata={'id': item.pk})
    return JsonResponse(_serialize(item), status=201)


@require_http_methods(['GET', 'DELETE'])
def prescription_detail(request, pk):
    user, _ = _user_from_token(request)
    if user is None:
        return _json_error('Token Bearer obrigatório.', 401)
    try:
        item = Prescription.objects.get(pk=pk, owner=user)
    except Prescription.DoesNotExist:
        return _json_error('Prescrição não encontrada.', 404)
    if request.method == 'DELETE':
        item.delete()
        audit(request, 'prescription.delete', user=user, metadata={'id': pk})
        return JsonResponse({'deleted': True})
    return JsonResponse(_serialize(item))
