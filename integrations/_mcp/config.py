# integrations/mcp/config.py

from __future__ import annotations

from dataclasses import dataclass, field


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
