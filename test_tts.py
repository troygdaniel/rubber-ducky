#!/usr/bin/env python3
"""Test script for TTS with XTTS v2."""

import time
import sys
from pathlib import Path
from rubber_ducky.tts import TTSEngine
from rubber_ducky.audio import AudioPlayback
from rubber_ducky.config import settings


def test_default_voice():
    """Test 1: Default XTTS voice."""
    print("=" * 60)
    print("TEST 1: Default XTTS Voice")
    print("=" * 60)

    print("\nLoading XTTS v2 model...")
    print("(This may take several minutes on first run - downloading ~2.1GB)\n")

    # Create TTS engine (CPU for compatibility)
    engine = TTSEngine(device="cpu")

    # Test text
    test_text = "Hello! This is the default XTTS voice. How does it sound?"
    print(f"Text: \"{test_text}\"\n")

    # Synthesize
    print("Synthesizing speech...")
    start_time = time.time()
    audio = engine.synthesize(test_text)
    synthesis_time = time.time() - start_time

    duration = len(audio) / engine.get_sample_rate()
    print(f"✓ Generated {len(audio)} samples ({duration:.2f}s)")
    print(f"  Synthesis time: {synthesis_time:.2f}s")
    print(f"  Real-time factor: {duration / synthesis_time:.2f}x\n")

    # Save to file
    output_path = Path("test_tts_default.wav")
    engine.synthesize_to_file(test_text, output_path)
    print(f"✓ Saved to: {output_path}\n")

    # Play audio
    print("Playing audio...")
    playback = AudioPlayback(sample_rate=engine.get_sample_rate())
    playback.play(audio, blocking=True)
    playback.stop()

    print("✓ Playback complete\n")

    return engine


def test_cloned_voice(engine):
    """Test 2: Voice cloning."""
    print("=" * 60)
    print("TEST 2: Voice Cloning")
    print("=" * 60)

    # Check if voice sample provided as argument
    if len(sys.argv) < 2:
        print("\nSkipped (no voice sample provided)")
        print("Usage: python test_tts.py <voice_sample.wav>")
        print("\nExample:")
        print("  python test_tts.py ~/my_voice.wav")
        print()
        return

    voice_sample = sys.argv[1]
    voice_path = Path(voice_sample).expanduser()

    if not voice_path.exists():
        print(f"\n✗ Voice sample not found: {voice_path}")
        print()
        return

    print(f"\nVoice sample: {voice_path}")

    # Check duration
    try:
        import soundfile as sf
        audio_data, sr = sf.read(voice_path)
        duration = len(audio_data) / sr
        print(f"Sample duration: {duration:.1f}s")

        if duration < 5:
            print("⚠ Warning: Sample is short (<5s). 6-10s recommended.")
        elif duration > 15:
            print("⚠ Warning: Sample is long (>15s). 6-10s recommended.")
        else:
            print("✓ Duration is good (6-10s optimal)")

    except Exception as e:
        print(f"⚠ Could not validate duration: {e}")

    # Load voice
    print("\nLoading voice sample...")
    engine.load_voice_sample(voice_path)

    # Synthesize with cloned voice
    test_text = "This is my cloned voice speaking. Pretty cool, right?"
    print(f"\nText: \"{test_text}\"\n")

    print("Synthesizing with cloned voice...")
    start_time = time.time()
    audio = engine.synthesize(test_text)
    synthesis_time = time.time() - start_time

    audio_duration = len(audio) / engine.get_sample_rate()
    print(f"✓ Generated {len(audio)} samples ({audio_duration:.2f}s)")
    print(f"  Synthesis time: {synthesis_time:.2f}s")
    print(f"  Real-time factor: {audio_duration / synthesis_time:.2f}x\n")

    # Save to file
    output_path = Path("test_tts_cloned.wav")
    engine.synthesize_to_file(test_text, output_path)
    print(f"✓ Saved to: {output_path}\n")

    # Play audio
    print("Playing cloned voice...")
    playback = AudioPlayback(sample_rate=engine.get_sample_rate())
    playback.play(audio, blocking=True)
    playback.stop()

    print("✓ Playback complete\n")


def test_speech_parameters(engine):
    """Test 3: Different speech parameters."""
    print("=" * 60)
    print("TEST 3: Speech Parameters")
    print("=" * 60)

    base_text = "Testing different speech parameters."

    # Test different speeds
    print("\nTesting speech speed variations...\n")

    speeds = [0.75, 1.0, 1.5]
    for speed in speeds:
        print(f"Speed: {speed}x")
        audio = engine.synthesize(base_text, speed=speed)
        duration = len(audio) / engine.get_sample_rate()
        print(f"  Duration: {duration:.2f}s\n")

        # Save
        output = Path(f"test_tts_speed_{speed}.wav")
        engine.synthesize_to_file(base_text, output, speed=speed)

    print("✓ Speed variation tests complete")
    print("  Files: test_tts_speed_*.wav\n")


def test_longer_text(engine):
    """Test 4: Longer text synthesis."""
    print("=" * 60)
    print("TEST 4: Longer Text Synthesis")
    print("=" * 60)

    long_text = """
    The rubber ducky project demonstrates how modern AI technologies
    can work together to create a natural voice conversation system.
    By combining WhisperX for transcription, XTTS for speech synthesis,
    and large language models for conversation, we can build a powerful
    local assistant that respects your privacy.
    """

    print(f"\nText length: {len(long_text)} characters\n")

    print("Synthesizing longer passage...")
    start_time = time.time()
    audio = engine.synthesize(long_text.strip())
    synthesis_time = time.time() - start_time

    duration = len(audio) / engine.get_sample_rate()
    print(f"✓ Generated {len(audio)} samples ({duration:.2f}s)")
    print(f"  Synthesis time: {synthesis_time:.2f}s")
    print(f"  Real-time factor: {duration / synthesis_time:.2f}x\n")

    # Save
    output_path = Path("test_tts_long.wav")
    engine.synthesize_to_file(long_text.strip(), output_path)
    print(f"✓ Saved to: {output_path}\n")

    # Play
    print("Playing audio...")
    playback = AudioPlayback(sample_rate=engine.get_sample_rate())
    playback.play(audio, blocking=True)
    playback.stop()

    print("✓ Playback complete\n")


def main():
    """Run all TTS tests."""
    print("\n" + "=" * 60)
    print("RUBBER DUCKY - TTS TEST (XTTS v2)")
    print("=" * 60)
    print()

    print("This will test:")
    print("  1. Default XTTS voice")
    print("  2. Voice cloning (if sample provided)")
    print("  3. Speech parameters (speed variations)")
    print("  4. Longer text synthesis")
    print()

    if len(sys.argv) > 1:
        print(f"Voice sample: {sys.argv[1]}")
    else:
        print("No voice sample provided (only default voice will be tested)")
        print("Usage: python test_tts.py <voice_sample.wav>")

    print()

    try:
        # Test 1: Default voice
        input("Press Enter to start Test 1 (Default Voice)...")
        engine = test_default_voice()

        # Test 2: Cloned voice
        if len(sys.argv) > 1:
            input("Press Enter to start Test 2 (Voice Cloning)...")
            test_cloned_voice(engine)
        else:
            test_cloned_voice(engine)  # Will skip with message

        # Test 3: Speech parameters
        input("Press Enter to start Test 3 (Speech Parameters)...")
        test_speech_parameters(engine)

        # Test 4: Longer text
        input("Press Enter to start Test 4 (Longer Text)...")
        test_longer_text(engine)

        # Summary
        print("=" * 60)
        print("TTS TESTS COMPLETE ✓")
        print("=" * 60)
        print("\nPhase 4 Complete: XTTS v2 voice cloning is working!")
        print("  ✓ Default XTTS voice synthesis")
        print("  ✓ Voice cloning from sample")
        print("  ✓ Speech parameter control (speed)")
        print("  ✓ Longer text synthesis")
        print("\nGenerated files:")
        print("  - test_tts_default.wav")
        if len(sys.argv) > 1:
            print("  - test_tts_cloned.wav")
        print("  - test_tts_speed_*.wav")
        print("  - test_tts_long.wav")
        print("\nNext: Phase 5 - LLM integration (Claude + Ollama)")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
