from events.speech import TranscriptGenerated
from uuid import uuid4

event = TranscriptGenerated(
    correlation_id=uuid4(),
    source="stt",
    text="Hello ORION",
)

print(event)
