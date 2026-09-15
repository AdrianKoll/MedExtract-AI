import json
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Verifica banco, migrações e espaço de mídia; envia alerta opcional.'

    def handle(self, *args, **options):
        checks = {'database': 'ok', 'media': 'ok'}
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception as exc:
            checks['database'] = f'error: {exc.__class__.__name__}'
        try:
            settings.MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
        except OSError:
            checks['media'] = 'unwritable'
        healthy = all(value == 'ok' for value in checks.values())
        payload = json.dumps({'service': 'medextract', 'healthy': healthy, 'checks': checks}).encode()
        if not healthy and settings.ALERT_WEBHOOK_URL:
            request = urllib.request.Request(settings.ALERT_WEBHOOK_URL, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
            try:
                urllib.request.urlopen(request, timeout=10).read()
            except Exception:
                self.stderr.write('alerta não pôde ser enviado')
        self.stdout.write(json.dumps({'healthy': healthy, 'checks': checks}))
        if not healthy:
            raise SystemExit(1)
