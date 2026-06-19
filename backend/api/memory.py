from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.memory.vector_store import VectorStore, episodic_store, knowledge_store
from backend.memory.episodic import recall_similar_episodes

router = APIRouter(prefix="/memory", tags=["memory"])


class AddMemoryRequest(BaseModel):
    text: str
    metadata: Optional[dict] = None
    collection: str = "knowledge_base"


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5
    collection: str = "knowledge_base"


@router.post("/add")
def add_memory(req: AddMemoryRequest):
    store = VectorStore(req.collection)
    doc_id = store.add(text=req.text, metadata=req.metadata)
    return {"id": doc_id, "collection": req.collection}


@router.post("/search")
def search_memory(req: SearchRequest):
    store = VectorStore(req.collection)
    results = store.search(query=req.query, n_results=req.n_results)
    return {"results": results, "count": len(results)}


@router.get("/episodes")
def get_episodes(query: str = "", n: int = 5):
    results = recall_similar_episodes(query or "agent task", n=n)
    return {"results": results}


@router.get("/stats")
def memory_stats():
    return {
        "episodic": episodic_store.count(),
        "knowledge": knowledge_store.count(),
    }
