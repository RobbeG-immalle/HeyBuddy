"""tests/test_home_automation.py — Unit tests for home automation modules."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from heybuddy.home_automation.home_assistant import HomeAssistantClient
from heybuddy.home_automation.nest_sdm import NestSDMClient


# ---------------------------------------------------------------------------
# HomeAssistantClient tests
# ---------------------------------------------------------------------------


class TestHomeAssistantClient:
    """Tests for the Home Assistant REST API client."""

    def _client(self, token="test-token", base_url="http://ha.local:8123"):
        return HomeAssistantClient({"base_url": base_url, "token": token})

    def test_no_token_returns_none(self):
        client = HomeAssistantClient({})
        result = client.send_command("turn on the lights")
        assert result is None

    def test_turn_on_light_calls_correct_service(self):
        client = self._client()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        with patch("requests.Session.post", return_value=mock_response) as mock_post:
            client._ensure_session()
            client._session.post = mock_post
            result = client.send_command("turn on the living room lights")

        assert result is not None
        called_url = mock_post.call_args[0][0]
        assert "light/turn_on" in called_url

    def test_turn_off_light_calls_correct_service(self):
        client = self._client()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch("requests.Session.post", return_value=mock_response) as mock_post:
            client._ensure_session()
            client._session.post = mock_post
            result = client.send_command("turn off the bedroom lights")

        called_url = mock_post.call_args[0][0]
        assert "light/turn_off" in called_url

    def test_api_error_returns_none(self):
        client = self._client()
        client._ensure_session()
        client._session.post = MagicMock(
            side_effect=requests.RequestException("Connection refused")
        )
        result = client.send_command("turn on the lights")
        assert result is None

    def test_unknown_command_returns_none(self):
        client = self._client()
        result = client._parse_command("do something weird")[0]
        # generic turn on/off fallback
        # "do something weird" doesn't contain turn on/off so should return None domain
        # Actually let's test what _parse_command returns for a completely unknown command
        domain, service, _ = client._parse_command("xyzzy teleport")
        assert domain is None

    def test_get_state_success(self):
        client = self._client()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "entity_id": "light.living_room",
            "state": "on",
        }
        client._ensure_session()
        client._session.get = MagicMock(return_value=mock_response)

        state = client.get_state("light.living_room")
        assert state["state"] == "on"

    def test_get_state_error_returns_none(self):
        client = self._client()
        client._ensure_session()
        client._session.get = MagicMock(
            side_effect=requests.RequestException("timeout")
        )
        state = client.get_state("light.living_room")
        assert state is None

    def test_session_includes_auth_header(self):
        client = self._client(token="my-secret-token")
        client._ensure_session()
        assert "Bearer my-secret-token" in client._session.headers["Authorization"]


# ---------------------------------------------------------------------------
# NestSDMClient tests
# ---------------------------------------------------------------------------


class TestNestSDMClient:
    """Tests for the Google Nest SDM API client."""

    def _client(self):
        return NestSDMClient(
            {
                "project_id": "test-project",
                "client_id": "client123",
                "client_secret": "secret123",
                "refresh_token": "refresh123",
            }
        )

    def test_no_project_id_returns_not_configured(self):
        client = NestSDMClient({})
        result = client.send_command("set thermostat to 21")
        assert "not configured" in result.lower()

    def test_list_devices_returns_empty_on_error(self):
        client = self._client()
        client._ensure_access_token = MagicMock(side_effect=Exception("auth error"))
        devices = client.list_devices()
        assert devices == []

    def test_set_thermostat_no_devices(self):
        client = self._client()
        client.list_devices = MagicMock(return_value=[])
        result = client._set_thermostat(21.0)
        assert "no nest thermostat" in result.lower()

    def test_get_temperature_no_devices(self):
        client = self._client()
        client.list_devices = MagicMock(return_value=[])
        result = client._get_temperature()
        assert "no nest thermostat" in result.lower()

    def test_get_camera_info_no_cameras(self):
        client = self._client()
        client.list_devices = MagicMock(return_value=[])
        result = client._get_camera_info()
        assert "no nest camera" in result.lower()

    def test_get_camera_info_with_cameras(self):
        client = self._client()
        client.list_devices = MagicMock(
            return_value=[
                {"name": "enterprises/p/devices/cam1", "type": "sdm.devices.types.CAMERA"},
                {"name": "enterprises/p/devices/cam2", "type": "sdm.devices.types.DOORBELL"},
            ]
        )
        result = client._get_camera_info()
        assert "2" in result

    def test_send_command_temperature_query(self):
        client = self._client()
        client._get_temperature = MagicMock(return_value="It is 20 degrees.")
        result = client.send_command("what is the temperature")
        assert result == "It is 20 degrees."

    def test_send_command_set_thermostat(self):
        client = self._client()
        client._set_thermostat = MagicMock(return_value="Thermostat set to 22 degrees.")
        result = client.send_command("set thermostat to 22 degrees")
        assert result == "Thermostat set to 22 degrees."

    def test_send_command_camera(self):
        client = self._client()
        client._get_camera_info = MagicMock(return_value="Found 1 Nest camera(s).")
        result = client.send_command("show me the camera")
        assert "camera" in result.lower()

    def test_ensure_access_token_raises_without_credentials(self):
        client = NestSDMClient({"project_id": "proj"})
        with pytest.raises(ValueError):
            client._ensure_access_token()

    def test_get_temperature_reads_ambient(self):
        client = self._client()
        devices = [
            {
                "name": "enterprises/p/devices/thermo1",
                "type": "sdm.devices.types.THERMOSTAT",
                "traits": {
                    "sdm.devices.traits.Temperature": {
                        "ambientTemperatureCelsius": 20.5
                    }
                },
            }
        ]
        client.list_devices = MagicMock(return_value=devices)
        result = client._get_temperature()
        assert "20.5" in result
