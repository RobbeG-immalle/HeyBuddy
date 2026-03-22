"""
heybuddy/tts.py — pyttsx3-based text-to-speech.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pyttsx3  # type: ignore

    _PYTTSX3_AVAILABLE = True
except ImportError:
    _PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not installed — TTS disabled. Install with: pip install pyttsx3")


class TextToSpeech:
    """Speaks text using pyttsx3 (offline, cross-platform).

    A fresh pyttsx3 engine is created for every :meth:`speak` call.  This
    avoids the well-known Windows bug where the engine hangs silently after
    the first ``runAndWait()`` when the same instance is reused.

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """Convert *text* to speech and play it through the speakers.

        A new pyttsx3 engine is initialised for every call so that the
        engine never gets stuck after a previous ``runAndWait()`` (a known
        pyttsx3 issue on Windows).

        Args:
            text: The string to speak aloud.
        """
        if not text:
            return
        if not _PYTTSX3_AVAILABLE:
            return
        logger.info("Speaking: '%s'", text)
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            if self._voice_id:
                engine.setProperty("voice", self._voice_id)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:  # pragma: no cover
            logger.error("TTS error: %s", exc)

    def cleanup(self) -> None:
        """No-op — engines are created and destroyed per :meth:`speak` call."""
