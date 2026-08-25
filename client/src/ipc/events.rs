use crate::ipc::messages::Envelope;

#[allow(dead_code)]
#[derive(Debug, Clone)]
pub enum RuntimeEvent {
    Connected,
    Disconnected,

    // ------------------------------------------------------------------
    // Pipeline
    // ------------------------------------------------------------------
    PipelineStart,
    VoicePipelineStart,
    ChatPipelineStart,

    PipelineComplete,
    PipelineFailed {
        error: String,
    },
    PipelineRestart,

    // ------------------------------------------------------------------
    // Voice
    // ------------------------------------------------------------------
    VoiceRecordingStart,
    VoiceRecordingCompleted {
        audio_path: Option<String>,
    },
    VoiceRecordingFailed {
        error: String,
    },

    SpeechDetected,
    SilenceDetected {
        silence_duration: f32,
    },

    // ------------------------------------------------------------------
    // Speech-to-Text
    // ------------------------------------------------------------------
    TranscriptGenerated {
        text: String,
    },
    TranscriptGenerationFailed {
        error: String,
    },

    // ------------------------------------------------------------------
    // Agent
    // ------------------------------------------------------------------
    AgentProcessingStart,

    // Assistant
    AssistantStart,
    AssistantChunk(String),
    AssistantEnd,

    ResponseGenerationFailed {
        error: String,
    },

    // ------------------------------------------------------------------
    // Tools
<<<<<<< HEAD
    // ------------------------------------------------------------------
=======
<<<<<<< HEAD
=======
    // ------------------------------------------------------------------
>>>>>>> b708882 (feat: major changes, updated mcp architecture and added multi-llm integration)
>>>>>>> 03ba8c4 (feat: major changes, updated mcp architecture and added multi-llm integration)
    ToolStarted {
        name: String,
    },
    ToolFinished {
        name: String,
        success: bool,
    },

    // ------------------------------------------------------------------
    // Text-to-Speech
    // ------------------------------------------------------------------
    SpeechSynthesisStart {
        text: String,
    },
    SpeechGenerated {
        audio_path: Option<String>,
        text: String,
    },
    SpeechGenerationFailed {
        error: String,
    },

    // ------------------------------------------------------------------
    // Audio Playback
    // ------------------------------------------------------------------
    AudioPlaybackStarted,
    AudioPlaybackCompleted,
    AudioPlaybackFailed {
        error: String,
    },

    // ------------------------------------------------------------------
    // Runtime
    // ------------------------------------------------------------------
    Status(String),
    Error {
        code: String,
        message: String,
    },

    // ------------------------------------------------------------------
    // Connection
    // ------------------------------------------------------------------
    Ping,
    Pong,

    // ------------------------------------------------------------------
    // Voice streaming
    // ------------------------------------------------------------------
    VoiceStart,
    VoiceChunk {
        sequence: u64,
        bytes: Vec<u8>,
    },
    VoiceEnd,

    // ------------------------------------------------------------------
    // Unknown / unsupported
    // ------------------------------------------------------------------
    Unknown(Envelope),
}
