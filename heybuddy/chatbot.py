"""
heybuddy/chatbot.py — OpenAI GPT chatbot integration.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Maximum number of conversation turns kept in memory.
_MAX_HISTORY_TURNS = 10


class Chatbot:
    """Sends user messages to OpenAI GPT and returns responses.

    The chatbot maintains a short conversation history so follow-up questions
    make sense to the model.

    Args:
        config: The ``chatbot`` section of the HeyBuddy configuration dict.

    Example config keys:
        - ``api_key``: OpenAI API key.
        - ``model``: Model name (e.g. ``"gpt-4o-mini"``).
        - ``max_tokens``: Maximum tokens in the response (default 256).
        - ``system_prompt``: System message defining the assistant's persona.
    """

    def __init__(self, config: dict) -> None:
        self._config = config
        self._api_key: Optional[str] = config.get("api_key")
        self._model: str = config.get("model", "gpt-4o-mini")
        self._max_tokens: int = int(config.get("max_tokens", 256))
        self._system_prompt: str = config.get(
            "system_prompt",
            "You are HeyBuddy, a helpful voice assistant on a Raspberry Pi. "
            "Keep answers short — they will be spoken aloud.",
        )
        self._history: List[Dict[str, str]] = []
        self._client = None
        self._initialised = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Send *user_message* to GPT and return the assistant's reply.

        Args:
            user_message: The text to send to the model.

        Returns:
            The assistant's text response, or an error message string.
        """
        self._initialise()

        if self._client is None:
            logger.warning("OpenAI client not available — returning fallback response")
            return "Sorry, the chatbot is currently unavailable."

        self._history.append({"role": "user", "content": user_message})

        messages = [{"role": "system", "content": self._system_prompt}] + self._history

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=self._max_tokens,
            )
            reply = response.choices[0].message.content.strip()
            self._history.append({"role": "assistant", "content": reply})
            # Keep history within the allowed window.
            if len(self._history) > _MAX_HISTORY_TURNS * 2:
                self._history = self._history[-_MAX_HISTORY_TURNS * 2 :]
            logger.info("GPT reply: '%s'", reply)
            return reply
        except Exception as exc:
            logger.error("OpenAI API error: %s", exc)
            return "I'm sorry, I couldn't process that request right now."

    def reset_history(self) -> None:
        """Clear the conversation history."""
        self._history = []
        logger.debug("Chatbot history cleared")

    def set_system_prompt(self, prompt: str) -> None:
        """Update the system prompt used for subsequent chat calls.

        Does **not** clear conversation history — use :meth:`set_personality`
        if you also want to reset the history.

        Args:
            prompt: The new system prompt string.
        """
        self._system_prompt = prompt
        logger.debug("System prompt updated")

    def set_personality(self, system_prompt: str) -> None:
        """Switch to a new personality by updating the system prompt and
        clearing conversation history.

        Clearing history ensures the new character does not remember the
        previous character's conversation.

        Args:
            system_prompt: The new system prompt string.
        """
        self.set_system_prompt(system_prompt)
        self.reset_history()
        logger.info("Personality changed — history cleared")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _initialise(self) -> None:
        if self._initialised:
            return
        try:
            from openai import OpenAI  # type: ignore

            if not self._api_key:
                logger.warning(
                    "No OpenAI API key configured — chatbot will return fallback responses"
                )
            else:
                self._client = OpenAI(api_key=self._api_key)
                logger.debug("OpenAI client initialised (model=%s)", self._model)
        except ImportError:
            logger.warning(
                "openai package not installed — chatbot disabled. "
                "Install with: pip install openai"
            )
        except Exception as exc:
            logger.error("Failed to initialise OpenAI client: %s", exc)
        self._initialised = True
