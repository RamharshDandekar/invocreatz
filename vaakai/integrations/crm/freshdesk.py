"""Freshdesk CRM Integration — REST API v2 client.

Handles ticket creation, contact lookup, and knowledge base queries
via Freshdesk REST API.
"""

from __future__ import annotations

import aiohttp
import base64
import structlog
from typing import Dict, Any, Optional, List

from config import settings

logger = structlog.get_logger(__name__)


class FreshdeskClient:
    """Async Freshdesk REST API client."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url: Optional[str] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Freshdesk client with API key auth."""
        api_key = settings.freshdesk_api_key or None
        domain = settings.freshdesk_domain or None

        if not all([api_key, domain]):
            logger.warning("freshdesk_not_configured")
            return

        self._base_url = f"https://{domain}.freshdesk.com/api/v2"

        # Freshdesk uses API key as basic auth password
        auth_str = base64.b64encode(f"{api_key}:X".encode()).decode()
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Basic {auth_str}",
                "Content-Type": "application/json",
            }
        )
        self._initialized = True
        logger.info("freshdesk_initialized")

    async def lookup_contact(self, phone: str) -> Optional[Dict[str, Any]]:
        """Search for a Freshdesk contact by phone."""
        if not self._initialized:
            return None

        try:
            async with self._session.get(
                f"{self._base_url}/contacts",
                params={"phone": phone},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0] if data else None
                return None
        except Exception as e:
            logger.error("freshdesk_lookup_error", error=str(e))
            return None

    async def create_contact(
        self, name: str, phone: str, email: Optional[str] = None
    ) -> Optional[int]:
        """Create a Freshdesk contact."""
        if not self._initialized:
            return None

        payload = {"name": name, "phone": phone}
        if email:
            payload["email"] = email

        try:
            async with self._session.post(
                f"{self._base_url}/contacts",
                json=payload,
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    return data.get("id")
                return None
        except Exception as e:
            logger.error("freshdesk_create_contact_error", error=str(e))
            return None

    async def create_ticket(
        self,
        requester_id: int,
        subject: str,
        description: str,
        priority: int = 2,  # 1=Low,2=Medium,3=High,4=Urgent
        status: int = 2,    # 2=Open,3=Pending,4=Resolved,5=Closed
        source: int = 3,    # 3=Phone
        tags: Optional[List[str]] = None,
    ) -> Optional[int]:
        """Create a Freshdesk ticket."""
        if not self._initialized:
            return None

        payload = {
            "requester_id": requester_id,
            "subject": subject,
            "description": description,
            "priority": priority,
            "status": status,
            "source": source,
            "tags": tags or ["vaakai", "ai-generated"],
        }

        try:
            async with self._session.post(
                f"{self._base_url}/tickets",
                json=payload,
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    ticket_id = data.get("id")
                    logger.info("freshdesk_ticket_created", ticket_id=ticket_id)
                    return ticket_id
                else:
                    error = await resp.text()
                    logger.error("freshdesk_ticket_error", status=resp.status, error=error)
                    return None
        except Exception as e:
            logger.error("freshdesk_ticket_create_error", error=str(e))
            return None

    async def update_ticket(self, ticket_id: int, updates: Dict[str, Any]) -> bool:
        """Update a Freshdesk ticket."""
        if not self._initialized:
            return False

        try:
            async with self._session.put(
                f"{self._base_url}/tickets/{ticket_id}",
                json=updates,
            ) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error("freshdesk_ticket_update_error", error=str(e))
            return False

    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket details."""
        if not self._initialized:
            return None

        try:
            async with self._session.get(
                f"{self._base_url}/tickets/{ticket_id}",
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception as e:
            logger.error("freshdesk_get_ticket_error", error=str(e))
            return None

    async def search_solutions(self, query: str) -> List[Dict[str, Any]]:
        """Search Freshdesk solution articles (knowledge base)."""
        if not self._initialized:
            return []

        try:
            async with self._session.get(
                f"{self._base_url}/search/solutions",
                params={"term": query},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("results", [])
                return []
        except Exception as e:
            logger.error("freshdesk_search_error", error=str(e))
            return []

    async def close(self):
        if self._session:
            await self._session.close()


freshdesk_client = FreshdeskClient()
