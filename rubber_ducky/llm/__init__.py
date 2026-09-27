"""LLM provider abstraction layer."""

from rubber_ducky.llm.base import LLMProvider, Message, LLMResponse
from rubber_ducky.llm.claude import ClaudeProvider
from rubber_ducky.llm.ollama import OllamaProvider

__all__ = [
    "LLMProvider",
    "Message",
    "LLMResponse",
    "ClaudeProvider",
    "OllamaProvider",
]
