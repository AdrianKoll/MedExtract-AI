from django.db import models


class Prescription(models.Model):
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
