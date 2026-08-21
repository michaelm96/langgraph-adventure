"""FastAPI server for langgraph-adventure web UI.

Local-only browser UI wrapping the existing game_graph. Each browser
session = one thread_id (UUID4 in URL). See spec §3.
"""
from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from langgraph_adventure.game_graph import build_game_graph
from langgraph_adventure.meta_graph import graph as meta_graph

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

DB_PATH = Path.home() / ".langgraph_adventure" / "game.db"

app = FastAPI(title="langgraph-adventure")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _build_checkpointer() -> SqliteSaver:
    """Return a SQLite-backed checkpointer (matches cli/play._get_checkpointer).

    ponytail: direct sqlite3 + SqliteSaver instead of the persistence.get_checkpointer
    helper. The helper still calls the renamed `with_msgpack_allowlist` (langgraph 1.2
    has it under `with_allowlist`); reusing the CLI's known-good pattern avoids touching
    persistence.py — the plan forbids edits to existing modules.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return SqliteSaver(sqlite3.connect(str(DB_PATH), check_same_thread=False))


# ponytail: module-level compiled graph — single instance shared across requests.
# Per C1 ruling: game_graph.graph is compiled but lacks a checkpointer, so state
# wouldn't persist between requests. Recompile here with the SQLite checkpointer.
graph = build_game_graph().compile(checkpointer=_build_checkpointer())


def _opening_scene(theme: str):
    """Get the opening Scene from the meta-graph (matches cli/play.play_session).

    The spec says `present_scene` would invoke the meta-graph internally, but the
    current `present_scene` is a Phase 4 stub. We generate the scene in the web
    layer (like the CLI does) until Phase 7 wires real scene generation into the
    game graph itself.
    """
    result = meta_graph.invoke(
        {
            "theme": theme,
            "world_seed": str(uuid.uuid4()),
            "current_request": "continue",
            "history": [],
            "npc_dialogues": {},
        }
    )
    return result["history"][-1]


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/play/new?theme=noir-detective", status_code=307)


@app.get("/play/new")
def play_new(theme: str = "noir-detective") -> RedirectResponse:
    """Create a new thread_id and redirect to /play/{thread_id}."""
    thread_id = str(uuid.uuid4())
    return RedirectResponse(url=f"/play/{thread_id}?theme={theme}", status_code=307)


@app.get("/play/{thread_id}")
def play(thread_id: str, request: Request, theme: str = "noir-detective"):
    """Render the play page with the latest scene + actions.

    On first invocation (no checkpoint for thread_id), generates the opening
    scene from meta-graph and seeds the game graph with it.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)

    # C2 first-visit gate: state.next is None before any invocation.
    if state.next is None or not state.values:
        scene = _opening_scene(theme)
        initial = {
            "messages": [],
            "current_scene": scene,
            "chosen_action": None,
            "npc_dialogues": {},
            "theme": theme,
        }
        graph.invoke(initial, config=config)
        state = graph.get_state(config)

    scene = state.values.get("current_scene")
    actions = scene.actions if scene and scene.actions else []

    return templates.TemplateResponse(
        "play.html.j2",
        {"request": request, "thread_id": thread_id, "scene": scene, "actions": actions},
    )


@app.post("/play/{thread_id}/action")
def play_action(thread_id: str, action: str = "", request: Request = None):
    """Resume the graph's interrupt with the chosen action. Returns HTMX partial."""
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)

    if not state.next:
        return templates.TemplateResponse(
            "_narration.html.j2",
            {"request": request, "thread_id": thread_id, "scene": None, "actions": []},
        )

    graph.invoke(Command(resume=action), config=config)
    state = graph.get_state(config)
    scene = state.values.get("current_scene")
    actions = scene.actions if scene and scene.actions else []

    return templates.TemplateResponse(
        "_narration.html.j2",
        {"request": request, "thread_id": thread_id, "scene": scene, "actions": actions},
    )


@app.post("/play/{thread_id}/undo")
def play_undo(thread_id: str, request: Request = None):
    """Rewind to the previous checkpoint's state values."""
    config = {"configurable": {"thread_id": thread_id}}
    history = list(graph.get_state_history(config))

    # history[0] is most recent. history[1] is one step back.
    if len(history) < 2:
        # Nothing to undo.
        state = graph.get_state(config)
        scene = state.values.get("current_scene")
        actions = scene.actions if scene and scene.actions else []
        return templates.TemplateResponse(
            "_narration.html.j2",
            {"request": request, "thread_id": thread_id, "scene": scene, "actions": actions},
        )

    prior = history[1]
    graph.update_state(config, values=prior.values)

    state = graph.get_state(config)
    scene = state.values.get("current_scene")
    actions = scene.actions if scene and scene.actions else []
    return templates.TemplateResponse(
        "_narration.html.j2",
        {"request": request, "thread_id": thread_id, "scene": scene, "actions": actions},
    )


@app.post("/play/{thread_id}/fork")
def play_fork(thread_id: str) -> RedirectResponse:
    """Create a new thread seeded from the current state's values."""
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)
    new_thread_id = str(uuid.uuid4())
    new_config = {"configurable": {"thread_id": new_thread_id}}
    graph.update_state(new_config, values=state.values)
    return RedirectResponse(url=f"/play/{new_thread_id}", status_code=307)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("LG_ADV_WEB_PORT", "8000"))
    uvicorn.run("langgraph_adventure.web.server:app", host="127.0.0.1", port=port, reload=False)
