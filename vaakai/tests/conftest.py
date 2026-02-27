"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("memory.redis_client.redis_client") as mock:
        mock.connect = AsyncMock()
        mock.disconnect = AsyncMock()
        mock.create_session = AsyncMock()
        mock.get_session = AsyncMock(return_value={})
        mock.update_session = AsyncMock()
        mock.delete_session = AsyncMock()
        mock.get_customer_context = AsyncMock(return_value=None)
        mock.append_message = AsyncMock()
        mock.get_conversation_history = AsyncMock(return_value=[])
        mock.get_erp_cache = AsyncMock(return_value=None)
        mock.set_erp_cache = AsyncMock()
        mock._redis = AsyncMock()
        yield mock


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("core.llm.openai_client.openai_client") as mock:
        mock.generate = AsyncMock(return_value={
            "text": "Test response",
            "model": "gpt-4o-mini",
            "confidence": 0.95,
        })
        mock.build_messages = MagicMock(return_value=[
            {"role": "system", "content": "You are VaakAI"},
            {"role": "user", "content": "test"},
        ])
        yield mock
