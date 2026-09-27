"""Speech-to-text transcription using WhisperX."""

import numpy as np
import torch
from typing import Optional, Dict, Any, List
import warnings


class TranscriptionEngine:
    """Transcribe speech to text using WhisperX.

    WhisperX provides:
    - Fast transcription (70x realtime with large-v2)
    - Word-level timestamps
    - Speaker diarization (optional)
    """

    def __init__(
        self,
        model_name: str = "base",
        language: Optional[str] = None,
        device: str = "cpu",
        compute_type: str = "float32",
        enable_diarization: bool = False
    ):
        """Initialize transcription engine.

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            language: Language code (None for auto-detect)
            device: Device to use ('cpu', 'cuda', or 'mps')
            compute_type: Computation type ('float32', 'float16', 'int8')
            enable_diarization: Enable speaker diarization
        """
        self.model_name = model_name
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.enable_diarization = enable_diarization

        self.model = None
        self.align_model = None
        self.align_metadata = None
        self.diarize_model = None
        self._is_loaded = False

    def load_model(self):
        """Load WhisperX model (lazy loading)."""
        if self._is_loaded:
            return

        try:
            import whisperx

            # Load main Whisper model
            print(f"Loading WhisperX model '{self.model_name}'...")
            self.model = whisperx.load_model(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )

            # Note: Alignment and diarization models loaded on-demand
            self._is_loaded = True
            print(f"✓ WhisperX model loaded")

        except ImportError:
            raise ImportError(
                "WhisperX not installed. Install with: pip install whisperx\n"
                "Note: Requires PyTorch to be installed first."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load WhisperX model: {e}")

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        batch_size: int = 16
    ) -> Dict[str, Any]:
        """Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (mono, float32)
            sample_rate: Sample rate in Hz (must be 16000 for Whisper)
            batch_size: Batch size for inference

        Returns:
            Dictionary with transcription results:
            {
                "text": "full transcription",
                "segments": [{"text": "...", "start": 0.0, "end": 1.2}, ...],
                "language": "en"
            }
        """
        if not self._is_loaded:
            self.load_model()

        if sample_rate != 16000:
            raise ValueError("WhisperX requires 16kHz audio")

        # Ensure audio is float32 and 1D
        audio = audio.astype(np.float32)
        if audio.ndim > 1:
            audio = audio.flatten()

        try:
            import whisperx

            # Transcribe
            result = self.model.transcribe(
                audio,
                language=self.language,
                batch_size=batch_size
            )

            # Get detected language if auto-detect was used
            detected_language = result.get("language", self.language or "en")

            # Load alignment model for word-level timestamps
            if self.align_model is None:
                print(f"Loading alignment model for '{detected_language}'...")
                self.align_model, self.align_metadata = whisperx.load_align_model(
                    language_code=detected_language,
                    device=self.device
                )

            # Align timestamps
            result = whisperx.align(
                result["segments"],
                self.align_model,
                self.align_metadata,
                audio,
                self.device,
                return_char_alignments=False
            )

            # Optional: Speaker diarization
            if self.enable_diarization:
                result = self._add_diarization(audio, result)

            # Format result
            full_text = " ".join([seg["text"] for seg in result["segments"]])

            return {
                "text": full_text.strip(),
                "segments": result["segments"],
                "language": detected_language,
                "word_segments": result.get("word_segments", [])
            }

        except Exception as e:
            # Return error gracefully
            return {
                "text": "",
                "segments": [],
                "language": self.language or "en",
                "error": str(e)
            }

    def _add_diarization(self, audio: np.ndarray, result: Dict) -> Dict:
        """Add speaker diarization to transcription result.

        Args:
            audio: Audio data
            result: Transcription result from WhisperX

        Returns:
            Updated result with speaker labels
        """
        try:
            import whisperx

            # Load diarization model if not loaded
            if self.diarize_model is None:
                print("Loading diarization model...")
                self.diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=None,  # HuggingFace token if needed
                    device=self.device
                )

            # Run diarization
            diarize_segments = self.diarize_model(audio)

            # Assign speakers to words
            result = whisperx.assign_word_speakers(diarize_segments, result)

            return result

        except Exception as e:
            warnings.warn(f"Diarization failed: {e}")
            return result

    def transcribe_file(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcription result dictionary
        """
        import soundfile as sf

        # Load audio file
        audio, sample_rate = sf.read(audio_path, dtype='float32')

        # Resample if needed
        if sample_rate != 16000:
            import librosa
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
            sample_rate = 16000

        return self.transcribe(audio, sample_rate)

    def get_speaker_segments(self, result: Dict) -> List[Dict]:
        """Extract speaker-labeled segments from result.

        Args:
            result: Transcription result with diarization

        Returns:
            List of segments with speaker labels
        """
        if not self.enable_diarization:
            return result.get("segments", [])

        segments = []
        for seg in result.get("segments", []):
            speaker = seg.get("speaker", "UNKNOWN")
            segments.append({
                "speaker": speaker,
                "text": seg["text"],
                "start": seg["start"],
                "end": seg["end"]
            })

        return segments

    def format_transcript(self, result: Dict, include_timestamps: bool = False) -> str:
        """Format transcription result as readable text.

        Args:
            result: Transcription result
            include_timestamps: Include timestamps in output

        Returns:
            Formatted transcript string
        """
        if "error" in result:
            return f"[Error: {result['error']}]"

        if not result.get("segments"):
            return "[No speech detected]"

        lines = []

        if self.enable_diarization:
            # Format with speaker labels
            for seg in result["segments"]:
                speaker = seg.get("speaker", "UNKNOWN")
                text = seg["text"]

                if include_timestamps:
                    start = seg["start"]
                    end = seg["end"]
                    lines.append(f"[{start:.1f}s - {end:.1f}s] {speaker}: {text}")
                else:
                    lines.append(f"{speaker}: {text}")

        else:
            # Format without speaker labels
            for seg in result["segments"]:
                text = seg["text"]

                if include_timestamps:
                    start = seg["start"]
                    end = seg["end"]
                    lines.append(f"[{start:.1f}s - {end:.1f}s] {text}")
                else:
                    lines.append(text)

        return "\n".join(lines)

    def __del__(self):
        """Cleanup models on deletion."""
        # Free GPU memory
        if self.model is not None:
            del self.model
        if self.align_model is not None:
            del self.align_model
        if self.diarize_model is not None:
            del self.diarize_model

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Test function
if __name__ == "__main__":
    import sys
    from pathlib import Path

    print("Testing TranscriptionEngine...")
    print("=" * 60)

    # Check if audio file provided
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"Transcribing file: {audio_file}\n")

        engine = TranscriptionEngine(
            model_name="base",
            device="cpu",
            enable_diarization=False
        )

        result = engine.transcribe_file(audio_file)

        print("Transcription:")
        print("-" * 60)
        print(engine.format_transcript(result, include_timestamps=True))
        print("-" * 60)
        print(f"\nFull text: {result['text']}")
        print(f"Language: {result['language']}")
        print(f"Segments: {len(result['segments'])}")

    else:
        print("Usage: python -m rubber_ducky.transcription.engine <audio_file>")
        print("\nExample:")
        print("  python -m rubber_ducky.transcription.engine recording.wav")
        print("\nOr test with captured audio:")

        # Test with live recording
        from rubber_ducky.audio import AudioCapture

        print("\nRecording 5 seconds of audio...")
        print("(Speak into your microphone!)\n")

        capture = AudioCapture(sample_rate=16000)
        capture.start()

        import time
        time.sleep(5)

        audio = capture.get_accumulated_audio(duration=5.0)
        capture.stop()

        print(f"Captured {len(audio)} samples\n")
        print("Transcribing...")

        engine = TranscriptionEngine(
            model_name="base",
            device="cpu",
            enable_diarization=False
        )

        result = engine.transcribe(audio, sample_rate=16000)

        print("\nTranscription:")
        print("-" * 60)
        print(engine.format_transcript(result))
        print("-" * 60)
        print(f"\nFull text: {result['text']}")
        print(f"Language: {result['language']}")

    print("\n✓ TranscriptionEngine test complete")
