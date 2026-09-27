"""Claude API provider using Anthropic SDK."""

from typing import List, Optional, Iterator
import anthropic

from rubber_ducky.llm.base import LLMProvider, Message, LLMResponse


class ClaudeProvider(LLMProvider):
    """LLM provider for Anthropic's Claude API.

    Uses the official Anthropic SDK to interact with Claude models.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        default_system_prompt: Optional[str] = None
    ):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            default_system_prompt: Default system prompt for all requests
        """
        self.api_key = api_key
        self.model = model
        self.default_system_prompt = default_system_prompt
        self.client = anthropic.Anthropic(api_key=api_key)

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
            system_prompt: Optional system prompt (overrides default)
            temperature: Sampling temperature (0.0-1.0 for Claude)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic API parameters

        Returns:
            LLMResponse with generated text
        """
        # Use provided system prompt, fall back to default, or None
        system = system_prompt or self.default_system_prompt

        # Build request
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }

        if system:
            request_params["system"] = system

        # Make API call
        response = self.client.messages.create(**request_params)

        # Extract text from response
        text = response.content[0].text if response.content else ""

        return LLMResponse(
            text=text,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason
        )

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
            temperature: Sampling temperature (0.0-1.0 for Claude)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic API parameters

        Returns:
            LLMResponse with generated text
        """
        self.validate_messages(messages)

        # Extract system message if present
        system = None
        chat_messages = messages

        if messages and messages[0].role == "system":
            system = messages[0].content
            chat_messages = messages[1:]

        # Use default system prompt if no system message provided
        if system is None and self.default_system_prompt:
            system = self.default_system_prompt

        # Convert to Anthropic format
        api_messages = [msg.to_dict() for msg in chat_messages]

        # Build request
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages,
            **kwargs
        }

        if system:
            request_params["system"] = system

        # Make API call
        response = self.client.messages.create(**request_params)

        # Extract text from response
        text = response.content[0].text if response.content else ""

        return LLMResponse(
            text=text,
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason
        )

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
            system_prompt: Optional system prompt (overrides default)
            temperature: Sampling temperature (0.0-1.0 for Claude)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic API parameters

        Yields:
            Text chunks as they're generated
        """
        # Use provided system prompt, fall back to default, or None
        system = system_prompt or self.default_system_prompt

        # Build request
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }

        if system:
            request_params["system"] = system

        # Stream response
        with self.client.messages.stream(**request_params) as stream:
            for text in stream.text_stream:
                yield text

    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier string
        """
        return self.model


# Test function
if __name__ == "__main__":
    import os
    from pathlib import Path

    print("Testing ClaudeProvider...")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("RUBBER_DUCKY_CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ No API key found")
        print("Set RUBBER_DUCKY_CLAUDE_API_KEY or ANTHROPIC_API_KEY environment variable")
        exit(1)

    # Create provider
    provider = ClaudeProvider(
        api_key=api_key,
        model="claude-sonnet-4-5-20250929",
        default_system_prompt="You are a helpful voice assistant."
    )

    print(f"Model: {provider.get_model_name()}\n")

    # Test 1: Simple generation
    print("Test 1: Simple generation")
    print("-" * 60)

    prompt = "What is the capital of France? Answer in one sentence."
    print(f"Prompt: {prompt}\n")

    response = provider.generate(prompt, max_tokens=100)
    print(f"Response: {response.text}")
    print(f"Tokens: {response.tokens_used}")
    print(f"Finish: {response.finish_reason}\n")

    # Test 2: Conversation
    print("Test 2: Conversation")
    print("-" * 60)

    messages = [
        Message(role="system", content="You are a helpful voice assistant. Be concise."),
        Message(role="user", content="Hi! What's your name?"),
        Message(role="assistant", content="I'm Claude, an AI assistant created by Anthropic."),
        Message(role="user", content="What can you help me with?")
    ]

    print("Conversation:")
    for msg in messages:
        print(f"  {msg.role}: {msg.content}")
    print()

    response = provider.chat(messages, max_tokens=150)
    print(f"Response: {response.text}")
    print(f"Tokens: {response.tokens_used}\n")

    # Test 3: Streaming
    print("Test 3: Streaming")
    print("-" * 60)

    prompt = "Count from 1 to 5, one number per line."
    print(f"Prompt: {prompt}\n")
    print("Streaming response:")

    for chunk in provider.stream(prompt, max_tokens=100):
        print(chunk, end="", flush=True)

    print("\n")
    print("=" * 60)
    print("✓ ClaudeProvider tests complete")
