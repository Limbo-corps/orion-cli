# integrations/_mcp/config.py

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class MCPServerConfig:
    """
    Configuration for a single MCP server.
    """

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass(slots=True, frozen=True)
class MCPConfig:
    """
    Configuration for all MCP servers.
    """

    servers: list[MCPServerConfig] = field(default_factory=list)


def load_config(path: str | Path = "mcp.json") -> MCPConfig:
    """
    Build an MCPConfig from a Claude-Desktop-style JSON file:

        { "mcpServers": { "<name>": { "command": ..., "args": [...], "env": {...}, "enabled": true } } }
    """
    p = Path(path)
    if not p.exists():
        return MCPConfig(servers=[])

    raw = json.loads(p.read_text())

    servers = [
        MCPServerConfig(
            name=name,
            command=spec["command"],
            args=spec.get("args", []),
            env=spec.get("env", {}),
            enabled=spec.get("enabled", True),
        )
        for name, spec in raw.get("mcpServers", {}).items()
    ]

    return MCPConfig(servers=servers)
