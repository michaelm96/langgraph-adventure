# Phase 7 — Token Streaming with `astream_events`
Phases 4–6 showed how to *route*, *fan out*, and *merge*. Now we look at *observing* the graph as it runs — specifically, watching tokens come out of the LLM one at a time.

## 1. Concept
`graph.astream_events(input, version="v2")` is an async iterator that yields a dict for **every** internal event the graph emits while running: chain starts/streams/ends, chat-model starts/stream/end, tool calls, retriever reads, etc. Each event has an `event` key (kind) and a `data` payload. Filter for the kinds you care about.

For token-by-token rendering, the magic kind is `on_chat_model_stream`: it fires **per chunk** (often a single token), with `event["data"]["chunk"]` carrying the model's incremental output — typically an `AIMessageChunk` with a `.content` string. Print `chunk.content` as you go and the user sees the model's reply materialize word-by-word instead of all at once.

`astream` (Phase 1) streams **state updates** after each node. `astream_events` streams **internal events** during each node. Use `astream` when you only want output; use `astream_events` when you want to observe progress (UIs, logs, token streaming).

## 2. Reading
- LangGraph streaming events: <https://langchain-ai.github.io/langgraph/concepts/streaming/#stream-events>
Focus on (a) the v2 event schema and the `version="v2"` requirement, (b) which event kinds exist and which one carries tokens, (c) why you should always filter by kind — the raw stream is verbose.

## 3. Hands-on
In `cli/play.py`, replace the meta-graph `invoke` (or `stream`) with `astream_events(..., version="v2")`. Inside the loop, filter on `event["event"] == "on_chat_model_stream"` and `print(event["data"]["chunk"].content, end="", flush=True)` to render token-by-token. Keep a fallback — when no chunks arrive (cached response, tool-only steps), show the final state from `on_chain_end` so the user is never left staring at silence.

## 4. Reference
Working code: `src/langgraph_adventure/phases/phase7_stream.py`. Run it:

```bash
MOCK_LLM=1 python -m langgraph_adventure.phases.phase7_stream
```

The demo builds the meta-graph, drains `astream_events(version="v2")` for one invoke, sorts the distinct event kinds seen, counts `on_chat_model_stream` chunks, and asserts the hook fired at least once. MOCK_LLM fires the events but emits one chunk per LLM call — production models emit many.

## 5. Self-check
1. What's the difference between `astream` (yields state updates) and `astream_events` (yields internal events)?
2. Why must you specify `version="v2"` in langgraph 1.2.x?
3. When does `on_chat_model_stream` fire — per token, per chunk, per response?

If any answer felt shaky, re-read the streaming section in the LangGraph docs and trace one `astream_events` invocation against the meta-graph by hand. Move on only when the event schema and the streaming hook are clear.
