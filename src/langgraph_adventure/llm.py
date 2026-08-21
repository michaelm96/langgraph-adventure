"""LLM factory.

MiniMax provider (Anthropic-compatible API) plus a MOCK mode for tests.
Reads MINIMAX_API_KEY directly from env (no config.toml).
"""
from __future__ import annotations

import os
from typing import AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk


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

    if "/" not in model_str:
        raise ValueError(f"Model must be 'provider/name', got: {model_str!r}")
    provider, name = model_str.split("/", 1)

    if provider == "minimax":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=name,
            api_key=os.environ["MINIMAX_API_KEY"],
            base_url="https://api.minimax.io/anthropic",
        )

    raise ValueError(f"Unknown provider: {provider}")
