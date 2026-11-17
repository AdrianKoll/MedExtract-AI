import re


STRENGTH_PATTERN = r'\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|ui|%)'
MEDICINE_WITH_STRENGTH = re.compile(
    rf'\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*){{0,2}})\s+({STRENGTH_PATTERN})\b',
    re.I,
)


def clean(value):
    # Remove pontuação residual capturada pelas expressões regulares.
    return value.rstrip(' .;,') if value else ''


def _normalize(text):
    # OCR pode devolver Markdown, quebras de linha e espaços inconsistentes.
    # Retiramos somente a formatação, preservando o conteúdo da receita.
    without_markdown = re.sub(r'[*_`]+', '', text or '')
    return re.sub(r'\s+', ' ', without_markdown).strip()


def _medicine_candidates(text):
    # Procura todos os pares "nome + concentração", em vez de assumir que
    # o primeiro texto da imagem é o medicamento.
    candidates = []
    for match in MEDICINE_WITH_STRENGTH.finditer(text):
        medicine = clean(match.group(1))
        # OCR pode juntar o título da seção ao primeiro medicamento.
        for marker in ('prescrição médica', 'prescrição', 'receita médica'):
            if marker in medicine.lower():
                medicine = re.split(marker, medicine, maxsplit=1, flags=re.I)[-1].strip()
                break
        strength = clean(match.group(2))
        pair = (medicine, strength)
        if pair not in candidates:
            candidates.append(pair)
    return candidates


def extract_prescription(text):
    # A extração é deliberadamente determinística e local: não envia a receita
    # para uma API externa e deixa os campos vazios quando não encontra evidência.
    normalized = _normalize(text)
    candidates = _medicine_candidates(normalized)
    first_sentence = re.split(r'[.!?]', normalized)[0]

    # Primeiro tenta um medicamento associado à concentração. Isso evita que
    # cabeçalhos como "Clínica ..." virem o nome do medicamento.
    if candidates:
        medicine, strength = candidates[0]
    else:
        medicine_match = re.match(
            r'^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*)?)',
            first_sentence,
        )
        strength_match = re.search(rf'\b({STRENGTH_PATTERN})\b', normalized, re.I)
        medicine = clean(medicine_match.group(1) if medicine_match else '')
        strength = clean(strength_match.group(1) if strength_match else '')

    # Cada expressão procura um campo independente para tolerar formatos variados.
    quantity_match = re.search(
        r'(?:quantidade|qtd|caixa|cápsulas?|comprimidos?|frascos?)\s*[:\-]?\s*\d+',
        normalized,
        re.I,
    )
    dosage_match = re.search(
        r'(?:tomar|usar|aplicar|ingerir)[^.]+?(?=\bpor\b|\bdurante\b|$)',
        normalized,
        re.I,
    )
    duration_match = re.search(
        r'(?:por|durante)\s+\d+\s*(?:dias?|semanas?|meses?)',
        normalized,
        re.I,
    )
    quantity = clean(quantity_match.group(0) if quantity_match else '')
    dosage = clean(dosage_match.group(0) if dosage_match else '')
    duration = clean(duration_match.group(0) if duration_match else '')

    # Não despeja o OCR inteiro em Notas: cabeçalhos, CPF e linhas já extraídas
    # tornam a saída confusa. Preserva apenas a seção explícita de observações.
    notes = ''
    observation_match = re.search(
        r'(?:observa(?:ção|ções))\s*:\s*(.+?)(?=\s+(?:assinatura|$))',
        normalized,
        re.I,
    )
    if observation_match:
        notes = clean(observation_match.group(1))

    other_medicines = [f'{name} {dose}' for name, dose in candidates[1:]]
    if other_medicines:
        other_text = f"Outros medicamentos identificados: {'; '.join(other_medicines)}."
        notes = f'{other_text} {notes}'.strip()

    return {
        'medicine': medicine,
        'strength': strength,
        'quantity': quantity,
        'dosage': dosage,
        'duration': duration,
        'notes': notes,
    }
