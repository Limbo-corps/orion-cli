//! Client-side audio: microphone capture and speech output.
//!
//! Per the architecture, the *client* owns all audio hardware. [`Recorder`]
//! captures the microphone to a 16-bit PCM WAV (via `cpal` + `hound`); the app
//! sends that file's path to the runtime, which transcribes it. [`Speaker`]
//! speaks the assistant's reply through the system speech engine by shelling
//! out to `spd-say` (speech-dispatcher) — no build-time audio library required,
//! and it degrades to silence if speech-dispatcher isn't installed.

use std::path::PathBuf;
use std::process::Command;
use std::sync::{Arc, Mutex};

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{FromSample, Sample, SizedSample};

/// Default location for the recorded clip (shared with the runtime, same host).
pub fn recording_path() -> PathBuf {
    std::env::temp_dir().join("orion_client_recording.wav")
}

/// Build an input stream for sample type `T`, converting each sample to i16.
fn build_input<T>(
    device: &cpal::Device,
    config: &cpal::StreamConfig,
    sink: Arc<Mutex<Vec<i16>>>,
) -> Result<cpal::Stream, String>
where
    T: SizedSample,
    i16: FromSample<T>,
{
    device
        .build_input_stream(
            config.clone(),
            move |data: &[T], _: &cpal::InputCallbackInfo| {
                if let Ok(mut buf) = sink.lock() {
                    buf.extend(data.iter().map(|&s| i16::from_sample(s)));
                }
            },
            |err| eprintln!("audio input error: {err}"),
            None,
        )
        .map_err(|e| e.to_string())
}

/// An in-progress microphone recording. Dropping/finishing it stops capture.
pub struct Recorder {
    stream: cpal::Stream,
    samples: Arc<Mutex<Vec<i16>>>,
    sample_rate: u32,
    channels: u16,
    path: PathBuf,
}

impl Recorder {
    /// Open the default input device and start capturing into memory.
    pub fn start(path: PathBuf) -> Result<Self, String> {
        let host = cpal::default_host();
        let device = host
            .default_input_device()
            .ok_or_else(|| "no input device".to_string())?;
        let supported = device.default_input_config().map_err(|e| e.to_string())?;

        let sample_rate = supported.sample_rate();
        let channels = supported.channels();
        let sample_format = supported.sample_format();
        let config: cpal::StreamConfig = supported.into();

        let samples = Arc::new(Mutex::new(Vec::<i16>::new()));

        // Accept any input sample format the device offers, converting each
        // sample to i16 for the WAV.
        let stream = match sample_format {
            cpal::SampleFormat::I8 => build_input::<i8>(&device, &config, samples.clone()),
            cpal::SampleFormat::I16 => build_input::<i16>(&device, &config, samples.clone()),
            cpal::SampleFormat::I32 => build_input::<i32>(&device, &config, samples.clone()),
            cpal::SampleFormat::U8 => build_input::<u8>(&device, &config, samples.clone()),
            cpal::SampleFormat::U16 => build_input::<u16>(&device, &config, samples.clone()),
            cpal::SampleFormat::U32 => build_input::<u32>(&device, &config, samples.clone()),
            cpal::SampleFormat::F32 => build_input::<f32>(&device, &config, samples.clone()),
            cpal::SampleFormat::F64 => build_input::<f64>(&device, &config, samples.clone()),
            other => return Err(format!("unsupported sample format: {other:?}")),
        }?;

        stream.play().map_err(|e| e.to_string())?;

        Ok(Self {
            stream,
            samples,
            sample_rate,
            channels,
            path,
        })
    }

    pub fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    pub fn channels(&self) -> u16 {
        self.channels
    }

    /// Stop capture, write the WAV, and return its path.
    pub fn finish(self) -> Result<PathBuf, String> {
        let Recorder {
            stream,
            samples,
            sample_rate,
            channels,
            path,
        } = self;

        drop(stream); // stop the input stream

        let samples = samples
            .lock()
            .map_err(|_| "audio buffer poisoned".to_string())?;

        let spec = hound::WavSpec {
            channels,
            sample_rate,
            bits_per_sample: 16,
            sample_format: hound::SampleFormat::Int,
        };

        let mut writer = hound::WavWriter::create(&path, spec).map_err(|e| e.to_string())?;
        for &sample in samples.iter() {
            writer.write_sample(sample).map_err(|e| e.to_string())?;
        }
        writer.finalize().map_err(|e| e.to_string())?;

        Ok(path)
    }
}

/// Speaks assistant responses through speech-dispatcher's `spd-say` CLI.
pub struct Speaker;

impl Speaker {
    pub fn new() -> Self {
        Self
    }

    /// Speak `text`, cancelling anything currently being spoken first.
    pub fn speak(&self, text: &str) {
        let text = text.trim();
        if text.is_empty() {
            return;
        }
        // `-C` cancels current speech, so a new reply interrupts an old one.
        let _ = Command::new("spd-say").arg("-C").arg(text).spawn();
    }

    /// Stop any in-progress speech.
    pub fn stop(&self) {
        let _ = Command::new("spd-say").arg("--cancel").spawn();
    }
}

impl Default for Speaker {
    fn default() -> Self {
        Self::new()
    }
}
