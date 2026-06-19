"""
POST /chat/stream  — single-turn streaming chat (no agent loop)
POST /chat         — non-streaming chat
"""
import json
from typing import Optional, AsyncIterator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.adapters import get_adapter, Message
from backend.db.database import get_session
from backend.db.models import Conversation, Turn
from backend.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


async def _build_messages(
    conversation_id: Optional[str],
    new_message: str,
    session: Session,
) -> list[Message]:
    messages: list[Message] = []

    if conversation_id:
        turns = session.exec(
            select(Turn)
            .where(Turn.conversation_id == conversation_id)
            .order_by(Turn.created_at)
        ).all()
        for t in turns:
            messages.append(Message(role=t.role, content=t.content))

    messages.append(Message(role="user", content=new_message))
    return messages


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    session: Session = Depends(get_session),
):
    """Stream a chat response as Server-Sent Events."""
    model = req.model or settings.default_model
    adapter = get_adapter(model)
    messages = await _build_messages(req.conversation_id, req.message, session)

    # Persist the user turn
    conv_id = req.conversation_id
    if conv_id:
        turn = Turn(
            conversation_id=conv_id,
            role="user",
            content=req.message,
            model=model,
        )
        session.add(turn)
        session.commit()

    async def event_stream():
        text_buffer = []
        try:
            async for event in adapter.stream(
                messages=messages,
                system=req.system_prompt,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            ):
                payload = {"type": event.type.value}
                if event.text:
                    payload["text"] = event.text
                    text_buffer.append(event.text)
                if event.stop_reason:
                    payload["stop_reason"] = event.stop_reason
                if event.usage:
                    payload["usage"] = event.usage
                yield f"data: {json.dumps(payload)}\n\n"

            # Persist assistant response
            if conv_id and text_buffer:
                resp_turn = Turn(
                    conversation_id=conv_id,
                    role="assistant",
                    content="".join(text_buffer),
                    model=model,
                )
                session.add(resp_turn)
                session.commit()

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("")
async def chat(
    req: ChatRequest,
    session: Session = Depends(get_session),
):
    """Non-streaming chat completion."""
    model = req.model or settings.default_model
    adapter = get_adapter(model)
    messages = await _build_messages(req.conversation_id, req.message, session)

    result = await adapter.complete(
        messages=messages,
        system=req.system_prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )

    # Persist turns
    if req.conversation_id:
        session.add(Turn(
            conversation_id=req.conversation_id,
            role="user",
            content=req.message,
            model=model,
        ))
        session.add(Turn(
            conversation_id=req.conversation_id,
            role="assistant",
            content=result.text,
            model=model,
            token_count=result.output_tokens,
        ))
        session.commit()

    return {
        "text": result.text,
        "model": result.model or model,
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    }
