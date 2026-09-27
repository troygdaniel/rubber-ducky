"""Turn manager for conversation flow and turn-taking logic."""

import numpy as np
import time
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class TurnState(Enum):
    """Turn states for conversation management."""
    LISTENING = "listening"      # Waiting for speech
    SPEAKING = "speaking"        # User is speaking
    PROCESSING = "processing"    # Transcribing + LLM + TTS
    PLAYING = "playing"          # Playing assistant response
    INTERRUPTION = "interruption"  # User interrupted


@dataclass
class Turn:
    """Represents a single turn in the conversation.

    Attributes:
        turn_number: Sequential turn number
        speaker: 'user' or 'assistant'
        audio: Audio data (if user turn)
        text: Transcribed text (user) or response text (assistant)
        timestamp: When the turn started
        duration: Audio duration in seconds
        interrupted: Whether this turn was interrupted
    """
    turn_number: int
    speaker: str
    audio: Optional[np.ndarray] = None
    text: Optional[str] = None
    timestamp: Optional[float] = None
    duration: Optional[float] = None
    interrupted: bool = False


class TurnManager:
    """Manages conversation turns and state transitions.

    Handles:
    - Turn-taking logic with VAD
    - Speech/silence duration tracking
    - Turn history
    - Interruption detection
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        min_silence_duration: float = 0.8,  # Silence before turn end
        min_speech_duration: float = 0.3   # Min speech to count as turn
    ):
        """Initialize turn manager.

        Args:
            sample_rate: Audio sample rate
            min_silence_duration: Seconds of silence before ending turn
            min_speech_duration: Minimum speech duration to count as turn
        """
        self.sample_rate = sample_rate
        self.min_silence_duration = min_silence_duration
        self.min_speech_duration = min_speech_duration

        # State
        self.state = TurnState.LISTENING
        self.turn_history: List[Turn] = []
        self.current_turn_number = 0

        # Audio accumulation for current turn
        self.accumulated_audio: List[np.ndarray] = []
        self.turn_start_time: Optional[float] = None

        # Timing tracking
        self.last_speech_time: Optional[float] = None
        self.last_silence_time: Optional[float] = None

    def start_turn(self, speaker: str = "user"):
        """Start a new turn.

        Args:
            speaker: 'user' or 'assistant'
        """
        self.current_turn_number += 1
        self.accumulated_audio = []
        self.turn_start_time = time.time()
        self.state = TurnState.SPEAKING if speaker == "user" else TurnState.PROCESSING

    def add_audio(self, audio_chunk: np.ndarray):
        """Add audio chunk to current turn.

        Args:
            audio_chunk: Audio data to add
        """
        self.accumulated_audio.append(audio_chunk)

    def get_accumulated_audio(self) -> np.ndarray:
        """Get accumulated audio for current turn.

        Returns:
            Concatenated audio as numpy array
        """
        if not self.accumulated_audio:
            return np.array([], dtype=np.float32)

        return np.concatenate(self.accumulated_audio)

    def get_audio_duration(self) -> float:
        """Get duration of accumulated audio.

        Returns:
            Duration in seconds
        """
        audio = self.get_accumulated_audio()
        return len(audio) / self.sample_rate

    def update_speech_state(self, is_speech: bool) -> None:
        """Update speech/silence timing.

        Args:
            is_speech: Whether current chunk contains speech
        """
        current_time = time.time()

        if is_speech:
            self.last_speech_time = current_time
            self.last_silence_time = None
        else:
            if self.last_silence_time is None:
                self.last_silence_time = current_time

    def get_silence_duration(self) -> float:
        """Get duration of current silence.

        Returns:
            Silence duration in seconds
        """
        if self.last_silence_time is None:
            return 0.0

        return time.time() - self.last_silence_time

    def should_end_turn(self) -> bool:
        """Check if current turn should end.

        Turn ends when:
        - Silence duration exceeds threshold
        - Audio duration is sufficient

        Returns:
            True if turn should end
        """
        silence_duration = self.get_silence_duration()
        audio_duration = self.get_audio_duration()

        # Need minimum speech duration
        if audio_duration < self.min_speech_duration:
            return False

        # End on sufficient silence
        return silence_duration >= self.min_silence_duration

    def end_turn(
        self,
        text: Optional[str] = None,
        interrupted: bool = False
    ) -> Turn:
        """End current turn and add to history.

        Args:
            text: Transcribed or generated text
            interrupted: Whether turn was interrupted

        Returns:
            Completed Turn object
        """
        audio = self.get_accumulated_audio()
        duration = self.get_audio_duration()

        turn = Turn(
            turn_number=self.current_turn_number,
            speaker="user" if self.state == TurnState.SPEAKING else "assistant",
            audio=audio if len(audio) > 0 else None,
            text=text,
            timestamp=self.turn_start_time,
            duration=duration,
            interrupted=interrupted
        )

        self.turn_history.append(turn)

        # Reset for next turn
        self.accumulated_audio = []
        self.turn_start_time = None
        self.last_speech_time = None
        self.last_silence_time = None

        return turn

    def get_conversation_text(self, max_turns: Optional[int] = None) -> str:
        """Get conversation as formatted text.

        Args:
            max_turns: Maximum number of recent turns to include

        Returns:
            Formatted conversation string
        """
        turns = self.turn_history
        if max_turns:
            turns = turns[-max_turns:]

        lines = []
        for turn in turns:
            if turn.text:
                speaker_label = turn.speaker.upper()
                lines.append(f"{speaker_label}: {turn.text}")

        return "\n".join(lines)

    def get_user_turns(self) -> List[Turn]:
        """Get all user turns.

        Returns:
            List of user turns
        """
        return [t for t in self.turn_history if t.speaker == "user"]

    def get_assistant_turns(self) -> List[Turn]:
        """Get all assistant turns.

        Returns:
            List of assistant turns
        """
        return [t for t in self.turn_history if t.speaker == "assistant"]

    def get_last_turn(self) -> Optional[Turn]:
        """Get the most recent turn.

        Returns:
            Last turn or None
        """
        return self.turn_history[-1] if self.turn_history else None

    def clear_history(self):
        """Clear conversation history."""
        self.turn_history = []
        self.current_turn_number = 0

    def get_statistics(self) -> dict:
        """Get conversation statistics.

        Returns:
            Dictionary with stats
        """
        user_turns = self.get_user_turns()
        assistant_turns = self.get_assistant_turns()

        user_duration = sum(t.duration for t in user_turns if t.duration)
        assistant_duration = sum(t.duration for t in assistant_turns if t.duration)

        interrupted_turns = len([t for t in self.turn_history if t.interrupted])

        return {
            "total_turns": len(self.turn_history),
            "user_turns": len(user_turns),
            "assistant_turns": len(assistant_turns),
            "user_speaking_time": user_duration,
            "assistant_speaking_time": assistant_duration,
            "interrupted_turns": interrupted_turns,
            "current_state": self.state.value
        }


# Test function
if __name__ == "__main__":
    print("Testing TurnManager...")
    print("=" * 60)

    # Create manager
    manager = TurnManager(sample_rate=16000, min_silence_duration=0.8)

    print(f"Initial state: {manager.state.value}\n")

    # Simulate Turn 1: User speaks
    print("Turn 1: User speaking...")
    manager.start_turn(speaker="user")
    manager.state = TurnState.SPEAKING

    # Add some audio chunks
    for i in range(5):
        chunk = np.random.randn(1600).astype(np.float32)  # 0.1s of audio
        manager.add_audio(chunk)
        manager.update_speech_state(is_speech=True)

    # Add silence
    for i in range(10):
        chunk = np.random.randn(1600).astype(np.float32) * 0.01
        manager.add_audio(chunk)
        manager.update_speech_state(is_speech=False)
        time.sleep(0.1)

        if manager.should_end_turn():
            break

    print(f"  Audio duration: {manager.get_audio_duration():.2f}s")
    print(f"  Silence duration: {manager.get_silence_duration():.2f}s")
    print(f"  Should end: {manager.should_end_turn()}")

    turn1 = manager.end_turn(text="Hello, how are you?")
    print(f"  ✓ Turn ended: {turn1.speaker} said '{turn1.text}'")
    print()

    # Simulate Turn 2: Assistant responds
    print("Turn 2: Assistant responding...")
    manager.start_turn(speaker="assistant")
    turn2 = manager.end_turn(text="I'm doing well, thanks!", interrupted=False)
    print(f"  ✓ Turn ended: {turn2.speaker} said '{turn2.text}'")
    print()

    # Get conversation
    print("Conversation so far:")
    print("-" * 60)
    print(manager.get_conversation_text())
    print("-" * 60)
    print()

    # Statistics
    stats = manager.get_statistics()
    print("Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()

    print("=" * 60)
    print("✓ TurnManager test complete")
