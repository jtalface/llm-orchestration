from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.db.database import get_session
from backend.db.models import Conversation, Turn
from backend.config import settings

router = APIRouter(prefix="/conversations", tags=["conversations"])


class CreateConversationRequest(BaseModel):
    title: str = "New conversation"
    model: Optional[str] = None
    system_prompt: Optional[str] = None


@router.get("")
def list_conversations(session: Session = Depends(get_session)):
    convs = session.exec(
        select(Conversation).order_by(Conversation.updated_at.desc()).limit(100)
    ).all()
    return convs


@router.post("")
def create_conversation(
    req: CreateConversationRequest,
    session: Session = Depends(get_session),
):
    conv = Conversation(
        title=req.title,
        model=req.model or settings.default_model,
        system_prompt=req.system_prompt,
    )
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, session: Session = Depends(get_session)):
    conv = session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    turns = session.exec(
        select(Turn)
        .where(Turn.conversation_id == conversation_id)
        .order_by(Turn.created_at)
    ).all()
    return {"conversation": conv, "turns": turns}


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, session: Session = Depends(get_session)):
    conv = session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    session.exec(
        select(Turn).where(Turn.conversation_id == conversation_id)
    )
    turns = session.exec(select(Turn).where(Turn.conversation_id == conversation_id)).all()
    for t in turns:
        session.delete(t)
    session.delete(conv)
    session.commit()
    return {"ok": True}


@router.patch("/{conversation_id}")
def update_conversation(
    conversation_id: str,
    req: CreateConversationRequest,
    session: Session = Depends(get_session),
):
    conv = session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if req.title:
        conv.title = req.title
    if req.model:
        conv.model = req.model
    if req.system_prompt is not None:
        conv.system_prompt = req.system_prompt
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv
