"""
heybuddy/skin_manager.py — Personality/skin system for HeyBuddy.

Each "skin" is a character profile that defines the AI's persona, voice,
speech rate, wake word model, and startup greeting.  Skins are loaded from
the ``skins:`` section of the YAML config file.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Config dict used when no skins section exists at all.
_DEFAULT_SKIN: Dict[str, Any] = {
    "name": "Buddy",
    "system_prompt": (
        "You are HeyBuddy, a helpful and friendly voice assistant. "
        "Keep your answers concise — they will be spoken aloud via text-to-speech."
    ),
    "voice_id": None,
    "elevenlabs_voice_id": None,
    "wake_word_model": None,
    "tts_rate": 175,
    "greeting": "HeyBuddy is ready. How can I help?",
}


class SkinManager:
    """Manages character skins (personalities) for HeyBuddy.

    Skins are loaded from the ``skins:`` section of the config dict.
    The ``active_skin`` config key determines which skin is loaded on startup.
    If the requested skin does not exist the ``"default"`` skin is used;
    if that does not exist either, an internal fallback is used.

    Args:
        config: The full HeyBuddy configuration dictionary.

    Example config structure::

        active_skin: "lobster"
        skins:
          lobster:
            name: "Larry the Lobster"
            system_prompt: "You are Larry…"
            voice_id: null
            wake_word_model: null
            tts_rate: 175
            greeting: "Ahoy landlubber!"
          default:
            name: "Buddy"
            system_prompt: "You are HeyBuddy…"
            voice_id: null
            wake_word_model: null
            tts_rate: 175
            greeting: "HeyBuddy is ready."
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self._skins: Dict[str, Dict[str, Any]] = config.get("skins", {})
        initial_skin_name: str = config.get("active_skin", "default")
        self._active_skin_name: str = self._resolve_skin_name(initial_skin_name)
        logger.debug(
            "SkinManager initialised — active skin: '%s'", self._active_skin_name
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def active_skin(self) -> Dict[str, Any]:
        """Return the config dict for the currently active skin."""
        return self._get_skin_config(self._active_skin_name)

    def switch_skin(self, skin_name: str) -> Dict[str, Any]:
        """Switch to a different skin by name.

        If *skin_name* does not exist the ``"default"`` skin is used as a
        fallback.

        Args:
            skin_name: The key of the skin to activate (e.g. ``"lobster"``).

        Returns:
            The config dict of the newly active skin.
        """
        resolved = self._resolve_skin_name(skin_name)
        self._active_skin_name = resolved
        logger.info("Skin switched to '%s'", resolved)
        return self._get_skin_config(resolved)

    def list_skins(self) -> List[str]:
        """Return the names (keys) of all available skins."""
        return list(self._skins.keys())

    def get_skin(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the config dict for a specific skin, or ``None`` if not found.

        The returned dict is fully merged with the built-in defaults so that
        all keys are always present (same semantics as :attr:`active_skin`).

        Args:
            name: The skin key to look up.

        Returns:
            The skin config dict with defaults filled in, or ``None`` if the
            skin does not exist.
        """
        if name not in self._skins:
            return None
        return self._get_skin_config(name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_skin_name(self, name: str) -> str:
        """Return *name* if it exists, otherwise fall back to ``"default"``."""
        if name in self._skins:
            return name
        if name != "default":
            logger.warning(
                "Skin '%s' not found — falling back to 'default'", name
            )
        if "default" in self._skins:
            return "default"
        # No skins at all — use the built-in fallback
        return "default"

    def _get_skin_config(self, name: str) -> Dict[str, Any]:
        """Return the merged skin config for *name*, filling in defaults."""
        if name in self._skins:
            skin = dict(self._skins[name])
        else:
            skin = {}

        # Fill in any missing keys from the built-in fallback
        merged: Dict[str, Any] = dict(_DEFAULT_SKIN)
        merged.update(skin)
        return merged
