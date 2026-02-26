"""ElevenLabs TTS Client — Sub-75ms English voice synthesis.

Uses ElevenLabs Flash v2 for ultra-low-latency English text-to-speech.
Supports streaming synthesis (token-by-token from LLM → audio chunks).
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, AsyncIterator, List

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Voice profiles for different emotional tones
VOICE_PROFILES = {
    "default": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - calm, professional
        "stability": 0.5,
        "similarity_boost": 0.75,
    },
    "empathetic": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "stability": 0.6,
        "similarity_boost": 0.8,
        "style": 0.3,
    },
    "energetic": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "stability": 0.4,
        "similarity_boost": 0.7,
        "style": 0.5,
    },
}

# Emotion to voice profile mapping
EMOTION_VOICE_MAP = {
    "neutral": "default",
    "happy": "energetic",
    "angry": "empathetic",
    "frustrated": "empathetic",
    "sad": "empathetic",
    "anxious": "empathetic",
    "urgent": "default",
    "confused": "default",
    "satisfied": "default",
}


class ElevenLabsTTS:
    """ElevenLabs Flash TTS for English voice synthesis.

    Features:
    - Sub-75ms first-byte latency
    - Streaming synthesis (text chunk → audio chunk)
    - Emotion-adaptive voice profiles
    - MP3/PCM output formats
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize the HTTP client."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0),
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            },
        )
        logger.info("elevenlabs_tts_initialized")

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.aclose()

    async def synthesize(
        self,
        text: str,
        emotion: str = "neutral",
        output_format: str = "mp3_44100_128",
    ) -> Dict[str, Any]:
        """Synthesize text to audio.

        Args:
            text: Text to convert to speech
            emotion: Current emotion state for voice adaptation
            output_format: Audio format (mp3_44100_128, pcm_16000, etc.)

        Returns:
            Dictionary with 'audio' (bytes), 'duration_ms', 'latency_ms' keys.
        """
        if not self._client:
            await self.initialize()

        start_time = time.monotonic()

        # Select voice profile based on emotion
        profile_name = EMOTION_VOICE_MAP.get(emotion, "default")
        profile = VOICE_PROFILES[profile_name]

        try:
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2",  # Flash model for low latency
                "voice_settings": {
                    "stability": profile.get("stability", 0.5),
                    "similarity_boost": profile.get("similarity_boost", 0.75),
                    "style": profile.get("style", 0.0),
                    "use_speaker_boost": True,
                },
            }

            url = f"{self.BASE_URL}/text-to-speech/{profile['voice_id']}"
            response = await self._client.post(
                url,
                json=payload,
                params={"output_format": output_format},
            )
            response.raise_for_status()

            audio_bytes = response.content
            latency_ms = (time.monotonic() - start_time) * 1000

            logger.info(
                "elevenlabs_synthesized",
                text_length=len(text),
                audio_bytes=len(audio_bytes),
                latency_ms=round(latency_ms, 1),
                emotion=emotion,
            )

            return {
                "audio": audio_bytes,
                "format": output_format,
                "latency_ms": round(latency_ms, 1),
                "provider": "elevenlabs",
            }

        except Exception as e:
            logger.error("elevenlabs_synthesis_failed", error=str(e))
            return {
                "audio": b"",
                "error": str(e),
                "latency_ms": (time.monotonic() - start_time) * 1000,
            }

    async def synthesize_stream(
        self,
        text_chunks: AsyncIterator[str],
        emotion: str = "neutral",
        output_format: str = "mp3_44100_128",
    ) -> AsyncIterator[bytes]:
        """Streaming synthesis — convert text tokens to audio chunks.

        Takes an async iterator of text tokens (from LLM streaming) and
        yields audio chunks. This enables first-audio-byte delivery
        before the LLM has finished generating the full response.
        """
        if not self._client:
            await self.initialize()

        profile_name = EMOTION_VOICE_MAP.get(emotion, "default")
        profile = VOICE_PROFILES[profile_name]

        # Buffer text until we have a natural speech segment
        text_buffer = ""
        FLUSH_CHARS = 80  # Flush buffer every ~80 characters

        async for chunk in text_chunks:
            text_buffer += chunk

            # Check for natural break points or buffer full
            should_flush = (
                len(text_buffer) >= FLUSH_CHARS
                or text_buffer.endswith((".", "!", "?", ",", ";", "।"))
            )

            if should_flush and text_buffer.strip():
                try:
                    url = f"{self.BASE_URL}/text-to-speech/{profile['voice_id']}/stream"
                    payload = {
                        "text": text_buffer.strip(),
                        "model_id": "eleven_turbo_v2",
                        "voice_settings": {
                            "stability": profile.get("stability", 0.5),
                            "similarity_boost": profile.get("similarity_boost", 0.75),
                        },
                    }

                    response = await self._client.post(
                        url,
                        json=payload,
                        params={"output_format": output_format},
                    )
                    response.raise_for_status()
                    yield response.content

                except Exception as e:
                    logger.error("elevenlabs_stream_chunk_failed", error=str(e))

                text_buffer = ""

        # Flush remaining buffer
        if text_buffer.strip():
            try:
                url = f"{self.BASE_URL}/text-to-speech/{profile['voice_id']}/stream"
                payload = {
                    "text": text_buffer.strip(),
                    "model_id": "eleven_turbo_v2",
                    "voice_settings": {
                        "stability": profile.get("stability", 0.5),
                        "similarity_boost": profile.get("similarity_boost", 0.75),
                    },
                }
                response = await self._client.post(
                    url,
                    json=payload,
                    params={"output_format": output_format},
                )
                response.raise_for_status()
                yield response.content
            except Exception as e:
                logger.error("elevenlabs_final_flush_failed", error=str(e))


# Singleton instance
elevenlabs_tts = ElevenLabsTTS()
