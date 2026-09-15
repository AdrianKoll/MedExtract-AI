import hashlib
import time
from collections import defaultdict, deque

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache

from .middleware import client_ip
from .models import AuditEvent


def audit(request, action, outcome='success', metadata=None, user=None):
    try:
        AuditEvent.objects.create(user=user or (request.user if getattr(request, 'user', None) and request.user.is_authenticated else None), action=action, outcome=outcome, ip_address=client_ip(request), metadata=metadata or {})
    except Exception:
        pass


def login_with_protection(request, username, password):
    ip = client_ip(request) or 'unknown'
    digest = hashlib.sha256(f'{ip}:{username}'.lower().encode()).hexdigest()
    key = f'medextract-login:{digest}'
    attempts = cache.get(key, 0)
    if attempts >= settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        audit(request, 'login', 'blocked', {'reason': 'brute_force_lockout'})
        return None, True
    user = authenticate(username=username, password=password)
    if user is None:
        cache.set(key, attempts + 1, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        audit(request, 'login', 'failure')
    else:
        cache.delete(key)
        audit(request, 'login', 'success', user=user)
    return user, False
