"""WhatsApp Integration — Meta Cloud API client.

Handles sending/receiving messages via the official
Meta WhatsApp Cloud API for omnichannel support.
Supports text, template, interactive, and media messages.
"""

from __future__ import annotations

import aiohttp
import structlog
from typing import Dict, Any, Optional, List

from config import settings

logger = structlog.get_logger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v18.0"


class WhatsAppClient:
    """Async Meta WhatsApp Cloud API client."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._phone_number_id: Optional[str] = None
        self._initialized = False

    async def initialize(self):
        """Initialize WhatsApp Cloud API client."""
        token = settings.whatsapp_token or None
        phone_id = settings.whatsapp_phone_number_id or None

        if not all([token, phone_id]):
            logger.warning("whatsapp_not_configured")
            return

        self._phone_number_id = phone_id
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )
        self._initialized = True
        logger.info("whatsapp_initialized")

    @property
    def _messages_url(self) -> str:
        return f"{GRAPH_API_BASE}/{self._phone_number_id}/messages"

    async def send_text(self, to: str, text: str) -> Optional[str]:
        """Send a text message to a WhatsApp number.

        Args:
            to: Recipient phone number with country code (e.g., '919876543210')
            text: Message text

        Returns:
            Message ID if successful
        """
        if not self._initialized:
            return None

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        try:
            async with self._session.post(self._messages_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    msg_id = data.get("messages", [{}])[0].get("id")
                    logger.info("whatsapp_text_sent", to=to, msg_id=msg_id)
                    return msg_id
                else:
                    error = await resp.text()
                    logger.error("whatsapp_send_failed", status=resp.status, error=error)
                    return None
        except Exception as e:
            logger.error("whatsapp_send_error", error=str(e))
            return None

    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict]] = None,
    ) -> Optional[str]:
        """Send a template message (for initiating conversations)."""
        if not self._initialized:
            return None

        template = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template["components"] = components

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template,
        }

        try:
            async with self._session.post(self._messages_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("messages", [{}])[0].get("id")
                return None
        except Exception as e:
            logger.error("whatsapp_template_error", error=str(e))
            return None

    async def send_interactive(
        self,
        to: str,
        body_text: str,
        buttons: Optional[List[Dict]] = None,
        list_sections: Optional[List[Dict]] = None,
        header: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> Optional[str]:
        """Send an interactive message (buttons or list)."""
        if not self._initialized:
            return None

        interactive: Dict[str, Any] = {
            "body": {"text": body_text},
        }

        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}

        if buttons:
            interactive["type"] = "button"
            interactive["action"] = {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn["id"], "title": btn["title"]},
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        elif list_sections:
            interactive["type"] = "list"
            interactive["action"] = {
                "button": "Options",
                "sections": list_sections,
            }

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": interactive,
        }

        try:
            async with self._session.post(self._messages_url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("messages", [{}])[0].get("id")
                return None
        except Exception as e:
            logger.error("whatsapp_interactive_error", error=str(e))
            return None

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark a received message as read."""
        if not self._initialized:
            return False

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        try:
            async with self._session.post(self._messages_url, json=payload) as resp:
                return resp.status == 200
        except Exception:
            return False

    @staticmethod
    def parse_webhook(body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse an incoming WhatsApp webhook payload.

        Returns normalized message dict or None.
        """
        try:
            entry = body.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            messages = value.get("messages", [])
            if not messages:
                return None

            msg = messages[0]
            contact = value.get("contacts", [{}])[0]

            parsed = {
                "message_id": msg.get("id"),
                "from": msg.get("from"),
                "timestamp": msg.get("timestamp"),
                "type": msg.get("type"),
                "contact_name": contact.get("profile", {}).get("name"),
            }

            if msg["type"] == "text":
                parsed["text"] = msg["text"]["body"]
            elif msg["type"] == "interactive":
                if "button_reply" in msg.get("interactive", {}):
                    parsed["text"] = msg["interactive"]["button_reply"]["title"]
                    parsed["button_id"] = msg["interactive"]["button_reply"]["id"]
                elif "list_reply" in msg.get("interactive", {}):
                    parsed["text"] = msg["interactive"]["list_reply"]["title"]
                    parsed["list_id"] = msg["interactive"]["list_reply"]["id"]
            elif msg["type"] == "audio":
                parsed["audio_id"] = msg["audio"]["id"]
            elif msg["type"] == "image":
                parsed["image_id"] = msg["image"]["id"]
                parsed["caption"] = msg["image"].get("caption")

            return parsed

        except (KeyError, IndexError) as e:
            logger.error("whatsapp_parse_error", error=str(e))
            return None

    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Download a media file from WhatsApp."""
        if not self._initialized:
            return None

        try:
            # First get the media URL
            async with self._session.get(
                f"{GRAPH_API_BASE}/{media_id}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    media_url = data.get("url")
                else:
                    return None

            # Then download the actual file
            async with self._session.get(media_url) as resp:
                if resp.status == 200:
                    return await resp.read()
                return None
        except Exception as e:
            logger.error("whatsapp_download_error", error=str(e))
            return None

    async def close(self):
        if self._session:
            await self._session.close()


whatsapp_client = WhatsAppClient()
