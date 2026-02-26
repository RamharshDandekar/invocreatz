"""Consent Manager — DPDPA-compliant consent capture and tracking.

Handles explicit consent flows required under India's
Digital Personal Data Protection Act (DPDPA) 2023.

Consent is captured for:
- Call recording
- Data processing
- Analytics usage
- Third-party sharing (CRM/ERP)
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import structlog

from memory.redis_client import redis_client

logger = structlog.get_logger(__name__)


class ConsentPurpose(str, Enum):
    """DPDPA consent purposes."""
    CALL_RECORDING = "call_recording"
    DATA_PROCESSING = "data_processing"
    ANALYTICS = "analytics"
    THIRD_PARTY_SHARING = "third_party_sharing"
    MARKETING = "marketing"


class ConsentStatus(str, Enum):
    """Consent status."""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"


@dataclass
class ConsentRecord:
    """Individual consent record."""
    id: str
    customer_phone: str
    purpose: ConsentPurpose
    status: ConsentStatus
    granted_at: Optional[float] = None
    withdrawn_at: Optional[float] = None
    expires_at: Optional[float] = None
    channel: str = "voice"
    metadata: Dict[str, Any] = field(default_factory=dict)


# Consent prompts in multiple languages
CONSENT_PROMPTS = {
    "en": {
        ConsentPurpose.CALL_RECORDING: (
            "This call may be recorded for quality assurance and training purposes. "
            "Do you consent to the recording? Say yes or no."
        ),
        ConsentPurpose.DATA_PROCESSING: (
            "We process your data to serve you better as per our privacy policy "
            "under the Digital Personal Data Protection Act. "
            "Do you consent to data processing? Say yes or no."
        ),
    },
    "hi": {
        ConsentPurpose.CALL_RECORDING: (
            "Yeh call quality aur training ke liye record ki ja sakti hai. "
            "Kya aap recording ki anumati dete hain? Haan ya naa kahiye."
        ),
        ConsentPurpose.DATA_PROCESSING: (
            "Hum aapki data ko behtar seva ke liye process karte hain, "
            "Digital Personal Data Protection Act ke tahat. "
            "Kya aap data processing ki anumati dete hain? Haan ya naa kahiye."
        ),
    },
    "bn": {
        ConsentPurpose.CALL_RECORDING: (
            "Ei call quality o training er jonno record kora hote pare. "
            "Apni ki recording er onumoti den? Hyan ba na bolun."
        ),
        ConsentPurpose.DATA_PROCESSING: (
            "Amra apnar data better service er jonno process kori. "
            "Apni ki data processing er onumoti den?"
        ),
    },
}

# Affirmative patterns per language (for voice-based consent capture)
AFFIRMATIVE_PATTERNS = {
    "en": ["yes", "yeah", "yep", "sure", "okay", "ok", "i agree", "i consent", "go ahead"],
    "hi": ["haan", "ha", "haa", "theek hai", "sahi", "manzoor", "agree"],
    "bn": ["hyan", "ha", "thik ache", "raji"],
    "ta": ["aam", "sari", "ok"],
    "te": ["avunu", "sare", "ok"],
}

NEGATIVE_PATTERNS = {
    "en": ["no", "nope", "nah", "i don't", "i do not", "decline", "refuse", "deny"],
    "hi": ["nahi", "naa", "na", "mana", "nahi chahiye"],
    "bn": ["na", "nai"],
    "ta": ["illai", "venda"],
    "te": ["ledu", "vaddu"],
}

# Default consent validity: 1 year
DEFAULT_CONSENT_TTL = 365 * 24 * 3600


class ConsentManager:
    """Manages DPDPA-compliant consent flows.

    Stores consent records in Redis with expiry and provides
    methods for capture, verification, and withdrawal.
    """

    def __init__(self):
        self._pending_consents: Dict[str, List[ConsentPurpose]] = {}

    def get_consent_prompt(
        self, purpose: ConsentPurpose, language: str = "en"
    ) -> str:
        """Get the consent prompt in the specified language."""
        lang_prompts = CONSENT_PROMPTS.get(language, CONSENT_PROMPTS["en"])
        return lang_prompts.get(purpose, CONSENT_PROMPTS["en"].get(purpose, ""))

    def parse_consent_response(self, text: str, language: str = "en") -> Optional[bool]:
        """Parse a user's response to determine consent status.

        Returns:
            True  — user consented
            False — user declined
            None  — unable to determine
        """
        text_lower = text.lower().strip()

        affirmatives = AFFIRMATIVE_PATTERNS.get(language, AFFIRMATIVE_PATTERNS["en"])
        negatives = NEGATIVE_PATTERNS.get(language, NEGATIVE_PATTERNS["en"])

        for word in affirmatives:
            if word in text_lower:
                return True

        for word in negatives:
            if word in text_lower:
                return False

        return None

    async def request_consent(
        self,
        session_id: str,
        phone: str,
        purposes: List[ConsentPurpose],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Initiate a consent request for the given purposes.

        Returns prompts to be spoken to the user.
        The actual consent capture happens via capture_consent().
        """
        self._pending_consents[session_id] = purposes

        prompts = []
        for purpose in purposes:
            prompt = self.get_consent_prompt(purpose, language)
            if prompt:
                prompts.append({"purpose": purpose.value, "prompt": prompt})

        logger.info(
            "consent_requested",
            session_id=session_id,
            phone=phone,
            purposes=[p.value for p in purposes],
        )

        return {
            "session_id": session_id,
            "status": "pending",
            "prompts": prompts,
        }

    async def capture_consent(
        self,
        session_id: str,
        phone: str,
        purpose: ConsentPurpose,
        user_response: str,
        language: str = "en",
        channel: str = "voice",
    ) -> ConsentRecord:
        """Capture the user's consent response.

        Stores the consent record in Redis with TTL.
        """
        consent_granted = self.parse_consent_response(user_response, language)

        if consent_granted is None:
            # Ambiguous response — requires re-prompt
            return ConsentRecord(
                id=f"consent_{uuid.uuid4().hex[:8]}",
                customer_phone=phone,
                purpose=purpose,
                status=ConsentStatus.PENDING,
                channel=channel,
                metadata={"raw_response": user_response, "needs_retry": True},
            )

        now = time.time()
        record = ConsentRecord(
            id=f"consent_{uuid.uuid4().hex[:8]}",
            customer_phone=phone,
            purpose=purpose,
            status=ConsentStatus.GRANTED if consent_granted else ConsentStatus.DENIED,
            granted_at=now if consent_granted else None,
            expires_at=now + DEFAULT_CONSENT_TTL if consent_granted else None,
            channel=channel,
        )

        # Store in Redis
        consent_key = f"consent:{phone}:{purpose.value}"
        await redis_client._redis.set(
            consent_key,
            record.status.value,
            ex=DEFAULT_CONSENT_TTL if consent_granted else 3600,
        )

        logger.info(
            "consent_captured",
            phone=phone,
            purpose=purpose.value,
            status=record.status.value,
        )

        return record

    async def check_consent(
        self, phone: str, purpose: ConsentPurpose
    ) -> ConsentStatus:
        """Check if a customer has given consent for a specific purpose."""
        consent_key = f"consent:{phone}:{purpose.value}"
        try:
            value = await redis_client._redis.get(consent_key)
            if value:
                return ConsentStatus(value)
        except Exception:
            pass
        return ConsentStatus.PENDING

    async def withdraw_consent(
        self, phone: str, purpose: ConsentPurpose
    ) -> bool:
        """Withdraw previously granted consent (DPDPA right to withdraw)."""
        consent_key = f"consent:{phone}:{purpose.value}"
        try:
            await redis_client._redis.set(
                consent_key,
                ConsentStatus.WITHDRAWN.value,
                ex=DEFAULT_CONSENT_TTL,
            )
            logger.info(
                "consent_withdrawn",
                phone=phone,
                purpose=purpose.value,
            )
            return True
        except Exception as e:
            logger.error("consent_withdraw_error", error=str(e))
            return False

    async def get_all_consents(self, phone: str) -> Dict[str, str]:
        """Get all consent statuses for a customer (for DPDPA data requests)."""
        consents = {}
        for purpose in ConsentPurpose:
            status = await self.check_consent(phone, purpose)
            consents[purpose.value] = status.value
        return consents

    async def handle_data_deletion_request(self, phone: str) -> Dict[str, Any]:
        """Handle a DPDPA right-to-erasure request.

        Withdraws all consents and flags data for deletion.
        """
        withdrawn = []
        for purpose in ConsentPurpose:
            await self.withdraw_consent(phone, purpose)
            withdrawn.append(purpose.value)

        # Flag for deletion in Redis
        await redis_client._redis.set(
            f"deletion_request:{phone}",
            str(time.time()),
            ex=30 * 24 * 3600,  # 30-day processing window
        )

        logger.warning(
            "data_deletion_requested",
            phone=phone,
            purposes_withdrawn=withdrawn,
        )

        return {
            "phone": phone,
            "status": "deletion_requested",
            "purposes_withdrawn": withdrawn,
            "processing_deadline_days": 30,
        }


# Singleton
consent_manager = ConsentManager()
