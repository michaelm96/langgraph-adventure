"""Persistence helpers (checkpointers).

Phase 4: just SqliteSaver. Phase 9 may add update_state / time-travel.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver


DB_PATH = Path.home() / ".langgraph_adventure" / "game.db"


def get_sqlite_saver() -> SqliteSaver:
    """Return a SqliteSaver rooted at ~/.langgraph_adventure/game.db.

    Creates parent directory if missing. Uses check_same_thread=False per
    SqliteSaver's documented threading model.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver(sqlite3.connect(str(DB_PATH), check_same_thread=False))
