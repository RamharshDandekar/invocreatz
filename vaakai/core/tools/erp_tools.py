"""ERP LangChain Tools — Function definitions for LLM tool calling.

Allows the LLM to query ERP systems (SAP, Odoo) during conversation
for order status, inventory, shipment tracking, invoices, and returns.
"""

from __future__ import annotations

import structlog

from integrations.erp.sap import sap_client
from integrations.erp.odoo import odoo_client

logger = structlog.get_logger(__name__)

# ── OpenAI-compatible tool definitions ─────────────

ERP_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Check the status and details of a customer order. Provide order ID or reference number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID or reference number",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "track_shipment",
            "description": "Track a shipment or delivery by delivery/tracking ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delivery_id": {
                        "type": "string",
                        "description": "Delivery or tracking ID",
                    },
                },
                "required": ["delivery_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_invoice_status",
            "description": "Check payment/invoice status by invoice number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "string",
                        "description": "Invoice number or ID",
                    },
                },
                "required": ["invoice_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check product availability/stock levels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID, SKU, or material number",
                    },
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "initiate_return",
            "description": "Initiate a product return or refund for an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Original order ID",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for return",
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
]


# ── Tool execution handlers ───────────────────────

async def check_order_status(order_id: str) -> dict:
    """Check order status from SAP or Odoo."""
    # Try SAP
    result = await sap_client.get_order(order_id)
    if result:
        d = result.get("d", result)
        return {
            "source": "sap",
            "order_id": order_id,
            "status": d.get("OverallDeliveryStatus", "unknown"),
            "total_amount": d.get("TotalNetAmount"),
            "currency": d.get("TransactionCurrency"),
            "created": d.get("CreationDate"),
        }

    # Try Odoo
    result = await odoo_client.get_order(order_id)
    if result:
        state_labels = {
            "draft": "Quotation",
            "sent": "Quotation Sent",
            "sale": "Confirmed",
            "done": "Completed",
            "cancel": "Cancelled",
        }
        return {
            "source": "odoo",
            "order_id": result.get("name"),
            "status": state_labels.get(result.get("state"), result.get("state")),
            "total_amount": result.get("amount_total"),
            "date": result.get("date_order"),
        }

    return {"error": f"Order {order_id} not found"}


async def track_shipment(delivery_id: str) -> dict:
    """Track shipment from SAP."""
    result = await sap_client.get_shipment_tracking(delivery_id)
    if result:
        d = result.get("d", result)
        return {
            "source": "sap",
            "delivery_id": delivery_id,
            "status": d.get("DeliveryStatus", "unknown"),
            "ship_to": d.get("ShipToParty"),
            "planned_date": d.get("PlannedGoodsIssueDate"),
            "actual_date": d.get("ActualGoodsMovementDate"),
        }

    return {"error": f"Shipment {delivery_id} not found"}


async def check_invoice_status(invoice_id: str) -> dict:
    """Check invoice status from SAP or Odoo."""
    # Try SAP
    result = await sap_client.get_invoice(invoice_id)
    if result:
        d = result.get("d", result)
        return {
            "source": "sap",
            "invoice_id": invoice_id,
            "amount": d.get("TotalNetAmount"),
            "status": d.get("BillingDocumentStatus", "unknown"),
        }

    # Try Odoo
    result = await odoo_client.get_invoice(invoice_id)
    if result:
        return {
            "source": "odoo",
            "invoice_id": result.get("name"),
            "amount_total": result.get("amount_total"),
            "amount_due": result.get("amount_residual"),
            "payment_status": result.get("payment_state"),
            "due_date": result.get("invoice_date_due"),
        }

    return {"error": f"Invoice {invoice_id} not found"}


async def check_inventory(product_id: str) -> dict:
    """Check product stock from SAP or Odoo."""
    # Try SAP
    result = await sap_client.check_inventory(product_id)
    if result:
        d = result.get("d", result)
        return {
            "source": "sap",
            "product_id": product_id,
            "available_stock": d.get("MatlStkInQualityInspection"),
            "unit": d.get("MaterialBaseUnit"),
        }

    # Try Odoo
    try:
        pid = int(product_id)
        result = await odoo_client.check_product_stock(pid)
        if result:
            return {
                "source": "odoo",
                "product_name": result.get("name"),
                "available": result.get("qty_available"),
                "forecasted": result.get("virtual_available"),
                "unit": result.get("uom_id", [None, ""])[1] if isinstance(result.get("uom_id"), list) else "",
            }
    except (ValueError, TypeError):
        pass

    return {"error": f"Product {product_id} not found"}


async def initiate_return(order_id: str, reason: str) -> dict:
    """Initiate a return in SAP or Odoo."""
    # Try SAP
    return_id = await sap_client.create_return_order(
        original_order_id=order_id,
        reason=reason,
        items=[],
    )
    if return_id:
        return {
            "source": "sap",
            "return_order_id": return_id,
            "status": "created",
            "original_order": order_id,
        }

    # Try Odoo
    try:
        oid = int(order_id)
        return_id = await odoo_client.create_return(oid, reason)
        if return_id:
            return {
                "source": "odoo",
                "return_id": return_id,
                "status": "created",
                "original_order": order_id,
            }
    except (ValueError, TypeError):
        pass

    return {"error": f"Could not initiate return for order {order_id}"}


ERP_TOOL_HANDLERS = {
    "check_order_status": check_order_status,
    "track_shipment": track_shipment,
    "check_invoice_status": check_invoice_status,
    "check_inventory": check_inventory,
    "initiate_return": initiate_return,
}
