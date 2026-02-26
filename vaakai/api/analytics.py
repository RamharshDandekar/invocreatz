"""Analytics API Routes — Reporting and insights.

Endpoints:
- GET /analytics/summary          — Overall analytics summary
- GET /analytics/calls            — Call history with filters
- GET /analytics/sentiment        — Sentiment trends
- GET /analytics/language-dist    — Language distribution
- GET /analytics/intents          — Top intents
- GET /analytics/fraud            — Fraud alerts
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from memory.postgres_client import CallRepository, FraudRepository

router = APIRouter()


@router.get("/analytics/summary")
async def analytics_summary(
    days: int = Query(7, ge=1, le=365),
):
    """Get overall analytics summary for the past N days."""
    summary = await CallRepository.get_analytics_summary(days)
    return summary


@router.get("/analytics/calls")
async def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    channel: Optional[str] = None,
    language: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """List call records with pagination and filters."""
    calls = await CallRepository.list_calls(
        page=page,
        page_size=page_size,
        status=status,
        channel=channel,
        language=language,
        date_from=date_from,
        date_to=date_to,
    )
    return {
        "page": page,
        "page_size": page_size,
        "calls": calls,
    }


@router.get("/analytics/sentiment")
async def sentiment_trends(
    days: int = Query(7, ge=1, le=365),
    granularity: str = Query("day", regex="^(hour|day|week)$"),
):
    """Get sentiment trends over time."""
    trends = await CallRepository.get_sentiment_trends(days, granularity)
    return {"granularity": granularity, "days": days, "trends": trends}


@router.get("/analytics/language-distribution")
async def language_distribution(
    days: int = Query(30, ge=1, le=365),
):
    """Get language distribution across calls."""
    dist = await CallRepository.get_language_distribution(days)
    return {"days": days, "distribution": dist}


@router.get("/analytics/intents")
async def top_intents(
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
):
    """Get top detected intents."""
    intents = await CallRepository.get_top_intents(days, limit)
    return {"days": days, "intents": intents}


@router.get("/analytics/fraud")
async def fraud_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
):
    """List fraud alerts."""
    alerts = await FraudRepository.list_flags(
        page=page,
        page_size=page_size,
        status=status,
    )
    return {
        "page": page,
        "page_size": page_size,
        "alerts": alerts,
    }


@router.get("/analytics/performance")
async def performance_metrics(
    days: int = Query(7, ge=1, le=365),
):
    """Get performance metrics (latency, resolution rates, etc)."""
    metrics = await CallRepository.get_performance_metrics(days)
    return {"days": days, "metrics": metrics}
