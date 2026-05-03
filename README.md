# PII Scrubber API

Detect and remove Personally Identifiable Information from text.
Supports Polish and international formats — ready to deploy and monetize on RapidAPI.

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

---

## Deploy on Railway (free — 500h/month)

1. Utwórz konto na [railway.app](https://railway.app)
2. **New Project → Deploy from GitHub repo**
3. Wgraj ten folder na GitHub (wystarczy publiczne repo)
4. Railway automatycznie wykryje `Dockerfile` i zbuduje obraz
5. Po deployu dostaniesz URL w stylu `https://pii-scrubber-api-production.up.railway.app`
6. Sprawdź: `GET /health` → `{"status": "ok"}`

> Railway free tier: 512 MB RAM, 1 vCPU — w zupełności wystarczy dla tego API.

---

## Deploy on Render (alternatywa)

1. Konto na [render.com](https://render.com)
2. **New → Web Service → Connect repo**
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Instancja: **Free** (usypia po 15 min bezczynności — dla startu OK)

---

## Monetyzacja przez RapidAPI

### Krok 1 — Dodaj API

1. Przejdź na [rapidapi.com/provider](https://rapidapi.com/provider)
2. Kliknij **Add New API**
3. Wypełnij:
   - Name: `PII Scrubber`
   - Category: `Text Analysis`
   - Base URL: Twój Railway/Render URL

### Krok 2 — Dodaj endpointy

Dla każdego endpointu kliknij **Add Endpoint**:

| Endpoint | Method | Path |
|----------|--------|------|
| Scrub text | POST | /scrub |
| Detect only | POST | /detect |
| Batch scrub | POST | /scrub/batch |

Dla każdego dodaj przykładowe body z dokumentacji powyżej.

### Krok 3 — Utwórz plany cenowe

Przejdź do **Pricing** i dodaj plany:

| Plan | Cena | Limit |
|------|------|-------|
| Free | $0/mies. | 100 req/mies. |
| Basic | $9/mies. | 5 000 req/mies. |
| Pro | $29/mies. | 50 000 req/mies. |
| Ultra | $79/mies. | Unlimited |

> Ustaw **overages** (opłata za nadmiarowe requesty) na $0.002 za request — dochód pasywny bez limitu.

### Krok 4 — Opublikuj

1. **Visibility → Public**
2. Napisz opis w English (kupujący są głównie z USA/UK):
   - "Remove emails, phone numbers, PESELs, NIPs, IBANs and names from any text. GDPR-compliant. Supports Polish and international formats."
3. Dodaj tagi: `pii`, `gdpr`, `privacy`, `text`, `nlp`, `poland`

---

## Szacowane przychody

Przy 10 płacących użytkownikach (mieszanka Basic + Pro):
- 5 × Basic ($9) = $45
- 5 × Pro ($29) = $145
- **Razem: ~$190/mies. pasywnie**

RapidAPI pobiera 20% prowizji → Twoje: **~$152/mies.**

---

## Jak rozwijać API żeby zarabiać więcej

- [ ] Obsługa **PDF** (wyciąganie tekstu + scrubbing) — duży plus dla B2B
- [ ] Endpoint `/anonymize` — zamiast usuwać, zastępuje imiona generowanymi pseudonimami
- [ ] Wsparcie dla **DE, FR, UK** formatów (telefony, ID)
- [ ] Streaming response dla długich dokumentów
- [ ] Webhook po zakończeniu przetwarzania (async batch)
