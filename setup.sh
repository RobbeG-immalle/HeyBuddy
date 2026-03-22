#!/usr/bin/env bash
# setup.sh — Install system dependencies for HeyBuddy on Raspberry Pi OS
set -euo pipefail

echo "=== HeyBuddy System Setup ==="

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
