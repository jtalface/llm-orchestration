import os
from pathlib import Path
from backend.tools.registry import tool
from backend.config import settings


def _safe_path(path: str) -> Path:
    """Resolve path and ensure it stays within the artifacts directory."""
    base = Path(settings.artifacts_path).resolve()
    target = (base / path).resolve()
    if not str(target).startswith(str(base)):
        raise PermissionError(
            f"Path {path!r} resolves outside artifacts directory. "
            f"All file operations are restricted to {base}"
        )
    return target


@tool(description="Read the contents of a file. Path is relative to the artifacts directory.")
async def read_file(path: str) -> str:
    """Read a file from the artifacts directory."""
    target = _safe_path(path)
    if not target.exists():
        return f"File not found: {path}"
    if not target.is_file():
        return f"Not a file: {path}"
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        if len(content) > 20_000:
            return content[:20_000] + f"\n\n[truncated — file is {len(content)} chars total]"
        return content
    except Exception as e:
        return f"Error reading {path}: {e}"


@tool(description="Write content to a file. Path is relative to the artifacts directory. Creates directories as needed.")
async def write_file(path: str, content: str) -> str:
    """Write content to a file in the artifacts directory."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Written {len(content)} characters to {path}"


@tool(description="Append content to an existing file. Creates the file if it doesn't exist.")
async def append_file(path: str, content: str) -> str:
    """Append content to a file in the artifacts directory."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as f:
        f.write(content)
    return f"Appended {len(content)} characters to {path}"


@tool(description="List files and directories at a path. Path is relative to the artifacts directory.")
async def list_directory(path: str = ".") -> str:
    """List contents of a directory in the artifacts directory."""
    target = _safe_path(path)
    if not target.exists():
        return f"Directory not found: {path}"
    if not target.is_dir():
        return f"Not a directory: {path}"

    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
    lines = []
    for entry in entries:
        if entry.is_dir():
            lines.append(f"[dir]  {entry.name}/")
        else:
            size = entry.stat().st_size
            lines.append(f"[file] {entry.name}  ({size:,} bytes)")

    return "\n".join(lines) if lines else "(empty directory)"


@tool(description="Delete a file. Path is relative to the artifacts directory.", requires_confirmation=True)
async def delete_file(path: str) -> str:
    """Delete a file from the artifacts directory."""
    target = _safe_path(path)
    if not target.exists():
        return f"File not found: {path}"
    target.unlink()
    return f"Deleted {path}"
