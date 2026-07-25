from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================
# Event Status
# ============================================================


class EventStatus(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


# ============================================================
# Base Event
# ============================================================


class Event(BaseModel):
    """
    Base class for all Orion domain events.

    Every event represents something that has occurred within the runtime
    and carries common metadata used for routing, tracing, logging, and
    correlation.
    """

    #: Unique identifier for this event instance.
    event_id: UUID = Field(default_factory=uuid4)

    #: Correlates related events belonging to the same workflow/request.
    correlation_id: UUID

    #: Client session that originated the event.
    session_id: UUID

    #: Time at which the event was created.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    #: Component or service that published the event.
    source: str

    #: Human-readable description of the event.
    message: str = ""

    #: Severity of the event.
    status: EventStatus = EventStatus.INFO
