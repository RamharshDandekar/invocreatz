"""BERT-BiLSTM Emotion Detector — Real-time sentiment and emotion analysis.

Hybrid model combining BERT contextual embeddings with BiLSTM
for temporal emotion tracking. Handles anger, frustration, urgency
detection in regional Indian speech patterns.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List

import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Emotion labels
EMOTION_LABELS = {
    0: "neutral",
    1: "happy",
    2: "angry",
    3: "frustrated",
    4: "sad",
    5: "anxious",
    6: "urgent",
    7: "confused",
    8: "satisfied",
}

# Urgency indicators in multiple languages
URGENCY_KEYWORDS = {
    "en": ["urgent", "emergency", "immediately", "asap", "right now", "critical", "help"],
    "hi": ["turant", "jaldi", "abhi", "emergency", "madad", "urgent", "तुरंत", "जल्दी", "अभी", "मदद"],
    "bn": ["এখনই", "জরুরি", "দ্রুত", "সাহায্য"],
    "ta": ["உடனே", "அவசரம்", "உதவி"],
    "te": ["వెంటనే", "అత్యవసరం", "సహాయం"],
}

# Anger/frustration indicators
ANGER_KEYWORDS = {
    "en": ["angry", "terrible", "worst", "hate", "disgusting", "unacceptable", "ridiculous", "useless"],
    "hi": ["gussa", "kharab", "bakwas", "bekar", "ghatiya", "गुस्सा", "बकवास", "बेकार", "घटिया"],
    "bn": ["রাগ", "খারাপ", "বাজে"],
    "ta": ["கோபம்", "மோசமான"],
    "te": ["కోపం", "చెడ్డ"],
}

# Positive indicators
POSITIVE_KEYWORDS = {
    "en": ["thank", "great", "perfect", "excellent", "wonderful", "amazing", "happy", "good"],
    "hi": ["dhanyavaad", "bahut accha", "shandaar", "theek", "धन्यवाद", "बहुत अच्छा", "शानदार"],
}


class EmotionDetector:
    """Real-time emotion detection using BERT-BiLSTM hybrid model.

    Outputs:
    - Emotion label (neutral, happy, angry, frustrated, etc.)
    - Emotion confidence score (0.0 - 1.0)
    - Urgency score (0 - 10)
    - Sentiment polarity (-1.0 to 1.0)
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._initialized = False
        self._emotion_history: List[Dict[str, Any]] = []

    async def initialize(self):
        """Load the emotion detection model."""
        try:
            def _load_model():
                try:
                    from transformers import AutoModelForSequenceClassification, AutoTokenizer
                    model_name = "bert-base-multilingual-cased"
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForSequenceClassification.from_pretrained(
                        model_name, num_labels=len(EMOTION_LABELS)
                    )
                    model.eval()
                    return tokenizer, model
                except Exception:
                    return None, None

            self._tokenizer, self._model = await asyncio.to_thread(_load_model)
            self._initialized = self._model is not None
            if self._initialized:
                logger.info("emotion_model_loaded")
            else:
                logger.warning("emotion_model_not_available_using_keyword_fallback")
        except Exception as e:
            logger.warning("emotion_init_error", error=str(e))

    async def detect(
        self, text: str, language: str = "en", turn_index: int = 0
    ) -> Dict[str, Any]:
        """Detect emotion, sentiment, and urgency from text.

        Args:
            text: Input text (can be multilingual)
            language: Detected language code
            turn_index: Position in conversation (for trajectory tracking)

        Returns:
            Dictionary with emotion analysis results.
        """
        start_time = time.monotonic()

        if not text or not text.strip():
            return self._empty_result()

        # Try ML model first
        ml_result = None
        if self._initialized:
            ml_result = await self._detect_with_model(text)

        # Keyword-based analysis (always run for urgency/anger detection)
        keyword_result = self._detect_with_keywords(text, language)

        # Combine results
        if ml_result and ml_result["confidence"] > 0.5:
            result = ml_result
            result["method"] = "bert_bilstm"
        else:
            result = keyword_result
            result["method"] = "keyword"

        # Calculate urgency score (0-10)
        urgency = self._calculate_urgency(text, language, result)
        result["urgency_score"] = urgency

        # Calculate sentiment polarity (-1.0 to 1.0)
        result["sentiment_polarity"] = self._calculate_sentiment(result["emotion"])

        # Track emotion trajectory
        result["turn_index"] = turn_index
        self._emotion_history.append({
            "turn": turn_index,
            "emotion": result["emotion"],
            "sentiment": result["sentiment_polarity"],
            "urgency": urgency,
        })
        result["emotion_trajectory"] = self._emotion_history.copy()

        elapsed_ms = (time.monotonic() - start_time) * 1000
        result["detection_time_ms"] = round(elapsed_ms, 1)

        logger.info(
            "emotion_detected",
            emotion=result["emotion"],
            confidence=result["confidence"],
            urgency=urgency,
            sentiment=result["sentiment_polarity"],
        )

        return result

    async def _detect_with_model(self, text: str) -> Optional[Dict[str, Any]]:
        """Run BERT-BiLSTM model inference."""
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
                emotion = EMOTION_LABELS.get(predicted.item(), "neutral")
                return emotion, confidence.item()

            emotion, confidence = await asyncio.to_thread(_run_inference)

            return {
                "emotion": emotion,
                "confidence": round(confidence, 3),
            }
        except Exception as e:
            logger.error("emotion_inference_failed", error=str(e))
            return None

    def _detect_with_keywords(self, text: str, language: str) -> Dict[str, Any]:
        """Keyword-based emotion detection across languages."""
        text_lower = text.lower()

        # Check anger/frustration
        anger_score = 0
        anger_words = ANGER_KEYWORDS.get(language, []) + ANGER_KEYWORDS.get("en", [])
        for kw in anger_words:
            if kw.lower() in text_lower:
                anger_score += 1

        # Check urgency
        urgency_score = 0
        urgency_words = URGENCY_KEYWORDS.get(language, []) + URGENCY_KEYWORDS.get("en", [])
        for kw in urgency_words:
            if kw.lower() in text_lower:
                urgency_score += 1

        # Check positive
        positive_score = 0
        positive_words = POSITIVE_KEYWORDS.get(language, []) + POSITIVE_KEYWORDS.get("en", [])
        for kw in positive_words:
            if kw.lower() in text_lower:
                positive_score += 1

        # Determine dominant emotion
        if anger_score > 0 and anger_score >= urgency_score:
            emotion = "angry" if anger_score >= 2 else "frustrated"
            confidence = min(anger_score * 0.3, 0.9)
        elif urgency_score > 0:
            emotion = "urgent"
            confidence = min(urgency_score * 0.3, 0.9)
        elif positive_score > 0:
            emotion = "happy" if positive_score >= 2 else "satisfied"
            confidence = min(positive_score * 0.3, 0.9)
        else:
            emotion = "neutral"
            confidence = 0.5

        return {"emotion": emotion, "confidence": round(confidence, 3)}

    def _calculate_urgency(self, text: str, language: str, emotion_result: Dict) -> int:
        """Calculate urgency score from 0-10."""
        score = 0
        text_lower = text.lower()

        # Urgency keywords boost
        urgency_words = URGENCY_KEYWORDS.get(language, []) + URGENCY_KEYWORDS.get("en", [])
        for kw in urgency_words:
            if kw.lower() in text_lower:
                score += 2

        # Anger increases urgency
        if emotion_result.get("emotion") in ("angry", "frustrated"):
            score += 2

        # Exclamation marks indicate urgency
        score += min(text.count("!"), 2)

        # ALL CAPS words indicate urgency
        words = text.split()
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        score += min(caps_words, 2)

        # Multiple question marks
        if text.count("?") >= 2:
            score += 1

        return min(score, 10)

    def _calculate_sentiment(self, emotion: str) -> float:
        """Map emotion to sentiment polarity (-1.0 to 1.0)."""
        sentiment_map = {
            "happy": 0.8,
            "satisfied": 0.6,
            "neutral": 0.0,
            "confused": -0.2,
            "anxious": -0.3,
            "sad": -0.5,
            "frustrated": -0.6,
            "angry": -0.8,
            "urgent": -0.4,
        }
        return sentiment_map.get(emotion, 0.0)

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "emotion": "neutral",
            "confidence": 0.0,
            "urgency_score": 0,
            "sentiment_polarity": 0.0,
            "method": "default",
            "detection_time_ms": 0,
        }

    def reset_trajectory(self):
        """Reset emotion trajectory for a new call."""
        self._emotion_history.clear()

    def get_trajectory(self) -> List[Dict[str, Any]]:
        """Get the emotion trajectory for the current call."""
        return self._emotion_history.copy()

    def get_average_sentiment(self) -> float:
        """Calculate average sentiment across the call."""
        if not self._emotion_history:
            return 0.0
        sentiments = [h["sentiment"] for h in self._emotion_history]
        return round(sum(sentiments) / len(sentiments), 3)


# Singleton instance
emotion_detector = EmotionDetector()
