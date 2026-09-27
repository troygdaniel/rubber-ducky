"""Audio I/O module for rubber-ducky.

Components:
- AudioCapture: Microphone input with sounddevice
- AudioPlayback: Speaker output with sounddevice
- VADEngine: Voice activity detection with Silero VAD
"""

from .capture import AudioCapture
from .playback import AudioPlayback
from .vad import VADEngine

__all__ = ["AudioCapture", "AudioPlayback", "VADEngine"]
