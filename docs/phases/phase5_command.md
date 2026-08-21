# Phase 5 — Explicit Routing with `Command`
Phase 4 stopped the graph and waited for a player choice. Phase 5 routes that choice to the right next node — explicitly, in code. It's the bridge from "the player picked something" to "the graph knows what to do with it."

## 1. Concept
`Command(goto=..., update=...)` is a node return value that does two things at once: tells the graph which node to run next **and** what state to apply. Instead of relying on declarative edges (which are static, decided at build time), a `Command` lets a node decide at runtime — the same node can route to `END` on one input and to a sub-graph on another.

The pattern looks like:

```python
def route_choice(state) -> Command:
    if state["chosen_action"].next_state == "end":
        return Command(goto=END, update={})
    if state["chosen_action"].next_state == "custom":
        return Command(goto="interpret_custom_action", update={"chosen_action": state["chosen_action"]})
    return Command(goto="react_npcs", update={"chosen_action": state["chosen_action"]})
```

The `update` half replaces the standard "return a dict from the node" pattern — and it runs in the same atomic step as the goto, so there's no half-applied state if anything goes wrong downstream.

## 2. Reading
- LangGraph `Command`: <https://langchain-ai.github.io/langgraph/concepts/low_level/#command>
Focus on (a) when `Command(goto=...)` overrides declarative edges, (b) `update=` semantics vs returning a state dict, (c) how `Command` combines routing and state updates in one step.

## 3. Hands-on
Add `route_choice` between `interrupt_for_choice` and the rest of the graph. It returns `Command(goto=..., update=...)` based on `chosen_action.next_state`:

- `"continue"` → `Command(goto="react_npcs", update={"chosen_action": ...})` (full flow)
- `"end"` → `Command(goto=END, update={})` (terminate early)
- `"custom"` → `Command(goto="interpret_custom_action", update=...)` (stub for now)

Wire `interrupt_for_choice → route_choice` with an edge. The `react_npcs → next_scene → END` chain stays declarative. Then test all three flows: resume `"A"` (continue), resume `"B"` (end), resume `"custom"` (stub → continue). Each one should land at `END` with the expected `chosen_action.next_state`.

## 4. Reference
Working code: `src/langgraph_adventure/phases/phase5_command.py`. Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase5_command
```

The demo exercises all three flows against the real graph (with `InMemorySaver`). For each, it prints `chosen_action.next_state` and asserts the expected value. The `custom` flow goes through `interpret_custom_action`, whose Phase 5 stub always returns `next_state="continue"` — Phase 8 will swap that for a real LLM call.

## 5. Self-check
1. What's the difference between `add_edge` (declarative) and `Command(goto=...)` (imperative)?
2. Why does `route_choice` need to return `Command` rather than just a state dict?
3. What happens if you `Command(goto="non-existent-node")` — does it fail at runtime, at build time, or silently?

If any answer felt shaky, re-read the **Command** section in the LangGraph docs and trace the three `route_choice` branches by hand before moving on.