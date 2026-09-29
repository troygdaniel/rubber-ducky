"""Main conversation engine integrating all components."""

import time
import numpy as np
import warnings
import threading
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Suppress torchcodec/torchaudio warnings (non-critical, uses fallback)
warnings.filterwarnings("ignore", message=".*torchcodec.*")
warnings.filterwarnings("ignore", message=".*torchaudio.*")

from rubber_ducky.audio import AudioCapture, AudioPlayback, VADEngine
from rubber_ducky.transcription import TranscriptionEngine
from rubber_ducky.tts import TTSEngine
from rubber_ducky.llm import Message, ClaudeProvider, OllamaProvider
from rubber_ducky.conversation.turn_manager import TurnManager, TurnState
from rubber_ducky.storage.database import SessionLocal
from rubber_ducky.storage.models import Conversation, Turn as DBTurn
from rubber_ducky.config import settings


class ConversationEngine:
    """Main conversation engine.

    Integrates all components into a complete voice conversation system:
    - Audio capture with VAD
    - Speech-to-text (WhisperX)
    - LLM conversation (Claude/Ollama)
    - Text-to-speech (XTTS v2)
    - Turn-taking and state management
    """

    def __init__(self, config=None, debug: bool = False, push_to_talk: bool = False):
        """Initialize conversation engine.

        Args:
            config: Settings object (defaults to global settings)
            debug: Enable debug output
            push_to_talk: Use push-to-talk mode (hold spacebar to record)
        """
        self.config = config or settings
        self.debug = debug
        self.push_to_talk = push_to_talk
        self.console = Console()

        # Components (lazy loaded)
        self.audio_capture: Optional[AudioCapture] = None
        self.audio_playback: Optional[AudioPlayback] = None
        self.vad: Optional[VADEngine] = None
        self.transcription: Optional[TranscriptionEngine] = None
        self.tts: Optional[TTSEngine] = None
        self.llm = None

        # State
        self.turn_manager = TurnManager(
            sample_rate=self.config.sample_rate,
            min_silence_duration=self.config.vad_min_silence_duration,
            min_speech_duration=self.config.vad_min_speech_duration
        )

        self.running = False
        self.conversation_id: Optional[int] = None

        # Push-to-talk state
        self.recording = False
        self.input_thread = None

        # System prompt for LLM
        self.system_prompt = self.config.conversation_system_prompt

    def _input_thread_fn(self):
        """Thread function to wait for Enter key in push-to-talk mode."""
        while self.running:
            try:
                # Wait for Enter key (blocking)
                input()

                if not self.push_to_talk:
                    continue

                # Toggle recording state
                if not self.recording:
                    # Start recording
                    if self.turn_manager.state == TurnState.LISTENING:
                        self.recording = True
                        self.turn_manager.start_turn(speaker="user")
                        self.turn_manager.state = TurnState.SPEAKING
                        self.console.print("[green]🎤 Recording... (press Enter again to stop)[/green]")
                else:
                    # Stop recording
                    if self.turn_manager.state == TurnState.SPEAKING:
                        self.recording = False
                        duration = self.turn_manager.get_audio_duration()
                        if duration > 0.3:  # Minimum 300ms
                            self.console.print(f"[dim]Stopped recording ({duration:.1f}s)[/dim]\n")
                            self.turn_manager.state = TurnState.PROCESSING
                        else:
                            # Too short, cancel
                            self.turn_manager.accumulated_audio = []
                            self.turn_manager.state = TurnState.LISTENING
                            self.console.print("[yellow]Recording too short, try again[/yellow]")
            except:
                break

    def initialize_components(self):
        """Initialize all components (lazy loading)."""
        self.console.print("[yellow]Initializing components...[/yellow]")

        # Audio I/O
        self.audio_capture = AudioCapture(sample_rate=self.config.sample_rate)
        self.audio_playback = AudioPlayback(sample_rate=self.config.sample_rate)
        self.console.print("✓ Audio I/O ready")

        # VAD
        self.vad = VADEngine(
            sample_rate=self.config.sample_rate,
            threshold=self.config.vad_threshold,
            min_speech_duration=self.config.vad_min_speech_duration,
            min_silence_duration=self.config.vad_min_silence_duration
        )
        self.console.print("✓ VAD ready")

        # Transcription (WhisperX)
        self.console.print(f"Loading WhisperX ({self.config.whisper_model})...")
        self.transcription = TranscriptionEngine(
            model_name=self.config.whisper_model,
            language=self.config.whisper_language,
            device=self.config.whisper_device,
            compute_type=self.config.whisper_compute_type,
            enable_diarization=False
        )
        self.console.print("✓ Transcription ready")

        # TTS (XTTS v2)
        self.console.print("Loading XTTS v2...")
        self.tts = TTSEngine(
            voice_sample=self.config.xtts_voice_sample,
            device=self.config.xtts_device
        )
        # Load model now (not lazily) to avoid delay on first response
        self.tts.load_model()
        self.console.print("✓ TTS ready")

        # LLM
        if self.config.llm_provider == "claude":
            if not self.config.claude_api_key:
                raise ValueError("Claude API key not configured")
            self.llm = ClaudeProvider(
                api_key=self.config.claude_api_key,
                model=self.config.claude_model,
                default_system_prompt=self.system_prompt
            )
            self.console.print(f"✓ LLM ready (Claude: {self.config.claude_model})")
        else:
            self.llm = OllamaProvider(
                base_url=self.config.ollama_base_url,
                model=self.config.ollama_model,
                default_system_prompt=self.system_prompt
            )
            if not self.llm.is_available():
                raise RuntimeError("Ollama is not running. Start with: ollama serve")
            self.console.print(f"✓ LLM ready (Ollama: {self.config.ollama_model})")

        self.console.print("[green]All components initialized![/green]\n")

    def start(self):
        """Start the conversation loop."""
        self.running = True

        try:
            # Initialize components
            self.initialize_components()

            # Create database conversation record
            self.create_conversation_record()

            # Show instructions
            self.show_instructions()

            # Start input thread if push-to-talk
            if self.push_to_talk:
                self.input_thread = threading.Thread(target=self._input_thread_fn, daemon=True)
                self.input_thread.start()

            # Start audio capture
            self.audio_capture.start()

            # Main loop
            if self.push_to_talk:
                self.console.print("[cyan]Ready (press Enter to start recording)...[/cyan]\n")
            else:
                self.console.print("[cyan]Listening...[/cyan]\n")
            self.main_loop()

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Conversation ended by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            if self.debug:
                import traceback
                traceback.print_exc()
        finally:
            self.cleanup()

    def main_loop(self):
        """Main conversation loop with state machine."""
        while self.running:
            state = self.turn_manager.state

            if state == TurnState.LISTENING:
                self.handle_listening()

            elif state == TurnState.SPEAKING:
                self.handle_speaking()

            elif state == TurnState.PROCESSING:
                self.handle_processing()

            elif state == TurnState.PLAYING:
                self.handle_playing()

            time.sleep(0.01)  # Prevent busy loop

    def handle_listening(self):
        """Handle LISTENING state - monitor for speech start."""
        # In push-to-talk mode, keyboard handles state transitions
        if self.push_to_talk:
            time.sleep(0.01)
            return

        # Get audio chunk
        chunk = self.audio_capture.get_chunk(timeout=0.1)
        if chunk is None:
            return

        # Check for speech
        is_speech = self.vad.detect(chunk)

        if is_speech:
            # Speech detected - start user turn
            if self.debug:
                self.console.print("[dim]Speech detected[/dim]")

            self.turn_manager.start_turn(speaker="user")
            self.turn_manager.add_audio(chunk)
            self.turn_manager.update_speech_state(is_speech=True)
            self.turn_manager.state = TurnState.SPEAKING

            self.console.print("[green]🎤 You're speaking...[/green]")

    def handle_speaking(self):
        """Handle SPEAKING state - accumulate user speech."""
        # Get audio chunk
        chunk = self.audio_capture.get_chunk(timeout=0.1)
        if chunk is None:
            return

        # Add to turn
        self.turn_manager.add_audio(chunk)

        # In push-to-talk mode, keyboard handles when to stop
        if self.push_to_talk:
            return

        # Check for speech/silence (VAD mode only)
        is_speech = self.vad.detect(chunk)
        self.turn_manager.update_speech_state(is_speech)

        # Check if turn should end
        if self.turn_manager.should_end_turn():
            duration = self.turn_manager.get_audio_duration()
            self.console.print(f"[dim]Speech ended ({duration:.1f}s)[/dim]\n")

            self.turn_manager.state = TurnState.PROCESSING

    def handle_processing(self):
        """Handle PROCESSING state - transcribe, LLM, TTS."""
        # Get user audio
        user_audio = self.turn_manager.get_accumulated_audio()

        if len(user_audio) == 0:
            # No audio - back to listening
            self.turn_manager.state = TurnState.LISTENING
            return

        # Step 1: Transcribe
        self.console.print("[cyan]Transcribing...[/cyan]")
        transcription_start = time.time()

        result = self.transcription.transcribe(user_audio, sample_rate=self.config.sample_rate)
        user_text = result.get("text", "").strip()

        transcription_time = time.time() - transcription_start

        if not user_text:
            self.console.print("[yellow]Could not understand speech. Try again.[/yellow]\n")
            self.turn_manager.end_turn(text="[inaudible]", speaker="user")
            self.turn_manager.state = TurnState.LISTENING
            self.console.print("[cyan]Listening...[/cyan]\n")
            return

        # Save user turn
        user_turn = self.turn_manager.end_turn(text=user_text, speaker="user")
        self.save_turn_to_db(user_turn)

        self.console.print(f"[bold blue]You:[/bold blue] {user_text}")
        if self.debug:
            self.console.print(f"[dim](transcribed in {transcription_time:.2f}s)[/dim]")

        # Step 2: Get LLM response
        self.console.print("[cyan]Thinking...[/cyan]")
        llm_start = time.time()

        # Build conversation history
        messages = self.build_llm_messages()

        if self.debug:
            self.console.print(f"[dim]Messages to LLM: {len(messages)} messages[/dim]")
            for msg in messages:
                self.console.print(f"[dim]  {msg.role}: {msg.content[:50]}...[/dim]")

        llm_response = self.llm.chat(
            messages,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens
        )
        assistant_text = llm_response.text.strip()

        if self.debug:
            self.console.print(f"[dim]Raw LLM response: '{llm_response.text}'[/dim]")
            self.console.print(f"[dim]Stripped text: '{assistant_text}'[/dim]")

        llm_time = time.time() - llm_start

        # Handle empty response
        if not assistant_text:
            self.console.print("[yellow]LLM returned empty response. Returning to listening.[/yellow]\n")
            self.turn_manager.state = TurnState.LISTENING
            self.console.print("[cyan]Listening...[/cyan]\n")
            return

        self.console.print(f"[bold green]Assistant:[/bold green] {assistant_text}")
        if self.debug:
            self.console.print(f"[dim](generated in {llm_time:.2f}s, {llm_response.tokens_used} tokens)[/dim]")

        # Step 3: Generate TTS
        self.console.print("[cyan]Speaking...[/cyan]")
        tts_start = time.time()

        assistant_audio = self.tts.synthesize(assistant_text)
        tts_time = time.time() - tts_start

        if self.debug:
            duration = len(assistant_audio) / self.tts.get_sample_rate()
            self.console.print(f"[dim](synthesized {duration:.1f}s in {tts_time:.2f}s)[/dim]")

        # Save assistant turn
        self.turn_manager.start_turn(speaker="assistant")
        assistant_turn = self.turn_manager.end_turn(text=assistant_text, speaker="assistant")
        assistant_turn.audio = assistant_audio  # Store TTS audio
        assistant_turn.duration = len(assistant_audio) / self.tts.get_sample_rate()
        self.save_turn_to_db(assistant_turn)

        # Step 4: Play response
        self.turn_manager.state = TurnState.PLAYING

        # Note: TTS sample rate is 24kHz, playback expects 16kHz by default
        # We need to resample the audio
        resampled_audio = self.resample_audio(
            assistant_audio,
            from_rate=self.tts.get_sample_rate(),
            to_rate=self.config.sample_rate
        )

        self.audio_playback.play(resampled_audio, blocking=False)

    def handle_playing(self):
        """Handle PLAYING state - wait for playback to finish.

        NOTE: Interruption detection is disabled to prevent echo/feedback.
        The system was hearing its own voice and treating it as user input.
        To re-enable interruptions, add proper acoustic echo cancellation.
        """
        # Check if still playing
        if not self.audio_playback.is_playing:
            # Finished playing
            self.console.print("[cyan]Listening...[/cyan]\n")
            self.turn_manager.state = TurnState.LISTENING
            return

        # Just wait - don't check for interruption to avoid feedback loop
        time.sleep(0.1)

    def build_llm_messages(self):
        """Build message history for LLM.

        Returns:
            List of Message objects
        """
        messages = []

        # Add system prompt
        if self.system_prompt:
            messages.append(Message(role="system", content=self.system_prompt))

        # Add recent conversation history
        for turn in self.turn_manager.turn_history[-10:]:  # Last 10 turns
            if turn.text:
                role = "user" if turn.speaker == "user" else "assistant"
                messages.append(Message(role=role, content=turn.text))

        return messages

    def resample_audio(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio from one sample rate to another.

        Args:
            audio: Audio data
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

    def create_conversation_record(self):
        """Create database record for this conversation."""
        try:
            db = SessionLocal()
            conversation = Conversation(
                llm_provider=self.config.llm_provider,
                llm_model=self.llm.get_model_name(),
                voice_sample=str(self.config.xtts_voice_sample) if self.config.xtts_voice_sample else None
            )
            db.add(conversation)
            db.commit()
            self.conversation_id = conversation.id
            db.close()
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not create conversation record: {e}[/yellow]")

    def save_turn_to_db(self, turn):
        """Save turn to database.

        Args:
            turn: Turn object from TurnManager
        """
        if not self.conversation_id:
            return

        try:
            db = SessionLocal()

            # Convert float timestamp to datetime if needed
            timestamp = turn.timestamp
            if isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp)

            db_turn = DBTurn(
                conversation_id=self.conversation_id,
                turn_number=turn.turn_number,
                speaker=turn.speaker,
                transcription=turn.text if turn.speaker == "user" else None,
                llm_response=turn.text if turn.speaker == "assistant" else None,
                audio_duration=turn.duration,
                timestamp=timestamp
            )
            db.add(db_turn)
            db.commit()
            db.close()
        except Exception as e:
            if self.debug:
                self.console.print(f"[dim]Warning: Could not save turn: {e}[/dim]")

    def show_instructions(self):
        """Show user instructions."""
        instructions = Text()
        instructions.append("Voice Conversation Started\n\n", style="bold cyan")
        instructions.append("How to use:\n", style="bold")
        if self.push_to_talk:
            instructions.append("• Press ENTER to start recording\n")
            instructions.append("• Press ENTER again to stop and send\n")
            instructions.append("• Assistant will respond automatically\n")
            instructions.append("• Press Ctrl+C to exit\n\n")
            instructions.append("Mode: Push-to-talk\n", style="yellow")
        else:
            instructions.append("• Just speak naturally\n")
            instructions.append("• Wait for silence detection to end your turn\n")
            instructions.append("• Assistant responds automatically\n")
            instructions.append("• Press Ctrl+C to exit\n\n")
            instructions.append("Mode: Voice activity detection\n", style="yellow")
        instructions.append(f"LLM: {self.llm.get_model_name()}\n", style="dim")
        instructions.append(f"Voice: {self.config.xtts_voice_sample or 'default'}", style="dim")

        self.console.print(Panel(instructions, title="Rubber Ducky 🦆", border_style="cyan"))
        self.console.print()

    def cleanup(self):
        """Clean up resources."""
        self.running = False

        # Input thread is daemon, will stop when main thread stops

        if self.audio_capture:
            self.audio_capture.stop()

        if self.audio_playback:
            self.audio_playback.stop()

        # Show conversation summary
        if self.turn_manager.turn_history:
            self.console.print("\n" + "=" * 60)
            self.console.print("[bold]Conversation Summary[/bold]")
            self.console.print("=" * 60)

            stats = self.turn_manager.get_statistics()
            for key, value in stats.items():
                self.console.print(f"  {key}: {value}")

            self.console.print("=" * 60)


# Test/Demo function
if __name__ == "__main__":
    import sys

    print("Starting Rubber Ducky conversation engine...")
    print("Press Ctrl+C to stop\n")

    engine = ConversationEngine(debug=True)

    try:
        engine.start()
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
