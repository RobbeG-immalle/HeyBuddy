"""
heybuddy/tts.py — ElevenLabs-based text-to-speech with pyttsx3 fallback.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Speaks text using ElevenLabs API, with pyttsx3 as offline fallback.

    Args:
        config: The ``tts`` section of the HeyBuddy configuration dict.

    Config keys:
        - ``engine``: ``"elevenlabs"`` (default) or ``"pyttsx3"`` (offline fallback).
        - ``elevenlabs_api_key``: ElevenLabs API key.
        - ``elevenlabs_voice_id``: ElevenLabs voice ID (default: ``"Rachel"``).
        - ``elevenlabs_model``: Model to use (default: ``"eleven_multilingual_v2"``).
        - ``rate``: Words per minute for pyttsx3 fallback (default 175).
        - ``volume``: Volume for pyttsx3 fallback (default 1.0).
        - ``voice_id``: pyttsx3 voice ID for fallback, or ``None`` for system default.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._engine_type: str = config.get("engine", "elevenlabs")

        # ElevenLabs settings
        self._elevenlabs_api_key: Optional[str] = config.get("elevenlabs_api_key")
        self._elevenlabs_voice_id: str = config.get("elevenlabs_voice_id", "Rachel")
        self._elevenlabs_model: str = config.get(
            "elevenlabs_model", "eleven_multilingual_v2"
        )

        # pyttsx3 fallback settings
        self._rate: int = int(config.get("rate", 175))
        self._volume: float = float(config.get("volume", 1.0))
        self._pyttsx3_voice_id: Optional[str] = config.get("voice_id")

        self._elevenlabs_client = None
        self._initialised = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """Convert *text* to speech and play it through the speakers.

        Uses ElevenLabs when configured and an API key is available; falls
        back to pyttsx3 otherwise.  A fresh pyttsx3 engine is created for
        every call to avoid the Windows silent-after-first-call bug.

        Args:
            text: The string to speak aloud.
        """
        if not text:
            return
        self._initialise()
        logger.info("Speaking: '%s'", text)

        if self._engine_type == "elevenlabs" and self._elevenlabs_client is not None:
            self._speak_elevenlabs(text)
        else:
            self._speak_pyttsx3(text)

    def cleanup(self) -> None:
        """Release resources held by the TTS engine."""
        self._elevenlabs_client = None

    def set_voice(
        self,
        elevenlabs_voice_id: Optional[str] = None,
        pyttsx3_voice_id: Optional[str] = None,
        rate: Optional[int] = None,
    ) -> None:
        """Update voice settings at runtime (e.g. when switching skins).

        Args:
            elevenlabs_voice_id: ElevenLabs voice ID to use for subsequent
                :meth:`speak` calls, or ``None`` to leave unchanged.
            pyttsx3_voice_id: pyttsx3 voice ID for the fallback engine, or
                ``None`` to leave unchanged.
            rate: Words per minute for the pyttsx3 fallback, or ``None`` to
                leave unchanged.
        """
        if elevenlabs_voice_id is not None:
            self._elevenlabs_voice_id = elevenlabs_voice_id
            logger.debug("ElevenLabs voice updated — voice_id=%s", elevenlabs_voice_id)
        if pyttsx3_voice_id is not None:
            self._pyttsx3_voice_id = pyttsx3_voice_id
            logger.debug("pyttsx3 voice updated — voice_id=%s", pyttsx3_voice_id)
        if rate is not None:
            self._rate = int(rate)
            logger.debug("TTS rate updated — rate=%s", rate)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        """Lazily initialise the chosen TTS engine."""
        if self._initialised:
            return

        if self._engine_type == "elevenlabs":
            try:
                from elevenlabs.client import ElevenLabs  # type: ignore

                if not self._elevenlabs_api_key:
                    logger.warning(
                        "No ElevenLabs API key configured — falling back to pyttsx3. "
                        "Get a key at https://elevenlabs.io/"
                    )
                    self._engine_type = "pyttsx3"
                else:
                    self._elevenlabs_client = ElevenLabs(
                        api_key=self._elevenlabs_api_key
                    )
                    logger.debug(
                        "ElevenLabs TTS initialised (voice=%s, model=%s)",
                        self._elevenlabs_voice_id,
                        self._elevenlabs_model,
                    )
            except ImportError:
                logger.warning(
                    "elevenlabs package not installed — falling back to pyttsx3. "
                    "Install with: pip install elevenlabs"
                )
                self._engine_type = "pyttsx3"

        self._initialised = True

    def _speak_elevenlabs(self, text: str) -> None:
        """Speak *text* using the ElevenLabs API.

        Audio is requested as raw PCM (16-bit, 22 050 Hz, mono) and streamed
        directly to PyAudio as chunks arrive, keeping memory usage low and
        reducing latency.  Falls back to pyttsx3 on any error.
        """
        try:
            import pyaudio  # type: ignore

            audio_stream = self._elevenlabs_client.text_to_speech.convert(
                voice_id=self._elevenlabs_voice_id,
                text=text,
                model_id=self._elevenlabs_model,
                output_format="pcm_22050",
            )

            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=22050,
                output=True,
            )
            try:
                for chunk in audio_stream:
                    stream.write(chunk)
            finally:
                stream.stop_stream()
                stream.close()
                pa.terminate()
        except Exception as exc:
            logger.error(
                "ElevenLabs TTS error: %s — falling back to pyttsx3", exc
            )
            self._speak_pyttsx3(text)

    def _speak_pyttsx3(self, text: str) -> None:
        """Speak *text* using pyttsx3.

        A fresh engine is created for every call to avoid the Windows bug
        where the engine goes silent after the first ``runAndWait()``.
        """
        try:
            import pyttsx3  # type: ignore

            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            if self._pyttsx3_voice_id:
                engine.setProperty("voice", self._pyttsx3_voice_id)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except ImportError:
            logger.warning("pyttsx3 not installed — TTS disabled.")
        except Exception as exc:
            logger.error("pyttsx3 TTS error: %s", exc)
