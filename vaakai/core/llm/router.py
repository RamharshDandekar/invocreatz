"""Multi-LLM Router — Intelligent routing between LLM providers.

Routes requests to the optimal LLM based on:
- Intent complexity (simple → fast model, complex → powerful model)
- Current load and latency
- Fallback chain for reliability
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List, AsyncIterator

import structlog

from core.llm.openai_client import openai_client
from core.llm.llama_client import llama_client
from core.nlu.intent import INTENT_COMPLEXITY

logger = structlog.get_logger(__name__)

# Model routing configuration
MODEL_ROUTES = {
    "simple": {
        "primary": {"provider": "openai", "model": "gpt-4o-mini"},
        "fallback": {"provider": "llama", "model": "llama3.1:8b"},
    },
    "medium": {
        "primary": {"provider": "openai", "model": "gpt-4o-mini"},
        "fallback": {"provider": "llama", "model": "llama3.1:8b"},
    },
    "complex": {
        "primary": {"provider": "openai", "model": "gpt-4o"},
        "fallback": {"provider": "llama", "model": "llama3.1:70b"},
    },
}


class LLMRouter:
    """Routes LLM requests to the optimal model based on task complexity.

    Implements:
    - Complexity-based routing
    - Automatic fallback on primary model failure
    - Streaming support for low-latency TTS integration
    - Token usage tracking
    """

    def __init__(self):
        self._total_tokens_used: int = 0
        self._request_count: int = 0

    async def initialize(self):
        """Initialize all LLM clients."""
        await asyncio.gather(
            openai_client.initialize(),
            llama_client.initialize(),
            return_exceptions=True,
        )
        logger.info("llm_router_initialized")

    async def close(self):
        """Clean up all clients."""
        await asyncio.gather(
            openai_client.close(),
            llama_client.close(),
            return_exceptions=True,
        )

    def select_model(self, intent: str, urgency_score: int = 0) -> Dict[str, str]:
        """Select the appropriate model based on intent complexity and urgency.

        Args:
            intent: Classified intent name
            urgency_score: Urgency score (0-10)

        Returns:
            Dictionary with 'provider' and 'model' keys.
        """
        complexity = INTENT_COMPLEXITY.get(intent, "complex")

        # High urgency always gets the best model
        if urgency_score >= 7:
            complexity = "complex"

        route = MODEL_ROUTES.get(complexity, MODEL_ROUTES["complex"])
        selected = route["primary"]

        logger.info(
            "model_selected",
            intent=intent,
            complexity=complexity,
            provider=selected["provider"],
            model=selected["model"],
        )

        return selected

    async def generate(
        self,
        messages: List[Dict[str, str]],
        intent: str = "other",
        urgency_score: int = 0,
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate a response using the optimal LLM.

        Automatically falls back to secondary model on failure.
        """
        selected = self.select_model(intent, urgency_score)
        complexity = INTENT_COMPLEXITY.get(intent, "complex")

        # Try primary model
        result = await self._call_provider(
            provider=selected["provider"],
            model=selected["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )

        # If primary fails, try fallback
        if result.get("error") and not result.get("text"):
            fallback = MODEL_ROUTES.get(complexity, MODEL_ROUTES["complex"])["fallback"]
            logger.warning(
                "llm_fallback_triggered",
                primary=selected["model"],
                fallback=fallback["model"],
            )
            result = await self._call_provider(
                provider=fallback["provider"],
                model=fallback["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Track usage
        self._request_count += 1
        self._total_tokens_used += result.get("usage", {}).get("total_tokens", 0)

        return result

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        intent: str = "other",
        urgency_score: int = 0,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AsyncIterator[str]:
        """Stream response tokens from the selected LLM.

        Critical for low-latency TTS integration — tokens are sent to
        TTS as they arrive, not waiting for complete response.
        """
        selected = self.select_model(intent, urgency_score)

        if selected["provider"] == "openai":
            async for token in openai_client.generate_stream(
                messages=messages,
                model=selected["model"],
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield token
        elif selected["provider"] == "llama":
            async for token in llama_client.generate_stream(
                messages=messages,
                model=selected["model"],
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield token

    async def _call_provider(
        self,
        provider: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Call a specific LLM provider."""
        if provider == "openai":
            return await openai_client.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )
        elif provider == "llama":
            return await llama_client.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        else:
            return {"text": "", "error": f"Unknown provider: {provider}", "confidence": 0.0}

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "total_requests": self._request_count,
            "total_tokens_used": self._total_tokens_used,
            "avg_tokens_per_request": (
                self._total_tokens_used / max(self._request_count, 1)
            ),
        }


# Singleton instance
llm_router = LLMRouter()
