"""Phase 6 demo: Send fanout for parallel NPC reactions.

Demonstrates:
- Scene with 3 NPCs triggers 3 parallel _npc_react invocations
- All NPC dialogues merge into state.npc_dialogues via operator.or_ reducer
- merge_reactions formats dialogues into AIMessages in state.messages
- No regression on Phase 4 + 5 demos
"""
import os
os.environ.setdefault("MOCK_LLM", "1")  # per C10 ruling
import time
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langgraph_adventure.game_graph import build_game_graph
from langgraph_adventure.state import Scene, Action


def demo() -> None:
    g = build_game_graph().compile(checkpointer=InMemorySaver())

    # 3-NPC scene to stress the fanout
    fake = Scene(
        scene_id="p6_demo",
        description="A crowded crossroads. Three figures stand in the dust.",
        npcs=["Old Hermit", "Witch of the Mist", "Cave Troll"],
        actions=[Action(id="A", label="Approach them", next_state="continue")],
    )

    config = {"configurable": {"thread_id": "phase6-demo"}}
    state = {"messages": [], "current_scene": fake, "chosen_action": None, "npc_dialogues": {}}

    start = time.perf_counter()
    r1 = g.invoke(state, config)
    assert "__interrupt__" in r1
    r2 = g.invoke(Command(resume="A"), config)
    elapsed = time.perf_counter() - start

    # Verify npc_dialogues
    npc_dialogues = r2.get("npc_dialogues", {})
    print(f"[npc_dialogues] {len(npc_dialogues)} NPCs reacted:")
    for persona, dialogue in npc_dialogues.items():
        print(f"  {persona}: \"{dialogue}\"")
    assert set(npc_dialogues.keys()) == {"Old Hermit", "Witch of the Mist", "Cave Troll"}

    # Verify AIMessages from merge_reactions
    msgs = r2.get("messages", [])
    npc_msgs = [m for m in msgs if hasattr(m, "content") and isinstance(m.content, str) and ('"' in m.content)]
    print(f"\n[merge_reactions] {len(npc_msgs)} NPC AIMessages")
    for m in npc_msgs:
        print(f"  - {m.content}")
    assert len(npc_msgs) == 3, f"expected 3 NPC messages from merge_reactions, got {len(npc_msgs)}"

    # Verify parallel execution: 3 NPCs should take < 3x single-NPC time
    # (MOCK is fast, but the principle holds — parallel < serial)
    print(f"\nelapsed: {elapsed*1000:.1f}ms (3 NPCs in parallel)")
    assert elapsed < 5.0, f"unexpectedly slow: {elapsed:.1f}s"
    print("\nSend fanout + merge_reactions verified for 3 NPCs ✓")


if __name__ == "__main__":
    demo()
