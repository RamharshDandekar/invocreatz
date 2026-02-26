"""Odoo ERP Integration — JSON-RPC API client.

Handles product lookup, order management, invoice queries,
and inventory checks via Odoo's JSON-RPC API.
Results cached in Redis for 5 minutes.
"""

from __future__ import annotations

import aiohttp
import json
import structlog
from typing import Dict, Any, Optional, List

from config import settings
from memory.redis_client import redis_client

logger = structlog.get_logger(__name__)

ERP_CACHE_TTL = 300


class OdooClient:
    """Async Odoo JSON-RPC client with Redis caching."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._url: Optional[str] = None
        self._db: Optional[str] = None
        self._uid: Optional[int] = None
        self._password: Optional[str] = None
        self._initialized = False
        self._request_id = 0

    async def initialize(self):
        """Authenticate with Odoo via JSON-RPC."""
        odoo_url = getattr(settings, "ODOO_URL", None)
        odoo_db = getattr(settings, "ODOO_DB", None)
        odoo_user = getattr(settings, "ODOO_USERNAME", None)
        odoo_pass = getattr(settings, "ODOO_PASSWORD", None)

        if not all([odoo_url, odoo_db, odoo_user, odoo_pass]):
            logger.warning("odoo_not_configured")
            return

        self._url = odoo_url.rstrip("/")
        self._db = odoo_db
        self._password = odoo_pass
        self._session = aiohttp.ClientSession()

        try:
            # Authenticate
            result = await self._jsonrpc(
                f"{self._url}/jsonrpc",
                "call",
                {
                    "service": "common",
                    "method": "authenticate",
                    "args": [odoo_db, odoo_user, odoo_pass, {}],
                },
            )
            if result and isinstance(result, int):
                self._uid = result
                self._initialized = True
                logger.info("odoo_authenticated", uid=self._uid)
            else:
                logger.error("odoo_auth_failed")
        except Exception as e:
            logger.error("odoo_init_error", error=str(e))

    async def _jsonrpc(self, url: str, method: str, params: Dict) -> Any:
        """Execute a JSON-RPC call."""
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._request_id,
        }

        async with self._session.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "error" in data:
                    logger.error("odoo_rpc_error", error=data["error"])
                    return None
                return data.get("result")
            return None

    async def _execute(
        self, model: str, method: str, args: List, kwargs: Optional[Dict] = None
    ) -> Any:
        """Execute an Odoo model method."""
        if not self._initialized:
            return None

        return await self._jsonrpc(
            f"{self._url}/jsonrpc",
            "call",
            {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self._db,
                    self._uid,
                    self._password,
                    model,
                    method,
                    args,
                    kwargs or {},
                ],
            },
        )

    async def search_customer(self, phone: str) -> Optional[Dict[str, Any]]:
        """Find a customer (res.partner) by phone."""
        cache_key = f"odoo:customer:{phone}"
        cached = await redis_client.get_erp_cache(cache_key)
        if cached:
            return cached

        ids = await self._execute(
            "res.partner",
            "search",
            [[["phone", "=", phone]]],
            {"limit": 1},
        )

        if ids:
            records = await self._execute(
                "res.partner",
                "read",
                [ids],
                {"fields": ["name", "email", "phone", "city", "country_id"]},
            )
            if records:
                await redis_client.set_erp_cache(cache_key, records[0], ERP_CACHE_TTL)
                return records[0]

        return None

    async def get_order(self, order_name: str) -> Optional[Dict[str, Any]]:
        """Get a sale order by name/reference."""
        cache_key = f"odoo:order:{order_name}"
        cached = await redis_client.get_erp_cache(cache_key)
        if cached:
            return cached

        ids = await self._execute(
            "sale.order",
            "search",
            [[["name", "=", order_name]]],
            {"limit": 1},
        )

        if ids:
            records = await self._execute(
                "sale.order",
                "read",
                [ids],
                {
                    "fields": [
                        "name", "state", "amount_total", "date_order",
                        "partner_id", "order_line",
                    ]
                },
            )
            if records:
                await redis_client.set_erp_cache(cache_key, records[0], ERP_CACHE_TTL)
                return records[0]

        return None

    async def get_customer_orders(
        self, partner_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent orders for a customer."""
        ids = await self._execute(
            "sale.order",
            "search",
            [[["partner_id", "=", partner_id]]],
            {"limit": limit, "order": "date_order DESC"},
        )

        if ids:
            return await self._execute(
                "sale.order",
                "read",
                [ids],
                {
                    "fields": [
                        "name", "state", "amount_total",
                        "date_order", "delivery_status",
                    ]
                },
            ) or []

        return []

    async def check_product_stock(
        self, product_id: int, warehouse_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Check product stock availability."""
        cache_key = f"odoo:stock:{product_id}:{warehouse_id or 'all'}"
        cached = await redis_client.get_erp_cache(cache_key)
        if cached:
            return cached

        records = await self._execute(
            "product.product",
            "read",
            [[product_id]],
            {"fields": ["name", "qty_available", "virtual_available", "uom_id"]},
        )

        if records:
            await redis_client.set_erp_cache(cache_key, records[0], ERP_CACHE_TTL)
            return records[0]

        return None

    async def get_invoice(self, invoice_name: str) -> Optional[Dict[str, Any]]:
        """Get an invoice/bill by number."""
        ids = await self._execute(
            "account.move",
            "search",
            [[["name", "=", invoice_name], ["move_type", "=", "out_invoice"]]],
            {"limit": 1},
        )

        if ids:
            records = await self._execute(
                "account.move",
                "read",
                [ids],
                {
                    "fields": [
                        "name", "state", "amount_total", "amount_residual",
                        "invoice_date", "invoice_date_due", "payment_state",
                    ]
                },
            )
            return records[0] if records else None

        return None

    async def create_return(
        self, order_id: int, reason: str
    ) -> Optional[int]:
        """Create a return picking for an order."""
        if not self._initialized:
            return None

        try:
            # Find delivery picking for the order
            pickings = await self._execute(
                "stock.picking",
                "search",
                [[
                    ["origin", "like", f"SO{order_id:05d}"],
                    ["picking_type_code", "=", "outgoing"],
                ]],
                {"limit": 1},
            )

            if not pickings:
                return None

            # Create return wizard and confirm
            return_wizard_id = await self._execute(
                "stock.return.picking",
                "create",
                [{"picking_id": pickings[0]}],
            )

            if return_wizard_id:
                result = await self._execute(
                    "stock.return.picking",
                    "create_returns",
                    [[return_wizard_id]],
                )
                logger.info("odoo_return_created", result=result)
                return return_wizard_id

            return None
        except Exception as e:
            logger.error("odoo_return_error", error=str(e))
            return None

    async def close(self):
        if self._session:
            await self._session.close()


odoo_client = OdooClient()
