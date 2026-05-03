from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class EntityType(str, Enum):
    EMAIL        = "EMAIL"
    PHONE        = "PHONE"
    PESEL        = "PESEL"
    NIP          = "NIP"
    IBAN         = "IBAN"
    CREDIT_CARD  = "CREDIT_CARD"
    IP_ADDRESS   = "IP_ADDRESS"
    NAME         = "NAME"


class ScrubRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000, description="Text to scrub")
    entities: Optional[List[EntityType]] = Field(
        None, description="Entity types to scrub. Defaults to all."
    )
    replacement_pattern: Optional[str] = Field(
        None,
        description="Replacement string. Use {type} for entity type placeholder. E.g. '[{type}]' → '[EMAIL]'. Defaults to '[{type}]'.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Skontaktuj się z Janem Kowalskim pod adresem jan@firma.pl lub 604 123 456.",
                "entities": None,
                "replacement_pattern": "[{type}]",
            }
        }
    }


class DetectedEntity(BaseModel):
    entity_type: EntityType
    value: str
    start: int
    end: int
    confidence: float = Field(..., ge=0.0, le=1.0)


class ScrubResponse(BaseModel):
    scrubbed_text: str
    detected_entities: List[DetectedEntity]
    entities_count: int
    chars_removed: int


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    entities: Optional[List[EntityType]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "PESEL: 92070483651, NIP: 527-281-45-11",
                "entities": ["PESEL", "NIP"],
            }
        }
    }


class DetectResponse(BaseModel):
    detected_entities: List[DetectedEntity]
    entities_count: int


class BatchScrubItem(BaseModel):
    id: Optional[str] = None
    text: str = Field(..., min_length=1, max_length=50_000)


class BatchScrubRequest(BaseModel):
    items: List[BatchScrubItem] = Field(..., min_length=1, max_length=50)
    entities: Optional[List[EntityType]] = None
    replacement_pattern: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {"id": "doc_1", "text": "Email: kowalski@example.com"},
                    {"id": "doc_2", "text": "Telefon: +48 601 234 567"},
                ],
                "entities": None,
            }
        }
    }


class BatchScrubResult(BaseModel):
    id: Optional[str]
    scrubbed_text: str
    entities_count: int


class BatchScrubResponse(BaseModel):
    results: List[BatchScrubResult]
    total_texts: int
    total_entities_found: int
