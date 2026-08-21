# Implementation Plan: LangGraph Tutorial (AI Text Adventure Engine)

**Date:** 2026-08-21
**Goal:** Build a tutorial project that teaches 9 LangGraph concepts by building an AI-driven text adventure engine. Each phase teaches exactly one concept through a runnable game slice.

**Spec:** `langgraph-adventure/docs/superpowers/specs/2026-08-21-langgraph-tutorial-design.md`
**Repo:** `/Users/michael/Documents/vscode/langgraph-adventure/`

## Architecture

Two LangGraph graphs (meta-graph + game-graph) + per-NPC sub-graphs. CLI runs the game-graph. Meta-graph generates scenes on demand. NPCs are sub-graphs called via `Send` for parallel reactions.

## Tech Stack

- **Python 3.11+**
- **LangGraph** (`langgraph>=0.2`, real library — `StateGraph`, `MessagesState`, `interrupt`, `Command`, `Send`, `astream_events`, `Store`, `SqliteSaver`, `update_state`)
- **LangChain Anthropic** (`langchain-anthropic`) — MiniMax-M3 uses Anthropic Messages API
- **MiniMax provider** (existing pattern from `lg` repo, base URL `https://api.minimax.io/anthropic`)
- **Pydantic** for Scene/Action/NPCReaction models
- **SQLite** (stdlib `sqlite3`) for checkpointer + Store
- **Typer** for CLI
- **No pytest framework** — per-phase demo functions only, MOCK_LLM=1 for fast tests

## Global Constraints

1. **Real LangGraph library throughout.** No hand-rolled graph machinery. Use `StateGraph`, `MessagesState`, `ToolNode`, `SqliteSaver`, `Store`, `interrupt`, `Command`, `Send`, `astream_events`, `update_state`.
2. **Each phase ships runnable.** Demo function passes under MOCK_LLM=1.
3. **One concept per phase.** Don't sneak concepts ahead of their phase.
4. **Cumulative code matches phase 9.** `meta_graph.py` / `game_graph.py` / `npc_graph.py` always reflect the full build.
5. **Pydantic models in `state.py`.** Used as `Scene` / `Action` / `NPCReaction` for clean serialization.
6. **Studio exposure.** `langgraph.json` exposes all 3 graphs (meta-graph, game-graph, NPC subgraph) for visual debugging.
7. **Demo convention.** `python -m langgraph_adventure.phases.phase{N}` runs the demo. MOCK_LLM=1 for fast tests.
8. **Tutorial docs.** `docs/phases/phase{N}.md` accompanies each phase.

## File Structure

```
langgraph-adventure/
├── pyproject.toml
├── README.md
├── .gitignore
├── langgraph.json
├── docs/
│   └── phases/
│       ├── README.md
│       ├── phase1_stategraph.md
│       ├── phase2_conditional.md
│       ├── phase3_subgraph.md
│       ├── phase4_interrupt.md
│       ├── phase5_command.md
│       ├── phase6_send.md
│       ├── phase7_stream.md
│       ├── phase8_store.md
│       └── phase9_time_travel.md
└── src/langgraph_adventure/
    ├── __init__.py
    ├── llm.py              # MiniMax provider (Anthropic Messages API)
    ├── state.py            # Scene, Action, NPCReaction Pydantic models
    ├── meta_graph.py       # build_meta_graph() — 2 nodes
    ├── game_graph.py       # build_game_graph() — 7 nodes
    ├── npc_graph.py        # build_npc_graph(persona) — 3 nodes
    ├── store.py            # npc_recall, npc_remember wrappers
    ├── persistence.py      # SqliteSaver + Store setup
    ├── cli/
    │   ├── __init__.py
    │   └── play.py         # typer app
    └── phases/
        ├── __init__.py
        ├── phase1_stategraph.py
        ├── phase2_conditional.py
        ├── phase3_subgraph.py
        ├── phase4_interrupt.py
        ├── phase5_command.py
        ├── phase6_send.py
        ├── phase7_stream.py
        ├── phase8_store.py
        └── phase9_time_travel.py
```

---

## Phase 0: Project Scaffolding

### Task 0.1 — Initialize repo + pyproject.toml + .gitignore
**Files (Create):**
- `pyproject.toml`
- `.gitignore`

**Interfaces:**
- pyproject.toml declares project metadata, langgraph>=0.2, langchain-anthropic, typer, pydantic, [dev] extras with langgraph-cli[inmem]>=0.1, [project.scripts] `lg-adv = "langgraph_adventure.cli.play:app"`, package-data includes langgraph.json.
- .gitignore includes .env, __pycache__, *.egg-info, .langgraph_api/, *.db.

**Steps:**
1. Write `pyproject.toml` matching `lg` repo's structure but with project name `langgraph-adventure`, version `0.1.0`, scripts `lg-adv`.
2. Write `.gitignore` (Python defaults + Studio artifacts + DB files).
4. `pip install -e ".[dev]"`.

### Task 0.2 — langgraph.json + README + package skeleton
**Files (Create):**
- `langgraph.json`
- `README.md`
- `src/langgraph_adventure/__init__.py`
- `src/langgraph_adventure/cli/__init__.py`

**Interfaces:**
- `langgraph.json`: 3 graphs — `meta`, `game`, `npc` — pointing at `build_meta_graph()`, `build_game_graph()`, `build_npc_graph()` in their respective modules.
- README: project intro + 9-phase roadmap + how to run demos + Studio URL.

**Steps:**
1. Write `langgraph.json` with 3 graph definitions.
2. Write minimal `README.md` (forward-references to docs/phases/README.md once it's written in Phase 1).
3. Write empty `__init__.py` files for `langgraph_adventure` and `langgraph_adventure.cli`.
4. `python -c "import langgraph_adventure"` succeeds (empty package imports clean).

### Task 0.3 — llm.py (MiniMax provider)
**Files (Create):**
- `src/langgraph_adventure/llm.py`

**Interfaces:**
- `resolve_model(model_str: str) -> BaseChatModel` — parses `"provider/name"` strings, dispatches to ChatAnthropic for `minimax` (base URL `https://api.minimax.io/anthropic`, env `MINIMAX_API_KEY`), raises `ValueError` for unknown providers.
- `MOCK_LLM` env var flag (module-level `_MOCK_ENABLED` boolean) — when set, returns a `_MockChatModel` whose `invoke`/`astream` return canned outputs and whose `bind_tools` is a no-op.
- Reads config from `~/.langgraph_adventure/config.toml` (key `minimax_api_key`) with env fallback.

**Steps:**
1. Copy pattern from `~/Documents/vscode/langgraph/src/langgraph_agent/agents/llm.py` (specifically the `_resolve_model_string` function). Replace `path` references with this project's structure.
2. Add `_MockChatModel` class: inherits `BaseChatModel`, `invoke(messages) -> AIMessage(content="MOCK_RESPONSE")`, `astream(messages) -> AsyncIterator[AIMessageChunk]` yields single chunk. `bind_tools(*args, **kwargs) -> self` (no-op).
3. `from langgraph_adventure.llm import resolve_model; llm = resolve_model("minimax/MiniMax-M3"); print(type(llm).__name__)` prints `ChatAnthropic`.

---

## Phase 1: StateGraph + add_messages (basic turn loop)

**Concept:** Build basic graph; messages flow through add_messages reducer.
**Game slice:** "You stand before a heavy door. It creaks slightly. Open it? (yes/no)"

### Task 1.1 — state.py (Pydantic models)
**Files (Create):**
- `src/langgraph_adventure/state.py`

**Interfaces:**
- `class Scene(BaseModel)`: fields `scene_id: str`, `description: str` (3-5 sentences, second-person narration), `npcs: list[str]` (names of NPCs in scene, empty list for phase 1-2), `actions: list[Action]`.
- `class Action(BaseModel)`: fields `id: str` (e.g. "A", "B", "C"), `label: str` (short, 2-5 words), `next_state: str` ("continue" / "end" / "branch_left" / "branch_right" for phase 2+).
- `class NPCReaction(BaseModel)`: fields `npc_name: str`, `dialogue: str`, `memory_update: str | None`.
- `class MetaState(TypedDict)`: `theme: str`, `world_seed: str`, `history: list[Scene]`, `current_request: str`.

**Steps:**
1. Define `Scene`, `Action`, `NPCReaction` Pydantic models.
2. Define `MetaState` TypedDict with `total=False`.
3. `python -c "from langgraph_adventure.state import Scene, Action; Scene(description='test', actions=[Action(id='A', label='Open door', next_state='continue')])"` succeeds.

### Task 1.2 — meta_graph.py (theme_intake → scene_generator)
**Files (Create):**
- `src/langgraph_adventure/meta_graph.py`

**Interfaces:**
- `def build_meta_graph() -> CompiledStateGraph`: 2-node graph. Node 1 `theme_intake(state: MetaState) -> dict` returns `{"history": [Scene(scene_id="opening", description=f"...", npcs=[], actions=[Action(id="A", label="Open the door", next_state="continue")])]}`. Node 2 `scene_generator(state) -> dict` no-op for phase 1 (returns empty dict).
- State has `theme: str` (default "noir detective"), `history: list[Scene]` with `add` reducer (using `Annotated[list[Scene], operator.add]`).

**Steps:**
1. Define `MetaState` TypedDict with `Annotated[list[Scene], operator.add]` for `history`.
2. Define `theme_intake` node: hardcodes an opening Scene for the "noir detective" theme. Uses `from langgraph_adventure.llm import resolve_model; llm = resolve_model(...)` if MOCK_LLM unset, otherwise generates Scene from a hardcoded template.
3. Define `scene_generator` node: returns empty dict for now.
4. Build graph: `builder = StateGraph(MetaState); builder.add_node("theme_intake", theme_intake); builder.add_node("scene_generator", scene_generator); builder.add_edge(START, "theme_intake"); builder.add_edge("theme_intake", END)`.
5. `graph = builder.compile()`.
6. `python -c "from langgraph_adventure.meta_graph import build_meta_graph; g = build_meta_graph(); result = g.invoke({'theme': 'noir detective', 'world_seed': 'test', 'history': []}); print(len(result['history']), 'scenes')"` prints `1 scenes`.

### Task 1.3 — phase1_stategraph.py (demo + tutorial doc)
**Files (Create):**
- `src/langgraph_adventure/phases/__init__.py`
- `src/langgraph_adventure/phases/phase1_stategraph.py`
- `docs/phases/README.md`
- `docs/phases/phase1_stategraph.md`

**Interfaces:**
- `def demo() -> None`: builds meta_graph, invokes with theme="noir detective", prints `scene.description` and `scene.actions` to stdout. Asserts `len(history) == 1` and `len(scene.actions) >= 2`.
- Phase 1 demo is identical to the cumulative code (since meta-graph is the only graph so far).
- `docs/phases/README.md`: 5-section overview (concept, reading, hands-on, reference, self-check) explaining the tutorial structure.
- `docs/phases/phase1_stategraph.md`: 5-section doc for phase 1. Reading links to LangGraph `StateGraph` docs. Hands-on task: user builds 2-node graph themselves, runs demo.

**Steps:**
1. Write `phases/__init__.py` (empty).
2. Write `phases/phase1_stategraph.py` with `demo()` function and `if __name__ == "__main__": demo()`.
3. Write `docs/phases/README.md` explaining tutorial structure.
4. Write `docs/phases/phase1_stategraph.md` with all 5 sections (concept explainer, reading links, hands-on task, reference code, self-check).
5. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase1_stategraph` prints the opening scene + 2+ actions.
6. Commit: `feat(phase1): stategraph + add_messages + opening scene`.

---

## Phase 2: conditional_edges (branching scenes)

**Concept:** `add_conditional_edges` routes based on state.
**Game slice:** "Go left into the forest, or right into the cave?" — different scenes per choice.

### Task 2.1 — scene_generator with conditional branches
**Files (Modify):**
- `src/langgraph_adventure/meta_graph.py`

**Interfaces:**
- `scene_generator(state) -> dict`: reads `state["current_request"]` (default "continue"), looks up from a hardcoded dict of scenes, returns `{"history": [Scene(...)]}` matching the branch.
- Conditional edge: `builder.add_conditional_edges("theme_intake", route_request, {"continue": "scene_generator", "branch_left": "scene_generator", "branch_right": "scene_generator"})`. The `route_request` function returns "continue" / "branch_left" / "branch_right" from `state["current_request"]`.

**Steps:**
1. Define 3 hardcoded scenes: opening (door), left_path (forest), right_path (cave). Each Scene has 2+ actions with `next_state` pointing to next branch.
3. Update `theme_intake` to also set `current_request` to "continue" in the returned dict.
4. Update `scene_generator` to return Scene matching `state["current_request"]`. Falls back to opening if request unknown.
5. Add conditional edge with `route_request` function.
6. Test: invoke graph, then invoke again with `current_request="branch_left"` injected, confirm different scene in history.

### Task 2.2 — phase2_conditional.py + phase2 doc
**Files (Create):**
- `src/langgraph_adventure/phases/phase2_conditional.py`
- `docs/phases/phase2_conditional.md`

**Interfaces:**
- `phase2_conditional.demo()`: invokes graph twice (once with default, once with `branch_left`), prints both scenes, asserts `history[-2].description != history[-1].description`.

**Steps:**
1. Write `phase2_conditional.py` mirroring phase1 pattern but with 2 invokes.
2. Write `docs/phases/phase2_conditional.md` (5 sections: concept=conditional_edges, reading=LangGraph docs on conditional edges, hands-on task, reference code, self-check).
3. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase2_conditional` runs both invokes and shows different scenes.
4. Commit: `feat(phase2): conditional_edges for scene branching`.

---

## Phase 3: subgraph-as-node (NPC appears)

**Concept:** Sub-graph compiled separately, used as a node.
**Game slice:** First NPC ("Old Hermit") appears; their own graph runs to generate dialogue.

### Task 3.1 — npc_graph.py (per-NPC subgraph)
**Files (Create):**
- `src/langgraph_adventure/npc_graph.py`

**Interfaces:**
- `class NPCState(TypedDict)`: `persona: str`, `situation: str`, `dialogue: str`.
- `def build_npc_graph(persona: str) -> CompiledStateGraph`: 3-node graph — `perceive_situation` (sets state from persona + situation arg), `decide_action` (LLM call with persona + situation → action decision), `speak` (formats dialogue). Compiles to sub-graph. For phase 3, `decide_action` returns canned dialogue ("I have nothing to say to you yet." for MOCK, real LLM later).

**Steps:**
1. Define `NPCState` TypedDict.
2. Define 3 node functions.
3. `build_npc_graph(persona)`: builder = StateGraph(NPCState); add nodes; edges perceive → decide → speak → END. Compile. Return compiled graph.
4. Test: `from langgraph_adventure.npc_graph import build_npc_graph; g = build_npc_graph("Old Hermit"); result = g.invoke({"persona": "Old Hermit", "situation": "A traveler approaches"}); print(result["dialogue"])` prints canned line.

### Task 3.2 — Integrate NPC into meta-graph
**Files (Modify):**
- `src/langgraph_adventure/meta_graph.py`

**Interfaces:**
- Opening Scene (and left/right scenes) now include `npcs: ["Old Hermit"]` (or different NPC per branch).
- Add node `invoke_npc` to meta-graph: receives Scene with NPCs, calls `build_npc_graph(persona).invoke(...)` for each NPC, collects dialogues into `{"npc_dialogues": {persona: dialogue}}`.
- Conditional edge from `scene_generator` to `invoke_npc` if NPCs present, else END.

**Steps:**
1. Update Scene templates to include `npcs=["Old Hermit"]` in opening scene (and phase 2 branches can have other NPCs).
2. Add `invoke_npc` node.
3. Add conditional edge from `scene_generator`: route to `invoke_npc` if `state["history"][-1].npcs`, else END.
4. Test: invoke graph, confirm `npc_dialogues` in result contains Old Hermit's canned line.

### Task 3.3 — phase3_subgraph.py + phase3 doc
**Files (Create):**
- `src/langgraph_adventure/phases/phase3_subgraph.py`
- `docs/phases/phase3_subgraph.md`

**Steps:**
1. Write `phase3_subgraph.py` mirroring phase2 but printing NPC dialogues too.
2. Write `docs/phases/phase3_subgraph.md` (5 sections).
3. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase3_subgraph` shows scenes + NPC dialogues.
4. Commit: `feat(phase3): npc subgraph + invoke_npc node`.

---

## Phase 4: interrupt() (game pauses)

**Concept:** Graph pauses, awaits human input, resumes via Command(resume=...).
**Game slice:** Game pauses at menu, awaits your pick.

### Task 4.1 — game_graph.py (present_scene + interrupt_for_choice)
**Files (Create):**
- `src/langgraph_adventure/game_graph.py`

**Interfaces:**
- `class GameState(MessagesState)`: extends `MessagesState` (which has `messages: Annotated[list[AnyMessage], add_messages]`); adds `current_scene: Scene | None`, `chosen_action: Action | None`, `npc_dialogues: dict[str, str]`.
- `def build_game_graph() -> CompiledStateGraph`: 7 nodes (but only 2 used in phase 4):
  - `present_scene(state) -> dict`: streams narration (just `print` for phase 4, astream_events comes in phase 7), returns empty dict.
  - `interrupt_for_choice(state) -> dict`: calls `interrupt({"actions": state["current_scene"].actions, "scene_id": state["current_scene"].scene_id})`. Graph pauses.
- Graph: `builder = StateGraph(GameState); add_node("present_scene", present_scene); add_node("interrupt_for_choice", interrupt_for_choice); add_edge(START, "present_scene"); add_edge("present_scene", "interrupt_for_choice"); add_edge("interrupt_for_choice", END)` (other nodes added in later phases).

**Steps:**
1. Define `GameState` extending `MessagesState`.
2. Define `present_scene` (prints scene description + action menu, returns empty dict).
3. Define `interrupt_for_choice` calling `from langgraph import interrupt; interrupt({...})`.
4. Build graph with 2 nodes + edges.
5. Test: `g.invoke({"messages": [], "current_scene": Scene(...)})` raises GraphInterrupt (expected).

### Task 4.2 — cli/play.py (REPL with interrupt handling)
**Files (Create):**
- `src/langgraph_adventure/cli/play.py`

**Interfaces:**
- `app = typer.Typer()`.
- Command `play(theme: str = "noir detective")`: opens graph, gets opening Scene from meta-graph, enters REPL loop.
- REPL loop: invoke game-graph, catches `GraphInterrupt`, prints action menu, reads input, calls `graph.invoke(Command(resume=user_choice))`. Loop until action with `next_state="end"`.

**Steps:**
1. Define `app = typer.Typer()`.
2. Define `play(theme: str)`:
   - `meta = build_meta_graph(); meta_result = meta.invoke({"theme": theme})` → get opening Scene.
   - `game = build_game_graph().compile(checkpointer=SqliteSaver.from_conn_string("~/.langgraph_adventure/game.db"))`.
   - `config = {"configurable": {"thread_id": str(uuid.uuid4())}}`.
   - Loop: try `game.invoke({"messages": [], "current_scene": meta_result["history"][-1]}, config)`. On `GraphInterrupt` (from `langgraph.errors`), show menu, read input, `game.invoke(Command(resume=input), config)`. Break when action.next_state == "end".
3. `if __name__ == "__main__": app()`.
4. Test: `lg-adv play "noir detective"` opens REPL, shows scene + menu.

### Task 4.3 — phase4_interrupt.py + phase4 doc
**Files (Create):**
- `src/langgraph_adventure/persistence.py` (empty for now, SqliteSaver added in phase 9)
- `src/langgraph_adventure/phases/phase4_interrupt.py`
- `docs/phases/phase4_interrupt.md`

**Steps:**
1. Write `persistence.py` with placeholder (just `SqliteSaver` import works).
2. Write `phase4_interrupt.py` with `demo()` that:
   - Builds game-graph WITHOUT checkpointer (for testability).
   - Invokes with a fake Scene, catches `GraphInterrupt`.
   - Asserts interrupt payload contains `actions` and `scene_id`.
   - Calls `graph.invoke(Command(resume=Action(id="A")))`, confirms `chosen_action` in state.
3. Write `docs/phases/phase4_interrupt.md` (5 sections).
4. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase4_interrupt` runs demo, shows interrupt + resume flow.
5. Commit: `feat(phase4): game-graph with interrupt() + REPL`.

---

## Phase 5: Command (explicit routing)

**Concept:** `Command(goto=..., update=...)` for explicit node navigation.
**Game slice:** "Type a custom action" — LLM routes it.

### Task 5.1 — route_choice node with Command
**Files (Modify):**
- `src/langgraph_adventure/game_graph.py`

**Interfaces:**
- New node `route_choice(state) -> Command`: reads `state["chosen_action"]`, returns `Command(goto="react_npcs" if state["chosen_action"].next_state != "end" else END, update={"chosen_action": state["chosen_action"]})`.
- Add edge: `builder.add_edge("interrupt_for_choice", "route_choice")`.
- `react_npcs` and `next_scene` are stub nodes for phase 5 (return empty dict, but graph still terminates cleanly).

**Steps:**
1. Add `route_choice` node returning `Command(goto=..., update=...)`.
2. Add stub `react_npcs`, `next_scene` nodes (return empty dict).
3. Update edges: `interrupt_for_choice → route_choice → react_npcs → next_scene → END`.
4. Test: invoke with chosen_action pointing to continue, confirm flow reaches next_scene; with end, confirms termination at END.

### Task 5.2 — Custom action routing (LLM interprets custom input)
**Files (Modify):**
- `src/langgraph_adventure/game_graph.py`

**Interfaces:**
- In `interrupt_for_choice`, expose "Type your own action" option (action with id="custom", label="(type your own action)").
- When player picks custom, CLI prompts for free text, builds `Action(id="custom_1", label=<text>, next_state=<LLM-determined>)` where LLM routes text to one of {"continue", "branch_left", "branch_right", "end"}.
- Add node `interpret_custom_action(state) -> dict`: LLM call with `state["chosen_action"].label` + theme, returns `{"chosen_action": Action(..., next_state=<routed>)}`. Update `route_choice` to call this first if `chosen_action.id.startswith("custom")`.

**Steps:**
1. Update `interrupt_for_choice` payload: add Action(id="custom", label="(type your own action)") to menu.
2. Add `interpret_custom_action` node (LLM call to route).
3. Update `route_choice`: if `chosen_action.id.startswith("custom")`, `goto="interpret_custom_action"`, else `goto="react_npcs"` or END as before.
4. Update edges: `route_choice → interpret_custom_action → react_npcs → next_scene → END`.
5. Test: simulate custom action, confirm routing works (MOCK returns first available next_state).

### Task 5.3 — phase5_command.py + phase5 doc
**Files (Create):**
- `src/langgraph_adventure/phases/phase5_command.py`
- `docs/phases/phase5_command.md`

**Steps:**
1. Write `phase5_command.py` with `demo()` exercising Command routing (continuation, end, custom → routed).
2. Write `docs/phases/phase5_command.md` (5 sections).
3. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase5_command` runs demo.
4. Commit: `feat(phase5): Command-based routing + custom action LLM interpreter`.

---

## Phase 6: Send (parallel NPCs)

**Concept:** `Send` to fan out work across parallel branches.
**Game slice:** Two NPCs (Hermit + Wanderer) both react to your move in parallel.

### Task 6.1 — react_npcs with Send fanout
**Files (Modify):**
- `src/langgraph_adventure/game_graph.py`

**Interfaces:**
- Replace stub `react_npcs` with real implementation: for each NPC in `state["current_scene"].npcs`, build `Send(npc_id, build_npc_graph(persona).invoke({"persona": npc_name, "situation": state["current_scene"].description}))`. Use `from langgraph.types import Send`.
- Update GameState to include `parallel_npcs: list[Send]` if needed (Send is a special LangGraph type).

**Steps:**
1. Import `from langgraph.types import Send`.
2. Implement `react_npcs(state) -> list[Send]`: returns `[(Send(npc, build_npc_graph(npc).invoke({...})))]` per NPC.
3. Update `add_node` calls: `builder.add_node("react_npcs", react_npcs)`. LangGraph automatically handles list-of-Send return as fanout.
4. Test: invoke with Scene containing 2 NPCs, confirm both NPC dialogues appear in `state["npc_dialogues"]`.

### Task 6.2 — merge_reactions node
**Files (Modify):**
- `src/langgraph_adventure/game_graph.py`

**Interfaces:**
- Add `merge_reactions(state) -> dict`: reads `state["npc_dialogues"]` (now populated by Send-fanned NPC graphs), formats into `{"messages": [AIMessage(content=f"{npc}: {dialogue}")]}`.
- Update edges: `react_npcs → merge_reactions → next_scene → END`.

**Steps:**
1. Define `merge_reactions` node.
2. Update edges.
3. Test: invoke with 2 NPCs, confirm both reactions appear in `state["messages"]`.

### Task 6.3 — phase6_send.py + phase6 doc
**Files (Create):**
- `src/langgraph_adventure/phases/phase6_send.py`
- `docs/phases/phase6_send.md`

**Steps:**
1. Write `phase6_send.py` with `demo()` showing parallel NPC reactions (timing: assert max_time, not sum).
2. Write `docs/phases/phase6_send.md` (5 sections).
3. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase6_send` runs demo, asserts parallel execution.
4. Commit: `feat(phase6): Send fanout for parallel NPC reactions`.

---

## Phase 7: astream_events (token streaming)

**Concept:** Stream tokens from LLM as they're generated.
**Game slice:** Narration appears word-by-word in terminal.

### Task 7.1 — Convert CLI to astream_events
**Files (Modify):**
- `src/langgraph_adventure/cli/play.py`

**Interfaces:**
- Replace `graph.invoke(...)` with `graph.astream_events(..., version="v2")` in REPL.
- Filter for `event["event"] == "on_chat_model_stream"`, extract `event["data"]["chunk"].content` (token-by-token), print without newline (flush=True).
- For phase 7, apply streaming only in `present_scene` node narration (narrate descriptions as they stream).

**Steps:**
1. Update REPL loop to use `astream_events`.
2. Add token-printing logic.
3. Test: `lg-adv play "noir detective"` shows narration streaming token-by-token.

### Task 7.2 — phase7_stream.py + phase7 doc
**Files (Create):**
- `src/langgraph_adventure/phases/phase7_stream.py`
- `docs/phases/phase7_stream.md`

**Steps:**
1. Write `phase7_stream.py` with `demo()` showing streaming output (capture tokens, assert multiple chunks received).
2. Write `docs/phases/phase7_stream.md` (5 sections).
3. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase7_stream` runs demo.
4. Commit: `feat(phase7): astream_events for token streaming narration`.

---

## Phase 8: Store (long-term memory)

**Concept:** Cross-thread key-value memory via `Store`.
**Game slice:** NPC remembers your name and last action from yesterday's session.

### Task 8.1 — store.py wrappers
**Files (Create):**
- `src/langgraph_adventure/store.py`

**Interfaces:**
- `from langgraph.store.memory import InMemoryStore` (or SqliteStore from langgraph for persistence — chose InMemoryStore for tutorial simplicity, document the upgrade path).
- `def get_store() -> BaseStore`: returns singleton InMemoryStore (or fresh one for tests).
- `def npc_recall(store, npc_name: str, key: str) -> str | None`: `store.get(("npc_memories", npc_name), key)`.
- `def npc_remember(store, npc_name: str, key: str, value: str) -> None`: `store.put(("npc_memories", npc_name), key, value)`.

**Steps:**
1. Define `get_store()`.
2. Define `npc_recall` / `npc_remember`.
3. Test: write memory, read back, confirm value matches.

### Task 8.2 — NPC graph reads/writes memory
**Files (Modify):**
- `src/langgraph_adventure/npc_graph.py`

**Interfaces:**
- `decide_action` reads player's name from store: `store.get(("npc_memories", persona), "player_name")`.
- If player_name known, dialogue includes greeting ("Ah, {player_name}, we meet again.").
- After dialogue generated, `speak` writes back to store: `store.put(("npc_memories", persona), "last_interaction", dialogue)`.

**Steps:**
1. Update `decide_action` to read player_name from store.
2. Update `speak` to write dialogue back to store.
3. Pass store into NPC graph invocation (use `config={"configurable": ..., "store": store}`).
4. Test: invoke NPC with name "Michael" in store, dialogue greets him; invoke again, dialogue remembers last interaction.

### Task 8.3 — persist node in game-graph
**Files (Modify):**
- `src/langgraph_adventure/game_graph.py`

**Interfaces:**
- Add `persist(state) -> dict`: writes all NPC dialogues from current turn to store via `npc_remember`.
- Update edges: `merge_reactions → persist → next_scene → END`.

**Steps:**
1. Define `persist` node.
2. Update edges.
3. Test: invoke game-graph, confirm store now contains NPC memories.

### Task 8.4 — phase8_store.py + phase8 doc
**Files (Create):**
- `src/langgraph_adventure/phases/phase8_store.py`
- `docs/phases/phase8_store.md`

**Steps:**
1. Write `phase8_store.py` with `demo()` exercising memory (write, restart "session", read back).
2. Write `docs/phases/phase8_store.md` (5 sections).
3. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase8_store` runs demo.
4. Commit: `feat(phase8): Store for long-term NPC memory`.

---

## Phase 9: checkpointer + update_state (time travel)

**Concept:** Save/restore state, fork checkpoints.
**Game slice:** "Undo last turn" button — rewinds to previous checkpoint.

### Task 9.1 — SqliteSaver integration
**Files (Modify):**
- `src/langgraph_adventure/persistence.py`

**Interfaces:**
- `def get_checkpointer() -> SqliteSaver`: returns `SqliteSaver.from_conn_string("~/.langgraph_adventure/game.db")` (or InMemorySaver for tests).
- `def get_store() -> BaseStore`: returns InMemoryStore for tutorial (could be Postgres-backed in production).

**Steps:**
1. Implement `get_checkpointer`.
2. Update `cli/play.py` to use `get_checkpointer()` instead of inline SqliteSaver.
3. Update phase 4 demo to use `InMemorySaver` for testability.

### Task 9.2 — Undo last turn
**Files (Modify):**
- `src/langgraph_adventure/cli/play.py`

**Interfaces:**
- New REPL command `/undo`: calls `graph.get_state(config)`, gets previous checkpoint, calls `graph.update_state(config, values=previous.values)`, restores prior state.
- Print "Turn undone — you're back at: <previous scene description>".

**Steps:**
1. Add `/undo` handler in REPL loop.
2. Update `graph.update_state` with previous state's values.
3. Test: play 2 turns, `/undo`, confirm scene description matches turn 1.

### Task 9.3 — persistence.py polish + phase9 doc
**Files (Modify):**
- `src/langgraph_adventure/persistence.py`
- `src/langgraph_adventure/cli/play.py`

**Interfaces:**
- `persistence.py`: typed `get_checkpointer()` with docstring noting thread_id isolation.
- `cli/play.py`: add `/fork` command (bonus) — fork state into new thread for alternate exploration.

**Steps:**
1. Polish `persistence.py` with type hints + docstring.
2. Add `/fork` command (optional bonus).
3. Update README with full command list.

### Task 9.4 — phase9_time_travel.py + phase9 doc
**Files (Create):**
- `src/langgraph_adventure/phases/phase9_time_travel.py`
- `docs/phases/phase9_time_travel.md`

**Steps:**
1. Write `phase9_time_travel.py` with `demo()` exercising checkpointer + update_state for undo.
2. Write `docs/phases/phase9_time_travel.md` (5 sections).
3. `MOCK_LLM=1 python -m langgraph_adventure.phases.phase9_time_travel` runs demo.
4. Commit: `feat(phase9): checkpointer + undo + time travel`.

---

## Phase 10: Final Integration

### Task 10.1 — Update README + sanity checks
**Files (Modify):**
- `README.md`

**Interfaces:**
- Full README: intro + 9-phase roadmap + how to run demos + Studio URL + contributing guide.
- Sanity: `MOCK_LLM=1 python -m langgraph_adventure.phases.phase{1..9}` all pass.

**Steps:**
1. Polish README.
2. Run all 9 demos, confirm all pass.
3. Run `python -m langgraph_cli dev` to verify Studio exposure.
4. Commit: `docs: full README + sanity check`.

### Task 10.2 — git push to github
**Steps:**
1. `git remote add origin https://github.com/michaelm96/langgraph-adventure.git`.
2. `git push -u origin main`.

---

## Self-Review

### Spec coverage
- Spec §4.1 (meta-graph): covered by Phase 1 + 2.
- Spec §4.2 (game-graph): covered by Phase 4-9.
- Spec §4.3 (NPC graph): covered by Phase 3.
- Spec §4.4 (state): covered by Phase 1 + 4.
- Spec §5 (file layout): matches plan structure.
- Spec §6 (data flow): covered by Phases 4-9.
- Spec §7 (9 phases + concepts): all 9 phases planned.
- Spec §8 (error handling): TODO — error handling skipped in current plan for tutorial simplicity. Add if time.
- Spec §9 (testing): per-phase demo convention enforced.
- Spec §9.5 (tutorial docs): per-phase doc writing included in each phase.
- Spec §10 (repo): separate repo + GitHub push in Task 0.1 + 10.2.

### Placeholder scan
- Task 5.2 step 5: "Test: simulate custom action, confirm routing works (MOCK returns first available next_state)." — concrete.
- All `if __name__ == "__main__"` and demo functions are explicit.
- No TBDs in the plan.

### Type consistency
- `MetaState` (TypedDict) declared once in state.py, imported by meta_graph.py.
- `GameState` (extends MessagesState) declared once in game_graph.py.
- `NPCState` (TypedDict) declared once in npc_graph.py.
- `Scene` / `Action` / `NPCReaction` (Pydantic) declared in state.py, used everywhere.

### Ambiguity check
- "Cumulative code matches phase 9" — clarified in Global Constraint #4: `meta_graph.py` / `game_graph.py` / `npc_graph.py` always reflect full build; phases/ directory has per-phase reference demos.
- Tutorial docs structure (5 sections) — fixed in spec §9.5.

## Execution Handoff

Recommend **subagent-driven** execution: 9 phases, each phase 3-5 tasks, sub-agents implement + review per task. Plan file (`docs/superpowers/plans/2026-08-21-langgraph-tutorial.md`) is the source of truth. Worker dispatch template uses `task-brief` script from `~/.pi/agent/git/github.com/obra/superpowers/skills/subagent-driven-development/scripts/`.

Inline execution also viable but takes longer. Defer to user.