"""FastAPI server for langgraph-adventure web UI.

Local-only browser UI wrapping the existing game_graph. Each browser
session = one thread_id (UUID4 in URL). See spec §3.
"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="langgraph-adventure")


@app.get("/")
def root() -> dict[str, str]:
    """Placeholder. Real redirect added in Task 2."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("langgraph_adventure.web.server:app", host="127.0.0.1", port=8000, reload=False)
