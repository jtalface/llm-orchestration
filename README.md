# LLM Orchestration Platform

A fully self-hosted LLM platform with multi-model routing, a full agent loop (Plan → Act → Observe → Reflect), 14 built-in tools, vector memory, and a streaming React chat UI — all running locally, cloud-deployable on demand.

> Inspired by the architecture of frontier AI products like Claude Code, Devin, and Gemini Deep Research — built from scratch as a personal productivity tool.

---

## Features

| Capability | Details |
|---|---|
| **Multi-model routing** | Claude, GPT-4o, Gemini, Ollama (local), OpenRouter (300+ models) — same interface for all |
| **Agent loop** | Full Plan → Act → Observe → Reflect cycle with max-step guard, error recovery, and self-verification |
| **14 built-in tools** | Web search, code execution (sandboxed), file system, HTTP client, browser, calculator, datetime |
| **Vector memory** | ChromaDB embedded — semantic search, episodic run history, RAG retrieval at agent startup |
| **Multi-agent** | Manager decomposes goal → specialist agents run in parallel → synthesis pass |
| **Streaming UI** | React + Vite frontend with real-time token streaming, agent trace viewer, model hot-swap |
| **Local-first** | SQLite + ChromaDB, no cloud services required beyond LLM API calls |
| **Cloud-ready** | Swap SQLite → Postgres, ChromaDB → Qdrant, deploy via Docker Compose to Fly.io / Railway |

---

## Quick Start

### 1. Clone & set up Python environment

```bash
git clone https://github.com/jtalface/llm-orchestration.git
cd llm-orchestration

python3 -m venv .venv
.venv/bin/pip install fastapi "uvicorn[standard]" pydantic pydantic-settings \
    sqlmodel anthropic openai httpx chromadb python-dotenv \
    sse-starlette aiofiles tenacity rich
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and fill in your keys:
```

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
TAVILY_API_KEY=...          # for web search
OLLAMA_BASE_URL=http://localhost:11434   # if running local models
```

### 3. Install frontend dependencies

```bash
cd frontend && npm install && cd ..
```

### 4. Start both servers

```bash
./start.sh
```

| Service | URL |
|---|---|
| Frontend (chat UI) | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

---

## Usage

### Chat mode

Select a model from the dropdown and send a message. The model responds directly, no tools involved. Full conversation history is persisted in SQLite.

### Agent mode (⚡)

Toggle **Agent** in the top bar. Give the agent a *goal* instead of a question. It will:

1. Plan the steps needed
2. Call tools (web search, code execution, file writes, HTTP calls…)
3. Observe each result
4. Reflect and replan if needed
5. Keep going until the goal is achieved

Every tool call and result is visible in the collapsible **Agent Trace** panel below each response.

### Switching models

The model dropdown lets you hot-swap between any provider mid-conversation:

```
claude-sonnet-4-6        → Anthropic (direct)
gpt-4o                   → OpenAI (direct)
gemini-2.5-flash         → Google (OpenAI-compat endpoint)
llama3.2                 → Ollama (local, no API key needed)
anthropic/claude-opus-4-8 → OpenRouter (300+ models, one key)
```

---

## API Reference

### Chat

```http
POST /chat/stream
Content-Type: application/json

{
  "message": "Explain transformers in simple terms",
  "model": "claude-sonnet-4-6",
  "conversation_id": "optional-uuid"
}
```

Returns a Server-Sent Events stream of `text_delta`, `stop`, and `error` events.

### Agent

```http
POST /agents/run/stream
Content-Type: application/json

{
  "goal": "Search for the top 5 AI companies by valuation and write a comparison report",
  "model": "claude-sonnet-4-6",
  "multi_agent": false
}
```

Returns an SSE stream of `step_start`, `text_delta`, `tool_call`, `tool_result`, `step_end`, `done`, and `error` events.

### Conversations

```http
GET    /conversations           # list all
POST   /conversations           # create
GET    /conversations/{id}      # get with turns
PATCH  /conversations/{id}      # rename / update
DELETE /conversations/{id}      # delete
```

### Memory

```http
POST /memory/add                # store a document
POST /memory/search             # semantic search
GET  /memory/episodes           # past agent run summaries
GET  /memory/stats              # document counts
```

---

## Adding a Custom Tool

Any Python function decorated with `@tool` is automatically registered and exposed to all LLMs:

```python
# backend/tools/my_tools.py
from backend.tools.registry import tool

@tool(description="Convert currency using live exchange rates.")
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    # your implementation
    ...
```

Then import it in `backend/tools/__init__.py`:

```python
from backend.tools import my_tools  # triggers registration
```

The tool schema (name, description, parameter types) is auto-generated from the function signature and injected into every LLM call that needs it.

---

## Adding a Custom LLM Provider

Subclass `BaseLLMAdapter` and implement `stream()` and `complete()`:

```python
# backend/adapters/my_provider.py
from backend.adapters.base import BaseLLMAdapter, Message, StreamEvent, CompletionResult

class MyProviderAdapter(BaseLLMAdapter):
    provider = "myprovider"

    async def stream(self, messages, tools=None, system=None, **kwargs):
        # yield StreamEvent objects
        ...

    async def complete(self, messages, tools=None, system=None, **kwargs) -> CompletionResult:
        ...
```

Then register the prefix in `backend/adapters/__init__.py`:

```python
_REGISTRY["myprovider"] = MyProviderAdapter
```

---

## Project Structure

```
llm-orchestration/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # Settings (pydantic-settings + .env)
│   ├── adapters/                   # LLM provider adapters
│   │   ├── base.py                 # BaseLLMAdapter interface
│   │   ├── anthropic_adapter.py    # Claude (native streaming)
│   │   ├── openai_adapter.py       # GPT-4o, o3
│   │   ├── gemini_adapter.py       # Gemini 2.5 (OpenAI-compat)
│   │   ├── ollama_adapter.py       # Any local Ollama model
│   │   └── openrouter_adapter.py   # 300+ models via OpenRouter
│   ├── orchestration/
│   │   ├── agent.py                # Single agent loop (Plan→Act→Observe→Reflect)
│   │   ├── multi_agent.py          # Manager + specialist topology
│   │   └── context_manager.py      # Token budget + sliding window compression
│   ├── tools/
│   │   ├── registry.py             # @tool decorator + schema generation + execute_tool()
│   │   ├── web_search.py           # web_search, fetch_url (Tavily)
│   │   ├── code_executor.py        # run_python, pip_install (sandboxed subprocess)
│   │   ├── file_system.py          # read/write/append/list/delete (artifacts dir)
│   │   ├── http_client.py          # http_get, http_post
│   │   └── utility.py              # calculator, get_datetime, format_json
│   ├── memory/
│   │   ├── vector_store.py         # ChromaDB interface (add, search, delete)
│   │   └── episodic.py             # Agent run summaries — save and recall
│   ├── db/
│   │   ├── models.py               # SQLModel: Conversation, Turn, AgentRun
│   │   └── database.py             # SQLite engine + session factory
│   └── api/
│       ├── chat.py                 # POST /chat/stream, POST /chat
│       ├── conversations.py        # CRUD /conversations
│       ├── agents.py               # POST /agents/run/stream, GET /agents/tools
│       └── memory.py               # POST /memory/search, GET /memory/episodes
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── types.ts
│       ├── components/
│       │   ├── Chat.tsx            # Message list, input, SSE consumer
│       │   ├── Sidebar.tsx         # Conversation history + CRUD
│       │   ├── MessageBubble.tsx   # Markdown rendering + agent trace
│       │   ├── AgentTrace.tsx      # Collapsible tool call viewer
│       │   └── ModelSelector.tsx   # Model dropdown + Chat/Agent toggle
│       └── hooks/
│           └── useConversations.ts
├── data/                           # Auto-created: SQLite DB, ChromaDB, artifacts
├── .env.example
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile.backend
└── start.sh
```

---

## Cloud Deployment

The app is stateless except for `./data/`. To deploy:

1. Replace SQLite with Postgres: change `DB_PATH` to a Postgres URL in `config.py`
2. Replace embedded ChromaDB with Qdrant: swap `vector_store.py`
3. Build and deploy with Docker Compose:

```bash
docker compose up --build
```

Or push to [Fly.io](https://fly.io):

```bash
fly launch
fly secrets set ANTHROPIC_API_KEY=sk-ant-...
fly deploy
```

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design, layer diagrams, data flow, and design decision rationale.

---

## License

MIT
