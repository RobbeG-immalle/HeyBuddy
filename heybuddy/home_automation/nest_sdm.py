"""
heybuddy/home_automation/nest_sdm.py — Google Nest Device Access SDM API.

Controls Nest thermostats and cameras using the Smart Device Management (SDM)
REST API from Google.

Reference:
    https://developers.google.com/nest/device-access/api
"""

import logging
import re
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_SDM_BASE_URL = "https://smartdevicemanagement.googleapis.com/v1"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_REQUEST_TIMEOUT = 10


class NestSDMClient:
    """Control Google Nest devices via the Smart Device Management (SDM) API.

    Args:
        config: The ``nest_sdm`` section of the HeyBuddy configuration dict.

    Example config keys:
        - ``project_id``: Nest Device Access project ID.
        - ``client_id``: OAuth2 client ID.
        - ``client_secret``: OAuth2 client secret.
        - ``refresh_token``: OAuth2 refresh token (obtained via the OAuth flow).
    """

    def __init__(self, config: dict) -> None:
        self._project_id: Optional[str] = config.get("project_id")
        self._client_id: Optional[str] = config.get("client_id")
        self._client_secret: Optional[str] = config.get("client_secret")
        self._refresh_token: Optional[str] = config.get("refresh_token")
        self._access_token: Optional[str] = None
        self._session: Optional[requests.Session] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_command(self, command: str) -> str:
        """Parse *command* and dispatch the appropriate Nest SDM API call.

        Args:
            command: Normalised (lowercase) voice command string.

        Returns:
            A human-readable response string.
        """
        if not self._project_id:
            logger.warning("Nest SDM project_id not configured — command ignored")
            return "Nest integration is not configured."

        command_lower = command.lower()

        # Thermostat set-point
        temp_match = re.search(r"\b(\d+\.?\d*)\s*(?:degrees?|celsius|fahrenheit|°)?", command_lower)
        if any(w in command_lower for w in ("set", "thermostat", "heat", "cool")) and temp_match:
            temp = float(temp_match.group(1))
            return self._set_thermostat(temp)

        # Temperature query
        if any(w in command_lower for w in ("temperature", "how warm", "how cold", "what is the temp")):
            return self._get_temperature()

        # Camera snapshot / feed
        if "camera" in command_lower:
            return self._get_camera_info()

        logger.debug("No specific Nest action matched for: '%s'", command)
        return "I'm not sure how to handle that Nest command."

    def list_devices(self) -> List[Dict[str, Any]]:
        """Return a list of all devices in the Nest Device Access project.

        Returns:
            A list of device dicts, or an empty list on failure.
        """
        try:
            self._ensure_access_token()
            url = f"{_SDM_BASE_URL}/enterprises/{self._project_id}/devices"
            response = self._get_session().get(url, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json().get("devices", [])
        except Exception as exc:
            logger.error("Failed to list Nest devices: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_thermostat(self, temperature_celsius: float) -> str:
        """Set the thermostat to *temperature_celsius*."""
        devices = self.list_devices()
        thermostat_name = self._find_device_name(devices, "sdm.devices.types.THERMOSTAT")

        if not thermostat_name:
            return "No Nest thermostat found."

        try:
            self._ensure_access_token()
            url = f"{_SDM_BASE_URL}/{thermostat_name}:executeCommand"
            payload = {
                "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat",
                "params": {"heatCelsius": temperature_celsius},
            }
            response = self._get_session().post(url, json=payload, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
            logger.info("Thermostat set to %.1f°C", temperature_celsius)
            return f"Thermostat set to {temperature_celsius:.0f} degrees."
        except Exception as exc:
            logger.error("Failed to set thermostat: %s", exc)
            return "Sorry, I couldn't set the thermostat."

    def _get_temperature(self) -> str:
        """Query the ambient temperature from the first available thermostat."""
        devices = self.list_devices()
        thermostat_name = self._find_device_name(devices, "sdm.devices.types.THERMOSTAT")

        if not thermostat_name:
            return "No Nest thermostat found."

        try:
            for device in devices:
                if device.get("name") == thermostat_name:
                    traits = device.get("traits", {})
                    temp_trait = traits.get("sdm.devices.traits.Temperature", {})
                    ambient = temp_trait.get("ambientTemperatureCelsius")
                    if ambient is not None:
                        return f"The current temperature is {ambient:.1f} degrees Celsius."
        except Exception as exc:
            logger.error("Failed to read temperature: %s", exc)

        return "I couldn't read the temperature right now."

    def _get_camera_info(self) -> str:
        """Return basic info about available Nest cameras."""
        devices = self.list_devices()
        camera_names = [
            d.get("name", "") for d in devices
            if "CAMERA" in d.get("type", "").upper() or "DOORBELL" in d.get("type", "").upper()
        ]
        if not camera_names:
            return "No Nest cameras found."
        return f"Found {len(camera_names)} Nest camera(s). Live view is available in the Google Home app."

    def _find_device_name(self, devices: List[Dict[str, Any]], device_type: str) -> Optional[str]:
        for device in devices:
            if device.get("type") == device_type:
                return device.get("name")
        return None

    def _ensure_access_token(self) -> None:
        """Refresh the OAuth2 access token if not yet obtained."""
        if self._access_token:
            return
        if not all([self._client_id, self._client_secret, self._refresh_token]):
            raise ValueError("Nest SDM OAuth2 credentials are incomplete.")
        response = requests.post(
            _TOKEN_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        logger.debug("Nest SDM access token refreshed")

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            }
        )
        return self._session
