"""Utility functions for rubber-ducky."""

import numpy as np
from pathlib import Path


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1m 23s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def ensure_sample_rate(audio: np.ndarray, current_rate: int, target_rate: int) -> np.ndarray:
    """Resample audio to target sample rate if needed.

    Args:
        audio: Audio array
        current_rate: Current sample rate
        target_rate: Target sample rate

    Returns:
        Resampled audio array
    """
    if current_rate == target_rate:
        return audio

    # Simple linear interpolation resampling
    # For production, use librosa.resample or scipy.signal.resample
    duration = len(audio) / current_rate
    new_length = int(duration * target_rate)

    indices = np.linspace(0, len(audio) - 1, new_length)
    resampled = np.interp(indices, np.arange(len(audio)), audio)

    return resampled


def validate_audio_file(file_path: Path) -> bool:
    """Check if file exists and is a valid audio format.

    Args:
        file_path: Path to audio file

    Returns:
        True if valid, False otherwise
    """
    if not file_path.exists():
        return False

    valid_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a'}
    return file_path.suffix.lower() in valid_extensions
