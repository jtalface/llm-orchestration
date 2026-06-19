import json
import uuid
from typing import AsyncIterator, Optional

import anthropic

from backend.adapters.base import (
    BaseLLMAdapter, Message, StreamEvent, StreamEventType,
    CompletionResult, ToolCall,
)
from backend.config import settings


class AnthropicAdapter(BaseLLMAdapter):
    provider = "anthropic"
    supports_tool_use = True
    supports_vision = True

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: Optional[str] = None):
        self.model = model
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.anthropic_api_key
        )

    def format_tool_schema(self, tool_schemas: list[dict]) -> list[dict]:
        """Convert normalized schemas to Anthropic tool format."""
        result = []
        for t in tool_schemas:
            result.append({
                "name": t["name"],
                "description": t.get("description", ""),
                "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
            })
        return result

    def _messages_to_anthropic(self, messages: list[Message]) -> list[dict]:
        result = []
        for m in messages:
            if isinstance(m.content, str):
                result.append({"role": m.role, "content": m.content})
            else:
                # list content blocks (tool results, images, etc.)
                result.append({"role": m.role, "content": m.content})
        return result

    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        system: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        params = dict(
            model=self.model,
            messages=self._messages_to_anthropic(messages),
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if system:
            params["system"] = system
        if tools:
            params["tools"] = self.format_tool_schema(tools)

        # Track partial tool call inputs for streaming assembly
        tool_call_buffers: dict[int, dict] = {}

        async with self.client.messages.stream(**params) as s:
            async for event in s:
                etype = event.type

                if etype == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        tool_call_buffers[event.index] = {
                            "id": block.id,
                            "name": block.name,
                            "input_json": "",
                        }
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_START,
                            tool_call_id=block.id,
                            tool_name=block.name,
                        )

                elif etype == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        yield StreamEvent(
                            type=StreamEventType.TEXT_DELTA,
                            text=delta.text,
                        )
                    elif delta.type == "input_json_delta":
                        buf = tool_call_buffers.get(event.index)
                        if buf:
                            buf["input_json"] += delta.partial_json
                            yield StreamEvent(
                                type=StreamEventType.TOOL_CALL_DELTA,
                                tool_call_id=buf["id"],
                                tool_input_delta=delta.partial_json,
                            )

                elif etype == "content_block_stop":
                    buf = tool_call_buffers.pop(event.index, None)
                    if buf:
                        try:
                            parsed = json.loads(buf["input_json"]) if buf["input_json"] else {}
                        except json.JSONDecodeError:
                            parsed = {}
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_END,
                            tool_call_id=buf["id"],
                            tool_name=buf["name"],
                            tool_input=parsed,
                        )

                elif etype == "message_delta":
                    if hasattr(event, "usage"):
                        yield StreamEvent(
                            type=StreamEventType.USAGE,
                            usage={"output_tokens": event.usage.output_tokens},
                        )

                elif etype == "message_stop":
                    final = await s.get_final_message()
                    yield StreamEvent(
                        type=StreamEventType.STOP,
                        stop_reason=final.stop_reason,
                        usage={
                            "input_tokens": final.usage.input_tokens,
                            "output_tokens": final.usage.output_tokens,
                        },
                    )

    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        system: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
    ) -> CompletionResult:
        params = dict(
            model=self.model,
            messages=self._messages_to_anthropic(messages),
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if system:
            params["system"] = system
        if tools:
            params["tools"] = self.format_tool_schema(tools)

        response = await self.client.messages.create(**params)

        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    input=block.input,
                ))

        return CompletionResult(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model,
        )
