from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langgraph.store.base import BaseStore


class NPCState(TypedDict):
    """Sub-graph state for a single NPC.

    persona is baked in at build time (config) and stays constant.
    situation comes from the caller (the surrounding game-graph's current scene).
    dialogue is the NPC's output - what they say or do.
    """

    persona: str
    situation: str
    dialogue: str


def _perceive_situation(state: NPCState, runtime: Runtime) -> dict:
    """Just passes through - the situation was set by the caller."""
    return {}


def _decide_action(state: NPCState, runtime: Runtime) -> dict:
    """MOCK canned dialogue. Reads player_name from store for greeting.

    If runtime.store is None (no store passed in config), falls back to the
    MOCK canned dialogue without greeting.
    """
    persona_lines = {
        "Old Hermit": "I've been waiting for someone to come this way. The forest has grown quiet lately.",
        "Witch of the Mist": "Ah, a traveler. The fog here is thicker than it looks.",
        "Cave Troll": "Grrr...",
    }
    base_line = persona_lines.get(state["persona"], "...")

    # Read player_name from store if available
    store = getattr(runtime, "store", None)
    player_name = None
    if store is not None:
        result = store.get(("npc_memories", state["persona"]), "player_name")
        if result is not None:
            player_name = result.value

    if player_name:
        # Replace the first sentence with a greeting
        base_line = f"Ah, {player_name}, we meet again. {base_line}"

    return {"dialogue": base_line}


def _speak(state: NPCState, runtime: Runtime) -> dict:
    """Write last_interaction to store after dialogue is produced."""
    store = getattr(runtime, "store", None)
    if store is not None:
        store.put(("npc_memories", state["persona"]), "last_interaction", state["dialogue"])
    return {}


def build_npc_graph(persona: str, store: BaseStore | None = None) -> CompiledStateGraph:
    """Build a per-NPC subgraph. `persona` is baked in.

    Compile flow: perceive_situation -> decide_action -> speak -> END.

    Optional `store`: passed to `compile(store=...)` so nodes can read/write
    per-NPC long-term memory via `runtime.store`. In langgraph 1.2.x the
    `config['store']` path is NOT honored; the compile-time parameter is
    the only public way to inject a store.

    Usage:
        g = build_npc_graph("Old Hermit", store=get_store())
        result = g.invoke({"persona": "Old Hermit", "situation": "..."})
        print(result["dialogue"])
    """
    builder = StateGraph(NPCState)
    builder.add_node("perceive_situation", _perceive_situation)
    builder.add_node("decide_action", _decide_action)
    builder.add_node("speak", _speak)
    builder.add_edge(START, "perceive_situation")
    builder.add_edge("perceive_situation", "decide_action")
    builder.add_edge("decide_action", "speak")
    builder.add_edge("speak", END)
    if store is None:
        return builder.compile()
    return builder.compile(store=store)
