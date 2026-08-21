"""Phase 9 demo: checkpointer + update_state for time travel.

Demonstrates:
- Every invoke() creates a new checkpoint; the chain can be walked via parent_config
- get_state(config) reads the current checkpoint's state
- update_state(config, values=prev_values) restores state — enables "undo last turn"
- Fork: update_state(new_config, values=cur_values) seeds a new thread for alternate exploration
"""
import os
os.environ.setdefault("MOCK_LLM", "1")  # per C10 ruling
import uuid
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langgraph_adventure.game_graph import build_game_graph
from langgraph_adventure.store import reset_store
from langgraph_adventure.state import Scene, Action


def demo() -> None:
    reset_store()
    g = build_game_graph().compile(checkpointer=InMemorySaver())

    # Play 2 turns: scene A → scene B (different scenes)
    fake_a = Scene(
        scene_id="turn1",
        description="Turn 1: a dark forest.",
        npcs=[],
        actions=[Action(id="A", label="Continue", next_state="continue")],
    )
    fake_b = Scene(
        scene_id="turn2",
        description="Turn 2: a moonlit clearing.",
        npcs=[],
        actions=[Action(id="A", label="Continue", next_state="continue")],
    )

    config = {"configurable": {"thread_id": "phase9-time-travel"}}

    # Turn 1
    state_a = {"messages": [], "current_scene": fake_a, "chosen_action": None, "npc_dialogues": {}}
    r1 = g.invoke(state_a, config)
    assert "__interrupt__" in r1
    r2 = g.invoke(Command(resume="A"), config)
    print(f"[turn 1] after invoke, current_scene.scene_id: {r2['current_scene'].scene_id}")
    assert r2["current_scene"].scene_id == "turn1"

    # Manually inject the next scene (no LLM transition in MOCK; phase 9 demonstrates
    # the checkpointer/undo mechanics, not scene generation). After turn 2 the
    # current_scene should reflect the new scene.
    g.update_state(config, values={"current_scene": fake_b})
    cur = g.get_state(config)
    print(f"[after turn 2 setup] current_scene.scene_id: {cur.values['current_scene'].scene_id}")
    assert cur.values["current_scene"].scene_id == "turn2"

    # Undo: walk back to turn 1
    print("\n[undo]")
    if cur.parent_config:
        prev = g.get_state(cur.parent_config)
        print(f"  parent checkpoint scene: {prev.values['current_scene'].scene_id}")
        g.update_state(config, values=prev.values)
        after = g.get_state(config)
        print(f"  after undo scene: {after.values['current_scene'].scene_id}")
        assert after.values["current_scene"].scene_id == "turn1"
    else:
        print("  no parent")

    # Fork: copy current state to a new thread
    print("\n[fork]")
    new_tid = f"fork-{uuid.uuid4().hex[:8]}"
    cur_state = g.get_state(config)
    new_config = {"configurable": {"thread_id": new_tid}}
    g.update_state(new_config, values=cur_state.values)
    forked = g.get_state(new_config)
    print(f"  forked thread: {new_tid}")
    print(f"  forked scene: {forked.values['current_scene'].scene_id}")
    assert forked.values["current_scene"].scene_id == "turn1"

    print("\ntime travel + fork verified ✓")


if __name__ == "__main__":
    demo()
