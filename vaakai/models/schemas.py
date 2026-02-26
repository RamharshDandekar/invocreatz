"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ── Call Schemas ───────────────────────────────────

class CallInitiateRequest(BaseModel):
    phone_number: str = Field(..., description="E.164 format phone number")
    language: Optional[str] = Field(None, description="Preferred language code (auto-detect if empty)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the call")
    campaign_id: Optional[str] = Field(None, description="Proactive outreach campaign ID")


class CallInitiateResponse(BaseModel):
    session_id: str
    status: str
    message: str


class CallEndRequest(BaseModel):
    session_id: str
    reason: Optional[str] = Field("normal", description="Reason for ending the call")


class CallEndResponse(BaseModel):
    session_id: str
    status: str
    duration_seconds: Optional[int] = None
    qa_score: Optional[float] = None


class CallAnalytics(BaseModel):
    session_id: str
    direction: str
    channel: str
    status: str
    phone_number: str
    language_detected: Optional[str] = None
    duration_seconds: Optional[int] = None
    sentiment_avg: Optional[float] = None
    urgency_score: Optional[float] = None
    fraud_score: Optional[float] = None
    qa_overall_score: Optional[float] = None
    escalated: bool = False
    started_at: datetime
    ended_at: Optional[datetime] = None


# ── Customer Schemas ──────────────────────────────

class CustomerProfile(BaseModel):
    id: uuid.UUID
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None
    crm_external_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    consent_given: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    preferred_language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ── Ticket Schemas ─────────────────────────────────

class TicketCreateRequest(BaseModel):
    customer_phone: str
    subject: str
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", description="low | medium | high | urgent")
    intent: Optional[str] = None
    call_session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    crm_ticket_id: Optional[str] = None
    subject: str
    status: str
    priority: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── WhatsApp Schemas ───────────────────────────────

class WhatsAppMessageRequest(BaseModel):
    phone_number: str = Field(..., description="Recipient phone number in E.164 format")
    template_name: Optional[str] = Field(None, description="Pre-approved template name")
    message: Optional[str] = Field(None, description="Free-text message (if no template)")
    context: Optional[Dict[str, Any]] = Field(None, description="Template variable values")


class WhatsAppMessageResponse(BaseModel):
    message_id: str
    status: str
    phone_number: str


# ── Fraud Schemas ──────────────────────────────────

class FraudFlagRequest(BaseModel):
    session_id: str
    reason: Optional[str] = None


class FraudFlagResponse(BaseModel):
    id: uuid.UUID
    call_id: uuid.UUID
    fraud_score: float
    status: str
    indicators: Optional[List[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analytics Schemas ──────────────────────────────

class AnalyticsQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    channel: Optional[str] = None
    language: Optional[str] = None
    min_qa_score: Optional[float] = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)


class AnalyticsSummary(BaseModel):
    total_calls: int
    avg_duration_seconds: float
    avg_sentiment: float
    avg_qa_score: float
    resolution_rate: float
    escalation_rate: float
    fraud_flags_count: int
    language_distribution: Dict[str, int]
    emotion_distribution: Dict[str, int]
    calls_by_day: List[Dict[str, Any]]


# ── Admin Schemas ──────────────────────────────────

class RetrainQueueRequest(BaseModel):
    call_session_id: str
    turn_index: int
    utterance: str
    detected_intent: Optional[str] = None
    confidence: float


class RetrainQueueResponse(BaseModel):
    id: uuid.UUID
    status: str = "queued"
    message: str = "Utterance added to retraining queue"


# ── Health Schemas ─────────────────────────────────

class ComponentHealth(BaseModel):
    name: str
    status: str  # "healthy" | "degraded" | "unhealthy"
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    uptime_seconds: float
    components: List[ComponentHealth]
