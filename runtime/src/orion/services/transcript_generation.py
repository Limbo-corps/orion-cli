# import asyncio
# import os

# from groq import Groq

# from orion.services.base import BaseService

# from orion.events.base import Event
# from orion.events.events import (
#     VoiceRecordingCompletedEvent,
#     TranscriptGeneratedEvent,
#     TranscriptGenerationFailedEvent,
#     SilenceDetectedEvent,
# )


# # Phrases Whisper commonly hallucinates from near-silence / ambient noise.
# # Compared after lowercasing and stripping surrounding punctuation/space.
# _JUNK_PHRASES = {
#     "",
#     "you",
#     "thank you",
#     "thanks",
#     "thanks for watching",
#     "thank you for watching",
#     "please subscribe",
#     "subscribe",
#     "bye",
#     "goodbye",
#     "good luck with you",
#     "okay",
#     "ok",
#     "yeah",
#     "uh",
#     "um",
#     "hmm",
#     "so",
#     "the",
#     "you're welcome",
#     "i'm sorry",
# }

# # Transcripts shorter than this (after normalization) are treated as noise.
# _MIN_TRANSCRIPT_CHARS = 2


# def is_junk_transcript(text: str) -> bool:
#     """
#     True when a transcript is almost certainly a Whisper silence
#     hallucination rather than real speech, so we can skip the
#     (expensive) agent + memory pipeline entirely.
#     """
#     normalized = text.strip().lower().strip(" .!?,…\"'")

#     if len(normalized) < _MIN_TRANSCRIPT_CHARS:
#         return True

#     return normalized in _JUNK_PHRASES


# class TranscriptGenerationService(BaseService):
#     service_name = "transcript_generation"

#     subscribed_events = [
#         VoiceRecordingCompletedEvent,
#     ]

#     def __init__(self):
#         super().__init__()

#         self.client = Groq(
#             api_key=os.getenv("GROQ_API_KEY"),
#         )

#     async def handle(
#         self,
#         event: Event,
#     ) -> None:

#         try:
#             assert isinstance(
#                 event,
#                 VoiceRecordingCompletedEvent,
#             )

#             transcript = await self.transcribe(
#                 str(event.audio_path),
#             )

#             #
#             # Guard: Whisper hallucinates phantom phrases ("Thank you.",
#             # ".", "you") on near-silence. Running the agent + memory
#             # pipeline on those wastes a large number of LLM tokens, so
#             # we drop them here and let the loop simply listen again.
#             #
#             if is_junk_transcript(transcript):
#                 await self.publish(
#                     SilenceDetectedEvent(
#                         session_id=event.session_id,
#                         correlation_id=event.correlation_id,
#                         source=self.service_name,
#                         message="Ignored non-speech transcript",
#                     )
#                 )
#                 return

#             await self.publish(
#                 TranscriptGeneratedEvent(
#                     session_id=event.session_id,
#                     correlation_id=event.correlation_id,
#                     source=self.service_name,
#                     message="Transcript generated",
#                     text=transcript,
#                 )
#             )

#         except Exception as e:
#             await self.publish(
#                 TranscriptGenerationFailedEvent(
#                     session_id=event.session_id,
#                     correlation_id=event.correlation_id,
#                     source=self.service_name,
#                     message="Transcript generation failed",
#                     error=str(e),
#                 )
#             )

#     async def transcribe(
#         self,
#         audio_path: str,
#     ) -> str:

#         return await asyncio.to_thread(
#             self._transcribe_sync,
#             audio_path,
#         )

#     def _transcribe_sync(
#         self,
#         audio_path: str,
#     ) -> str:

#         with open(audio_path, "rb") as audio_file:
#             transcription = self.client.audio.transcriptions.create(
#                 file=audio_file,
#                 model="whisper-large-v3-turbo",
#             )

#         return transcription.text
