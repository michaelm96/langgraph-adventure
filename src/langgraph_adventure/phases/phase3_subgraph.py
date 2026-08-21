"""Phase 3 demo — NPC subgraphs invoked from inside the meta-graph.

When a Scene has NPCs, `meta_graph.invoke_npc` builds and invokes a per-NPC
subgraph (`npc_graph.build_npc_graph(persona)`) for each persona. The
returned dialogues are collected into `state["npc_dialogues"]`. The demo
runs the meta-graph for all three `current_request` branches and prints
both the scene and the NPC dialogue for each, then spot-checks that the
"continue" branch produced the Old Hermit dialogue.

Run:
    MOCK_LLM=1 python -m langgraph_adventure.phases.phase3_subgraph
"""

from __future__ import annotations

import os

# C10: enable MOCK mode before any graph / LLM imports.
os.environ.setdefault("MOCK_LLM", "1")

from langgraph_adventure.meta_graph import build_meta_graph


def demo() -> None:
    g = build_meta_graph()
    base = {"theme": "noir detective", "world_seed": "test", "history": [], "npc_dialogues": {}}

    for req in ["continue", "branch_left", "branch_right"]:
        r = g.invoke({**base, "current_request": req})
        scene = r["history"][0]
        print(f"\n[{req}] scene_id={scene.scene_id}")
        print(f"  {scene.description}")
        print(f"  npcs: {scene.npcs}")
        for persona, dialogue in r.get("npc_dialogues", {}).items():
            print(f"  {persona}: \"{dialogue}\"")

    # Spot-check: continue branch has Old Hermit
    r = g.invoke({**base, "current_request": "continue"})
    assert "Old Hermit" in r["npc_dialogues"], "expected Old Hermit dialogue"
    print("\nnpc subgraphs invoked from meta-graph ✓")


if __name__ == "__main__":
    demo()
