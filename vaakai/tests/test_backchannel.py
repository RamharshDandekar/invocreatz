"""Tests for Backchannel Engine."""

import pytest
from core.backchannel import backchannel_engine


class TestBackchannelEngine:
    """Test suite for BackchannelEngine."""

    def setup_method(self):
        backchannel_engine.reset()

    def test_english_response(self):
        result = backchannel_engine.get_response("en", "neutral", "thinking")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hindi_response(self):
        result = backchannel_engine.get_response("hi", "neutral", "acknowledgement")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empathy_for_anger(self):
        result = backchannel_engine.get_response("en", "angry", "empathy")
        assert isinstance(result, str)

    def test_no_repetition(self):
        """Test that responses don't repeat immediately."""
        responses = set()
        for _ in range(5):
            r = backchannel_engine.get_response("en", "neutral", "thinking")
            responses.add(r)
        # Should have at least 2 different responses in 5 tries
        assert len(responses) >= 2

    def test_supported_languages(self):
        """Test that all supported languages return valid responses."""
        for lang in ["en", "hi", "bn", "ta", "te"]:
            result = backchannel_engine.get_response(lang, "neutral", "acknowledgement")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_unsupported_language_fallback(self):
        """Unsupported language should fall back to English."""
        result = backchannel_engine.get_response("xx", "neutral", "thinking")
        assert isinstance(result, str)
        assert len(result) > 0
