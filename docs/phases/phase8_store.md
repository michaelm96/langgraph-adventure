# Phase 8 — Long-Term Memory with `Store`
Phase 4's checkpointer remembers *this* conversation. Phase 8's `Store` remembers the *player* — across threads, across sessions, across restarts.

## 1. Concept
A `Store` is a cross-thread key-value memory. Nodes read and write with `store.get(namespace_tuple, key)` / `store.put(namespace_tuple, key, value)`, where the namespace is a tuple like `("npc_memories", "Old Hermit")`. Unlike a checkpointer — which is scoped to one `thread_id` and stores the whole graph state at each step — a store is scoped to nothing but its namespaces, so anything written under one `thread_id` is visible from every other.

That difference is the whole point: a checkpointer resumes an interrupted game; a store gives an NPC a memory that survives the game ending.

Nodes reach the store via `runtime.store`, which langgraph injects when the node takes a `Runtime` parameter:

```python
def _decide_action(state: NPCState, runtime: Runtime) -> dict:
    result = runtime.store.get(("npc_memories", state["persona"]), "player_name")
    ...
```

The store is attached at **compile** time — `builder.compile(store=my_store)`. In langgraph 1.2.x, passing a store through `config` is not honored; the compile-time parameter is the only public injection point.

## 2. Reading
- LangGraph Memory Store: <https://langchain-ai.github.io/langgraph/concepts/persistence/#memory-store>

Focus on (a) namespace tuples and how they partition memory, (b) `get`/`put`/`search` semantics, (c) why store and checkpointer are separate concerns.

## 3. Hands-on
In `npc_graph.py`, `_decide_action` reads `player_name` from `runtime.store.get(("npc_memories", persona), "player_name")` and, when present, prefixes the canned line with `"Ah, {name}, we meet again."`. After the line is produced, `_speak` writes it back as `last_interaction` in that same per-NPC namespace.

The parent graph passes its store down: `_npc_react_node` reads `runtime.store` and hands it to `build_npc_graph(npc_name, store=store)`, which compiles the subgraph with `compile(store=store)`. The game-graph's `persist` node writes player-level history under a different namespace, `("player_history", scene_id)`, so NPC memories and player history never collide.

Helpers live in `store.py`: `get_store()` (singleton `InMemoryStore`), `reset_store()` for test isolation, and `npc_recall(store, npc, key)` / `npc_remember(store, npc, key, value)` which wrap the namespace convention so callers never hand-build tuples.

Try it: pre-seed a `player_name`, run one scene, then run a second scene under a **different `thread_id`** and confirm the NPC still greets the player by name.

## 4. Reference
Working code: `src/langgraph_adventure/phases/phase8_store.py`. Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase8_store
```

The demo seeds `npc_remember(store, "Old Hermit", "player_name", "Michael")`, then plays two "sessions" on separate thread ids (`session-1`, `session-2`) sharing one store. It asserts that (a) the Hermit greets Michael by name in both sessions, (b) `last_interaction` was written to `("npc_memories", "Old Hermit")`, and (c) the turn was recorded under `("player_history", "forest_meet")`.

Note the upgrade path: `InMemoryStore` dies with the process. Swapping in a persistent store implementation keeps every signature above unchanged.

## 5. Self-check
1. What's the difference between a `Store` and a `Checkpointer`?
2. Why does `config['store']` not work in langgraph 1.2.x — what must you use instead?
3. How do you namespace per-NPC memories so two NPCs don't collide?

If any answer felt shaky, re-read the Memory Store docs and trace the store through the demo by hand: seed → `compile(store=...)` → `_npc_react_node` → `build_npc_graph(store=...)` → `_decide_action` reads → `_speak` writes. Move on only when you can say which layer owns the store at each hop.
