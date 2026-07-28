use crate::ipc::messages::Envelope;

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub enum RuntimeEvent {
    Connected,
    Disconnected,

    /// The user's turn text echoed by the runtime — a typed prompt or a
    /// transcribed voice message.
    UserPrompt(String),

    // Assistant
    AssistantStart,
    AssistantChunk(String),
    AssistantEnd,

    // Tools
    ToolStarted {
        name: String,
    },
    ToolFinished {
        name: String,
        success: bool,
    },

    // Runtime
    Status(String),
    Error {
        code: String,
        message: String,
    },

    // Connection
    Ping,
    Pong,

    // Voice (future)
    VoiceStart,
    VoiceChunk {
        sequence: u64,
        bytes: Vec<u8>,
    },
    VoiceEnd,

    // Unknown / unsupported
    Unknown(Envelope),
}
