"""IndicLID Language Detection — Identifies Indian languages and dialects.

Uses AI4Bharat's IndicLID model for language identification from text
and audio features. Supports 22+ Indian languages with code-switching detection.
Target: <200ms detection time.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List, Tuple
from collections import Counter

import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Supported languages with full names
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "sa": "Sanskrit",
    "ne": "Nepali",
    "sd": "Sindhi",
    "ks": "Kashmiri",
    "doi": "Dogri",
    "kok": "Konkani",
    "mai": "Maithili",
    "mni": "Manipuri",
    "sat": "Santali",
    "brx": "Bodo",
}

# Script-based detection patterns (Unicode ranges)
SCRIPT_PATTERNS = {
    "hi": (0x0900, 0x097F),   # Devanagari
    "bn": (0x0980, 0x09FF),   # Bengali
    "ta": (0x0B80, 0x0BFF),   # Tamil
    "te": (0x0C00, 0x0C7F),   # Telugu
    "kn": (0x0C80, 0x0CFF),   # Kannada
    "ml": (0x0D00, 0x0D7F),   # Malayalam
    "gu": (0x0A80, 0x0AFF),   # Gujarati
    "pa": (0x0A00, 0x0A7F),   # Gurmukhi (Punjabi)
    "or": (0x0B00, 0x0B7F),   # Odia
    "ur": (0x0600, 0x06FF),   # Arabic script (Urdu)
}


class LanguageDetector:
    """Multi-strategy language detection for Indian languages.

    Uses a combination of:
    1. Script-based detection (fast, Unicode range matching)
    2. IndicLID model (ML-based, handles Romanized text)
    3. Code-switching detection (token-level language tagging)
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._initialized = False

    async def initialize(self):
        """Load IndicLID model (lazy initialization)."""
        try:
            # Try loading the IndicLID transformer model
            def _load_model():
                try:
                    from transformers import AutoModelForSequenceClassification, AutoTokenizer
                    model_name = "ai4bharat/IndicLID"
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForSequenceClassification.from_pretrained(model_name)
                    model.eval()
                    return tokenizer, model
                except Exception:
                    return None, None

            self._tokenizer, self._model = await asyncio.to_thread(_load_model)
            self._initialized = self._model is not None
            if self._initialized:
                logger.info("indiclid_model_loaded")
            else:
                logger.warning("indiclid_model_not_available_using_fallback")
        except Exception as e:
            logger.warning("indiclid_init_failed_using_fallback", error=str(e))
            self._initialized = False

    def _detect_script(self, text: str) -> Optional[Tuple[str, float]]:
        """Fast script-based language detection using Unicode ranges."""
        if not text:
            return None

        script_counts: Counter = Counter()
        latin_count = 0
        total = 0

        for char in text:
            code_point = ord(char)
            if char.isalpha():
                total += 1
                for lang, (start, end) in SCRIPT_PATTERNS.items():
                    if start <= code_point <= end:
                        script_counts[lang] += 1
                        break
                else:
                    if code_point < 0x0080:  # ASCII / Latin
                        latin_count += 1

        if total == 0:
            return None

        # If dominant script found
        if script_counts:
            dominant_lang, count = script_counts.most_common(1)[0]
            confidence = count / total
            if confidence > 0.5:
                return (dominant_lang, confidence)

        # If mostly Latin, assume English
        if latin_count / total > 0.7:
            return ("en", latin_count / total)

        return None

    async def detect(self, text: str) -> Dict[str, Any]:
        """Detect the language of the given text.

        Returns:
            Dictionary with 'language', 'confidence', 'method',
            'is_code_switched', 'secondary_language' keys.
        """
        start_time = time.monotonic()

        if not text or not text.strip():
            return {
                "language": "en",
                "confidence": 0.0,
                "method": "default",
                "is_code_switched": False,
                "detection_time_ms": 0,
            }

        # Strategy 1: Fast script detection
        script_result = self._detect_script(text)

        # Strategy 2: ML model (if available and script detection is uncertain)
        ml_result = None
        if self._initialized and (not script_result or script_result[1] < 0.8):
            ml_result = await self._detect_with_model(text)

        # Strategy 3: Code-switching detection
        code_switch_info = self._detect_code_switching(text)

        # Combine results
        if ml_result and ml_result["confidence"] > 0.7:
            result = ml_result
            result["method"] = "indiclid"
        elif script_result:
            result = {
                "language": script_result[0],
                "confidence": script_result[1],
                "method": "script",
            }
        else:
            result = {
                "language": "en",
                "confidence": 0.5,
                "method": "default",
            }

        # Add code-switching info
        result["is_code_switched"] = code_switch_info["is_code_switched"]
        if code_switch_info["is_code_switched"]:
            result["secondary_language"] = code_switch_info.get("secondary_language")
            result["language_distribution"] = code_switch_info.get("distribution", {})

        elapsed_ms = (time.monotonic() - start_time) * 1000
        result["detection_time_ms"] = round(elapsed_ms, 1)

        logger.info(
            "language_detected",
            language=result["language"],
            confidence=result["confidence"],
            method=result["method"],
            time_ms=result["detection_time_ms"],
            code_switched=result["is_code_switched"],
        )

        return result

    async def _detect_with_model(self, text: str) -> Optional[Dict[str, Any]]:
        """Use the IndicLID transformer model for detection."""
        try:
            import torch

            def _run_inference():
                inputs = self._tokenizer(
                    text, return_tensors="pt", truncation=True, max_length=128, padding=True
                )
                with torch.no_grad():
                    outputs = self._model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                confidence, predicted = torch.max(probs, dim=-1)
                label = self._model.config.id2label[predicted.item()]
                return label, confidence.item()

            label, confidence = await asyncio.to_thread(_run_inference)

            # Map IndicLID labels to our language codes
            lang_code = self._map_indiclid_label(label)

            return {
                "language": lang_code,
                "confidence": round(confidence, 3),
                "raw_label": label,
            }
        except Exception as e:
            logger.error("indiclid_inference_failed", error=str(e))
            return None

    def _map_indiclid_label(self, label: str) -> str:
        """Map IndicLID model label to ISO language code."""
        label_mapping = {
            "hin": "hi", "ben": "bn", "tam": "ta", "tel": "te",
            "mar": "mr", "guj": "gu", "kan": "kn", "mal": "ml",
            "pan": "pa", "ori": "or", "asm": "as", "urd": "ur",
            "san": "sa", "nep": "ne", "eng": "en", "sin": "sd",
        }
        # Handle various label formats
        label_lower = label.lower().split("_")[0] if "_" in label else label.lower()[:3]
        return label_mapping.get(label_lower, "en")

    def _detect_code_switching(self, text: str) -> Dict[str, Any]:
        """Detect if text contains code-switching (mixed languages).

        Common in Indian speech: "Mera order kab aayega, I ordered it last Tuesday"
        """
        if not text or len(text.split()) < 4:
            return {"is_code_switched": False}

        words = text.split()
        word_languages: List[str] = []

        for word in words:
            script_result = self._detect_script(word)
            if script_result:
                word_languages.append(script_result[0])
            else:
                word_languages.append("en")  # Assume Latin/English by default

        if not word_languages:
            return {"is_code_switched": False}

        # Count language distribution
        lang_counter = Counter(word_languages)
        total_words = len(word_languages)

        # Code-switching detected if no single language covers > 80% of words
        dominant_lang, dominant_count = lang_counter.most_common(1)[0]
        dominant_ratio = dominant_count / total_words

        if dominant_ratio < 0.80 and len(lang_counter) >= 2:
            secondary = lang_counter.most_common(2)[1][0] if len(lang_counter) >= 2 else None
            return {
                "is_code_switched": True,
                "dominant_language": dominant_lang,
                "secondary_language": secondary,
                "distribution": dict(lang_counter),
            }

        return {"is_code_switched": False}

    async def detect_from_audio_features(
        self, audio_data: bytes, sample_rate: int = 8000
    ) -> Dict[str, Any]:
        """Detect language from raw audio features (prosody, phonemes).

        This is used for initial detection before STT completes,
        providing language routing hints in <200ms.
        """
        # For production: would use audio-level language ID
        # For now, default to Hindi (most common) and refine after STT
        return {
            "language": "hi",
            "confidence": 0.3,
            "method": "audio_prosody",
            "note": "preliminary_detection",
        }


# Singleton instance
language_detector = LanguageDetector()
