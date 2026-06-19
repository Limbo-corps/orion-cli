# services/agent_service.py

import os

from groq import Groq

from services.base import BaseService

from events.base import Event
from events.events import (
    TranscriptGeneratedEvent,
    ResponseGeneratedEvent,
    PipelineFailedEvent,
)


class AgentService(BaseService):
    service_name = "agent"

    subscribed_events = [
        TranscriptGeneratedEvent,
    ]

    def __init__(self):
        super().__init__()

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

    async def handle(self, event: Event) -> None:
        try:
            assert isinstance(
                event,
                TranscriptGeneratedEvent,
            )

            response = await self.generate_response(
                event.text
            )

            await self.publish(
                ResponseGeneratedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Response generated",
                    text=response,
                )
            )

        except Exception as e:
            await self.publish(
                PipelineFailedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Agent processing failed",
                    error=str(e),
                )
            )

    async def generate_response(
        self,
        prompt: str,
    ) -> str:

        completion = (
            self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
        )

        return completion.choices[0].message.content