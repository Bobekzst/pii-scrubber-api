from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
import os
import io
import pdfplumber

from app.models import (
    ScrubRequest, ScrubResponse,
    DetectRequest, DetectResponse,
    BatchScrubRequest, BatchScrubResponse, BatchScrubResult,
    PDFScrubResponse,
    EntityType,
)
from app.scrubber import scrub_text, detect_entities

# ─── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ─── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PII Scrubber API",
    description=(
        "Detect and remove Personally Identifiable Information (PII) from text. "
        "Supports Polish and international formats: email, phone, PESEL, NIP, IBAN, "
        "credit cards, IP addresses and full names."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "API Support",
        "email": os.getenv("SUPPORT_EMAIL", "support@example.com"),
    },
    license_info={"name": "MIT"},
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─── Middleware: timing header ──────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.perf_counter() - start) * 1000:.1f}ms"
    return response


# ─── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Status"])
async def health():
    """Quick liveness check. Returns 200 when the service is running."""
    return {"status": "ok", "version": "1.0.0"}


# ─── /scrub ────────────────────────────────────────────────────────────────────
@app.post(
    "/scrub",
    response_model=ScrubResponse,
    tags=["PII"],
    summary="Scrub PII from text",
    description=(
        "Detects and replaces PII entities in the input text. "
        "By default all entity types are scrubbed and replaced with `[ENTITY_TYPE]`.\n\n"
        "**Supported entities:** EMAIL, PHONE, PESEL, NIP, IBAN, CREDIT_CARD, IP_ADDRESS, NAME\n\n"
        "**Limits:** 50 000 characters per request."
    ),
)
@limiter.limit("60/minute")
async def scrub(request: Request, body: ScrubRequest):
    entity_set = set(body.entities) if body.entities else None
    pattern = body.replacement_pattern or "[{type}]"

    scrubbed, entities = scrub_text(body.text, entity_set, pattern)

    return ScrubResponse(
        scrubbed_text=scrubbed,
        detected_entities=entities,
        entities_count=len(entities),
        chars_removed=len(body.text) - len(scrubbed),
    )


# ─── /detect ───────────────────────────────────────────────────────────────────
@app.post(
    "/detect",
    response_model=DetectResponse,
    tags=["PII"],
    summary="Detect PII without removing it",
    description=(
        "Scans the text and returns the position and type of every detected PII entity "
        "**without modifying the original text**. Useful for auditing or highlighting."
    ),
)
@limiter.limit("60/minute")
async def detect(request: Request, body: DetectRequest):
    entity_set = set(body.entities) if body.entities else None
    entities = detect_entities(body.text, entity_set)

    return DetectResponse(
        detected_entities=entities,
        entities_count=len(entities),
    )


# ─── /scrub/batch ──────────────────────────────────────────────────────────────
@app.post(
    "/scrub/batch",
    response_model=BatchScrubResponse,
    tags=["PII"],
    summary="Scrub PII from multiple texts",
    description=(
        "Process up to **50 texts** in a single request. "
        "Each item can carry an optional `id` field for correlation. "
        "Same entity and replacement options apply to all items."
    ),
)
@limiter.limit("20/minute")
async def scrub_batch(request: Request, body: BatchScrubRequest):
    entity_set = set(body.entities) if body.entities else None
    pattern = body.replacement_pattern or "[{type}]"

    results = []
    total_entities = 0

    for item in body.items:
        scrubbed, entities = scrub_text(item.text, entity_set, pattern)
        total_entities += len(entities)
        results.append(BatchScrubResult(
            id=item.id,
            scrubbed_text=scrubbed,
            entities_count=len(entities),
        ))

    return BatchScrubResponse(
        results=results,
        total_texts=len(body.items),
        total_entities_found=total_entities,
    )


# ─── /scrub/pdf ────────────────────────────────────────────────────────────────
@app.post(
    "/scrub/pdf",
    response_model=PDFScrubResponse,
    tags=["PII"],
    summary="Scrub PII from a PDF file",
    description=(
        "Upload a PDF file and get back the full extracted text with all PII removed. "
        "Supports multi-page PDFs up to **10 MB**. "
        "Scanned PDFs (image-only) are not supported — the PDF must contain selectable text."
    ),
)
@limiter.limit("20/minute")
async def scrub_pdf(
    request: Request,
    file: UploadFile = File(..., description="PDF file to scrub"),
    replacement_pattern: str = Form(default="[{type}]", description="Replacement pattern, e.g. [{{type}}] → [EMAIL]"),
    entities: str = Form(default="", description="Comma-separated entity types to scrub. Leave empty for all."),
):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()

    # 10 MB limit
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    # Extract text from PDF
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            pages = len(pdf.pages)
            full_text = "\n\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except Exception:
        raise HTTPException(status_code=422, detail="Could not parse PDF. Make sure it contains selectable text.")

    if not full_text:
        raise HTTPException(status_code=422, detail="No text found in PDF. Scanned image PDFs are not supported.")

    # Parse entity filter
    entity_set = None
    if entities.strip():
        try:
            entity_set = {EntityType(e.strip().upper()) for e in entities.split(",") if e.strip()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid entity type: {e}")

    # Scrub
    scrubbed, detected = scrub_text(full_text, entity_set, replacement_pattern)

    return PDFScrubResponse(
        scrubbed_text=scrubbed,
        detected_entities=detected,
        entities_count=len(detected),
        pages=pages,
        original_chars=len(full_text),
    )


# ─── Error handlers ────────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
