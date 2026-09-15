import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Cria um backup consistente do banco e remove backups antigos.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default=os.environ.get('BACKUP_DIR', str(settings.BASE_DIR / 'backups')))
        parser.add_argument('--keep', type=int, default=int(os.environ.get('BACKUP_KEEP', '14')))

    def handle(self, *args, **options):
        output = Path(options['output_dir'])
        output.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        database_url = os.environ.get('DATABASE_URL', '')
        if database_url.startswith(('postgres://', 'postgresql://')):
            destination = output / f'medextract-{stamp}.dump'
            result = subprocess.run(['pg_dump', '--format=custom', '--file', str(destination), database_url], capture_output=True, text=True)
            if result.returncode:
                raise CommandError(result.stderr or 'pg_dump falhou')
        else:
            source = Path(settings.DATABASES['default']['NAME'])
            if not source.exists():
                raise CommandError(f'Banco não encontrado: {source}')
            destination = output / f'medextract-{stamp}.sqlite3'
            shutil.copy2(source, destination)
        backups = sorted(output.glob('medextract-*'), key=lambda item: item.stat().st_mtime, reverse=True)
        for old in backups[options['keep']:]:
            old.unlink(missing_ok=True)
        self.stdout.write(self.style.SUCCESS(f'backup criado em {destination}'))
