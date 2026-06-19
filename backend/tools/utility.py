import math
import json as json_module
from datetime import datetime, timezone
from backend.tools.registry import tool


@tool(description="Evaluate a mathematical expression. Safe subset of Python math.")
def calculator(expression: str) -> str:
    """Safely evaluate a math expression like '2 ** 10', 'sqrt(144)', etc."""
    allowed = {
        k: v for k, v in math.__dict__.items()
        if not k.startswith("_")
    }
    allowed.update({"abs": abs, "round": round, "int": int, "float": float})
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error evaluating {expression!r}: {e}"


@tool(description="Get the current date and time in UTC.")
def get_datetime() -> str:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc).isoformat()


@tool(description="Parse and pretty-print a JSON string.")
def format_json(json_string: str) -> str:
    """Pretty-print a JSON string."""
    try:
        data = json_module.loads(json_string)
        return json_module.dumps(data, indent=2)
    except json_module.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
