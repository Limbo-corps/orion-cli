# integrations/_mcp/discovery.py

from __future__ import annotations

from typing import Any


def mcp_tools_to_openai(list_tools_result: Any) -> list[dict[str, Any]]:
    """
    Convert an MCP `list_tools()` result into OpenAI/Groq function-tool schemas.
    """
    schemas: list[dict[str, Any]] = []

    for tool in list_tools_result.tools:
        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema
                    or {"type": "object", "properties": {}},
                },
            }
        )

    return schemas
