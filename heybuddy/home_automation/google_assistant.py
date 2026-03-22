"""
heybuddy/home_automation/google_assistant.py — Google Assistant SDK integration.

Sends text commands to Google Assistant using the Google Assistant gRPC API.
This requires a registered Google Actions device (device model + instance IDs)
and valid OAuth2 credentials.

Reference:
    https://developers.google.com/assistant/sdk/guides/service/python
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GoogleAssistantClient:
    """Send text commands to Google Assistant.

    Args:
        config: The ``google_assistant`` section of the HeyBuddy config dict.

    Example config keys:
        - ``credentials_file``: Path to the OAuth2 credentials JSON file.
        - ``device_model_id``: Google Actions device model ID.
        - ``device_instance_id``: Google Actions device instance ID.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._credentials_file: str = config.get("credentials_file", "credentials.json")
        self._device_model_id: Optional[str] = config.get("device_model_id")
        self._device_instance_id: Optional[str] = config.get("device_instance_id")
        self._assistant = None
        self._credentials = None
        self._channel = None
        self._initialised = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_command(self, command: str) -> Optional[str]:
        """Send a text command to Google Assistant.

        Args:
            command: Natural language command string (e.g. "turn on the lights").

        Returns:
            The text response from Google Assistant, or ``None`` on failure.
        """
        self._initialise()

        if self._assistant is None:
            logger.warning(
                "Google Assistant SDK not available — command ignored: '%s'", command
            )
            return None

        logger.info("Sending to Google Assistant: '%s'", command)
        try:
            response_text = self._send_text_query(command)
            logger.info("Google Assistant response: '%s'", response_text)
            return response_text
        except Exception as exc:
            logger.error("Google Assistant error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if self._initialised:
            return
        try:
            import google.auth.transport.grpc as google_auth_grpc  # type: ignore
            import google.auth.transport.requests as google_auth_requests  # type: ignore
            import google.oauth2.credentials as google_oauth2  # type: ignore
            import googleapiclient.discovery  # type: ignore

            # Load credentials from file
            import json
            import os

            if not os.path.exists(self._credentials_file):
                logger.warning(
                    "Google Assistant credentials file not found: %s",
                    self._credentials_file,
                )
                self._initialised = True
                return

            with open(self._credentials_file, "r", encoding="utf-8") as fh:
                cred_data = json.load(fh)

            self._credentials = google_oauth2.Credentials(
                token=cred_data.get("token"),
                refresh_token=cred_data.get("refresh_token"),
                token_uri=cred_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=cred_data.get("client_id"),
                client_secret=cred_data.get("client_secret"),
            )
            http_request = google_auth_requests.Request()
            self._credentials.refresh(http_request)

            self._channel = google_auth_grpc.secure_authorized_channel(
                self._credentials,
                http_request,
                "embeddedassistant.googleapis.com",
            )
            # Import the generated gRPC stubs if available
            try:
                from google.assistant.embedded.v1alpha2 import (  # type: ignore
                    embedded_assistant_pb2_grpc,
                )

                self._assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
                    self._channel
                )
                logger.debug("Google Assistant SDK initialised")
            except ImportError:
                logger.warning(
                    "google-assistant-sdk gRPC stubs not available. "
                    "Install the google-assistant-sdk package."
                )
        except ImportError:
            logger.warning(
                "google-auth or google-assistant-sdk packages not available. "
                "Install with: pip install google-auth google-auth-oauthlib"
            )
        except Exception as exc:
            logger.error("Failed to initialise Google Assistant SDK: %s", exc)
        self._initialised = True

    def _send_text_query(self, text: str) -> Optional[str]:
        """Send a text query via the Embedded Assistant API and collect the response."""
        try:
            from google.assistant.embedded.v1alpha2 import (  # type: ignore
                embedded_assistant_pb2,
            )
        except ImportError:
            return None

        config = embedded_assistant_pb2.AssistConfig(
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding="LINEAR16",
                sample_rate_hertz=16000,
                volume_percentage=100,
            ),
            dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                language_code="en-US",
                conversation_state=b"",
                is_new_conversation=True,
            ),
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self._device_instance_id,
                device_model_id=self._device_model_id,
            ),
            text_query=text,
        )

        response_text_parts = []
        for resp in self._assistant.Assist(
            iter([embedded_assistant_pb2.AssistRequest(config=config)]),
            timeout=10,
        ):
            if resp.HasField("dialog_state_out"):
                if resp.dialog_state_out.supplemental_display_text:
                    response_text_parts.append(
                        resp.dialog_state_out.supplemental_display_text
                    )

        return " ".join(response_text_parts) if response_text_parts else None
