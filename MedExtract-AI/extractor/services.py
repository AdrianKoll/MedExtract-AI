import re


def clean(value):
    return value.rstrip(' .;') if value else ''


def extract_prescription(text):
    normalized = re.sub(r'\s+', ' ', text).strip()
    first_sentence = re.split(r'[.!?]', normalized)[0]
    medicine_match = re.match(r'^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*)?)', first_sentence)
    strength_match = re.search(r'\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|ui|%)\b', normalized, re.I)
    quantity_match = re.search(r'(?:quantidade|qtd|caixa|cápsulas?|comprimidos?|frascos?)\s*[:\-]?\s*\d+', normalized, re.I)
    dosage_match = re.search(r'(?:tomar|usar|aplicar|ingerir)[^.]+?(?=\bpor\b|\bdurante\b|$)', normalized, re.I)
    duration_match = re.search(r'(?:por|durante)\s+\d+\s*(?:dias?|semanas?|meses?)', normalized, re.I)
    medicine = clean(medicine_match.group(1) if medicine_match else '')
    strength = clean(strength_match.group(0) if strength_match else '')
    quantity = clean(quantity_match.group(0) if quantity_match else '')
    dosage = clean(dosage_match.group(0) if dosage_match else '')
    duration = clean(duration_match.group(0) if duration_match else '')
    consumed = ' '.join(item for item in [medicine, strength, quantity, dosage, duration] if item)
    notes = normalized.replace(consumed, '').strip()
    return {'medicine': medicine, 'strength': strength, 'quantity': quantity, 'dosage': dosage, 'duration': duration, 'notes': notes}
