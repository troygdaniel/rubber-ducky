"""Conversation engine - main conversation loop.

This is a placeholder. Will be implemented in Phase 6.
"""

from rubber_ducky.config import Settings


class ConversationEngine:
    """Main conversation engine with state machine."""

    def __init__(self, settings: Settings, debug: bool = False):
        """Initialize conversation engine.

        Args:
            settings: Application settings
            debug: Enable debug output
        """
        self.settings = settings
        self.debug = debug

    def start(self):
        """Start the conversation loop."""
        print("Conversation engine not yet implemented")
        print("This will be implemented in Phase 6")
        print("\nPlanned features:")
        print("  - Voice activity detection (VAD)")
        print("  - Real-time transcription with WhisperX")
        print("  - LLM conversation (Claude or Ollama)")
        print("  - Text-to-speech with XTTS v2")
        print("  - Barge-in support (interrupt assistant)")
