# Phase 1 — StateGraph + `add_messages`

The smallest useful LangGraph program: a 2-node graph that emits one hardcoded opening scene. The point is to feel the machinery before the next phase layers branching on top.

## 1. Concept

A **`StateGraph`** is a directed graph of Python callables (nodes) connected by edges. You give it a `TypedDict` describing state, add them with `add_node(name, fn)`, wire edges with `add_edge(...)`, then `compile()` to get a runnable graph. Invoke with `g.invoke(initial_state)`.

The state shape — `MetaState` in `meta_graph.py` — is a `TypedDict` with `theme`, `world_seed`, and `history`. The `history` field uses an **`add_messages`-style reducer** via `Annotated[list[Scene], operator.add]`. When a node returns `{"history": [scene]}`, the value gets *appended* — not overwritten. Without the reducer, returning a list would replace the whole list with that one scene.

For Phase 1 the reducer isn't strictly needed (only one scene is emitted) but it's there because later phases will stream many scenes through the graph.

## 2. Reading

- LangGraph low-level overview: <https://langchain-ai.github.io/langgraph/concepts/low_level/#stategraph>
- Reducers: <https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers>

Skim the first link, then re-read **Reducers**. You should be able to explain what `Annotated[list[Scene], operator.add]` does before the hands-on.

## 3. Hands-on

Build your own 2-node graph before peeking at the reference:

1. Make a `TypedDict` `MyState` with `name: str` and `log: Annotated[list[str], operator.add]`.
2. Add two nodes: `greet` (returns `{"log": [f"hello, {name}"]}`) and `farewell` (returns `{"log": [f"goodbye, {name}"]}`).
3. Wire `START → greet → farewell → END` and `compile()`.
4. Invoke with `{"name": "Ada", "log": []}` and print the final `log`.

Your solution should look almost identical to the reference — that's the point. LangGraph has one shape; you just fill it in.

## 4. Reference

Working code: `src/langgraph_adventure/phases/phase1_stategraph.py`.

```python
import os
os.environ.setdefault("MOCK_LLM", "1")  # mock mode before graph imports

from langgraph_adventure.meta_graph import build_meta_graph

def demo() -> None:
    g = build_meta_graph()
    result = g.invoke(
        {"theme": "noir detective", "world_seed": "test", "history": []}
    )
    assert len(result["history"]) == 1
    scene = result["history"][0]
    assert len(scene.actions) >= 2
    print(f"Scene: {scene.description}")
    print("Actions:")
    for a in scene.actions:
        print(f"  [{a.id}] {a.label} → {a.next_state}")
```

Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase1_stategraph
```

Expected output:

```
Scene: You stand before a heavy door. It creaks slightly. The air smells of rain and old wood.
Actions:
  [A] Open the door → continue
  [B] Turn back → end
```

The actual graph (`meta_graph.py`) wires `START → theme_intake → scene_generator → END`. `theme_intake` returns a hardcoded `Scene`; `scene_generator` is a no-op placeholder that later phases will replace with an LLM-driven generator.

## 5. Self-check

1. Why is `MetaState` a `TypedDict` instead of a regular `dict` or a Pydantic `BaseModel`?
2. What does `Annotated[list[Scene], operator.add]` do, and what would happen if you dropped the `Annotated[...]` wrapper?
3. What are `START` and `END` — real nodes, or sentinels the runtime uses to know where execution begins and ends?

If any answer felt shaky, re-read the **StateGraph** and **Reducers** sections and try the hands-on again.