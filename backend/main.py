from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.database import create_db_and_tables

# Import tools module to trigger @tool registration
import backend.tools  # noqa: F401

from backend.api import chat, conversations, agents, memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    create_db_and_tables()
    yield


app = FastAPI(
    title="LLM Orchestration Platform",
    version="0.1.0",
    description="Personal LLM platform with multi-model routing, agent loop, and memory",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(agents.router)
app.include_router(memory.router)


@app.get("/")
def root():
    return {
        "name": "LLM Orchestration Platform",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
