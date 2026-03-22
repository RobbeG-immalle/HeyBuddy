"""tests/test_chatbot.py — Unit tests for the chatbot module."""

from unittest.mock import MagicMock, patch

import pytest

from heybuddy.chatbot import Chatbot, _MAX_HISTORY_TURNS


class TestChatbotInit:
    """Tests for Chatbot initialisation."""

    def test_default_model(self):
        bot = Chatbot({})
        assert bot._model == "gpt-4o-mini"

    def test_custom_model(self):
        bot = Chatbot({"model": "gpt-4o"})
        assert bot._model == "gpt-4o"

    def test_default_max_tokens(self):
        bot = Chatbot({})
        assert bot._max_tokens == 256

    def test_api_key_stored(self):
        bot = Chatbot({"api_key": "sk-test-123"})
        assert bot._api_key == "sk-test-123"

    def test_history_starts_empty(self):
        bot = Chatbot({})
        assert bot._history == []


class TestChatbotChat:
    """Tests for Chatbot.chat()."""

    def _make_mock_response(self, content: str):
        """Build a mock OpenAI chat completions response."""
        choice = MagicMock()
        choice.message.content = content
        response = MagicMock()
        response.choices = [choice]
        return response

    def test_returns_gpt_reply(self):
        bot = Chatbot({"api_key": "sk-test"})
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._make_mock_response(
            "Here is a joke!"
        )
        bot._client = mock_client
        bot._initialised = True

        reply = bot.chat("Tell me a joke")
        assert reply == "Here is a joke!"

    def test_appends_to_history(self):
        bot = Chatbot({"api_key": "sk-test"})
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._make_mock_response(
            "Response"
        )
        bot._client = mock_client
        bot._initialised = True

        bot.chat("Hello")
        assert len(bot._history) == 2
        assert bot._history[0]["role"] == "user"
        assert bot._history[1]["role"] == "assistant"

    def test_history_trimmed_at_max(self):
        bot = Chatbot({"api_key": "sk-test"})
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._make_mock_response("ok")
        bot._client = mock_client
        bot._initialised = True

        # Fill history beyond the max
        for _ in range(_MAX_HISTORY_TURNS + 5):
            bot.chat("msg")

        assert len(bot._history) <= _MAX_HISTORY_TURNS * 2

    def test_no_client_returns_fallback(self):
        bot = Chatbot({})
        bot._initialised = True  # skip real init
        reply = bot.chat("Hello")
        assert "unavailable" in reply.lower()

    def test_api_error_returns_error_message(self):
        bot = Chatbot({"api_key": "sk-test"})
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        bot._client = mock_client
        bot._initialised = True

        reply = bot.chat("Hello")
        assert "sorry" in reply.lower() or "couldn't" in reply.lower()

    def test_reset_history(self):
        bot = Chatbot({"api_key": "sk-test"})
        bot._history = [{"role": "user", "content": "hi"}]
        bot.reset_history()
        assert bot._history == []

    def test_system_prompt_included_in_messages(self):
        bot = Chatbot({"api_key": "sk-test", "system_prompt": "You are a test bot."})
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = self._make_mock_response("ok")
        bot._client = mock_client
        bot._initialised = True

        bot.chat("Hello")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a test bot."

    def test_initialise_without_api_key_leaves_client_none(self):
        bot = Chatbot({})
        with patch("heybuddy.chatbot.Chatbot._initialise", wraps=bot._initialise):
            bot._initialise()
        assert bot._client is None
