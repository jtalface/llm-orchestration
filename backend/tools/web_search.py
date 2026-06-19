import httpx
from backend.tools.registry import tool
from backend.config import settings


@tool(description="Search the web for current information. Returns titles, URLs, and content snippets.")
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Tavily. Returns relevant results with snippets."""
    if not settings.tavily_api_key:
        return _fallback_search(query)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    lines = []
    if data.get("answer"):
        lines.append(f"Summary: {data['answer']}\n")

    for i, result in enumerate(data.get("results", []), 1):
        lines.append(f"[{i}] {result['title']}")
        lines.append(f"    URL: {result['url']}")
        lines.append(f"    {result.get('content', '')[:400]}")
        lines.append("")

    return "\n".join(lines) or "No results found."


@tool(description="Fetch and read the full text content of a webpage URL.")
async def fetch_url(url: str) -> str:
    """Retrieve the text content of a URL."""
    async with httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LLM-Orchestration/1.0)"},
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text" not in content_type and "json" not in content_type:
            return f"Non-text content at {url} (type: {content_type})"
        # Return first 8000 chars to keep context manageable
        return resp.text[:8000]


def _fallback_search(query: str) -> str:
    return (
        f"[web_search] No TAVILY_API_KEY configured. "
        f"Cannot search for: {query!r}. "
        f"Set TAVILY_API_KEY in .env to enable web search."
    )
