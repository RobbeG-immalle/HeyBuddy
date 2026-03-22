"""tests/test_intent.py — Unit tests for the intent parser."""

import pytest

from heybuddy.intent import (
    Intent,
    extract_home_automation_action,
    parse_intent,
)


class TestParseIntent:
    """Tests for parse_intent()."""

    # Home automation commands
    def test_turn_on_lights(self):
        intent, text = parse_intent("turn on the living room lights")
        assert intent == Intent.HOME_AUTOMATION
        assert "turn on" in text

    def test_turn_off_lights(self):
        intent, _ = parse_intent("turn off the bedroom lights")
        assert intent == Intent.HOME_AUTOMATION

    def test_set_thermostat(self):
        intent, _ = parse_intent("set the thermostat to 21 degrees")
        assert intent == Intent.HOME_AUTOMATION

    def test_dim_lights(self):
        intent, _ = parse_intent("dim the kitchen lights")
        assert intent == Intent.HOME_AUTOMATION

    def test_lock_door(self):
        intent, _ = parse_intent("lock the front door")
        assert intent == Intent.HOME_AUTOMATION

    def test_play_music(self):
        intent, _ = parse_intent("play some music")
        assert intent == Intent.HOME_AUTOMATION

    def test_nest_keyword(self):
        intent, _ = parse_intent("what is the temperature on the nest")
        assert intent == Intent.HOME_AUTOMATION

    def test_google_home_keyword(self):
        intent, _ = parse_intent("ask google home to turn on the lights")
        assert intent == Intent.HOME_AUTOMATION

    # Chatbot commands
    def test_chatbot_joke(self):
        intent, _ = parse_intent("tell me a joke")
        assert intent == Intent.CHATBOT

    def test_chatbot_weather(self):
        intent, _ = parse_intent("what's the weather forecast for tomorrow")
        assert intent == Intent.CHATBOT

    def test_chatbot_general(self):
        intent, _ = parse_intent("how do I make pasta?")
        assert intent == Intent.CHATBOT

    def test_chatbot_greeting(self):
        intent, _ = parse_intent("hello, how are you?")
        assert intent == Intent.CHATBOT

    # Edge cases
    def test_empty_string(self):
        intent, text = parse_intent("")
        assert intent == Intent.UNKNOWN
        assert text == ""

    def test_whitespace_only(self):
        intent, text = parse_intent("   ")
        assert intent == Intent.UNKNOWN
        assert text == ""

    def test_normalises_to_lowercase(self):
        _, text = parse_intent("TURN ON THE LIGHTS")
        assert text == text.lower()


class TestExtractHomeAutomationAction:
    """Tests for extract_home_automation_action()."""

    def test_turn_on_verb(self):
        result = extract_home_automation_action("turn on the living room lights")
        assert result["verb"] == "turn on"

    def test_turn_off_verb(self):
        result = extract_home_automation_action("turn off the fan")
        assert result["verb"] == "turn off"

    def test_set_temperature_extracts_value(self):
        result = extract_home_automation_action("set the thermostat to 22 degrees")
        assert result["verb"] == "set"
        assert result["value"] == "22"

    def test_dim_verb(self):
        result = extract_home_automation_action("dim the lights to 30 percent")
        assert result["verb"] == "dim"
        assert result["value"] == "30"

    def test_no_verb_still_returns_target(self):
        result = extract_home_automation_action("living room lights")
        assert result["verb"] is None
        assert result["target"] is not None

    def test_target_contains_remainder(self):
        result = extract_home_automation_action("turn on the kitchen fan")
        assert "kitchen fan" in result["target"]
