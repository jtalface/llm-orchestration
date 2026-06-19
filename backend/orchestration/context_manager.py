"""
Manages the context window: tracks token usage, applies a sliding window
when approaching the limit, and injects memory retrievals.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from backend.adapters.base import Message
from backend.config import settings

# Rough token estimate: 1 token ≈ 4 chars
def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _message_tokens(msg: Message) -> int:
    if isinstance(msg.content, str):
        return _estimate_tokens(msg.content) + 4  # role overhead
    if isinstance(msg.content, list):
        total = 4
        for block in msg.content:
            if isinstance(block, dict):
                total += _estimate_tokens(str(block))
        return total
    return 4


class ContextManager:
    """
    Wraps a message list and enforces token budget.
    When budget is exceeded, older non-system messages are compressed.
    """

    def __init__(self, budget: int = 0):
        self.budget = budget or settings.context_window_budget
        self._messages: list[Message] = []
        self._total_tokens: int = 0

    def add(self, message: Message) -> None:
        self._messages.append(message)
        self._total_tokens += _message_tokens(message)
        self._maybe_compress()

    def get_messages(self) -> list[Message]:
        return list(self._messages)

    @property
    def token_count(self) -> int:
        return self._total_tokens

    @property
    def is_near_limit(self) -> bool:
        return self._total_tokens > self.budget * 0.85

    def _maybe_compress(self) -> None:
        """
        If over budget, drop the oldest user/assistant message pairs
        (not the first user message — that's the goal) until back under 80%.
        """
        target = int(self.budget * 0.7)
        if self._total_tokens <= target:
            return

        # Keep first message (the goal) and last N messages
        if len(self._messages) <= 4:
            return

        # Drop messages from index 1, keeping the goal (0) and recent tail
        dropped = 0
        while self._total_tokens > target and len(self._messages) > 4:
            removed = self._messages.pop(1)
            self._total_tokens -= _message_tokens(removed)
            dropped += 1

        if dropped:
            # Insert a compression notice
            notice = Message(
                role="user",
                content=f"[{dropped} earlier messages were removed to stay within context limits]",
            )
            self._messages.insert(1, notice)
            self._total_tokens += _message_tokens(notice)
