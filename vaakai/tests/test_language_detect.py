"""Tests for Language Detection module."""

import pytest
from core.language_detect import language_detector


class TestLanguageDetector:
    """Test suite for LanguageDetector."""

    @pytest.mark.asyncio
    async def test_detect_hindi(self):
        """Test Hindi detection from Devanagari script."""
        result = await language_detector.detect("मुझे मेरा ऑर्डर ट्रैक करना है")
        assert result["language"] == "hi"
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_detect_english(self):
        """Test English detection."""
        result = await language_detector.detect("I want to track my order")
        assert result["language"] == "en"
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_detect_bengali(self):
        """Test Bengali detection from Bengali script."""
        result = await language_detector.detect("আমার অর্ডার কোথায়")
        assert result["language"] == "bn"

    @pytest.mark.asyncio
    async def test_detect_tamil(self):
        """Test Tamil detection from Tamil script."""
        result = await language_detector.detect("என் ஆர்டர் எங்கே")
        assert result["language"] == "ta"

    @pytest.mark.asyncio
    async def test_detect_telugu(self):
        """Test Telugu detection from Telugu script."""
        result = await language_detector.detect("నా ఆర్డర్ ఎక్కడ ఉంది")
        assert result["language"] == "te"

    @pytest.mark.asyncio
    async def test_detect_empty_string(self):
        """Test handling of empty input."""
        result = await language_detector.detect("")
        assert "language" in result
        assert result["confidence"] >= 0

    @pytest.mark.asyncio
    async def test_detect_code_switching(self):
        """Test code-switching detection (Hindi + English)."""
        result = await language_detector.detect(
            "Mera order kab deliver hoga, please check"
        )
        assert "language" in result
        # Code-switched text may detect either Hindi or English

    @pytest.mark.asyncio
    async def test_result_structure(self):
        """Test that result contains expected keys."""
        result = await language_detector.detect("Hello world")
        assert "language" in result
        assert "confidence" in result
        assert "method" in result
        assert "is_code_switched" in result
