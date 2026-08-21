"""Phase 7 demo: astream_events for token streaming.

Demonstrates:
- astream_events(version="v2") yields discrete events as the graph runs
- Filter for `on_chat_model_stream` events to get token-by-token chunks
- Even MOCK_LLM fires these events (1 chunk per node call)
"""
import os
os.environ.setdefault("MOCK_LLM", "1")  # per C10 ruling
import asyncio
from langgraph_adventure.meta_graph import build_meta_graph


async def demo_async() -> None:
    g = build_meta_graph()
    events_seen = []
    chunks_seen = []

    print("[streaming] events from meta_graph.astream_events:")
    async for event in g.astream_events(
        {"theme": "noir detective", "world_seed": "test", "current_request": "continue", "history": [], "npc_dialogues": {}},
        version="v2",
    ):
        kind = event["event"]
        events_seen.append(kind)
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            content = chunk.content if hasattr(chunk, "content") else ""
            chunks_seen.append(content)

    print(f"\n[summary] event kinds: {sorted(set(events_seen))}")
    print(f"[summary] on_chat_model_stream chunks: {len(chunks_seen)}")

    assert "on_chat_model_stream" in events_seen, "expected on_chat_model_stream events"
    assert len(chunks_seen) >= 1, f"expected >= 1 chunks, got {len(chunks_seen)}"
    print("\nastream_events hook works ✓")


def demo() -> None:
    asyncio.run(demo_async())


if __name__ == "__main__":
    demo()
