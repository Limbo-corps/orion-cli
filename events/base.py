from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from enum import Enum

# ============================================================
# Event Status
# ============================================================

class EventStatus(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Event(BaseModel):
    """
    The Base Event Implementation
    """

    event_id: UUID = Field(default_factory=uuid4)
    status: str = EventStatus.INFO
    correlation_id: UUID
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    message: str = ""
