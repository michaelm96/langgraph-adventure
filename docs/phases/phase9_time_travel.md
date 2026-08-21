# Phase 9 — Time Travel with Checkpointers

The checkpointer saves state at every step. Phase 9 uses that to walk back to a prior turn (`/undo`) and to branch the run onto a fresh thread (`/fork`).

## 1. Concept
A `Checkpointer` saves state at every node. `get_state(config)` reads current state. `update_state(config, values=...)` rewrites state at the current checkpoint (or seeds a new thread). Together they enable time travel: undo by reading a parent checkpoint and `update_state`-ing its values into the current.

Each checkpoint carries a `parent_config` — the config of the checkpoint one step earlier. Reading `get_state(parent_config)` gives you the *previous* state of the same thread; passing those values back through `update_state(current_config, values=prev.values)` makes the current thread look like the prior turn again. Fork is the same call but aimed at a *different* `thread_id`: `update_state(new_config, values=cur.values)` seeds a brand-new thread with a copy of today's state, so the player can explore an alternate branch without disturbing the original.

## 2. Reading
- LangGraph persistence concepts: <https://langchain-ai.github.io/langgraph/concepts/persistence/#checkpoints>

Focus on (a) the checkpoint chain and `parent_config`, (b) `get_state` vs `update_state`, (c) how `thread_id` isolates state across invocations.

## 3. Hands-on
In `cli/play.py`, add `/undo` and `/fork` slash commands.

`/undo` reads `state.parent_config` from `graph.get_state(config)`. If it exists, fetch `prev = graph.get_state(state.parent_config)`, then call `graph.update_state(config, values=prev.values)` to roll the current thread back. Print the new current_scene so the player sees the time-travel take effect.

`/fork` reads the current `state.values` and writes them into a fresh thread via `graph.update_state({"configurable": {"thread_id": new_id}}, values=state.values)`. Switch the session's active `thread_id` to `new_id` so subsequent input runs on the branch instead of the original. The original thread is untouched — come back to it any time by switching `thread_id` back.

Both commands reuse the existing compiled graph: `update_state` does not run nodes, it only rewrites checkpointed state, so neither command touches the LLM or the scene generator.

## 4. Reference
Working code: `src/langgraph_adventure/phases/phase9_time_travel.py`. Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase9_time_travel
```

The demo plays turn 1, uses `update_state` to swap in a turn-2 scene (MOCK has no real scene transition), then walks `parent_config` to undo back to turn 1, and finally forks the rolled-back state onto a new thread id. It asserts each step: turn-1 scene after invoke, turn-2 scene after the manual update, turn-1 again after undo, and turn-1 in the forked thread.

## 5. Self-check
1. What's the difference between `checkpointer` and `store`?
2. How does `update_state` differ from `invoke`? (Hint: `update_state` doesn't run any nodes.)
3. When would you use `/fork` instead of `/undo`?

If any answer felt shaky, re-read the persistence concepts doc and trace the chain by hand: invoke writes a checkpoint → `get_state` reads it → `parent_config` points one step earlier → `update_state` rewrites without running nodes. Move on only when you can describe both commands without peeking.
