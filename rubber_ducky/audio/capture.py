"""Audio capture from microphone using sounddevice."""

import numpy as np
import sounddevice as sd
from queue import Queue, Empty
from typing import Optional
import threading


class AudioCapture:
    """Capture audio from microphone in real-time."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "float32",
        chunk_duration: float = 0.1,  # 100ms chunks
        device: Optional[int] = None
    ):
        """Initialize audio capture.

        Args:
            sample_rate: Sample rate in Hz (16000 for Whisper)
            channels: Number of audio channels (1 for mono)
            dtype: NumPy dtype for audio data
            chunk_duration: Duration of each audio chunk in seconds
            device: Input device index (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.device = device

        self.audio_queue: Queue = Queue()
        self.stream: Optional[sd.InputStream] = None
        self.is_running = False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback function for sounddevice stream.

        Args:
            indata: Input audio data from microphone
            frames: Number of frames
            time_info: Time information
            status: Stream status
        """
        if status:
            print(f"Audio capture status: {status}")

        # Put audio data in queue
        self.audio_queue.put(indata.copy())

    def start(self):
        """Start capturing audio from microphone."""
        if self.is_running:
            return

        self.stream = sd.InputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=self.dtype,
            blocksize=self.chunk_size,
            callback=self._audio_callback
        )

        self.stream.start()
        self.is_running = True

    def stop(self):
        """Stop capturing audio."""
        if not self.is_running:
            return

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.is_running = False

        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Empty:
                break

    def get_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get next audio chunk from queue.

        Args:
            timeout: Maximum time to wait for chunk in seconds

        Returns:
            Audio chunk as numpy array, or None if timeout
        """
        try:
            chunk = self.audio_queue.get(timeout=timeout)
            return chunk.flatten()  # Ensure 1D array
        except Empty:
            return None

    def get_accumulated_audio(self, duration: float) -> np.ndarray:
        """Accumulate audio chunks for specified duration.

        Args:
            duration: Duration in seconds to accumulate

        Returns:
            Accumulated audio as numpy array
        """
        chunks = []
        samples_needed = int(self.sample_rate * duration)
        samples_collected = 0

        while samples_collected < samples_needed:
            chunk = self.get_chunk(timeout=duration)
            if chunk is None:
                break

            chunks.append(chunk)
            samples_collected += len(chunk)

        if not chunks:
            return np.array([], dtype=self.dtype)

        audio = np.concatenate(chunks)
        return audio[:samples_needed]  # Trim to exact duration

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def list_audio_devices():
    """List all available audio input devices.

    Returns:
        List of device dictionaries
    """
    devices = sd.query_devices()
    input_devices = []

    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append({
                'index': i,
                'name': device['name'],
                'channels': device['max_input_channels'],
                'sample_rate': device['default_samplerate']
            })

    return input_devices


def get_default_input_device():
    """Get default input device index.

    Returns:
        Device index or None if not found
    """
    try:
        return sd.default.device[0]
    except Exception:
        return None


# Test function
if __name__ == "__main__":
    import time

    print("Testing AudioCapture...")
    print(f"Default input device: {get_default_input_device()}")
    print("\nAvailable input devices:")
    for device in list_audio_devices():
        print(f"  [{device['index']}] {device['name']}")

    print("\nRecording 3 seconds of audio...")
    with AudioCapture(sample_rate=16000) as capture:
        time.sleep(3)

        # Get chunks
        chunks_received = 0
        while True:
            chunk = capture.get_chunk(timeout=0.1)
            if chunk is None:
                break
            chunks_received += 1
            print(f"  Chunk {chunks_received}: {len(chunk)} samples")

    print(f"\nTotal chunks received: {chunks_received}")
    print("✓ AudioCapture test complete")
