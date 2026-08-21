# langgraph-adventure

An AI text adventure engine built to teach LangGraph concepts one phase at a time.
Each phase ships a small, runnable demo plus the cumulative production code, so you
can read the demo to learn the pattern and read the production code to see how it
fits the whole.

## What's this

A 9-phase tutorial project. By the end you have a working text adventure where a
meta graph orchestrates a game graph and per-NPC subgraphs, with streaming,
memory, interrupts, and time travel. Every phase is a self-contained lesson:
the demo file shows only that phase's concept, and the production code in
`src/langgraph_adventure/` is always equivalent to the final (phase 9) state.

## Roadmap

1. **StateGraph + add_messages** — the smallest useful graph: a chat turn loop.
2. **conditional_edges** — branch on player intent to take an action or quit.
3. **subgraph-as-node** — NPC reactions live in their own graphs, invoked as nodes.
4. **interrupt()** — pause for human input before a consequential choice.
5. **Command (explicit routing)** — nodes return the next node, not just state.
6. **Send (map-reduce parallel)** — fan out to all NPCs, then fold their reactions.
7. **astream_events (token streaming)** — stream tokens to the player as they generate.
8. **Store (long-term memory)** — remember NPCs across sessions.
9. **checkpointer + update_state (time travel)** — rewind and replay any turn.

Per-phase concept docs land in `docs/phases/README.md` (written in Task 1.3).

## Run a demo

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase{N}
```

Replace `N` with the phase number. `MOCK_LLM=1` skips real LLM calls so you can
run any demo without an API key.

## Studio

After installing the dev extras (`pip install -e ".[dev]"`), start the LangGraph
Studio dev server:

```bash
python -m langgraph_cli dev
```

The UI loads `langgraph.json`, which exposes the `meta` and `game` graphs. The
NPC graph is added in phase 3.

## Status

Tutorial in progress — phases 1-9 land in order. See `.superpowers/sdd/` for
the full plan and the per-task briefs.
