"""AI4Bharat Indic TTS — Voice synthesis for 22 Indian languages.

Uses AI4Bharat's TTS models for generating natural-sounding speech
in Indian regional languages including Hindi, Tamil, Telugu, Bengali, etc.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional, Dict, Any, AsyncIterator

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Language to voice model mapping
INDIC_VOICE_MAP = {
    "hi": {"model": "hi-IN", "gender": "female", "name": "Hindi Female"},
    "bn": {"model": "bn-IN", "gender": "female", "name": "Bengali Female"},
    "ta": {"model": "ta-IN", "gender": "female", "name": "Tamil Female"},
    "te": {"model": "te-IN", "gender": "female", "name": "Telugu Female"},
    "mr": {"model": "mr-IN", "gender": "female", "name": "Marathi Female"},
    "gu": {"model": "gu-IN", "gender": "female", "name": "Gujarati Female"},
    "kn": {"model": "kn-IN", "gender": "female", "name": "Kannada Female"},
    "ml": {"model": "ml-IN", "gender": "female", "name": "Malayalam Female"},
    "pa": {"model": "pa-IN", "gender": "female", "name": "Punjabi Female"},
    "or": {"model": "or-IN", "gender": "female", "name": "Odia Female"},
    "as": {"model": "as-IN", "gender": "female", "name": "Assamese Female"},
    "ur": {"model": "ur-IN", "gender": "female", "name": "Urdu Female"},
    "sa": {"model": "sa-IN", "gender": "female", "name": "Sanskrit Female"},
    "ne": {"model": "ne-IN", "gender": "female", "name": "Nepali Female"},
}


class IndicTTS:
    """AI4Bharat TTS client for Indian language voice synthesis.

    Provides text-to-speech for 22+ Indian languages using
    AI4Bharat's pre-trained models via their inference API.
    """

    BASE_URL = "https://api-inference.huggingface.co/models"

    # HF model IDs for AI4Bharat TTS per language
    HF_TTS_MODELS = {
        "hi": "ai4bharat/indic-tts-coqui-hi",
        "bn": "ai4bharat/indic-tts-coqui-bn",
        "ta": "ai4bharat/indic-tts-coqui-ta",
        "te": "ai4bharat/indic-tts-coqui-te",
        "mr": "ai4bharat/indic-tts-coqui-mr",
        "gu": "ai4bharat/indic-tts-coqui-gu",
        "kn": "ai4bharat/indic-tts-coqui-kn",
        "ml": "ai4bharat/indic-tts-coqui-ml",
        "pa": "ai4bharat/indic-tts-coqui-pa",
        "or": "ai4bharat/indic-tts-coqui-or",
    }
    DEFAULT_TTS_MODEL = "ai4bharat/indic-tts-coqui-hi"

    def __init__(self):
        self.hf_token = settings.hf_token or settings.ai4bharat_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize the HTTP client."""
        headers = {"Content-Type": "application/json"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0),
            headers=headers,
        )
        logger.info("indic_tts_initialized")

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.aclose()

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        gender: str = "female",
        sample_rate: int = 22050,
    ) -> Dict[str, Any]:
        """Synthesize text to speech in an Indian language.

        Args:
            text: Text to convert to speech
            language: ISO 639 language code
            gender: Voice gender (male/female)
            sample_rate: Output audio sample rate

        Returns:
            Dictionary with 'audio' (base64), 'format', 'latency_ms' keys.
        """
        if not self._client:
            await self.initialize()

        start_time = time.monotonic()

        voice_config = INDIC_VOICE_MAP.get(language, INDIC_VOICE_MAP["hi"])

        try:
            model_id = self.HF_TTS_MODELS.get(language, self.DEFAULT_TTS_MODEL)

            payload = {
                "inputs": text,
            }

            response = await self._client.post(
                f"{self.BASE_URL}/{model_id}",
                json=payload,
            )

            # Handle model loading (HF cold start)
            if response.status_code == 503:
                import asyncio
                body = response.json()
                wait_time = body.get("estimated_time", 20)
                logger.info("indic_tts_model_loading", model=model_id, estimated_wait=wait_time)
                await asyncio.sleep(min(wait_time, 30))
                response = await self._client.post(
                    f"{self.BASE_URL}/{model_id}",
                    json=payload,
                )

            response.raise_for_status()

            # HF TTS returns raw audio bytes directly
            audio_bytes = response.content

            latency_ms = (time.monotonic() - start_time) * 1000

            logger.info(
                "indic_tts_synthesized",
                language=language,
                model=model_id,
                text_length=len(text),
                audio_size=len(audio_bytes),
                latency_ms=round(latency_ms, 1),
            )

            if audio_bytes:
                return {
                    "audio": audio_bytes,
                    "format": "wav",
                    "sample_rate": sample_rate,
                    "language": language,
                    "latency_ms": round(latency_ms, 1),
                    "provider": "ai4bharat",
                }

            return {
                "audio": b"",
                "error": "no_audio_in_response",
                "latency_ms": round(latency_ms, 1),
            }

        except Exception as e:
            logger.error("indic_tts_failed", error=str(e), language=language)
            return {
                "audio": b"",
                "error": str(e),
                "latency_ms": (time.monotonic() - start_time) * 1000,
            }

    async def synthesize_stream(
        self,
        text_chunks: AsyncIterator[str],
        language: str = "hi",
        gender: str = "female",
    ) -> AsyncIterator[bytes]:
        """Streaming synthesis — text chunks to audio chunks.

        Buffers text until natural break points, then synthesizes
        each segment for streaming delivery.
        """
        text_buffer = ""
        FLUSH_CHARS = 100  # Indian scripts tend to be more compact

        async for chunk in text_chunks:
            text_buffer += chunk

            # Flush on sentence boundaries or buffer full
            should_flush = (
                len(text_buffer) >= FLUSH_CHARS
                or text_buffer.endswith(("।", ".", "!", "?", "|"))
            )

            if should_flush and text_buffer.strip():
                result = await self.synthesize(
                    text=text_buffer.strip(),
                    language=language,
                    gender=gender,
                )
                if result.get("audio"):
                    yield result["audio"]
                text_buffer = ""

        # Flush remaining
        if text_buffer.strip():
            result = await self.synthesize(
                text=text_buffer.strip(),
                language=language,
                gender=gender,
            )
            if result.get("audio"):
                yield result["audio"]

    @property
    def supported_languages(self) -> list:
        return list(INDIC_VOICE_MAP.keys())


# Singleton instance
indic_tts = IndicTTS()
