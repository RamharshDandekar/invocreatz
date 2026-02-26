"""CRM LangChain Tools — Function definitions for LLM tool calling.

These tools allow the LLM to interact with CRM systems (Salesforce,
Zoho, Freshdesk) during a conversation via OpenAI function calling.
"""

from __future__ import annotations

from typing import Optional

import structlog

from integrations.crm.salesforce import salesforce_client
from integrations.crm.zoho import zoho_client
from integrations.crm.freshdesk import freshdesk_client

logger = structlog.get_logger(__name__)

# ── OpenAI-compatible tool definitions ─────────────

CRM_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_customer",
            "description": "Look up customer information by phone number in CRM. Returns name, email, account details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number (e.g., +919876543210)",
                    },
                },
                "required": ["phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a customer support ticket in the CRM system. Use when customer has an issue that needs tracking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Brief ticket subject/title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High", "Urgent"],
                        "description": "Ticket priority level",
                    },
                },
                "required": ["phone", "subject", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_open_tickets",
            "description": "Get list of open/pending support tickets for a customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number",
                    },
                },
                "required": ["phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the knowledge base for solutions to customer problems. Use before creating tickets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing the customer's issue",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# ── Tool execution handlers ───────────────────────

async def lookup_customer(phone: str) -> dict:
    """Execute customer lookup across available CRMs."""
    # Try Salesforce first, then Zoho, then Freshdesk
    result = await salesforce_client.lookup_customer(phone)
    if result:
        return {
            "source": "salesforce",
            "name": result.get("Name"),
            "email": result.get("Email"),
            "phone": result.get("Phone"),
            "account_id": result.get("AccountId"),
            "city": result.get("MailingCity"),
        }

    result = await zoho_client.search_contacts(phone)
    if result:
        return {
            "source": "zoho",
            "name": result.get("Full_Name"),
            "email": result.get("Email"),
            "phone": result.get("Phone"),
        }

    result = await freshdesk_client.lookup_contact(phone)
    if result:
        return {
            "source": "freshdesk",
            "name": result.get("name"),
            "email": result.get("email"),
            "phone": result.get("phone"),
        }

    return {"error": "Customer not found in any CRM"}


async def create_support_ticket(
    phone: str, subject: str, description: str, priority: str = "Medium"
) -> dict:
    """Create a support ticket in the first available CRM."""
    # Try Salesforce
    sf_customer = await salesforce_client.lookup_customer(phone)
    if sf_customer:
        case_id = await salesforce_client.create_case(
            contact_id=sf_customer["Id"],
            subject=subject,
            description=description,
            priority=priority,
        )
        if case_id:
            return {"source": "salesforce", "ticket_id": case_id, "status": "created"}

    # Try Freshdesk
    fd_customer = await freshdesk_client.lookup_contact(phone)
    if fd_customer:
        priority_map = {"Low": 1, "Medium": 2, "High": 3, "Urgent": 4}
        ticket_id = await freshdesk_client.create_ticket(
            requester_id=fd_customer["id"],
            subject=subject,
            description=description,
            priority=priority_map.get(priority, 2),
        )
        if ticket_id:
            return {"source": "freshdesk", "ticket_id": ticket_id, "status": "created"}

    # Try Zoho
    zoho_customer = await zoho_client.search_contacts(phone)
    if zoho_customer:
        ticket_id = await zoho_client.create_ticket(
            contact_id=zoho_customer.get("id", ""),
            subject=subject,
            description=description,
            priority=priority,
        )
        if ticket_id:
            return {"source": "zoho", "ticket_id": ticket_id, "status": "created"}

    return {"error": "Could not create ticket — no CRM available"}


async def get_open_tickets(phone: str) -> dict:
    """Get open tickets from available CRMs."""
    sf_customer = await salesforce_client.lookup_customer(phone)
    if sf_customer:
        cases = await salesforce_client.get_open_cases(sf_customer["Id"])
        if cases:
            return {
                "source": "salesforce",
                "tickets": [
                    {
                        "id": c.get("Id"),
                        "subject": c.get("Subject"),
                        "status": c.get("Status"),
                        "priority": c.get("Priority"),
                    }
                    for c in cases
                ],
            }

    return {"tickets": [], "message": "No open tickets found"}


async def search_knowledge_base(query: str) -> dict:
    """Search knowledge base across CRMs."""
    # Try Salesforce Knowledge
    results = await salesforce_client.search_knowledge(query)
    if results:
        return {
            "source": "salesforce",
            "articles": [
                {"title": r.get("Title"), "summary": r.get("Summary")}
                for r in results[:3]
            ],
        }

    # Try Freshdesk Solutions
    results = await freshdesk_client.search_solutions(query)
    if results:
        return {
            "source": "freshdesk",
            "articles": [
                {"title": r.get("title"), "description": r.get("description_text", "")[:200]}
                for r in results[:3]
            ],
        }

    return {"articles": [], "message": "No knowledge base articles found"}


# Map function names to handlers
CRM_TOOL_HANDLERS = {
    "lookup_customer": lookup_customer,
    "create_support_ticket": create_support_ticket,
    "get_open_tickets": get_open_tickets,
    "search_knowledge_base": search_knowledge_base,
}
