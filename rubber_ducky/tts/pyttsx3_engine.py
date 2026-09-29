"""Text-to-speech using pyttsx3 (local, instant, macOS built-in voices)."""

import numpy as np
import tempfile
import soundfile as sf
from pathlib import Path


class Pyttsx3Engine:
    """Generate speech from text using pyttsx3.

    Uses macOS built-in "say" command (System Preferences > Accessibility > Speech).

    Features:
    - Instant synthesis (< 0.1s)
    - 100% local (no external API calls)
    - Uses system voices
    - Free

    Limitations:
    - Robotic voice (no voice cloning)
    - Less natural than XTTS
    - macOS/Linux/Windows voices vary
    """

    def __init__(
        self,
        voice: str = None,
        rate: int = 200,  # Words per minute
        sample_rate: int = 16000
    ):
        """Initialize pyttsx3 TTS engine.

        Args:
            voice: Voice name (None = default system voice)
            rate: Speech rate in words per minute (default: 200)
            sample_rate: Output sample rate in Hz (default: 16000)
        """
        self.voice = voice
        self.rate = rate
        self.sample_rate = sample_rate
        self.engine = None
        self._is_loaded = False

    def load_model(self):
        """Load pyttsx3 engine (lazy loading)."""
        if self._is_loaded:
            return

        import pyttsx3

        self.engine = pyttsx3.init()

        # Set properties
        self.engine.setProperty('rate', self.rate)

        # Set voice if specified
        if self.voice:
            voices = self.engine.getProperty('voices')
            for v in voices:
                if self.voice.lower() in v.name.lower():
                    self.engine.setProperty('voice', v.id)
                    break

        self._is_loaded = True

    def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize

        Returns:
            Audio data as numpy array (float32, mono, 16kHz)
        """
        if not self._is_loaded:
            self.load_model()

        # Create temporary file for audio output
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Save to file (pyttsx3 doesn't support in-memory synthesis)
            self.engine.save_to_file(text, tmp_path)
            self.engine.runAndWait()

            # Load audio from file
            audio, sr = sf.read(tmp_path)

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)

            # Resample to target sample rate if needed
            if sr != self.sample_rate:
                audio = self._resample(audio, sr, self.sample_rate)

            # Convert to float32
            audio = audio.astype(np.float32)

            return audio

        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

    def _resample(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio to target sample rate.

        Args:
            audio: Input audio
            from_rate: Source sample rate
            to_rate: Target sample rate

        Returns:
            Resampled audio
        """
        if from_rate == to_rate:
            return audio

        # Simple linear interpolation resampling
        duration = len(audio) / from_rate
        new_length = int(duration * to_rate)
        indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)

        return resampled.astype(np.float32)

    def get_sample_rate(self) -> int:
        """Get the sample rate of generated audio.

        Returns:
            Sample rate in Hz
        """
        return self.sample_rate

    def get_available_voices(self):
        """Get list of available system voices.

        Returns:
            List of voice names
        """
        if not self._is_loaded:
            self.load_model()

        voices = self.engine.getProperty('voices')
        return [v.name for v in voices]


# Test/Demo function
if __name__ == "__main__":
    import time

    print("Testing pyttsx3 TTS engine...")
    print()

    engine = Pyttsx3Engine()

    # Test synthesis
    text = "Hello! This is a test of the pyttsx3 text-to-speech engine. It should be very fast."

    print(f"Synthesizing: '{text}'")
    start = time.time()

    audio = engine.synthesize(text)

    elapsed = time.time() - start
    duration = len(audio) / engine.get_sample_rate()

    print(f"✓ Generated {duration:.1f}s of audio in {elapsed:.2f}s")
    print(f"  Sample rate: {engine.get_sample_rate()} Hz")
    print(f"  Audio shape: {audio.shape}")

    # List available voices
    print("\nAvailable voices:")
    for voice in engine.get_available_voices():
        print(f"  - {voice}")
