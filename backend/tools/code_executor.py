import asyncio
import sys
import os
import tempfile
from pathlib import Path
from backend.tools.registry import tool
from backend.config import settings


@tool(description="Execute Python code in a sandboxed subprocess. Returns stdout, stderr, and any errors.")
async def run_python(code: str, timeout: int = 30) -> str:
    """
    Run Python code safely in a subprocess with a timeout.
    The code runs in an isolated temp directory.
    Returns stdout + stderr combined.
    """
    artifacts_dir = Path(settings.artifacts_path)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        dir=artifacts_dir,
        delete=False,
        prefix="exec_",
    ) as f:
        f.write(code)
        script_path = f.name

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(artifacts_dir),
            env={**os.environ, "PYTHONPATH": ""},
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return f"[timeout] Code execution exceeded {timeout}s limit."

        parts = []
        if stdout:
            parts.append(stdout.decode(errors="replace").strip())
        if stderr:
            parts.append(f"[stderr]\n{stderr.decode(errors='replace').strip()}")
        if proc.returncode != 0 and not stderr:
            parts.append(f"[exit code {proc.returncode}]")

        return "\n".join(parts) or "(no output)"

    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


@tool(description="Install a Python package using pip. Returns installation output.")
async def pip_install(package: str) -> str:
    """Install a Python package via pip."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "pip", "install", package, "--quiet",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    if proc.returncode == 0:
        return f"Successfully installed {package}."
    return f"Failed to install {package}:\n{stderr.decode(errors='replace')}"
