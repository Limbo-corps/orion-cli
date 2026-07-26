"""
Audio transcription for the voice pipeline.

The client records audio and sends the runtime a file path over IPC; the
runtime transcribes it here (Groq Whisper) and feeds the text into the normal
chat pipeline. The backend never touches a microphone — it only reads the file
the client produced.
"""

from __future__ import annotations

import asyncio
import os

from groq import Groq

#: Groq speech-to-text model used for transcription.
_MODEL = "whisper-large-v3-turbo"


async def transcribe_audio(path: str) -> str:
    """
    Transcribe the audio file at ``path`` to text.

    Runs the blocking Groq call in a worker thread so the event loop stays
    responsive.
    """
    return await asyncio.to_thread(_transcribe_sync, path)


def _transcribe_sync(path: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    with open(path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=audio_file,
            model=_MODEL,
        )

    return result.text
