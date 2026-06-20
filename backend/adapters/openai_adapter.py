import json
import uuid
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

from backend.adapters.base import (
    BaseLLMAdapter, Message, StreamEvent, StreamEventType,
    CompletionResult, ToolCall,
)
from backend.config import settings


class OpenAIAdapter(BaseLLMAdapter):
    provider = "openai"
    supports_tool_use = True
    supports_vision = True

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        key = api_key or settings.openai_api_key or "not-set"
        self.client = AsyncOpenAI(
            api_key=key,
            base_url=base_url,
        )

    def format_tool_schema(self, tool_schemas: list[dict]) -> list[dict]:
        """OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                },
            }
            for t in tool_schemas
        ]

    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        system: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(self.messages_to_provider(messages))

        params = dict(
            model=self.model,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True},
        )
        if tools:
            params["tools"] = self.format_tool_schema(tools)
            params["tool_choice"] = "auto"

        # Buffers for assembling streamed tool calls
        tool_buffers: dict[int, dict] = {}

        s = await self.client.chat.completions.create(**params)
        async for chunk in s:
            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                if chunk.usage:
                    yield StreamEvent(
                        type=StreamEventType.USAGE,
                        usage={
                            "input_tokens": chunk.usage.prompt_tokens,
                            "output_tokens": chunk.usage.completion_tokens,
                        },
                    )
                continue

            delta = choice.delta

            if delta.content:
                yield StreamEvent(type=StreamEventType.TEXT_DELTA, text=delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_buffers:
                        tool_buffers[idx] = {
                            "id": tc.id or str(uuid.uuid4()),
                            "name": tc.function.name or "",
                            "input_json": "",
                        }
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_START,
                            tool_call_id=tool_buffers[idx]["id"],
                            tool_name=tool_buffers[idx]["name"],
                        )
                    if tc.function.name and not tool_buffers[idx]["name"]:
                        tool_buffers[idx]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_buffers[idx]["input_json"] += tc.function.arguments
                        yield StreamEvent(
                            type=StreamEventType.TOOL_CALL_DELTA,
                            tool_call_id=tool_buffers[idx]["id"],
                            tool_input_delta=tc.function.arguments,
                        )

            if choice.finish_reason:
                for buf in tool_buffers.values():
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
                tool_buffers.clear()
                yield StreamEvent(
                    type=StreamEventType.STOP,
                    stop_reason=choice.finish_reason,
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
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(self.messages_to_provider(messages))

        params = dict(
            model=self.model,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if tools:
            params["tools"] = self.format_tool_schema(tools)
            params["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**params)
        choice = response.choices[0]
        msg = choice.message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    inp = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    inp = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, input=inp))

        return CompletionResult(
            text=msg.content or "",
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            model=response.model,
        )
