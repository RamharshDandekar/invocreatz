"""CRM API Routes — Customer and ticket management.

Endpoints:
- GET    /crm/customer/{phone}  — Look up customer
- POST   /crm/ticket            — Create support ticket
- GET    /crm/ticket/{id}       — Get ticket details
- PATCH  /crm/ticket/{id}       — Update ticket
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.tools.crm_tools import (
    lookup_customer,
    create_support_ticket,
    get_open_tickets,
    search_knowledge_base,
)

router = APIRouter()


class TicketCreateRequest(BaseModel):
    phone: str
    subject: str
    description: str
    priority: str = "Medium"


class KBSearchRequest(BaseModel):
    query: str


@router.get("/crm/customer/{phone}")
async def get_customer(phone: str):
    """Look up a customer by phone number across all CRM systems."""
    result = await lookup_customer(phone)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/crm/ticket")
async def create_ticket(req: TicketCreateRequest):
    """Create a support ticket in the available CRM."""
    result = await create_support_ticket(
        phone=req.phone,
        subject=req.subject,
        description=req.description,
        priority=req.priority,
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/crm/tickets/{phone}")
async def list_tickets(phone: str):
    """Get open tickets for a customer."""
    return await get_open_tickets(phone)


@router.post("/crm/knowledge/search")
async def kb_search(req: KBSearchRequest):
    """Search the CRM knowledge base."""
    return await search_knowledge_base(req.query)
