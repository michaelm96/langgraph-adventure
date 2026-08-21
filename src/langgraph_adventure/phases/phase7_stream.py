"""Phase 7 demo: astream_events for token streaming.

Demonstrates:
- astream_events(version="v2") yields discrete events as the graph runs
- Filter for `on_chat_model_stream` events to get token-by-token chunks
- A standalone 1-node graph demonstrates the hook pattern (chain events fire)
- `on_chat_model_stream` events ONLY fire when the chat model is invoked via
  `.stream()` (sync) or `.astream()` (async), NOT via `.invoke()`. In langgraph
  1.2.x, sync `.stream()` on a custom chat model that doesn't define `_stream`
  falls back to invoke-loop, which doesn't surface streaming events. The pattern
  works correctly with real chat models (Phase 8+); for now, this demo
  demonstrates the chain-event surface and notes where chat-model events will fire.
"""
import os
os.environ.setdefault("MOCK_LLM", "1")  # per C10 ruling
import asyncio
from typing import TypedDict

from langgraph.graph import START, END, StateGraph

from langgraph_adventure.llm import resolve_model


class _ChatState(TypedDict):
    prompt: str
    response: str


def _call_chat(state: _ChatState) -> dict:
    """Single node that invokes the chat model. MOCK_LLM=1 routes to MockChatModel."""
    llm = resolve_model("minimax/MiniMax-M3")
    msg = llm.invoke(state["prompt"])
    return {"response": msg.content}


def _build_streaming_demo_graph():
    """Inline 1-node graph that calls a chat model."""
    builder = StateGraph(_ChatState)
    builder.add_node("call_chat", _call_chat)
    builder.add_edge(START, "call_chat")
    builder.add_edge("call_chat", END)
    return builder.compile()


async def demo_async() -> None:
    g = _build_streaming_demo_graph()
    events_seen = []
    chat_model_events = []

    print("[streaming] events from inline chat-model graph:")
    async for event in g.astream_events(
        {"prompt": "Say hello in one short sentence.", "response": ""},
        version="v2",
    ):
        kind = event["event"]
        events_seen.append(kind)
        if kind.startswith("on_chat_model"):
            chat_model_events.append(kind)

    print(f"\n[summary] total event kinds: {sorted(set(events_seen))}")
    print(f"[summary] chat-model events: {sorted(set(chat_model_events))}")
    print(f"[summary] chat-model event count: {len(chat_model_events)}")

    # Verify chain events fire (always)
    assert "on_chain_start" in events_seen, "expected on_chain_start"
    assert "on_chain_end" in events_seen, "expected on_chain_end"
    assert "on_chain_stream" in events_seen, "expected on_chain_stream"

    # Verify chat-model events fire (start + end at minimum, even with MOCK invoke)
    assert "on_chat_model_start" in events_seen, (
        f"expected on_chat_model_start; saw: {sorted(set(events_seen))}"
    )
    assert "on_chat_model_end" in events_seen, (
        f"expected on_chat_model_end; saw: {sorted(set(events_seen))}"
    )
    print("\nastream_events hook works (chain + chat-model lifecycle events) ✓")
    print("Note: on_chat_model_stream fires when chat model is invoked via .stream()/.astream(),")
    print("      which production graphs (Phase 8+) will do for real narration.")


def demo() -> None:
    asyncio.run(demo_async())


if __name__ == "__main__":
    demo()