"""Phase 8 demo: Store for long-term NPC memory.

Demonstrates:
- NPC subgraph reads player_name from store; writes last_interaction to store
- Same store instance, "different sessions" (different graph invocations)
  — the NPC remembers across them
- Player history is persisted via the game-graph's persist node
"""
import os
os.environ.setdefault("MOCK_LLM", "1")  # per C10 ruling
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langgraph_adventure.game_graph import build_game_graph
from langgraph_adventure.store import get_store, npc_recall, npc_remember, reset_store
from langgraph_adventure.state import Scene, Action


def demo() -> None:
    reset_store()
    store = get_store()

    # Pre-seed: player has introduced themselves to Old Hermit before
    npc_remember(store, "Old Hermit", "player_name", "Michael")

    g = build_game_graph().compile(checkpointer=InMemorySaver(), store=store)

    # Session 1: Michael meets Old Hermit
    print("[session 1] Michael enters the forest")
    fake1 = Scene(
        scene_id="forest_meet",
        description="A misty forest. The Old Hermit sits by a small fire.",
        npcs=["Old Hermit"],
        actions=[Action(id="A", label="Approach", next_state="continue")],
    )
    config = {"configurable": {"thread_id": "session-1"}}
    state = {"messages": [], "current_scene": fake1, "chosen_action": None, "npc_dialogues": {}}
    r1 = g.invoke(state, config)
    assert "__interrupt__" in r1
    r2 = g.invoke(Command(resume="A"), config)
    print(f"  npc_dialogues: {r2['npc_dialogues']}")
    assert "Michael" in r2["npc_dialogues"]["Old Hermit"]
    assert "we meet again" in r2["npc_dialogues"]["Old Hermit"]

    # Verify last_interaction was written
    last = npc_recall(store, "Old Hermit", "last_interaction")
    print(f"  stored last_interaction: {last!r}")
    assert last is not None

    # Verify player_history was written
    history = store.get(("player_history", "forest_meet"), "turn_forest_meet_A")
    print(f"  player_history: {history.value if history else None}")
    assert history is not None
    assert history.value["action_id"] == "A"

    # Session 2: same player, fresh thread — NPC remembers
    print("\n[session 2] Michael returns the next day")
    fake2 = Scene(
        scene_id="forest_return",
        description="The forest clearing. The Hermit's fire is freshly lit.",
        npcs=["Old Hermit"],
        actions=[Action(id="A", label="Greet", next_state="continue")],
    )
    config2 = {"configurable": {"thread_id": "session-2"}}
    state2 = {"messages": [], "current_scene": fake2, "chosen_action": None, "npc_dialogues": {}}
    r1b = g.invoke(state2, config2)
    assert "__interrupt__" in r1b
    r2b = g.invoke(Command(resume="A"), config2)
    print(f"  npc_dialogues: {r2b['npc_dialogues']}")
    assert "Michael" in r2b["npc_dialogues"]["Old Hermit"]
    assert "we meet again" in r2b["npc_dialogues"]["Old Hermit"]

    print("\nNPC remembers player across sessions ✓")


if __name__ == "__main__":
    demo()
