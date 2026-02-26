"""PII Redactor — Microsoft Presidio-based PII detection and redaction.

Identifies and masks personal data (Aadhaar, PAN, phone, email, names, etc.)
in conversation text before storage or analytics.
Supports Indian PII patterns alongside standard ones.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PIIEntity:
    """Detected PII entity."""
    entity_type: str
    text: str
    start: int
    end: int
    score: float


# ── Indian-specific regex patterns ────────────────────

INDIAN_PII_PATTERNS = {
    "AADHAAR_NUMBER": re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b"),
    "PAN_NUMBER": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "INDIAN_PHONE": re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b"),
    "IFSC_CODE": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "INDIAN_PASSPORT": re.compile(r"\b[A-Z]\d{7}\b"),
    "GSTIN": re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]\b"),
    "VEHICLE_REGISTRATION": re.compile(
        r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{1,4}\b"
    ),
    "UPI_ID": re.compile(r"\b[\w.]+@[a-z]{2,}\b"),
    "BANK_ACCOUNT": re.compile(r"\b\d{9,18}\b"),
}

STANDARD_PII_PATTERNS = {
    "EMAIL_ADDRESS": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    ),
    "CREDIT_CARD": re.compile(
        r"\b(?:\d{4}[\s-]?){3}\d{4}\b"
    ),
    "DATE_OF_BIRTH": re.compile(
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    ),
    "IP_ADDRESS": re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    ),
}

# Mask patterns per entity type
MASK_PATTERNS = {
    "AADHAAR_NUMBER": "XXXX-XXXX-****",
    "PAN_NUMBER": "XXXXX****X",
    "INDIAN_PHONE": "+91-XXXXXXXX**",
    "CREDIT_CARD": "****-****-****-****",
    "EMAIL_ADDRESS": "***@***.***",
    "BANK_ACCOUNT": "XXXXXXXXX***",
    "DEFAULT": "[REDACTED]",
}


class PIIRedactor:
    """Multi-strategy PII detection and redaction.

    Uses:
    1. Microsoft Presidio (when available)
    2. Custom Indian PII regex patterns
    3. Standard PII regex patterns
    """

    def __init__(self):
        self._presidio_available = False
        self._analyzer = None
        self._anonymizer = None

    async def initialize(self):
        """Try to load Presidio analyzer + custom recognizers."""
        try:
            from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
            from presidio_anonymizer import AnonymizerEngine

            self._analyzer = AnalyzerEngine()

            # Register Indian PII recognizers
            for entity_type, pattern in INDIAN_PII_PATTERNS.items():
                recognizer = PatternRecognizer(
                    supported_entity=entity_type,
                    patterns=[
                        Pattern(
                            name=entity_type.lower(),
                            regex=pattern.pattern,
                            score=0.85,
                        )
                    ],
                )
                self._analyzer.registry.add_recognizer(recognizer)

            self._anonymizer = AnonymizerEngine()
            self._presidio_available = True
            logger.info("pii_redactor_presidio_loaded")
        except ImportError:
            logger.warning("pii_redactor_presidio_unavailable_using_regex")
            self._presidio_available = False
        except Exception as e:
            logger.error("pii_redactor_init_error", error=str(e))
            self._presidio_available = False

    def detect(self, text: str, language: str = "en") -> List[PIIEntity]:
        """Detect PII entities in text.

        Returns list of detected PII entities with positions and scores.
        """
        entities: List[PIIEntity] = []

        # Try Presidio first
        if self._presidio_available and self._analyzer:
            try:
                results = self._analyzer.analyze(
                    text=text,
                    language="en",  # Presidio primarily supports English
                    entities=None,  # Detect all
                    score_threshold=0.5,
                )
                for result in results:
                    entities.append(
                        PIIEntity(
                            entity_type=result.entity_type,
                            text=text[result.start : result.end],
                            start=result.start,
                            end=result.end,
                            score=result.score,
                        )
                    )
            except Exception as e:
                logger.warning("presidio_detection_error", error=str(e))

        # Always run custom Indian patterns (they may catch things Presidio misses)
        for entity_type, pattern in {
            **INDIAN_PII_PATTERNS,
            **STANDARD_PII_PATTERNS,
        }.items():
            for match in pattern.finditer(text):
                # Avoid duplicates with Presidio results
                overlap = any(
                    e.start <= match.start() < e.end or e.start < match.end() <= e.end
                    for e in entities
                )
                if not overlap:
                    entities.append(
                        PIIEntity(
                            entity_type=entity_type,
                            text=match.group(),
                            start=match.start(),
                            end=match.end(),
                            score=0.85,
                        )
                    )

        # Sort by position
        entities.sort(key=lambda e: e.start)
        return entities

    def redact(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Detect and redact PII from text.

        Returns:
            Dictionary with 'redacted_text', 'entities_found', 'entity_count'
        """
        entities = self.detect(text, language)

        if not entities:
            return {
                "redacted_text": text,
                "entities_found": [],
                "entity_count": 0,
            }

        # Build redacted text by replacing entities from end to start
        redacted = text
        for entity in reversed(entities):
            mask = MASK_PATTERNS.get(entity.entity_type, MASK_PATTERNS["DEFAULT"])
            redacted = redacted[: entity.start] + mask + redacted[entity.end :]

        return {
            "redacted_text": redacted,
            "entities_found": [
                {
                    "type": e.entity_type,
                    "score": e.score,
                    "position": {"start": e.start, "end": e.end},
                }
                for e in entities
            ],
            "entity_count": len(entities),
        }

    def redact_for_logging(self, text: str) -> str:
        """Quick redaction for log-safe output."""
        result = self.redact(text)
        return result["redacted_text"]


# Singleton
pii_redactor = PIIRedactor()
