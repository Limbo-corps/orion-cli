# integrations/_mcp/langchain_tools.py

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient


async def load_mcp_tools(config_path: str | Path = "mcp.json") -> list[BaseTool]:
    """
    Load tools from every enabled MCP server declared in `mcp.json` and return
    them as LangChain BaseTools, ready for `llm.bind_tools(...)` and `ToolNode`.

    Config format (Claude-Desktop style):

        {
          "mcpServers": {
            "<name>": {
              "command": "npx",
              "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
              "env": {"KEY": "value"},
              "enabled": true,
              "tools": ["read_text_file", "list_directory"]
            }
          }
        }

    The optional per-server "tools" allowlist keeps only the named tools.
    Every tool schema is sent to the LLM on *every* call, so exposing only
    the few you actually need meaningfully cuts prompt tokens. When no
    server declares "tools", all discovered tools are used.

    Returns an empty list if the config file is missing or has no enabled
    servers, so the agent degrades gracefully to its built-in OrionTools.
    """
    path = Path(config_path)
    if not path.exists():
        return []

    raw = json.loads(path.read_text())

    connections: dict[str, dict] = {}
    allowlist: set[str] = set()

    for name, spec in raw.get("mcpServers", {}).items():
        if not spec.get("enabled", True):
            continue

        connection: dict = {
            "command": spec["command"],
            "args": spec.get("args", []),
            "transport": "stdio",
        }

        env = spec.get("env") or {}
        if env:
            connection["env"] = env

        connections[name] = connection
        allowlist.update(spec.get("tools", []) or [])

    if not connections:
        return []

    client = MultiServerMCPClient(connections)
    tools = await client.get_tools()

    # If any server declared an allowlist, keep only those tools.
    if allowlist:
        tools = [tool for tool in tools if tool.name in allowlist]

    return tools
