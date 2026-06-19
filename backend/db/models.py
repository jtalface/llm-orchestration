from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    title: str = Field(default="New conversation")
    model: str = Field(default="claude-sonnet-4-6")
    system_prompt: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class Turn(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    role: str  # user | assistant | tool_result
    content: str = Field(sa_column=Column(Text))
    model: Optional[str] = None
    step: Optional[int] = None  # agent step index
    tool_calls: Optional[list] = Field(default=None, sa_column=Column(JSON))
    tool_results: Optional[list] = Field(default=None, sa_column=Column(JSON))
    token_count: Optional[int] = None
    created_at: datetime = Field(default_factory=utcnow)
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class AgentRun(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    conversation_id: Optional[str] = Field(default=None, foreign_key="conversation.id")
    goal: str = Field(sa_column=Column(Text))
    model: str
    status: str = Field(default="running")  # running | completed | failed | stopped
    steps_taken: int = Field(default=0)
    total_tokens: int = Field(default=0)
    result: Optional[str] = Field(default=None, sa_column=Column(Text))
    error: Optional[str] = Field(default=None, sa_column=Column(Text))
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: Optional[datetime] = None
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))
