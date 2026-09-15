import time
from collections import defaultdict, deque

from django.conf import settings
from django.http import JsonResponse

from .models import AuditEvent

_requests = defaultdict(deque)


def client_ip(request):
    return request.META.get('REMOTE_ADDR', '')[:45] or None


class SecurityAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        key = f"{client_ip(request)}:{request.path}"
        now = time.monotonic()
        bucket = _requests[key]
        while bucket and now - bucket[0] > settings.RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= settings.RATE_LIMIT_MAX_REQUESTS and request.path.startswith('/api/'):
            return JsonResponse({'error': 'Limite de requisições excedido. Tente novamente mais tarde.'}, status=429)
        bucket.append(now)
        response = self.get_response(request)
        if request.path.startswith('/api/') and request.method in {'POST', 'DELETE', 'PATCH', 'PUT'}:
            try:
                AuditEvent.objects.create(user=request.user if request.user.is_authenticated else None, action=f'{request.method} {request.path}', outcome=str(response.status_code), ip_address=client_ip(request))
            except Exception:
                pass
        return response
