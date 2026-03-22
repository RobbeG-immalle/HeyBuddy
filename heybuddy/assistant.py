"""
heybuddy/assistant.py — Main orchestrator for the HeyBuddy assistant.

Flow:
    1. Wake word detector waits for "Hey Buddy".
    2. Speech recognizer captures the spoken command.
    3. Intent parser routes the command.
    4. Home automation handler OR chatbot processes the command.
    5. TTS speaks the response back to the user.
"""

import logging
from typing import Any, Dict

from heybuddy.chatbot import Chatbot
from heybuddy.intent import Intent, parse_intent
from heybuddy.skin_manager import SkinManager
from heybuddy.speech_recognition import SpeechRecognizer
from heybuddy.tts import TextToSpeech
from heybuddy.wake_word import WakeWordDetector
from heybuddy.home_automation.google_assistant import GoogleAssistantClient
from heybuddy.home_automation.home_assistant import HomeAssistantClient
from heybuddy.home_automation.nest_sdm import NestSDMClient

logger = logging.getLogger(__name__)


class Assistant:
    """Top-level assistant orchestrator.

    Args:
        config: The full HeyBuddy configuration dictionary (loaded from YAML).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config

        # Skin/personality system
        self._skin_manager = SkinManager(config)
        skin = self._skin_manager.active_skin

        # Build per-subsystem configs, overriding with skin values where set
        tts_config = dict(config.get("tts", {}))
        if skin.get("tts_rate") is not None:
            tts_config["rate"] = skin["tts_rate"]
        if skin.get("voice_id") is not None:
            tts_config["voice_id"] = skin["voice_id"]

        chatbot_config = dict(config.get("chatbot", {}))
        if skin.get("system_prompt"):
            chatbot_config["system_prompt"] = skin["system_prompt"]

        wake_word_config = dict(config.get("wake_word", {}))
        if skin.get("wake_word_model") is not None:
            wake_word_config["model_path"] = skin["wake_word_model"]

        # Subsystem initialisation
        self._wake_word = WakeWordDetector(wake_word_config)
        self._stt = SpeechRecognizer(config.get("speech_recognition", {}))
        self._tts = TextToSpeech(tts_config)
        self._chatbot = Chatbot(chatbot_config)
        self._google_assistant = GoogleAssistantClient(
            config.get("google_assistant", {})
        )
        self._home_assistant = HomeAssistantClient(
            config.get("home_assistant", {})
        )
        self._nest_sdm = NestSDMClient(config.get("nest_sdm", {}))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the main assistant loop (blocking).

        Listens for the wake word, then processes commands in a loop until
        :meth:`cleanup` is called or a ``KeyboardInterrupt`` is raised.
        """
        greeting = self._skin_manager.active_skin.get(
            "greeting", "HeyBuddy is ready. Say Hey Buddy to start."
        )
        self._tts.speak(greeting)
        self._wake_word.start(on_detected=self._handle_wake_word)

    def cleanup(self) -> None:
        """Release all resources held by the assistant subsystems."""
        logger.debug("Cleaning up assistant resources…")
        self._wake_word.cleanup()
        self._stt.cleanup()
        self._tts.cleanup()

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _handle_wake_word(self) -> None:
        """Called by the wake word detector each time the wake word fires."""
        logger.info("Wake word detected — listening for command…")
        self._tts.speak("Yes?")

        text = self._stt.listen()

        if not text:
            logger.info("No speech detected after wake word")
            self._tts.speak("I didn't catch that. Please try again.")
            return

        logger.info("Command: '%s'", text)
        intent, normalised = parse_intent(text)

        if intent == Intent.HOME_AUTOMATION:
            response = self._handle_home_automation(normalised)
        else:
            response = self._chatbot.chat(text)

        if response:
            self._tts.speak(response)

    def _handle_home_automation(self, command: str) -> str:
        """Route a home automation command to the appropriate backend.

        Tries Google Assistant first, then falls back to Home Assistant.
        Nest SDM commands are detected by keyword.

        Args:
            command: Normalised (lowercase) command string.

        Returns:
            A human-readable response string.
        """
        # Nest-specific keywords
        if any(kw in command for kw in ("thermostat", "temperature", "nest", "camera")):
            logger.info("Routing to Nest SDM: '%s'", command)
            return self._nest_sdm.send_command(command)

        # Try Google Assistant SDK first
        google_response = self._google_assistant.send_command(command)
        if google_response:
            return google_response

        # Fallback: Home Assistant REST API
        ha_response = self._home_assistant.send_command(command)
        if ha_response:
            return ha_response

        return "Sorry, I couldn't process that home automation command."
