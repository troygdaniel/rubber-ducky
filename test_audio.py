#!/usr/bin/env python3
"""Test script for audio pipeline (capture + VAD + playback)."""

import time
import numpy as np
from rubber_ducky.audio import AudioCapture, AudioPlayback, VADEngine
from rubber_ducky.config import settings


def test_devices():
    """Test 1: List available audio devices."""
    print("=" * 60)
    print("TEST 1: Audio Devices")
    print("=" * 60)

    from rubber_ducky.audio.capture import list_audio_devices, get_default_input_device
    from rubber_ducky.audio.playback import list_output_devices, get_default_output_device

    print(f"\nDefault input device: {get_default_input_device()}")
    print("\nInput devices (microphones):")
    for device in list_audio_devices():
        print(f"  [{device['index']}] {device['name']}")

    print(f"\nDefault output device: {get_default_output_device()}")
    print("\nOutput devices (speakers):")
    for device in list_output_devices():
        print(f"  [{device['index']}] {device['name']}")

    print("\n✓ Device listing works\n")


def test_playback():
    """Test 2: Audio playback with test tone."""
    print("=" * 60)
    print("TEST 2: Audio Playback")
    print("=" * 60)

    print("\nGenerating 440 Hz tone (A4 note)...")
    sample_rate = settings.sample_rate
    duration = 1.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    tone = 0.3 * np.sin(2 * np.pi * frequency * t)

    print(f"Playing {duration}s tone through speakers...")
    playback = AudioPlayback(sample_rate=sample_rate)
    playback.play(tone, blocking=True)

    print("✓ Audio playback works\n")


def test_capture():
    """Test 3: Audio capture from microphone."""
    print("=" * 60)
    print("TEST 3: Audio Capture")
    print("=" * 60)

    duration = 3.0
    print(f"\nRecording {duration} seconds from microphone...")
    print("(Make some noise!)\n")

    capture = AudioCapture(sample_rate=settings.sample_rate)
    capture.start()

    chunks = []
    start_time = time.time()

    while time.time() - start_time < duration:
        chunk = capture.get_chunk(timeout=0.5)
        if chunk is not None:
            chunks.append(chunk)
            # Calculate RMS to show activity
            rms = np.sqrt(np.mean(chunk ** 2))
            bars = int(rms * 100)
            print(f"  {'█' * min(bars, 50)} {rms:.3f}", end='\r')

    capture.stop()

    print(f"\n\n✓ Captured {len(chunks)} chunks ({sum(len(c) for c in chunks)} samples)")
    print(f"  Duration: {sum(len(c) for c in chunks) / settings.sample_rate:.2f}s\n")

    return chunks


def test_vad(audio_chunks):
    """Test 4: Voice Activity Detection."""
    print("=" * 60)
    print("TEST 4: Voice Activity Detection")
    print("=" * 60)

    print("\nAnalyzing captured audio with VAD...")
    vad = VADEngine(
        threshold=settings.vad_threshold,
        sample_rate=settings.sample_rate,
        min_speech_duration=settings.vad_min_speech_duration,
        min_silence_duration=settings.vad_min_silence_duration
    )

    speech_chunks = 0
    silence_chunks = 0

    for i, chunk in enumerate(audio_chunks):
        is_speech = vad.detect(chunk)

        if is_speech:
            speech_chunks += 1
            print(f"  Chunk {i+1:3d}: SPEECH", end='')
            silence = vad.get_silence_duration()
            if silence > 0:
                print(f" (silence: {silence:.2f}s)")
            else:
                print()
        else:
            silence_chunks += 1

    print(f"\n✓ VAD detected {speech_chunks} speech chunks, {silence_chunks} silence chunks\n")


def test_roundtrip():
    """Test 5: Full roundtrip (capture → playback)."""
    print("=" * 60)
    print("TEST 5: Audio Roundtrip")
    print("=" * 60)

    duration = 2.0
    print(f"\nRecording {duration}s from microphone...")
    print("(Say something!)\n")

    # Capture
    capture = AudioCapture(sample_rate=settings.sample_rate)
    capture.start()

    audio = capture.get_accumulated_audio(duration=duration)
    capture.stop()

    print(f"Captured {len(audio)} samples ({len(audio) / settings.sample_rate:.2f}s)")

    # Playback
    print("Playing back what you said...")
    time.sleep(0.5)  # Brief pause

    playback = AudioPlayback(sample_rate=settings.sample_rate)
    playback.play(audio, blocking=True)

    print("✓ Roundtrip works (you should have heard yourself)\n")


def test_vad_live():
    """Test 6: Live VAD detection."""
    print("=" * 60)
    print("TEST 6: Live VAD Detection")
    print("=" * 60)

    print("\nListening for speech (speak into microphone)...")
    print("Speech starts after 0.25s of speech")
    print("Speech ends after 0.8s of silence")
    print("\nPress Ctrl+C to stop\n")

    capture = AudioCapture(sample_rate=settings.sample_rate, chunk_duration=0.1)
    vad = VADEngine(
        threshold=settings.vad_threshold,
        sample_rate=settings.sample_rate,
        min_speech_duration=0.25,
        min_silence_duration=0.8
    )

    capture.start()

    try:
        while True:
            chunk = capture.get_chunk(timeout=0.2)
            if chunk is None:
                continue

            is_speech = vad.detect(chunk)

            if is_speech:
                silence = vad.get_silence_duration()
                if silence > 0:
                    print(f"  🎤 SPEECH (silence: {silence:.2f}s)     ", end='\r')
                else:
                    print("  🎤 SPEECH                    ", end='\r')
            else:
                print("  🔇 silence                   ", end='\r')

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\n✓ Live VAD works\n")
    finally:
        capture.stop()


def main():
    """Run all audio tests."""
    print("\n" + "=" * 60)
    print("RUBBER DUCKY - AUDIO PIPELINE TEST")
    print("=" * 60)
    print()

    try:
        # Test 1: Devices
        test_devices()

        # Test 2: Playback
        input("Press Enter to test audio playback (you'll hear a tone)...")
        test_playback()

        # Test 3: Capture
        input("Press Enter to test audio capture (3 second recording)...")
        chunks = test_capture()

        # Test 4: VAD on recorded audio
        if chunks:
            test_vad(chunks)

        # Test 5: Roundtrip
        input("Press Enter to test roundtrip (record + playback)...")
        test_roundtrip()

        # Test 6: Live VAD
        input("Press Enter to test live VAD (Ctrl+C to stop)...")
        test_vad_live()

        # Summary
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nPhase 2 Complete: Audio pipeline is working!")
        print("  ✓ Audio capture (microphone)")
        print("  ✓ Audio playback (speakers)")
        print("  ✓ Voice Activity Detection (VAD)")
        print("  ✓ Roundtrip (capture → playback)")
        print("\nNext: Phase 3 - WhisperX transcription")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
