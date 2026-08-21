# Phase 6 — Parallel NPC Reactions with `Send`
Phase 5 routed the player's choice to the right node. Phase 6 fans **one node** out across **many inputs** — three NPCs in a scene each get their own reaction subgraph, invoked in parallel, and the results merge into one state.

## 1. Concept
`Send(node, arg)` is a routing primitive that a conditional-edge router can return. Instead of naming one downstream node, the router returns `list[Send]` — one per item — and langgraph invokes `node` N times in parallel, each with its own `arg` as the node's input. The targeted node runs N times concurrently; their state updates merge via the field's reducer.

This is how you parallelize per-item work without writing a for-loop in a single node. The fanout pattern:

```python
def route_after_choice(state) -> list[Send]:
    npcs = state["current_scene"].npcs
    return [Send("_npc_react", {"npc_name": npc, "situation": ...}) for npc in npcs]
```

Each `Send` carries its own dict arg, so the same node can process different inputs. The fan-out runs in parallel, and `Annotated[dict, operator.or_]` merges the per-NPC `{name: dialogue}` dicts into one.

## 2. Reading
- LangGraph `Send`: <https://langchain-ai.github.io/langgraph/concepts/low_level/#send>
Focus on (a) why `Send` only works as a conditional-edge return, (b) how each `Send`'s arg becomes the target node's input, (c) how parallel writes need a reducer (here `operator.or_`) to merge without overwriting.

## 3. Hands-on
In `game_graph.py`, replace the Phase 5 `react_npcs` stub with a conditional-edge router that returns `list[Send]`. One `Send` per NPC in `state["current_scene"].npcs`, targeting `_npc_react`. Declare `npc_dialogues: Annotated[dict[str, str], operator.or_]` so parallel writes merge. Add `merge_reactions` downstream of `_npc_react` — it runs **once** after the fanout completes, reading the merged `npc_dialogues` and formatting each entry as an `AIMessage` into `state.messages`. Test with a 3-NPC scene and verify all three dialogues appear in both `npc_dialogues` AND `messages`.

## 4. Reference
Working code: `src/langgraph_adventure/phases/phase6_send.py`. Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase6_send
```

The demo builds a 3-NPC scene, resumes action `"A"` (continue), and verifies: (a) all 3 NPCs are in `npc_dialogues`, (b) all 3 NPC `AIMessage`s are in `messages` from `merge_reactions`, (c) elapsed time is under 5 seconds (parallel fanout is fast even with 3 NPCs).

## 5. Self-check
1. Why does `list[Send]` work as a router return but NOT as a regular node return?
2. What's the purpose of the `operator.or_` reducer on `npc_dialogues`?
3. When does `merge_reactions` run — per NPC, or once after fanout completes?

If any answer felt shaky, re-read the **Send** section in the LangGraph docs and trace the 3-NPC flow by hand: fanout from `route_choice` → 3 parallel `_npc_react` → `merge_reactions` collects → `next_scene`. Move on only when the routing and merge are clear.
