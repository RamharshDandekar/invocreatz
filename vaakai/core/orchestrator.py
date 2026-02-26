"""VaakAI Orchestrator — Main pipeline conductor.

Manages the complete voice conversation pipeline:
STT → Language Detect → NLU/Emotion → Multi-LLM Router → Tool Executor → TTS

Runs fraud detection in parallel on every frame.
Handles streaming, interruption, turn-taking, and escalation.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Optional, Dict, Any, List, AsyncIterator
from dataclasses import dataclass, field

import structlog

from config import settings
from core.stt.ai4bharat import ai4bharat_stt
from core.stt.deepgram import deepgram_stt
from core.language_detect import language_detector
from core.nlu.intent import intent_classifier
from core.nlu.emotion import emotion_detector
from core.fraud_detector import fraud_detector
from core.llm.router import llm_router
from core.llm.openai_client import openai_client
from core.backchannel import backchannel_engine
from core.tts.elevenlabs import elevenlabs_tts
from core.tts.indic_tts import indic_tts
from memory.redis_client import redis_client
from memory.postgres_client import (
    CustomerRepository, CallRepository, TurnRepository,
    FraudRepository, RetrainRepository, CallDirection, ChannelType, CallStatus,
)

logger = structlog.get_logger(__name__)

# Confidence threshold below which utterances are queued for retraining
RETRAIN_CONFIDENCE_THRESHOLD = 0.7

# Max failed resolution attempts before escalation
MAX_FAILED_RESOLUTIONS = 3


@dataclass
class CallSession:
    """Active call session state."""
    session_id: str
    phone_number: str
    direction: CallDirection
    channel: ChannelType
    language: str = "hi"
    language_confidence: float = 0.0
    customer_id: Optional[str] = None
    customer_context: str = ""
    turn_index: int = 0
    failed_resolutions: int = 0
    is_active: bool = True
    start_time: float = field(default_factory=time.time)
    latencies: List[int] = field(default_factory=list)
    transcript_parts: List[str] = field(default_factory=list)
    call_db_id: Optional[str] = None


class VaakAIOrchestrator:
    """Main pipeline orchestrator for VaakAI voice conversations.

    Lifecycle:
    1. start_session() — Initialize call, load customer context
    2. process_audio() — Process each audio chunk through the pipeline
    3. end_session() — Finalize call, trigger post-call processing
    """

    def __init__(self):
        self._sessions: Dict[str, CallSession] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize all pipeline components."""
        logger.info("orchestrator_initializing")

        init_tasks = [
            ai4bharat_stt.initialize(),
            deepgram_stt.initialize(),
            language_detector.initialize(),
            intent_classifier.initialize(),
            emotion_detector.initialize(),
            fraud_detector.initialize(),
            llm_router.initialize(),
            elevenlabs_tts.initialize(),
            indic_tts.initialize(),
            redis_client.connect(),
        ]

        results = await asyncio.gather(*init_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"component_init_partial_failure", index=i, error=str(result))

        self._initialized = True
        logger.info("orchestrator_initialized")

    async def shutdown(self):
        """Clean up all components."""
        for session_id in list(self._sessions.keys()):
            await self.end_session(session_id)

        await asyncio.gather(
            ai4bharat_stt.close(),
            deepgram_stt.close(),
            elevenlabs_tts.close(),
            indic_tts.close(),
            llm_router.close(),
            redis_client.disconnect(),
            return_exceptions=True,
        )
        logger.info("orchestrator_shutdown")

    # ── Session Management ──────────────────────────

    async def start_session(
        self,
        phone_number: str,
        direction: CallDirection = CallDirection.INBOUND,
        channel: ChannelType = ChannelType.VOICE,
        context: Optional[Dict[str, Any]] = None,
    ) -> CallSession:
        """Start a new call session.

        Steps:
        1. Generate session ID
        2. Look up customer in CRM/DB
        3. Load omnichannel context from Redis
        4. Create call record in DB
        5. Initialize session state
        """
        session_id = f"call_{uuid.uuid4().hex[:12]}"

        # Look up / create customer (graceful if DB unavailable)
        customer = None
        customer_context = ""
        call_record = None
        try:
            customer = await CustomerRepository.get_or_create(phone_number)
            # Load omnichannel context from Redis
            omnichannel_ctx = await redis_client.get_customer_context(phone_number)
            customer_context = self._build_customer_context(customer, omnichannel_ctx)
            # Create call record in DB
            call_record = await CallRepository.create(
                session_id=session_id,
                phone_number=phone_number,
                direction=direction,
                channel=channel,
                customer_id=customer.id,
            )
        except Exception as e:
            logger.warning("session_db_unavailable", error=str(e))

        # Create session
        session = CallSession(
            session_id=session_id,
            phone_number=phone_number,
            direction=direction,
            channel=channel,
            customer_id=str(customer.id) if customer else None,
            customer_context=customer_context,
            call_db_id=str(call_record.id) if call_record else None,
        )

        self._sessions[session_id] = session

        # Store session in Redis (graceful if unavailable)
        try:
            await redis_client.create_session(session_id, {
                "phone": phone_number,
                "customer_id": str(customer.id) if customer else None,
                "language": session.language,
                "channel": channel.value,
                "start_time": session.start_time,
            })
        except Exception as e:
            logger.warning("session_redis_unavailable", error=str(e))

        # Reset per-call state
        emotion_detector.reset_trajectory()
        fraud_detector.reset()
        backchannel_engine.reset()

        logger.info(
            "session_started",
            session_id=session_id,
            phone=phone_number,
            direction=direction.value,
        )

        return session

    async def process_audio(
        self, session_id: str, audio_data: bytes
    ) -> Dict[str, Any]:
        """Process an audio chunk through the full pipeline.

        Pipeline steps (parallel where possible):
        1. STT (transcription)
        2. Language detection (if first chunk)
        3. Parallel: Intent + Emotion + Fraud analysis
        4. Back-channel response (immediate)
        5. LLM response generation
        6. TTS synthesis
        7. Update session state

        Returns:
            Dictionary with 'text_response', 'audio_response',
            'backchannel_audio', metadata, scores, etc.
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return {"error": "Session not found or inactive"}

        turn_start = time.monotonic()

        # ── Step 1: Language Detection (first few turns) ──────
        if session.turn_index < 3:
            lang_result = await language_detector.detect(
                # Use empty string for audio-level detection on first frame
                ""
            )
            if lang_result["confidence"] > session.language_confidence:
                session.language = lang_result["language"]
                session.language_confidence = lang_result["confidence"]

        # ── Step 2: Speech-to-Text ────────────────────────────
        if session.language == "en":
            stt_result = await deepgram_stt.transcribe(audio_data, language="en")
        else:
            stt_result = await ai4bharat_stt.transcribe(
                audio_data, language=session.language
            )
            # Fallback to Deepgram if AI4Bharat fails
            if not stt_result.get("text") and stt_result.get("error"):
                stt_result = await deepgram_stt.transcribe(audio_data, language="en")

        user_text = stt_result.get("text", "").strip()
        if not user_text:
            return {"status": "no_speech_detected", "session_id": session_id}

        # Refine language detection from actual text
        if session.turn_index < 5:
            text_lang = await language_detector.detect(user_text)
            if text_lang["confidence"] > session.language_confidence:
                session.language = text_lang["language"]
                session.language_confidence = text_lang["confidence"]

        session.transcript_parts.append(f"User: {user_text}")

        # ── Step 3: Parallel Analysis ─────────────────────────
        intent_task = intent_classifier.classify(user_text, session.language)
        emotion_task = emotion_detector.detect(user_text, session.language, session.turn_index)
        fraud_task = fraud_detector.analyze_frame(
            text=user_text,
            turn_index=session.turn_index,
            language=session.language,
            caller_phone=session.phone_number,
        )

        intent_result, emotion_result, fraud_result = await asyncio.gather(
            intent_task, emotion_task, fraud_task
        )

        # Inject intent/emotion into fraud analysis
        fraud_result_with_context = await fraud_detector.analyze_frame(
            text=user_text,
            turn_index=session.turn_index,
            language=session.language,
            emotion=emotion_result.get("emotion"),
            intent=intent_result.get("intent"),
            caller_phone=session.phone_number,
        )

        # ── Step 4: Back-channel Response ─────────────────────
        backchannel_text = backchannel_engine.get_response(
            language=session.language,
            emotion=emotion_result.get("emotion", "neutral"),
            response_type="thinking",
        )

        # Synthesize backchannel audio (non-blocking)
        backchannel_audio = None
        if session.language == "en":
            bc_result = await elevenlabs_tts.synthesize(backchannel_text)
            backchannel_audio = bc_result.get("audio")
        else:
            bc_result = await indic_tts.synthesize(backchannel_text, session.language)
            backchannel_audio = bc_result.get("audio")

        # ── Step 5: Check Escalation Conditions ───────────────
        should_escalate, escalation_reason = self._check_escalation(
            session, intent_result, emotion_result, fraud_result_with_context
        )

        if should_escalate:
            return await self._handle_escalation(
                session, escalation_reason, user_text, emotion_result
            )

        # ── Step 6: LLM Response Generation ──────────────────
        try:
            conversation_history = await redis_client.get_conversation_history(session_id)
        except Exception:
            conversation_history = []

        messages = openai_client.build_messages(
            user_text=user_text,
            conversation_history=conversation_history,
            language=session.language,
            emotion=emotion_result.get("emotion", "neutral"),
            urgency_score=emotion_result.get("urgency_score", 0),
            intent=intent_result.get("intent", "other"),
            customer_context=session.customer_context,
        )

        llm_result = await llm_router.generate(
            messages=messages,
            intent=intent_result.get("intent", "other"),
            urgency_score=emotion_result.get("urgency_score", 0),
        )

        bot_response = llm_result.get("text", "I'm sorry, could you repeat that?")
        session.transcript_parts.append(f"Bot: {bot_response}")

        # ── Step 7: TTS Synthesis ─────────────────────────────
        if session.language == "en":
            tts_result = await elevenlabs_tts.synthesize(
                bot_response,
                emotion=emotion_result.get("emotion", "neutral"),
            )
        else:
            tts_result = await indic_tts.synthesize(
                bot_response,
                language=session.language,
            )

        # ── Step 8: Update State ──────────────────────────────
        turn_latency_ms = int((time.monotonic() - turn_start) * 1000)
        session.latencies.append(turn_latency_ms)

        # Store conversation in Redis (graceful)
        try:
            await redis_client.append_message(session_id, "user", user_text)
            await redis_client.append_message(session_id, "assistant", bot_response, {
                "intent": intent_result.get("intent"),
                "emotion": emotion_result.get("emotion"),
                "fraud_score": fraud_result_with_context.get("cumulative_score"),
            })
        except Exception:
            pass

        # Store turn in DB (graceful)
        try:
            await TurnRepository.add_turn(
                call_id=uuid.UUID(session.call_db_id),
                turn_index=session.turn_index,
                speaker="user",
                text=user_text,
                language=session.language,
                intent=intent_result.get("intent"),
                intent_confidence=intent_result.get("confidence"),
                emotion=emotion_result.get("emotion"),
                emotion_confidence=emotion_result.get("confidence"),
            )
            await TurnRepository.add_turn(
                call_id=uuid.UUID(session.call_db_id),
                turn_index=session.turn_index,
                speaker="bot",
                text=bot_response,
                language=session.language,
                llm_model_used=llm_result.get("model"),
                llm_confidence=llm_result.get("confidence"),
                latency_ms=turn_latency_ms,
                tool_calls=llm_result.get("tool_calls", []),
            )
        except Exception:
            pass

        # Queue for retraining if low confidence
        try:
            if llm_result.get("confidence", 1.0) < RETRAIN_CONFIDENCE_THRESHOLD:
                await RetrainRepository.add_to_queue(
                    call_id=uuid.UUID(session.call_db_id),
                    turn_index=session.turn_index,
                    utterance=user_text,
                    detected_intent=intent_result.get("intent"),
                    confidence=llm_result.get("confidence", 0.0),
                )
        except Exception:
            pass

        session.turn_index += 1

        # Update Redis session (graceful)
        try:
            await redis_client.update_session(session_id, {
                "language": session.language,
                "turn_index": session.turn_index,
                "last_intent": intent_result.get("intent"),
                "last_emotion": emotion_result.get("emotion"),
                "fraud_score": fraud_result_with_context.get("cumulative_score"),
            })
        except Exception:
            pass

        return {
            "session_id": session_id,
            "user_text": user_text,
            "bot_response": bot_response,
            "audio_response": tts_result.get("audio", b""),
            "backchannel_audio": backchannel_audio,
            "backchannel_text": backchannel_text,
            "language": session.language,
            "intent": intent_result,
            "emotion": emotion_result,
            "fraud": fraud_result_with_context,
            "llm_model": llm_result.get("model"),
            "latency_ms": turn_latency_ms,
            "turn_index": session.turn_index - 1,
        }

    async def process_text(
        self, session_id: str, text: str
    ) -> Dict[str, Any]:
        """Process a text message (for WhatsApp/widget channels).

        Same pipeline as process_audio but skips STT step.
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            return {"error": "Session not found or inactive"}

        turn_start = time.monotonic()

        # Language detection from text
        lang_result = await language_detector.detect(text)
        session.language = lang_result["language"]
        session.language_confidence = lang_result["confidence"]

        # Parallel analysis
        intent_result, emotion_result, fraud_result = await asyncio.gather(
            intent_classifier.classify(text, session.language),
            emotion_detector.detect(text, session.language, session.turn_index),
            fraud_detector.analyze_frame(text, session.turn_index, session.language),
        )

        # LLM response
        try:
            conversation_history = await redis_client.get_conversation_history(session_id)
        except Exception:
            conversation_history = []
        messages = openai_client.build_messages(
            user_text=text,
            conversation_history=conversation_history,
            language=session.language,
            emotion=emotion_result.get("emotion", "neutral"),
            urgency_score=emotion_result.get("urgency_score", 0),
            intent=intent_result.get("intent", "other"),
            customer_context=session.customer_context,
        )

        llm_result = await llm_router.generate(
            messages=messages,
            intent=intent_result.get("intent", "other"),
        )

        bot_response = llm_result.get("text", "")

        # Store in Redis (graceful if unavailable)
        try:
            await redis_client.append_message(session_id, "user", text)
            await redis_client.append_message(session_id, "assistant", bot_response)
        except Exception:
            pass

        session.turn_index += 1

        return {
            "session_id": session_id,
            "user_text": text,
            "bot_response": bot_response,
            "language": session.language,
            "intent": intent_result,
            "emotion": emotion_result,
            "fraud": fraud_result,
            "latency_ms": int((time.monotonic() - turn_start) * 1000),
        }

    async def end_session(self, session_id: str, reason: str = "normal") -> Dict[str, Any]:
        """End a call session and trigger post-call processing.

        Steps:
        1. Finalize call record
        2. Update customer context for omnichannel memory
        3. Trigger async QA scoring
        4. Clean up session
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.is_active = False
        duration = int(time.time() - session.start_time)
        avg_latency = int(sum(session.latencies) / max(len(session.latencies), 1))

        # Finalize call record
        full_transcript = "\n".join(session.transcript_parts)
        emotion_trajectory = emotion_detector.get_trajectory()
        avg_sentiment = emotion_detector.get_average_sentiment()
        fraud_summary = fraud_detector.get_analysis_summary()

        try:
            await CallRepository.end_call(
                session_id=session_id,
                transcript=full_transcript,
                transcript_redacted=full_transcript,  # TODO: PII redaction
                resolution_summary=reason,
                emotion_trajectory=emotion_trajectory,
                intent_history=[],
                sentiment_avg=avg_sentiment,
                urgency_score=float(fraud_summary.get("cumulative_score", 0)),
                fraud_score=fraud_summary.get("cumulative_score", 0.0),
                duration_seconds=duration,
                avg_response_latency_ms=avg_latency,
            )
        except Exception as e:
            logger.warning("end_call_db_unavailable", error=str(e))

        # Update omnichannel context
        try:
            await redis_client.append_customer_interaction(
                session.phone_number,
                {
                    "channel": session.channel.value,
                    "session_id": session_id,
                    "summary": reason,
                    "sentiment": avg_sentiment,
                    "language": session.language,
                    "timestamp": time.time(),
                },
            )
        except Exception:
            pass

        # Clean up
        try:
            await redis_client.delete_session(session_id)
        except Exception:
            pass
        del self._sessions[session_id]

        logger.info(
            "session_ended",
            session_id=session_id,
            duration=duration,
            turns=session.turn_index,
            avg_latency_ms=avg_latency,
        )

        return {
            "session_id": session_id,
            "status": "completed",
            "duration_seconds": duration,
            "total_turns": session.turn_index,
            "avg_latency_ms": avg_latency,
            "sentiment_avg": avg_sentiment,
            "fraud_score": fraud_summary.get("cumulative_score", 0),
        }

    # ── Escalation Logic ───────────────────────────

    def _check_escalation(
        self,
        session: CallSession,
        intent_result: Dict,
        emotion_result: Dict,
        fraud_result: Dict,
    ) -> tuple:
        """Check if the call should be escalated to a human agent.

        Conditions:
        1. 3+ failed resolution attempts
        2. Extreme negative sentiment
        3. Explicit escalation request
        4. High fraud score
        """
        # Explicit escalation request
        if intent_result.get("intent") == "escalation_request":
            return True, "customer_requested_escalation"

        # High fraud score
        if fraud_result.get("is_suspicious", False):
            return True, f"fraud_alert_score_{fraud_result.get('cumulative_score', 0)}"

        # Extreme anger
        emotion = emotion_result.get("emotion", "neutral")
        urgency = emotion_result.get("urgency_score", 0)
        if emotion == "angry" and urgency >= 8:
            return True, "extreme_negative_emotion"

        # Failed resolutions
        if session.failed_resolutions >= MAX_FAILED_RESOLUTIONS:
            return True, "max_failed_resolutions_exceeded"

        return False, ""

    async def _handle_escalation(
        self,
        session: CallSession,
        reason: str,
        last_utterance: str,
        emotion_result: Dict,
    ) -> Dict[str, Any]:
        """Handle escalation to human agent."""
        logger.warning(
            "call_escalated",
            session_id=session.session_id,
            reason=reason,
            phone=session.phone_number,
        )

        # Update call status
        await CallRepository.update_status(
            session.session_id,
            CallStatus.ESCALATED,
            escalated=True,
            escalation_reason=reason,
        )

        # If fraud-related, create fraud flag
        if "fraud" in reason:
            await FraudRepository.create_flag(
                call_id=uuid.UUID(session.call_db_id),
                fraud_score=fraud_detector.get_score(),
                indicators=fraud_detector.get_indicators(),
                description=f"Escalated: {reason}",
                customer_id=uuid.UUID(session.customer_id) if session.customer_id else None,
            )

        # Generate escalation response
        escalation_messages = {
            "en": "I'm connecting you with a human agent who can better assist you. They'll have the full context of our conversation.",
            "hi": "Main aapko ek human agent se connect kar raha hoon jo aapki behtar madad kar sakenge. Unke paas hamari puri baat ka context hoga.",
        }
        response = escalation_messages.get(session.language, escalation_messages["en"])

        # Synthesize escalation response
        if session.language == "en":
            tts_result = await elevenlabs_tts.synthesize(response, emotion="empathetic")
        else:
            tts_result = await indic_tts.synthesize(response, session.language)

        session.is_active = False

        return {
            "session_id": session.session_id,
            "status": "escalated",
            "reason": reason,
            "bot_response": response,
            "audio_response": tts_result.get("audio", b""),
            "escalation_context": {
                "phone": session.phone_number,
                "transcript": "\n".join(session.transcript_parts),
                "emotion_trajectory": emotion_detector.get_trajectory(),
                "fraud_indicators": fraud_detector.get_indicators(),
                "language": session.language,
            },
        }

    # ── Helper Methods ──────────────────────────────

    def _build_customer_context(self, customer, omnichannel_ctx: Optional[Dict]) -> str:
        """Build a natural language customer context for LLM prompt injection."""
        parts = []

        if customer.name:
            parts.append(f"Customer name: {customer.name}")
        parts.append(f"Phone: {customer.phone}")
        if customer.preferred_language:
            parts.append(f"Preferred language: {customer.preferred_language}")

        if omnichannel_ctx:
            interactions = omnichannel_ctx.get("interactions", [])
            if interactions:
                last = interactions[-1]
                parts.append(
                    f"Last interaction: {last.get('channel', 'unknown')} channel, "
                    f"sentiment was {last.get('sentiment', 'unknown')}"
                )
                if last.get("summary"):
                    parts.append(f"Last interaction summary: {last['summary']}")

        return "\n".join(parts) if parts else "No prior context available."

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return [sid for sid, s in self._sessions.items() if s.is_active]


# Singleton instance
orchestrator = VaakAIOrchestrator()
