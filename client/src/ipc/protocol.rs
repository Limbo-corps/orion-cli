use crate::ipc::{error::IpcError, messages::Envelope};

/// Serialize an IPC message into bytes.
///
/// The Orion IPC protocol is newline-delimited JSON (NDJSON), so every
/// encoded message is terminated with '\n'.
pub fn encode(message: &Envelope) -> Result<Vec<u8>, IpcError> {
    let mut bytes = serde_json::to_vec(message)?;
    bytes.push(b'\n');
    Ok(bytes)
}

/// Deserialize an IPC message received from the socket.
pub fn decode(data: &str) -> Result<Envelope, IpcError> {
    Ok(serde_json::from_str(data.trim_end())?)
}
