"""SQLAlchemy database models for VaakAI."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    JSON, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────

class CallStatus(str, enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class CallDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ChannelType(str, enum.Enum):
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    WIDGET = "widget"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class FraudStatus(str, enum.Enum):
    CLEAR = "clear"
    SUSPICIOUS = "suspicious"
    CONFIRMED = "confirmed"
    INVESTIGATING = "investigating"


# ── Models ─────────────────────────────────────────

class Customer(Base):
    """Customer profile aggregated across all channels."""
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="hi")
    crm_external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    erp_external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    calls: Mapped[List["CallRecord"]] = relationship("CallRecord", back_populates="customer")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="customer")
    fraud_flags: Mapped[List["FraudFlag"]] = relationship("FraudFlag", back_populates="customer")


class CallRecord(Base):
    """Record of every call processed by VaakAI."""
    __tablename__ = "call_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    direction: Mapped[CallDirection] = mapped_column(SQLEnum(CallDirection), nullable=False)
    channel: Mapped[ChannelType] = mapped_column(SQLEnum(ChannelType), default=ChannelType.VOICE)
    status: Mapped[CallStatus] = mapped_column(SQLEnum(CallStatus), default=CallStatus.INITIATED)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    language_detected: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    language_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Transcript and analysis
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript_redacted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intent_history: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    emotion_trajectory: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scores
    sentiment_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    urgency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    fraud_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)

    # QA scores (filled post-call)
    qa_resolution_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qa_empathy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qa_compliance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    qa_overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timing
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_response_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="calls")
    turns: Mapped[List["ConversationTurn"]] = relationship("ConversationTurn", back_populates="call")

    __table_args__ = (
        Index("ix_call_records_started_at", "started_at"),
        Index("ix_call_records_customer_status", "customer_id", "status"),
    )


class ConversationTurn(Base):
    """Individual turn in a conversation (user utterance + bot response)."""
    __tablename__ = "conversation_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("call_records.id"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String(10), nullable=False)  # "user" or "bot"
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_redacted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    intent_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    emotion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    emotion_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tool_calls: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    call: Mapped["CallRecord"] = relationship("CallRecord", back_populates="turns")

    __table_args__ = (
        Index("ix_conv_turns_call_idx", "call_id", "turn_index"),
    )


class Ticket(Base):
    """CRM tickets created during calls."""
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    call_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("call_records.id"), nullable=True
    )
    crm_ticket_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TicketStatus] = mapped_column(SQLEnum(TicketStatus), default=TicketStatus.OPEN)
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="medium")
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sentiment_at_creation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tickets")


class FraudFlag(Base):
    """Fraud detection flags raised during calls."""
    __tablename__ = "fraud_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("call_records.id"), nullable=False
    )
    fraud_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[FraudStatus] = mapped_column(SQLEnum(FraudStatus), default=FraudStatus.SUSPICIOUS)
    indicators: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=list)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="fraud_flags")


class RetrainingQueue(Base):
    """Low-confidence utterances queued for model retraining."""
    __tablename__ = "retraining_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("call_records.id"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    utterance: Mapped[str] = mapped_column(Text, nullable=False)
    detected_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    correct_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Human-labeled
    correct_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Human-labeled
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
