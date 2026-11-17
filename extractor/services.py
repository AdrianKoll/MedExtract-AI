import re


STRENGTH_PATTERN = r'\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|ui|%)'
MEDICINE_WITH_STRENGTH = re.compile(
    rf'\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*){{0,2}})\s+({STRENGTH_PATTERN})\b',
    re.I,
)


def clean(value):
    # Remove pontuação residual capturada pelas expressões regulares.
    return value.strip(' \t\r\n.,;:-') if value else ''


def _normalize(text):
    # OCR pode devolver Markdown, quebras de linha e espaços inconsistentes.
    # Retiramos somente a formatação, preservando o conteúdo da receita.
    without_markdown = re.sub(r'[*_`]+', '', text or '')
    return re.sub(r'\s+', ' ', without_markdown).strip()


def _medicine_candidates(text):
    # Retorna os offsets para separar a receita em blocos associados a cada
    # medicamento; a busca não depende de uma quantidade máxima de itens.
    candidates = []
    for match in MEDICINE_WITH_STRENGTH.finditer(text):
        medicine = clean(match.group(1))
        # OCR pode juntar o título da seção ao primeiro medicamento.
        for marker in ('prescrição médica', 'prescrição', 'receita médica'):
            if marker in medicine.lower():
                medicine = re.split(marker, medicine, maxsplit=1, flags=re.I)[-1].strip()
                break
        medicine = re.sub(r'^\d+[.)-]*\s*', '', medicine)
        strength = clean(match.group(2))
        if medicine:
            candidates.append({'medicine': medicine, 'strength': strength, 'start': match.start(), 'end': match.end()})
    return candidates


def _extract_fields(section):
    # Cada campo é procurado apenas no trecho até o próximo medicamento, para
    # que quantidade/posologia/duração não sejam atribuídas ao remédio errado.
    quantity_match = re.search(
        r'\b(?:quantidade|qtd)\s*[:\-]?\s*(\d+(?:\s+(?:comprimidos?|cápsulas?|frascos?|unidades?))?)',
        section,
        re.I,
    )
    if not quantity_match:
        quantity_match = re.search(
            r'\b(\d+\s+(?:comprimidos?|cápsulas?|frascos?|unidades?))\b', section, re.I
        )
    dosage_match = re.search(
        r'(?:tomar|usar|aplicar|ingerir)[^.]*?(?=\bpor\b|\bdurante\b|$)',
        section,
        re.I,
    )
    duration_match = re.search(
        r'\b(?:por|durante)\s+\d+\s*(?:dias?|semanas?|meses?)\b',
        section,
        re.I,
    )
    observation_match = re.search(
        r'(?:observa(?:ção|ções))\s*:\s*(.+?)(?=\s+(?:assinatura|$))',
        section,
        re.I,
    )
    return {
        'quantity': clean(quantity_match.group(1) if quantity_match else ''),
        'dosage': clean(dosage_match.group(0) if dosage_match else ''),
        'duration': clean(duration_match.group(0) if duration_match else ''),
        'notes': clean(observation_match.group(1) if observation_match else ''),
    }


def extract_prescription(text):
    # A extração é deliberadamente determinística e local: não envia a receita
    # para uma API externa e deixa os campos vazios quando não encontra evidência.
    normalized = _normalize(text)
    candidates = _medicine_candidates(normalized)

    if candidates:
        medications = []
        for index, candidate in enumerate(candidates):
            section_end = candidates[index + 1]['start'] if index + 1 < len(candidates) else len(normalized)
            fields = _extract_fields(normalized[candidate['end']:section_end])
            medications.append({
                'medicine': candidate['medicine'],
                'strength': candidate['strength'],
                **fields,
            })
    else:
        # Mantém a saída anterior para entradas sem par medicamento/concentração
        # reconhecível; a interface ainda apresenta um cartão de resultado.
        first_sentence = re.split(r'[.!?]', normalized)[0]
        medicine_match = re.match(
            r'^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9-]*)?)',
            first_sentence,
        )
        strength_match = re.search(rf'\b({STRENGTH_PATTERN})\b', normalized, re.I)
        fallback = {
            'medicine': clean(medicine_match.group(1) if medicine_match else ''),
            'strength': clean(strength_match.group(1) if strength_match else ''),
            **_extract_fields(normalized),
        }
        medications = [fallback]

    # Os campos no nível superior permanecem para clientes antigos da API e
    # versões anteriores do histórico; a lista contém os medicamentos completos.
    primary = medications[0]
    return {
        **primary,
        'medications': medications,
    }
