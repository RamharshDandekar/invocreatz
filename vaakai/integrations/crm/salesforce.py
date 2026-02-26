"""Salesforce CRM Integration — REST API client.

Handles:
- Customer lookup by phone / email
- Case (ticket) creation and updates
- Contact creation
- Knowledge base search
"""

from __future__ import annotations

import aiohttp
import structlog
from typing import Dict, Any, Optional, List

from config import settings

logger = structlog.get_logger(__name__)

SF_API_VERSION = "v59.0"


class SalesforceClient:
    """Async Salesforce REST API client with OAuth 2.0 auth."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._instance_url: Optional[str] = None
        self._initialized = False

    async def initialize(self):
        """Authenticate with Salesforce via OAuth 2.0 client credentials."""
        # Use Salesforce-specific fields, fall back to generic CRM fields
        sf_url = settings.salesforce_url or settings.crm_api_url or None
        sf_client_id = settings.salesforce_client_id or settings.crm_api_key or None
        sf_client_secret = settings.salesforce_client_secret or None

        if not sf_url or not sf_client_id:
            logger.warning("salesforce_not_configured", has_url=bool(sf_url), has_client_id=bool(sf_client_id))
            return

        self._instance_url = sf_url.rstrip("/")
        self._session = aiohttp.ClientSession()

        # If we have both client_id and client_secret, use OAuth flow
        if sf_client_secret:
            try:
                async with self._session.post(
                    f"{self._instance_url}/services/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": sf_client_id,
                        "client_secret": sf_client_secret,
                    },
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._access_token = data["access_token"]
                        self._instance_url = data.get("instance_url", self._instance_url)
                        self._initialized = True
                        logger.info("salesforce_authenticated", mode="oauth")
                    else:
                        error = await resp.text()
                        logger.error("salesforce_auth_failed", status=resp.status, error=error)
            except Exception as e:
                logger.error("salesforce_init_error", error=str(e))
        else:
            # Use client_id (CRM_API_KEY) directly as session token / API key
            self._access_token = sf_client_id
            self._initialized = True
            logger.info("salesforce_authenticated", mode="api_key")

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    @property
    def _base_url(self) -> str:
        return f"{self._instance_url}/services/data/{SF_API_VERSION}"

    async def query(self, soql: str) -> List[Dict[str, Any]]:
        """Execute a SOQL query."""
        if not self._initialized:
            return []

        try:
            import urllib.parse
            encoded = urllib.parse.quote(soql)
            async with self._session.get(
                f"{self._base_url}/query/?q={encoded}",
                headers=self._headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("records", [])
                else:
                    logger.error("sf_query_failed", status=resp.status)
                    return []
        except Exception as e:
            logger.error("sf_query_error", error=str(e))
            return []

    async def lookup_customer(self, phone: str) -> Optional[Dict[str, Any]]:
        """Look up a Salesforce Contact by phone number."""
        records = await self.query(
            f"SELECT Id, Name, Email, Phone, AccountId, "
            f"MailingCity, MailingState "
            f"FROM Contact WHERE Phone = '{phone}' LIMIT 1"
        )
        return records[0] if records else None

    async def create_case(
        self,
        contact_id: str,
        subject: str,
        description: str,
        priority: str = "Medium",
        origin: str = "VaakAI",
        status: str = "New",
    ) -> Optional[str]:
        """Create a Salesforce Case and return its ID."""
        if not self._initialized:
            return None

        payload = {
            "ContactId": contact_id,
            "Subject": subject,
            "Description": description,
            "Priority": priority,
            "Origin": origin,
            "Status": status,
        }

        try:
            async with self._session.post(
                f"{self._base_url}/sobjects/Case/",
                headers=self._headers,
                json=payload,
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    logger.info("sf_case_created", case_id=data.get("id"))
                    return data.get("id")
                else:
                    error = await resp.text()
                    logger.error("sf_case_create_failed", status=resp.status, error=error)
                    return None
        except Exception as e:
            logger.error("sf_case_create_error", error=str(e))
            return None

    async def update_case(self, case_id: str, updates: Dict[str, Any]) -> bool:
        """Update a Salesforce Case."""
        if not self._initialized:
            return False

        try:
            async with self._session.patch(
                f"{self._base_url}/sobjects/Case/{case_id}",
                headers=self._headers,
                json=updates,
            ) as resp:
                return resp.status == 204
        except Exception as e:
            logger.error("sf_case_update_error", error=str(e))
            return False

    async def get_open_cases(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get open cases for a contact."""
        return await self.query(
            f"SELECT Id, Subject, Status, Priority, CreatedDate "
            f"FROM Case WHERE ContactId = '{contact_id}' "
            f"AND IsClosed = false ORDER BY CreatedDate DESC"
        )

    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search Salesforce Knowledge articles."""
        if not self._initialized:
            return []

        try:
            import urllib.parse
            encoded = urllib.parse.quote(query)
            async with self._session.get(
                f"{self._base_url}/search/?q=FIND+'{encoded}'+IN+ALL+FIELDS+"
                f"RETURNING+KnowledgeArticleVersion(Title,Summary,UrlName)+LIMIT+{limit}",
                headers=self._headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("searchRecords", [])
                return []
        except Exception as e:
            logger.error("sf_knowledge_search_error", error=str(e))
            return []

    async def close(self):
        if self._session:
            await self._session.close()


salesforce_client = SalesforceClient()
