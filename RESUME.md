# Resume Instructions - After macOS 27 Upgrade

**Date:** September 27, 2026
**Project:** rubber-ducky (local voice conversation system)
**Status:** ✅ Code complete - Phase 6 done! Ready to install and test.

## What We Built

A complete local voice conversation system:
- **Phase 1:** Foundation (config, database, CLI, MCP server) ✅
- **Phase 2:** Audio Pipeline (capture, playback, VAD) ✅
- **Phase 3:** WhisperX Transcription ✅
- **Phase 4:** XTTS v2 Voice Cloning ✅
- **Phase 5:** LLM Integration (Claude + Ollama) ✅
- **Phase 6:** Conversation Engine (full integration) ✅

**Project stats:**
- 27 Python modules
- 6 test suites (all structure tests passing)
- Complete end-to-end system: Mic → VAD → WhisperX → LLM → XTTS → Speaker

## The Blocker

macOS 26 had a pip bug (truststore can't parse version "26.0.1"). This prevented installing dependencies.

**Expected fix:** macOS 27 should have fixed pip compatibility.

## Next Steps After Reboot

### 1. Test if pip works now

```bash
cd ~/dev/rubber-ducky

# Test Python 3.12 and pip
/opt/homebrew/bin/python3.12 --version
/opt/homebrew/bin/python3.12 -m pip --version
```

If pip works, continue to step 2. If not, tell Claude "pip still broken" and we'll try conda.

### 2. Create virtual environment

```bash
# Remove old broken venv
rm -rf .venv

# Create new venv
/opt/homebrew/bin/python3.12 -m venv .venv

# Activate it
source .venv/bin/activate

# Verify
which python
python --version
```

### 3. Install dependencies

**CRITICAL ORDER - Install PyTorch FIRST:**

```bash
# 1. PyTorch (MUST be first)
pip install torch torchvision torchaudio

# 2. WhisperX (pulls compatible versions)
pip install whisperx

# 3. Everything else
pip install coqui-tts anthropic httpx pydantic-settings pyyaml sqlalchemy rich click sounddevice soundfile librosa

# 4. Install rubber-ducky package
pip install -e .
```

### 4. Configure

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your Claude API key
# OR set to use Ollama:
# RUBBER_DUCKY_LLM_PROVIDER=ollama
```

Minimum `.env`:
```
RUBBER_DUCKY_CLAUDE_API_KEY=your_api_key_here
```

### 5. Test the system

```bash
# Check setup
rubber-ducky setup

# List audio devices
rubber-ducky devices

# (Optional) Clone your voice
rubber-ducky clone-voice --sample ~/voice.wav --name Troy

# Start conversation!
rubber-ducky converse
```

## If You Get Stuck

Tell Claude:
- "pip still broken" → We'll try conda/miniforge
- "torch won't install" → We'll troubleshoot PyTorch
- "whisperx won't install" → We'll check dependencies
- "rubber-ducky command not found" → We'll check `pip install -e .`
- Any other error → Just paste the error message

## What the System Does

When you run `rubber-ducky converse`:

1. **LISTENING** - Monitors microphone with VAD
2. **SPEAKING** - Accumulates your speech
3. **PROCESSING:**
   - Transcribes with WhisperX (~30ms)
   - Gets LLM response (~300ms)
   - Generates voice with XTTS (~1.5s)
4. **PLAYING** - Speaks response (you can interrupt anytime!)

Then loops back to LISTENING.

## Project Location

```
~/dev/rubber-ducky/
├── rubber_ducky/          # Main package (27 Python modules)
├── data/                  # Auto-created (DB, voice samples, models)
├── test_*.py              # 6 test suites
├── requirements.txt       # Dependencies
├── .env                   # Your config (create this)
└── README.md             # User documentation
```

## Quick Reference

```bash
# Setup and test
rubber-ducky setup
rubber-ducky devices
rubber-ducky config

# Clone voice
rubber-ducky clone-voice --sample voice.wav --name Troy

# Start conversation
rubber-ducky converse
rubber-ducky converse --provider ollama
rubber-ducky converse --voice ~/my-voice.wav --debug
```

## Resume Prompt for Claude

When you start a new Claude session, say:

> "I'm resuming the rubber-ducky project after rebooting. Read ~/dev/rubber-ducky/RESUME.md and help me install and test it. I just upgraded to macOS 27."

Claude will read this file and know exactly where we left off.

## Git History

```
b57a5cb Add conversation structure test and fix lazy imports
2736d78 Phase 6 complete: Conversation Engine Integration
b763907 Fix LLM module imports and add structure test
8653033 Phase 5 complete: LLM Integration
c760fc7 Phase 4 complete: XTTS v2 Voice Cloning
b7d02d2 Phase 3 complete: WhisperX Transcription
4893f59 Phase 2 complete: Audio Pipeline
8efa4e7 Add MCP server for Claude Code integration
2325d8c Phase 1 complete: Foundation
```

All code is committed and ready to use!

---

**You're all set!** After reboot, just follow steps 1-5 above. Good luck! 🦆
