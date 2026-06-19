# Import all tool modules to trigger @tool registration
from backend.tools import web_search, code_executor, file_system, http_client, utility
from backend.tools.registry import (
    tool, get_tool, get_all_tools, get_tool_schemas,
    get_tool_schemas_for, execute_tool, ToolDefinition,
)

__all__ = [
    "tool", "get_tool", "get_all_tools", "get_tool_schemas",
    "get_tool_schemas_for", "execute_tool", "ToolDefinition",
]
