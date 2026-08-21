from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


class NPCState(TypedDict):
    """Sub-graph state for a single NPC.

    persona is baked in at build time (config) and stays constant.
    situation comes from the caller (the surrounding game-graph's current scene).
    dialogue is the NPC's output - what they say or do.
    """

    persona: str
    situation: str
    dialogue: str


def _perceive_situation(state: NPCState) -> dict:
    """Just passes through - the situation was set by the caller."""
    return {}


def _decide_action(state: NPCState) -> dict:
    """MOCK canned dialogue. Real LLM call comes in phase 9.

    Returns a fixed line keyed by persona so different NPCs produce different output.
    """
    persona_lines = {
        "Old Hermit": "I've been waiting for someone to come this way. The forest has grown quiet lately.",
        "Witch of the Mist": "Ah, a traveler. The fog here is thicker than it looks.",
        "Cave Troll": "Grrr...",
    }
    return {"dialogue": persona_lines.get(state["persona"], "...")}


def _speak(state: NPCState) -> dict:
    """Format the dialogue for output."""
    return {}


def build_npc_graph(persona: str) -> CompiledStateGraph:
    """Build a per-NPC subgraph. `persona` is baked in.

    Compile flow: perceive_situation -> decide_action -> speak -> END.

    Usage:
        g = build_npc_graph("Old Hermit")
        result = g.invoke({"persona": "Old Hermit", "situation": "A traveler approaches", "dialogue": ""})
        print(result["dialogue"])  # "I've been waiting..."
    """
    builder = StateGraph(NPCState)
    builder.add_node("perceive_situation", _perceive_situation)
    builder.add_node("decide_action", _decide_action)
    builder.add_node("speak", _speak)
    builder.add_edge(START, "perceive_situation")
    builder.add_edge("perceive_situation", "decide_action")
    builder.add_edge("decide_action", "speak")
    builder.add_edge("speak", END)
    return builder.compile()
