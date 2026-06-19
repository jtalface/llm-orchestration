from __future__ import annotations
import uuid
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import settings


_client: Optional[chromadb.ClientAPI] = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _get_collection(name: str) -> chromadb.Collection:
    return _get_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


class VectorStore:
    """
    Thin wrapper around ChromaDB for semantic storage and retrieval.
    Supports multiple named collections (one per conversation, one for episodic, etc.)
    """

    def __init__(self, collection_name: str = "default"):
        self.collection_name = collection_name

    @property
    def _collection(self) -> chromadb.Collection:
        return _get_collection(self.collection_name)

    def add(
        self,
        text: str,
        metadata: Optional[dict] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """Store a text document with optional metadata. Returns the doc_id."""
        doc_id = doc_id or str(uuid.uuid4())
        self._collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )
        return doc_id

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        """
        Semantic search. Returns list of dicts with keys:
        id, text, metadata, distance
        """
        kwargs: dict = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where

        try:
            results = self._collection.query(**kwargs)
        except Exception:
            return []

        output = []
        for i in range(len(results["ids"][0])):
            output.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return output

    def delete(self, doc_id: str) -> None:
        self._collection.delete(ids=[doc_id])

    def count(self) -> int:
        return self._collection.count()

    def clear(self) -> None:
        _get_client().delete_collection(self.collection_name)


# Shared named stores
episodic_store = VectorStore("episodic_memory")
knowledge_store = VectorStore("knowledge_base")
