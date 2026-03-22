"""
heybuddy/wake_word.py — Porcupine-based wake word detection.

Listens continuously on the microphone and fires a callback when the
configured wake word is detected. Falls back gracefully when Porcupine
is unavailable (useful for testing without hardware).
"""

import logging
import struct
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Detects the configured wake word using Picovoice Porcupine.

    Args:
        config: The ``wake_word`` section of the HeyBuddy configuration dict.

    Example config keys:
        - ``keyword``: Built-in keyword name or path to a ``.ppn`` file.
        - ``sensitivity``: Float between 0.0 and 1.0.
        - ``access_key``: Picovoice access key.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._porcupine = None
        self._pa = None
        self._stream = None
        self._keyword = config.get("keyword", "hey buddy")
        self._sensitivity = float(config.get("sensitivity", 0.5))
        self._access_key: Optional[str] = config.get("access_key")
        self._running = False
        self._initialised = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, on_detected: Callable[[], None]) -> None:
        """Start listening for the wake word.

        Blocks the calling thread until :meth:`stop` is called or a
        ``KeyboardInterrupt`` is raised.

        Args:
            on_detected: Zero-argument callable invoked each time the wake
                word is detected.
        """
        self._initialise()
        self._running = True
        logger.info("Wake word detector started — listening for '%s'", self._keyword)

        try:
            while self._running:
                if self._porcupine is not None and self._stream is not None:
                    pcm = self._stream.read(
                        self._porcupine.frame_length, exception_on_overflow=False
                    )
                    pcm_unpacked = struct.unpack_from(
                        "h" * self._porcupine.frame_length, pcm
                    )
                    result = self._porcupine.process(pcm_unpacked)
                    if result >= 0:
                        logger.info("Wake word detected!")
                        on_detected()
                else:
                    # Fallback: poll every 0.1 s so the loop is still stoppable.
                    time.sleep(0.1)
        except Exception as exc:  # pragma: no cover
            logger.error("Wake word detection error: %s", exc)
            raise
        finally:
            self._cleanup_stream()

    def stop(self) -> None:
        """Signal the detection loop to stop."""
        self._running = False

    def cleanup(self) -> None:
        """Release all resources held by this detector."""
        self.stop()
        self._cleanup_stream()
        if self._porcupine is not None:
            try:
                self._porcupine.delete()
            except Exception as exc:  # pragma: no cover
                logger.warning("Error deleting Porcupine instance: %s", exc)
            self._porcupine = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if self._initialised:
            return
        try:
            import pvporcupine  # type: ignore

            keyword_arg = self._keyword
            # If the keyword looks like a file path, treat it as a .ppn model.
            if keyword_arg.endswith(".ppn"):
                self._porcupine = pvporcupine.create(
                    access_key=self._access_key,
                    keyword_paths=[keyword_arg],
                    sensitivities=[self._sensitivity],
                )
            else:
                self._porcupine = pvporcupine.create(
                    access_key=self._access_key,
                    keywords=[keyword_arg],
                    sensitivities=[self._sensitivity],
                )

            import pyaudio  # type: ignore

            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._porcupine.frame_length,
            )
            logger.debug("Porcupine initialised with keyword '%s'", keyword_arg)
        except ImportError:
            logger.warning(
                "pvporcupine or pyaudio not installed — wake word detection disabled. "
                "Install with: pip install pvporcupine pyaudio"
            )
        except Exception as exc:
            logger.error("Failed to initialise Porcupine: %s", exc)
            raise
        self._initialised = True

    def _cleanup_stream(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:  # pragma: no cover
                pass
            self._stream = None
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:  # pragma: no cover
                pass
            self._pa = None
