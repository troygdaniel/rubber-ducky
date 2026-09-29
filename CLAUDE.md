# Rubber Ducky - Claude Project Context

## Project Overview

**rubber-ducky** is a local voice conversation system combining WhisperX (transcription + speaker diarization), Coqui XTTS v2 (TTS with voice cloning), and configurable LLMs (Claude API or Ollama). Built as a CLI-only application prioritizing privacy.

**Status:** Phase 6 Complete (Full Integration) - September 2026

## Architecture

### High-Level Flow

```
┌─────────────┐
│ Microphone  │
└──────┬──────┘
       ↓
┌─────────────┐
│   VAD       │ (Silero VAD - detects speech start/end)
│ (Silero)    │
└──────┬──────┘
       ↓
┌─────────────┐
│  WhisperX   │ (Transcription + Speaker Diarization)
│             │ 70x realtime, word-level timestamps
└──────┬──────┘
       ↓
┌─────────────┐
│     LLM     │ (Claude API or Ollama)
│ Claude/     │
│  Ollama     │
└──────┬──────┘
       ↓
┌─────────────┐
│  XTTS v2    │ (Text-to-Speech with voice cloning)
│  (Coqui)    │
└──────┬──────┘
       ↓
┌─────────────┐
│   Speaker   │
└─────────────┘
```

### State Machine (Conversation Engine)

```
LISTENING ──[VAD detects speech]──> SPEAKING
    ↑                                   │
    │                                   │
    │                          [Silence > 800ms]
    │                                   │
    │                                   ↓
PLAYING <──[TTS complete]──── PROCESSING
    │
    │
[User speaks]──> INTERRUPTION ──> SPEAKING
```

**States:**
1. **LISTENING**: Monitoring for speech (VAD active)
2. **SPEAKING**: User is speaking (accumulating audio)
3. **PROCESSING**: Transcribe → LLM → TTS pipeline
4. **PLAYING**: Playing assistant response
5. **INTERRUPTION**: User barged in (stop playback, new turn)

## Project Structure

```
rubber-ducky/
├── rubber_ducky/              # Main package
│   ├── __init__.py
│   ├── __main__.py           # Entry point for python -m rubber_ducky
│   ├── config.py             # Pydantic Settings configuration ✅
│   ├── utils.py              # Shared utilities ✅
│   │
│   ├── cli/                  # Click commands ✅
│   │   ├── __init__.py
│   │   └── commands.py       # converse, setup, clone-voice, devices, config
│   │
│   ├── conversation/         # Conversation engine (Phase 6)
│   │   ├── __init__.py
│   │   ├── engine.py         # ConversationEngine (main loop) 🚧
│   │   └── turn_manager.py  # TurnManager (turn-taking logic)
│   │
│   ├── audio/               # Audio I/O (Phase 2) ✅
│   │   ├── __init__.py
│   │   ├── capture.py       # AudioCapture (sounddevice) ✅
│   │   ├── playback.py      # AudioPlayback ✅
│   │   └── vad.py           # VADEngine (Silero VAD wrapper) ✅
│   │
│   ├── transcription/       # WhisperX (Phase 3) ✅
│   │   ├── __init__.py
│   │   └── engine.py        # TranscriptionEngine ✅
│   │
│   ├── tts/                 # Coqui XTTS v2 (Phase 4)
│   │   ├── __init__.py
│   │   └── engine.py        # TTSEngine (voice cloning)
│   │
│   ├── llm/                 # LLM abstraction (Phase 5)
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract LLMProvider interface
│   │   ├── claude.py        # ClaudeProvider (Anthropic API)
│   │   └── ollama.py        # OllamaProvider (local LLM)
│   │
│   └── storage/             # SQLite (Phase 1) ✅
│       ├── __init__.py
│       ├── database.py      # SQLAlchemy setup
│       └── models.py        # Conversation, Turn models
│
├── data/                    # Auto-created local storage
│   ├── conversations.db     # SQLite database
│   ├── voice_samples/       # Cloned voice WAV files
│   └── models/              # Downloaded models cache
│
├── .venv/                   # Python virtual environment
├── .env                     # Configuration (gitignored)
├── .env.example             # Example environment variables ✅
├── .gitignore               # ✅
├── config.yaml              # User configuration (gitignored)
├── config.yaml.example      # Example YAML config ✅
├── requirements.txt         # Python dependencies ✅
├── setup.py                 # Package setup with console_scripts ✅
├── README.md                # User documentation ✅
└── CLAUDE.md                # This file ✅
```

## Key Files

### Critical Implementation Files (Phase Order)

**Phase 1: Foundation** ✅
1. `rubber_ducky/config.py` - Pydantic Settings (all settings loaded here)
2. `rubber_ducky/storage/models.py` - SQLAlchemy models (Conversation, Turn)
3. `rubber_ducky/cli/commands.py` - Click CLI (user entry point)
4. `setup.py` - Package setup (makes `rubber-ducky` command available)

**Phase 2: Audio Pipeline** ✅
5. `rubber_ducky/audio/vad.py` - VAD wrapper (Silero VAD with energy fallback)
6. `rubber_ducky/audio/capture.py` - Audio capture (sounddevice)
7. `rubber_ducky/audio/playback.py` - Audio playback

**Phase 3-6:** WhisperX → XTTS → LLM → Integration

### Configuration System

**Settings Hierarchy:**
1. Default values in `config.py`
2. Environment variables (`.env` with `RUBBER_DUCKY_` prefix)
3. YAML config (`config.yaml`)
4. Command-line options

**Key Settings:**

```python
# rubber_ducky/config.py
class Settings(BaseSettings):
    # Paths
    data_dir: Path = Path("~/dev/rubber-ducky/data").expanduser()

    # LLM
    llm_provider: Literal["claude", "ollama"] = "claude"
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-5-20250929"

    # Audio
    sample_rate: int = 16000  # Whisper requires 16kHz

    # VAD (turn-taking)
    vad_threshold: float = 0.5
    vad_min_silence_duration: float = 0.8  # Silence before turn end

    # WhisperX
    whisper_model: str = "base"  # tiny, base, small, medium, large

    # XTTS
    xtts_voice_sample: Optional[str] = None  # Path to cloned voice
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Transcription** | WhisperX | Speech-to-text + speaker diarization (70x realtime) |
| **Diarization** | pyannote.audio | Speaker separation (bundled with WhisperX) |
| **VAD** | Silero VAD | Voice activity detection (8MB, low latency) |
| **TTS** | Coqui XTTS v2 | Voice cloning with 6-sec sample |
| **LLM** | Claude API / Ollama | Conversation responses |
| **Audio I/O** | sounddevice | Microphone capture + speaker playback |
| **CLI** | Click + Rich | Terminal interface with formatting |
| **Config** | Pydantic Settings | Settings management |
| **Storage** | SQLAlchemy + SQLite | Conversation history |
| **Package** | setuptools | Console scripts entry point |

## Dependencies

**Installation Order (CRITICAL):**

```bash
# 1. PyTorch FIRST (required by WhisperX)
pip install torch torchvision torchaudio

# 2. WhisperX (pulls PyTorch-compatible versions)
pip install whisperx

# 3. Everything else
pip install -r requirements.txt

# 4. Install package
pip install -e .
```

**Key Packages:**
- `torch>=2.2.0` - PyTorch (MUST install first)
- `whisperx>=3.1.0` - WhisperX (includes pyannote.audio)
- `coqui-tts>=0.27.5` - XTTS v2 (maintained fork: idiap/coqui-ai-TTS)
- `silero-vad>=4.0.0` - Voice Activity Detection
- `anthropic>=0.34.0` - Claude API client
- `sounddevice>=0.4.6` - Audio I/O
- `click>=8.1.7` - CLI framework
- `rich>=13.7.0` - Terminal formatting
- `pydantic-settings>=2.5.0` - Configuration
- `sqlalchemy>=2.0.0` - Database ORM
- `threading` - Built-in Python module for input handling

## Development Patterns

### Following Existing Patterns

**From Troy's whisper project:**
- Click CLI structure
- sounddevice for audio capture
- setup.py with console_scripts entry point

**From Troy's ollama-assistant:**
- Pydantic Settings for configuration
- SQLite for local storage
- LLM abstraction layer (provider pattern)

**From Troy's maildown:**
- Local data/ directory for all storage
- REST API pattern (not used here, but similar architecture)

### Code Style

- **Type hints**: Use throughout
- **Docstrings**: Google style for all classes/functions
- **Error handling**: Try/except with rich console output
- **Async**: Not needed for MVP (sequential processing acceptable)

## CLI Commands

```bash
# Start voice conversation (RECOMMENDED: use push-to-talk)
rubber-ducky converse --push-to-talk [--provider claude|ollama] [--voice FILE] [--debug]

# Voice activity detection mode (has acoustic feedback issues)
rubber-ducky converse [--provider claude|ollama] [--voice FILE] [--debug]

# Initial setup (download models, check deps)
rubber-ducky setup

# Clone voice from sample
rubber-ducky clone-voice --sample FILE --name NAME

# List audio devices
rubber-ducky devices

# View/update configuration
rubber-ducky config [--key KEY] [--value VALUE]
```

**Push-to-Talk Mode (Recommended):**
- Press ENTER once to start your turn
- Speak your message
- VAD automatically detects when you stop (silence > 0.8s)
- System processes and responds automatically
- No accessibility permissions required
- Clear visual states show what's happening (YOU/PROCESSING/ASSISTANT/WAITING)

## Implementation Phases

### Phase 1: Foundation ✅ Complete
- [x] Directory structure
- [x] requirements.txt, setup.py
- [x] config.py (Pydantic Settings)
- [x] Database models (SQLAlchemy)
- [x] CLI skeleton (Click)
- [x] README.md, CLAUDE.md

### Phase 2: Audio Pipeline ✅ Complete
- [x] audio/capture.py - AudioCapture class with queue-based capture
- [x] audio/playback.py - AudioPlayback class with blocking/async modes
- [x] audio/vad.py - VADEngine with Silero VAD + energy fallback
- [x] Test: test_audio.py - 6 comprehensive tests
- [x] Documentation: TESTING.md

### Phase 3: Transcription ✅ Complete
- [x] transcription/engine.py - WhisperX integration with lazy loading
- [x] Word-level timestamps with alignment
- [x] Speaker diarization support (optional)
- [x] File and live audio transcription
- [x] Test: test_transcription.py - 4 comprehensive tests
- [x] Format transcript with/without timestamps

### Phase 4: TTS ✅ Complete
- [x] tts/engine.py - XTTS v2 integration
- [x] Implement `clone-voice` command
- [x] Test: Text → speech with cloned voice
- [x] Voice cloning from 6-10s sample
- [x] Test: test_tts.py - 4 comprehensive tests

### Phase 5: LLM ✅ Complete
- [x] llm/base.py - Abstract LLMProvider interface
- [x] llm/claude.py - Anthropic Claude API integration
- [x] llm/ollama.py - Ollama HTTP API integration
- [x] Test: test_llm.py - Conversation with both providers
- [x] Multi-turn conversation support
- [x] Streaming response support
- [x] Message validation and formatting

### Phase 6: Integration ✅ Complete
- [x] conversation/turn_manager.py - Turn-taking logic with VAD
- [x] conversation/engine.py - Main conversation loop
- [x] State machine (LISTENING → SPEAKING → PROCESSING → PLAYING)
- [x] End-to-end: Microphone → VAD → WhisperX → LLM → XTTS → Speaker
- [x] Interruption support (disabled due to acoustic feedback)
- [x] Database integration (conversation logging)
- [x] Audio resampling (24kHz TTS → 16kHz playback)

### Phase 7: Polish ✅ Complete
- [x] Error handling (graceful failures, clear messages)
- [x] Push-to-talk mode (eliminates acoustic feedback)
- [x] Performance optimization (eager XTTS loading)
- [x] Documentation updates (CLAUDE.md with usage recommendations)
- [x] Suppress non-critical warnings (torchcodec)

## Testing Strategy

**Component Testing:**
```bash
# Test audio capture
python -c "from rubber_ducky.audio import AudioCapture; ..."

# Test VAD
python -c "from rubber_ducky.audio import VADEngine; ..."

# Test WhisperX
python -c "from rubber_ducky.transcription import TranscriptionEngine; ..."
```

**Integration Testing:**
1. Run `rubber-ducky converse`
2. Speak into microphone
3. Verify: VAD → transcription → LLM → TTS → playback
4. Test interruption (barge-in)

**Performance Targets:**
- VAD: < 50ms detection time
- WhisperX: < 100ms for 2s audio (70x realtime)
- LLM: 200-500ms (Claude API typical)
- TTS: 1-2s for ~20 words
- **Total latency: < 3s** (acceptable for MVP)

## Key Technical Decisions

### Voice Activity Detection

**Silero VAD** - Lightweight, low latency, offline
- Start speaking: VAD > threshold for > 250ms
- Stop speaking: VAD < threshold for > 800ms
- Interruption: VAD detects speech during playback

### Latency Optimization

**MVP (Sequential):**
Transcribe (30ms) → LLM (300ms) → TTS (1.5s) = ~2s total

**Future (Streaming):**
LLM stream → TTS per sentence → play chunks as ready = < 1s to first audio

### Interruption Handling

Monitor VAD during PLAYING state:
- Speech detected → stop playback immediately
- Discard remaining TTS audio
- Start new user turn
- Save interrupted turn to DB (marked as interrupted)

## Important Notes

**License Restriction:**
Coqui XTTS v2 weights are non-commercial only (CPML license). For commercial use, replace with OpenAI TTS API or ElevenLabs.

**Model Download:**
First run downloads ~2.3 GB (WhisperX + XTTS). Models cached in `data/models/`.

**GPU Recommended:**
WhisperX and XTTS run much faster with CUDA. CPU works but slower.

**Python Version:**
Requires Python 3.10-3.14 (3.10 recommended for best compatibility with dependencies).

## Known Limitations

**TTS Synthesis Delay (10-60 seconds for long responses):**
The current implementation generates the entire response audio before playing anything. For long responses (200+ characters), this creates a noticeable delay. User sees "Generating voice..." message while waiting.

**Why it happens:**
1. LLM generates full response (~5s)
2. XTTS synthesizes entire response to audio (~50s for 64s of audio)
3. Audio starts playing only after synthesis completes

**Solution (future enhancement):**
Implement streaming pipeline to synthesize and play sentence-by-sentence:
1. LLM streams response sentence by sentence
2. Synthesize first sentence while LLM generates second
3. Play first sentence while synthesizing second
4. Result: < 5s to first audio (vs 50s+ currently)

## Future Enhancements

1. **Streaming pipeline**: LLM + TTS sentence-by-sentence (< 5s to first audio vs 50s+ currently)
2. **Conversation memory**: Context across sessions
3. **Custom wake word**: "Hey Ducky" activation
4. **Multi-language**: Test XTTS with other languages
5. **Web UI**: Optional React frontend (like maildown pattern)

## Troubleshooting

**Common Issues:**

1. **"torch not found"** → Install PyTorch first
2. **"CUDA not available"** → Will use CPU (slower but works)
3. **"Claude API key not configured"** → Set in .env or use Ollama
4. **"No audio devices"** → Run `rubber-ducky devices` to list
5. **Acoustic feedback / echo** → Use `--push-to-talk` mode (recommended)
6. **System responds to itself** → Use `--push-to-talk` mode instead of VAD
7. **Slow first response** → Model loads at startup now (20-30s wait is normal)
8. **Database timestamp error** → Fixed in v1.1 (converts float to datetime)

## Development Workflow

**Starting work on new phase:**
1. Read this file (CLAUDE.md) for context
2. Read plan file (`~/.claude/plans/mutable-gliding-pelican.md`)
3. Implement modules in sequence
4. Test each component independently
5. Update CLAUDE.md with learnings

**When stuck:**
- Check existing patterns in whisper/ollama-assistant/maildown
- Refer to plan file for implementation details
- Test components in isolation before integration

## Status Summary

**Project Status:** ✅ **COMPLETE** (September 2026)

All 7 phases complete:
- ✅ Phase 1: Foundation
- ✅ Phase 2: Audio Pipeline
- ✅ Phase 3: Transcription (WhisperX)
- ✅ Phase 4: TTS (XTTS v2 voice cloning)
- ✅ Phase 5: LLM Integration (Claude + Ollama)
- ✅ Phase 6: Conversation Engine (full integration)
- ✅ Phase 7: Polish (push-to-talk, optimizations)

**Working Features:**
- Voice conversation with Ollama (llama3.2) or Claude
- Voice cloning with XTTS v2
- Push-to-talk mode (recommended)
- VAD mode (has acoustic feedback issues)
- Conversation history in SQLite database

**Recommended Usage:**
```bash
rubber-ducky converse --push-to-talk --debug
```

**Future Enhancements:**
- Echo cancellation for hands-free VAD mode
- GPU support for faster TTS synthesis
- Streaming LLM + TTS for lower latency
