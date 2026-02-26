"""Post-Call QA Agent — Automated quality assurance scoring.

Runs asynchronously (via Celery) after each call ends to:
1. Score the conversation on multiple dimensions
2. Detect compliance violations
3. Flag conversations needing human review
4. Update analytics metrics

Scoring dimensions:
- Resolution Quality (0-10)
- Agent Politeness / Tone (0-10)
- Response Accuracy (0-10)
- Compliance Adherence (0-10)
- Customer Satisfaction Prediction (0-10)
"""

from __future__ import annotations

import json
from typing import Dict, Any, List, Optional

import structlog

from core.llm.openai_client import openai_client
from core.celery_app import celery_app

logger = structlog.get_logger(__name__)

QA_SYSTEM_PROMPT = """You are a Quality Assurance analyst for a customer service AI chatbot called VaakAI.
Analyze the following conversation transcript and score it on each dimension from 0-10.

Scoring dimensions:
1. resolution_quality: Was the customer's issue resolved? (0=unresolved, 10=perfectly resolved)
2. tone_quality: Was the bot's tone appropriate, empathetic, and professional? (0=rude/cold, 10=excellent)
3. accuracy: Were the bot's responses factually accurate and helpful? (0=incorrect, 10=perfectly accurate)
4. compliance: Did the conversation follow proper compliance procedures (consent, PII handling)? (0=violations, 10=fully compliant)
5. csat_prediction: Predicted customer satisfaction score (0=very dissatisfied, 10=very satisfied)

Also provide:
- summary: A 2-3 sentence summary of the conversation
- issues: List of any issues or areas for improvement
- escalation_needed: Boolean — should this conversation be reviewed by a human supervisor?

Respond in JSON format only."""


class QAAgent:
    """Post-call quality assurance scoring agent."""

    async def score_conversation(
        self,
        transcript: str,
        language: str = "en",
        emotion_trajectory: Optional[List[str]] = None,
        fraud_score: float = 0.0,
        call_duration: int = 0,
        avg_latency_ms: int = 0,
    ) -> Dict[str, Any]:
        """Score a completed conversation.

        Args:
            transcript: Full conversation transcript
            language: Primary language of the conversation
            emotion_trajectory: List of emotions detected across turns
            fraud_score: Final fraud detection score
            call_duration: Total call duration in seconds
            avg_latency_ms: Average response latency

        Returns:
            Dictionary with scores, summary, issues, and flags
        """
        # Build context for the QA analysis
        context_parts = [
            f"Language: {language}",
            f"Duration: {call_duration}s",
            f"Avg Response Latency: {avg_latency_ms}ms",
        ]

        if emotion_trajectory:
            context_parts.append(f"Emotion trajectory: {' → '.join(emotion_trajectory)}")

        if fraud_score > 0:
            context_parts.append(f"Fraud score: {fraud_score:.2f}")

        context = "\n".join(context_parts)
        full_prompt = f"Call Metadata:\n{context}\n\nTranscript:\n{transcript}"

        try:
            result = await openai_client.generate(
                messages=[
                    {"role": "system", "content": QA_SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt},
                ],
                model="gpt-4o-mini",  # Cost-effective for batch QA
                temperature=0.3,
            )

            response_text = result.get("text", "{}")

            # Parse JSON response
            try:
                # Clean markdown wrapping if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]

                scores = json.loads(response_text.strip())
            except json.JSONDecodeError:
                logger.warning("qa_json_parse_failed", response=response_text[:200])
                scores = self._default_scores()

            # Add computed metrics
            scores["latency_score"] = self._score_latency(avg_latency_ms)
            scores["overall_score"] = self._compute_overall(scores)

            # Flag for review if any score is below threshold
            if scores.get("overall_score", 0) < 5 or scores.get("escalation_needed"):
                scores["needs_review"] = True
            else:
                scores["needs_review"] = False

            return scores

        except Exception as e:
            logger.error("qa_scoring_failed", error=str(e))
            return self._default_scores()

    def _score_latency(self, avg_ms: int) -> float:
        """Score response latency (target: <500ms)."""
        if avg_ms <= 300:
            return 10.0
        elif avg_ms <= 500:
            return 8.0
        elif avg_ms <= 1000:
            return 6.0
        elif avg_ms <= 2000:
            return 4.0
        else:
            return 2.0

    def _compute_overall(self, scores: Dict) -> float:
        """Compute weighted overall quality score."""
        weights = {
            "resolution_quality": 0.30,
            "tone_quality": 0.15,
            "accuracy": 0.25,
            "compliance": 0.15,
            "csat_prediction": 0.15,
        }

        total = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            val = scores.get(key)
            if isinstance(val, (int, float)):
                total += val * weight
                weight_sum += weight

        return round(total / max(weight_sum, 0.01), 2)

    def _default_scores(self) -> Dict[str, Any]:
        """Return default scores when QA analysis fails."""
        return {
            "resolution_quality": 5,
            "tone_quality": 5,
            "accuracy": 5,
            "compliance": 5,
            "csat_prediction": 5,
            "overall_score": 5.0,
            "summary": "QA analysis unavailable",
            "issues": ["Automated QA scoring failed"],
            "escalation_needed": False,
            "needs_review": True,
        }


qa_agent = QAAgent()


# ── Celery Tasks ─────────────────────────────────

@celery_app.task(name="vaakai.post_call_qa")
def task_post_call_qa(
    call_id: str,
    transcript: str,
    language: str = "en",
    emotion_trajectory: Optional[List[str]] = None,
    fraud_score: float = 0.0,
    call_duration: int = 0,
    avg_latency_ms: int = 0,
):
    """Celery task for async post-call QA scoring."""
    import asyncio

    async def _run():
        scores = await qa_agent.score_conversation(
            transcript=transcript,
            language=language,
            emotion_trajectory=emotion_trajectory,
            fraud_score=fraud_score,
            call_duration=call_duration,
            avg_latency_ms=avg_latency_ms,
        )

        # Store QA scores in database
        from memory.postgres_client import CallRepository
        await CallRepository.update_qa_scores(call_id, scores)

        return scores

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
