use serde::{Deserialize, Serialize, de::DeserializeOwned};
use serde_json::{Value, json};
use uuid::Uuid;

/// All IPC message types exchanged between the Orion runtime and clients.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MessageType {
    // Connection
    Ping,
    Pong,

    // Prompt submission
    SubmitPrompt,
    CancelRequest,

    // Voice
    VoiceStart,
    VoiceChunk,
    VoiceEnd,

    // Assistant streaming
    AssistantStart,
    AssistantChunk,
    AssistantEnd,

    // Tool execution
    ToolStarted,
    ToolFinished,

    // Runtime
    Status,
    Error,
}

/// Every IPC message is wrapped inside an Envelope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    #[serde(default = "default_version")]
    pub version: u32,

    #[serde(default = "Uuid::new_v4")]
    pub id: Uuid,

    #[serde(default = "Uuid::new_v4")]
    pub correlation_id: Uuid,

    #[serde(rename = "type")]
    pub message_type: MessageType,

    #[serde(default)]
    pub payload: Value,
}

const fn default_version() -> u32 {
    1
}

impl Envelope {
    /// Create a ping request.
    pub fn ping() -> Self {
        Self {
            version: 1,
            id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            message_type: MessageType::Ping,
            payload: json!({}),
        }
    }

    /// Create a pong response.
    pub fn pong() -> Self {
        Self {
            version: 1,
            id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            message_type: MessageType::Pong,
            payload: json!({}),
        }
    }

    /// Create a prompt submission.
    pub fn submit_prompt(text: impl Into<String>) -> Self {
        Self {
            version: 1,
            id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            message_type: MessageType::SubmitPrompt,
            payload: serde_json::to_value(SubmitPromptPayload { text: text.into() }).unwrap(),
        }
    }

    /// Announce the start of a voice recording session (metadata only).
    pub fn voice_start(sample_rate: u32, channels: u32) -> Self {
        Self {
            version: 1,
            id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            message_type: MessageType::VoiceStart,
            payload: serde_json::to_value(VoiceStartPayload {
                sample_rate,
                channels,
                encoding: "pcm16".to_string(),
            })
            .unwrap(),
        }
    }

    /// Finish a recording by handing the runtime the recorded file path.
    pub fn voice_end(path: impl Into<String>) -> Self {
        Self {
            version: 1,
            id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            message_type: MessageType::VoiceEnd,
            payload: serde_json::to_value(VoiceEndPayload { path: path.into() }).unwrap(),
        }
    }

    /// Deserialize the payload into a strongly typed struct.
    pub fn payload<T>(&self) -> serde_json::Result<T>
    where
        T: DeserializeOwned,
    {
        serde_json::from_value(self.payload.clone())
    }
}

/* -------------------------------------------------------------------------- */
/*                             Payload Definitions                            */
/* -------------------------------------------------------------------------- */

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubmitPromptPayload {
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CancelRequestPayload {
    pub request_id: Uuid,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceStartPayload {
    pub sample_rate: u32,
    pub channels: u32,
    pub encoding: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceChunkPayload {
    pub sequence: u64,
    pub data: Vec<u8>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VoiceEndPayload {
    /// Path to the recorded audio file the runtime should transcribe.
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AssistantStartPayload;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssistantChunkPayload {
    pub text: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AssistantEndPayload;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolStartedPayload {
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolFinishedPayload {
    pub name: String,
    pub success: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusPayload {
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorPayload {
    pub code: String,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PingPayload;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PongPayload;
