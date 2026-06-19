"""
The single-agent loop: Plan → Act → Observe → Reflect → Replan.

Yields AgentEvent objects for streaming to the frontend.
"""
from __future__ import annotations
import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import AsyncIterator, Optional

from backend.adapters.base import (
    BaseLLMAdapter, Message, StreamEvent, StreamEventType, ToolCall
)
from backend.adapters import get_adapter
from backend.tools.registry import get_tool_schemas, execute_tool
from backend.orchestration.context_manager import ContextManager
from backend.memory.episodic import format_episode_context, save_episode
from backend.config import settings


class AgentEventType(str, Enum):
    STEP_START = "step_start"
    TEXT_DELTA = "text_delta"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STEP_END = "step_end"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentEvent:
    type: AgentEventType
    step: int = 0
    text: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None
    tool_result: Optional[str] = None
    tool_call_id: Optional[str] = None
    stop_reason: Optional[str] = None
    final_text: Optional[str] = None
    error: Optional[str] = None
    usage: Optional[dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _build_default_system_prompt(tools: list[dict]) -> str:
    tool_lines = "\n".join(
        f"- **{t['name']}**: {t['description']}" for t in tools
    )
    return f"""You are an autonomous agent running inside an LLM Orchestration Platform.

You have access to the following tools:
{tool_lines}

Approach each goal methodically:
1. Think through what you need to accomplish step by step
2. Use tools to gather information, write code, or take actions
3. Observe results and adjust your approach
4. Continue until the goal is fully achieved

When the goal is complete, provide a clear final summary of what was accomplished.
If you cannot complete the goal, explain exactly why and what would be needed.
"""


async def run_agent(
    goal: str,
    model: str = "",
    system_prompt: Optional[str] = None,
    tool_names: Optional[list[str]] = None,
    max_steps: int = 0,
    max_tokens: int = 0,
    run_id: Optional[str] = None,
    use_episodic_memory: bool = True,
) -> AsyncIterator[AgentEvent]:
    """
    Run the agent loop. Yields AgentEvent objects.

    tool_names: if None, all registered tools are available.
    """
    model = model or settings.default_model
    max_steps = max_steps or settings.default_max_steps
    max_tokens = max_tokens or settings.default_max_tokens

    adapter = get_adapter(model)
    ctx = ContextManager()

    # Get available tools
    from backend.tools.registry import get_tool_schemas_for, get_tool_schemas
    if tool_names is not None:
        tools = get_tool_schemas_for(tool_names)
    else:
        tools = get_tool_schemas()

    # Build system prompt now that we know the tool list
    sys_prompt = system_prompt or _build_default_system_prompt(tools)
    if use_episodic_memory:
        episode_context = format_episode_context(goal)
        if episode_context:
            sys_prompt = f"{sys_prompt}\n\n{episode_context}"

    # Seed context with the goal
    ctx.add(Message(role="user", content=goal))

    step = 0
    full_text_buffer = []
    total_input_tokens = 0
    total_output_tokens = 0
    outcome = "failure"
    final_text = ""

    try:
        while step < max_steps:
            step += 1
            yield AgentEvent(type=AgentEventType.STEP_START, step=step)

            # Collect tool calls and text from this step
            pending_tool_calls: list[ToolCall] = []
            step_text_parts: list[str] = []
            assembled_tool_calls: dict[str, dict] = {}  # id → {name, input}

            # Stream from the model
            async for event in adapter.stream(
                messages=ctx.get_messages(),
                tools=tools,
                system=sys_prompt,
                max_tokens=max_tokens,
            ):
                if event.type == StreamEventType.TEXT_DELTA:
                    yield AgentEvent(
                        type=AgentEventType.TEXT_DELTA,
                        step=step,
                        text=event.text,
                    )
                    step_text_parts.append(event.text or "")

                elif event.type == StreamEventType.TOOL_CALL_START:
                    assembled_tool_calls[event.tool_call_id] = {
                        "id": event.tool_call_id,
                        "name": event.tool_name,
                        "input": {},
                    }

                elif event.type == StreamEventType.TOOL_CALL_END:
                    tc = assembled_tool_calls.get(event.tool_call_id, {})
                    tc["input"] = event.tool_input or {}
                    tc["name"] = event.tool_name or tc.get("name", "")
                    pending_tool_calls.append(
                        ToolCall(id=tc["id"], name=tc["name"], input=tc["input"])
                    )
                    yield AgentEvent(
                        type=AgentEventType.TOOL_CALL,
                        step=step,
                        tool_name=tc["name"],
                        tool_input=tc["input"],
                        tool_call_id=tc["id"],
                    )

                elif event.type == StreamEventType.USAGE:
                    if event.usage:
                        total_input_tokens += event.usage.get("input_tokens", 0)
                        total_output_tokens += event.usage.get("output_tokens", 0)

                elif event.type == StreamEventType.STOP:
                    stop_reason = event.stop_reason
                    if event.usage:
                        total_input_tokens += event.usage.get("input_tokens", 0)
                        total_output_tokens += event.usage.get("output_tokens", 0)

            step_text = "".join(step_text_parts)
            full_text_buffer.append(step_text)

            # Build assistant message for context (with tool use blocks if any)
            if pending_tool_calls:
                # Anthropic-style multi-block content
                content_blocks = []
                if step_text.strip():
                    content_blocks.append({"type": "text", "text": step_text})
                for tc in pending_tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    })
                ctx.add(Message(role="assistant", content=content_blocks))
            else:
                ctx.add(Message(role="assistant", content=step_text))

            # Execute tool calls and collect results
            if pending_tool_calls:
                tool_result_blocks = []
                for tc in pending_tool_calls:
                    try:
                        result = await execute_tool(tc.name, tc.input)
                        result_str = str(result)
                    except Exception as e:
                        result_str = f"[tool error] {tc.name}: {e}"

                    yield AgentEvent(
                        type=AgentEventType.TOOL_RESULT,
                        step=step,
                        tool_name=tc.name,
                        tool_result=result_str[:4000],  # cap per result
                        tool_call_id=tc.id,
                    )

                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": result_str[:8000],
                    })

                ctx.add(Message(role="user", content=tool_result_blocks))

            else:
                # No tool calls → model is done
                final_text = step_text
                outcome = "success"
                yield AgentEvent(
                    type=AgentEventType.DONE,
                    step=step,
                    final_text=final_text,
                    stop_reason="end_turn",
                    usage={
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "steps": step,
                    },
                )
                break

            yield AgentEvent(type=AgentEventType.STEP_END, step=step)

        else:
            # Exhausted max_steps
            final_text = f"Agent reached maximum steps ({max_steps}) without completing the goal."
            outcome = "partial"
            yield AgentEvent(
                type=AgentEventType.DONE,
                step=step,
                final_text=final_text,
                stop_reason="max_steps",
                usage={
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "steps": step,
                },
            )

    except Exception as e:
        yield AgentEvent(
            type=AgentEventType.ERROR,
            step=step,
            error=str(e),
        )
        outcome = "failure"
        final_text = f"Agent failed with error: {e}"

    finally:
        # Persist episode summary
        if final_text and run_id:
            try:
                save_episode(
                    goal=goal,
                    summary=final_text[:1000],
                    outcome=outcome,
                    model=model,
                    steps_taken=step,
                    run_id=run_id,
                )
            except Exception:
                pass  # non-critical
