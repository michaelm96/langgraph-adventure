"""Phase 1 demo — StateGraph + add_messages reducer.

Builds the meta-graph from Task 1.2 and invokes it with MOCK_LLM=1.
Asserts one opening Scene with at least two Actions, then prints the
scene description and an actions table.

Run:
    MOCK_LLM=1 python -m langgraph_adventure.phases.phase1_stategraph
"""

from __future__ import annotations

import os

# C10: enable MOCK mode before any graph / LLM imports.
os.environ.setdefault("MOCK_LLM", "1")

from langgraph_adventure.meta_graph import build_meta_graph


def demo() -> None:
    g = build_meta_graph()
    result = g.invoke(
        {"theme": "noir detective", "world_seed": "test", "history": []}
    )
    assert len(result["history"]) == 1, (
        f"expected 1 scene, got {len(result['history'])}"
    )
    scene = result["history"][0]
    assert len(scene.actions) >= 2, (
        f"expected 2+ actions, got {len(scene.actions)}"
    )
    print(f"Scene: {scene.description}")
    print("Actions:")
    for a in scene.actions:
        print(f"  [{a.id}] {a.label} → {a.next_state}")


if __name__ == "__main__":
    demo()