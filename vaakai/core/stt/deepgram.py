"""Deepgram STT Client — Fallback speech-to-text for English and other languages.

Deepgram Nova-3 provides sub-300ms streaming transcription with
excellent accuracy for English and common global languages.
"""

from __future__ import annotations

import asyncio
from typing import Optional, AsyncIterator, Dict, Any, Callable

import structlog

from config import settings

logger = structlog.get_logger(__name__)


class DeepgramSTT:
    """Deepgram Nova-3 STT client.

    Used as the primary STT for English and as fallback when BHASHINI
    is unavailable or returns low-confidence results.
    """

    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self._client = None

    async def initialize(self):
        """Initialize the Deepgram SDK client."""
        try:
            from deepgram import DeepgramClient, DeepgramClientOptions

            config = DeepgramClientOptions(
                options={"keepalive": "true"},
            )
            self._client = DeepgramClient(self.api_key, config)
            logger.info("deepgram_stt_initialized")
        except ImportError:
            logger.warning("deepgram_sdk_not_installed")
        except Exception as e:
            logger.error("deepgram_init_failed", error=str(e))

    async def close(self):
        """Clean up resources."""
        self._client = None

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        sample_rate: int = 8000,
        audio_format: str = "linear16",
    ) -> Dict[str, Any]:
        """Transcribe a complete audio segment.

        Args:
            audio_data: Raw audio bytes
            language: Language code (default: English)
            sample_rate: Audio sample rate
            audio_format: Audio encoding format

        Returns:
            Dictionary with 'text', 'confidence', 'language' keys
        """
        if not self._client:
            await self.initialize()

        if not self._client:
            return {"text": "", "confidence": 0.0, "language": language, "error": "client_not_initialized"}

        try:
            from deepgram import PrerecordedOptions

            options = PrerecordedOptions(
                model="nova-3",
                language=language,
                smart_format=True,
                punctuate=True,
                diarize=False,
                utterances=True,
                sample_rate=sample_rate,
                encoding=audio_format,
            )

            source = {"buffer": audio_data, "mimetype": f"audio/{audio_format}"}
            response = await asyncio.to_thread(
                self._client.listen.rest.v("1").transcribe_file, source, options
            )

            # Parse Deepgram response
            result = response.to_dict()
            channels = result.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    best = alternatives[0]
                    return {
                        "text": best.get("transcript", ""),
                        "confidence": best.get("confidence", 0.0),
                        "language": language,
                        "provider": "deepgram",
                        "words": best.get("words", []),
                    }

            return {"text": "", "confidence": 0.0, "language": language, "provider": "deepgram"}

        except Exception as e:
            logger.error("deepgram_transcription_failed", error=str(e))
            return {"text": "", "confidence": 0.0, "language": language, "error": str(e)}

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        language: str = "en",
        sample_rate: int = 8000,
        on_transcript: Optional[Callable] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Streaming transcription using Deepgram's WebSocket API.

        Yields partial transcripts as they arrive for low-latency processing.
        """
        if not self._client:
            await self.initialize()

        if not self._client:
            logger.error("deepgram_client_unavailable_for_stream")
            return

        results_queue: asyncio.Queue = asyncio.Queue()
        stream_complete = asyncio.Event()

        try:
            from deepgram import LiveOptions, LiveTranscriptionEvents

            options = LiveOptions(
                model="nova-3",
                language=language,
                smart_format=True,
                punctuate=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
                sample_rate=sample_rate,
                encoding="linear16",
                channels=1,
            )

            connection = self._client.listen.live.v("1")

            async def on_message(self_conn, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if transcript:
                    data = {
                        "text": transcript,
                        "confidence": result.channel.alternatives[0].confidence,
                        "is_final": result.is_final,
                        "language": language,
                        "provider": "deepgram",
                    }
                    await results_queue.put(data)
                    if on_transcript:
                        await on_transcript(data)

            async def on_error(self_conn, error, **kwargs):
                logger.error("deepgram_stream_error", error=str(error))

            connection.on(LiveTranscriptionEvents.Transcript, on_message)
            connection.on(LiveTranscriptionEvents.Error, on_error)

            await connection.start(options)

            # Feed audio chunks
            async for chunk in audio_chunks:
                connection.send(chunk)

            # Signal end of stream
            await connection.finish()
            stream_complete.set()

        except Exception as e:
            logger.error("deepgram_streaming_failed", error=str(e))
            stream_complete.set()

        # Yield all accumulated results
        while not results_queue.empty():
            yield await results_queue.get()


# Singleton instance
deepgram_stt = DeepgramSTT()
