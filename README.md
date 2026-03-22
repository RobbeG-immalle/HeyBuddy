# HeyBuddy 🎙️

A Python-based voice assistant, chatbot, and home automation tool. Say **"Hey Buddy"** to wake it up, speak your command, and have a conversation powered by AI — or optionally control your smart home.

HeyBuddy runs on a **Raspberry Pi** *or* any **desktop PC** (Linux / macOS / Windows) that has a microphone and speakers. **No Google Nest, Google Home, or any other smart-home hardware is required** — those integrations are entirely optional.

---

## Features

- 🎤 **Wake Word Detection** — Always-on "Hey Buddy" detection via [Picovoice Porcupine](https://picovoice.ai/products/porcupine/)
- 🗣️ **Offline Speech-to-Text** — Transcribes commands using [Vosk](https://alphacephei.com/vosk/) (no cloud required for STT)
- 🔊 **Text-to-Speech** — Speaks responses using [pyttsx3](https://pyttsx3.readthedocs.io/)
- 🤖 **AI Chatbot** — Natural language conversations via [OpenAI GPT](https://openai.com/api/)
- 🏠 **Google Home / Nest Control** *(optional)* — Send commands to Google Home devices via the Google Assistant SDK
- 🌡️ **Nest Device Access** *(optional)* — Control Nest thermostats and cameras via the Google Nest SDM API
- 🏡 **Home Assistant** *(optional)* — Local smart home control via the [Home Assistant](https://www.home-assistant.io/) REST API
- 🧠 **Intent Parser** — Routes commands to the right handler (home automation vs. chatbot)

---

## Platform Support

HeyBuddy works anywhere Python 3.9+ runs. The core features (wake word → speech-to-text → chatbot → text-to-speech) only need a **microphone** and **speakers/headset** — no special hardware.

| Platform | Status | Notes |
|---|---|---|
| **Raspberry Pi 4 / 3B+** | ✅ Fully supported | Recommended for always-on use |
| **Linux desktop/laptop** | ✅ Fully supported | Any distro with ALSA/PulseAudio |
| **macOS** | ✅ Fully supported | Uses the built-in CoreAudio |
| **Windows** | ✅ Fully supported | Uses the default audio devices |

### Do I need a Google Nest or Google Home?

**No.** Google Nest and Google Home integrations are **completely optional**. If you only want a voice-controlled AI chatbot, you just need:

1. A Picovoice access key (free) — for wake word detection
2. An OpenAI API key — for the GPT chatbot
3. A microphone and speaker/headset

Leave the `google_assistant`, `nest_sdm`, and `home_assistant` sections out of your `config.yaml` (or keep the placeholder values) and HeyBuddy will work as a standalone voice assistant.

---

## Hardware Requirements

### Raspberry Pi (always-on assistant)

- Raspberry Pi 4 (recommended) or Raspberry Pi 3B+
- USB microphone or USB sound card with microphone
- Speaker (USB, 3.5mm, or Bluetooth)
- MicroSD card (16 GB+, Class 10)
- Raspberry Pi OS (Bullseye or later, 64-bit recommended)
- Internet connection (for OpenAI API)

### Desktop / Laptop (testing or daily use)

- Any computer running Linux, macOS, or Windows
- Built-in or USB microphone
- Speakers or headset
- Python 3.9+
- Internet connection (for OpenAI API)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/RobbeG-immalle/HeyBuddy.git
cd HeyBuddy
```

### 2. Install system-level dependencies

#### Raspberry Pi / Debian / Ubuntu

```bash
chmod +x setup.sh
./setup.sh
```

#### macOS

```bash
brew install portaudio espeak
```

#### Windows

No extra system packages are needed — PyAudio ships with pre-built wheels on Windows.

### 3. Create a Python virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate          # Windows (cmd)
# venv\Scripts\Activate.ps1      # Windows (PowerShell)
pip install -r requirements.txt
```

### 4. Download the Vosk speech model

```bash
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk-model-en-us
cd ..
```

> **Tip:** On Windows you can download and unzip the model manually from <https://alphacephei.com/vosk/models>.

### 5. Configure HeyBuddy

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your API keys and settings (see [Configuration](#configuration) below).

> **Minimal config** — for a PC-only chatbot you only need the `wake_word`, `speech_recognition`, `tts`, and `chatbot` sections. The `google_assistant`, `nest_sdm`, and `home_assistant` sections can be left blank or removed entirely.

---

## Configuration

All settings live in `config.yaml` (gitignored for security). Copy `config.example.yaml` and fill in your values.

### Wake Word

```yaml
wake_word:
  keyword: "hey buddy"           # Porcupine built-in keyword or path to .ppn file
  sensitivity: 0.5               # 0.0–1.0 (higher = more sensitive, more false positives)
  access_key: "YOUR_PICOVOICE_ACCESS_KEY"
```

Get a free Picovoice access key at [https://console.picovoice.ai/](https://console.picovoice.ai/).

### Speech Recognition

```yaml
speech_recognition:
  model_path: "models/vosk-model-en-us"
  sample_rate: 16000
  listen_timeout: 10             # seconds to wait for speech after wake word
```

### Text-to-Speech

```yaml
tts:
  rate: 175                      # words per minute
  volume: 1.0                    # 0.0–1.0
  voice_id: null                 # null = system default; set to a specific voice ID if needed
```

### OpenAI Chatbot

```yaml
chatbot:
  api_key: "YOUR_OPENAI_API_KEY"
  model: "gpt-4o-mini"
  max_tokens: 256
  system_prompt: "You are HeyBuddy, a helpful voice assistant on a Raspberry Pi."
```

### Google Home / Assistant *(optional)*

Only needed if you have Google Home devices you want to control by voice.

```yaml
google_assistant:
  credentials_file: "credentials.json"
  device_model_id: "your-device-model-id"
  device_instance_id: "your-device-instance-id"
```

### Google Nest SDM API *(optional)*

Only needed if you have Nest thermostats or cameras.

```yaml
nest_sdm:
  project_id: "YOUR_NEST_PROJECT_ID"
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  refresh_token: "YOUR_REFRESH_TOKEN"
```

Follow the [Google Nest Device Access guide](https://developers.google.com/nest/device-access/get-started) to obtain these credentials.

### Home Assistant *(optional)*

Only needed if you run a [Home Assistant](https://www.home-assistant.io/) instance.

```yaml
home_assistant:
  base_url: "http://homeassistant.local:8123"
  token: "YOUR_LONG_LIVED_ACCESS_TOKEN"
```

---

## Usage

Start HeyBuddy:

```bash
source venv/bin/activate
python main.py
```

Or with a custom config file:

```bash
python main.py --config /path/to/config.yaml
```

### Testing on Your PC

You do **not** need a Raspberry Pi to try HeyBuddy. Any computer with a microphone and speakers (or headset) will work:

1. Install the system dependencies for your OS (see [Installation](#installation) above).
2. Create a `config.yaml` with only the required sections — `wake_word`, `speech_recognition`, `tts`, and `chatbot`.
3. Run `python main.py` and say **"Hey Buddy"** followed by a question (e.g. *"Tell me a joke"*).

All chatbot features work on any platform. Home automation commands will simply be skipped if the corresponding integration is not configured.

### Voice Commands

Once running, say **"Hey Buddy"** followed by a command:

| Command example | Action |
|---|---|
| "Turn on the living room lights" | Home automation — Google Home / Home Assistant |
| "Set the thermostat to 21 degrees" | Nest SDM thermostat control |
| "What's the temperature inside?" | Nest SDM sensor query |
| "Turn off all lights" | Home automation broadcast |
| "Tell me a joke" | OpenAI GPT chatbot |
| "What's the weather like?" | OpenAI GPT chatbot |

---

## Project Structure

```
HeyBuddy/
├── main.py                          # Entry point
├── config.example.yaml              # Example configuration
├── requirements.txt                 # Python dependencies
├── setup.sh                         # Linux system setup (Raspberry Pi & desktop)
├── heybuddy/
│   ├── __init__.py
│   ├── assistant.py                 # Main orchestrator loop
│   ├── wake_word.py                 # Porcupine wake word detection
│   ├── speech_recognition.py        # Vosk offline STT
│   ├── tts.py                       # pyttsx3 text-to-speech
│   ├── chatbot.py                   # OpenAI GPT integration
│   ├── intent.py                    # Intent parser (routes commands)
│   ├── config.py                    # YAML config loader
│   └── home_automation/
│       ├── __init__.py
│       ├── google_assistant.py      # Google Assistant SDK
│       ├── home_assistant.py        # Home Assistant REST API
│       └── nest_sdm.py              # Google Nest Device Access API
└── tests/
    ├── __init__.py
    ├── test_intent.py
    ├── test_chatbot.py
    └── test_home_automation.py
```

---

## Running Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

---

## Troubleshooting

### No audio input detected

- **Linux:** Run `arecord -l` to list recording devices
- **macOS / Windows:** Check your system sound settings to ensure the correct input device is selected
- Set the correct device in `config.yaml` under `speech_recognition.device_index`
- Ensure your microphone is not muted

### Wake word not triggering

- Increase `wake_word.sensitivity` (e.g., `0.7`)
- Check your Picovoice access key is valid
- Speak clearly and close to the microphone

### "ALSA lib" errors in terminal

These are harmless ALSA warnings from PortAudio. Suppress them by running:
```bash
python main.py 2>/dev/null
```

### OpenAI API errors

- Verify your API key in `config.yaml`
- Check you have sufficient OpenAI credits at [https://platform.openai.com/usage](https://platform.openai.com/usage)

### Nest / Google Home not responding

- Ensure your `credentials.json` is valid and not expired
- Re-run the OAuth flow if the refresh token has expired
- Check that your Google account has the correct permissions for Device Access

---

## Contributing

Pull requests are welcome! Please open an issue first to discuss proposed changes.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

