"""Interactive REPL for the adventure game.

Bridges the meta-graph (which generates scenes) and the game-graph (which
runs the game loop with `interrupt()` pausing for player choice).

langgraph 1.2.x interrupt pattern: at the root-graph level, `GraphInterrupt`
is suppressed — `g.invoke()` returns normally with `__interrupt__` populated.
We read the actions off the interrupt payload, prompt the user, then resume
with `Command(resume=choice)`.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import typer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from langgraph_adventure.game_graph import build_game_graph
from langgraph_adventure.meta_graph import build_meta_graph

app = typer.Typer()

DB_PATH = Path.home() / ".langgraph_adventure" / "game.db"


def _get_checkpointer() -> SqliteSaver:
    """Return a SQLite-backed checkpointer, creating the parent dir if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # ponytail: direct sqlite3 + SqliteSaver — `from_conn_string` is a contextmanager
    # and returns an iterator, not a saver, so it can't go straight into `compile()`.
    return SqliteSaver(sqlite3.connect(str(DB_PATH), check_same_thread=False))


def play_session(theme: str) -> None:
    """Run one REPL session: meta-graph opening → game-graph loop."""
    print(f"=== {theme} ===\n")

    # Step 1: opening scene from meta-graph
    meta = build_meta_graph()
    meta_result = meta.invoke({
        "theme": theme,
        "world_seed": str(uuid.uuid4()),
        "current_request": "continue",
        "history": [],
        "npc_dialogues": {},
    })
    scene = meta_result["history"][-1]
    print(f"Opening scene: {scene.scene_id}")

    # Step 2: game-graph REPL
    game = build_game_graph().compile(checkpointer=_get_checkpointer())
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = {
        "messages": [],
        "current_scene": scene,
        "chosen_action": None,
        "npc_dialogues": {},
    }

    step = 0
    while step < 50:  # ponytail: safety cap so a buggy graph can't loop forever
        step += 1
        result = game.invoke(state, config)

        if "__interrupt__" in result:
            # Graph paused for player choice; render menu and resume
            actions = result["__interrupt__"][0].value["actions"]
            chosen_id = result["__interrupt__"][0].value.get("scene_id", "?")
            print(f"\n--- {chosen_id} ---")
            print("What do you do?")
            for a in actions:
                print(f"  [{a['id']}] {a['label']}")
            choice = input("> ").strip()
            state = Command(resume=choice)
            continue

        # No interrupt — game finished
        action = result.get("chosen_action")
        if action and action.next_state == "end":
            print("\n[game over]")
            return
        print(f"\n[step {step}: no interrupt, no end — state keys: {list(result.keys())}]")
        return  # safety exit


@app.command()
def play(theme: str = typer.Option("noir detective", "--theme", "-t", help="Adventure theme")):
    """Start an interactive adventure session."""
    play_session(theme)


if __name__ == "__main__":
    app()
