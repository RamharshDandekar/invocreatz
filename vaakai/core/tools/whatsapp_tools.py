"""WhatsApp LangChain Tools — Function definitions for LLM tool calling.

Allows the LLM to send WhatsApp messages to customers during
conversations (e.g., sending order confirmations, links, summaries).
"""

from __future__ import annotations

import structlog

from integrations.whatsapp.meta_cloud import whatsapp_client

logger = structlog.get_logger(__name__)

WHATSAPP_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_message",
            "description": "Send a WhatsApp message to the customer. Use for sending order details, ticket numbers, confirmations, or follow-up information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number with country code (e.g., 919876543210)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Message text to send",
                    },
                },
                "required": ["phone", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp_options",
            "description": "Send an interactive WhatsApp message with buttons for quick replies. Max 3 buttons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number",
                    },
                    "message": {
                        "type": "string",
                        "description": "Message body text",
                    },
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of option labels (max 3)",
                    },
                },
                "required": ["phone", "message", "options"],
            },
        },
    },
]


async def send_whatsapp_message(phone: str, message: str) -> dict:
    """Send a text message via WhatsApp."""
    msg_id = await whatsapp_client.send_text(phone, message)
    if msg_id:
        return {
            "status": "sent",
            "message_id": msg_id,
            "to": phone,
        }
    return {"error": "Failed to send WhatsApp message"}


async def send_whatsapp_options(
    phone: str, message: str, options: list
) -> dict:
    """Send interactive options via WhatsApp."""
    buttons = [
        {"id": f"opt_{i}", "title": opt[:20]}
        for i, opt in enumerate(options[:3])
    ]

    msg_id = await whatsapp_client.send_interactive(
        to=phone,
        body_text=message,
        buttons=buttons,
    )

    if msg_id:
        return {
            "status": "sent",
            "message_id": msg_id,
            "options_sent": [b["title"] for b in buttons],
        }
    return {"error": "Failed to send WhatsApp interactive message"}


WHATSAPP_TOOL_HANDLERS = {
    "send_whatsapp_message": send_whatsapp_message,
    "send_whatsapp_options": send_whatsapp_options,
}
