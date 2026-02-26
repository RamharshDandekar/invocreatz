"""BHASHINI STT Client — Speech-to-Text for 22 Indian languages.

BHASHINI (bhashini.gov.in) is the Government of India's AI platform
that provides speech recognition for all 22 scheduled Indian languages.
"""

from __future__ import annotations

import asyncio
import base64
from typing import Optional, AsyncIterator, Dict, Any

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)

# Language code mapping for BHASHINI
BHASHINI_LANGUAGE_MAP = {
    "hi": "hi",   # Hindi
    "bn": "bn",   # Bengali
    "ta": "ta",   # Tamil
    "te": "te",   # Telugu
    "mr": "mr",   # Marathi
    "gu": "gu",   # Gujarati
    "kn": "kn",   # Kannada
    "ml": "ml",   # Malayalam
    "pa": "pa",   # Punjabi
    "or": "or",   # Odia
    "as": "as",   # Assamese
    "ur": "ur",   # Urdu
    "sa": "sa",   # Sanskrit
    "ne": "ne",   # Nepali
    "sd": "sd",   # Sindhi
    "ks": "ks",   # Kashmiri
    "doi": "doi", # Dogri
    "kok": "kok", # Konkani
    "mai": "mai", # Maithili
    "mni": "mni", # Manipuri
    "sat": "sat", # Santali
    "brx": "brx", # Bodo
}


class BhashiniSTT:
    """BHASHINI Speech-to-Text client for Indian languages.

    Supports streaming transcription via the BHASHINI API pipeline.
    Falls back gracefully if the API is unavailable.
    """

    BASE_URL = "https://dhruva-api.bhashini.gov.in/services/inference"
    PIPELINE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    def __init__(self):
        self.api_key = settings.bhashini_api_key
        self.user_id = settings.bhashini_user_id
        self._client: Optional[httpx.AsyncClient] = None
        self._pipeline_config: Optional[Dict] = None

    async def initialize(self):
        """Initialize the HTTP client and fetch pipeline configuration."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            },
        )
        logger.info("bhashini_stt_initialized")

    async def close(self):
        """Clean up resources."""
        if self._client:
            await self._client.aclose()

    async def _get_pipeline_config(self, source_language: str) -> Dict[str, Any]:
        """Fetch the STT pipeline config for a given language."""
        payload = {
            "pipelineTasks": [
                {"taskType": "asr", "config": {"language": {"sourceLanguage": source_language}}}
            ],
            "pipelineRequestConfig": {
                "pipelineId": "64392f96daac500b55c543cd"
            },
        }
        try:
            response = await self._client.post(
                "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("bhashini_pipeline_config_failed", error=str(e))
            raise

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "hi",
        sample_rate: int = 8000,
        audio_format: str = "wav",
    ) -> Dict[str, Any]:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes (PCM or WAV)
            language: ISO 639 language code
            sample_rate: Audio sample rate in Hz
            audio_format: Audio format (wav, pcm, mp3)

        Returns:
            Dictionary with 'text', 'confidence', 'language' keys
        """
        if not self._client:
            await self.initialize()

        bhashini_lang = BHASHINI_LANGUAGE_MAP.get(language, language)

        # Encode audio to base64 for API
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {"sourceLanguage": bhashini_lang},
                        "audioFormat": audio_format,
                        "samplingRate": sample_rate,
                    },
                }
            ],
            "inputData": {
                "audio": [{"audioContent": audio_b64}]
            },
        }

        try:
            response = await self._client.post(self.BASE_URL, json=payload)
            response.raise_for_status()
            result = response.json()

            # Parse BHASHINI response
            pipeline_output = result.get("pipelineResponse", [{}])
            if pipeline_output:
                asr_output = pipeline_output[0].get("output", [{}])
                if asr_output:
                    transcript = asr_output[0].get("source", "")
                    return {
                        "text": transcript,
                        "confidence": 0.85,  # BHASHINI doesn't always return confidence
                        "language": bhashini_lang,
                        "provider": "bhashini",
                    }

            return {"text": "", "confidence": 0.0, "language": bhashini_lang, "provider": "bhashini"}

        except httpx.TimeoutException:
            logger.warning("bhashini_timeout", language=bhashini_lang)
            return {"text": "", "confidence": 0.0, "language": bhashini_lang, "error": "timeout"}
        except Exception as e:
            logger.error("bhashini_transcription_failed", error=str(e), language=bhashini_lang)
            return {"text": "", "confidence": 0.0, "language": bhashini_lang, "error": str(e)}

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        language: str = "hi",
        sample_rate: int = 8000,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Streaming transcription — yields partial results as audio arrives.

        Accumulates audio in a buffer and sends chunks for transcription
        at regular intervals for near-real-time results.
        """
        buffer = bytearray()
        chunk_duration_bytes = sample_rate * 2  # 1 second of 16-bit audio

        async for chunk in audio_chunks:
            buffer.extend(chunk)

            # When we have enough audio (1 second), transcribe
            if len(buffer) >= chunk_duration_bytes:
                audio_segment = bytes(buffer[:chunk_duration_bytes])
                buffer = buffer[chunk_duration_bytes:]

                result = await self.transcribe(
                    audio_data=audio_segment,
                    language=language,
                    sample_rate=sample_rate,
                )
                if result.get("text"):
                    yield result

        # Process remaining buffer
        if buffer:
            result = await self.transcribe(
                audio_data=bytes(buffer),
                language=language,
                sample_rate=sample_rate,
            )
            if result.get("text"):
                yield result

    @property
    def supported_languages(self) -> list:
        return list(BHASHINI_LANGUAGE_MAP.keys())


# Singleton instance
bhashini_stt = BhashiniSTT()
