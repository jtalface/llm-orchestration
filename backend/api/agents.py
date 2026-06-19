"""
POST /agents/run/stream  — run the agent loop, stream events as SSE
POST /agents/run         — run agent, return when done
GET  /agents/tools       — list available tools
GET  /agents/models      — list known models
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session

from backend.db.database import get_session
from backend.db.models import AgentRun
from backend.orchestration.agent import run_agent, AgentEventType
from backend.orchestration.multi_agent import run_multi_agent
from backend.tools.registry import get_all_tools
from backend.config import settings

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentRunRequest(BaseModel):
    goal: str
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    tool_names: Optional[list[str]] = None  # None = all tools
    max_steps: int = 0  # 0 = use default
    max_tokens: int = 0
    conversation_id: Optional[str] = None
    multi_agent: bool = False


@router.post("/run/stream")
async def run_agent_stream(
    req: AgentRunRequest,
    session: Session = Depends(get_session),
):
    """Run the agent loop and stream events as Server-Sent Events."""
    run_id = str(uuid.uuid4())

    # Create run record
    run = AgentRun(
        id=run_id,
        conversation_id=req.conversation_id,
        goal=req.goal,
        model=req.model or settings.default_model,
    )
    session.add(run)
    session.commit()

    async def event_stream():
        steps = 0
        try:
            if req.multi_agent:
                gen = run_multi_agent(
                    goal=req.goal,
                    model=req.model or settings.default_model,
                )
            else:
                gen = run_agent(
                    goal=req.goal,
                    model=req.model or settings.default_model,
                    system_prompt=req.system_prompt,
                    tool_names=req.tool_names,
                    max_steps=req.max_steps or settings.default_max_steps,
                    max_tokens=req.max_tokens or settings.default_max_tokens,
                    run_id=run_id,
                )

            async for event in gen:
                if req.multi_agent:
                    payload = {"type": event.type}
                    if event.plan:
                        payload["plan"] = event.plan
                    if event.agent_event:
                        ae = event.agent_event
                        payload["subtask_id"] = event.subtask_id
                        payload["agent_event"] = {
                            "type": ae.type.value,
                            "step": ae.step,
                            "text": ae.text,
                            "tool_name": ae.tool_name,
                            "tool_input": ae.tool_input,
                            "tool_result": ae.tool_result,
                        }
                    if event.final_text:
                        payload["final_text"] = event.final_text
                else:
                    payload = {
                        "type": event.type.value,
                        "step": event.step,
                    }
                    if event.text:
                        payload["text"] = event.text
                    if event.tool_name:
                        payload["tool_name"] = event.tool_name
                    if event.tool_input:
                        payload["tool_input"] = event.tool_input
                    if event.tool_result:
                        payload["tool_result"] = event.tool_result
                    if event.tool_call_id:
                        payload["tool_call_id"] = event.tool_call_id
                    if event.final_text:
                        payload["final_text"] = event.final_text
                    if event.error:
                        payload["error"] = event.error
                    if event.usage:
                        payload["usage"] = event.usage

                    if not req.multi_agent:
                        if event.type == AgentEventType.STEP_START:
                            steps = event.step
                        elif event.type == AgentEventType.DONE:
                            _update_run(session, run_id, "completed", event.final_text or "", steps)
                        elif event.type == AgentEventType.ERROR:
                            _update_run(session, run_id, "failed", event.error or "", steps)

                yield f"data: {json.dumps(payload)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            _update_run(session, run_id, "failed", str(e), steps)
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _update_run(session, run_id: str, status: str, result: str, steps: int):
    run = session.get(AgentRun, run_id)
    if run:
        run.status = status
        run.result = result[:4000]
        run.steps_taken = steps
        run.finished_at = datetime.now(timezone.utc)
        session.add(run)
        session.commit()


@router.get("/tools")
def list_tools():
    """List all registered tools."""
    return [
        {
            "name": t.name,
            "description": t.description,
            "parameters": t.parameters,
            "requires_confirmation": t.requires_confirmation,
        }
        for t in get_all_tools()
    ]


@router.get("/models")
def list_models():
    """Return known model IDs grouped by provider."""
    return {
        "anthropic": [
            "claude-opus-4-8",
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
        ],
        "openai": ["gpt-4o", "gpt-4o-mini", "o1", "o3"],
        "gemini": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "ollama": ["llama3.2", "mistral", "qwen2.5", "phi4", "deepseek-r1"],
        "openrouter": [
            "anthropic/claude-opus-4-8",
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mixtral-8x7b-instruct",
        ],
    }


@router.get("/runs")
def list_runs(session: Session = Depends(get_session)):
    from sqlmodel import select
    runs = session.exec(
        select(AgentRun).order_by(AgentRun.started_at.desc()).limit(50)
    ).all()
    return runs
