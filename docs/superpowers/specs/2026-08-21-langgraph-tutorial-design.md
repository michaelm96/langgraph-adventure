# LangGraph Tutorial: AI Text Adventure Engine

**Date:** 2026-08-21
**Status:** Design — pending user review
**Goal:** Hands-on tutorial that teaches 9 LangGraph concepts by building an AI-driven text adventure engine.

## 1. Overview

This project teaches LangGraph through a single application: an AI-driven text adventure engine where an LLM generates scenes and NPCs on the fly, and the player navigates via choice-based input.

The project is structured as **9 incremental phases**. Each phase:
- Teaches exactly **one** LangGraph concept
- Ships a **runnable** game slice that exercises that concept
- Builds cumulatively on previous phases' working code
- Includes one reading task (point at LangGraph docs) + one hands-on task (you modify the graph yourself before peeking at the answer)
- Ends with a self-check (demo function passes, expected output appears)

By phase 9 the user has built the full design and practiced every major LangGraph pattern.

## 2. Goals

Learn these 9 LangGraph concepts by using them in the running game:

| # | Concept | Why this game scenario exercises it |
|---|---------|-------------------------------------|
| 1 | `StateGraph` + `add_messages` reducer | Player input is a HumanMessage; narration is an AIMessage |
| 2 | `add_conditional_edges` | Player picks A or B; graph branches |
| 3 | subgraph-as-node | First NPC appears, runs its own graph |
| 4 | `interrupt()` | Game pauses, awaits player choice |
| 5 | `Command` (explicit routing) | Player picks "custom action"; LLM routes it |
| 6 | `Send` (map-reduce parallel) | Two NPCs react in parallel to player move |
| 7 | `astream_events` (token streaming) | Narration streams token-by-token to terminal |
| 8 | `Store` (long-term memory) | NPC remembers you across sessions |
| 9 | checkpointer + `update_state` (time travel) | "Undo last turn" button |

## 3. Non-Goals

- Not a commercial game. No art, no audio, no commercial polish.
- Not production-ready. Error handling is "good enough for tutorial," not enterprise-grade.
- Not exhaustive. Doesn't cover LangGraph Cloud, LangGraph Platform, or remote deployment.
- Not framework. Each phase is direct LangGraph code; no abstractions, no helper layers.

## 4. Architecture

Two LangGraph graphs, each in its own file. Player experience is driven by the **game graph**; scenes are generated on demand by the **meta graph**.

### 4.1 Meta graph (`meta_graph.py`)

Generates scenes on demand. Pure LLM, no player interaction.

```
theme_intake   → (entry) receives theme seed + world_seed → outputs Scene-1
scene_generator → (entry) receives world state + player history → outputs next Scene
```

Output: `Scene` Pydantic model (description, npcs, actions).

### 4.2 Game graph (`game_graph.py`)

Plays scenes. Drives player experience.

```
present_scene       → (entry) takes Scene, narrates to player, presents choices
interrupt_for_choice → interrupt({actions, scene_id}) — pauses graph
route_choice        → receives resume value, builds Command(goto="react_npcs", update=...)
react_npcs          → Send-fanout: for each NPC, run build_npc_graph(persona) in parallel
merge_reactions     → collects NPCReaction objects, updates world state
persist             → writes each NPC's new memory to Store
next_scene          → invokes meta-graph for next Scene, loops back to present_scene
```

### 4.3 NPC graphs (`npc_graph.py`)

Small sub-graph (~3 nodes) used inside `react_npcs` via `Send`:

```
perceive_situation → reads persona + recent memories from Store
decide_action      → LLM structured output: action type + dialogue
speak              → returns NPCReaction
```

### 4.4 State

- `MetaState(TypedDict)`: theme, world_seed, history: list, current_scene_request
- `GameState(MessagesState)`: scene, choice, npc_reactions, world_history
- `Scene`, `NPCReaction`, `Action`: Pydantic models (clean serialization for Store)

## 5. Components

File layout under `src/langgraph_adventure/`:

```
langgraph_adventure/
├── __init__.py
├── meta_graph.py          # MetaState + build_meta_graph()
├── game_graph.py          # GameState + build_game_graph()
├── npc_graph.py           # build_npc_graph(persona) → NPC sub-graph
├── state.py               # Scene, NPCReaction, Action Pydantic models
├── store.py               # Store wrappers: npc_recall, npc_remember
├── persistence.py         # SqliteSaver checkpointer
├── llm.py                 # minimax provider (Anthropic Messages API)
├── phases/
│   ├── phase1_stategraph.py     # runnable reference for phase 1 only
│   ├── phase2_conditional.py    # phase 1 + 2
│   ├── ...
│   └── phase9_time_travel.py    # all 9 phases together
└── cli/
    ├── __init__.py
    ├── play.py                  # typer app
    └── langgraph.json           # Studio config: 3 graphs exposed
```

Each `phases/phase{N}_*.py` is a self-contained runnable demo showing only the concepts introduced in that phase. `phase9_time_travel.py` shows all 9 concepts together. The main `meta_graph.py`, `game_graph.py`, `npc_graph.py` are the cumulative production code (always equivalent to phase 9 state).

## 6. Data Flow (one player turn)

1. **Player starts session:** `lg-adv play "noir detective"`
   - CLI creates thread_id, opens checkpointer, calls `meta_graph.invoke({"theme": ..., "history": []})`
   - Game state initialized with opening scene

2. **Player sees scene:** `present_scene` calls `astream_events` to stream narration tokens to CLI
   - Prints: scene description, NPC names + descriptions, action menu
   - Reaches `interrupt_for_choice` → `interrupt({"actions": [...], "scene_id": ...})`
   - Graph pauses, checkpointer saves state

3. **Player picks action:** CLI calls `graph.invoke(Command(resume=<choice>))`
   - LangGraph resumes graph; `route_choice` builds Command to next node

4. **NPCs react in parallel:** `react_npcs` uses `Send(npc_id, build_npc_graph(persona).invoke(...))` per NPC
   - Each NPC graph reads its memories from Store, decides action, returns dialogue
   - LangGraph merges in parallel

5. **Persist + advance:** `persist` writes NPC memories to Store; `next_scene` calls meta-graph for next Scene; loops back

## 7. Phases (tutorial structure)

Each phase = one runnable game slice + one concept. The user does the hands-on task themselves before peeking at the reference.

### Phase 1: StateGraph + add_messages
- **Concept:** Build basic graph; messages flow through add_messages reducer
- **Game slice:** "You stand before a heavy door. It creaks slightly. Open it? (yes/no)"
- **Hands-on:** Build a 2-node graph yourself (input → response)
- **Self-check:** `python -m langgraph_adventure.phases.phase1_stategraph` with MOCK_LLM=1 prints the scene + your answer

### Phase 2: conditional_edges
- **Concept:** Graph branches based on state
- **Game slice:** "Go left into the forest, or right into the cave?" — two different scenes
- **Hands-on:** Add `add_conditional_edges` from input node to two scene nodes
- **Self-check:** Picking "left" vs "right" produces different output

### Phase 3: subgraph-as-node
- **Concept:** Sub-graph compiled separately, used as a node
- **Game slice:** First NPC ("Old Hermit") appears; their own graph runs to generate dialogue
- **Hands-on:** Build the NPC graph, compile separately, add as node
- **Self-check:** NPC dialogue appears in narration

### Phase 4: interrupt()
- **Concept:** Graph pauses, awaits human input, resumes via Command(resume=...)
- **Game slice:** Game pauses at menu, awaits your pick
- **Hands-on:** Wrap `present_scene` to call `interrupt()`
- **Self-check:** Graph pauses; CLI waits; your pick resumes it

### Phase 5: Command (explicit routing)
- **Concept:** `Command(goto=..., update=...)` for explicit node navigation
- **Game slice:** "Type a custom action" — LLM interprets which scene to route to
- **Hands-on:** Replace `add_conditional_edges` with `Command`-based routing
- **Self-check:** Custom actions navigate to correct scenes

### Phase 6: Send (map-reduce parallel)
- **Concept:** `Send` to fan out work across parallel branches
- **Game slice:** Two NPCs (Hermit + Wanderer) both react to your move in parallel
- **Hands-on:** Replace sequential NPC calls with `Send` map-reduce
- **Self-check:** Both NPC reactions appear, total time ≈ max time (not sum)

### Phase 7: astream_events (token streaming)
- **Concept:** Stream tokens from LLM as they're generated
- **Game slice:** Narration appears word-by-word in terminal
- **Hands-on:** Replace `graph.invoke(...)` with `graph.astream_events(..., version="v2")`
- **Self-check:** Narration streams token-by-token

### Phase 8: Store (long-term memory)
- **Concept:** Cross-thread key-value memory via `Store`
- **Game slice:** NPC remembers your name and last action from yesterday's session
- **Hands-on:** Add `npc_recall` and `npc_remember` calls in NPC graph
- **Self-check:** Resume yesterday's session; NPC greets you by name

### Phase 9: checkpointer + update_state (time travel)
- **Concept:** Save/restore state, fork checkpoints
- **Game slice:** "Undo last turn" button — rewinds to previous checkpoint
- **Hands-on:** Use `graph.get_state(config)` and `graph.update_state(config, values)`
- **Self-check:** Undo restores prior state; replay from there works

## 8. Error Handling

Each LLM-calling node wraps calls with retry + fallback:

- **LLM failures (rate limit, timeout, parse error):** exponential backoff (3 retries) → fallback to simpler prompt → if still failing, return Scene with empty NPCs and "the world is silent" description. Game continues. CLI exposes `/retry`.
- **Malformed LLM output:** Pydantic validation rejects → caught → retry with "format your response as: ..." appended. Max 2 retries.
- **interrupt timeout:** 5 min no input → CLI auto-saves and exits cleanly.
- **Store corruption:** memory read fails → treat as empty. Warn to stderr.
- **Checkpointer lock contention:** retry on SQLite busy. Persistent failure → clear CLI error.

All errors logged to `~/.langgraph_adventure/logs/<session_id>.log` (per-session log).

## 9. Testing

Each phase gets:
- **Demo function** (`demo()`) — runnable via `python -m langgraph_adventure.phases.phase{N}` — exercises the concept with MOCK_LLM=1, prints expected output.
- **No pytest framework** — same convention as `lg`. Each demo is ~30 lines, runs in <1s with MOCK_LLM=1.

Total: 9 demos + 1 full integration demo (phase 9 with all features).

## 9.5 Tutorial docs (alongside code)

Under `docs/phases/`:

```
docs/phases/
├── README.md               # overview + how to use this tutorial
├── phase1_stategraph.md    # concept explainer + reading links + hands-on task + reference
├── phase2_conditional.md
├── ...
└── phase9_time_travel.md
```

Each tutorial doc has the same structure:
1. **Concept** (1 paragraph: what it is, why it matters)
2. **Reading** (link to relevant LangGraph docs page)
3. **Hands-on task** (modify the cumulative code yourself; don't peek yet)
4. **Reference** (the working code after the task, with comments)
5. **Self-check** (how to verify you got it right)

## 10. Repository

Separate repo: `~/Documents/vscode/langgraph-adventure/` (clean git history showing phases, no temptation to mix with `lg`). Push to github.com/michaelm96/langgraph-adventure.

The `lg` repo (multi-client agent) and `langgraph-adventure` repo (this tutorial) are independent.

## 11. Acceptance Criteria

For each phase, "done" = demo passes, expected output appears, hands-on task completed before peeking at reference.

Overall: by phase 9, user can `git log` and see 9 phase commits, each shippable.

## 12. Open Questions

- **Theme constraint:** Phases 1–8 use a fixed theme ("noir detective"). Phase 9 lets player pick any theme (LLM-generated). Rationale: fixed theme keeps phases 1–8 reproducible; variable theme is itself the phase-9 lesson.
- **Visualization:** Studio exposure planned. Web UI explicitly out of scope.
- **Voice/audio:** Out of scope.
- **Multiplayer:** Out of scope (single-player only).
- **Cost:** each phase uses MiniMax-M3 default; phase 9 might benefit from cheaper model for NPC reactions. Defer until phase 9 implementation.