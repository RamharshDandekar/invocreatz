"""PostgreSQL async client and session management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update, func, and_
import structlog

from config import settings
from models.database import (
    Base, Customer, CallRecord, ConversationTurn, Ticket,
    FraudFlag, RetrainingQueue, CallStatus, CallDirection,
    ChannelType, TicketStatus, FraudStatus,
)

logger = structlog.get_logger(__name__)

# ── Engine & Session Factory ────────────────────────

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables (development only; use Alembic in production)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def get_session() -> AsyncSession:
    """Dependency for FastAPI — yields an async session."""
    async with async_session_factory() as session:
        yield session


# ── Customer Operations ─────────────────────────────

class CustomerRepository:
    """Database operations for Customer model."""

    @staticmethod
    async def get_by_phone(phone: str) -> Optional[Customer]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Customer).where(Customer.phone == phone)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(customer_id: uuid.UUID) -> Optional[Customer]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create(phone: str, name: Optional[str] = None, **kwargs) -> Customer:
        async with async_session_factory() as session:
            customer = Customer(phone=phone, name=name, **kwargs)
            session.add(customer)
            await session.commit()
            await session.refresh(customer)
            logger.info("customer_created", phone=phone, customer_id=str(customer.id))
            return customer

    @staticmethod
    async def get_or_create(phone: str, **kwargs) -> Customer:
        customer = await CustomerRepository.get_by_phone(phone)
        if not customer:
            customer = await CustomerRepository.create(phone, **kwargs)
        return customer

    @staticmethod
    async def update(customer_id: uuid.UUID, **kwargs) -> Optional[Customer]:
        async with async_session_factory() as session:
            await session.execute(
                update(Customer).where(Customer.id == customer_id).values(**kwargs)
            )
            await session.commit()
            return await CustomerRepository.get_by_id(customer_id)


# ── Call Record Operations ──────────────────────────

class CallRepository:
    """Database operations for CallRecord model."""

    @staticmethod
    async def create(
        session_id: str,
        phone_number: str,
        direction: CallDirection,
        channel: ChannelType = ChannelType.VOICE,
        customer_id: Optional[uuid.UUID] = None,
    ) -> CallRecord:
        async with async_session_factory() as session:
            call = CallRecord(
                session_id=session_id,
                phone_number=phone_number,
                direction=direction,
                channel=channel,
                customer_id=customer_id,
                status=CallStatus.INITIATED,
            )
            session.add(call)
            await session.commit()
            await session.refresh(call)
            logger.info("call_created", session_id=session_id, direction=direction.value)
            return call

    @staticmethod
    async def get_by_session_id(session_id: str) -> Optional[CallRecord]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(CallRecord).where(CallRecord.session_id == session_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def update_status(session_id: str, status: CallStatus, **kwargs) -> Optional[CallRecord]:
        async with async_session_factory() as session:
            await session.execute(
                update(CallRecord)
                .where(CallRecord.session_id == session_id)
                .values(status=status, **kwargs)
            )
            await session.commit()
            return await CallRepository.get_by_session_id(session_id)

    @staticmethod
    async def end_call(
        session_id: str, transcript: str, transcript_redacted: str,
        resolution_summary: str, emotion_trajectory: list,
        intent_history: list, sentiment_avg: float,
        urgency_score: float, fraud_score: float,
        duration_seconds: int, avg_response_latency_ms: int,
    ) -> Optional[CallRecord]:
        async with async_session_factory() as session:
            await session.execute(
                update(CallRecord)
                .where(CallRecord.session_id == session_id)
                .values(
                    status=CallStatus.COMPLETED,
                    transcript=transcript,
                    transcript_redacted=transcript_redacted,
                    resolution_summary=resolution_summary,
                    emotion_trajectory=emotion_trajectory,
                    intent_history=intent_history,
                    sentiment_avg=sentiment_avg,
                    urgency_score=urgency_score,
                    fraud_score=fraud_score,
                    duration_seconds=duration_seconds,
                    avg_response_latency_ms=avg_response_latency_ms,
                    ended_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
            return await CallRepository.get_by_session_id(session_id)

    @staticmethod
    async def get_analytics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        channel: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CallRecord]:
        async with async_session_factory() as session:
            query = select(CallRecord)
            filters = []
            if start_date:
                filters.append(CallRecord.started_at >= start_date)
            if end_date:
                filters.append(CallRecord.started_at <= end_date)
            if channel:
                filters.append(CallRecord.channel == channel)
            if filters:
                query = query.where(and_(*filters))
            query = query.order_by(CallRecord.started_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    async def get_summary_stats(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        async with async_session_factory() as session:
            filters = []
            if start_date:
                filters.append(CallRecord.started_at >= start_date)
            if end_date:
                filters.append(CallRecord.started_at <= end_date)

            where_clause = and_(*filters) if filters else True

            result = await session.execute(
                select(
                    func.count(CallRecord.id).label("total_calls"),
                    func.avg(CallRecord.duration_seconds).label("avg_duration"),
                    func.avg(CallRecord.sentiment_avg).label("avg_sentiment"),
                    func.avg(CallRecord.qa_overall_score).label("avg_qa_score"),
                ).where(where_clause)
            )
            row = result.one()

            # Escalation rate
            escalated_result = await session.execute(
                select(func.count(CallRecord.id))
                .where(and_(where_clause, CallRecord.escalated == True))
            )
            escalated_count = escalated_result.scalar() or 0

            # Resolution rate
            resolved_result = await session.execute(
                select(func.count(CallRecord.id))
                .where(and_(where_clause, CallRecord.status == CallStatus.COMPLETED))
            )
            resolved_count = resolved_result.scalar() or 0

            total = row.total_calls or 1

            return {
                "total_calls": row.total_calls or 0,
                "avg_duration_seconds": float(row.avg_duration or 0),
                "avg_sentiment": float(row.avg_sentiment or 0),
                "avg_qa_score": float(row.avg_qa_score or 0),
                "resolution_rate": resolved_count / total,
                "escalation_rate": escalated_count / total,
            }


# ── Conversation Turn Operations ────────────────────

class TurnRepository:
    @staticmethod
    async def add_turn(
        call_id: uuid.UUID,
        turn_index: int,
        speaker: str,
        text: str,
        text_redacted: Optional[str] = None,
        language: Optional[str] = None,
        intent: Optional[str] = None,
        intent_confidence: Optional[float] = None,
        emotion: Optional[str] = None,
        emotion_confidence: Optional[float] = None,
        llm_model_used: Optional[str] = None,
        llm_confidence: Optional[float] = None,
        latency_ms: Optional[int] = None,
        tool_calls: Optional[list] = None,
    ) -> ConversationTurn:
        async with async_session_factory() as session:
            turn = ConversationTurn(
                call_id=call_id,
                turn_index=turn_index,
                speaker=speaker,
                text=text,
                text_redacted=text_redacted,
                language=language,
                intent=intent,
                intent_confidence=intent_confidence,
                emotion=emotion,
                emotion_confidence=emotion_confidence,
                llm_model_used=llm_model_used,
                llm_confidence=llm_confidence,
                latency_ms=latency_ms,
                tool_calls=tool_calls or [],
            )
            session.add(turn)
            await session.commit()
            await session.refresh(turn)
            return turn


# ── Ticket Operations ───────────────────────────────

class TicketRepository:
    @staticmethod
    async def create(
        customer_id: uuid.UUID,
        subject: str,
        description: Optional[str] = None,
        call_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> Ticket:
        async with async_session_factory() as session:
            ticket = Ticket(
                customer_id=customer_id,
                call_id=call_id,
                subject=subject,
                description=description,
                **kwargs,
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            logger.info("ticket_created", ticket_id=str(ticket.id))
            return ticket

    @staticmethod
    async def update_status(ticket_id: uuid.UUID, status: TicketStatus) -> Optional[Ticket]:
        async with async_session_factory() as session:
            await session.execute(
                update(Ticket).where(Ticket.id == ticket_id).values(status=status)
            )
            await session.commit()
            result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
            return result.scalar_one_or_none()


# ── Fraud Flag Operations ──────────────────────────

class FraudRepository:
    @staticmethod
    async def create_flag(
        call_id: uuid.UUID,
        fraud_score: float,
        indicators: Optional[list] = None,
        description: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
    ) -> FraudFlag:
        async with async_session_factory() as session:
            flag = FraudFlag(
                call_id=call_id,
                customer_id=customer_id,
                fraud_score=fraud_score,
                indicators=indicators or [],
                description=description,
            )
            session.add(flag)
            await session.commit()
            await session.refresh(flag)
            logger.warning("fraud_flag_created", call_id=str(call_id), score=fraud_score)
            return flag

    @staticmethod
    async def get_flags_count(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        async with async_session_factory() as session:
            query = select(func.count(FraudFlag.id))
            if start_date:
                query = query.where(FraudFlag.created_at >= start_date)
            if end_date:
                query = query.where(FraudFlag.created_at <= end_date)
            result = await session.execute(query)
            return result.scalar() or 0


# ── Retraining Queue Operations ────────────────────

class RetrainRepository:
    @staticmethod
    async def add_to_queue(
        call_id: uuid.UUID,
        turn_index: int,
        utterance: str,
        detected_intent: Optional[str] = None,
        confidence: float = 0.0,
    ) -> RetrainingQueue:
        async with async_session_factory() as session:
            entry = RetrainingQueue(
                call_id=call_id,
                turn_index=turn_index,
                utterance=utterance,
                detected_intent=detected_intent,
                confidence=confidence,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            logger.info("retraining_queued", call_id=str(call_id), confidence=confidence)
            return entry

    @staticmethod
    async def get_pending(limit: int = 100) -> List[RetrainingQueue]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RetrainingQueue)
                .where(RetrainingQueue.reviewed == False)
                .order_by(RetrainingQueue.confidence.asc())
                .limit(limit)
            )
            return list(result.scalars().all())
