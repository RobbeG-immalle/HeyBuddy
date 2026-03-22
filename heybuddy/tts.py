"""
heybuddy/tts.py — pyttsx3-based text-to-speech.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Speaks text using pyttsx3 (offline, cross-platform).

    Args:
        config: The ``tts`` section of the HeyBuddy configuration dict.

    Example config keys:
        - ``rate``: Words per minute (default 175).
        - ``volume``: Float 0.0–1.0 (default 1.0).
        - ``voice_id``: Specific voice ID string, or ``None`` for system default.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._rate: int = int(config.get("rate", 175))
        self._volume: float = float(config.get("volume", 1.0))
        self._voice_id: Optional[str] = config.get("voice_id")
        self._engine = None
        self._initialised = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """Convert *text* to speech and play it through the speakers.

        Args:
            text: The string to speak aloud.
        """
        if not text:
            return
        self._initialise()
        if self._engine is None:
            logger.warning("TTS engine not available — cannot speak: %s", text)
            return
        logger.info("Speaking: '%s'", text)
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as exc:  # pragma: no cover
            logger.error("TTS error: %s", exc)

    def cleanup(self) -> None:
        """Release the TTS engine."""
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:  # pragma: no cover
                pass
            self._engine = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if self._initialised:
            return
        try:
            import pyttsx3  # type: ignore

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            self._engine.setProperty("volume", self._volume)
            if self._voice_id:
                self._engine.setProperty("voice", self._voice_id)
            logger.debug(
                "TTS engine initialised (rate=%d, volume=%.1f)", self._rate, self._volume
            )
        except ImportError:
            logger.warning(
                "pyttsx3 not installed — TTS disabled. Install with: pip install pyttsx3"
            )
        except Exception as exc:
            logger.error("Failed to initialise TTS engine: %s", exc)
        self._initialised = True
