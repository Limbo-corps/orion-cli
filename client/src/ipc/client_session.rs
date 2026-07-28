use std::path::Path;

use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader, BufWriter},
    net::{
        UnixStream,
        unix::{OwnedReadHalf, OwnedWriteHalf},
    },
};
use uuid::Uuid;

use crate::ipc::{
    error::IpcError,
    messages::Envelope,
    protocol::{decode, encode},
};

pub struct ClientSession {
    id: Uuid,
    reader: BufReader<OwnedReadHalf>,
    writer: BufWriter<OwnedWriteHalf>,
    /// Persistent line buffer so a `receive()` cancelled inside a `select!`
    /// resumes instead of losing partially-read bytes (cancel-safety).
    read_buf: String,
}

impl ClientSession {
    pub async fn connect<P: AsRef<Path>>(path: P) -> Result<Self, IpcError> {
        let stream = UnixStream::connect(path).await?;

        let (reader, writer) = stream.into_split();

        Ok(Self {
            id: Uuid::new_v4(),
            reader: BufReader::new(reader),
            writer: BufWriter::new(writer),
            read_buf: String::new(),
        })
    }

    pub fn id(&self) -> Uuid {
        self.id
    }

    pub async fn send(&mut self, message: &Envelope) -> Result<(), IpcError> {
        let bytes = encode(message)?;

        self.writer.write_all(&bytes).await?;
        self.writer.flush().await?;

        Ok(())
    }

    pub async fn receive(&mut self) -> Result<Envelope, IpcError> {
        // Append into the persistent buffer. If this future is dropped by a
        // `select!` (e.g. a UI tick wins), the bytes read so far remain in
        // `read_buf`, and the next call resumes reading the same line — so no
        // message is corrupted or lost.
        let bytes = self.reader.read_line(&mut self.read_buf).await?;

        if bytes == 0 && self.read_buf.is_empty() {
            return Err(IpcError::Disconnected);
        }

        let line = std::mem::take(&mut self.read_buf);
        decode(&line)
    }

    pub async fn close(mut self) -> Result<(), IpcError> {
        self.writer.shutdown().await?;
        Ok(())
    }
}
