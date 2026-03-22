"""tests/test_skin_manager.py — Unit tests for the skin manager module."""

import pytest

from heybuddy.skin_manager import SkinManager, _DEFAULT_SKIN

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

_SAMPLE_CONFIG = {
    "active_skin": "lobster",
    "skins": {
        "lobster": {
            "name": "Larry the Lobster",
            "system_prompt": "You are Larry.",
            "voice_id": None,
            "wake_word_model": None,
            "tts_rate": 175,
            "greeting": "Ahoy landlubber!",
        },
        "pickle": {
            "name": "Pete the Pickle",
            "system_prompt": "You are Pete.",
            "voice_id": None,
            "wake_word_model": None,
            "tts_rate": 190,
            "greeting": "I'm a pickle.",
        },
        "default": {
            "name": "Buddy",
            "system_prompt": "You are HeyBuddy.",
            "voice_id": None,
            "wake_word_model": None,
            "tts_rate": 175,
            "greeting": "HeyBuddy is ready.",
        },
    },
}


class TestSkinManagerInit:
    """Tests for SkinManager initialisation."""

    def test_active_skin_set_from_config(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        assert mgr._active_skin_name == "lobster"

    def test_active_skin_defaults_to_default_when_missing(self):
        mgr = SkinManager({"skins": {"default": {"name": "Buddy"}}})
        assert mgr._active_skin_name == "default"

    def test_no_skins_section_uses_fallback(self):
        mgr = SkinManager({})
        skin = mgr.active_skin
        assert skin["name"] == _DEFAULT_SKIN["name"]

    def test_unknown_active_skin_falls_back_to_default(self):
        config = dict(_SAMPLE_CONFIG)
        config["active_skin"] = "nonexistent"
        mgr = SkinManager(config)
        assert mgr._active_skin_name == "default"


class TestSkinManagerActiveSkin:
    """Tests for the active_skin property."""

    def test_returns_correct_skin_config(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        skin = mgr.active_skin
        assert skin["name"] == "Larry the Lobster"
        assert skin["greeting"] == "Ahoy landlubber!"

    def test_active_skin_fills_missing_keys_from_defaults(self):
        """A skin with only a 'name' should have all default keys filled in."""
        config = {
            "active_skin": "minimal",
            "skins": {"minimal": {"name": "Min"}},
        }
        mgr = SkinManager(config)
        skin = mgr.active_skin
        assert skin["name"] == "Min"
        assert "system_prompt" in skin
        assert "tts_rate" in skin
        assert "greeting" in skin


class TestSkinManagerSwitchSkin:
    """Tests for SkinManager.switch_skin()."""

    def test_switch_to_existing_skin(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        new_skin = mgr.switch_skin("pickle")
        assert mgr._active_skin_name == "pickle"
        assert new_skin["name"] == "Pete the Pickle"

    def test_switch_to_nonexistent_skin_falls_back_to_default(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        new_skin = mgr.switch_skin("unicorn")
        assert mgr._active_skin_name == "default"
        assert new_skin["name"] == "Buddy"

    def test_switch_returns_new_skin_config(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        result = mgr.switch_skin("lobster")
        assert result["name"] == "Larry the Lobster"


class TestSkinManagerListSkins:
    """Tests for SkinManager.list_skins()."""

    def test_returns_all_skin_names(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        names = mgr.list_skins()
        assert set(names) == {"lobster", "pickle", "default"}

    def test_empty_skins_returns_empty_list(self):
        mgr = SkinManager({})
        assert mgr.list_skins() == []


class TestSkinManagerGetSkin:
    """Tests for SkinManager.get_skin()."""

    def test_returns_skin_by_name(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        skin = mgr.get_skin("lobster")
        assert skin is not None
        assert skin["name"] == "Larry the Lobster"

    def test_returns_none_for_missing_skin(self):
        mgr = SkinManager(_SAMPLE_CONFIG)
        assert mgr.get_skin("doesnotexist") is None

    def test_returns_copy_not_reference(self):
        """Mutating the returned dict must not affect the stored config."""
        mgr = SkinManager(_SAMPLE_CONFIG)
        skin = mgr.get_skin("lobster")
        skin["name"] = "MUTATED"
        assert mgr.get_skin("lobster")["name"] == "Larry the Lobster"

    def test_returns_merged_config_with_defaults(self):
        """A skin with only a name should have all default keys present."""
        config = {
            "active_skin": "minimal",
            "skins": {"minimal": {"name": "Min"}},
        }
        mgr = SkinManager(config)
        skin = mgr.get_skin("minimal")
        assert skin is not None
        assert skin["name"] == "Min"
        assert "system_prompt" in skin
        assert "tts_rate" in skin
        assert "greeting" in skin
