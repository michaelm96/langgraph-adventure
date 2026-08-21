# Tutorial Phases

This tutorial teaches LangGraph by building an AI text-adventure engine in 9 phases.
Every phase adds exactly one LangGraph concept to the running game.

| # | Concept | What you'll add |
|---|---------|-----------------|
| 1 | `StateGraph` + `add_messages` reducer | A 2-node meta-graph that emits an opening scene |
| 2 | `add_conditional_edges` | Branch on the player's A/B choice |
| 3 | subgraph-as-node | First NPC appears, runs its own mini-graph |
| 4 | `interrupt()` | Game pauses, awaits the player's choice |
| 5 | `Command` (explicit routing) | Player picks "custom action"; LLM routes it |
| 6 | `Send` (map-reduce parallel) | Two NPCs react in parallel to a player move |
| 7 | `astream_events` (token streaming) | Narration streams token-by-token to the terminal |
| 8 | `Store` (long-term memory) | NPCs remember you across sessions |
| 9 | checkpointer + `update_state` (time travel) | "Undo last turn" button |

By phase 9 you'll have built the full design and practiced every major LangGraph pattern.

## 1. Concept

Each phase teaches exactly one LangGraph concept. The running game grows by
increments — every phase leaves the previous demos runnable, and adds one new
piece. The point is to feel each concept in isolation before the next one
layers on top.

## 2. Reading

Before each phase, read the linked LangGraph docs page. The full starting
point is https://langchain-ai.github.io/langgraph/. Each phase doc links to
the specific subsection that matters for that phase.

## 3. Hands-on

Every phase has a hands-on task before you peek at the reference. Do the
task first — type the graph yourself, run it, see what happens. Then read
the reference section to compare your solution to the project's.

## 4. Reference

Working code lives in `src/langgraph_adventure/phases/phaseN_*.py`. Each
file exports a `demo()` function and is runnable as a module:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phaseN_...
```

Demos run with `MOCK_LLM=1` by default (no API key needed) — see
`src/langgraph_adventure/llm.py`.

## 5. Self-check

Each phase ends with 2–3 questions. Try answering them without looking at
the reference. If you're stuck, re-read the Concept section — the answers
are there.

Start with [Phase 1: StateGraph + add_messages](phase1_stategraph.md).