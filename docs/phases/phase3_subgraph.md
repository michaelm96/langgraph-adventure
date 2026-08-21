# Phase 3 — Subgraph-as-Node (NPC subgraph)

Phases 1–2 build a small linear graph with one branching point. Phase 3 nests a **subgraph inside a node**: each Scene's NPCs get their own compiled graph, invoked from inside `invoke_npc`. This is the standard way to isolate per-entity logic (NPCs, inventory items, factions) so each can have its own state shape and node set without polluting the parent graph.

## 1. Concept

A **subgraph** is just a compiled `StateGraph` you call from inside a node of another graph. You can invoke it directly with `g.invoke(state)`, or you can hand the compiled graph to `builder.add_node("name", subgraph)` and let the parent call it like any other node. The two patterns differ in who owns state shape and who controls the input/output mapping.

Use a subgraph when one branch of your logic deserves its own state model — e.g. an NPC subgraph with `{persona, situation, dialogue}` rather than reusing the parent game's `{theme, history, ...}`. The parent stays flat; the subgraph owns its complexity.

## 2. Reading

- LangGraph subgraphs: <https://langchain-ai.github.io/langgraph/concepts/low_level/#subgraphs>

Read the **Subgraphs** section. You should be able to explain the difference between calling a subgraph via `invoke()` (you own I/O) vs adding it as a node (LangGraph wires state for you) before the hands-on.

## 3. Hands-on

Build `npc_graph.py` with 3 nodes (`perceive_situation`, `decide_action`, `speak`) and wire it into the meta-graph as the `invoke_npc` node:

1. Define `NPCState(TypedDict)` with `persona`, `situation`, `dialogue`.
2. Write three node functions; `decide_action` returns a canned line keyed by `persona`.
3. `build_npc_graph(persona)` returns a compiled `StateGraph`; `persona` is baked in.
4. In `meta_graph.py`, add a node `invoke_npc` that, for each NPC in the latest scene, builds and invokes `build_npc_graph(persona)` and collects the dialogue into `state["npc_dialogues"]`.
5. Add a conditional edge after `scene_generator`: route to `invoke_npc` when the scene has NPCs, else `END`.

Compare your solution to the reference. The shape matters more than the names.

## 4. Reference

Working code: `src/langgraph_adventure/phases/phase3_subgraph.py`.

```python
import os
os.environ.setdefault("MOCK_LLM", "1")
from langgraph_adventure.meta_graph import build_meta_graph

def demo() -> None:
    g = build_meta_graph()
    base = {"theme": "noir detective", "world_seed": "test",
            "history": [], "npc_dialogues": {}}
    for req in ["continue", "branch_left", "branch_right"]:
        r = g.invoke({**base, "current_request": req})
        scene = r["history"][0]
        print(f"[{req}] scene_id={scene.scene_id}")
        for persona, dialogue in r["npc_dialogues"].items():
            print(f"  {persona}: \"{dialogue}\"")
    assert "Old Hermit" in g.invoke({**base, "current_request": "continue"})["npc_dialogues"]
    print("npc subgraphs invoked from meta-graph ✓")
```

Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase3_subgraph
```

The `meta_graph` wires `START → theme_intake → scene_generator → (conditional) → invoke_npc → END`. `invoke_npc` builds a fresh `build_npc_graph(persona)` for each NPC in the latest scene and merges their dialogues into `state["npc_dialogues"]`.

## 5. Self-check

1. Why is `persona` baked in at build time (via `build_npc_graph(persona)`) rather than passed through state on every invocation?
2. What's the difference between calling a subgraph via `g.invoke(...)` and adding it to the parent via `builder.add_node("invoke_npc", subgraph)`?
3. What does `add_conditional_edges("scene_generator", route_after_scene, {"invoke_npc": "invoke_npc", "__end__": END})` accomplish, and why is the routing function separate from `scene_generator` itself?

If any answer felt shaky, re-read the **Subgraphs** section and try the hands-on again.
