"""T013: ChatMessage and ChatConversation models for LLM chat."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import MessageRole


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ChatMessage(BaseModel):
    """A single message in an LLM conversation."""

    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str = Field(min_length=1, max_length=20000)
    timestamp: datetime = Field(default_factory=_utcnow)
    token_usage: int | None = Field(default=None, ge=0)


class ChatConversation(BaseModel):
    """An ordered LLM chat session."""

    id: UUID = Field(default_factory=uuid4)
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    last_active_at: datetime = Field(default_factory=_utcnow)
