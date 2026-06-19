import json as json_module
from typing import Optional
import httpx
from backend.tools.registry import tool


@tool(description="Make an HTTP GET request to any URL and return the response body.")
async def http_get(url: str, headers: Optional[str] = None) -> str:
    """Make an HTTP GET request. headers should be a JSON string if provided."""
    hdrs = {}
    if headers:
        try:
            hdrs = json_module.loads(headers)
        except json_module.JSONDecodeError:
            return "Error: headers must be a valid JSON string"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=hdrs)
            return _format_response(resp)
        except Exception as e:
            return f"Request failed: {e}"


@tool(description="Make an HTTP POST request with a JSON body. Returns the response.")
async def http_post(url: str, body: str, headers: Optional[str] = None) -> str:
    """Make an HTTP POST request. body and headers should be JSON strings."""
    hdrs = {"Content-Type": "application/json"}
    if headers:
        try:
            hdrs.update(json_module.loads(headers))
        except json_module.JSONDecodeError:
            return "Error: headers must be a valid JSON string"

    try:
        payload = json_module.loads(body)
    except json_module.JSONDecodeError:
        return "Error: body must be a valid JSON string"

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.post(url, json=payload, headers=hdrs)
            return _format_response(resp)
        except Exception as e:
            return f"Request failed: {e}"


def _format_response(resp: httpx.Response) -> str:
    lines = [f"Status: {resp.status_code}"]
    content_type = resp.headers.get("content-type", "")
    if "json" in content_type:
        try:
            data = resp.json()
            body = json_module.dumps(data, indent=2)[:6000]
        except Exception:
            body = resp.text[:6000]
    else:
        body = resp.text[:6000]
    lines.append(body)
    if len(resp.text) > 6000:
        lines.append(f"[truncated — {len(resp.text)} chars total]")
    return "\n".join(lines)
