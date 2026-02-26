"""Zoho CRM Integration — REST API client.

Handles customer lookup, ticket/deal creation, and module queries
via Zoho CRM REST API v2.1.
"""

from __future__ import annotations

import aiohttp
import structlog
from typing import Dict, Any, Optional, List

from config import settings

logger = structlog.get_logger(__name__)

ZOHO_API_BASE = "https://www.zohoapis.com/crm/v2.1"


class ZohoClient:
    """Async Zoho CRM REST API client."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._initialized = False

    async def initialize(self):
        """Authenticate with Zoho via OAuth 2.0 refresh token flow."""
        refresh_token = settings.zoho_refresh_token or None
        client_id = settings.zoho_client_id or None
        client_secret = settings.zoho_client_secret or None

        if not all([refresh_token, client_id, client_secret]):
            logger.warning("zoho_not_configured")
            return

        self._session = aiohttp.ClientSession()

        try:
            async with self._session.post(
                "https://accounts.zoho.com/oauth/v2/token",
                params={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._access_token = data.get("access_token")
                    self._initialized = True
                    logger.info("zoho_authenticated")
                else:
                    logger.error("zoho_auth_failed", status=resp.status)
        except Exception as e:
            logger.error("zoho_init_error", error=str(e))

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Zoho-oauthtoken {self._access_token}",
            "Content-Type": "application/json",
        }

    async def search_contacts(self, phone: str) -> Optional[Dict[str, Any]]:
        """Search for a Zoho contact by phone number."""
        if not self._initialized:
            return None

        try:
            async with self._session.get(
                f"{ZOHO_API_BASE}/Contacts/search",
                headers=self._headers,
                params={"phone": phone},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    records = data.get("data", [])
                    return records[0] if records else None
                return None
        except Exception as e:
            logger.error("zoho_search_error", error=str(e))
            return None

    async def create_ticket(
        self,
        contact_id: str,
        subject: str,
        description: str,
        priority: str = "Medium",
    ) -> Optional[str]:
        """Create a Zoho Desk ticket."""
        if not self._initialized:
            return None

        try:
            # Zoho Desk API (different from CRM)
            async with self._session.post(
                "https://desk.zoho.com/api/v1/tickets",
                headers=self._headers,
                json={
                    "contactId": contact_id,
                    "subject": subject,
                    "description": description,
                    "priority": priority,
                    "channel": "VaakAI",
                    "status": "Open",
                },
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    ticket_id = data.get("id")
                    logger.info("zoho_ticket_created", ticket_id=ticket_id)
                    return ticket_id
                return None
        except Exception as e:
            logger.error("zoho_ticket_error", error=str(e))
            return None

    async def get_deals(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get deals associated with a contact."""
        if not self._initialized:
            return []

        try:
            async with self._session.get(
                f"{ZOHO_API_BASE}/Contacts/{contact_id}/Deals",
                headers=self._headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [])
                return []
        except Exception as e:
            logger.error("zoho_deals_error", error=str(e))
            return []

    async def close(self):
        if self._session:
            await self._session.close()


zoho_client = ZohoClient()
