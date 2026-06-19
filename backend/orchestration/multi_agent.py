"""
Multi-agent orchestration: a manager agent decomposes a goal into subtasks,
spawns specialist agents, collects their results, and synthesizes the final output.
"""
from __future__ import annotations
import json
import uuid
import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional

from backend.adapters import get_adapter, Message
from backend.orchestration.agent import run_agent, AgentEvent, AgentEventType
from backend.config import settings


@dataclass
class SubtaskSpec:
    id: str
    title: str
    goal: str
    model: str
    tool_names: Optional[list[str]] = None


@dataclass
class MultiAgentEvent:
    type: str  # "plan" | "subtask_start" | "agent_event" | "subtask_done" | "synthesis" | "done" | "error"
    subtask_id: Optional[str] = None
    subtask_title: Optional[str] = None
    agent_event: Optional[AgentEvent] = None
    plan: Optional[list[dict]] = None
    final_text: Optional[str] = None
    error: Optional[str] = None


DECOMPOSE_SYSTEM = """You are a task decomposer. Given a high-level goal, break it into 2-5 concrete subtasks
that can be worked on independently. Each subtask should be self-contained.

Respond ONLY with valid JSON — a list of objects with these keys:
- title: short name for the subtask (5 words max)
- goal: full description of what the subtask agent should accomplish
- tools: list of tool names the subtask needs (from: web_search, fetch_url, run_python, pip_install, read_file, write_file, list_directory, http_get, http_post, calculator, get_datetime)

Example:
[
  {"title": "Market research", "goal": "Search for the top 5 EV companies by market share in 2026", "tools": ["web_search"]},
  {"title": "Data analysis", "goal": "Given the market share data, calculate growth rates and generate a bar chart", "tools": ["run_python", "write_file"]}
]
"""

SYNTHESIZE_SYSTEM = """You are a synthesis agent. You will receive the results of multiple specialist agents
that each worked on a subtask. Your job is to combine their findings into a single coherent, well-structured response
that fully addresses the original goal. Be thorough but concise. Do not just concatenate — integrate and synthesize."""


async def run_multi_agent(
    goal: str,
    model: str = "",
    max_parallel: int = 3,
) -> AsyncIterator[MultiAgentEvent]:
    model = model or settings.default_model
    adapter = get_adapter(model)

    # Step 1: Decompose the goal into subtasks
    decompose_result = await adapter.complete(
        messages=[Message(role="user", content=f"Decompose this goal into subtasks:\n\n{goal}")],
        system=DECOMPOSE_SYSTEM,
        max_tokens=2048,
        temperature=0.3,
    )

    try:
        raw = decompose_result.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        subtask_defs = json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError):
        yield MultiAgentEvent(
            type="error",
            error=f"Failed to parse decomposition plan. Raw: {decompose_result.text[:500]}",
        )
        return

    subtasks = [
        SubtaskSpec(
            id=str(uuid.uuid4()),
            title=s.get("title", f"Subtask {i+1}"),
            goal=s.get("goal", ""),
            model=model,
            tool_names=s.get("tools"),
        )
        for i, s in enumerate(subtask_defs)
    ]

    yield MultiAgentEvent(
        type="plan",
        plan=[{"id": s.id, "title": s.title, "goal": s.goal} for s in subtasks],
    )

    # Step 2: Run subtasks (respecting max_parallel)
    subtask_results: dict[str, str] = {}
    semaphore = asyncio.Semaphore(max_parallel)

    async def run_subtask(subtask: SubtaskSpec) -> None:
        async with semaphore:
            yield MultiAgentEvent(
                type="subtask_start",
                subtask_id=subtask.id,
                subtask_title=subtask.title,
            )
            last_text = ""
            async for event in run_agent(
                goal=subtask.goal,
                model=subtask.model,
                tool_names=subtask.tool_names,
                run_id=subtask.id,
                use_episodic_memory=False,
            ):
                yield MultiAgentEvent(
                    type="agent_event",
                    subtask_id=subtask.id,
                    subtask_title=subtask.title,
                    agent_event=event,
                )
                if event.type == AgentEventType.DONE and event.final_text:
                    last_text = event.final_text
            subtask_results[subtask.id] = last_text

            yield MultiAgentEvent(
                type="subtask_done",
                subtask_id=subtask.id,
                subtask_title=subtask.title,
                final_text=last_text,
            )

    # Run subtasks concurrently, streaming events as they come
    async def _collect(subtask: SubtaskSpec):
        events = []
        async for e in run_subtask(subtask):
            events.append(e)
        return events

    tasks = [asyncio.create_task(_collect(s)) for s in subtasks]
    for coro in asyncio.as_completed(tasks):
        events = await coro
        for e in events:
            yield e

    # Step 3: Synthesize all subtask results
    yield MultiAgentEvent(type="synthesis")

    results_text = "\n\n".join(
        f"## {s.title}\n{subtask_results.get(s.id, '(no result)')}"
        for s in subtasks
    )
    synthesis_prompt = (
        f"Original goal: {goal}\n\n"
        f"Results from specialist agents:\n\n{results_text}\n\n"
        f"Please synthesize these results into a final comprehensive response."
    )

    synthesis_result = await adapter.complete(
        messages=[Message(role="user", content=synthesis_prompt)],
        system=SYNTHESIZE_SYSTEM,
        max_tokens=4096,
        temperature=0.5,
    )

    yield MultiAgentEvent(
        type="done",
        final_text=synthesis_result.text,
    )
