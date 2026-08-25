use serde::{Deserialize, Serialize, de::DeserializeOwned};
use serde_json::{Value, json};
use uuid::Uuid;

/// All IPC message types exchanged between the Orion runtime and clients.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MessageType {
    // ----------------------------------------------------------------------
    // Connection
    // ----------------------------------------------------------------------

    Ping,
    Pong,

    // ----------------------------------------------------------------------
    // Prompt submission
    // ----------------------------------------------------------------------

    SubmitPrompt,
    CancelRequest,

    // ----------------------------------------------------------------------
    // Voice
    // ----------------------------------------------------------------------

    VoiceStart,
    VoiceChunk,
    VoiceEnd,

    // ----------------------------------------------------------------------
    // Assistant streaming
    // ----------------------------------------------------------------------

    AssistantStart,
    AssistantChunk,
    AssistantEnd,

    // ----------------------------------------------------------------------
    // Tool execution
    // ----------------------------------------------------------------------

    ToolStarted,
    ToolFinished,

    // ----------------------------------------------------------------------
    // Runtime
    // ----------------------------------------------------------------------

    Status,
    Error,
}

/// Every IPC message exchanged between Orion and a client is wrapped inside
/// an Envelope.
///
/// The envelope contains transport-level metadata while the payload contains
/// the message-specific data.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    /// IPC protocol version.
    #[serde(default = "default_version")]
    pub version: u32,

    /// Unique identifier for this individual message.
    #[serde(default = "Uuid::new_v4")]
    pub id: Uuid,

    /// Identifier connecting related messages to the same request/pipeline.
    #[serde(default = "Uuid::new_v4")]
    pub correlation_id: Uuid,

    /// Type of message contained in the envelope.
    #[serde(rename = "type")]
    pub message_type: MessageType,

    /// Message-specific payload.
    #[serde(default)]
    pub payload: Value,
}

const fn default_version() -> u32 {
    1
}

impl Envelope {
    /// Create an envelope with a newly generated message ID and correlation ID.
    pub fn new(message_type: MessageType, payload: Value) -> Self {
        Self {
            version: 1,
            id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            message_type,
            payload,
        }
    }

    /// Create an envelope using an existing correlation ID.
    ///
    /// This is important for runtime events because all events belonging to
    /// one pipeline must remain associated with the same request.
    pub fn with_correlation_id(
        message_type: MessageType,
        correlation_id: Uuid,
        payload: Value,
    ) -> Self {
        Self {
            version: 1,
            id: Uuid::new_v4(),
            correlation_id,
            message_type,
            payload,
        }
    }

    /// Create a ping request.
    pub fn ping() -> Self {
        Self::new(MessageType::Ping, json!({}))
    }

    /// Create a pong response.
    pub fn pong() -> Self {
        Self::new(MessageType::Pong, json!({}))
    }

    /// Create a prompt submission.
    pub fn submit_prompt(text: impl Into<String>) -> Self {
        Self::new(
            MessageType::SubmitPrompt,
            serde_json::to_value(SubmitPromptPayload {
                text: text.into(),
            })
            .expect("failed to serialize SubmitPromptPayload"),
        )
    }

    /// Create a prompt submission associated with an existing request.
    pub fn submit_prompt_with_correlation(
        correlation_id: Uuid,
        text: impl Into<String>,
    ) -> Self {
        Self::with_correlation_id(
            MessageType::SubmitPrompt,
            correlation_id,
            serde_json::to_value(SubmitPromptPayload {
                text: text.into(),
            })
            .expect("failed to serialize SubmitPromptPayload"),
        )
    }

    /// Create a cancel request.
    pub fn cancel_request(request_id: Uuid) -> Self {
        Self::new(
            MessageType::CancelRequest,
            serde_json::to_value(CancelRequestPayload { request_id })
                .expect("failed to serialize CancelRequestPayload"),
        )
    }

    /// Create a voice recording start message.
    pub fn voice_start(sample_rate: u32, channels: u32) -> Self {
        Self::new(
            MessageType::VoiceStart,
            serde_json::to_value(VoiceStartPayload {
                sample_rate,
                channels,
                encoding: "pcm16".to_string(),
            })
            .expect("failed to serialize VoiceStartPayload"),
        )
    }

    /// Create a voice chunk message.
    pub fn voice_chunk(sequence: u64, data: Vec<u8>) -> Self {
        Self::new(
            MessageType::VoiceChunk,
            serde_json::to_value(VoiceChunkPayload { sequence, data })
                .expect("failed to serialize VoiceChunkPayload"),
        )
    }

    /// Finish a voice recording by providing the recorded file path.
    pub fn voice_end(path: impl Into<String>) -> Self {
        Self::new(
            MessageType::VoiceEnd,
            serde_json::to_value(VoiceEndPayload { path: path.into() })
                .expect("failed to serialize VoiceEndPayload"),
        )
    }

    /// Signal that assistant response generation has started.
    pub fn assistant_start(correlation_id: Uuid) -> Self {
        Self::with_correlation_id(
            MessageType::AssistantStart,
            correlation_id,
            json!({}),
        )
    }

    /// Send an assistant response chunk.
    pub fn assistant_chunk(
        correlation_id: Uuid,
        text: impl Into<String>,
    ) -> Self {
        Self::with_correlation_id(
            MessageType::AssistantChunk,
            correlation_id,
            serde_json::to_value(AssistantChunkPayload {
                text: text.into(),
            })
            .expect("failed to serialize AssistantChunkPayload"),
        )
    }

    /// Signal that assistant response generation has completed.
    pub fn assistant_end(correlation_id: Uuid) -> Self {
        Self::with_correlation_id(
            MessageType::AssistantEnd,
            correlation_id,
            json!({}),
        )
    }

    /// Signal that a tool has started.
    pub fn tool_started(
        correlation_id: Uuid,
        name: impl Into<String>,
    ) -> Self {
        Self::with_correlation_id(
            MessageType::ToolStarted,
            correlation_id,
            serde_json::to_value(ToolStartedPayload {
                name: name.into(),
            })
            .expect("failed to serialize ToolStartedPayload"),
        )
    }

    /// Signal that a tool has finished.
    pub fn tool_finished(
        correlation_id: Uuid,
        name: impl Into<String>,
        success: bool,
    ) -> Self {
        Self::with_correlation_id(
            MessageType::ToolFinished,
            correlation_id,
            serde_json::to_value(ToolFinishedPayload {
                name: name.into(),
                success,
            })
            .expect("failed to serialize ToolFinishedPayload"),
        )
    }

    /// Send a runtime status update.
    pub fn status(
        correlation_id: Uuid,
        message: impl Into<String>,
    ) -> Self {
        Self::with_correlation_id(
            MessageType::Status,
            correlation_id,
            serde_json::to_value(StatusPayload {
                message: message.into(),
            })
            .expect("failed to serialize StatusPayload"),
        )
    }

    /// Send an error to the client.
    pub fn error(
        correlation_id: Uuid,
        code: impl Into<String>,
        message: impl Into<String>,
    ) -> Self {
        Self::with_correlation_id(
            MessageType::Error,
            correlation_id,
            serde_json::to_value(ErrorPayload {
                code: code.into(),
                message: message.into(),
            })
            .expect("failed to serialize ErrorPayload"),
        )
    }

    /// Deserialize the envelope payload into a strongly typed payload.
    pub fn payload<T>(&self) -> serde_json::Result<T>
    where
        T: DeserializeOwned,
    {
        serde_json::from_value(self.payload.clone())
    }

    /// Serialize this envelope to JSON.
    pub fn to_json(&self) -> serde_json::Result<String> {
        serde_json::to_string(self)
    }

    /// Deserialize an envelope from JSON.
    pub fn from_json(json: &str) -> serde_json::Result<Self> {
        serde_json::from_str(json)
    }
}

/* -------------------------------------------------------------------------- */
/*                             Payload Definitions                            */
/* -------------------------------------------------------------------------- */

/// User prompt submitted to Orion.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubmitPromptPayload {
    pub text: String,
}

/// Request cancellation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CancelRequestPayload {
    pub request_id: Uuid,
}

/// Metadata describing a voice recording session.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceStartPayload {
    pub sample_rate: u32,
    pub channels: u32,
    pub encoding: String,
}

/// A streamed audio frame.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceChunkPayload {
    pub sequence: u64,
    pub data: Vec<u8>,
}

/// Marks the end of a voice recording.
///
/// The runtime reads and transcribes the specified file.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceEndPayload {
    pub path: String,
}

/// Signals the start of assistant response generation.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AssistantStartPayload {}

/// A streamed fragment of assistant output.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssistantChunkPayload {
    pub text: String,
}

/// Signals completion of assistant response generation.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AssistantEndPayload {}

/// Indicates that a tool has started executing.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolStartedPayload {
    pub name: String,
}

/// Indicates that a tool has completed.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolFinishedPayload {
    pub name: String,
    pub success: bool,
}

/// General runtime status update.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusPayload {
    pub message: String,
}

/// Runtime error returned to the client.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorPayload {
    pub code: String,
    pub message: String,
}

/// Ping payload.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PingPayload {}

/// Pong payload.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PongPayload {}