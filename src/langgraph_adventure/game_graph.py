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

    Phase 5.2: also append a synthetic "custom" action so the player can type
    free text. The CLI/REPL prompts for input when this option is chosen.
    """
    scene = state.get("current_scene")
    if scene is None:
        return {}
    actions_payload = [{"id": a.id, "label": a.label, "next_state": a.next_state} for a in scene.actions]
    # Append "custom" option that lets player type free text
    actions_payload.append({"id": "custom", "label": "(type your own action)", "next_state": "custom"})
    payload = {
        "scene_id": scene.scene_id,
        "actions": actions_payload,
        "description": scene.description,
    }
    user_choice = interrupt(payload)
    matched = next((a for a in scene.actions if a.id == user_choice), None)
    if matched is not None:
        # Explicitly copy — assigning `chosen = matched` keeps a reference, and
        # langgraph's checkpoint re-serialization/deserialization then corrupts
        # `next_state` (returns 'continue' regardless of the original). The
        # explicit copy sidesteps the reference aliasing.
        chosen = Action(id=matched.id, label=matched.label, next_state=matched.next_state)
    elif user_choice == "custom":
        # In real CLI, REPL prompts for free text and passes it as the resume value.
        # In tests, the demo will pass a pre-built custom action.
        chosen = Action(id="custom", label="(typed)", next_state="custom")
    else:
        chosen = Action(id=user_choice, label=user_choice, next_state="continue")
    return {"chosen_action": chosen}


def interpret_custom_action(state: GameState) -> dict:
    """LLM call: interpret player's free-text action and route to next_state.

    Phase 5: stub returns 'continue' as default (MOCK LLM doesn't interpret).
    Phase 8 will swap to a real LLM call that reads chosen_action.label and
    decides between continue/branch_left/branch_right/end.

    Always sets chosen_action to a fresh Action with the determined next_state.
    """
    action = state.get("chosen_action")
    if action is None:
        return {}
    # Phase 5 stub: route everything to "continue" (MOCK fallback)
    # Phase 8 will replace this with a real LLM call
    determined_next_state = "continue"
    return {
        "chosen_action": Action(
            id=action.id,
            label=action.label,
            next_state=determined_next_state,
        ),
    }


def _route_choice(state: GameState) -> dict:
    """Pure routing decision — returns state dict only.

    NOTE: Do NOT use Command(goto=END, update={}) here. langgraph 1.2.x has a
    bug where Command(goto=END) corrupts the chosen_action field's next_state
    (silently overwrites it with 'continue' on checkpoint re-serialization).
    Use add_conditional_edges instead, with END as a routing target.

    Returns chosen_action so it's preserved; routing is done by the
    conditional edge wired in build_game_graph.
    """
    return {}


def _route_after_choice(state: GameState) -> str:
    """Conditional-edge router: pick next node based on chosen_action.next_state.

    - "end" → END (terminate game)
    - "custom" → interpret_custom_action (LLM routing stub)
    - otherwise → react_npcs (continue)
    """
    action = state.get("chosen_action")
    if action is None or action.next_state == "end":
        return "__end__"
    if action.next_state == "custom":
        return "interpret_custom_action"
    return "react_npcs"


def react_npcs(state: GameState) -> dict:
    """Run NPC reactions (Phase 6 wires Send fanout; Phase 5 just stub)."""
    return {}


def next_scene(state: GameState) -> dict:
    """Generate the next scene (Phase 7 streams narration; Phase 5 just stub)."""
    return {}


def build_game_graph() -> StateGraph:
    """Build the game-graph with 6 nodes.

    Returns the uncompiled builder; callers compile with `.compile(checkpointer=...)`.
    Compile flow: START → present_scene → interrupt_for_choice → _route_choice
                   → (conditional) → interpret_custom_action → react_npcs
                   → next_scene → END.

    Why no Command(goto=END): langgraph 1.2.x silently corrupts chosen_action
    state when Command routes to END. Conditional edges with END as a target
    don't have this bug.
    """
    builder = StateGraph(GameState)
    builder.add_node("present_scene", present_scene)
    builder.add_node("interrupt_for_choice", interrupt_for_choice)
    builder.add_node("route_choice", _route_choice)
    builder.add_node("interpret_custom_action", interpret_custom_action)
    builder.add_node("react_npcs", react_npcs)
    builder.add_node("next_scene", next_scene)
    builder.add_edge(START, "present_scene")
    builder.add_edge("present_scene", "interrupt_for_choice")
    builder.add_edge("interrupt_for_choice", "route_choice")
    builder.add_conditional_edges(
        "route_choice",
        _route_after_choice,
        {
            "react_npcs": "react_npcs",
            "interpret_custom_action": "interpret_custom_action",
            "__end__": END,
        },
    )
    builder.add_edge("interpret_custom_action", "react_npcs")
    builder.add_edge("react_npcs", "next_scene")
    builder.add_edge("next_scene", END)
    return builder


# Module-level singleton for Studio (added to langgraph.json in task 4.2)
graph = build_game_graph().compile()
