"""Text-to-speech module."""

from rubber_ducky.tts.engine import TTSEngine
from rubber_ducky.tts.pyttsx3_engine import Pyttsx3Engine

__all__ = ["TTSEngine", "Pyttsx3Engine"]
