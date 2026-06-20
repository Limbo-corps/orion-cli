from collections import deque
from pathlib import Path
import asyncio
import wave
import os

import numpy as np
import sounddevice as sd

from services.base import BaseService
from events.base import Event
from events.events import (
    PipelineStartEvent,
    VoiceRecordingStartEvent,
    VoiceRecordingCompletedEvent,
    VoiceRecordingFailedEvent,
    SpeechDetectedEvent,
    SilenceDetectedEvent,
)


class VoiceRecordingService(BaseService):
    service_name = "voice_recording"

    subscribed_events = [
        PipelineStartEvent,
    ]

    def __init__(self):
        super().__init__()
        self.silence_threshold = float(os.getenv("ORION_SILENCE_THRESHOLD", "500"))
        self.hangover_seconds = float(os.getenv("ORION_SILENCE_HANGOVER", "2.0"))
        self.max_duration = float(os.getenv("ORION_MAX_RECORD_SECONDS", "15"))
        self.listen_timeout = float(os.getenv("ORION_LISTEN_TIMEOUT", "2.0"))
        self.min_speech_seconds = float(os.getenv("ORION_MIN_SPEECH_SECONDS", "0.4"))
        self.pre_roll_seconds = float(os.getenv("ORION_PRE_ROLL_SECONDS", "0.3"))

    async def handle(
        self,
        event: Event,
    ) -> None:

        assert isinstance(
            event,
            PipelineStartEvent,
        )

        try:
            await self.publish(
                VoiceRecordingStartEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Recording started",
                )
            )

            audio_path, speech_started, silent_time = await self.record()

            #
            # If no speech was captured, skip the rest of the
            # pipeline so we never send silence to the transcriber
            # (which would hallucinate phantom phrases). The
            # continuous loop will simply start listening again.
            #
            if not speech_started:
                await self.publish(
                    SilenceDetectedEvent(
                        correlation_id=event.correlation_id,
                        source=self.service_name,
                        silence_duration=silent_time,
                        message="No speech detected, skipping pipeline",
                    )
                )
                return

            await self.publish(
                SpeechDetectedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Speech detected",
                )
            )

            await self.publish(
                SilenceDetectedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    silence_duration=silent_time,
                    message="Silence detected, recording stopped",
                )
            )

            await self.publish(
                VoiceRecordingCompletedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    audio_path=audio_path,
                    message=f"Recording completed: {audio_path}",
                )
            )

        except Exception as e:
            await self.publish(
                VoiceRecordingFailedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    error=str(e),
                    message="Voice recording failed",
                )
            )

    async def record(
        self,
        sample_rate: int = 16000,
    ) -> tuple[str | None, bool, float]:

        output_dir = Path("data/audio")

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = output_dir / "input.wav"

        #
        # The VAD loop is blocking, so run it in a worker
        # thread to avoid freezing the async event loop.
        #
        recording, speech_started, silent_time = await asyncio.to_thread(
            self._record_with_vad,
            sample_rate,
        )

        #
        # Nothing was said this cycle: don't write a file, and
        # signal back that there is no audio to process.
        #
        if not speech_started:
            return None, speech_started, silent_time

        with wave.open(
            str(output_path),
            "wb",
        ) as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            wav_file.writeframes(recording.tobytes())

        return str(output_path), speech_started, silent_time

    def _record_with_vad(self, sample_rate: int = 16000):
        """
        Listen to the microphone and only capture actual speech.

        Two phases:

        1. LISTEN  - monitor the mic, measure loudness (RMS), and
                     throw the audio away while it is quiet. Nothing
                     is saved during silence. If no speech begins
                     within `self.listen_timeout`, give up this cycle.
        2. RECORD  - once loudness crosses `self.silence_threshold`,
                     start saving audio and keep going until the
                     speaker is quiet for `self.hangover_seconds`.
                     `self.max_duration` caps the speech length.

        Returns (audio, speech_started, silent_time). When no speech
        was heard, `audio` is empty and `speech_started` is False.
        """

        frame_duration = 0.03  # analyse audio in 30ms chunks
        frame_size = int(sample_rate * frame_duration)

        #
        # Pre-roll buffer: keep the most recent few frames even while
        # listening, so when speech is detected we can rewind and
        # include the soft onset of the first word (no clipped start).
        #
        pre_roll_frames = max(1, int(self.pre_roll_seconds / frame_duration))
        lookback = deque(maxlen=pre_roll_frames)

        frames = []
        speech_started = False
        silent_time = 0.0
        waited_for_speech = 0.0

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        ) as stream:
            while True:
                block, _ = stream.read(frame_size)

                # Loudness of this chunk (root-mean-square energy).
                rms = np.sqrt(np.mean(block.astype(np.float32) ** 2))
                is_speech = rms > self.silence_threshold

                if not speech_started:
                    #
                    # LISTEN phase: buffer recent audio, watch for speech.
                    #
                    lookback.append(block.copy())

                    if is_speech:
                        speech_started = True
                        # Rewind: include the buffered onset frames.
                        frames.extend(lookback)
                    else:
                        waited_for_speech += frame_duration
                        if waited_for_speech >= self.listen_timeout:
                            break  # stayed quiet -> give up this cycle

                else:
                    #
                    # RECORD phase: save audio until the user stops.
                    #
                    frames.append(block.copy())

                    if is_speech:
                        silent_time = 0.0
                    else:
                        silent_time += frame_duration
                        if silent_time >= self.hangover_seconds:
                            break

                    if len(frames) * frame_duration >= self.max_duration:
                        break

        #
        # Treat ultra-short captures (a cough, a click, a stray
        # noise) as "no speech" so they never reach the transcriber.
        #
        recorded_time = len(frames) * frame_duration
        if recorded_time < self.min_speech_seconds:
            speech_started = False

        if speech_started and frames:
            audio = np.concatenate(frames)
        else:
            audio = np.zeros((0, 1), dtype="int16")

        return audio, speech_started, silent_time
