"""
Episodic memory: store summaries of completed agent runs so future runs
can learn from them. "Last time I tried X it failed because..."
"""
from datetime import datetime, timezone
from typing import Optional
from backend.memory.vector_store import episodic_store


def save_episode(
    goal: str,
    summary: str,
    outcome: str,  # "success" | "failure" | "partial"
    model: str,
    steps_taken: int,
    run_id: Optional[str] = None,
) -> str:
    """Store a completed agent run summary for future retrieval."""
    doc = f"Goal: {goal}\n\nOutcome: {outcome}\n\nSummary: {summary}"
    metadata = {
        "goal": goal[:500],
        "outcome": outcome,
        "model": model,
        "steps_taken": steps_taken,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if run_id:
        metadata["run_id"] = run_id

    return episodic_store.add(text=doc, metadata=metadata, doc_id=run_id)


def recall_similar_episodes(query: str, n: int = 3) -> list[dict]:
    """Find past agent runs similar to the current goal."""
    return episodic_store.search(query=query, n_results=n)


def format_episode_context(query: str, n: int = 3) -> str:
    """Return a formatted string of relevant past episodes for the system prompt."""
    episodes = recall_similar_episodes(query, n=n)
    if not episodes:
        return ""

    lines = ["## Relevant past experience:"]
    for ep in episodes:
        meta = ep["metadata"]
        lines.append(
            f"- [{meta.get('outcome', '?')}] {meta.get('goal', ep['text'][:100])}"
            f" ({meta.get('steps_taken', '?')} steps, {meta.get('timestamp', '')[:10]})"
        )
        # Add the summary if meaningfully different from the title
        summary_start = ep["text"].find("Summary:")
        if summary_start != -1:
            summary = ep["text"][summary_start + 8:].strip()[:300]
            lines.append(f"  → {summary}")
    return "\n".join(lines)
