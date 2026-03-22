"""
heybuddy/home_automation/home_assistant.py — Home Assistant REST API integration.

Controls smart home devices via a local Home Assistant instance using its
REST API and a long-lived access token.

Reference:
    https://developers.home-assistant.io/docs/api/rest/
"""

import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Timeout for all REST requests (seconds)
_REQUEST_TIMEOUT = 10


class HomeAssistantClient:
    """Send commands to Home Assistant via its REST API.

    Args:
        config: The ``home_assistant`` section of the HeyBuddy config dict.

    Example config keys:
        - ``base_url``: URL of the Home Assistant instance (e.g. ``"http://homeassistant.local:8123"``).
        - ``token``: Long-lived access token.
    """

    def __init__(self, config: dict) -> None:
        self._base_url: str = config.get("base_url", "http://homeassistant.local:8123").rstrip("/")
        self._token: Optional[str] = config.get("token")
        self._session: Optional[requests.Session] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_command(self, command: str) -> Optional[str]:
        """Parse *command* and call the relevant Home Assistant service.

        This implementation uses a simple keyword-based approach to map
        common voice commands to HA service calls.

        Args:
            command: Normalised (lowercase) command string.

        Returns:
            A human-readable confirmation string, or ``None`` on failure.
        """
        if not self._token:
            logger.warning("No Home Assistant token configured — command ignored")
            return None

        self._ensure_session()

        try:
            domain, service, service_data = self._parse_command(command)
            if domain is None:
                logger.debug("Could not map command to HA service: '%s'", command)
                return None

            endpoint = f"{self._base_url}/api/services/{domain}/{service}"
            logger.info("Calling HA service %s/%s: %s", domain, service, service_data)
            response = self._session.post(
                endpoint,
                json=service_data,
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            logger.debug("HA response: %d", response.status_code)
            return f"Done! {command.capitalize()}."
        except requests.RequestException as exc:
            logger.error("Home Assistant API error: %s", exc)
            return None

    def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the current state of a Home Assistant entity.

        Args:
            entity_id: HA entity ID (e.g. ``"light.living_room"``).

        Returns:
            A dict with the entity state, or ``None`` on failure.
        """
        if not self._token:
            return None
        self._ensure_session()
        try:
            url = f"{self._base_url}/api/states/{entity_id}"
            response = self._session.get(url, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error("Failed to get state for %s: %s", entity_id, exc)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_session(self) -> None:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                }
            )

    def _parse_command(
        self, command: str
    ) -> tuple[Optional[str], Optional[str], Dict[str, Any]]:
        """Map a natural language command to a (domain, service, service_data) tuple."""
        service_data: Dict[str, Any] = {}

        # Light commands
        if "light" in command or "lamp" in command:
            if any(w in command for w in ("turn on", "switch on", "on")):
                return "light", "turn_on", service_data
            if any(w in command for w in ("turn off", "switch off", "off")):
                return "light", "turn_off", service_data
            if "dim" in command or "brightness" in command:
                return "light", "turn_on", {"brightness_pct": 30}

        # Switch / plug commands
        if any(w in command for w in ("switch", "plug", "outlet")):
            if "on" in command:
                return "switch", "turn_on", service_data
            if "off" in command:
                return "switch", "turn_off", service_data

        # Scene commands
        if "scene" in command:
            return "scene", "turn_on", service_data

        # Climate (non-Nest fallback)
        if any(w in command for w in ("heat", "cool", "climate")):
            if "on" in command:
                return "climate", "turn_on", service_data
            if "off" in command:
                return "climate", "turn_off", service_data

        # Generic turn on/off for any domain
        if "turn on" in command:
            return "homeassistant", "turn_on", service_data
        if "turn off" in command:
            return "homeassistant", "turn_off", service_data

        return None, None, service_data
