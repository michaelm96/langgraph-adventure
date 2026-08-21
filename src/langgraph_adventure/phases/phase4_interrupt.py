"""Phase 4 demo: interrupt() pauses the graph, Command(resume=...) resumes it.

Uses langgraph 1.2.x pattern: GraphInterrupt is suppressed at root level;
instead, invoke() returns __interrupt__ populated. Resume via Command(resume=...).
"""
import os
os.environ.setdefault("MOCK_LLM", "1")  # per C10 ruling
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langgraph_adventure.game_graph import build_game_graph
from langgraph_adventure.state import Scene, Action


def demo() -> None:
    g = build_game_graph().compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "phase4-demo"}}

    fake_scene = Scene(
        scene_id="test_int",
        description="You stand in a featureless room. A single door.",
        npcs=[],
        actions=[Action(id="A", label="Open door", next_state="continue"), Action(id="B", label="Stay", next_state="end")],
    )

    state = {"messages": [], "current_scene": fake_scene, "chosen_action": None, "npc_dialogues": {}}

    # First invoke: graph pauses at interrupt_for_choice
    print("[step 1] first invoke (expects __interrupt__)")
    r1 = g.invoke(state, config)
    print(f"  result keys: {sorted(r1.keys())}")
    assert "__interrupt__" in r1, "expected __interrupt__ in result (langgraph 1.2.x pattern)"
    interrupt = r1["__interrupt__"][0]
    payload = interrupt.value
    print(f"  interrupt payload: scene_id={payload['scene_id']}, {len(payload['actions'])} actions")
    print(f"  actions: {payload['actions']}")
    assert payload["scene_id"] == "test_int"
    # Phase 5.2 added a "custom" option to the menu, so 3 actions now (was 2 in Phase 4)
    assert len(payload["actions"]) == 3, f"expected 3 actions (A, B, custom), got {len(payload['actions'])}"

    # Resume with chosen action id 'A'
    print("\n[step 2] resume with Command(resume='A')")
    r2 = g.invoke(Command(resume="A"), config)
    assert "chosen_action" in r2, "expected chosen_action in state after resume"
    print(f"  chosen_action: id={r2['chosen_action'].id}, label={r2['chosen_action'].label}, next_state={r2['chosen_action'].next_state}")
    assert r2["chosen_action"].id == "A"

    # Resume with 'B' on a fresh thread
    print("\n[step 3] fresh thread, resume with 'B' (next_state=end)")
    config2 = {"configurable": {"thread_id": "phase4-demo-2"}}
    r1b = g.invoke(state, config2)
    assert "__interrupt__" in r1b
    r2b = g.invoke(Command(resume="B"), config2)
    assert r2b["chosen_action"].id == "B"
    print(f"  chosen_action: id={r2b['chosen_action'].id}, next_state={r2b['chosen_action'].next_state}")

    print("\ninterrupt + resume both work ✓")


if __name__ == "__main__":
    demo()
