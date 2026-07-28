use std::path::Path;

use crate::ipc::{
    client_session::ClientSession,
    error::IpcError,
    events::RuntimeEvent,
    messages::{
        AssistantChunkPayload, Envelope, ErrorPayload, MessageType, StatusPayload,
        SubmitPromptPayload,
    },
};

/// High-level IPC client used by the TUI.
pub struct OrionClient {
    session: ClientSession,
}

impl OrionClient {
    /// Connect to the Orion runtime.
    pub async fn connect<P: AsRef<Path>>(path: P) -> Result<Self, IpcError> {
        let session = ClientSession::connect(path).await?;

        Ok(Self { session })
    }

    /// Returns the session ID.
    pub fn id(&self) -> uuid::Uuid {
        self.session.id()
    }

    /// Send a prompt to the runtime.
    pub async fn send_prompt(&mut self, prompt: impl Into<String>) -> Result<(), IpcError> {
        let envelope = Envelope::submit_prompt(prompt);
        self.session.send(&envelope).await
    }

    /// Announce the start of a voice recording (metadata only).
    pub async fn send_voice_start(
        &mut self,
        sample_rate: u32,
        channels: u32,
    ) -> Result<(), IpcError> {
        self.session
            .send(&Envelope::voice_start(sample_rate, channels))
            .await
    }

    /// Finish a recording by sending the runtime the recorded file path.
    pub async fn send_voice_end(&mut self, path: impl Into<String>) -> Result<(), IpcError> {
        self.session.send(&Envelope::voice_end(path)).await
    }

    /// Send a ping message.
    pub async fn ping(&mut self) -> Result<(), IpcError> {
        self.session.send(&Envelope::ping()).await
    }

    /// Wait for the next runtime event.
    pub async fn next_event(&mut self) -> Result<RuntimeEvent, IpcError> {
        let envelope = self.session.receive().await?;

        let event = match envelope.message_type {
            MessageType::AssistantStart => RuntimeEvent::AssistantStart,

            MessageType::AssistantChunk => {
                let payload: AssistantChunkPayload = envelope.payload()?;
                RuntimeEvent::AssistantChunk(payload.text)
            }

            MessageType::AssistantEnd => RuntimeEvent::AssistantEnd,

            // The runtime echoes the pipeline's user text back — a typed prompt
            // or a transcribed voice message. Shown as the user's turn.
            MessageType::SubmitPrompt => {
                let payload: SubmitPromptPayload = envelope.payload()?;
                RuntimeEvent::UserPrompt(payload.text)
            }

            MessageType::Status => {
                let payload: StatusPayload = envelope.payload()?;
                RuntimeEvent::Status(payload.message)
            }

            MessageType::Error => {
                let payload: ErrorPayload = envelope.payload()?;

                RuntimeEvent::Error {
                    code: payload.code,
                    message: payload.message,
                }
            }

            _ => RuntimeEvent::Unknown(envelope),
        };

        Ok(event)
    }

    /// Close the client connection.
    pub async fn close(self) -> Result<(), IpcError> {
        self.session.close().await
    }
}
