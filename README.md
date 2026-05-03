# PII Scrubber API

Detect and remove Personally Identifiable Information from text.
Supports Polish and international formats.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/scrub` | Remove PII from a single text |
| POST | `/detect` | Detect PII without modifying text |
| POST | `/scrub/batch` | Process up to 50 texts at once |
| GET | `/health` | Liveness check |

## Supported entity types

| Type | Examples |
|------|---------|
| `EMAIL` | jan@firma.pl |
| `PHONE` | +48 604 123 456, 22 123 45 67 |
| `PESEL` | 44051401458 (checksum validated) |
| `NIP` | 526-025-02-74 (checksum validated) |
| `IBAN` | PL61 1090 1014 0000 0712 1981 2874 |
| `CREDIT_CARD` | 4532 0151 1283 0366 (Luhn validated) |
| `IP_ADDRESS` | 192.168.1.100 |
| `NAME` | Jan Kowalski |

---

## Quick start (local)

```bash
# 1. Clone / download this folder
cd pii-scrubber-api

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
uvicorn app.main:app --reload

# 4. Open docs
# http://localhost:8000/docs
```

### Example request

```bash
curl -X POST http://localhost:8000/scrub \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Skontaktuj się z Janem Kowalskim: jan@firma.pl, tel. 604 123 456, PESEL 44051401458.",
    "replacement_pattern": "[{type}]"
  }'
```

Response:
```json
{
  "scrubbed_text": "Skontaktuj się z [NAME]: [EMAIL], tel. [PHONE], PESEL [PESEL].",
  "detected_entities": [
    { "entity_type": "NAME", "value": "Janem Kowalskim", "start": 17, "end": 32, "confidence": 0.8 },
    { "entity_type": "EMAIL", "value": "jan@firma.pl", "start": 34, "end": 46, "confidence": 0.95 }
  ],
  "entities_count": 4,
  "chars_removed": -12
}
```

