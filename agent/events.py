from events.base import Event, EventStatus


class PromptBuiltEvent(Event):
    """
    Final prompt rendered and sent to the LLM.
    """

    status: EventStatus = EventStatus.INFO

    prompt: str


class AgentReasoningStartedEvent(Event):
    """
    Agent has started reasoning.
    """

    status: EventStatus = EventStatus.INFO


class AgentReasoningCompletedEvent(Event):
    """
    Agent finished reasoning.
    """

    status: EventStatus = EventStatus.SUCCESS

    response: str


class AgentReasoningFailedEvent(Event):
    """
    Agent reasoning failed.
    """

    status: EventStatus = EventStatus.ERROR

    error: str


class ToolCallRequestedEvent(Event):
    """
    The LLM requested one or more tool calls.
    """

    status: EventStatus = EventStatus.INFO

    tool_names: list[str]


class ToolCallCompletedEvent(Event):
    """
    Tool execution completed.
    """

    status: EventStatus = EventStatus.SUCCESS

    tool_names: list[str]


class ToolCallFailedEvent(Event):
    """
    Tool execution failed.
    """

    status: EventStatus = EventStatus.ERROR

    tool_name: str
    error: str
