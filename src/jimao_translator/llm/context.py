"""T311: Context windowing helper.

Trim a long `ChatConversation` into a payload suitable for the LLM Messages API:
  * System prompt always comes first (if provided).
  * Keep the `max_messages` most recent messages.
  * The last message (the one we're about to send) is NEVER dropped silently.
"""

from __future__ import annotations

from ..models.chat import ChatConversation


def trim_conversation(
    conversation: ChatConversation,
    max_messages: int = 20,
    system_prompt: str | None = None,
) -> list[dict[str, str]]:
    """Return Messages-API payload: optional system + up to max_messages recent turns."""
    payload: list[dict[str, str]] = []
    if system_prompt:
        payload.append({"role": "system", "content": system_prompt})

    recent = (
        conversation.messages[-max_messages:]
        if len(conversation.messages) > max_messages
        else list(conversation.messages)
    )
    for msg in recent:
        payload.append({"role": msg.role.value, "content": msg.content})
    return payload
