"""Voice Activity Detection using Silero VAD."""

import numpy as np
import torch
from typing import Optional
import warnings

# Silero VAD will be loaded dynamically
try:
    # Silero VAD is installed via: pip install git+https://github.com/snakers4/silero-vad.git
    # For now, we'll implement a placeholder and lazy loading
    SILERO_AVAILABLE = False
except ImportError:
    SILERO_AVAILABLE = False


class VADEngine:
    """Voice Activity Detection using Silero VAD.

    Detects when speech starts and stops in audio stream.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        sample_rate: int = 16000,
        min_speech_duration: float = 0.25,
        min_silence_duration: float = 0.8
    ):
        """Initialize VAD engine.

        Args:
            threshold: Confidence threshold for speech detection (0-1)
            sample_rate: Sample rate of audio in Hz
            min_speech_duration: Minimum duration of speech to trigger (seconds)
            min_silence_duration: Minimum silence duration to end speech (seconds)
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.min_speech_duration = min_speech_duration
        self.min_silence_duration = min_silence_duration

        self.model: Optional[torch.nn.Module] = None
        self._is_loaded = False

        # State tracking
        self._speech_start_time: Optional[float] = None
        self._silence_start_time: Optional[float] = None
        self._current_time: float = 0.0
        self._is_speech_active = False

    def load_model(self):
        """Load Silero VAD model (lazy loading)."""
        if self._is_loaded:
            return

        try:
            # Load Silero VAD model
            # This will be implemented once silero-vad is installed
            # For now, use a placeholder

            # Real implementation would be:
            # self.model, utils = torch.hub.load(
            #     repo_or_dir='snakers4/silero-vad',
            #     model='silero_vad',
            #     force_reload=False,
            #     onnx=False
            # )

            # Placeholder for now
            warnings.warn(
                "Silero VAD not installed. Using energy-based fallback. "
                "Install with: pip install git+https://github.com/snakers4/silero-vad.git"
            )

            self._is_loaded = True

        except Exception as e:
            warnings.warn(f"Failed to load Silero VAD: {e}. Using fallback.")
            self._is_loaded = True

    def detect(self, audio_chunk: np.ndarray) -> bool:
        """Detect if audio chunk contains speech.

        Args:
            audio_chunk: Audio data as numpy array

        Returns:
            True if speech detected, False otherwise
        """
        if not self._is_loaded:
            self.load_model()

        # Calculate chunk duration
        chunk_duration = len(audio_chunk) / self.sample_rate
        self._current_time += chunk_duration

        # Get speech probability
        speech_prob = self._get_speech_probability(audio_chunk)

        # Update state
        is_speech = speech_prob > self.threshold

        if is_speech:
            if not self._is_speech_active:
                # Speech just started
                if self._speech_start_time is None:
                    self._speech_start_time = self._current_time

                # Check if we've had enough speech to confirm
                speech_duration = self._current_time - self._speech_start_time
                if speech_duration >= self.min_speech_duration:
                    self._is_speech_active = True
                    self._silence_start_time = None

        else:
            if self._is_speech_active:
                # Silence detected during speech
                if self._silence_start_time is None:
                    self._silence_start_time = self._current_time

                # Check if we've had enough silence to confirm end
                silence_duration = self._current_time - self._silence_start_time
                if silence_duration >= self.min_silence_duration:
                    self._is_speech_active = False
                    self._speech_start_time = None

            else:
                # Reset speech start if we're not in speech yet
                self._speech_start_time = None

        return self._is_speech_active

    def _get_speech_probability(self, audio_chunk: np.ndarray) -> float:
        """Get probability that audio chunk contains speech.

        Args:
            audio_chunk: Audio data as numpy array

        Returns:
            Probability between 0 and 1
        """
        if self.model is not None:
            # Use actual Silero VAD model
            try:
                # Convert to tensor
                audio_tensor = torch.from_numpy(audio_chunk).float()

                # Get speech probability
                with torch.no_grad():
                    speech_prob = self.model(audio_tensor, self.sample_rate).item()

                return speech_prob

            except Exception as e:
                warnings.warn(f"Silero VAD inference failed: {e}. Using fallback.")

        # Fallback: simple energy-based detection
        return self._energy_based_detection(audio_chunk)

    def _energy_based_detection(self, audio_chunk: np.ndarray) -> float:
        """Simple energy-based speech detection (fallback).

        Args:
            audio_chunk: Audio data as numpy array

        Returns:
            Pseudo-probability between 0 and 1
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))

        # Normalize to 0-1 range (assuming typical speech is around 0.1-0.3 RMS)
        # This is a rough heuristic
        normalized = min(1.0, rms / 0.2)

        return normalized

    def reset(self):
        """Reset VAD state."""
        self._speech_start_time = None
        self._silence_start_time = None
        self._current_time = 0.0
        self._is_speech_active = False

    def get_silence_duration(self) -> float:
        """Get duration of current silence in seconds.

        Returns:
            Silence duration in seconds, or 0 if speech is active
        """
        if not self._is_speech_active or self._silence_start_time is None:
            return 0.0

        return self._current_time - self._silence_start_time

    def is_speech_active(self) -> bool:
        """Check if speech is currently active.

        Returns:
            True if speech is active, False otherwise
        """
        return self._is_speech_active


# Test function
if __name__ == "__main__":
    import time
    from .capture import AudioCapture

    print("Testing VADEngine...")

    # Create VAD with default settings
    vad = VADEngine(
        threshold=0.5,
        sample_rate=16000,
        min_speech_duration=0.25,
        min_silence_duration=0.8
    )

    print("Listening for speech (speak into microphone)...")
    print("Speech detection starts after 0.25s of speech")
    print("Speech ends after 0.8s of silence")
    print("\nPress Ctrl+C to stop\n")

    with AudioCapture(sample_rate=16000, chunk_duration=0.1) as capture:
        try:
            while True:
                chunk = capture.get_chunk(timeout=0.2)
                if chunk is None:
                    continue

                # Detect speech
                is_speech = vad.detect(chunk)

                # Print status
                if is_speech:
                    silence = vad.get_silence_duration()
                    if silence > 0:
                        print(f"  SPEECH (silence: {silence:.2f}s)", end='\r')
                    else:
                        print("  SPEECH", end='\r')
                else:
                    print("  silence", end='\r')

                # Small delay for readability
                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n\n✓ VADEngine test complete")
