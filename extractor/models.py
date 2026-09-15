import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class ApiToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=120, default='API token')
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=timezone.now)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_valid(self):
        return self.revoked_at is None and self.expires_at > timezone.now() and self.user.is_active

    @staticmethod
    def issue_for_user(user, name='API token', lifetime=None):
        lifetime = lifetime or settings.API_TOKEN_LIFETIME
        raw_token = f'medx_{secrets.token_urlsafe(32)}'
        credential = ApiToken.objects.create(
            user=user,
            name=name[:120],
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=timezone.now() + lifetime,
        )
        return raw_token

    @staticmethod
    def find_credential(raw_token):
        if not raw_token or not raw_token.startswith('medx_'):
            return None
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        try:
            credential = ApiToken.objects.select_related('user').get(token_hash=token_hash)
        except ApiToken.DoesNotExist:
            return None
        if not credential.is_valid:
            return None
        credential.last_used_at = timezone.now()
        credential.save(update_fields=['last_used_at'])
        return credential

    @staticmethod
    def find_user(raw_token):
        credential = ApiToken.find_credential(raw_token)
        return credential.user if credential else None


class Integration(models.Model):
    PROVIDERS = [('ocr', 'OCR'), ('transcription', 'Transcrição')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='integrations')
    provider = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    endpoint = models.URLField(max_length=500, blank=True)
    secret_encrypted = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'provider', 'name'], name='unique_user_integration')]


class AuditEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_events')
    action = models.CharField(max_length=100)
    outcome = models.CharField(max_length=30, default='success')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['created_at']), models.Index(fields=['user', 'created_at'])]


class Prescription(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions', null=True, blank=True)
    source_text = models.TextField()
    source_type = models.CharField(max_length=20, default='text')
    source_name = models.CharField(max_length=255, blank=True)
    medicine = models.CharField(max_length=160, blank=True)
    strength = models.CharField(max_length=80, blank=True)
    quantity = models.CharField(max_length=80, blank=True)
    dosage = models.CharField(max_length=240, blank=True)
    duration = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.medicine or 'Prescrição sem medicamento identificado'
