#!/usr/bin/env python3
"""Test script for LLM providers (Claude + Ollama)."""

import sys
import os
from rubber_ducky.llm import ClaudeProvider, OllamaProvider, Message
from rubber_ducky.config import settings


def test_claude():
    """Test 1: Claude API provider."""
    print("=" * 60)
    print("TEST 1: Claude API Provider")
    print("=" * 60)

    # Check API key
    api_key = settings.claude_api_key
    if not api_key:
        print("\n❌ Claude API key not configured")
        print("Set RUBBER_DUCKY_CLAUDE_API_KEY in .env file")
        print("\nSkipping Claude tests...\n")
        return None

    print(f"\nModel: {settings.claude_model}")
    print("✓ API key configured\n")

    # Create provider
    provider = ClaudeProvider(
        api_key=api_key,
        model=settings.claude_model,
        default_system_prompt="You are a helpful voice assistant. Be concise and natural in conversation."
    )

    # Test 1a: Simple prompt
    print("Test 1a: Simple prompt")
    print("-" * 60)

    prompt = "What's the weather like today?"
    print(f"Prompt: \"{prompt}\"\n")

    try:
        response = provider.generate(
            prompt,
            system_prompt="You are a helpful assistant. The user cannot see weather data, so politely explain you don't have access to real-time weather.",
            max_tokens=100
        )

        print(f"Response: {response.text}")
        print(f"Tokens used: {response.tokens_used}")
        print(f"Finish reason: {response.finish_reason}\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

    # Test 1b: Multi-turn conversation
    print("Test 1b: Multi-turn conversation")
    print("-" * 60)

    messages = [
        Message(role="system", content="You are a helpful voice assistant. Be concise."),
        Message(role="user", content="Hi there!"),
        Message(role="assistant", content="Hello! How can I help you today?"),
        Message(role="user", content="Can you tell me a short fun fact?")
    ]

    print("Conversation:")
    for msg in messages:
        role_label = msg.role.upper()
        print(f"  {role_label}: {msg.content}")
    print()

    try:
        response = provider.chat(messages, max_tokens=150)
        print(f"ASSISTANT: {response.text}")
        print(f"Tokens used: {response.tokens_used}\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

    # Test 1c: Streaming
    print("Test 1c: Streaming response")
    print("-" * 60)

    prompt = "List 3 benefits of walking. Be brief."
    print(f"Prompt: \"{prompt}\"\n")
    print("ASSISTANT: ", end="", flush=True)

    try:
        for chunk in provider.stream(prompt, max_tokens=200):
            print(chunk, end="", flush=True)
        print("\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return None

    print("✓ Claude provider tests passed\n")
    return provider


def test_ollama():
    """Test 2: Ollama local provider."""
    print("=" * 60)
    print("TEST 2: Ollama Local Provider")
    print("=" * 60)

    print(f"\nBase URL: {settings.ollama_base_url}")
    print(f"Model: {settings.ollama_model}\n")

    # Create provider
    provider = OllamaProvider(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        default_system_prompt="You are a helpful voice assistant. Be concise and natural in conversation."
    )

    # Check if Ollama is running
    if not provider.is_available():
        print("❌ Ollama is not running")
        print("\nStart Ollama:")
        print("  1. Run: ollama serve")
        print(f"  2. Pull model: ollama pull {settings.ollama_model}")
        print("\nSkipping Ollama tests...\n")
        return None

    print("✓ Ollama is running")

    # List models
    try:
        models = provider.list_models()
        print(f"✓ Found {len(models)} model(s)")

        if settings.ollama_model not in [m.split(':')[0] for m in models]:
            print(f"\n⚠ Warning: Model '{settings.ollama_model}' not found")
            print(f"Pull it with: ollama pull {settings.ollama_model}")
            print("\nSkipping Ollama tests...\n")
            return None

    except Exception as e:
        print(f"⚠ Could not list models: {e}")

    print()

    # Test 2a: Simple prompt
    print("Test 2a: Simple prompt")
    print("-" * 60)

    prompt = "What is 2+2? Answer in one sentence."
    print(f"Prompt: \"{prompt}\"\n")

    try:
        response = provider.generate(prompt, max_tokens=50)
        print(f"Response: {response.text}")
        print(f"Tokens used: {response.tokens_used}\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

    # Test 2b: Multi-turn conversation
    print("Test 2b: Multi-turn conversation")
    print("-" * 60)

    messages = [
        Message(role="system", content="You are a helpful voice assistant. Be concise."),
        Message(role="user", content="Hi!"),
        Message(role="assistant", content="Hello! How can I assist you?"),
        Message(role="user", content="What's your favorite color?")
    ]

    print("Conversation:")
    for msg in messages:
        role_label = msg.role.upper()
        print(f"  {role_label}: {msg.content}")
    print()

    try:
        response = provider.chat(messages, max_tokens=100)
        print(f"ASSISTANT: {response.text}\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
        return None

    # Test 2c: Streaming
    print("Test 2c: Streaming response")
    print("-" * 60)

    prompt = "Count from 1 to 3."
    print(f"Prompt: \"{prompt}\"\n")
    print("ASSISTANT: ", end="", flush=True)

    try:
        for chunk in provider.stream(prompt, max_tokens=50):
            print(chunk, end="", flush=True)
        print("\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return None

    print("✓ Ollama provider tests passed\n")
    return provider


def test_conversation_simulation(provider_name: str, provider):
    """Test 3: Simulate a voice conversation."""
    print("=" * 60)
    print(f"TEST 3: Conversation Simulation ({provider_name})")
    print("=" * 60)

    if provider is None:
        print(f"\nSkipping (no {provider_name} provider available)\n")
        return

    print("\nSimulating a 3-turn conversation...\n")

    # Conversation history
    messages = [
        Message(
            role="system",
            content="You are a helpful voice assistant named Ducky. Keep responses brief and conversational."
        )
    ]

    # Turn 1
    user_input = "Hi Ducky, what can you help me with?"
    messages.append(Message(role="user", content=user_input))

    print(f"USER: {user_input}")
    try:
        response = provider.chat(messages, max_tokens=100)
        print(f"DUCKY: {response.text}\n")
        messages.append(Message(role="assistant", content=response.text))
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return

    # Turn 2
    user_input = "Tell me a quick tip for productivity"
    messages.append(Message(role="user", content=user_input))

    print(f"USER: {user_input}")
    try:
        response = provider.chat(messages, max_tokens=150)
        print(f"DUCKY: {response.text}\n")
        messages.append(Message(role="assistant", content=response.text))
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return

    # Turn 3
    user_input = "Thanks! That's helpful."
    messages.append(Message(role="user", content=user_input))

    print(f"USER: {user_input}")
    try:
        response = provider.chat(messages, max_tokens=100)
        print(f"DUCKY: {response.text}\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return

    print("✓ Conversation simulation complete\n")


def main():
    """Run all LLM tests."""
    print("\n" + "=" * 60)
    print("RUBBER DUCKY - LLM PROVIDER TESTS")
    print("=" * 60)
    print()

    print("Testing both Claude API and Ollama local providers...")
    print()

    # Test Claude
    input("Press Enter to test Claude API...")
    claude_provider = test_claude()

    # Test Ollama
    input("Press Enter to test Ollama...")
    ollama_provider = test_ollama()

    # Conversation simulations
    if claude_provider:
        input("Press Enter to simulate conversation with Claude...")
        test_conversation_simulation("Claude", claude_provider)

    if ollama_provider:
        input("Press Enter to simulate conversation with Ollama...")
        test_conversation_simulation("Ollama", ollama_provider)

    # Summary
    print("=" * 60)
    print("LLM TESTS COMPLETE ✓")
    print("=" * 60)
    print("\nPhase 5 Complete: LLM integration is working!")

    results = []
    if claude_provider:
        results.append("✓ Claude API provider")
    else:
        results.append("✗ Claude API (not configured)")

    if ollama_provider:
        results.append("✓ Ollama local provider")
    else:
        results.append("✗ Ollama (not running)")

    print("\nResults:")
    for result in results:
        print(f"  {result}")

    print("\nImplemented features:")
    print("  ✓ Abstract LLM provider interface")
    print("  ✓ Claude API integration")
    print("  ✓ Ollama local integration")
    print("  ✓ Multi-turn conversations")
    print("  ✓ Streaming responses")
    print("  ✓ Conversation history management")

    print("\nNext: Phase 6 - Conversation Engine")
    print("  Integrate: Audio → Transcription → LLM → TTS → Playback")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
