"""Phase 2 demo — `add_conditional_edges` for scene branching.

Invokes the meta-graph twice with different `current_request` values
(`"continue"` then `"branch_left"`) and asserts the dispatched scenes
differ. The conditional edge in `meta_graph.py` routes by `current_request`
into the same `scene_generator` node, which then picks the scene factory
based on the routing key.

Run:
    MOCK_LLM=1 python -m langgraph_adventure.phases.phase2_conditional
"""

from __future__ import annotations

import os

# C10: enable MOCK mode before any graph / LLM imports.
os.environ.setdefault("MOCK_LLM", "1")

from langgraph_adventure.meta_graph import build_meta_graph


def demo() -> None:
    g = build_meta_graph()
    base = {"theme": "noir detective", "world_seed": "test", "history": []}

    # First invoke: default branch
    r1 = g.invoke({**base, "current_request": "continue"})
    scene1 = r1["history"][0]
    print(f"[continue] scene_id={scene1.scene_id}")
    print(f"  {scene1.description}")
    print("  actions:")
    for a in scene1.actions:
        print(f"    [{a.id}] {a.label} → {a.next_state}")

    # Second invoke: left branch
    r2 = g.invoke({**base, "current_request": "branch_left"})
    scene2 = r2["history"][0]
    print(f"\n[branch_left] scene_id={scene2.scene_id}")
    print(f"  {scene2.description}")
    print("  actions:")
    for a in scene2.actions:
        print(f"    [{a.id}] {a.label} → {a.next_state}")

    assert scene1.scene_id != scene2.scene_id, "branches produced the same scene"
    assert scene1.scene_id == "opening", f"expected 'opening', got {scene1.scene_id}"
    assert scene2.scene_id == "forest", f"expected 'forest', got {scene2.scene_id}"
    print("\nbranches differ ✓")


if __name__ == "__main__":
    demo()
