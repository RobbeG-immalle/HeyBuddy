#!/usr/bin/env bash
# setup.sh — Install system dependencies for HeyBuddy.
# Works on Raspberry Pi OS, Debian/Ubuntu, and macOS.
set -euo pipefail

echo "=== HeyBuddy System Setup ==="

# ------------------------------------------------------------------
# Detect platform
# ------------------------------------------------------------------
OS="$(uname -s)"

case "$OS" in
    Linux)
        if command -v apt-get &> /dev/null; then
            echo "Detected Debian/Ubuntu/Raspberry Pi OS — using apt-get"

            # Update package index
            sudo apt-get update -y

            # PortAudio (required by PyAudio)
            sudo apt-get install -y portaudio19-dev

            # Python audio bindings
            sudo apt-get install -y python3-pyaudio

            # espeak and libespeak (required by pyttsx3 on Linux)
            sudo apt-get install -y espeak libespeak-dev

            # Additional audio utilities (alsa, etc.)
            sudo apt-get install -y alsa-utils libasound2-dev

            # Build tools (needed to compile some Python packages)
            sudo apt-get install -y build-essential python3-dev python3-pip python3-venv

            # wget + unzip for downloading the Vosk model
            sudo apt-get install -y wget unzip
        else
            echo "Non-Debian Linux detected. Please install the following packages manually:"
            echo "  - portaudio development headers (portaudio19-dev or portaudio-devel)"
            echo "  - espeak and libespeak-dev"
            echo "  - Python 3 development headers and venv"
            echo "  - alsa-utils and libasound2-dev"
            exit 1
        fi
        ;;
    Darwin)
        echo "Detected macOS"
        if ! command -v brew &> /dev/null; then
            echo "Homebrew is required but not installed."
            echo "Install it from https://brew.sh/ and re-run this script."
            exit 1
        fi
        brew install portaudio espeak
        echo "(Python 3 and pip are expected to be installed already)"
        ;;
    *)
        echo "Unsupported OS: $OS"
        echo "On Windows, no extra system packages are required — PyAudio"
        echo "ships with pre-built wheels. Just run:"
        echo "  pip install -r requirements.txt"
        exit 1
        ;;
esac

echo ""
echo "=== System dependencies installed successfully ==="
echo ""
echo "Next steps:"
echo "  1. python3 -m venv venv"
echo "  2. source venv/bin/activate"
echo "  3. pip install -r requirements.txt"
echo "  4. Download a Vosk model into models/ (see README.md)"
echo "  5. cp config.example.yaml config.yaml  (and fill in your API keys)"
echo "  6. python main.py"
