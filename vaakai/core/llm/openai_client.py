"""OpenAI LLM Client — GPT-4o and GPT-4o-mini for response generation."""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, List, AsyncIterator

import structlog
from openai import AsyncOpenAI

from config import settings

logger = structlog.get_logger(__name__)

# System prompt template for VaakAI
SYSTEM_PROMPT_TEMPLATE = """You are VaakAI, an intelligent, empathetic customer service assistant.

INSTRUCTIONS:
- Respond in {language_name} (language code: {language}).
- Be concise but helpful. Keep responses under 3 sentences for simple queries.
- Show empathy when the customer is frustrated or angry.
- If you need to perform an action (check order, create ticket, etc.), describe what you're doing.
- Never reveal you are an AI unless directly asked.
- Use natural, conversational language appropriate for the detected emotion state.
- If you cannot help, offer to connect the customer with a human agent.

CUSTOMER CONTEXT:
{customer_context}

CURRENT STATE:
- Emotion: {emotion}
- Urgency: {urgency_score}/10
- Intent: {intent}
"""


class OpenAIClient:
    """Async OpenAI client for GPT-4o and GPT-4o-mini.

    Supports both streaming and non-streaming response generation.
    """

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    async def initialize(self):
        """Initialize the OpenAI async client."""
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("openai_client_initialized")

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.close()

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Generate a response from OpenAI.

        Args:
            messages: Chat messages in OpenAI format
            model: Model name (gpt-4o-mini for simple, gpt-4o for complex)
            temperature: Creativity parameter
            max_tokens: Maximum response length
            tools: Optional tool definitions for function calling

        Returns:
            Dictionary with 'text', 'model', 'confidence', 'tool_calls',
            'usage', 'latency_ms' keys.
        """
        if not self._client:
            await self.initialize()

        start_time = time.monotonic()

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self._client.chat.completions.create(**kwargs)

            choice = response.choices[0]
            latency_ms = (time.monotonic() - start_time) * 1000

            result = {
                "text": choice.message.content or "",
                "model": model,
                "finish_reason": choice.finish_reason,
                "confidence": 0.85,  # Heuristic confidence
                "tool_calls": [],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "latency_ms": round(latency_ms, 1),
            }

            # Parse tool calls if present
            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                    for tc in choice.message.tool_calls
                ]

            logger.info(
                "openai_response_generated",
                model=model,
                tokens=response.usage.total_tokens,
                latency_ms=result["latency_ms"],
            )

            return result

        except Exception as e:
            logger.error("openai_generation_failed", error=str(e), model=model)
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
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> AsyncIterator[str]:
        """Stream response tokens for low-latency TTS integration.

        Yields individual tokens as they arrive from the API.
        """
        if not self._client:
            await self.initialize()

        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("openai_stream_failed", error=str(e))
            yield "I'm sorry, I'm having trouble processing your request. Can you please try again?"

    def build_messages(
        self,
        user_text: str,
        conversation_history: List[Dict[str, str]],
        language: str = "en",
        emotion: str = "neutral",
        urgency_score: int = 0,
        intent: str = "other",
        customer_context: str = "No prior context available.",
    ) -> List[Dict[str, str]]:
        """Build the messages array for OpenAI API.

        Includes system prompt with context injection and conversation history.
        """
        language_names = {
            "en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil",
            "te": "Telugu", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada",
            "ml": "Malayalam", "pa": "Punjabi", "or": "Odia", "ur": "Urdu",
        }

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            language=language,
            language_name=language_names.get(language, "the customer's language"),
            emotion=emotion,
            urgency_score=urgency_score,
            intent=intent,
            customer_context=customer_context,
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 10 turns)
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        # Add current user message
        messages.append({"role": "user", "content": user_text})

        return messages


# Singleton instance
openai_client = OpenAIClient()
