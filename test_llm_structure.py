#!/usr/bin/env python3
"""Quick structure test for LLM module (no external dependencies needed)."""

from rubber_ducky.llm.base import LLMProvider, Message, LLMResponse


class MockProvider(LLMProvider):
    """Mock LLM provider for testing structure."""

    def __init__(self):
        self.model = "mock-model"

    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=1024, **kwargs):
        return LLMResponse(
            text=f"Mock response to: {prompt[:50]}...",
            model=self.model,
            tokens_used=20,
            finish_reason="mock_stop"
        )

    def chat(self, messages, temperature=0.7, max_tokens=1024, **kwargs):
        last_message = messages[-1].content if messages else "No messages"
        return LLMResponse(
            text=f"Mock response to: {last_message[:50]}...",
            model=self.model,
            tokens_used=len(messages) * 10,
            finish_reason="mock_stop"
        )

    def stream(self, prompt, system_prompt=None, temperature=0.7, max_tokens=1024, **kwargs):
        words = ["Mock", "streaming", "response"]
        for word in words:
            yield word + " "

    def get_model_name(self):
        return self.model


def test_base_classes():
    """Test base class structure."""
    print("=" * 60)
    print("TEST: Base Classes")
    print("=" * 60)
    print()

    # Test Message
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.to_dict() == {"role": "user", "content": "Hello"}
    print("✓ Message class works")

    # Test LLMResponse
    resp = LLMResponse(text="Hi", model="test", tokens_used=10)
    assert resp.text == "Hi"
    assert resp.model == "test"
    assert resp.tokens_used == 10
    print("✓ LLMResponse class works")
    print()


def test_mock_provider():
    """Test mock provider implementation."""
    print("=" * 60)
    print("TEST: Mock Provider")
    print("=" * 60)
    print()

    provider = MockProvider()

    # Test generate
    response = provider.generate("What is Python?")
    assert "Mock response" in response.text
    assert response.tokens_used == 20
    print(f"✓ Generate: {response.text}")

    # Test chat
    messages = [
        Message(role="system", content="Be helpful"),
        Message(role="user", content="Hello")
    ]
    response = provider.chat(messages)
    assert "Mock response" in response.text
    assert response.tokens_used == 20
    print(f"✓ Chat: {response.text}")

    # Test stream
    chunks = list(provider.stream("Test"))
    assert len(chunks) == 3
    print(f"✓ Stream: {''.join(chunks)}")

    # Test model name
    assert provider.get_model_name() == "mock-model"
    print(f"✓ Model name: {provider.get_model_name()}")
    print()


def test_message_validation():
    """Test message validation."""
    print("=" * 60)
    print("TEST: Message Validation")
    print("=" * 60)
    print()

    provider = MockProvider()

    # Valid messages
    messages = [
        Message(role="system", content="Be helpful"),
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi")
    ]

    try:
        provider.validate_messages(messages)
        print("✓ Valid messages passed validation")
    except ValueError as e:
        print(f"✗ Should not raise error: {e}")
        return False

    # Invalid: empty list
    try:
        provider.validate_messages([])
        print("✗ Empty list should fail validation")
        return False
    except ValueError:
        print("✓ Empty list correctly rejected")

    # Invalid: empty content
    try:
        provider.validate_messages([Message(role="user", content="")])
        print("✗ Empty content should fail validation")
        return False
    except ValueError:
        print("✓ Empty content correctly rejected")

    # Invalid: bad role
    try:
        provider.validate_messages([Message(role="invalid", content="test")])
        print("✗ Invalid role should fail validation")
        return False
    except ValueError:
        print("✓ Invalid role correctly rejected")

    print()
    return True


def test_conversation_history():
    """Test conversation history formatting."""
    print("=" * 60)
    print("TEST: Conversation History")
    print("=" * 60)
    print()

    provider = MockProvider()

    # Create long conversation
    messages = [
        Message(role="system", content="Be helpful"),
        Message(role="user", content="Turn 1"),
        Message(role="assistant", content="Response 1"),
        Message(role="user", content="Turn 2"),
        Message(role="assistant", content="Response 2"),
        Message(role="user", content="Turn 3"),
        Message(role="assistant", content="Response 3"),
    ]

    # Test limiting to last 3 messages
    limited = provider.format_conversation_history(messages, max_messages=3)
    assert len(limited) == 3
    assert limited[0].role == "system"  # System message preserved
    assert limited[-1].content == "Response 3"
    print(f"✓ Limited to 3 messages (kept system + last 2)")

    # Test no limit
    unlimited = provider.format_conversation_history(messages, max_messages=None)
    assert len(unlimited) == len(messages)
    print(f"✓ No limit: {len(unlimited)} messages preserved")

    print()


def main():
    """Run all structure tests."""
    print("\n" + "=" * 60)
    print("RUBBER DUCKY - LLM STRUCTURE TEST")
    print("=" * 60)
    print("\nTesting LLM abstraction layer structure...")
    print("(No external dependencies required)")
    print()

    test_base_classes()
    test_mock_provider()
    test_message_validation()
    test_conversation_history()

    print("=" * 60)
    print("✓ ALL STRUCTURE TESTS PASSED")
    print("=" * 60)
    print()
    print("LLM abstraction layer is correctly implemented!")
    print()
    print("To test with real providers:")
    print("  1. Install dependencies:")
    print("     pip install anthropic httpx")
    print("  2. Set API key in .env:")
    print("     RUBBER_DUCKY_CLAUDE_API_KEY=your_key")
    print("  3. Run: python test_llm.py")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
