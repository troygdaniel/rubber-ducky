"""Conversation engine and turn management."""

# Lazy imports to avoid dependency errors
__all__ = [
    "ConversationEngine",
    "TurnManager",
    "TurnState",
    "Turn",
]

def __getattr__(name):
    """Lazy import conversation components."""
    if name == "ConversationEngine":
        from rubber_ducky.conversation.engine import ConversationEngine
        return ConversationEngine
    elif name == "TurnManager":
        from rubber_ducky.conversation.turn_manager import TurnManager
        return TurnManager
    elif name == "TurnState":
        from rubber_ducky.conversation.turn_manager import TurnState
        return TurnState
    elif name == "Turn":
        from rubber_ducky.conversation.turn_manager import Turn
        return Turn
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
