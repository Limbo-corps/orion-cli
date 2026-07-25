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
}

impl ClientSession {
    pub async fn connect<P: AsRef<Path>>(path: P) -> Result<Self, IpcError> {
        let stream = UnixStream::connect(path).await?;

        let (reader, writer) = stream.into_split();

        Ok(Self {
            id: Uuid::new_v4(),
            reader: BufReader::new(reader),
            writer: BufWriter::new(writer),
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
        let mut line = String::new();

        let bytes = self.reader.read_line(&mut line).await?;

        if bytes == 0 {
            return Err(IpcError::Disconnected);
        }

        decode(&line)
    }

    pub async fn close(mut self) -> Result<(), IpcError> {
        self.writer.shutdown().await?;
        Ok(())
    }
}
