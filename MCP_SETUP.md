# Rubber-Ducky MCP Server Setup

## What is This?

The rubber-ducky MCP server allows Claude Code to use voice I/O instead of typing. Claude can:
- **Listen** to you speaking (via `listen_and_transcribe` tool)
- **Speak** back to you (via `speak` tool)

## Quick Setup

### 1. Install rubber-ducky with MCP support

```bash
cd ~/dev/rubber-ducky
pip install -e .
```

This installs the `rubber-ducky-mcp` command.

### 2. Test the MCP server

```bash
# Test that the command exists
rubber-ducky-mcp --help

# Should show: MCP server will start via stdio
```

### 3. Configure Claude Code

Add to your Claude Code MCP configuration (`~/.config/claude/mcp.json`):

```json
{
  "mcpServers": {
    "rubber-ducky": {
      "command": "rubber-ducky-mcp",
      "description": "Voice I/O for Claude Code",
      "env": {
        "RUBBER_DUCKY_DATA_DIR": "~/dev/rubber-ducky/data"
      }
    }
  }
}
```

Or copy the provided config:
```bash
cp ~/dev/rubber-ducky/mcp-config.json ~/.config/claude/mcp.json
```

### 4. Restart Claude Code

Restart Claude Code to load the new MCP server.

### 5. Verify it's working

In Claude Code, check available tools:

```
You should see:
- listen_and_transcribe
- speak
- status
```

## Usage Examples

### Basic Voice Conversation

**You:** "Use the listen tool to hear what I want to say"

**Claude Code:**
```
[Uses listen_and_transcribe tool]
[Hears your speech, transcribes it]
[Processes your request]
[Uses speak tool to respond verbally]
```

### Example Prompts

**Voice dictation:**
> "Listen for my dictation, then help me edit it"

**Voice Q&A:**
> "I'm going to ask you questions verbally. Use listen to hear me, then speak your answers back"

**Voice brainstorming:**
> "Let's brainstorm ideas for my project. I'll speak my thoughts, you respond verbally"

## MCP Tools Reference

### `listen_and_transcribe`

**Description:** Listen to microphone and transcribe speech to text

**Parameters:**
- `max_duration` (optional): Maximum seconds to listen (default: 30)
- `silence_threshold` (optional): Seconds of silence before stopping (default: 0.8)

**Returns:**
```json
{
  "text": "transcribed speech",
  "duration": 3.2,
  "speakers": 1
}
```

**Example:**
```python
# Claude Code will call this tool like:
listen_and_transcribe(max_duration=60, silence_threshold=1.0)
```

### `speak`

**Description:** Convert text to speech and play through speakers

**Parameters:**
- `text` (required): Text to speak
- `voice` (optional): Voice sample to use (uses configured voice if not specified)

**Returns:**
```json
{
  "success": true,
  "audio_duration": 2.1
}
```

**Example:**
```python
# Claude Code will call this tool like:
speak(text="Hello! I heard you say...")
```

### `status`

**Description:** Check if rubber-ducky is ready

**Parameters:** None

**Returns:**
```json
{
  "ready": true,
  "models_loaded": true,
  "audio_devices_ok": true,
  "config": {
    "llm_provider": "claude",
    "whisper_model": "base",
    "voice_sample": "default"
  }
}
```

## Current Status

**Phase 1 Complete:** MCP server structure is built

**Not Yet Implemented:**
- Audio capture (Phase 2)
- Speech transcription (Phase 3)
- Voice cloning/TTS (Phase 4)

Currently, the tools return placeholder responses explaining they're not yet implemented.

## Troubleshooting

### "Command not found: rubber-ducky-mcp"

Install the package:
```bash
cd ~/dev/rubber-ducky
pip install -e .
```

### MCP server not showing in Claude Code

1. Check Claude Code MCP config: `~/.config/claude/mcp.json`
2. Restart Claude Code
3. Check for errors in Claude Code logs

### Tools return "Not implemented yet"

This is expected! Audio components will be built in Phase 2-4.

The MCP server structure is ready, we just need to fill in the actual audio/transcription/TTS code.

## Next Steps

As we implement each phase:
- **Phase 2**: `listen_and_transcribe` will actually capture audio and use VAD
- **Phase 3**: Transcription with WhisperX will work
- **Phase 4**: `speak` will use your cloned voice via XTTS v2

The MCP server will automatically work once those components are complete.

## Performance

**Expected latency (when fully implemented):**
- `listen_and_transcribe`: ~30ms (70x realtime transcription)
- `speak`: 1-2s (TTS generation + playback)

**MCP overhead:** ~10-50ms (negligible)

Total voice conversation latency: ~2-3s (acceptable for natural conversation)
