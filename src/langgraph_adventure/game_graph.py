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
from langgraph.types import interrupt, Command

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
    # Look up the real next_state from the scene's action list.
    # Free-text input (e.g. from "custom") won't match; fall back to a
    # synthetic Action with next_state="continue" — phase 5.2 will fix that.
    matched = next((a for a in scene.actions if a.id == user_choice), None)
    chosen = matched if matched is not None else Action(id=user_choice, label=user_choice, next_state="continue")
    return {"chosen_action": chosen}


def route_choice(state: GameState) -> Command:
    """Explicit Command routing based on chosen_action.next_state.

    - next_state == "end": terminate the game
    - otherwise: continue to react_npcs
    """
    action = state.get("chosen_action")
    if action is None or action.next_state == "end":
        return Command(goto=END, update={})
    return Command(goto="react_npcs", update={"chosen_action": action})


def react_npcs(state: GameState) -> dict:
    """Run NPC reactions (Phase 6 wires Send fanout; Phase 5 just stub)."""
    return {}


def next_scene(state: GameState) -> dict:
    """Generate the next scene (Phase 7 streams narration; Phase 5 just stub)."""
    return {}


def build_game_graph() -> StateGraph:
    """Build the game-graph with 5 nodes.

    Returns the uncompiled builder; callers compile with `.compile(checkpointer=...)`.
    Compile flow: START → present_scene → interrupt_for_choice → route_choice
                   → react_npcs → next_scene → END.

    `route_choice` uses Command(goto=...) which overrides the advisory edge from
    it to `react_npcs`; when next_state == "end", goto=END terminates early.
    """
    builder = StateGraph(GameState)
    builder.add_node("present_scene", present_scene)
    builder.add_node("interrupt_for_choice", interrupt_for_choice)
    builder.add_node("route_choice", route_choice)
    builder.add_node("react_npcs", react_npcs)
    builder.add_node("next_scene", next_scene)
    builder.add_edge(START, "present_scene")
    builder.add_edge("present_scene", "interrupt_for_choice")
    builder.add_edge("interrupt_for_choice", "route_choice")
    builder.add_edge("route_choice", "react_npcs")
    builder.add_edge("react_npcs", "next_scene")
    builder.add_edge("next_scene", END)
    return builder


# Module-level singleton for Studio (added to langgraph.json in task 4.2)
graph = build_game_graph().compile()
