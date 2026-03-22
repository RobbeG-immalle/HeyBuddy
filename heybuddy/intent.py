"""
heybuddy/intent.py — Intent parser that routes voice commands.

Commands that match home-automation keywords are routed to the home
automation subsystem; everything else falls through to the chatbot.
"""

import logging
import re
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Intent(Enum):
    """High-level intent categories."""

    HOME_AUTOMATION = auto()
    CHATBOT = auto()
    UNKNOWN = auto()


# ---------------------------------------------------------------------------
# Keyword lists used for simple intent detection
# ---------------------------------------------------------------------------

_HOME_AUTOMATION_VERBS: List[str] = [
    "turn on",
    "turn off",
    "switch on",
    "switch off",
    "set",
    "dim",
    "brighten",
    "lock",
    "unlock",
    "open",
    "close",
    "play",
    "pause",
    "stop",
    "increase",
    "decrease",
    "raise",
    "lower",
]

_HOME_AUTOMATION_NOUNS: List[str] = [
    "light",
    "lights",
    "lamp",
    "thermostat",
    "temperature",
    "heat",
    "fan",
    "air conditioning",
    "ac",
    "door",
    "garage",
    "blind",
    "blinds",
    "curtain",
    "curtains",
    "tv",
    "television",
    "music",
    "scene",
    "alarm",
    "camera",
    "nest",
    "google home",
    "speaker",
    "plug",
    "outlet",
    "switch",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_intent(text: str) -> Tuple[Intent, str]:
    """Determine the intent of *text* and return a (Intent, normalised_text) tuple.

    Args:
        text: Raw transcribed command from the user.

    Returns:
        A tuple of (Intent, normalised_text) where normalised_text is the
        command stripped of leading/trailing whitespace and lowercased.
    """
    if not text:
        return Intent.UNKNOWN, ""

    normalised = text.strip().lower()

    if not normalised:
        return Intent.UNKNOWN, ""

    if _is_home_automation(normalised):
        logger.debug("Intent: HOME_AUTOMATION for '%s'", normalised)
        return Intent.HOME_AUTOMATION, normalised

    logger.debug("Intent: CHATBOT for '%s'", normalised)
    return Intent.CHATBOT, normalised


def extract_home_automation_action(text: str) -> Dict[str, Optional[str]]:
    """Extract structured fields from a home-automation command.

    Returns a dict with keys:
        - ``verb``: The action verb (e.g. ``"turn on"``).
        - ``target``: The device or area (e.g. ``"living room lights"``).
        - ``value``: An optional numeric value (e.g. ``"21"`` for thermostat).
    """
    normalised = text.strip().lower()
    result: Dict[str, Optional[str]] = {"verb": None, "target": None, "value": None}

    # Find the first matching verb.
    for verb in sorted(_HOME_AUTOMATION_VERBS, key=len, reverse=True):
        if normalised.startswith(verb):
            result["verb"] = verb
            remainder = normalised[len(verb) :].strip()
            # Extract optional numeric value (e.g. "to 21", "to 70%")
            value_match = re.search(r"\b(\d+\.?\d*)\s*(?:%|degrees?|celsius|fahrenheit)?", remainder)
            if value_match:
                result["value"] = value_match.group(1)
            result["target"] = remainder
            break

    if result["verb"] is None:
        result["target"] = normalised

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_home_automation(text: str) -> bool:
    """Return True if *text* looks like a home automation command."""
    for verb in _HOME_AUTOMATION_VERBS:
        if text.startswith(verb):
            return True

    for noun in _HOME_AUTOMATION_NOUNS:
        if noun in text:
            return True

    return False
