"""Audio playback to speakers using sounddevice."""

import numpy as np
import sounddevice as sd
from queue import Queue, Empty
from typing import Optional
import threading


class AudioPlayback:
    """Play audio through speakers in real-time."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "float32",
        device: Optional[int] = None
    ):
        """Initialize audio playback.

        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels (1 for mono)
            dtype: NumPy dtype for audio data
            device: Output device index (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.device = device

        self.audio_queue: Queue = Queue()
        self.is_playing = False
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def play(self, audio: np.ndarray, blocking: bool = False):
        """Play audio through speakers.

        Args:
            audio: Audio data as numpy array
            blocking: If True, wait for playback to complete
        """
        # Ensure audio is the right shape and type
        if audio.ndim == 1:
            audio = audio.reshape(-1, 1) if self.channels == 1 else audio
        audio = audio.astype(self.dtype)

        if blocking:
            # Play synchronously
            sd.play(audio, self.sample_rate, device=self.device)
            sd.wait()
        else:
            # Add to queue for async playback
            self.audio_queue.put(audio)
            if not self.is_playing:
                self._start_playback_thread()

    def _start_playback_thread(self):
        """Start background playback thread."""
        if self.is_playing:
            return

        self.is_playing = True
        self._stop_event.clear()
        self._playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._playback_thread.start()

    def _playback_loop(self):
        """Background thread that plays queued audio."""
        while not self._stop_event.is_set():
            try:
                audio = self.audio_queue.get(timeout=0.1)

                # Play this chunk
                sd.play(audio, self.sample_rate, device=self.device)
                sd.wait()

            except Empty:
                # Queue is empty, check if we should stop
                if self.audio_queue.empty():
                    break

        self.is_playing = False

    def stop(self):
        """Stop playback immediately."""
        self._stop_event.set()
        sd.stop()

        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Empty:
                break

        self.is_playing = False

    def wait(self):
        """Wait for all queued audio to finish playing."""
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join()

    def get_duration(self, audio: np.ndarray) -> float:
        """Get duration of audio in seconds.

        Args:
            audio: Audio data as numpy array

        Returns:
            Duration in seconds
        """
        num_samples = len(audio) if audio.ndim == 1 else audio.shape[0]
        return num_samples / self.sample_rate

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def list_output_devices():
    """List all available audio output devices.

    Returns:
        List of device dictionaries
    """
    devices = sd.query_devices()
    output_devices = []

    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            output_devices.append({
                'index': i,
                'name': device['name'],
                'channels': device['max_output_channels'],
                'sample_rate': device['default_samplerate']
            })

    return output_devices


def get_default_output_device():
    """Get default output device index.

    Returns:
        Device index or None if not found
    """
    try:
        return sd.default.device[1]
    except Exception:
        return None


# Test function
if __name__ == "__main__":
    import time

    print("Testing AudioPlayback...")
    print(f"Default output device: {get_default_output_device()}")
    print("\nAvailable output devices:")
    for device in list_output_devices():
        print(f"  [{device['index']}] {device['name']}")

    print("\nGenerating test tone (440 Hz, 1 second)...")
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0  # A4 note

    t = np.linspace(0, duration, int(sample_rate * duration))
    tone = 0.3 * np.sin(2 * np.pi * frequency * t)

    print("Playing tone...")
    with AudioPlayback(sample_rate=sample_rate) as playback:
        playback.play(tone, blocking=True)

    print("✓ AudioPlayback test complete")
