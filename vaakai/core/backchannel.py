"""Back-channel Engine — Natural filler responses during LLM processing.

Generates human-like acknowledgements ("Hmm", "Let me check", "Ek second...")
to prevent dead air while the main LLM processes the response.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Back-channel responses by language
BACKCHANNEL_RESPONSES = {
    "en": {
        "thinking": [
            "Let me check that for you...",
            "One moment please...",
            "Let me pull that up...",
            "Just a second...",
            "Looking into that now...",
        ],
        "acknowledgement": [
            "I understand.",
            "Got it.",
            "Right.",
            "I see.",
            "Okay.",
        ],
        "empathy": [
            "I understand how frustrating that must be.",
            "I'm sorry to hear that.",
            "I completely understand your concern.",
            "That's definitely something we should look into.",
        ],
        "confirmation": [
            "Sure, I can help with that.",
            "Absolutely, let me assist you.",
            "Of course, I'll take care of that.",
        ],
    },
    "hi": {
        "thinking": [
            "Ek second, check karta hoon...",
            "Dekhta hoon...",
            "Ruko, abhi dekhta hoon...",
            "Bas ek minute...",
            "Abhi check karta hoon...",
        ],
        "acknowledgement": [
            "Samajh gaya.",
            "Theek hai.",
            "Ji haan.",
            "Bilkul.",
            "Achha.",
        ],
        "empathy": [
            "Main samajh sakta hoon aapki pareshani.",
            "Mujhe dukh hai yeh sunke.",
            "Aapki baat bilkul sahi hai.",
            "Hum isko zaroor dekhenge.",
        ],
        "confirmation": [
            "Ji zaroor, main madad karta hoon.",
            "Bilkul, abhi karta hoon.",
            "Haan ji, main isko handle karta hoon.",
        ],
    },
    "bn": {
        "thinking": [
            "Ek minute dekhchi...",
            "Check korchi...",
            "Dekhun ektu...",
        ],
        "acknowledgement": [
            "Bujhte perechi.",
            "Thik achhe.",
            "Ji.",
        ],
        "empathy": [
            "Ami bujhte parchi apnar somossya.",
            "Dukkhito shune.",
        ],
        "confirmation": [
            "Ji, ami sahajjo korbo.",
            "Oboshyoi.",
        ],
    },
    "ta": {
        "thinking": [
            "Oru nimisham paarkiren...",
            "Check pannuren...",
            "Konjam porunga...",
        ],
        "acknowledgement": [
            "Puriyudhu.",
            "Sari.",
            "Aama.",
        ],
        "empathy": [
            "Ungal parachanaiyai purindhu kollugiren.",
        ],
        "confirmation": [
            "Naan udavi seigiren.",
        ],
    },
    "te": {
        "thinking": [
            "Oka nimisham choodandi...",
            "Check chestunna...",
        ],
        "acknowledgement": [
            "Artham ayyindi.",
            "Sare.",
        ],
        "empathy": [
            "Mee samasya artham chesukuntunna.",
        ],
        "confirmation": [
            "Nenu sahayam chestanu.",
        ],
    },
}

# Emotion-to-response-type mapping
EMOTION_RESPONSE_MAP = {
    "neutral": "acknowledgement",
    "happy": "acknowledgement",
    "angry": "empathy",
    "frustrated": "empathy",
    "sad": "empathy",
    "anxious": "empathy",
    "urgent": "confirmation",
    "confused": "acknowledgement",
    "satisfied": "acknowledgement",
}


class BackchannelEngine:
    """Generates contextually appropriate filler responses.

    Selects responses based on:
    - Detected language
    - Current emotion state
    - Conversation phase (thinking, acknowledging, empathizing)
    """

    def __init__(self):
        self._last_response: Optional[str] = None
        self._used_responses: List[str] = []

    def get_response(
        self,
        language: str = "en",
        emotion: str = "neutral",
        response_type: Optional[str] = None,
    ) -> str:
        """Get an appropriate back-channel response.

        Args:
            language: Current conversation language
            emotion: Current detected emotion
            response_type: Override type (thinking/acknowledgement/empathy/confirmation)

        Returns:
            A natural filler response string.
        """
        # Determine response type based on emotion if not specified
        if not response_type:
            response_type = EMOTION_RESPONSE_MAP.get(emotion, "acknowledgement")

        # Get language-specific responses, fall back to English
        lang_responses = BACKCHANNEL_RESPONSES.get(language, BACKCHANNEL_RESPONSES["en"])
        candidates = lang_responses.get(response_type, lang_responses.get("acknowledgement", ["..."]))

        # Avoid repeating the same response
        available = [r for r in candidates if r != self._last_response]
        if not available:
            available = candidates

        response = random.choice(available)
        self._last_response = response
        self._used_responses.append(response)

        logger.debug(
            "backchannel_generated",
            language=language,
            emotion=emotion,
            type=response_type,
            response=response,
        )

        return response

    def get_thinking_response(self, language: str = "en") -> str:
        """Get a 'thinking/processing' filler response."""
        return self.get_response(language=language, response_type="thinking")

    def get_empathy_response(self, language: str = "en") -> str:
        """Get an empathetic response for negative emotions."""
        return self.get_response(language=language, response_type="empathy")

    def reset(self):
        """Reset for a new call."""
        self._last_response = None
        self._used_responses.clear()


# Singleton instance
backchannel_engine = BackchannelEngine()
