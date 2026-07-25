# integrations/_mcp/langchain_tools.py

from __future__ import annotations

import json
import os
from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection, StdioConnection


def _project_root() -> Path:
    """
    Determine the ORION project root deterministically, independent of the
    current working directory: walk up from this file until a project marker
    (pyproject.toml or .git) is found. Falls back to the cwd.
    """
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def _resolve(value: str) -> str:
    """
    Expand config placeholders so paths are never hardcoded to one machine:

    - ``${PROJECT_ROOT}`` -> the ORION project root, found from the code's own
      location (correct no matter which directory you launch from).
    - ``${CWD}`` / ``${PWD}`` -> the current working directory.
    - ``$VAR`` / ``${VAR}``   -> the matching environment variable.

    This lets `mcp.json` ship a portable value that resolves to whatever
    machine and directory the product actually runs in.
    """
    root = str(_project_root())
    cwd = str(Path.cwd())
    value = (
        value.replace("${PROJECT_ROOT}", root)
        .replace("${CWD}", cwd)
        .replace("${PWD}", cwd)
    )
    return os.path.expandvars(value)


async def load_mcp_tools(config_path: str | Path = "mcp.json") -> list[BaseTool]:
    """
    Load tools from every enabled MCP server declared in `mcp.json` and return
    them as LangChain BaseTools, ready for `llm.bind_tools(...)` and `ToolNode`.

    Config format (Claude-Desktop style):

        {
          "mcpServers": {
            "<name>": {
              "command": "npx",
              "args": ["-y", "@modelcontextprotocol/server-filesystem", "${CWD}"],
              "env": {"KEY": "value"},
              "enabled": true,
              "tools": ["read_text_file", "list_directory"]
            }
          }
        }

    Placeholders in "args" (``${CWD}`` / ``${PWD}`` / ``$VAR``) are expanded at
    runtime, so paths adapt to the machine ORION runs on instead of being
    hardcoded.

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

    connections: dict[str, Connection] = {}
    allowlist: set[str] = set()

    for name, spec in raw.get("mcpServers", {}).items():
        if not spec.get("enabled", True):
            continue

        connection: Connection = StdioConnection(
            transport="stdio",
            command=spec["command"],
            args=[_resolve(str(arg)) for arg in spec.get("args", [])],
            env=spec.get("env") or None,
        )

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
