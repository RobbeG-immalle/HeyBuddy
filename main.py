"""
main.py — Entry point for HeyBuddy voice assistant.

Usage:
    python main.py [--config CONFIG_PATH]
"""

import argparse
import logging
import sys

from heybuddy.assistant import Assistant
from heybuddy.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HeyBuddy — Python voice assistant (works on Raspberry Pi, Linux, macOS, and Windows)"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to the YAML configuration file (default: config.yaml)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger.info("Loading configuration from %s", args.config)
    config = load_config(args.config)

    assistant = Assistant(config)
    try:
        logger.info("Starting HeyBuddy assistant — say 'Hey Buddy' to begin!")
        assistant.run()
    except KeyboardInterrupt:
        logger.info("Shutting down HeyBuddy. Goodbye!")
    finally:
        assistant.cleanup()


if __name__ == "__main__":
    main()
