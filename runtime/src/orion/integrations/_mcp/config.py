from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


MCPTransport = Literal["stdio", "http"]


@dataclass(slots=True, frozen=True)
class MCPServerConfig:
    """
    Configuration for a single MCP server.
    """

    name: str

    transport: MCPTransport = "stdio"

    # stdio configuration
    command: str | None = None
    args: list[str] = field(default_factory=list)

    # HTTP configuration
    url: str | None = None

    # Common configuration
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass(slots=True, frozen=True)
class MCPConfig:
    """
    Configuration for all MCP servers.
    """

    servers: list[MCPServerConfig] = field(default_factory=list)


def _resolve_value(
    value: str,
    *,
    project_root: Path,
) -> str:
    """
    Resolve variables used inside MCP configuration values.

    Supported variables:

        ${PROJECT_ROOT}
        $PROJECT_ROOT

    Environment variables are also expanded.
    """

    value = value.replace(
        "${PROJECT_ROOT}",
        str(project_root),
    )

    value = value.replace(
        "$PROJECT_ROOT",
        str(project_root),
    )

    return os.path.expandvars(value)


def load_config(
    path: str | Path = "mcp.json",
) -> MCPConfig:
    """
    Load MCP server configuration from mcp.json.

    Supported transports:

    stdio:
        {
            "command": "npx",
            "args": [...]
        }

    http:
        {
            "type": "http",
            "url": "https://..."
        }

    Configuration values may use:

        ${PROJECT_ROOT}

    which resolves to the directory containing mcp.json.
    """

    config_path = Path(path).resolve()

    if not config_path.exists():
        return MCPConfig()

    raw = json.loads(
        config_path.read_text(),
    )

    project_root = config_path.parent

    servers: list[MCPServerConfig] = []

    for name, spec in raw.get(
        "mcpServers",
        {},
    ).items():

        transport: MCPTransport = spec.get(
            "type",
            "stdio",
        )

        if transport not in {"stdio", "http"}:
            raise ValueError(
                f"Unsupported MCP transport "
                f"'{transport}' for server '{name}'."
            )

        command = spec.get("command")

        if command is not None:
            command = _resolve_value(
                command,
                project_root=project_root,
            )

        args = [
            _resolve_value(
                arg,
                project_root=project_root,
            )
            for arg in spec.get(
                "args",
                [],
            )
        ]

        url = spec.get("url")

        if url is not None:
            url = _resolve_value(
                url,
                project_root=project_root,
            )

        env = {
            key: _resolve_value(
                value,
                project_root=project_root,
            )
            for key, value in spec.get(
                "env",
                {},
            ).items()
        }

        servers.append(
            MCPServerConfig(
                name=name,
                transport=transport,
                command=command,
                args=args,
                url=url,
                env=env,
                enabled=spec.get(
                    "enabled",
                    True,
                ),
            )
        )

    return MCPConfig(
        servers=servers,
    )
