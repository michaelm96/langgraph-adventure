"""Persistence helpers (checkpointers).

Phase 4: just SqliteSaver. Phase 9 may add update_state / time-travel.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import InMemorySaver


DB_PATH = Path.home() / ".langgraph_adventure" / "game.db"


_MSGPACK_ALLOWLIST = [("langgraph_adventure", "state")]


def get_sqlite_saver() -> SqliteSaver:
    """Return a SqliteSaver rooted at ~/.langgraph_adventure/game.db.

    Creates parent directory if missing. Uses check_same_thread=False per
    SqliteSaver's documented threading model. Adds ``langgraph_adventure.state``
    to msgpack allowlist so Scene/Action Pydantic models round-trip cleanly
    (without this, langgraph warns on every checkpoint save).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    saver = SqliteSaver(sqlite3.connect(str(DB_PATH), check_same_thread=False))
    return saver.with_msgpack_allowlist(_MSGPACK_ALLOWLIST)


def get_checkpointer(memory: bool = False) -> Any:
    """Return a checkpointer.

    Args:
        memory: if True, return InMemorySaver (for tests); otherwise return
                SqliteSaver (for persistent play sessions).

    Thread_id isolation: each ``config["configurable"]["thread_id"]`` keeps a
    separate checkpoint history. To "undo", rewind via ``update_state`` with
    values from a previous checkpoint.
    """
    if memory:
        return InMemorySaver().with_msgpack_allowlist(_MSGPACK_ALLOWLIST)
    return get_sqlite_saver()
