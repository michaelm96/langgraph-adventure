# langgraph-adventure

An AI text adventure engine built to teach LangGraph concepts one phase at a time.
Each phase ships a small, runnable demo plus the cumulative production code, so you
can read the demo to learn the pattern and read the production code to see how it
fits the whole.

## What's this

A 10-phase tutorial project. Phases 1–9 each ship a runnable demo + cumulative
production code, so by the end you have a working text adventure where a meta
graph orchestrates a game graph and per-NPC subgraphs, with streaming, memory,
interrupts, and time travel. Phase 10 ties it together (README + push).

Every demo file shows only that phase's concept, and the production code in
`src/langgraph_adventure/` is always equivalent to the final (phase 9) state.

## Roadmap

| Phase | Concept | Game slice | Demo |
|-------|---------|-----------|------|
| 1 | `StateGraph` + `add_messages` | "You see a door. Open it?" basic turn loop | `phase1_stategraph` |
| 2 | `add_conditional_edges` | "Go left into the forest, or right into the cave?" | `phase2_conditional` |
| 3 | subgraph-as-node | First NPC ("Old Hermit") appears | `phase3_subgraph` |
| 4 | `interrupt()` | Game pauses, awaits choice | `phase4_interrupt` |
| 5 | `Command` (explicit routing) | "Type a custom action" — LLM routes it | `phase5_command` |
| 6 | `Send` (map-reduce parallel) | Two NPCs react in parallel | `phase6_send` |
| 7 | `astream_events` (token streaming) | Narration streams token-by-token | `phase7_stream` |
| 8 | `Store` (long-term memory) | NPC remembers you across sessions | `phase8_store` |
| 9 | `checkpointer` + `update_state` (time travel) | "Undo last turn" | `phase9_time_travel` |
| 10 | Final integration | README refresh + push to GitHub | (no demo) |

Per-phase concept docs live in `docs/phases/phase{N}_*.md`.

## Run a demo

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase{N}
```

Replace `N` with the phase number. `MOCK_LLM=1` skips real LLM calls so you can
run any demo without an API key.

Or run them all in sequence:

```bash
for n in 1 2 3 4 5 6 7 8 9; do
  MOCK_LLM=1 python -m langgraph_adventure.phases.phase${n}_*
done
```

Phase 10 has no demo — it covers the README refresh and the git push.

## Play the game (REPL)

The cumulative game graph (built across phases 1–9) runs as an interactive
REPL. Start it with:

```bash
lg-adv play "noir detective"
```

Or with the variable theme (phase 9):

```bash
lg-adv play "high fantasy quest"
```

Inside the REPL:

- Pick a letter to choose an action.
- Type your own action (the LLM interprets it).
- `/undo` — rewind to the previous turn.
- `/fork <thread-id>` — copy state to a new thread for alternate exploration.
- `/exit` — quit.

## Studio

After installing the dev extras (`pip install -e ".[dev]"`), start the LangGraph
Studio dev server:

```bash
python -m langgraph_cli dev
```

The UI loads `langgraph.json`, which exposes the `meta` and `game` graphs. Use
Studio to visualize node structure and run individual nodes interactively.

## Project layout

```
langgraph-adventure/
├── pyproject.toml          # Package config + [dev] extras for Studio
├── README.md
├── docs/
│   ├── superpowers/
│   │   ├── specs/2026-08-21-langgraph-tutorial-design.md
│   │   └── plans/2026-08-21-langgraph-tutorial.md
│   └── phases/
│       ├── README.md       # 5-section template overview
│       └── phase{1..9}_*.md
├── src/langgraph_adventure/
│   ├── cli/play.py         # REPL + astream_events for opening narration
│   ├── state.py            # Pydantic Scene/Action/NPCReaction models
│   ├── meta_graph.py       # 2-node graph (theme_intake → scene_generator)
│   ├── npc_graph.py        # Per-NPC subgraph (uses runtime.store)
│   ├── game_graph.py       # Full game loop: present_scene → interrupt → react → merge → persist → next
│   ├── llm.py              # MiniMax provider + MOCK mode
│   ├── store.py            # InMemoryStore wrappers (npc_recall / npc_remember)
│   ├── persistence.py      # get_checkpointer(memory=...) helper
│   └── phases/
│       └── phase{1..9}_*.py  # Self-contained per-phase demos
└── langgraph.json          # Studio entrypoint (meta + game graphs)
```

## Status

✅ All 10 phases complete. The meta-graph, game-graph, and NPC subgraphs all
build and run under MOCK_LLM=1. Studio loads both graphs. The CLI REPL is
operational (with `--theme`, `/undo`, `/fork`, custom action input).

Real-mode operation (without `MOCK_LLM=1`) requires a valid `MINIMAX_API_KEY`
in `.env`. Phases 7+ work end-to-end with real MiniMax narration once that's
configured.

## Web UI

Local-only browser UI on top of the same game graph. Same SQLite DB as
the CLI — a `thread_id` opened in the CLI is the same `thread_id` you
can resume in the browser.

```bash
pip install -e ".[web]"
MOCK_LLM=1 python -m langgraph_adventure.web.server
# open http://127.0.0.1:8000/
```

Keyboard shortcuts: `1`/`2`/`3` choose action, `u` undo, `f` fork.

Single-user, no auth. URL is the only session token.

## License

MIT.