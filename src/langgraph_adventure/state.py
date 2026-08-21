"""Pydantic models for the adventure game state.

Defines the data shapes for scenes, player actions, and NPC reactions.
Graph-state TypedDicts (e.g. MetaState) live with their consumers, not here.
"""

from pydantic import BaseModel


class Action(BaseModel):
    """A single choice the player can make in a scene."""

    id: str
    label: str
    next_state: str


class Scene(BaseModel):
    """A location in the adventure: narration, present NPCs, and available actions."""

    scene_id: str = ""
    description: str
    npcs: list[str]
    actions: list[Action]


class NPCReaction(BaseModel):
    """An NPC's response to the player, optionally updating shared memory."""

    npc_name: str
    dialogue: str
    memory_update: str | None
