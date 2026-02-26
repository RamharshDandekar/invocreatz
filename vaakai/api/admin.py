"""Admin API Routes — System administration and configuration.

Endpoints:
- GET    /admin/sessions           — List active sessions
- DELETE /admin/sessions/{id}      — Force-end a session
- GET    /admin/retrain-queue      — View retraining queue
- POST   /admin/retrain/{id}/resolve — Resolve a retrain item
- POST   /admin/consent/check      — Check customer consent
- POST   /admin/consent/withdraw   — Withdraw consent (DPDPA)
- POST   /admin/data-deletion      — Handle DPDPA deletion request
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.orchestrator import orchestrator
from compliance.consent_manager import consent_manager, ConsentPurpose
from memory.postgres_client import RetrainRepository

router = APIRouter()


class ConsentCheckRequest(BaseModel):
    phone: str


class ConsentWithdrawRequest(BaseModel):
    phone: str
    purpose: str


class DataDeletionRequest(BaseModel):
    phone: str


class RetrainResolveRequest(BaseModel):
    corrected_intent: Optional[str] = None
    notes: Optional[str] = None


@router.get("/admin/sessions")
async def list_sessions():
    """List all active call sessions."""
    sessions = []
    for sid, s in orchestrator._sessions.items():
        if s.is_active:
            sessions.append({
                "session_id": sid,
                "phone": s.phone_number,
                "language": s.language,
                "channel": s.channel.value,
                "turn_index": s.turn_index,
                "duration_seconds": __import__("time").time() - s.start_time,
            })
    return {"active_sessions": sessions, "count": len(sessions)}


@router.delete("/admin/sessions/{session_id}")
async def force_end_session(session_id: str):
    """Force-end an active session (admin action)."""
    result = await orchestrator.end_session(session_id, reason="admin_force_end")
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/admin/retrain-queue")
async def get_retrain_queue(
    page: int = 1,
    page_size: int = 20,
):
    """View items queued for model retraining."""
    items = await RetrainRepository.list_queue(page, page_size)
    return {"page": page, "items": items}


@router.post("/admin/retrain/{item_id}/resolve")
async def resolve_retrain_item(
    item_id: str,
    req: RetrainResolveRequest,
):
    """Resolve/annotate a retraining queue item."""
    success = await RetrainRepository.resolve_item(
        item_id, req.corrected_intent, req.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "resolved", "item_id": item_id}


@router.post("/admin/consent/check")
async def check_consent(req: ConsentCheckRequest):
    """Check all consent statuses for a customer."""
    consents = await consent_manager.get_all_consents(req.phone)
    return {"phone": req.phone, "consents": consents}


@router.post("/admin/consent/withdraw")
async def withdraw_consent(req: ConsentWithdrawRequest):
    """Withdraw consent for a specific purpose (DPDPA compliance)."""
    try:
        purpose = ConsentPurpose(req.purpose)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid purpose. Valid: {[p.value for p in ConsentPurpose]}",
        )

    success = await consent_manager.withdraw_consent(req.phone, purpose)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to withdraw consent")

    return {"status": "withdrawn", "phone": req.phone, "purpose": req.purpose}


@router.post("/admin/data-deletion")
async def request_data_deletion(req: DataDeletionRequest):
    """Handle DPDPA right-to-erasure request."""
    result = await consent_manager.handle_data_deletion_request(req.phone)
    return result
