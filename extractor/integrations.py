import json

from django.core import signing
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Integration
from .api import _user_from_token, _json_error
from .security import audit


def _protect(value):
    return signing.dumps(value) if value else ''


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def integrations(request):
    user, _ = _user_from_token(request)
    if user is None:
        return _json_error('Token Bearer obrigatório.', 401)
    if request.method == 'GET':
        return JsonResponse({'results': [{'id': x.pk, 'provider': x.provider, 'name': x.name, 'endpoint': x.endpoint, 'enabled': x.enabled, 'created_at': x.created_at.isoformat()} for x in user.integrations.all()]})
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return _json_error('JSON inválido.', 400)
    provider = str(payload.get('provider', '')).strip().lower()
    name = str(payload.get('name', '')).strip()
    if provider not in {'ocr', 'transcription'} or not name:
        return _json_error('provider e name são obrigatórios; provider deve ser ocr ou transcription.', 400)
    item, _ = Integration.objects.update_or_create(user=user, provider=provider, name=name, defaults={'endpoint': str(payload.get('endpoint', '')).strip(), 'secret_encrypted': _protect(str(payload.get('secret', ''))), 'enabled': bool(payload.get('enabled', True))})
    audit(request, 'integration.upsert', user=user, metadata={'id': item.pk, 'provider': provider})
    return JsonResponse({'id': item.pk, 'provider': item.provider, 'name': item.name, 'enabled': item.enabled}, status=201)


@csrf_exempt
@require_http_methods(['DELETE'])
def integration_detail(request, pk):
    user, _ = _user_from_token(request)
    if user is None:
        return _json_error('Token Bearer obrigatório.', 401)
    deleted, _ = Integration.objects.filter(pk=pk, user=user).delete()
    if not deleted:
        return _json_error('Integração não encontrada.', 404)
    audit(request, 'integration.delete', user=user, metadata={'id': pk})
    return JsonResponse({'deleted': True})
