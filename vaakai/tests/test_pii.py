"""Tests for PII Redactor module."""

import pytest
from compliance.pii_redactor import pii_redactor


class TestPIIRedactor:
    """Test suite for PII redaction."""

    def test_aadhaar_detection(self):
        """Test Aadhaar number detection."""
        text = "My Aadhaar number is 2345 6789 0123"
        entities = pii_redactor.detect(text)
        types = [e.entity_type for e in entities]
        assert "AADHAAR_NUMBER" in types

    def test_pan_detection(self):
        """Test PAN number detection."""
        text = "My PAN is ABCDE1234F"
        entities = pii_redactor.detect(text)
        types = [e.entity_type for e in entities]
        assert "PAN_NUMBER" in types

    def test_phone_detection(self):
        """Test Indian phone number detection."""
        text = "Call me at +91 9876543210"
        entities = pii_redactor.detect(text)
        types = [e.entity_type for e in entities]
        assert "INDIAN_PHONE" in types

    def test_email_detection(self):
        """Test email detection."""
        text = "Send it to user@example.com"
        entities = pii_redactor.detect(text)
        types = [e.entity_type for e in entities]
        assert "EMAIL_ADDRESS" in types

    def test_redaction(self):
        """Test that PII is properly masked in output."""
        text = "My PAN is ABCDE1234F and email is test@test.com"
        result = pii_redactor.redact(text)
        assert "ABCDE1234F" not in result["redacted_text"]
        assert "test@test.com" not in result["redacted_text"]
        assert result["entity_count"] >= 2

    def test_no_pii(self):
        """Test text without PII."""
        text = "Hello, I want to check my order status"
        result = pii_redactor.redact(text)
        assert result["redacted_text"] == text
        assert result["entity_count"] == 0

    def test_redact_for_logging(self):
        """Test quick redaction method."""
        text = "My number is 9876543210"
        redacted = pii_redactor.redact_for_logging(text)
        assert "9876543210" not in redacted

    def test_gstin_detection(self):
        """Test GSTIN detection."""
        text = "Our GSTIN is 22ABCDE1234F1Z5"
        entities = pii_redactor.detect(text)
        types = [e.entity_type for e in entities]
        assert "GSTIN" in types
