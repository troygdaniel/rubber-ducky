"""MCP server for rubber-ducky voice I/O.

Exposes tools that allow Claude Code to:
- Listen to user speech and transcribe it
- Speak text responses using TTS
"""

import asyncio
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from rubber_ducky.config import settings


# Tool definitions
LISTEN_TOOL = Tool(
    name="listen_and_transcribe",
    description=(
        "Listen to user speech via microphone and transcribe it to text. "
        "Captures audio until silence is detected (configurable duration). "
        "Returns the transcribed text and metadata (duration, speaker count)."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "max_duration": {
                "type": "number",
                "description": "Maximum listening duration in seconds (default: 30)",
                "default": 30
            },
            "silence_threshold": {
                "type": "number",
                "description": "Seconds of silence before stopping (default: 0.8)",
                "default": 0.8
            }
        }
    }
)

SPEAK_TOOL = Tool(
    name="speak",
    description=(
        "Convert text to speech and play it through speakers. "
        "Uses the configured voice (cloned or default). "
        "Returns success status and audio duration."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to convert to speech"
            },
            "voice": {
                "type": "string",
                "description": "Voice sample to use (optional, uses configured voice if not specified)",
                "default": None
            }
        },
        "required": ["text"]
    }
)

STATUS_TOOL = Tool(
    name="status",
    description=(
        "Check if rubber-ducky is ready for voice I/O. "
        "Returns status of models, audio devices, and configuration."
    ),
    inputSchema={
        "type": "object",
        "properties": {}
    }
)


class RubberDuckyServer:
    """MCP server for rubber-ducky voice I/O."""

    def __init__(self):
        self.server = Server("rubber-ducky")
        self.audio_capture = None
        self.audio_playback = None
        self.vad = None
        self.whisper = None
        self.tts = None
        self.initialized = False

        # Register tool handlers
        self.server.list_tools = self.list_tools
        self.server.call_tool = self.call_tool

    async def list_tools(self) -> list[Tool]:
        """List available tools."""
        return [LISTEN_TOOL, SPEAK_TOOL, STATUS_TOOL]

    async def call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""

        if name == "status":
            return await self.handle_status()

        elif name == "listen_and_transcribe":
            return await self.handle_listen(
                max_duration=arguments.get("max_duration", 30),
                silence_threshold=arguments.get("silence_threshold", 0.8)
            )

        elif name == "speak":
            return await self.handle_speak(
                text=arguments["text"],
                voice=arguments.get("voice")
            )

        else:
            raise ValueError(f"Unknown tool: {name}")

    async def handle_status(self) -> list[TextContent]:
        """Check system status."""
        # For now, return basic status
        # TODO: Check if models are loaded, audio devices work, etc.

        status = {
            "ready": False,
            "models_loaded": False,
            "audio_devices_ok": False,
            "config": {
                "llm_provider": settings.llm_provider,
                "whisper_model": settings.whisper_model,
                "voice_sample": settings.xtts_voice_sample or "default"
            },
            "message": "MCP server running, but audio components not yet implemented (Phase 2+)"
        }

        import json
        return [TextContent(type="text", text=json.dumps(status, indent=2))]

    async def handle_listen(self, max_duration: float, silence_threshold: float) -> list[TextContent]:
        """Listen to microphone and transcribe speech."""

        # TODO: Implement in Phase 2 (audio) + Phase 3 (transcription)
        # For now, return placeholder

        result = {
            "error": "Not implemented yet",
            "message": "Audio capture will be implemented in Phase 2",
            "expected_return": {
                "text": "transcribed speech would go here",
                "duration": 3.2,
                "speakers": 1
            }
        }

        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def handle_speak(self, text: str, voice: Optional[str]) -> list[TextContent]:
        """Convert text to speech and play it."""

        # TODO: Implement in Phase 4 (TTS)
        # For now, return placeholder

        result = {
            "error": "Not implemented yet",
            "message": "TTS will be implemented in Phase 4",
            "requested_text": text,
            "voice": voice or settings.xtts_voice_sample or "default",
            "expected_return": {
                "success": True,
                "audio_duration": 2.1
            }
        }

        import json
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def initialize(self):
        """Initialize audio components (lazy loading)."""
        if self.initialized:
            return

        # TODO: Load models and initialize audio
        # For now, just mark as initialized
        self.initialized = True

    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def create_server() -> RubberDuckyServer:
    """Create a new rubber-ducky MCP server instance."""
    return RubberDuckyServer()


async def main():
    """Main entry point for MCP server."""
    server = create_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
