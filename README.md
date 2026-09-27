# Rubber Ducky 🦆

Local voice conversation system with WhisperX transcription, Coqui XTTS v2 voice cloning, and configurable LLMs (Claude API or Ollama).

**Status:** 🚧 In Development - Phase 5 Complete (Audio + Transcription + TTS + LLM)

## Features

- **Fully Local Processing**: All audio processing happens on your machine (except LLM when using Claude API)
- **Voice Cloning**: Clone any voice with just a 6-second audio sample (Coqui XTTS v2)
- **Speaker Diarization**: Identify who's speaking when in multi-person conversations (WhisperX + pyannote.audio)
- **Real-time Conversation**: Voice activity detection for natural turn-taking
- **Barge-in Support**: Interrupt the assistant mid-sentence
- **Configurable LLM**: Choose between Claude API (best quality) or Ollama (fully local)
- **Privacy-First**: No cloud processing except optional Claude API calls
- **MCP Server**: Use voice I/O directly in Claude Code (listen and speak tools)

## Requirements

- **Python**: 3.10-3.14 (3.10 recommended)
- **OS**: macOS, Linux, or Windows
- **GPU**: Recommended for fast inference (CUDA-compatible)
- **Disk**: ~3 GB for models (WhisperX + XTTS v2)
- **RAM**: 8 GB minimum, 16 GB recommended

## Quick Start

### 1. Installation

```bash
# Clone or navigate to rubber-ducky directory
cd ~/dev/rubber-ducky

# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# CRITICAL: Install PyTorch FIRST
pip install torch torchvision torchaudio

# Install WhisperX (pulls PyTorch-compatible versions)
pip install whisperx

# Install remaining dependencies
pip install -r requirements.txt

# Install rubber-ducky in editable mode
pip install -e .
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Claude API key (or configure Ollama)
nano .env
```

**Minimum .env configuration:**
```bash
RUBBER_DUCKY_CLAUDE_API_KEY=your_api_key_here
# or for Ollama:
# RUBBER_DUCKY_LLM_PROVIDER=ollama
```

### 3. Setup

```bash
# Run setup to check dependencies and download models
rubber-ducky setup
```

### 4. (Optional) Clone Your Voice

```bash
# Record a 6-10 second voice sample, then:
rubber-ducky clone-voice --sample ~/voice.wav --name "YourName"
```

### 5. Start Conversation

```bash
# Start talking!
rubber-ducky converse

# Or specify options:
rubber-ducky converse --provider ollama
rubber-ducky converse --voice ~/my-voice.wav
```

## Usage Modes

### 1. Standalone Voice Conversation

```bash
# Start voice conversation
rubber-ducky converse

# Initial setup and model download
rubber-ducky setup

# Clone a voice from audio sample
rubber-ducky clone-voice --sample voice.wav --name Troy

# List audio devices
rubber-ducky devices

# View configuration
rubber-ducky config
```

### 2. MCP Server (Claude Code Integration)

Use voice I/O directly in Claude Code:

```bash
# Start MCP server (Claude Code manages this automatically)
rubber-ducky-mcp
```

**Setup:** See [MCP_SETUP.md](MCP_SETUP.md) for configuration

**Tools exposed:**
- `listen_and_transcribe()` - Capture audio and return transcribed text
- `speak(text)` - Convert text to speech and play it
- `status()` - Check if voice I/O is ready

**Examples:** See [MCP_EXAMPLES.md](MCP_EXAMPLES.md) for real-world usage

## Configuration

Configuration is managed through:
1. **Environment variables** (`.env` file)
2. **YAML config** (`config.yaml`)
3. **Command-line options**

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RUBBER_DUCKY_LLM_PROVIDER` | `claude` | `claude` or `ollama` |
| `RUBBER_DUCKY_CLAUDE_API_KEY` | (required) | Your Anthropic API key |
| `RUBBER_DUCKY_WHISPER_MODEL` | `base` | `tiny`, `base`, `small`, `medium`, `large` |
| `RUBBER_DUCKY_XTTS_VOICE_SAMPLE` | (optional) | Path to cloned voice sample |

See `.env.example` and `config.yaml.example` for all options.

## Architecture

```
Microphone → VAD → WhisperX → LLM → XTTS v2 → Speaker
                ↑              ↓
            Turn-taking    Claude/Ollama
```

**Components:**
- **VAD** (Silero VAD): Detects when you start/stop speaking
- **WhisperX**: Transcribes speech with speaker labels (70x realtime)
- **LLM**: Generates responses (Claude API or Ollama)
- **XTTS v2**: Converts text to speech with your cloned voice
- **Turn Manager**: Handles conversation flow and interruptions

## Development Status

- [x] **Phase 1: Foundation** ✅ Complete
  - [x] Project structure
  - [x] Configuration system (Pydantic Settings)
  - [x] Database models (SQLAlchemy)
  - [x] CLI commands (Click)
  - [x] MCP server for Claude Code integration

- [x] **Phase 2: Audio Pipeline** ✅ Complete
  - [x] Audio capture (sounddevice)
  - [x] Audio playback
  - [x] VAD integration (Silero VAD + energy fallback)

- [x] **Phase 3: Transcription** ✅ Complete
  - [x] WhisperX integration
  - [x] Word-level timestamps
  - [x] Diarization support (optional)

- [x] **Phase 4: TTS** ✅ Complete
  - [x] XTTS v2 integration
  - [x] Voice cloning workflow
  - [x] Speech synthesis with cloned voices

- [x] **Phase 5: LLM** ✅ Complete
  - [x] LLM abstraction layer
  - [x] Claude provider (Anthropic API)
  - [x] Ollama provider (local models)
  - [x] Multi-turn conversations
  - [x] Streaming support

- [ ] **Phase 6: Integration**
  - [ ] Conversation engine
  - [ ] State machine
  - [ ] End-to-end testing

- [ ] **Phase 7: Polish**
  - [ ] Error handling
  - [ ] Documentation
  - [ ] Performance optimization

## Project Structure

```
rubber-ducky/
├── rubber_ducky/           # Main package
│   ├── cli/               # Click CLI commands
│   ├── conversation/      # Conversation engine & state machine
│   ├── audio/             # Audio I/O (capture, playback, VAD)
│   ├── transcription/     # WhisperX integration
│   ├── tts/              # Coqui XTTS v2 integration
│   ├── llm/              # LLM abstraction (Claude + Ollama)
│   ├── storage/          # SQLite database
│   └── config.py         # Pydantic Settings
├── data/                 # Local storage (auto-created)
│   ├── conversations.db  # SQLite database
│   ├── voice_samples/    # Cloned voices
│   └── models/           # Downloaded models cache
├── .env                  # Configuration (gitignored)
├── requirements.txt      # Python dependencies
└── setup.py             # Package setup
```

## License & Usage

**Code:** MIT License

**Models:**
- **Coqui XTTS v2**: Non-commercial use only (CPML license)
- **WhisperX**: MIT License
- **Silero VAD**: MIT License

**For commercial use**, replace XTTS v2 with:
- OpenAI TTS API
- ElevenLabs API
- Other commercial TTS solutions

## Troubleshooting

### "No module named torch"
Install PyTorch first: `pip install torch torchvision torchaudio`

### "CUDA not available"
XTTS and WhisperX will still work on CPU, just slower. For best performance, use a CUDA-compatible GPU.

### "Claude API key not configured"
Set `RUBBER_DUCKY_CLAUDE_API_KEY` in `.env` file, or switch to Ollama:
```bash
RUBBER_DUCKY_LLM_PROVIDER=ollama
```

### "No audio devices found"
Check your microphone and speakers are connected. Run `rubber-ducky devices` to list available devices.

## Contributing

This is a personal project, but suggestions and bug reports are welcome via issues.

## Credits

Built with:
- [WhisperX](https://github.com/m-bain/whisperx) - Fast speech recognition
- [Coqui TTS](https://github.com/idiap/coqui-ai-TTS) - Voice cloning
- [Silero VAD](https://github.com/snakers4/silero-vad) - Voice activity detection
- [Anthropic Claude](https://www.anthropic.com/) - LLM API
- [Ollama](https://ollama.ai/) - Local LLM runtime
