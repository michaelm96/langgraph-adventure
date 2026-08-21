"""LLM factory.

MiniMax provider (Anthropic-compatible API) plus a MOCK mode for tests.
Reads MINIMAX_API_KEY from env, falling back to .env file in cwd/parent dirs.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk


def _load_env_file() -> None:
    """Ponytail: stdlib-only .env loader. Walks up from cwd looking for .env."""
    if "MINIMAX_API_KEY" in os.environ:
        return
    for d in (Path.cwd(), *Path.cwd().parents):
        env_path = d / ".env"
        if env_path.is_file():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


class _MockChatModel(BaseChatModel):
    """Ponytail: cheap sentinel for tests. Returns a fixed canned response."""

    canned_response: str = "MOCK_RESPONSE"

    def _generate(self, messages, stop=None, **kwargs):
        from langchain_core.outputs import ChatResult, ChatGeneration
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=self.canned_response))]
        )

    async def astream(self, messages, **kwargs) -> AsyncIterator[AIMessageChunk]:
        yield AIMessageChunk(content=self.canned_response)

    @property
    def _llm_type(self) -> str:
        return "mock"

    def bind_tools(self, tools, **kwargs):
        """No-op; tools are never invoked."""
        return self


def resolve_model(model_str: str) -> BaseChatModel:
    """Return a chat model from a 'provider/name' string."""
    if os.environ.get("MOCK_LLM") == "1":
        return _MockChatModel()

    _load_env_file()

    if "/" not in model_str:
        raise ValueError(f"Model must be 'provider/name', got: {model_str!r}")
    provider, name = model_str.split("/", 1)

    if provider == "minimax":
        from langchain_anthropic import ChatAnthropic
        api_key = os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            raise RuntimeError(
                "MINIMAX_API_KEY not set. Either export it in your shell "
                "(`export MINIMAX_API_KEY=...`) or create a `.env` file in "
                "the project root with `MINIMAX_API_KEY=...`. "
                "See README → Status for context."
            )
        return ChatAnthropic(
            model=name,
            api_key=api_key,
            base_url="https://api.minimax.io/anthropic",
        )

    raise ValueError(f"Unknown provider: {provider}")
