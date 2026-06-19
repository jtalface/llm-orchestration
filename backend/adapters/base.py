from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Any, Optional
from enum import Enum


class StreamEventType(str, Enum):
    TEXT_DELTA = "text_delta"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_DELTA = "tool_call_delta"
    TOOL_CALL_END = "tool_call_end"
    USAGE = "usage"
    STOP = "stop"
    ERROR = "error"


@dataclass
class StreamEvent:
    type: StreamEventType
    text: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_input_delta: Optional[str] = None
    stop_reason: Optional[str] = None  # end_turn | tool_use | max_tokens
    usage: Optional[dict] = None
    error: Optional[str] = None


@dataclass
class Message:
    role: str  # user | assistant
    content: str | list  # str for simple text, list for multi-part (tool results etc.)


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class CompletionResult:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class BaseLLMAdapter(ABC):
    """
    Unified interface for all LLM providers.
    All adapters implement stream() and complete() with the same signature.
    """

    provider: str = "base"
    supports_tool_use: bool = True
    supports_vision: bool = False

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        system: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """Stream tokens and tool call events."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        system: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
    ) -> CompletionResult:
        """Non-streaming completion. Returns full result."""
        ...

    async def embed(self, text: str) -> list[float]:
        """Optional: return embedding vector for text."""
        raise NotImplementedError(f"{self.provider} adapter does not support embeddings")

    def format_tool_schema(self, tool_schemas: list[dict]) -> list[dict]:
        """
        Convert normalized tool schemas to provider-specific format.
        Override in subclass if the provider uses a different format.
        Default returns OpenAI-compatible format.
        """
        return tool_schemas

    def messages_to_provider(self, messages: list[Message]) -> list[dict]:
        """Convert Message dataclass list to provider's dict format."""
        result = []
        for m in messages:
            if isinstance(m.content, str):
                result.append({"role": m.role, "content": m.content})
            else:
                result.append({"role": m.role, "content": m.content})
        return result
