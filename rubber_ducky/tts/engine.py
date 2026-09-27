"""Text-to-speech with voice cloning using Coqui XTTS v2."""

import numpy as np
import torch
from pathlib import Path
from typing import Optional, Union
import warnings


class TTSEngine:
    """Generate speech from text using Coqui XTTS v2.

    XTTS v2 features:
    - Voice cloning from 6-10 second audio sample
    - Multi-language support (17 languages)
    - Streaming generation support
    - Fully offline after model download (~2.1 GB)

    License: CPML (non-commercial use only)
    """

    def __init__(
        self,
        voice_sample: Optional[Union[str, Path]] = None,
        language: str = "en",
        device: str = "cpu",
        use_deepspeed: bool = False
    ):
        """Initialize TTS engine.

        Args:
            voice_sample: Path to reference voice WAV file (6-10 seconds)
            language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi)
            device: Device to use ('cpu', 'cuda', or 'mps')
            use_deepspeed: Enable DeepSpeed for faster inference (requires GPU)
        """
        self.voice_sample = Path(voice_sample) if voice_sample else None
        self.language = language
        self.device = device
        self.use_deepspeed = use_deepspeed

        self.model = None
        self.speaker_embedding = None
        self.gpt_cond_latent = None
        self._is_loaded = False

    def load_model(self):
        """Load XTTS v2 model (lazy loading)."""
        if self._is_loaded:
            return

        try:
            from TTS.api import TTS

            print(f"Loading XTTS v2 model...")
            print("(This may take a few minutes on first run - downloading ~2.1GB)")

            # Load XTTS v2 model
            self.model = TTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                progress_bar=True,
                gpu=(self.device != "cpu")
            )

            # Move to device
            if self.device != "cpu":
                self.model.to(self.device)

            self._is_loaded = True
            print(f"✓ XTTS v2 model loaded")

            # Load voice sample if provided
            if self.voice_sample:
                self.load_voice_sample(self.voice_sample)

        except ImportError:
            raise ImportError(
                "Coqui TTS not installed. Install with: pip install coqui-tts\n"
                "Note: Requires PyTorch to be installed first."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load XTTS model: {e}")

    def load_voice_sample(self, voice_sample_path: Union[str, Path]):
        """Load reference voice for cloning.

        Args:
            voice_sample_path: Path to WAV file (6-10 seconds recommended)
        """
        if not self._is_loaded:
            self.load_model()

        voice_sample_path = Path(voice_sample_path)

        if not voice_sample_path.exists():
            raise FileNotFoundError(f"Voice sample not found: {voice_sample_path}")

        print(f"Loading voice sample: {voice_sample_path.name}")

        try:
            # Compute speaker embeddings from reference audio
            # XTTS uses these embeddings to clone the voice
            self.gpt_cond_latent, self.speaker_embedding = self.model.synthesizer.tts_model.get_conditioning_latents(
                audio_path=str(voice_sample_path)
            )

            self.voice_sample = voice_sample_path
            print(f"✓ Voice sample loaded")

        except Exception as e:
            raise RuntimeError(f"Failed to load voice sample: {e}")

    def synthesize(
        self,
        text: str,
        speed: float = 1.0,
        temperature: float = 0.75,
        repetition_penalty: float = 5.0,
        top_k: int = 50,
        top_p: float = 0.85
    ) -> np.ndarray:
        """Convert text to speech.

        Args:
            text: Text to synthesize
            speed: Speech speed multiplier (0.5 = slower, 2.0 = faster)
            temperature: Sampling temperature (higher = more variation)
            repetition_penalty: Penalty for repeating tokens
            top_k: Top-k sampling parameter
            top_p: Top-p (nucleus) sampling parameter

        Returns:
            Audio as numpy array (float32, mono, 24kHz)
        """
        if not self._is_loaded:
            self.load_model()

        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Use default voice if no sample loaded
        if self.speaker_embedding is None:
            warnings.warn(
                "No voice sample loaded. Using default XTTS voice. "
                "Load a voice sample with load_voice_sample() for voice cloning."
            )

        try:
            # Generate speech
            if self.speaker_embedding is not None:
                # Voice cloning mode
                wav = self.model.tts(
                    text=text,
                    language=self.language,
                    gpt_cond_latent=self.gpt_cond_latent,
                    speaker_embedding=self.speaker_embedding,
                    temperature=temperature,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                    speed=speed
                )
            else:
                # Default voice mode
                wav = self.model.tts(
                    text=text,
                    language=self.language,
                    temperature=temperature,
                    repetition_penalty=repetition_penalty,
                    top_k=top_k,
                    top_p=top_p,
                    speed=speed
                )

            # Convert to numpy array
            if isinstance(wav, torch.Tensor):
                wav = wav.cpu().numpy()
            elif isinstance(wav, list):
                wav = np.array(wav, dtype=np.float32)

            # Ensure mono and float32
            if wav.ndim > 1:
                wav = wav.flatten()
            wav = wav.astype(np.float32)

            return wav

        except Exception as e:
            raise RuntimeError(f"TTS synthesis failed: {e}")

    def synthesize_to_file(
        self,
        text: str,
        output_path: Union[str, Path],
        **kwargs
    ):
        """Synthesize speech and save to file.

        Args:
            text: Text to synthesize
            output_path: Path to save WAV file
            **kwargs: Additional arguments for synthesize()
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate audio
        audio = self.synthesize(text, **kwargs)

        # Save to file
        import soundfile as sf
        sf.write(output_path, audio, samplerate=24000)

        print(f"✓ Audio saved to: {output_path}")

    def get_sample_rate(self) -> int:
        """Get the output sample rate for XTTS v2.

        Returns:
            Sample rate in Hz (24000 for XTTS v2)
        """
        return 24000

    def clone_voice(
        self,
        voice_sample_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        voice_name: Optional[str] = None,
        test_text: str = "This is a test of the voice cloning system."
    ) -> Path:
        """Clone a voice from audio sample and save it.

        Args:
            voice_sample_path: Path to reference audio (6-10 seconds)
            output_dir: Directory to save cloned voice (default: data/voice_samples/)
            voice_name: Name for the voice (default: filename without extension)
            test_text: Text to synthesize for testing the clone

        Returns:
            Path to saved voice sample
        """
        voice_sample_path = Path(voice_sample_path)

        if not voice_sample_path.exists():
            raise FileNotFoundError(f"Voice sample not found: {voice_sample_path}")

        # Determine output location
        if output_dir is None:
            from rubber_ducky.config import settings
            output_dir = settings.voice_samples_dir

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine voice name
        if voice_name is None:
            voice_name = voice_sample_path.stem

        # Copy voice sample to voice_samples directory
        output_path = output_dir / f"{voice_name}.wav"

        import shutil
        shutil.copy(voice_sample_path, output_path)

        print(f"✓ Voice sample copied to: {output_path}")

        # Load and test the voice
        print(f"\nTesting voice clone...")
        self.load_voice_sample(output_path)

        test_output = output_dir / f"{voice_name}_test.wav"
        self.synthesize_to_file(test_text, test_output)

        print(f"✓ Test audio generated: {test_output}")
        print(f"\nVoice '{voice_name}' cloned successfully!")
        print(f"Use with: RUBBER_DUCKY_XTTS_VOICE_SAMPLE={output_path}")

        return output_path

    def __del__(self):
        """Cleanup model on deletion."""
        # Free GPU memory
        if self.model is not None:
            del self.model

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Test function
if __name__ == "__main__":
    import sys
    from pathlib import Path

    print("Testing TTSEngine...")
    print("=" * 60)

    # Create engine
    engine = TTSEngine(device="cpu")

    # Test 1: Default voice
    print("\nTest 1: Default XTTS voice")
    print("-" * 60)

    test_text = "Hello, this is a test of the XTTS voice synthesis system."
    print(f"Text: {test_text}\n")

    audio = engine.synthesize(test_text)
    print(f"✓ Generated {len(audio)} samples ({len(audio) / 24000:.2f}s)")

    # Save test audio
    test_output = Path("test_tts_default.wav")
    engine.synthesize_to_file(test_text, test_output)
    print(f"✓ Saved to: {test_output}")

    # Test 2: Voice cloning (if sample provided)
    if len(sys.argv) > 1:
        voice_sample = sys.argv[1]
        print(f"\n\nTest 2: Voice cloning")
        print("-" * 60)
        print(f"Voice sample: {voice_sample}\n")

        # Load voice
        engine.load_voice_sample(voice_sample)

        # Synthesize with cloned voice
        clone_text = "This is my cloned voice speaking. How does it sound?"
        audio = engine.synthesize(clone_text)
        print(f"✓ Generated {len(audio)} samples ({len(audio) / 24000:.2f}s)")

        # Save cloned voice test
        clone_output = Path("test_tts_cloned.wav")
        engine.synthesize_to_file(clone_text, clone_output)
        print(f"✓ Saved to: {clone_output}")

    else:
        print("\n\nSkipped voice cloning test (no sample provided)")
        print("Usage: python -m rubber_ducky.tts.engine <voice_sample.wav>")

    print("\n" + "=" * 60)
    print("✓ TTSEngine test complete")
    print("\nGenerated files:")
    print("  - test_tts_default.wav (default voice)")
    if len(sys.argv) > 1:
        print("  - test_tts_cloned.wav (cloned voice)")
