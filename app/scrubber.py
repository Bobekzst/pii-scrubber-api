import re
from typing import List, Optional, Set
from app.models import EntityType, DetectedEntity
from app.names_pl import ALL_NAMES


# ─── Regex Patterns ────────────────────────────────────────────────────────────

EMAIL_RE = re.compile(
    r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b'
)

# Polish mobile + landline; handles +48 prefix and various separators
PHONE_RE = re.compile(
    r'(?<!\d)'
    r'(?:\+48[\s\-]?)?'
    r'(?:\d{3}[\s\-]?\d{3}[\s\-]?\d{3}'        # 9-digit mobile
    r'|\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'  # landline xx xxx xx xx
    r')'
    r'(?!\d)'
)

# PESEL: exactly 11 digits (validated separately)
PESEL_RE = re.compile(r'(?<!\d)\d{11}(?!\d)')

# NIP: 10 digits with optional separators XXX-XXX-XX-XX or XXXXXXXXXX
NIP_RE = re.compile(
    r'(?<!\d)'
    r'\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'
    r'(?!\d)'
)

# Polish IBAN: PL + 26 digits
IBAN_RE = re.compile(
    r'\bPL\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}\b',
    re.IGNORECASE,
)

# Credit card: 16 digits with optional separators (Luhn validated)
CREDIT_CARD_RE = re.compile(
    r'(?<!\d)\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)'
)

# IPv4
IP_RE = re.compile(
    r'(?<!\d)(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
    r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?!\d)'
)

# Name: two capitalized words in sequence (first name from list + any surname)
# Looks for known first name followed by capitalized word
_name_pattern = r'\b(' + '|'.join(re.escape(n) for n in ALL_NAMES) + r')\s+([A-ZŁŚŻŹĆĄĘÓŃ][a-złśżźćąęóń]{2,})\b'
NAME_RE = re.compile(_name_pattern)


# ─── Validators ────────────────────────────────────────────────────────────────

def _validate_pesel(pesel: str) -> bool:
    if len(pesel) != 11 or not pesel.isdigit():
        return False
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    total = sum(int(pesel[i]) * weights[i] for i in range(10))
    control = (10 - (total % 10)) % 10
    return control == int(pesel[10])


def _validate_nip(nip: str) -> bool:
    digits = re.sub(r'[\s\-]', '', nip)
    if len(digits) != 10 or not digits.isdigit():
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    total = sum(int(digits[i]) * weights[i] for i in range(9))
    remainder = total % 11
    return remainder < 10 and remainder == int(digits[9])


def _luhn_check(number: str) -> bool:
    digits = re.sub(r'[\s\-]', '', number)
    if not digits.isdigit() or len(digits) != 16:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# ─── Core Scrubber ─────────────────────────────────────────────────────────────

def detect_entities(
    text: str,
    entity_types: Optional[Set[EntityType]] = None,
) -> List[DetectedEntity]:
    """
    Scan text and return all detected PII entities with their positions.
    entity_types=None means detect all supported types.
    """
    all_types = set(EntityType) if entity_types is None else entity_types
    found: List[DetectedEntity] = []

    # Track spans that are already claimed to avoid double-tagging
    occupied: List[tuple] = []

    def _add(etype: EntityType, m: re.Match, confidence: float = 0.95):
        s, e = m.start(), m.end()
        # Skip if overlaps with an already-claimed span
        for os, oe in occupied:
            if not (e <= os or s >= oe):
                return
        occupied.append((s, e))
        found.append(DetectedEntity(
            entity_type=etype,
            value=m.group(0),
            start=s,
            end=e,
            confidence=confidence,
        ))

    if EntityType.EMAIL in all_types:
        for m in EMAIL_RE.finditer(text):
            _add(EntityType.EMAIL, m)

    if EntityType.IBAN in all_types:
        for m in IBAN_RE.finditer(text):
            _add(EntityType.IBAN, m)

    if EntityType.CREDIT_CARD in all_types:
        for m in CREDIT_CARD_RE.finditer(text):
            if _luhn_check(m.group(0)):
                _add(EntityType.CREDIT_CARD, m, confidence=0.9)

    if EntityType.PESEL in all_types:
        for m in PESEL_RE.finditer(text):
            if _validate_pesel(m.group(0)):
                _add(EntityType.PESEL, m)

    if EntityType.NIP in all_types:
        for m in NIP_RE.finditer(text):
            if _validate_nip(m.group(0)):
                _add(EntityType.NIP, m)

    if EntityType.PHONE in all_types:
        for m in PHONE_RE.finditer(text):
            raw = re.sub(r'[\s\-]', '', m.group(0).replace('+48', ''))
            # Only accept 9-digit local numbers
            if len(raw) == 9:
                _add(EntityType.PHONE, m, confidence=0.85)

    if EntityType.IP_ADDRESS in all_types:
        for m in IP_RE.finditer(text):
            _add(EntityType.IP_ADDRESS, m)

    if EntityType.NAME in all_types:
        for m in NAME_RE.finditer(text):
            _add(EntityType.NAME, m, confidence=0.8)

    # Sort by position for consistent output
    found.sort(key=lambda e: e.start)
    return found


def scrub_text(
    text: str,
    entity_types: Optional[Set[EntityType]] = None,
    replacement_pattern: str = "[{type}]",
) -> tuple[str, List[DetectedEntity]]:
    """
    Replace all detected PII in text with the replacement pattern.
    Returns (scrubbed_text, detected_entities).
    """
    entities = detect_entities(text, entity_types)
    if not entities:
        return text, []

    # Replace from end to start so positions stay valid
    result = list(text)
    for entity in reversed(entities):
        replacement = replacement_pattern.replace("{type}", entity.entity_type.value)
        result[entity.start:entity.end] = list(replacement)

    return "".join(result), entities
