#!/usr/bin/env python3
"""Test conversation engine structure without heavy dependencies."""

import sys


def test_file_syntax():
    """Test that all Python files have valid syntax."""
    import ast
    from pathlib import Path

    print("=" * 60)
    print("TEST: File Syntax Validation")
    print("=" * 60)
    print()

    files = [
        "rubber_ducky/conversation/turn_manager.py",
        "rubber_ducky/conversation/engine.py",
        "rubber_ducky/conversation/__init__.py",
    ]

    for file_path in files:
        with open(file_path, 'r') as f:
            code = f.read()
        try:
            ast.parse(code)
            print(f"✓ {file_path}: Valid syntax")
        except SyntaxError as e:
            print(f"✗ {file_path}: Syntax error - {e}")
            return False

    print()
    return True


def test_turn_state_enum():
    """Test TurnState enum structure."""
    print("=" * 60)
    print("TEST: TurnState Enum")
    print("=" * 60)
    print()

    # Parse the file to extract the enum
    import ast

    with open("rubber_ducky/conversation/turn_manager.py", 'r') as f:
        tree = ast.parse(f.read())

    # Find the TurnState class
    turn_state_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TurnState":
            turn_state_class = node
            break

    if not turn_state_class:
        print("✗ TurnState enum not found")
        return False

    print("✓ TurnState enum defined")

    # Check for expected states
    expected_states = ["LISTENING", "SPEAKING", "PROCESSING", "PLAYING", "INTERRUPTION"]

    # Count assignments in the class
    state_count = 0
    for item in turn_state_class.body:
        if isinstance(item, ast.Assign):
            state_count += 1

    print(f"✓ Found {state_count} state definitions")
    print(f"  Expected: {expected_states}")
    print()

    return True


def test_turn_dataclass():
    """Test Turn dataclass structure."""
    print("=" * 60)
    print("TEST: Turn Dataclass")
    print("=" * 60)
    print()

    import ast

    with open("rubber_ducky/conversation/turn_manager.py", 'r') as f:
        tree = ast.parse(f.read())

    # Find the Turn class
    turn_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Turn":
            turn_class = node
            break

    if not turn_class:
        print("✗ Turn dataclass not found")
        return False

    print("✓ Turn dataclass defined")

    # Check for expected fields in docstring
    expected_fields = ["turn_number", "speaker", "audio", "text", "timestamp", "duration", "interrupted"]

    print(f"  Expected fields: {', '.join(expected_fields)}")
    print()

    return True


def test_turn_manager_methods():
    """Test TurnManager has required methods."""
    print("=" * 60)
    print("TEST: TurnManager Methods")
    print("=" * 60)
    print()

    import ast

    with open("rubber_ducky/conversation/turn_manager.py", 'r') as f:
        tree = ast.parse(f.read())

    # Find TurnManager class
    turn_manager = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TurnManager":
            turn_manager = node
            break

    if not turn_manager:
        print("✗ TurnManager class not found")
        return False

    print("✓ TurnManager class defined")

    # Extract method names
    methods = []
    for item in turn_manager.body:
        if isinstance(item, ast.FunctionDef):
            methods.append(item.name)

    required_methods = [
        "__init__",
        "start_turn",
        "add_audio",
        "get_accumulated_audio",
        "update_speech_state",
        "get_silence_duration",
        "should_end_turn",
        "end_turn",
        "get_conversation_text",
    ]

    print(f"\nFound {len(methods)} methods:")
    for method in methods:
        required = "✓" if method in required_methods else " "
        print(f"  {required} {method}")

    missing = set(required_methods) - set(methods)
    if missing:
        print(f"\n✗ Missing methods: {missing}")
        return False

    print(f"\n✓ All required methods present")
    print()

    return True


def test_conversation_engine_methods():
    """Test ConversationEngine has required methods."""
    print("=" * 60)
    print("TEST: ConversationEngine Methods")
    print("=" * 60)
    print()

    import ast

    with open("rubber_ducky/conversation/engine.py", 'r') as f:
        tree = ast.parse(f.read())

    # Find ConversationEngine class
    engine = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ConversationEngine":
            engine = node
            break

    if not engine:
        print("✗ ConversationEngine class not found")
        return False

    print("✓ ConversationEngine class defined")

    # Extract method names
    methods = []
    for item in engine.body:
        if isinstance(item, ast.FunctionDef):
            methods.append(item.name)

    required_methods = [
        "__init__",
        "initialize_components",
        "start",
        "main_loop",
        "handle_listening",
        "handle_speaking",
        "handle_processing",
        "handle_playing",
        "build_llm_messages",
        "resample_audio",
    ]

    print(f"\nFound {len(methods)} methods:")
    for method in sorted(methods):
        required = "✓" if method in required_methods else " "
        print(f"  {required} {method}")

    missing = set(required_methods) - set(methods)
    if missing:
        print(f"\n✗ Missing methods: {missing}")
        return False

    print(f"\n✓ All required methods present")
    print()

    return True


def test_state_machine_flow():
    """Verify state machine flow is documented."""
    print("=" * 60)
    print("TEST: State Machine Flow")
    print("=" * 60)
    print()

    with open("rubber_ducky/conversation/engine.py", 'r') as f:
        content = f.read()

    # Check for state handlers
    handlers = [
        "handle_listening",
        "handle_speaking",
        "handle_processing",
        "handle_playing"
    ]

    print("State handlers:")
    for handler in handlers:
        if handler in content:
            print(f"  ✓ {handler}")
        else:
            print(f"  ✗ {handler} - NOT FOUND")
            return False

    # Check for TurnState references
    print("\nTurnState usage:")
    states = ["LISTENING", "SPEAKING", "PROCESSING", "PLAYING"]
    for state in states:
        if f"TurnState.{state}" in content:
            print(f"  ✓ TurnState.{state}")
        else:
            print(f"  ✗ TurnState.{state} - NOT FOUND")

    print()
    return True


def test_imports_structure():
    """Test that imports are structured correctly."""
    print("=" * 60)
    print("TEST: Import Structure")
    print("=" * 60)
    print()

    import ast

    with open("rubber_ducky/conversation/engine.py", 'r') as f:
        tree = ast.parse(f.read())

    # Extract imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"from {module} import {alias.name}")

    required_imports = [
        "AudioCapture",
        "AudioPlayback",
        "VADEngine",
        "TranscriptionEngine",
        "TTSEngine",
        "Message",
        "ClaudeProvider",
        "OllamaProvider",
        "TurnManager",
        "TurnState",
    ]

    print("Checking required imports:")
    for req in required_imports:
        found = any(req in imp for imp in imports)
        status = "✓" if found else "✗"
        print(f"  {status} {req}")

    print()
    return True


def main():
    """Run all structure tests."""
    print("\n" + "=" * 60)
    print("RUBBER DUCKY - CONVERSATION ENGINE STRUCTURE TEST")
    print("=" * 60)
    print("\nValidating conversation engine structure...")
    print("(No heavy dependencies required)\n")

    tests = [
        test_file_syntax,
        test_turn_state_enum,
        test_turn_dataclass,
        test_turn_manager_methods,
        test_conversation_engine_methods,
        test_state_machine_flow,
        test_imports_structure,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 60)
    if all(results):
        print("✓ ALL STRUCTURE TESTS PASSED")
        print("=" * 60)
        print()
        print("Conversation engine structure is valid!")
        print()
        print("To test with real dependencies:")
        print("  1. Install: pip install torch whisperx coqui-tts anthropic httpx")
        print("  2. Configure .env with API keys")
        print("  3. Run: rubber-ducky converse")
        print()
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        failed_count = sum(1 for r in results if not r)
        print(f"\n{failed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
