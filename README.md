# HeyBuddy 🎙️

A Python-based voice assistant, chatbot, and home automation tool designed to run on a Raspberry Pi. Say **"Hey Buddy"** to wake it up, speak your command, and control your smart home or have a conversation powered by AI.

---

## Features

- 🎤 **Wake Word Detection** — Always-on wake word detection via [openWakeWord](https://github.com/dscripka/openWakeWord) (fully open-source, Apache 2.0 — runs efficiently on Raspberry Pi)
- 🗣️ **Offline Speech-to-Text** — Transcribes commands using [Vosk](https://alphacephei.com/vosk/) (no cloud required for STT)
- 🔊 **Text-to-Speech** — Speaks responses using [ElevenLabs](https://elevenlabs.io/) (high-quality AI voices) with [pyttsx3](https://pyttsx3.readthedocs.io/) as an offline fallback
- 🤖 **AI Chatbot** — Natural language conversations via [OpenAI GPT](https://openai.com/api/)
- 🏠 **Google Home / Nest Control** — Send commands to Google Home devices via the Google Assistant SDK
- 🌡️ **Nest Device Access** — Control Nest thermostats and cameras via the Google Nest SDM API
- 🏡 **Home Assistant** — Local smart home control via the [Home Assistant](https://www.home-assistant.io/) REST API
- 🧠 **Intent Parser** — Routes commands to the right handler (home automation vs. chatbot)

---

## Hardware Requirements

- Raspberry Pi 4 (recommended) or Raspberry Pi 3B+
- USB microphone or USB sound card with microphone
- Speaker (USB, 3.5mm, or Bluetooth)
- MicroSD card (16 GB+, Class 10)
- Raspberry Pi OS (Bullseye or later, 64-bit recommended)
- Internet connection (for OpenAI and Google APIs)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/RobbeG-immalle/HeyBuddy.git
cd HeyBuddy
```

### 2. Run the setup script

This installs all system-level dependencies (PortAudio, Python audio libs, etc.):

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Create a Python virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
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

### 5. Configure HeyBuddy

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your API keys and settings (see [Configuration](#configuration) below).

---

## Configuration

All settings live in `config.yaml` (gitignored for security). Copy `config.example.yaml` and fill in your values.

### Wake Word

```yaml
wake_word:
  model_path: null    # Path to custom .tflite/.onnx model, or null for default pre-trained models
  threshold: 0.5      # 0.0–1.0 (higher = fewer false positives, lower = more sensitive)
```

openWakeWord is fully open-source (Apache 2.0) and requires no account or API key.
Pre-trained models are downloaded automatically on first use.
You can also [train a custom wake word model](https://github.com/dscripka/openWakeWord#training-new-models) and point `model_path` at the resulting `.tflite` or `.onnx` file.

### Speech Recognition

```yaml
speech_recognition:
  model_path: "models/vosk-model-en-us"
  sample_rate: 16000
  listen_timeout: 10             # seconds to wait for speech after wake word
```

### Text-to-Speech

HeyBuddy uses [ElevenLabs](https://elevenlabs.io/) for high-quality, character-appropriate voices, with [pyttsx3](https://pyttsx3.readthedocs.io/) as an offline fallback.

```yaml
tts:
  # Engine: "elevenlabs" (recommended) or "pyttsx3" (offline fallback)
  engine: "elevenlabs"

  # ElevenLabs settings
  elevenlabs_api_key: "YOUR_ELEVENLABS_API_KEY"
  elevenlabs_voice_id: "Rachel"            # default voice (overridden per skin)
  elevenlabs_model: "eleven_multilingual_v2"  # or "eleven_turbo_v2_5" for faster responses

  # pyttsx3 fallback settings
  rate: 175    # words per minute
  volume: 1.0  # 0.0–1.0
  voice_id: null
```

#### Getting an ElevenLabs API key

1. Go to [https://elevenlabs.io/](https://elevenlabs.io/) and create a free account.
2. Navigate to **Profile → API Keys** and copy your key.
3. Paste it into `config.yaml` under `tts.elevenlabs_api_key`.

> **Free tier:** 10,000 characters/month ≈ 10–15 minutes of speech — more than enough for testing and light daily use.  Check [ElevenLabs pricing](https://elevenlabs.io/pricing) for current limits.

#### Choosing voices

Browse available voices at [https://elevenlabs.io/voices](https://elevenlabs.io/voices).  Each skin has a recommended voice pre-configured in `config.example.yaml`:

| Skin | Character | Recommended voice |
|---|---|---|
| `default` | Buddy | Rachel |
| `lobster` | Larry the Lobster | Adam |
| `pickle` | Pete the Pickle | Antoni |
| `robot` | Unit-7 | Arnold |
| `ghost` | Whisper | Bella |

Override the voice for any skin by setting `elevenlabs_voice_id` under that skin's config:

```yaml
skins:
  lobster:
    elevenlabs_voice_id: "Adam"   # or any other ElevenLabs voice name/ID
```

#### Offline fallback (pyttsx3)

If `engine` is set to `"pyttsx3"`, or if ElevenLabs is unavailable (no API key, no internet connection, or the `elevenlabs` package is not installed), HeyBuddy automatically falls back to pyttsx3.  A fresh pyttsx3 engine is created for every `speak()` call to avoid the Windows silent-after-first-call bug.

### OpenAI Chatbot

```yaml
chatbot:
  api_key: "YOUR_OPENAI_API_KEY"
  model: "gpt-4o-mini"
  max_tokens: 256
  system_prompt: "You are HeyBuddy, a helpful voice assistant on a Raspberry Pi."
```

### Google Home / Assistant

```yaml
google_assistant:
  credentials_file: "credentials.json"
  device_model_id: "your-device-model-id"
  device_instance_id: "your-device-instance-id"
```

### Google Nest SDM API

```yaml
nest_sdm:
  project_id: "YOUR_NEST_PROJECT_ID"
  client_id: "YOUR_CLIENT_ID"
  client_secret: "YOUR_CLIENT_SECRET"
  refresh_token: "YOUR_REFRESH_TOKEN"
```

Follow the [Google Nest Device Access guide](https://developers.google.com/nest/device-access/get-started) to obtain these credentials.

### Home Assistant

```yaml
home_assistant:
  base_url: "http://homeassistant.local:8123"
  token: "YOUR_LONG_LIVED_ACCESS_TOKEN"
```

---

## Skins & Personalities

HeyBuddy supports swappable character "skins" — each one changes the AI's personality, voice, speech rate, and startup greeting.  Think of them as collectible companion characters: a salty lobster, a chaotic pickle, a logical robot, or a melancholy ghost.

### What is a skin?

A skin is a named profile in `config.yaml` that defines:

| Key | Description |
|---|---|
| `name` | Display name (e.g. `"Larry the Lobster"`) |
| `system_prompt` | GPT personality prompt for this character |
| `elevenlabs_voice_id` | ElevenLabs voice ID or name for this skin (e.g. `"Adam"`) |
| `voice_id` | pyttsx3 voice ID for offline fallback, or `null` for the system default |
| `wake_word_model` | Path to a custom openWakeWord model, or `null` for default |
| `tts_rate` | Words per minute override for the pyttsx3 fallback (e.g. `175`) |
| `greeting` | What the character says when HeyBuddy starts up |

### Switching skins

Change the `active_skin` key in your `config.yaml` and restart HeyBuddy:

```yaml
# Change "default" to any skin key defined under "skins:"
active_skin: "lobster"
```

HeyBuddy will greet you as the new character and use their personality for all responses.

### Built-in example skins

`config.example.yaml` includes five ready-to-use skins:

| Key | Character | Style |
|---|---|---|
| `default` | Buddy | Friendly, helpful assistant |
| `lobster` | Larry the Lobster | Salty, sarcastic, ocean puns |
| `pickle` | Pete the Pickle | Chaotic, philosophical absurdist |
| `robot` | Unit-7 | Logical, precise, slightly condescending |
| `ghost` | Whisper | Soft-spoken, poetic, existential |

### Creating a custom skin

Add a new entry under `skins:` in your `config.yaml`:

```yaml
active_skin: "wizard"

skins:
  wizard:
    name: "Merlin"
    system_prompt: >
      You are Merlin, an ancient and wise wizard companion. You speak in riddles
      and make references to ancient lore. You find modern technology baffling
      but fascinating. Keep answers short — you're spoken aloud.
    elevenlabs_voice_id: "Josh"   # or any ElevenLabs voice ID
    voice_id: null                # pyttsx3 fallback voice, or null for system default
    wake_word_model: null         # or path to a custom .tflite/.onnx wake word model
    tts_rate: 155
    greeting: "Ah, you have summoned me once more. What wisdom do you seek?"
```

### Future: NFC-based skin switching

The skin system is designed with hardware in mind.  A planned enhancement will read an NFC tag embedded in each physical shell and automatically call `SkinManager.switch_skin()` when a new skin is snapped on, instantly changing the personality without any manual config changes.

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
├── setup.sh                         # Raspberry Pi system setup
├── heybuddy/
│   ├── __init__.py
│   ├── assistant.py                 # Main orchestrator loop
│   ├── wake_word.py                 # openWakeWord wake word detection
│   ├── speech_recognition.py        # Vosk offline STT
│   ├── tts.py                       # ElevenLabs TTS (pyttsx3 fallback)
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

- Run `arecord -l` to list recording devices
- Set the correct device in `config.yaml` under `speech_recognition.device_index`
- Ensure your microphone is not muted: `alsamixer`

### Wake word not triggering

- Lower `wake_word.threshold` (e.g., `0.3`) to make detection more sensitive
- Speak clearly and close to the microphone
- If using a custom model, verify the `model_path` points to a valid `.tflite` or `.onnx` file

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

