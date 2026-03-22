"""
heybuddy/speech_recognition.py — Vosk-based offline speech-to-text.

Captures audio from the microphone and transcribes it using the Vosk
speech recognition library. No internet connection is required.
"""

import json
import logging
import queue
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Offline speech-to-text using Vosk.

    Args:
        config: The ``speech_recognition`` section of the HeyBuddy config dict.

    Example config keys:
        - ``model_path``: Path to the Vosk model directory.
        - ``sample_rate``: Audio sample rate in Hz (default 16000).
        - ``listen_timeout``: Seconds to wait for speech (default 10).
        - ``device_index``: PyAudio device index (``None`` = system default).
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._model_path: str = config.get("model_path", "models/vosk-model-en-us")
        self._sample_rate: int = int(config.get("sample_rate", 16000))
        self._listen_timeout: int = int(config.get("listen_timeout", 10))
        self._device_index: Optional[int] = config.get("device_index")
        self._model = None
        self._recognizer = None
        self._pa = None
        self._initialised = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def listen(self) -> Optional[str]:
        """Capture audio and return the transcribed text.

        Listens for up to ``listen_timeout`` seconds. Returns ``None`` if
        nothing was understood or if Vosk is not available.

        Returns:
            Transcribed text as a string, or ``None`` on failure / timeout.
        """
        self._initialise()

        if self._recognizer is None or self._pa is None:
            logger.warning("Speech recognizer not available — returning None")
            return None

        import pyaudio  # type: ignore

        chunk = 4096
        stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._sample_rate,
            input=True,
            frames_per_buffer=chunk,
            input_device_index=self._device_index,
        )
        logger.debug("Listening for speech (timeout=%ds)…", self._listen_timeout)
        start_time = time.monotonic()

        try:
            while True:
                elapsed = time.monotonic() - start_time
                if elapsed >= self._listen_timeout:
                    logger.debug("Listen timeout reached")
                    break

                data = stream.read(chunk, exception_on_overflow=False)
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        logger.info("Recognised: '%s'", text)
                        return text
        except Exception as exc:  # pragma: no cover
            logger.error("Error during speech recognition: %s", exc)
        finally:
            stream.stop_stream()
            stream.close()
            # Reset recognizer for next use
            if self._recognizer is not None:
                self._recognizer.Reset()

        return None

    def cleanup(self) -> None:
        """Release PyAudio resources."""
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:  # pragma: no cover
                pass
            self._pa = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if self._initialised:
            return
        try:
            from vosk import KaldiRecognizer, Model  # type: ignore

            logger.debug("Loading Vosk model from '%s'…", self._model_path)
            self._model = Model(self._model_path)
            self._recognizer = KaldiRecognizer(self._model, self._sample_rate)
            logger.debug("Vosk model loaded")
        except ImportError:
            logger.warning(
                "vosk not installed — speech recognition disabled. "
                "Install with: pip install vosk"
            )
        except Exception as exc:
            logger.error("Failed to load Vosk model from '%s': %s", self._model_path, exc)

        try:
            import pyaudio  # type: ignore

            self._pa = pyaudio.PyAudio()
        except ImportError:
            logger.warning("pyaudio not installed — audio capture disabled.")
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to initialise PyAudio: %s", exc)

        self._initialised = True
