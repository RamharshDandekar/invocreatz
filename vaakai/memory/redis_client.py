"""Redis client for session memory and omnichannel context."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Optional, Dict, Any, List

import redis.asyncio as aioredis
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """Async Redis client for VaakAI session & omnichannel memory."""

    def __init__(self):
        self._pool: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initialize the Redis connection pool."""
        self._pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        await self._pool.ping()
        logger.info("redis_connected", url=settings.redis_url)

    async def disconnect(self):
        """Close the Redis connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("redis_disconnected")

    @property
    def pool(self) -> aioredis.Redis:
        if not self._pool:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._pool

    # ── Session Context (per active call) ──────────────

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def create_session(self, session_id: str, data: Dict[str, Any], ttl: int = 3600) -> None:
        """Create a new call session in Redis. TTL in seconds (default 1 hour)."""
        key = self._session_key(session_id)
        await self.pool.set(key, json.dumps(data), ex=ttl)
        logger.info("session_created", session_id=session_id)

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        data = await self.pool.get(self._session_key(session_id))
        return json.loads(data) if data else None

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Merge updates into existing session data."""
        key = self._session_key(session_id)
        existing = await self.pool.get(key)
        if existing:
            data = json.loads(existing)
            data.update(updates)
            ttl = await self.pool.ttl(key)
            await self.pool.set(key, json.dumps(data), ex=max(ttl, 300))
        else:
            await self.pool.set(key, json.dumps(updates), ex=3600)

    async def delete_session(self, session_id: str) -> None:
        """Delete session on call end."""
        await self.pool.delete(self._session_key(session_id))
        logger.info("session_deleted", session_id=session_id)

    # ── Omnichannel Context (per customer) ─────────────

    def _customer_key(self, phone: str) -> str:
        return f"customer:{phone}"

    async def set_customer_context(
        self, phone: str, data: Dict[str, Any], ttl: int = 86400
    ) -> None:
        """Store cross-channel customer context. Default TTL: 24 hours."""
        key = self._customer_key(phone)
        await self.pool.set(key, json.dumps(data), ex=ttl)

    async def get_customer_context(self, phone: str) -> Optional[Dict[str, Any]]:
        """Retrieve customer's cross-channel context."""
        data = await self.pool.get(self._customer_key(phone))
        return json.loads(data) if data else None

    async def append_customer_interaction(
        self, phone: str, interaction: Dict[str, Any]
    ) -> None:
        """Append an interaction to the customer's context history."""
        context = await self.get_customer_context(phone) or {"interactions": []}
        interactions = context.get("interactions", [])
        interactions.append(interaction)
        # Keep last 20 interactions
        context["interactions"] = interactions[-20:]
        await self.set_customer_context(phone, context)

    # ── ERP Cache ──────────────────────────────────────

    def _erp_cache_key(self, query_type: str, identifier: str) -> str:
        return f"erp_cache:{query_type}:{identifier}"

    async def cache_erp_response(
        self, query_type: str, identifier: str, data: Any, ttl: int = 300
    ) -> None:
        """Cache ERP query response. Default TTL: 5 minutes."""
        key = self._erp_cache_key(query_type, identifier)
        await self.pool.set(key, json.dumps(data), ex=ttl)

    async def get_erp_cache(self, query_type: str, identifier: str) -> Optional[Any]:
        """Retrieve cached ERP response."""
        data = await self.pool.get(self._erp_cache_key(query_type, identifier))
        return json.loads(data) if data else None

    # ── Conversation History (for LLM context) ────────

    def _conv_history_key(self, session_id: str) -> str:
        return f"conv:{session_id}"

    async def append_message(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None
    ) -> None:
        """Append a message to the conversation history."""
        message = {"role": role, "content": content}
        if metadata:
            message["metadata"] = metadata
        await self.pool.rpush(self._conv_history_key(session_id), json.dumps(message))

    async def get_conversation_history(
        self, session_id: str, last_n: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Retrieve conversation history for LLM context."""
        key = self._conv_history_key(session_id)
        if last_n:
            messages = await self.pool.lrange(key, -last_n, -1)
        else:
            messages = await self.pool.lrange(key, 0, -1)
        return [json.loads(m) for m in messages]

    # ── Health Check ───────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis connectivity and return stats."""
        try:
            await self.pool.ping()
            info = await self.pool.info("memory")
            return {
                "status": "healthy",
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Singleton instance
redis_client = RedisClient()
