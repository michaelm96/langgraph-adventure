# Phase 2 — `add_conditional_edges` for scene branching

Phase 1 ships a single hardcoded scene. Phase 2 layers a conditional edge so the graph can route between scenes based on state. The graph is still tiny; the point is the routing machinery.

## 1. Concept

A **conditional edge** picks the next node at runtime based on state. You call `add_conditional_edges(source_node, routing_fn, path_map)`. After `source_node` runs, LangGraph calls `routing_fn(state)` and looks up the returned key in `path_map` to decide which node to run next.

Without conditional edges, `add_edge(a, b)` always goes from `a` to `b`. With them, the same node can fan out to many successors — the routing function becomes the decision point. In this phase all three routes (`"continue"`, `"branch_left"`, `"branch_right"`) land on the same `scene_generator` node; differentiation happens inside `scene_generator` via a factory map keyed by `current_request`. A later phase will split routes into separate nodes.

## 2. Reading

- LangGraph conditional edges: <https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges>

Read the **Conditional edges** section. You should be able to explain the role of the routing function and the `path_map` dict before the hands-on.

## 3. Hands-on

Extend `meta_graph.py` so routing actually picks distinct scenes:

1. Add three scene factories: `_opening_scene`, `_forest_scene`, `_cave_scene`.
2. Write `route_request(state) -> str` returning `state["current_request"]`.
3. Wire `add_conditional_edges("theme_intake", route_request, {"continue": "scene_generator", "branch_left": "scene_generator", "branch_right": "scene_generator"})`.
4. Invoke the graph with three different `current_request` values and print each `scene_id`.

Compare your solution to the reference. The shape matters more than the names.

## 4. Reference

Working code: `src/langgraph_adventure/phases/phase2_conditional.py`.

```python
import os
os.environ.setdefault("MOCK_LLM", "1")
from langgraph_adventure.meta_graph import build_meta_graph

def demo() -> None:
    g = build_meta_graph()
    base = {"theme": "noir detective", "world_seed": "test", "history": []}
    r1 = g.invoke({**base, "current_request": "continue"})
    r2 = g.invoke({**base, "current_request": "branch_left"})
    # print scene_id + description + actions for each
    assert r1["history"][0].scene_id != r2["history"][0].scene_id
    print("branches differ ✓")
```

Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase2_conditional
```

Expected output (excerpt):

```
[continue] scene_id=opening
  You stand before a heavy door. It creaks slightly. The air smells of rain and old wood.
  actions:
    [A] Open the door → branch_left
    [B] Turn back → branch_right

[branch_left] scene_id=forest
  You step through the door into a dense, misty forest. Shafts of pale light filter through the canopy. Something rustles behind a fern.
  actions:
    [A] Investigate the sound → branch_left
    [B] Head back → branch_right

branches differ ✓
```

The graph (`meta_graph.py`) wires `START → theme_intake → (conditional) → scene_generator → END`. `theme_intake` preserves the injected `current_request` so the routing function sees whatever the caller passed in.

## 5. Self-check

1. What does the `path_map` dict in `add_conditional_edges` do, and how does it relate to the value returned by the routing function?
2. What happens if the routing function returns a key not in `path_map`?
3. Why does `theme_intake` preserve `current_request` instead of always resetting it to `"continue"`?

If any answer felt shaky, re-read the **Conditional edges** section and try the hands-on again.
