"""2-node LangGraph meta-graph with conditional_edges.

Phase 2 — `theme_intake` preserves an injected `current_request` (default
"continue"); `scene_generator` dispatches to one of three hardcoded scenes
based on `current_request`. The conditional edge demonstrates LangGraph's
`add_conditional_edges` pattern, even though all three branches currently
land on the same node (differentiation happens inside `scene_generator`).
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from langgraph_adventure.state import Action, Scene


class MetaState(TypedDict):
    """Graph state for the meta-graph.

    `history` uses an append reducer so each node that returns a list of
    Scenes accumulates rather than overwrites. `current_request` drives
    the conditional routing after `theme_intake`.
    """

    theme: str
    world_seed: str
    current_request: str  # "continue" | "branch_left" | "branch_right"
    history: Annotated[list[Scene], operator.add]


def _opening_scene() -> Scene:
    return Scene(
        scene_id="opening",
        description="You stand before a heavy door. It creaks slightly. The air smells of rain and old wood.",
        npcs=[],
        actions=[
            Action(id="A", label="Open the door", next_state="branch_left"),
            Action(id="B", label="Turn back", next_state="branch_right"),
        ],
    )


def _forest_scene() -> Scene:
    return Scene(
        scene_id="forest",
        description="You step through the door into a dense, misty forest. Shafts of pale light filter through the canopy. Something rustles behind a fern.",
        npcs=[],
        actions=[
            Action(id="A", label="Investigate the sound", next_state="branch_left"),
            Action(id="B", label="Head back", next_state="branch_right"),
        ],
    )


def _cave_scene() -> Scene:
    return Scene(
        scene_id="cave",
        description="You turn away from the door and find yourself on a rocky path that descends into a dark cave. Cool air breathes out from within.",
        npcs=[],
        actions=[
            Action(id="A", label="Enter the cave", next_state="branch_left"),
            Action(id="B", label="Stay outside", next_state="branch_right"),
        ],
    )


_SCENES = {
    "continue": _opening_scene,
    "branch_left": _forest_scene,
    "branch_right": _cave_scene,
}


def theme_intake(state: MetaState) -> dict:
    """Preserve injected `current_request` (default "continue"); `scene_generator` populates history."""
    request = state.get("current_request") or "continue"
    return {"current_request": request}


def route_request(state: MetaState) -> str:
    """Return the routing key used by the conditional edge."""
    return state.get("current_request", "continue")


def scene_generator(state: MetaState) -> dict:
    """Dispatch to a scene factory based on `current_request`."""
    request = state.get("current_request", "continue")
    factory = _SCENES.get(request, _opening_scene)
    return {"history": [factory()]}


def build_meta_graph() -> CompiledStateGraph:
    """Build and compile the meta-graph with a conditional edge."""
    builder = StateGraph(MetaState)
    builder.add_node("theme_intake", theme_intake)
    builder.add_node("scene_generator", scene_generator)
    builder.add_edge(START, "theme_intake")
    builder.add_conditional_edges(
        "theme_intake",
        route_request,
        {
            "continue": "scene_generator",
            "branch_left": "scene_generator",
            "branch_right": "scene_generator",
        },
    )
    builder.add_edge("scene_generator", END)
    return builder.compile()


# Module-level singleton so LangGraph Studio (`langgraph.json`) can import it.
graph = build_meta_graph()