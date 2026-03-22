"""
heybuddy/wake_word.py — openWakeWord-based wake word detection.

Listens continuously on the microphone and fires a callback when the
configured wake word is detected. Falls back gracefully when openWakeWord
is unavailable (useful for testing without hardware).
"""

import logging
import time
from typing import Callable, Optional

try:
    import numpy as np  # type: ignore
except ImportError:
    np = None  # type: ignore

logger = logging.getLogger(__name__)

# openWakeWord expects 16-bit PCM audio at 16 kHz, mono, 1280 samples per chunk.
_SAMPLE_RATE = 16000
_CHANNELS = 1
_CHUNK_SAMPLES = 1280  # 80 ms at 16 kHz


class WakeWordDetector:
    """Detects the configured wake word using openWakeWord.

    Args:
        config: The ``wake_word`` section of the HeyBuddy configuration dict.

    Example config keys:
        - ``model_path``: Path to a custom ``.tflite`` or ``.onnx`` model file,
          or ``null`` to use the default pre-trained openWakeWord models.
        - ``threshold``: Float between 0.0 and 1.0 — how confident the model
          must be before triggering (higher = fewer false positives).
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._model = None
        self._pa = None
        self._stream = None
        self._model_path: Optional[str] = config.get("model_path")
        self._threshold = float(config.get("threshold", 0.5))
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
        logger.info("Wake word detector started — listening (threshold=%.2f)", self._threshold)

        try:
            while self._running:
                if self._model is not None and self._stream is not None:
                    raw = self._stream.read(_CHUNK_SAMPLES, exception_on_overflow=False)
                    audio_frame = np.frombuffer(raw, dtype=np.int16)
                    predictions = self._model.predict(audio_frame)
                    if any(score >= self._threshold for score in predictions.values()):
                        logger.info("Wake word detected!")
                        self._model.reset()
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
        self._model = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if self._initialised:
            return
        try:
            import openwakeword  # type: ignore
            from openwakeword.model import Model  # type: ignore

            # Download pre-trained models on first use if none are cached locally.
            # This is a no-op when the models are already present.
            openwakeword.utils.download_models()

            if self._model_path:
                self._model = Model(wakeword_models=[self._model_path])
                logger.debug("openWakeWord initialised with custom model '%s'", self._model_path)
            else:
                self._model = Model()
                logger.debug("openWakeWord initialised with default pre-trained models")

            import pyaudio  # type: ignore

            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                rate=_SAMPLE_RATE,
                channels=_CHANNELS,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=_CHUNK_SAMPLES,
            )
        except ImportError:
            logger.warning(
                "openwakeword or pyaudio not installed — wake word detection disabled. "
                "Install with: pip install openwakeword pyaudio"
            )
        except Exception as exc:
            logger.error("Failed to initialise openWakeWord: %s", exc)
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
