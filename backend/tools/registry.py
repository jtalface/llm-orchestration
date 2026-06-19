import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Optional, get_type_hints
from functools import wraps


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON schema
    fn: Callable
    is_async: bool
    requires_confirmation: bool = False  # prompt user before running (for dangerous tools)


_REGISTRY: dict[str, ToolDefinition] = {}


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    requires_confirmation: bool = False,
):
    """
    Decorator that registers a function as a callable tool.

    Usage:
        @tool(description="Search the web for current information")
        async def web_search(query: str, max_results: int = 5) -> str:
            ...
    """
    def decorator(fn: Callable) -> Callable:
        tool_name = name or fn.__name__
        tool_desc = description or (inspect.getdoc(fn) or "")

        schema = _build_json_schema(fn)

        td = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            parameters=schema,
            fn=fn,
            is_async=inspect.iscoroutinefunction(fn),
            requires_confirmation=requires_confirmation,
        )
        _REGISTRY[tool_name] = td

        @wraps(fn)
        async def wrapper(*args, **kwargs):
            if td.is_async:
                return await fn(*args, **kwargs)
            return fn(*args, **kwargs)

        wrapper._tool_def = td
        return wrapper

    return decorator


def _build_json_schema(fn: Callable) -> dict:
    """Auto-generate a JSON Schema from Python function signature."""
    sig = inspect.signature(fn)
    try:
        hints = get_type_hints(fn)
    except Exception:
        hints = {}

    properties = {}
    required = []

    _type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        annotation = hints.get(param_name, str)
        json_type = _type_map.get(annotation, "string")

        prop: dict[str, Any] = {"type": json_type}

        # Pull inline description from param default if it's a string marker
        # (allows: query: str = "The search query to use")
        if isinstance(param.default, str) and param.default.startswith("__desc__:"):
            prop["description"] = param.default[9:]

        properties[param_name] = prop

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def get_tool(name: str) -> Optional[ToolDefinition]:
    return _REGISTRY.get(name)


def get_all_tools() -> list[ToolDefinition]:
    return list(_REGISTRY.values())


def get_tool_schemas() -> list[dict]:
    """Return normalized schemas for all registered tools (LLM-ready)."""
    return [
        {
            "name": td.name,
            "description": td.description,
            "parameters": td.parameters,
        }
        for td in _REGISTRY.values()
    ]


def get_tool_schemas_for(names: list[str]) -> list[dict]:
    """Return schemas for a specific subset of tools."""
    return [
        {
            "name": td.name,
            "description": td.description,
            "parameters": td.parameters,
        }
        for name in names
        if (td := _REGISTRY.get(name))
    ]


async def execute_tool(name: str, arguments: dict) -> Any:
    """Look up and run a tool by name with the given arguments."""
    td = _REGISTRY.get(name)
    if td is None:
        raise ValueError(f"Unknown tool: {name!r}. Available: {list(_REGISTRY.keys())}")

    try:
        if td.is_async:
            result = await td.fn(**arguments)
        else:
            result = td.fn(**arguments)
        return result
    except TypeError as e:
        raise ValueError(f"Tool {name!r} called with wrong arguments: {e}") from e
