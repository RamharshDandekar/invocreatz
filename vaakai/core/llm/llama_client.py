"""Llama LLM Client — Local/Ollama-based Llama 3.1 for cost-efficient inference."""

from __future__ import annotations

import time
from typing import Optional, Dict, Any, List, AsyncIterator

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class LlamaClient:
    """Client for Llama 3.1 models via Ollama API.

    Supports both 8B (fast/cheap) and 70B (complex reasoning) variants.
    Uses the Ollama-compatible API format.
    """

    def __init__(self):
        self.base_url = settings.llama_api_url
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize the HTTP client for Ollama API."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0),
        )
        logger.info("llama_client_initialized", base_url=self.base_url)

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.aclose()

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> Dict[str, Any]:
        """Generate a response using Llama via Ollama.

        Args:
            messages: Chat messages in OpenAI-compatible format
            model: Model name (llama3.1:8b or llama3.1:70b)
            temperature: Creativity parameter
            max_tokens: Maximum response length

        Returns:
            Dictionary with response data.
        """
        if not self._client:
            await self.initialize()

        start_time = time.monotonic()

        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.monotonic() - start_time) * 1000

            result = {
                "text": data.get("message", {}).get("content", ""),
                "model": model,
                "confidence": 0.80,
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": (
                        data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    ),
                },
                "latency_ms": round(latency_ms, 1),
            }

            logger.info(
                "llama_response_generated",
                model=model,
                latency_ms=result["latency_ms"],
            )

            return result

        except httpx.ConnectError:
            logger.warning("llama_connection_failed_ollama_not_running")
            return {
                "text": "",
                "model": model,
                "error": "Ollama not running",
                "confidence": 0.0,
                "tool_calls": [],
                "latency_ms": (time.monotonic() - start_time) * 1000,
            }
        except Exception as e:
            logger.error("llama_generation_failed", error=str(e), model=model)
            return {
                "text": "",
                "model": model,
                "error": str(e),
                "confidence": 0.0,
                "tool_calls": [],
                "latency_ms": (time.monotonic() - start_time) * 1000,
            }

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AsyncIterator[str]:
        """Stream response tokens from Llama/Ollama."""
        if not self._client:
            await self.initialize()

        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            async with self._client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                import json
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error("llama_stream_failed", error=str(e))
            yield "I'm sorry, I'm having trouble right now."

    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama is running and accessible."""
        try:
            if not self._client:
                await self.initialize()
            response = await self._client.get("/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "status": "healthy",
                    "available_models": [m["name"] for m in models],
                }
            return {"status": "degraded", "error": f"Status {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Singleton instance
llama_client = LlamaClient()
