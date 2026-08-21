# Phase 4 — Human-in-the-Loop via `interrupt()`
Phase 3 nested a subgraph inside a node. Phase 4 stops the graph and waits for a human — the human-in-the-loop pattern. It's also the foundation for tool confirmation, approval workflows, and any place an LLM agent must wait on a person.

## 1. Concept
`interrupt(payload)` raises `GraphInterrupt`, which LangGraph catches and persists via the checkpointer. The graph pauses at that node — state is frozen, `g.invoke()` returns control. To resume, call `g.invoke(Command(resume=value), config)`; the value is handed back as the return of `interrupt(...)`, and execution continues.

Two important properties:

- **The checkpointer is mandatory.** Without one, the graph cannot resume — it has no memory of where it stopped. Phase 4.2 uses `SqliteSaver` for cross-process REPLs; the 4.3 demo uses `InMemorySaver` to keep everything in one process.
- **LangGraph 1.2.x suppresses `GraphInterrupt` at the root-graph level.** Instead of an exception escaping, `invoke()` returns normally with `__interrupt__` populated. You read the payload off `result["__interrupt__"][0].value`, render a menu, then call `invoke(Command(resume=...), config)` to continue.

## 2. Reading
- LangGraph Human-in-the-Loop: <https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/>
Read the **Pause using `interrupt`** section. Focus on (a) `interrupt(value)` vs `Command(resume=value)`, (b) why a checkpointer is required, (c) what happens to state across the pause.

## 3. Hands-on
Build `game_graph.py` with two nodes:

1. `present_scene(state)` — prints scene narration + action menu (Phase 4 uses `print()`; Phase 7 swaps for token streaming via `astream_events`).
2. `interrupt_for_choice(state)` — calls `interrupt({"scene_id": ..., "actions": [...]})` and converts the returned choice into `{"chosen_action": Action(id=..., ...)}`.

Wire `START → present_scene → interrupt_for_choice → END` and expose `build_game_graph()` so callers `.compile(checkpointer=...)`. Then build a CLI REPL:

```python
while True:
    result = g.invoke(state, config)
    if "__interrupt__" not in result:
        break
    actions = result["__interrupt__"][0].value["actions"]
    choice = input(f"choose {[a['id'] for a in actions]}: ")
    state = Command(resume=choice)
```

Each iteration either consumes an interrupt (resume) or sees the graph finish (`break`).

## 4. Reference
Working code: `src/langgraph_adventure/phases/phase4_interrupt.py`. Demo: invoke with `InMemorySaver`, observe `__interrupt__`, resume with `Command(resume="A")`, assert `chosen_action.id == "A"`. See file for full 30-line example.

Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase4_interrupt
```

You should see three steps: first invoke returns `__interrupt__`; resuming with `"A"` sets `chosen_action.id == "A"`; a fresh thread resumed with `"B"` sets `chosen_action.id == "B"`. The CLI REPL (`cli/play.py`) wraps the same pattern in a `while True` loop with `input()`.

## 5. Self-check
1. What's the difference between `interrupt(value)` (inside the node) and `Command(resume=value)` (in the caller)?
2. Why does langgraph 1.2.x suppress `GraphInterrupt` at the root-graph level, and where does the interrupt payload surface instead?
3. What does the checkpointer do during an interrupt, and what would break if you compiled without one?

If any answer felt shaky, re-read the **Pause using `interrupt`** section and trace one pause/resume cycle by hand before moving on.
