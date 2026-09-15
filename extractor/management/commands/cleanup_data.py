from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from extractor.models import AuditEvent, ApiToken, Prescription


class Command(BaseCommand):
    help = 'Aplica a política de retenção de dados e remove demonstrações antigas.'

    def handle(self, *args, **options):
        now = timezone.now()
        demo_cutoff = now - timedelta(hours=settings.DEMO_RETENTION_HOURS)
        audit_cutoff = now - timedelta(days=settings.AUDIT_RETENTION_DAYS)
        prescription_cutoff = now - timedelta(days=settings.PRESCRIPTION_RETENTION_DAYS)
        demos, _ = Prescription.objects.filter(owner__isnull=True, created_at__lt=demo_cutoff).delete()
        prescriptions, _ = Prescription.objects.filter(created_at__lt=prescription_cutoff).delete()
        audits, _ = AuditEvent.objects.filter(created_at__lt=audit_cutoff).delete()
        tokens, _ = ApiToken.objects.filter(expires_at__lt=now).delete()
        self.stdout.write(self.style.SUCCESS(f'limpeza concluída: demos={demos}, prescriptions={prescriptions}, auditoria={audits}, tokens={tokens}'))
