"""SQLAlchemy models for conversation storage."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Conversation(Base):
    """Conversation session model."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    llm_provider = Column(String(20), nullable=False)  # 'claude' or 'ollama'
    llm_model = Column(String(100), nullable=False)
    voice_sample = Column(String(255), nullable=True)

    turns = relationship("Turn", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, started={self.started_at}, provider={self.llm_provider})>"


class Turn(Base):
    """Individual turn in a conversation (user or assistant)."""

    __tablename__ = "turns"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    speaker = Column(String(20), nullable=False)  # 'user' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # User turn data
    audio_duration = Column(Float, nullable=True)  # seconds
    transcription = Column(Text, nullable=True)
    diarization_speakers = Column(Integer, nullable=True)  # Number of speakers detected

    # Assistant turn data
    llm_response = Column(Text, nullable=True)
    tts_duration = Column(Float, nullable=True)  # Time to generate TTS

    # Status
    interrupted = Column(Boolean, default=False)  # True if turn was interrupted

    conversation = relationship("Conversation", back_populates="turns")

    def __repr__(self):
        return f"<Turn(id={self.id}, speaker={self.speaker}, turn={self.turn_number})>"
