"""
heybuddy/config.py — YAML configuration loader.
"""

import logging
import os
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)

# Keys whose values should be populated from environment variables when the
# placeholder string is still present (useful for CI / container deployments).
_ENV_OVERRIDES: Dict[str, str] = {
    "chatbot.api_key": "OPENAI_API_KEY",
    "wake_word.access_key": "PICOVOICE_ACCESS_KEY",
    "nest_sdm.client_id": "NEST_CLIENT_ID",
    "nest_sdm.client_secret": "NEST_CLIENT_SECRET",
    "nest_sdm.refresh_token": "NEST_REFRESH_TOKEN",
    "home_assistant.token": "HOME_ASSISTANT_TOKEN",
}


def _deep_get(data: Dict[str, Any], dotted_key: str) -> Any:
    """Retrieve a nested value using a dot-separated key path."""
    keys = dotted_key.split(".")
    node = data
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _deep_set(data: Dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set a nested value using a dot-separated key path."""
    keys = dotted_key.split(".")
    node = data
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from *path* and apply environment variable overrides.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A nested dictionary with the merged configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Configuration file not found: {path}\n"
            "Copy config.example.yaml to config.yaml and fill in your values."
        )

    with open(path, "r", encoding="utf-8") as fh:
        config: Dict[str, Any] = yaml.safe_load(fh) or {}

    logger.debug("Loaded configuration from %s", path)

    # Apply environment variable overrides for sensitive keys.
    for dotted_key, env_var in _ENV_OVERRIDES.items():
        env_value = os.environ.get(env_var)
        if env_value:
            _deep_set(config, dotted_key, env_value)
            logger.debug("Applied env override %s -> %s", env_var, dotted_key)

    return config
