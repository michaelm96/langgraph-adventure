"""Game-loop graph: present_scene + interrupt_for_choice.

Phase 4 wires up only 2 nodes. `present_scene` prints the scene narration
and action menu; `interrupt_for_choice` pauses the graph via `interrupt()`
so the player can pick an action. Later phases add streaming, the
scene-generator branch, and the action-handler node.
"""

from __future__ import annotations

from typing import Annotated, Any

from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import MessagesState, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt

from langgraph_adventure.state import Action, Scene


class GameState(MessagesState):
    """State for the game-graph.

    Inherits `messages` from MessagesState (uses add_messages reducer).
    Adds game-specific fields.
    """
    current_scene: Scene | None
    chosen_action: Action | None
    npc_dialogues: dict[str, str]


def present_scene(state: GameState) -> dict:
    """Stream the scene description + action menu to the player.

    Phase 4: just print() (simple, deterministic). Phase 7 swaps this for astream_events
    to stream narration token-by-token.
    """
    scene = state.get("current_scene")
    if scene is None:
        return {}
    print(f"\n--- {scene.scene_id} ---")
    print(scene.description)
    if scene.npcs:
        print(f"  npcs: {scene.npcs}")
    print("  what do you do?")
    for a in scene.actions:
        print(f"    [{a.id}] {a.label}")
    return {}


def interrupt_for_choice(state: GameState) -> dict:
    """Pause the graph and await a player choice.

    `interrupt({...})` raises GraphInterrupt; the graph pauses here. To resume,
    call `graph.invoke(Command(resume=<choice>), config)`. The payload should
    include everything the caller (CLI/REPL) needs to render the menu.
    """
    scene = state.get("current_scene")
    if scene is None:
        return {}
    payload = {
        "scene_id": scene.scene_id,
        "actions": [{"id": a.id, "label": a.label, "next_state": a.next_state} for a in scene.actions],
        "description": scene.description,
    }
    user_choice = interrupt(payload)
    return {"chosen_action": Action(id=user_choice, label=user_choice, next_state="continue")}


def build_game_graph() -> StateGraph:
    """Build the game-graph with 2 nodes (other nodes added in later phases).

    Returns the uncompiled builder; callers compile with `.compile(checkpointer=...)`.
    Compile flow: START → present_scene → interrupt_for_choice → END.

    Phase 4 doesn't compile here — the demo in 4.3 uses InMemorySaver so the
    graph can pause + resume in a single process. The REPL in 4.2 uses
    SqliteSaver for cross-process persistence.
    """
    builder = StateGraph(GameState)
    builder.add_node("present_scene", present_scene)
    builder.add_node("interrupt_for_choice", interrupt_for_choice)
    builder.add_edge(START, "present_scene")
    builder.add_edge("present_scene", "interrupt_for_choice")
    builder.add_edge("interrupt_for_choice", END)
    return builder


# Module-level singleton for Studio (added to langgraph.json in task 4.2)
graph = build_game_graph().compile()
