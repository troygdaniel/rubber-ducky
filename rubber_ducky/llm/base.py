"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass


@dataclass
class Message:
    """A message in a conversation.

    Attributes:
        role: 'user', 'assistant', or 'system'
        content: The message text
    """
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Response from an LLM provider.

    Attributes:
        text: The generated response text
        model: Model that generated the response
        tokens_used: Total tokens used (if available)
        finish_reason: Why generation stopped (if available)
    """
    text: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Provides a unified interface for different LLM backends
    (Claude API, Ollama, etc.).
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response to a single prompt.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific options

        Returns:
            LLMResponse with generated text
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> LLMResponse:
        """Generate a response to a conversation.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific options

        Returns:
            LLMResponse with generated text
        """
        pass

    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> Iterator[str]:
        """Stream a response to a prompt.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific options

        Yields:
            Text chunks as they're generated
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier string
        """
        pass

    def format_conversation_history(
        self,
        messages: List[Message],
        max_messages: Optional[int] = None
    ) -> List[Message]:
        """Format conversation history for the provider.

        Args:
            messages: Full conversation history
            max_messages: Maximum messages to include (most recent)

        Returns:
            Formatted message list
        """
        if max_messages is not None and len(messages) > max_messages:
            # Keep system message if present, then most recent messages
            if messages and messages[0].role == "system":
                return [messages[0]] + messages[-(max_messages - 1):]
            else:
                return messages[-max_messages:]
        return messages

    def validate_messages(self, messages: List[Message]) -> None:
        """Validate message format.

        Args:
            messages: Messages to validate

        Raises:
            ValueError: If messages are invalid
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        valid_roles = {"user", "assistant", "system"}
        for msg in messages:
            if msg.role not in valid_roles:
                raise ValueError(f"Invalid role: {msg.role}. Must be user, assistant, or system")
            if not msg.content or not msg.content.strip():
                raise ValueError("Message content cannot be empty")

        # Check role ordering
        if messages[0].role == "system":
            # System message must be first
            for msg in messages[1:]:
                if msg.role == "system":
                    raise ValueError("System message must be first in conversation")
