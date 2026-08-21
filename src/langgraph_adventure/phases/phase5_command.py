"""Phase 5 demo: Command-based explicit routing.

Demonstrates:
- 'continue' action → route_choice → react_npcs → next_scene → END (full flow)
- 'end' action → route_choice → END (terminate early)
- 'custom' action → route_choice → interpret_custom_action → react_npcs → next_scene → END
  (stub in phase 5; phase 8 swaps stub for real LLM call)
"""
import os
os.environ.setdefault("MOCK_LLM", "1")  # per C10 ruling
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langgraph_adventure.game_graph import build_game_graph
from langgraph_adventure.state import Scene, Action


def demo() -> None:
    g = build_game_graph().compile(checkpointer=InMemorySaver())

    fake = Scene(
        scene_id="phase5",
        description="Phase 5 scene.",
        npcs=[],
        actions=[
            Action(id="A", label="Open the door", next_state="continue"),
            Action(id="B", label="Turn back", next_state="end"),
        ],
    )

    # Test 1: 'A' (continue) → full flow through react_npcs → next_scene
    print("[test 1] resume 'A' (continue)")
    config = {"configurable": {"thread_id": "t5d-A"}}
    state = {"messages": [], "current_scene": fake, "chosen_action": None, "npc_dialogues": {}}
    r1 = g.invoke(state, config)
    assert "__interrupt__" in r1
    r2 = g.invoke(Command(resume="A"), config)
    print(f"  chosen_action.next_state: {r2['chosen_action'].next_state}")
    assert r2["chosen_action"].next_state == "continue"
    assert r2["chosen_action"].id == "A"
    print("  → continue flow OK")

    # Test 2: 'B' (end) → terminate at route_choice
    print("\n[test 2] resume 'B' (end)")
    config = {"configurable": {"thread_id": "t5d-B"}}
    r1 = g.invoke(state, config)
    assert "__interrupt__" in r1
    r2 = g.invoke(Command(resume="B"), config)
    print(f"  chosen_action.next_state: {r2['chosen_action'].next_state}")
    assert r2["chosen_action"].next_state == "end"
    assert r2["chosen_action"].id == "B"
    print("  → end flow OK")

    # Test 3: 'custom' → route to interpret_custom_action stub (which returns next_state='continue')
    print("\n[test 3] resume 'custom' (interpret_custom_action stub)")
    config = {"configurable": {"thread_id": "t5d-C"}}
    r1 = g.invoke(state, config)
    assert "__interrupt__" in r1
    r2 = g.invoke(Command(resume="custom"), config)
    print(f"  chosen_action.next_state: {r2['chosen_action'].next_state}")
    # Phase 5 stub routes everything to 'continue'; Phase 8 will replace with real LLM call
    assert r2["chosen_action"].next_state == "continue"
    print("  → custom flow OK (stub)")

    print("\nCommand routing verified for continue / end / custom ✓")


if __name__ == "__main__":
    demo()