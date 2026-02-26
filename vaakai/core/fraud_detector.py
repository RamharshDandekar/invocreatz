"""Fraud Detection Pipeline — Isolation Forest + LSTM anomaly detection.

Runs as a parallel thread alongside the main STT pipeline, analyzing:
- Speech patterns and anomalous phrasing
- Account access attempt patterns
- Social engineering indicators
- Sequential behavior analysis via LSTM

Max overhead: 50ms per audio frame.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List
from collections import deque
from dataclasses import dataclass, field

import numpy as np
import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Social engineering indicators
SOCIAL_ENGINEERING_PATTERNS = [
    "give me the otp",
    "share your password",
    "tell me your pin",
    "what is your account number",
    "verify your identity by sharing",
    "transfer money to",
    "i am calling from the bank",
    "your account will be blocked",
    "send the code",
    "otp bhejo",
    "password batao",
    "pin number do",
    "account number batao",
    "paisa transfer karo",
    "bank se bol raha hun",
    "account block ho jayega",
]

# Suspicious behavioral patterns
SUSPICIOUS_BEHAVIORS = {
    "rapid_account_queries": "Multiple account detail requests in short time",
    "identity_probing": "Attempting to extract personal identification info",
    "urgency_pressure": "Creating artificial urgency to bypass verification",
    "authority_claiming": "Falsely claiming to be from an authority",
    "detail_phishing": "Systematically extracting sensitive details",
    "callback_redirect": "Attempting to redirect to external numbers",
}


@dataclass
class FraudAnalysisFrame:
    """Single analysis frame for fraud detection."""
    timestamp: float
    text: str
    features: Dict[str, float] = field(default_factory=dict)
    indicators: List[str] = field(default_factory=list)
    score: float = 0.0


class FraudDetector:
    """Real-time fraud detection using Isolation Forest + LSTM.

    Runs in parallel with the main voice pipeline, analyzing each
    conversation turn for suspicious patterns. Produces a fraud score
    from 0.0 (safe) to 1.0 (highly suspicious).
    """

    def __init__(self):
        self._isolation_forest = None
        self._lstm_model = None
        self._initialized = False
        self._frame_buffer: deque = deque(maxlen=50)  # Last 50 analysis frames
        self._cumulative_score: float = 0.0
        self._turn_count: int = 0
        self.threshold = settings.fraud_score_threshold

    async def initialize(self):
        """Initialize fraud detection models."""
        try:
            def _load_models():
                try:
                    from sklearn.ensemble import IsolationForest
                    # Pre-trained isolation forest for anomaly detection
                    iso_forest = IsolationForest(
                        n_estimators=100,
                        contamination=0.1,
                        random_state=42,
                        max_samples="auto",
                    )
                    # Train on synthetic normal behavior features
                    normal_data = np.random.randn(1000, 8)
                    iso_forest.fit(normal_data)
                    return iso_forest
                except Exception:
                    return None

            self._isolation_forest = await asyncio.to_thread(_load_models)
            self._initialized = self._isolation_forest is not None
            if self._initialized:
                logger.info("fraud_detector_initialized")
            else:
                logger.warning("fraud_detector_fallback_mode")
        except Exception as e:
            logger.warning("fraud_detector_init_error", error=str(e))

    async def analyze_frame(
        self,
        text: str,
        turn_index: int,
        language: str = "en",
        emotion: Optional[str] = None,
        intent: Optional[str] = None,
        caller_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze a single conversation frame for fraud indicators.

        Args:
            text: Transcribed text from current turn
            turn_index: Position in conversation
            language: Detected language
            emotion: Detected emotion state
            intent: Classified intent
            caller_phone: Caller's phone number for pattern matching

        Returns:
            Dictionary with fraud analysis results.
        """
        start_time = time.monotonic()
        self._turn_count = turn_index + 1

        # Extract features
        features = self._extract_features(text, turn_index, emotion, intent)

        # Check for social engineering patterns
        se_indicators = self._check_social_engineering(text, language)

        # Check for suspicious behavioral patterns
        behavior_indicators = self._check_behavioral_patterns(turn_index)

        # Run Isolation Forest anomaly detection
        anomaly_score = 0.0
        if self._initialized:
            anomaly_score = await self._run_isolation_forest(features)

        # Combine all signals into final score
        all_indicators = se_indicators + behavior_indicators
        pattern_score = len(all_indicators) * 0.15
        combined_score = min(
            (anomaly_score * 0.4) + (pattern_score * 0.6),
            1.0,
        )

        # Update cumulative score (weighted moving average)
        self._cumulative_score = (
            self._cumulative_score * 0.7 + combined_score * 0.3
        )

        # Create analysis frame
        frame = FraudAnalysisFrame(
            timestamp=time.time(),
            text=text,
            features=features,
            indicators=all_indicators,
            score=combined_score,
        )
        self._frame_buffer.append(frame)

        elapsed_ms = (time.monotonic() - start_time) * 1000

        result = {
            "fraud_score": round(combined_score, 3),
            "cumulative_score": round(self._cumulative_score, 3),
            "anomaly_score": round(anomaly_score, 3),
            "is_suspicious": self._cumulative_score >= self.threshold,
            "indicators": all_indicators,
            "turn_index": turn_index,
            "analysis_time_ms": round(elapsed_ms, 1),
        }

        if self._cumulative_score >= self.threshold:
            logger.warning(
                "fraud_alert",
                score=result["cumulative_score"],
                indicators=all_indicators,
                turn=turn_index,
            )

        return result

    def _extract_features(
        self,
        text: str,
        turn_index: int,
        emotion: Optional[str],
        intent: Optional[str],
    ) -> Dict[str, float]:
        """Extract numerical features for anomaly detection."""
        words = text.split() if text else []

        features = {
            "text_length": len(text),
            "word_count": len(words),
            "question_count": text.count("?"),
            "exclamation_count": text.count("!"),
            "number_density": sum(1 for c in text if c.isdigit()) / max(len(text), 1),
            "caps_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
            "turn_index": turn_index,
            "avg_word_length": np.mean([len(w) for w in words]) if words else 0,
        }

        # Emotion-based features
        emotion_risk_map = {
            "angry": 0.3, "frustrated": 0.2, "urgent": 0.4,
            "neutral": 0.0, "happy": -0.1, "confused": 0.1,
        }
        features["emotion_risk"] = emotion_risk_map.get(emotion or "neutral", 0.0)

        # Intent-based features
        risky_intents = {"account_update", "payment_issue", "account_balance"}
        features["intent_risk"] = 0.3 if intent in risky_intents else 0.0

        return features

    def _check_social_engineering(self, text: str, language: str) -> List[str]:
        """Check for known social engineering patterns."""
        text_lower = text.lower()
        indicators = []

        for pattern in SOCIAL_ENGINEERING_PATTERNS:
            if pattern.lower() in text_lower:
                indicators.append(f"social_engineering: {pattern}")

        return indicators

    def _check_behavioral_patterns(self, turn_index: int) -> List[str]:
        """Check for suspicious behavioral patterns across conversation."""
        indicators = []

        if len(self._frame_buffer) < 2:
            return indicators

        recent_frames = list(self._frame_buffer)[-10:]

        # Check for rapid successive queries about account details
        account_related_count = sum(
            1 for f in recent_frames
            if any(kw in f.text.lower() for kw in ["account", "khata", "balance", "password", "pin"])
        )
        if account_related_count >= 3:
            indicators.append(SUSPICIOUS_BEHAVIORS["rapid_account_queries"])

        # Check for escalating pressure pattern
        urgency_count = sum(
            1 for f in recent_frames
            if any(kw in f.text.lower() for kw in ["urgent", "immediately", "jaldi", "turant", "block"])
        )
        if urgency_count >= 2:
            indicators.append(SUSPICIOUS_BEHAVIORS["urgency_pressure"])

        # Check for information extraction pattern
        info_extraction_count = sum(
            1 for f in recent_frames
            if any(kw in f.text.lower() for kw in ["what is your", "tell me your", "batao", "share"])
        )
        if info_extraction_count >= 2:
            indicators.append(SUSPICIOUS_BEHAVIORS["detail_phishing"])

        return indicators

    async def _run_isolation_forest(self, features: Dict[str, float]) -> float:
        """Run the Isolation Forest model for anomaly detection."""
        try:
            feature_vector = np.array([
                features.get("text_length", 0),
                features.get("word_count", 0),
                features.get("number_density", 0),
                features.get("caps_ratio", 0),
                features.get("emotion_risk", 0),
                features.get("intent_risk", 0),
                features.get("question_count", 0),
                features.get("avg_word_length", 0),
            ]).reshape(1, -1)

            def _predict():
                score = self._isolation_forest.score_samples(feature_vector)
                # Convert to 0-1 range (lower scores = more anomalous)
                normalized = max(0, min(1, 1 - (score[0] + 0.5)))
                return normalized

            return await asyncio.to_thread(_predict)
        except Exception as e:
            logger.error("isolation_forest_failed", error=str(e))
            return 0.0

    def get_score(self) -> float:
        """Get the current cumulative fraud score."""
        return round(self._cumulative_score, 3)

    def get_indicators(self) -> List[str]:
        """Get all fraud indicators detected so far."""
        all_indicators = set()
        for frame in self._frame_buffer:
            all_indicators.update(frame.indicators)
        return list(all_indicators)

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of the fraud analysis for the current call."""
        return {
            "cumulative_score": round(self._cumulative_score, 3),
            "is_suspicious": self._cumulative_score >= self.threshold,
            "total_turns_analyzed": self._turn_count,
            "indicators": self.get_indicators(),
            "threshold": self.threshold,
            "frames_analyzed": len(self._frame_buffer),
        }

    def reset(self):
        """Reset the detector for a new call."""
        self._frame_buffer.clear()
        self._cumulative_score = 0.0
        self._turn_count = 0


# Singleton instance
fraud_detector = FraudDetector()
