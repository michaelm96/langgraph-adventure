"""Store-based long-term memory helpers.

Tutorial uses InMemoryStore (no cross-process persistence). Upgrade path:
swap InMemoryStore → SqliteStore for cross-session persistence without
changing the helper signatures below.
"""
from __future__ import annotations
from typing import Any
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore


_store_instance: InMemoryStore | None = None


def get_store() -> BaseStore:
    """Return a singleton InMemoryStore.

    First call creates the store; subsequent calls return the same instance.
    For per-test isolation, tests can call `reset_store()` to clear.
    """
    global _store_instance
    if _store_instance is None:
        _store_instance = InMemoryStore()
    return _store_instance


def reset_store() -> None:
    """Clear the singleton store (for test isolation)."""
    global _store_instance
    _store_instance = None


def npc_recall(store: BaseStore, npc_name: str, key: str) -> Any:
    """Read a single memory value from an NPC's namespace.

    Namespaces follow LangGraph's tuple pattern: ("npc_memories", npc_name).
    Returns None if the key doesn't exist (vs raising).
    """
    result = store.get(("npc_memories", npc_name), key)
    if result is None:
        return None
    return result.value


def npc_remember(store: BaseStore, npc_name: str, key: str, value: Any) -> None:
    """Write a memory value into an NPC's namespace.

    Namespaces: ("npc_memories", npc_name).
    Overwrites any existing value at that key.
    """
    store.put(("npc_memories", npc_name), key, value)
