use thiserror::Error as ThisError;

#[derive(Debug, ThisError)]
pub enum IpcError {
    #[error("connection closed")]
    Disconnected,

    #[error(transparent)]
    Io(#[from] std::io::Error),

    #[error(transparent)]
    Json(#[from] serde_json::Error),
}
