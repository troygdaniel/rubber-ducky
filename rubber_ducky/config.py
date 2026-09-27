"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, Literal


class Settings(BaseSettings):
    """Application settings loaded from .env and config.yaml."""

    # Paths
    data_dir: Path = Path("~/dev/rubber-ducky/data").expanduser()
    voice_samples_dir: Optional[Path] = None
    models_cache_dir: Optional[Path] = None
    database_path: Optional[Path] = None

    # LLM Configuration
    llm_provider: Literal["claude", "ollama"] = "claude"
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-sonnet-4-5-20250929"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024

    # Audio Configuration
    sample_rate: int = 16000  # Whisper requires 16kHz
    chunk_duration: float = 2.0  # Audio chunk size in seconds

    # VAD Configuration
    vad_threshold: float = 0.5  # Silero VAD confidence threshold
    vad_min_speech_duration: float = 0.25  # Minimum speech duration (seconds)
    vad_min_silence_duration: float = 0.8  # Silence before turn end (seconds)

    # WhisperX Configuration
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_language: Optional[str] = None  # Auto-detect if None
    whisper_device: str = "cpu"  # cpu, cuda, mps
    whisper_compute_type: str = "float32"  # float16, int8 for faster inference

    # XTTS Configuration
    xtts_language: str = "en"
    xtts_voice_sample: Optional[str] = None  # Path to cloned voice sample
    xtts_device: str = "cpu"  # cpu, cuda, mps
    xtts_temperature: float = 0.7
    xtts_speed: float = 1.0

    # Conversation Settings
    enable_diarization: bool = False  # Speaker diarization (requires HF token)
    conversation_timeout: float = 300.0  # Auto-end after 5 min silence
    conversation_system_prompt: str = "You are a helpful voice assistant. Be concise and conversational."

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "RUBBER_DUCKY_"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set derived paths if not explicitly set
        if self.voice_samples_dir is None:
            self.voice_samples_dir = self.data_dir / "voice_samples"
        if self.models_cache_dir is None:
            self.models_cache_dir = self.data_dir / "models"
        if self.database_path is None:
            self.database_path = self.data_dir / "conversations.db"

        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.voice_samples_dir.mkdir(parents=True, exist_ok=True)
        self.models_cache_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
