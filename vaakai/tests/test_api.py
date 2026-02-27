"""Tests for FastAPI endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_orchestrator():
    """Mock the orchestrator for API tests."""
    with patch("api.call.orchestrator") as mock:
        mock.get_active_sessions.return_value = []
        mock._sessions = {}

        session_mock = MagicMock()
        session_mock.session_id = "test_session_123"
        session_mock.phone_number = "+919876543210"
        session_mock.language = "hi"
        session_mock.customer_id = "cust_1"
        session_mock.channel = MagicMock()
        session_mock.channel.value = "voice"
        session_mock.is_active = True
        session_mock.turn_index = 0
        session_mock.direction = MagicMock()
        session_mock.direction.value = "inbound"

        mock.start_session = AsyncMock(return_value=session_mock)

        mock.process_audio = AsyncMock(return_value={
            "session_id": "test_session_123",
            "user_text": "Hello",
            "bot_response": "Namaste!",
            "language": "hi",
            "intent": {"intent": "greeting", "confidence": 0.9},
            "emotion": {"emotion": "neutral", "urgency_score": 0},
            "fraud": {"cumulative_score": 0.0, "is_suspicious": False},
            "latency_ms": 250,
        })

        mock.process_text = AsyncMock(return_value={
            "session_id": "test_session_123",
            "user_text": "test",
            "bot_response": "Response",
            "language": "en",
        })

        mock.end_session = AsyncMock(return_value={
            "session_id": "test_session_123",
            "status": "completed",
            "duration_seconds": 120,
            "total_turns": 5,
        })

        yield mock


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health check endpoint."""
    with patch("api.main.orchestrator") as mock_orch:
        mock_orch.get_active_sessions.return_value = []
        mock_orch.initialize = AsyncMock()
        mock_orch.shutdown = AsyncMock()

        with patch("api.main.init_db", new_callable=AsyncMock):
            with patch("api.main.pii_redactor") as mock_pii:
                mock_pii.initialize = AsyncMock()

                from api.main import app
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    response = await ac.get("/api/v1/health")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert data["service"] == "vaakai"
