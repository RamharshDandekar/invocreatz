"""Tests for Emotion Detection module."""

import pytest
from core.nlu.emotion import emotion_detector


class TestEmotionDetector:
    """Test suite for EmotionDetector."""

    @pytest.mark.asyncio
    async def test_anger_detection(self):
        result = await emotion_detector.detect(
            "This is absolutely terrible! I'm furious!", "en", 0
        )
        assert result["emotion"] in ("angry", "frustrated")
        assert result["urgency_score"] >= 5

    @pytest.mark.asyncio
    async def test_happy_detection(self):
        result = await emotion_detector.detect(
            "Thank you so much! This is wonderful!", "en", 0
        )
        assert result["emotion"] in ("happy", "satisfied")
        assert result["sentiment_polarity"] > 0

    @pytest.mark.asyncio
    async def test_neutral_detection(self):
        result = await emotion_detector.detect(
            "I need to check my order status", "en", 0
        )
        assert result["emotion"] in ("neutral", "calm")

    @pytest.mark.asyncio
    async def test_hindi_frustration(self):
        result = await emotion_detector.detect(
            "yeh bahut bura hai, mujhe gussa aa raha hai", "hi", 0
        )
        assert result["urgency_score"] >= 3

    @pytest.mark.asyncio
    async def test_result_structure(self):
        result = await emotion_detector.detect("test", "en", 0)
        assert "emotion" in result
        assert "confidence" in result
        assert "urgency_score" in result
        assert "sentiment_polarity" in result

    @pytest.mark.asyncio
    async def test_urgency_bounds(self):
        result = await emotion_detector.detect("test input", "en", 0)
        assert 0 <= result["urgency_score"] <= 10
        assert -1.0 <= result["sentiment_polarity"] <= 1.0

    def test_trajectory_tracking(self):
        """Test that emotion trajectory is properly tracked."""
        emotion_detector.reset_trajectory()
        trajectory = emotion_detector.get_trajectory()
        assert isinstance(trajectory, list)

    def test_average_sentiment(self):
        """Test average sentiment calculation."""
        emotion_detector.reset_trajectory()
        avg = emotion_detector.get_average_sentiment()
        assert isinstance(avg, (int, float))
