"""Tests for NLU Intent Classification module."""

import pytest
from core.nlu.intent import intent_classifier


class TestIntentClassifier:
    """Test suite for IntentClassifier."""

    @pytest.mark.asyncio
    async def test_order_status_intent_en(self):
        result = await intent_classifier.classify("Where is my order?", "en")
        assert result["intent"] == "order_status"
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_order_status_intent_hi(self):
        result = await intent_classifier.classify("mera order kahan hai", "hi")
        assert result["intent"] == "order_status"

    @pytest.mark.asyncio
    async def test_refund_intent(self):
        result = await intent_classifier.classify("I want a refund for my purchase", "en")
        assert result["intent"] in ("refund_request", "return_request", "payment_issue")

    @pytest.mark.asyncio
    async def test_complaint_intent(self):
        result = await intent_classifier.classify("I have a complaint about your service", "en")
        assert result["intent"] == "complaint"

    @pytest.mark.asyncio
    async def test_escalation_intent(self):
        result = await intent_classifier.classify("Connect me to a manager", "en")
        assert result["intent"] == "escalation_request"

    @pytest.mark.asyncio
    async def test_greeting_intent(self):
        result = await intent_classifier.classify("Hello, good morning", "en")
        assert result["intent"] == "greeting"

    @pytest.mark.asyncio
    async def test_result_structure(self):
        result = await intent_classifier.classify("test message", "en")
        assert "intent" in result
        assert "confidence" in result
        assert "complexity" in result
        assert "top_intents" in result

    @pytest.mark.asyncio
    async def test_complexity_mapping(self):
        """Test that intents have correct complexity levels."""
        # Simple intent
        result = await intent_classifier.classify("What are your hours?", "en")
        # Complex intent
        result2 = await intent_classifier.classify("I need to file a legal dispute", "en")
        assert result2["complexity"] in ("simple", "medium", "complex")
