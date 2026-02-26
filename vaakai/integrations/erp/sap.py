"""SAP ERP Integration — RFC/OData API client.

Handles order lookup, inventory queries, invoice status, and
shipment tracking via SAP Business One / S/4HANA OData API.
Results are cached in Redis for 5 minutes.
"""

from __future__ import annotations

import aiohttp
import structlog
from typing import Dict, Any, Optional, List

from config import settings
from memory.redis_client import redis_client

logger = structlog.get_logger(__name__)

ERP_CACHE_TTL = 300  # 5 minutes


class SAPClient:
    """Async SAP OData API client with Redis caching."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url: Optional[str] = None
        self._initialized = False

    async def initialize(self):
        """Initialize SAP client with basic auth."""
        sap_url = getattr(settings, "SAP_URL", None)
        sap_user = getattr(settings, "SAP_USERNAME", None)
        sap_pass = getattr(settings, "SAP_PASSWORD", None)

        if not all([sap_url, sap_user, sap_pass]):
            logger.warning("sap_not_configured")
            return

        self._base_url = sap_url.rstrip("/")
        auth = aiohttp.BasicAuth(sap_user, sap_pass)
        self._session = aiohttp.ClientSession(
            auth=auth,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self._initialized = True
        logger.info("sap_initialized")

    async def _get(self, path: str, cache_key: Optional[str] = None) -> Optional[Dict]:
        """GET with optional Redis caching."""
        if not self._initialized:
            return None

        # Check cache
        if cache_key:
            cached = await redis_client.get_erp_cache(cache_key)
            if cached:
                return cached

        try:
            async with self._session.get(f"{self._base_url}{path}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if cache_key:
                        await redis_client.set_erp_cache(cache_key, data, ERP_CACHE_TTL)
                    return data
                else:
                    logger.error("sap_get_failed", path=path, status=resp.status)
                    return None
        except Exception as e:
            logger.error("sap_get_error", path=path, error=str(e))
            return None

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details from SAP."""
        return await self._get(
            f"/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{order_id}')",
            cache_key=f"sap:order:{order_id}",
        )

    async def get_order_status(self, order_id: str) -> Optional[str]:
        """Get order delivery status."""
        order = await self.get_order(order_id)
        if order:
            d = order.get("d", order)
            return d.get("OverallDeliveryStatus", d.get("DeliveryStatus", "unknown"))
        return None

    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice details from SAP."""
        return await self._get(
            f"/sap/opu/odata/sap/API_BILLING_DOCUMENT_SRV"
            f"/A_BillingDocument('{invoice_id}')",
            cache_key=f"sap:invoice:{invoice_id}",
        )

    async def check_inventory(
        self, material_id: str, plant: str = "1000"
    ) -> Optional[Dict[str, Any]]:
        """Check material inventory at a plant."""
        return await self._get(
            f"/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV"
            f"/A_MatlStkInAcctMod(Material='{material_id}',Plant='{plant}')",
            cache_key=f"sap:inventory:{material_id}:{plant}",
        )

    async def get_shipment_tracking(
        self, delivery_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get shipment/delivery tracking info."""
        return await self._get(
            f"/sap/opu/odata/sap/API_OUTBOUND_DELIVERY_SRV"
            f"/A_OutbDeliveryHeader('{delivery_id}')",
            cache_key=f"sap:shipment:{delivery_id}",
        )

    async def get_customer_orders(
        self, customer_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent orders for a customer."""
        result = await self._get(
            f"/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder"
            f"?$filter=SoldToParty eq '{customer_id}'"
            f"&$top={limit}&$orderby=CreationDate desc",
            cache_key=f"sap:customer_orders:{customer_id}",
        )
        if result and "d" in result:
            return result["d"].get("results", [])
        return []

    async def create_return_order(
        self, original_order_id: str, reason: str, items: List[Dict]
    ) -> Optional[str]:
        """Create a return/refund order in SAP."""
        if not self._initialized:
            return None

        payload = {
            "d": {
                "SalesOrderType": "RE",
                "ReferenceDocument": original_order_id,
                "ReturnReason": reason,
                "to_Item": {"results": items},
            }
        }

        try:
            async with self._session.post(
                f"{self._base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder",
                json=payload,
            ) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return data.get("d", {}).get("SalesOrder")
                else:
                    logger.error("sap_return_failed", status=resp.status)
                    return None
        except Exception as e:
            logger.error("sap_return_error", error=str(e))
            return None

    async def close(self):
        if self._session:
            await self._session.close()


sap_client = SAPClient()
