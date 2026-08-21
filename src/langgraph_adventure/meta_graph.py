"""2-node LangGraph meta-graph: theme_intake → scene_generator.

Phase 1 scaffold — `theme_intake` returns a hardcoded opening scene;
`scene_generator` is a no-op. Later tasks will swap in an LLM-backed
generator.
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
    Scenes accumulates rather than overwrites.
    """

    theme: str
    world_seed: str
    history: Annotated[list[Scene], operator.add]


def theme_intake(state: MetaState) -> dict:
    """Return a hardcoded opening scene. Phase 1 — no LLM call."""
    return {
        "history": [
            Scene(
                scene_id="opening",
                description="You stand before a heavy door. It creaks slightly. The air smells of rain and old wood.",
                npcs=[],
                actions=[
                    Action(id="A", label="Open the door", next_state="continue"),
                    Action(id="B", label="Turn back", next_state="end"),
                ],
            )
        ]
    }


def scene_generator(state: MetaState) -> dict:
    """Phase 1 no-op. Later tasks will replace this with an LLM-driven generator."""
    return {}


def build_meta_graph() -> CompiledStateGraph:
    """Build and compile the 2-node meta-graph."""
    builder = StateGraph(MetaState)
    builder.add_node("theme_intake", theme_intake)
    builder.add_node("scene_generator", scene_generator)
    builder.add_edge(START, "theme_intake")
    builder.add_edge("theme_intake", "scene_generator")
    builder.add_edge("scene_generator", END)
    return builder.compile()


# Module-level singleton so LangGraph Studio (`langgraph.json`) can import it.
graph = build_meta_graph()
