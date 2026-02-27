"""Tests for Fraud Detection module."""

import pytest
from core.fraud_detector import fraud_detector


class TestFraudDetector:
    """Test suite for FraudDetector."""

    def setup_method(self):
        """Reset fraud detector before each test."""
        fraud_detector.reset()

    @pytest.mark.asyncio
    async def test_normal_conversation(self):
        """Normal conversation should have low fraud score."""
        result = await fraud_detector.analyze_frame(
            text="I want to check my order status",
            turn_index=0,
            language="en",
        )
        assert result["cumulative_score"] < 0.5

    @pytest.mark.asyncio
    async def test_social_engineering_detection(self):
        """Social engineering patterns should raise fraud score."""
        result = await fraud_detector.analyze_frame(
            text="I'm calling from the bank, I need your OTP immediately",
            turn_index=0,
            language="en",
        )
        assert result["frame_score"] > 0

    @pytest.mark.asyncio
    async def test_account_takeover_pattern(self):
        """Account takeover patterns should be flagged."""
        result = await fraud_detector.analyze_frame(
            text="Please transfer all funds to this new account number right now",
            turn_index=0,
            language="en",
        )
        assert result["frame_score"] > 0

    @pytest.mark.asyncio
    async def test_cumulative_scoring(self):
        """Fraud score should accumulate over multiple suspicious frames."""
        # First suspicious message
        await fraud_detector.analyze_frame(
            text="I need your OTP code urgently",
            turn_index=0,
            language="en",
        )

        # Second suspicious message
        result = await fraud_detector.analyze_frame(
            text="Give me the password or your account will be blocked",
            turn_index=1,
            language="en",
        )

        assert result["cumulative_score"] > 0

    @pytest.mark.asyncio
    async def test_hindi_fraud_pattern(self):
        """Test fraud detection with Hindi patterns."""
        result = await fraud_detector.analyze_frame(
            text="jaldi apna OTP batao nahi to account band ho jayega",
            turn_index=0,
            language="hi",
        )
        assert result["frame_score"] > 0

    @pytest.mark.asyncio
    async def test_result_structure(self):
        result = await fraud_detector.analyze_frame(
            text="hello", turn_index=0, language="en"
        )
        assert "frame_score" in result
        assert "cumulative_score" in result
        assert "is_suspicious" in result
        assert "indicators" in result

    def test_reset(self):
        """Test that reset clears the state."""
        fraud_detector.reset()
        assert fraud_detector.get_score() == 0.0
        assert fraud_detector.get_indicators() == []

    @pytest.mark.asyncio
    async def test_threshold(self):
        """Fraud should only be flagged above threshold."""
        result = await fraud_detector.analyze_frame(
            text="Good morning, how are you?",
            turn_index=0,
            language="en",
        )
        assert result["is_suspicious"] is False
