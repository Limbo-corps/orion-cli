from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.tools import BaseTool
from pydantic import ConfigDict, PrivateAttr

from orion.integrations._mcp.manager import MCPManager


class MCPTool(BaseTool):
    """
    Thin LangChain adapter around an MCP tool.

    MCPManager owns:
        - MCP server lifecycle
        - tool discovery
        - MCP protocol communication
        - tool execution

    MCPTool only adapts an MCP tool to the LangChain/LangGraph
    tool interface.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _manager: MCPManager = PrivateAttr()
    _parameters: dict[str, Any] = PrivateAttr()
    _session_id: UUID = PrivateAttr()
    _correlation_id: UUID = PrivateAttr()

    def __init__(
        self,
        manager: MCPManager,
        *,
        name: str,
        description: str,
        parameters: dict[str, Any],
        session_id: UUID,
        correlation_id: UUID,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
        )

        self._manager = manager
        self._parameters = parameters
        self._session_id = session_id
        self._correlation_id = correlation_id

    @property
    def args(self) -> dict[str, Any]:
        """
        Return the original MCP JSON schema unchanged.

        LangGraph/LangChain can use this to expose the exact
        schema supplied by the MCP server.
        """
        return self._parameters

    def _run(
        self,
        **kwargs: Any,
    ) -> str:
        raise NotImplementedError(
            "MCPTool only supports asynchronous execution."
        )

    async def _arun(
        self,
        **kwargs: Any,
    ) -> str:
        return await self._manager.call_tool(
            self.name,
            kwargs,
            session_id=self._session_id,
            correlation_id=self._correlation_id,
        )


def create_mcp_tools(
    manager: MCPManager,
    *,
    session_id: UUID,
    correlation_id: UUID,
) -> list[MCPTool]:
    """
    Convert MCPManager's discovered tools into LangChain tools.

    The MCP JSON schema is preserved exactly. No Pydantic model
    or schema transformation is performed.
    """

    tools: list[MCPTool] = []

    for schema in manager.tools:
        function = schema["function"]

        name = function["name"]
        description = function.get("description", "")

        parameters = function.get(
            "parameters",
            {
                "properties": {},
                "type": "object",
            },
        )

        tools.append(
            MCPTool(
                manager,
                name=name,
                description=description,
                parameters=parameters,
                session_id=session_id,
                correlation_id=correlation_id,
            )
        )

    return tools
