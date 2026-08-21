"""FastAPI server for langgraph-adventure web UI.

Local-only browser UI wrapping the existing game_graph. Each browser
session = one thread_id (UUID4 in URL). See spec §3.
"""
from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(title="langgraph-adventure")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("langgraph_adventure.web.server:app", host="127.0.0.1", port=8000, reload=False)
