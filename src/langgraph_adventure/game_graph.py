"""Game-loop graph: present_scene + interrupt_for_choice.

Phase 4 wires up only 2 nodes. `present_scene` prints the scene narration
and action menu; `interrupt_for_choice` pauses the graph via `interrupt()`
so the player can pick an action. Later phases add streaming, the
scene-generator branch, and the action-handler node.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any

from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import MessagesState, add_messages
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage
from langgraph.types import interrupt, Command, Send
from langgraph.runtime import Runtime

from langgraph_adventure.npc_graph import build_npc_graph
from langgraph_adventure.state import Action, Scene
from langgraph_adventure.meta_graph import _SCENES


class GameState(MessagesState):
    """State for the game-graph.

    Inherits `messages` from MessagesState (uses add_messages reducer).
    Adds game-specific fields.

    `npc_dialogues` uses operator.or_ as a reducer so multiple parallel
    Send-fanned NPC reactions merge their dict contributions into one.
    """
    current_scene: Scene | None
    chosen_action: Action | None
    npc_dialogues: Annotated[dict[str, str], operator.or_]


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


def _route_after_choice(state: GameState) -> str | list[Send]:
    """Conditional-edge router: pick next node based on chosen_action.next_state.

    - "end" → END (terminate game)
    - "custom" → interpret_custom_action (LLM routing stub)
    - otherwise → fanout via Send to _npc_react (one Send per NPC in scene)

    Returning list[Send] from a conditional edge is the standard langgraph
    fanout pattern — each Send invokes the target node in parallel with its
    own input. The Send target (_npc_react) merges results into npc_dialogues.
    """
    action = state.get("chosen_action")
    if action is None or action.next_state == "end":
        return "__end__"
    if action.next_state == "custom":
        return "interpret_custom_action"
    # Fanout: one Send per NPC
    scene = state.get("current_scene")
    npcs = getattr(scene, "npcs", None) or []
    if not npcs:
        # No NPCs to react to — skip react_npcs, go straight to next_scene
        return "next_scene"
    return [
        Send("_npc_react", {"npc_name": npc, "situation": scene.description if scene else ""})
        for npc in npcs
    ]


def _npc_react_node(state: GameState, runtime: Runtime) -> dict:
    """Single-NPC react node. Reads npc_name and situation from state (set by Send arg).

    Runs the per-NPC subgraph and returns its dialogue, keyed by NPC name.
    Passes the parent graph's store to the NPC subgraph so it can read/write
    per-NPC long-term memory.
    """
    npc_name = state.get("npc_name", "")
    situation = state.get("situation", "")
    if not npc_name:
        return {}
    store = getattr(runtime, "store", None)
    npc_g = build_npc_graph(npc_name, store=store)
    result = npc_g.invoke({"persona": npc_name, "situation": situation, "dialogue": ""})
    return {"npc_dialogues": {npc_name: result["dialogue"]}}


def merge_reactions(state: GameState) -> dict:
    """Format npc_dialogues into MessagesState messages (AIMessage per NPC).

    Runs once after all parallel _npc_react invocations complete.
    Returns dict with messages list (consumed by MessagesState's add_messages reducer).
    """
    npc_dialogues = state.get("npc_dialogues", {})
    if not npc_dialogues:
        return {}
    messages = [
        AIMessage(content=f'{persona}: "{dialogue}"')
        for persona, dialogue in npc_dialogues.items()
    ]
    return {"messages": messages}


def persist(state: GameState, runtime: Runtime) -> dict:
    """Write player's action + scene context to store under player_history namespace.

    Keyed by session_id (from config) so the same player across sessions
    accumulates history.

    Note: per-NPC memories are already written by _speak in npc_graph. This
    node handles player-level history only.
    """
    action = state.get("chosen_action")
    scene = state.get("current_scene")
    if action is None or scene is None:
        return {}

    store = getattr(runtime, "store", None)
    if store is None:
        return {}

    # We don't have direct access to config here, so use a fixed key per turn.
    # Phase 9 uses session_id from config.
    turn_key = f"turn_{scene.scene_id}_{action.id}"
    history_entry = {
        "scene_id": scene.scene_id,
        "action_id": action.id,
        "action_label": action.label,
        "next_state": action.next_state,
    }
    store.put(("player_history", scene.scene_id), turn_key, history_entry)
    return {}


def next_scene(state: GameState) -> dict:
    """Pick the next scene based on the chosen action's routing key.

    Phase 7 would stream NPC dialogue here; for now, instant lookup via the
    meta-graph's hardcoded scene factories so the story actually progresses.
    """
    action = state.get("chosen_action")
    if action is None:
        return {}
    factory = _SCENES.get(action.next_state, _SCENES["continue"])
    return {"current_scene": factory()}


def build_game_graph() -> StateGraph:
    """Build the game-graph with 6 nodes.

    Returns the uncompiled builder; callers compile with `.compile(checkpointer=...)`.
    Compile flow: START → present_scene → interrupt_for_choice → route_choice
                   → (conditional) → [interpret_custom_action] → _npc_react (fanned)
                   → next_scene → END.

    Phase 6 changes:
    - `react_npcs` is no longer a regular node. The conditional edge from
      `route_choice` directly returns `list[Send]` for parallel NPC fanout.
    - `_npc_react` is the per-NPC node that Send targets.
    - When a scene has no NPCs, the conditional edge skips react_npcs and
      routes directly to `next_scene`.

    Why no Command(goto=END): langgraph 1.2.x silently corrupts chosen_action
    state when Command routes to END. Conditional edges with END as a target
    don't have this bug.
    """
    builder = StateGraph(GameState)
    builder.add_node("present_scene", present_scene)
    builder.add_node("interrupt_for_choice", interrupt_for_choice)
    builder.add_node("route_choice", _route_choice)
    builder.add_node("interpret_custom_action", interpret_custom_action)
    builder.add_node("_npc_react", _npc_react_node)
    builder.add_node("merge_reactions", merge_reactions)
    builder.add_node("persist", persist)
    builder.add_node("next_scene", next_scene)
    builder.add_edge(START, "present_scene")
    builder.add_edge("present_scene", "interrupt_for_choice")
    builder.add_edge("interrupt_for_choice", "route_choice")
    builder.add_conditional_edges(
        "route_choice",
        _route_after_choice,
        {
            "interpret_custom_action": "interpret_custom_action",
            "next_scene": "next_scene",
            "__end__": END,
        },
    )
    builder.add_edge("interpret_custom_action", "next_scene")
    builder.add_edge("_npc_react", "merge_reactions")
    builder.add_edge("merge_reactions", "persist")
    builder.add_edge("persist", "next_scene")
    builder.add_edge("next_scene", END)
    return builder


# Module-level singleton for Studio (added to langgraph.json in task 4.2)
graph = build_game_graph().compile()
