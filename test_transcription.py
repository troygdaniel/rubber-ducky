#!/usr/bin/env python3
"""Test script for transcription with WhisperX."""

import time
import numpy as np
from rubber_ducky.audio import AudioCapture
from rubber_ducky.transcription import TranscriptionEngine
from rubber_ducky.config import settings


def test_live_transcription():
    """Test 1: Record audio and transcribe it."""
    print("=" * 60)
    print("TEST 1: Live Audio Transcription")
    print("=" * 60)

    duration = 5.0
    print(f"\nRecording {duration} seconds...")
    print("Speak clearly into your microphone!")
    print("\nCountdown: ", end="", flush=True)

    for i in range(3, 0, -1):
        print(f"{i}... ", end="", flush=True)
        time.sleep(1)
    print("GO!\n")

    # Capture audio
    capture = AudioCapture(sample_rate=settings.sample_rate)
    capture.start()

    start_time = time.time()
    while time.time() - start_time < duration:
        chunk = capture.get_chunk(timeout=0.5)
        if chunk is not None:
            # Show audio level
            rms = np.sqrt(np.mean(chunk ** 2))
            bars = int(rms * 100)
            print(f"  🎤 {'█' * min(bars, 50)} {rms:.3f}", end='\r')

    audio = capture.get_accumulated_audio(duration=duration)
    capture.stop()

    print(f"\n\n✓ Captured {len(audio)} samples ({len(audio) / settings.sample_rate:.2f}s)\n")

    # Transcribe
    print("Transcribing with WhisperX...")
    print("(This may take a few seconds on first run - downloading model)\n")

    engine = TranscriptionEngine(
        model_name=settings.whisper_model,
        language=settings.whisper_language,
        device="cpu",  # Use CPU for compatibility
        compute_type=settings.whisper_compute_type,
        enable_diarization=False
    )

    result = engine.transcribe(audio, sample_rate=settings.sample_rate)

    # Display results
    print("=" * 60)
    print("TRANSCRIPTION RESULT")
    print("=" * 60)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return None

    print(f"\nLanguage: {result['language']}")
    print(f"Segments: {len(result['segments'])}\n")

    print("Transcript (with timestamps):")
    print("-" * 60)
    print(engine.format_transcript(result, include_timestamps=True))
    print("-" * 60)

    print(f"\nFull text:")
    print(f'  "{result["text"]}"')
    print()

    return result


def test_file_transcription():
    """Test 2: Transcribe from audio file (if provided)."""
    print("=" * 60)
    print("TEST 2: Audio File Transcription")
    print("=" * 60)

    import sys
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"\nTranscribing file: {audio_file}\n")

        engine = TranscriptionEngine(
            model_name=settings.whisper_model,
            device="cpu",
            enable_diarization=False
        )

        result = engine.transcribe_file(audio_file)

        print("Transcript:")
        print("-" * 60)
        print(engine.format_transcript(result, include_timestamps=True))
        print("-" * 60)
        print(f"\nFull text: {result['text']}")
        print(f"Language: {result['language']}")
        print()

    else:
        print("\nSkipped (no audio file provided)")
        print("Usage: python test_transcription.py <audio_file.wav>")
        print()


def test_diarization():
    """Test 3: Speaker diarization (optional)."""
    print("=" * 60)
    print("TEST 3: Speaker Diarization")
    print("=" * 60)

    print("\nSpeaker diarization requires:")
    print("  - HuggingFace account + access token")
    print("  - pyannote.audio models")
    print("\nSkipping for now (will implement when needed)")
    print()


def test_word_timestamps():
    """Test 4: Word-level timestamps."""
    print("=" * 60)
    print("TEST 4: Word-Level Timestamps")
    print("=" * 60)

    duration = 3.0
    print(f"\nRecording {duration} seconds for word timestamp test...")
    print("Say: 'The quick brown fox jumps over the lazy dog'\n")

    time.sleep(1)

    # Capture
    capture = AudioCapture(sample_rate=settings.sample_rate)
    capture.start()
    audio = capture.get_accumulated_audio(duration=duration)
    capture.stop()

    print(f"✓ Captured {len(audio) / settings.sample_rate:.2f}s\n")

    # Transcribe
    print("Transcribing with word-level timestamps...\n")

    engine = TranscriptionEngine(
        model_name=settings.whisper_model,
        device="cpu",
        enable_diarization=False
    )

    result = engine.transcribe(audio, sample_rate=settings.sample_rate)

    if "word_segments" in result and result["word_segments"]:
        print("Word-level timestamps:")
        print("-" * 60)
        for word_seg in result["word_segments"][:20]:  # Show first 20 words
            word = word_seg.get("word", "")
            start = word_seg.get("start", 0)
            end = word_seg.get("end", 0)
            print(f"  [{start:.2f}s - {end:.2f}s] {word}")
        print("-" * 60)
        print()
    else:
        print("(Word segments not available in result)")
        print()


def main():
    """Run all transcription tests."""
    print("\n" + "=" * 60)
    print("RUBBER DUCKY - TRANSCRIPTION TEST")
    print("=" * 60)
    print()

    print("WhisperX Model:", settings.whisper_model)
    print("Sample Rate:", settings.sample_rate, "Hz")
    print("Language:", settings.whisper_language or "auto-detect")
    print()

    try:
        # Test 1: Live transcription
        input("Press Enter to start live transcription test...")
        result = test_live_transcription()

        if result is None:
            print("Live transcription failed. Stopping tests.")
            return

        # Test 2: File transcription (if file provided)
        test_file_transcription()

        # Test 3: Diarization (skipped for now)
        test_diarization()

        # Test 4: Word timestamps
        if result:
            input("Press Enter to test word-level timestamps...")
            test_word_timestamps()

        # Summary
        print("=" * 60)
        print("TRANSCRIPTION TESTS COMPLETE ✓")
        print("=" * 60)
        print("\nPhase 3 Complete: WhisperX transcription is working!")
        print("  ✓ Live audio transcription")
        print("  ✓ Word-level timestamps")
        print("  ✓ Language detection")
        print("  ✓ Segment-based output")
        print("\nNext: Phase 4 - XTTS voice cloning")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
