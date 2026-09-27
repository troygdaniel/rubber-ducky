# Testing Guide

## Audio Pipeline Tests

### Quick Test

```bash
# Run all audio tests
python test_audio.py
```

### Individual Component Tests

**Test audio capture:**
```bash
python -m rubber_ducky.audio.capture
```

**Test audio playback:**
```bash
python -m rubber_ducky.audio.playback
```

**Test VAD:**
```bash
python -m rubber_ducky.audio.vad
```

## What Gets Tested

### Test 1: Audio Devices
- Lists all available microphones
- Lists all available speakers
- Shows default devices

### Test 2: Audio Playback
- Generates a 440 Hz test tone (A4 note)
- Plays through speakers
- Verifies sound output works

### Test 3: Audio Capture
- Records 3 seconds from microphone
- Shows real-time audio levels
- Verifies microphone input works

### Test 4: VAD (Voice Activity Detection)
- Analyzes recorded audio
- Detects speech vs silence
- Shows speech/silence breakdown

### Test 5: Roundtrip
- Records 2 seconds of audio
- Plays it back immediately
- Verifies full audio loop works

### Test 6: Live VAD
- Real-time speech detection
- Shows when you start/stop speaking
- Press Ctrl+C to stop

## Expected Results

**Working system:**
```
✓ Device listing works
✓ Audio playback works (you hear a tone)
✓ Captured X chunks (Y samples)
✓ VAD detected speech/silence
✓ Roundtrip works (you hear yourself)
✓ Live VAD works (responds to your speech)
```

## Troubleshooting

### No audio devices found
- Check microphone is connected
- Check speakers are connected
- Run `rubber-ducky devices` to list available devices

### Can't hear playback
- Check speaker volume
- Check correct output device selected
- Try different device: `AudioPlayback(device=INDEX)`

### Microphone not capturing
- Check microphone permissions (macOS/Linux)
- Check input volume/gain
- Try different device: `AudioCapture(device=INDEX)`

### VAD not detecting speech
- Speak louder/closer to microphone
- Adjust threshold: `VADEngine(threshold=0.3)` (lower = more sensitive)
- Check microphone levels in system settings

## Performance Benchmarks

Expected performance on modern hardware:

- **Audio capture latency:** < 100ms
- **Audio playback latency:** < 100ms
- **VAD detection time:** < 50ms per chunk
- **Total roundtrip:** < 300ms

## Next Steps

Once audio tests pass:
1. **Phase 3:** Add WhisperX transcription
2. **Phase 4:** Add XTTS voice cloning
3. **Phase 5:** Add LLM integration
4. **Phase 6:** Connect everything in conversation engine
