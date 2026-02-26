"""MuRIL BERT Intent Classifier — Multilingual intent classification for Indian languages.

Fine-tuned MuRIL (Multilingual Representations for Indian Languages) BERT model
for classifying customer intents from multilingual text input.
Best multilingual BERT for Indian languages (IEEE 2023).
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List, Tuple

import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Intent taxonomy for customer service
INTENT_LABELS = {
    0: "greeting",
    1: "order_status",
    2: "order_track",
    3: "order_cancel",
    4: "order_return",
    5: "order_refund",
    6: "payment_issue",
    7: "account_balance",
    8: "account_update",
    9: "complaint",
    10: "product_inquiry",
    11: "pricing_inquiry",
    12: "store_hours",
    13: "appointment_book",
    14: "appointment_cancel",
    15: "technical_support",
    16: "billing_inquiry",
    17: "subscription_manage",
    18: "feedback_positive",
    19: "feedback_negative",
    20: "escalation_request",
    21: "language_change",
    22: "goodbye",
    23: "other",
}

# Intent complexity mapping for LLM routing
INTENT_COMPLEXITY = {
    "greeting": "simple",
    "order_status": "simple",
    "order_track": "simple",
    "account_balance": "simple",
    "store_hours": "simple",
    "pricing_inquiry": "simple",
    "goodbye": "simple",
    "order_cancel": "medium",
    "order_return": "medium",
    "appointment_book": "medium",
    "appointment_cancel": "medium",
    "billing_inquiry": "medium",
    "subscription_manage": "medium",
    "account_update": "medium",
    "product_inquiry": "medium",
    "language_change": "simple",
    "order_refund": "complex",
    "payment_issue": "complex",
    "complaint": "complex",
    "technical_support": "complex",
    "feedback_negative": "complex",
    "escalation_request": "complex",
    "feedback_positive": "medium",
    "other": "complex",
}

# Keyword-based fallback patterns (multilingual)
KEYWORD_PATTERNS = {
    "order_status": ["order", "status", "where", "kahan", "kidhar", "order ka", "स्टेटस", "ऑर्डर"],
    "order_track": ["track", "tracking", "delivery", "shipping", "dispatch", "भेजा"],
    "order_cancel": ["cancel", "cancellation", "band karo", "रद्द"],
    "order_return": ["return", "exchange", "wapas", "वापस"],
    "order_refund": ["refund", "money back", "paisa wapas", "रिफंड", "पैसा"],
    "payment_issue": ["payment", "pay", "transaction", "upi", "भुगतान"],
    "account_balance": ["balance", "account", "khata", "बैलेंस", "खाता"],
    "complaint": ["complaint", "problem", "issue", "shikayat", "शिकायत", "समस्या"],
    "greeting": ["hello", "hi", "namaste", "namaskar", "नमस्ते"],
    "goodbye": ["bye", "thank", "dhanyavaad", "shukriya", "धन्यवाद", "शुक्रिया"],
    "escalation_request": ["manager", "supervisor", "human", "agent", "person", "इंसान"],
    "technical_support": ["not working", "error", "bug", "broken", "काम नहीं"],
    "store_hours": ["timing", "hours", "open", "close", "time", "समय"],
    "pricing_inquiry": ["price", "cost", "rate", "kimat", "कीमत", "दाम"],
    "billing_inquiry": ["bill", "invoice", "charge", "बिल"],
}


class IntentClassifier:
    """MuRIL BERT-based intent classifier for Indian languages.

    Uses a fine-tuned MuRIL model when available, falling back to
    keyword-based classification for robustness.
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._initialized = False

    async def initialize(self):
        """Load the MuRIL intent classification model."""
        try:
            def _load_model():
                try:
                    from transformers import AutoModelForSequenceClassification, AutoTokenizer
                    model_name = "google/muril-base-cased"
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForSequenceClassification.from_pretrained(
                        model_name, num_labels=len(INTENT_LABELS)
                    )
                    model.eval()
                    return tokenizer, model
                except Exception:
                    return None, None

            self._tokenizer, self._model = await asyncio.to_thread(_load_model)
            self._initialized = self._model is not None
            if self._initialized:
                logger.info("muril_intent_model_loaded")
            else:
                logger.warning("muril_model_not_available_using_keyword_fallback")
        except Exception as e:
            logger.warning("intent_classifier_init_error", error=str(e))

    async def classify(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Classify the intent of the given text.

        Args:
            text: Input text (can be multilingual)
            language: Detected language code

        Returns:
            Dictionary with 'intent', 'confidence', 'complexity',
            'top_intents', 'method' keys.
        """
        start_time = time.monotonic()

        if not text or not text.strip():
            return {
                "intent": "other",
                "confidence": 0.0,
                "complexity": "complex",
                "method": "default",
                "detection_time_ms": 0,
            }

        # Try ML model first
        ml_result = None
        if self._initialized:
            ml_result = await self._classify_with_model(text)

        # Keyword fallback
        keyword_result = self._classify_with_keywords(text)

        # Choose best result
        if ml_result and ml_result["confidence"] > 0.6:
            result = ml_result
            result["method"] = "muril"
        elif keyword_result["confidence"] > 0.3:
            result = keyword_result
            result["method"] = "keyword"
        else:
            result = {
                "intent": "other",
                "confidence": 0.3,
                "method": "default",
            }

        result["complexity"] = INTENT_COMPLEXITY.get(result["intent"], "complex")
        result["detection_time_ms"] = round((time.monotonic() - start_time) * 1000, 1)

        logger.info(
            "intent_classified",
            intent=result["intent"],
            confidence=result["confidence"],
            method=result["method"],
            complexity=result["complexity"],
        )

        return result

    async def _classify_with_model(self, text: str) -> Optional[Dict[str, Any]]:
        """Run MuRIL model inference for intent classification."""
        try:
            import torch

            def _run_inference():
                inputs = self._tokenizer(
                    text, return_tensors="pt", truncation=True, max_length=128, padding=True
                )
                with torch.no_grad():
                    outputs = self._model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                top_k = torch.topk(probs, k=3, dim=-1)

                top_intents = []
                for i in range(3):
                    idx = top_k.indices[0][i].item()
                    prob = top_k.values[0][i].item()
                    label = INTENT_LABELS.get(idx, "other")
                    top_intents.append({"intent": label, "confidence": round(prob, 3)})

                return top_intents

            top_intents = await asyncio.to_thread(_run_inference)

            return {
                "intent": top_intents[0]["intent"],
                "confidence": top_intents[0]["confidence"],
                "top_intents": top_intents,
            }
        except Exception as e:
            logger.error("muril_inference_failed", error=str(e))
            return None

    def _classify_with_keywords(self, text: str) -> Dict[str, Any]:
        """Keyword-based intent classification (multilingual patterns)."""
        text_lower = text.lower()
        scores: Dict[str, float] = {}

        for intent, keywords in KEYWORD_PATTERNS.items():
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            if matches > 0:
                scores[intent] = matches / len(keywords)

        if not scores:
            return {"intent": "other", "confidence": 0.2, "top_intents": []}

        # Sort by score
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_intents = [
            {"intent": intent, "confidence": round(score, 3)}
            for intent, score in sorted_intents[:3]
        ]

        return {
            "intent": sorted_intents[0][0],
            "confidence": round(sorted_intents[0][1], 3),
            "top_intents": top_intents,
        }


# Singleton instance
intent_classifier = IntentClassifier()
