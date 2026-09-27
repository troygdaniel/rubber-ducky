"""Ollama provider for local LLM inference."""

from typing import List, Optional, Iterator
import httpx
import json

from rubber_ducky.llm.base import LLMProvider, Message, LLMResponse


class OllamaProvider(LLMProvider):
    """LLM provider for Ollama local models.

    Communicates with Ollama via HTTP API for local LLM inference.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        default_system_prompt: Optional[str] = None,
        timeout: float = 300.0
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama API base URL
            model: Model name (must be pulled via `ollama pull`)
            default_system_prompt: Default system prompt for all requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.default_system_prompt = default_system_prompt
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

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
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama API parameters

        Returns:
            LLMResponse with generated text
        """
        # Use provided system prompt, fall back to default, or None
        system = system_prompt or self.default_system_prompt

        # Build request
        request_data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs.get("options", {})
            }
        }

        if system:
            request_data["system"] = system

        # Make API call
        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json=request_data
            )
            response.raise_for_status()
            result = response.json()

            return LLMResponse(
                text=result.get("response", ""),
                model=result.get("model", self.model),
                tokens_used=result.get("eval_count"),
                finish_reason=result.get("done_reason")
            )

        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")

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
            **kwargs: Additional Ollama API parameters

        Returns:
            LLMResponse with generated text
        """
        self.validate_messages(messages)

        # Convert to Ollama format
        api_messages = [msg.to_dict() for msg in messages]

        # Build request
        request_data = {
            "model": self.model,
            "messages": api_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs.get("options", {})
            }
        }

        # Make API call
        try:
            response = self.client.post(
                f"{self.base_url}/api/chat",
                json=request_data
            )
            response.raise_for_status()
            result = response.json()

            # Extract assistant message
            message = result.get("message", {})
            text = message.get("content", "")

            return LLMResponse(
                text=text,
                model=result.get("model", self.model),
                tokens_used=result.get("eval_count"),
                finish_reason=result.get("done_reason")
            )

        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")

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
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama API parameters

        Yields:
            Text chunks as they're generated
        """
        # Use provided system prompt, fall back to default, or None
        system = system_prompt or self.default_system_prompt

        # Build request
        request_data = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                **kwargs.get("options", {})
            }
        }

        if system:
            request_data["system"] = system

        # Stream response
        try:
            with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=request_data
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                yield chunk["response"]
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier string
        """
        return self.model

    def list_models(self) -> List[str]:
        """List available models in Ollama.

        Returns:
            List of model names
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()

            models = result.get("models", [])
            return [model.get("name") for model in models]

        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def is_available(self) -> bool:
        """Check if Ollama is running and accessible.

        Returns:
            True if Ollama is available
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()


# Test function
if __name__ == "__main__":
    print("Testing OllamaProvider...")
    print("=" * 60)

    # Create provider
    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2",
        default_system_prompt="You are a helpful voice assistant."
    )

    # Check if Ollama is available
    if not provider.is_available():
        print("❌ Ollama is not running")
        print("\nStart Ollama with: ollama serve")
        print(f"Ensure model is pulled: ollama pull {provider.model}")
        exit(1)

    print(f"Model: {provider.get_model_name()}")
    print(f"✓ Ollama is running\n")

    # List available models
    print("Available models:")
    try:
        models = provider.list_models()
        for model in models[:5]:
            print(f"  - {model}")
        if len(models) > 5:
            print(f"  ... and {len(models) - 5} more")
    except Exception as e:
        print(f"  Could not list models: {e}")
    print()

    # Test 1: Simple generation
    print("Test 1: Simple generation")
    print("-" * 60)

    prompt = "What is the capital of France? Answer in one sentence."
    print(f"Prompt: {prompt}\n")

    try:
        response = provider.generate(prompt, max_tokens=100)
        print(f"Response: {response.text}")
        print(f"Tokens: {response.tokens_used}")
        print(f"Finish: {response.finish_reason}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Test 2: Conversation
    print("Test 2: Conversation")
    print("-" * 60)

    messages = [
        Message(role="system", content="You are a helpful voice assistant. Be concise."),
        Message(role="user", content="Hi! What's your name?"),
        Message(role="assistant", content="I'm a helpful AI assistant."),
        Message(role="user", content="What can you help me with?")
    ]

    print("Conversation:")
    for msg in messages:
        print(f"  {msg.role}: {msg.content}")
    print()

    try:
        response = provider.chat(messages, max_tokens=150)
        print(f"Response: {response.text}")
        print(f"Tokens: {response.tokens_used}\n")
    except Exception as e:
        print(f"Error: {e}\n")

    # Test 3: Streaming
    print("Test 3: Streaming")
    print("-" * 60)

    prompt = "Count from 1 to 5, one number per line."
    print(f"Prompt: {prompt}\n")
    print("Streaming response:")

    try:
        for chunk in provider.stream(prompt, max_tokens=100):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\nError: {e}\n")

    print("=" * 60)
    print("✓ OllamaProvider tests complete")
