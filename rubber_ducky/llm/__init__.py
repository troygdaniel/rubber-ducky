"""LLM provider abstraction layer."""

from rubber_ducky.llm.base import LLMProvider, Message, LLMResponse

# Lazy imports for providers (to avoid dependency errors)
__all__ = [
    "LLMProvider",
    "Message",
    "LLMResponse",
    "ClaudeProvider",
    "OllamaProvider",
]

def __getattr__(name):
    """Lazy import providers to avoid dependency errors."""
    if name == "ClaudeProvider":
        from rubber_ducky.llm.claude import ClaudeProvider
        return ClaudeProvider
    elif name == "OllamaProvider":
        from rubber_ducky.llm.ollama import OllamaProvider
        return OllamaProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
