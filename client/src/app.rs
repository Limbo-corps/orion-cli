use crossterm::event::{MouseButton, MouseEvent, MouseEventKind};
use ratatui::layout::{Position, Rect};

use crate::audio::{Recorder, Speaker, recording_path};
use crate::effects::Effects;
use crate::ipc::{client::OrionClient, events::RuntimeEvent};
use crate::theme;
use crate::widgets::conversation::{ActivityKind, Author, ConversationWidget, Message};
use crate::widgets::events::{EventLog, EventStatus};

#[derive(Debug, PartialEq, Eq)]
pub enum InputMode {
    Normal,
    Insert,
}

pub struct App {
    pub should_quit: bool,
    pub mode: String,
    pub input_mode: InputMode,
    pub events_count: usize,
    pub frame_tick: usize,
    pub conversation: ConversationWidget,
    pub input: String,
    pub cursor_position: usize, // Track character index inside `input`
    pub msg_counter: usize,

    // Client
    pub client: Option<OrionClient>,

    // Audio — the client owns all audio hardware
    pub recorder: Option<Recorder>,
    pub speaker: Speaker,

    // Store layout bounds for mouse click target checks
    pub prompt_area: Rect,
    pub events_area: Rect,

    // Real-time runtime event trace
    pub events: EventLog,

    // Animations (tachyonfx)
    pub effects: Effects,
}

impl App {
    pub fn new() -> Self {
        Self {
            should_quit: false,
            mode: "IDLE".to_string(),
            input_mode: InputMode::Normal, // Start in Normal mode
            events_count: 0,
            frame_tick: 0,
            conversation: ConversationWidget::new(),
            input: String::new(),
            cursor_position: 0,
            msg_counter: 0,
            client: None,
            recorder: None,
            speaker: Speaker::new(),
            prompt_area: Rect::default(),
            events_area: Rect::default(),
            events: EventLog::new(),
            effects: Effects::new(),
        }
    }

    pub fn on_tick(&mut self) {
        self.frame_tick = self.frame_tick.wrapping_add(1);
    }

    pub fn move_cursor_left(&mut self) {
        let cursor_moved_left = self.cursor_position.saturating_sub(1);
        self.cursor_position = cursor_moved_left;
    }

    pub fn move_cursor_right(&mut self) {
        let cursor_moved_right = self.cursor_position.saturating_add(1);
        if cursor_moved_right <= self.input.len() {
            self.cursor_position = cursor_moved_right;
        }
    }

    pub fn enter_char(&mut self, new_char: char) {
        self.input.insert(self.cursor_position, new_char);
        self.move_cursor_right();
        self.effects.on_keystroke();
    }

    pub fn delete_char(&mut self) {
        if self.cursor_position != 0 {
            let current_index = self.cursor_position;
            let from_left_to_current_index = current_index - 1;

            self.input.remove(from_left_to_current_index);
            self.move_cursor_left();
        }
    }

    pub fn handle_mouse(&mut self, event: MouseEvent) {
        match event.kind {
            MouseEventKind::Down(MouseButton::Left) => {
                let click_pos = Position::new(event.column, event.row);

                // If user clicks inside the prompt box -> Enter Insert mode
                if self.prompt_area.contains(click_pos) {
                    self.input_mode = InputMode::Insert;
                } else {
                    // Clicking anywhere else switches back to Normal mode
                    self.input_mode = InputMode::Normal;
                }
            }
            // Vertical scroll wheel — route to whichever panel is hovered.
            MouseEventKind::ScrollUp => {
                let pos = Position::new(event.column, event.row);
                if self.events_area.contains(pos) {
                    self.events.scroll_up(2);
                } else {
                    self.conversation.scroll_up(2);
                }
            }
            MouseEventKind::ScrollDown => {
                let pos = Position::new(event.column, event.row);
                if self.events_area.contains(pos) {
                    self.events.scroll_down(2);
                } else {
                    self.conversation.scroll_down(2);
                }
            }
            _ => {}
        }
    }

    pub async fn submit_prompt(&mut self) {
        let content = self.input.trim().to_string();

        if content.is_empty() {
            return;
        }

        if let Some(client) = &mut self.client {
            if let Err(err) = client.send_prompt(content.clone()).await {
                self.mode = format!("ERROR: {}", err);
                return;
            }
        }

        self.msg_counter += 1;

        // Clean construction using Message::new
        self.events
            .push("PROMPT", EventStatus::Info, "prompt submitted");
        self.conversation.add_message(Message::new(
            format!("msg-{}", self.msg_counter),
            Author::User,
            content,
        ));
        self.effects.on_message();

        self.input.clear();
        self.cursor_position = 0; // Reset cursor position on submit
        self.events_count += 1;
        self.mode = "THINKING".into();
    }

    // --- Voice (push-to-talk) ------------------------------------------

    /// Toggle recording: press once to start, again to stop and send.
    pub async fn toggle_recording(&mut self) {
        if self.recorder.is_some() {
            self.stop_recording().await;
        } else {
            self.start_recording().await;
        }
    }

    async fn start_recording(&mut self) {
        self.speaker.stop(); // a new recording interrupts any speech

        match Recorder::start(recording_path()) {
            Ok(recorder) => {
                let sample_rate = recorder.sample_rate();
                let channels = recorder.channels() as u32;
                self.recorder = Some(recorder);
                self.mode = "RECORDING".into();
                self.effects.on_status_change(theme::DANGER);
                self.events
                    .push("VOICE_START", EventStatus::Running, "recording");

                if let Some(client) = &mut self.client {
                    let _ = client.send_voice_start(sample_rate, channels).await;
                }
            }
            Err(err) => {
                self.mode = format!("MIC ERROR: {}", err);
                self.events.push("VOICE_START", EventStatus::Failed, err);
            }
        }
    }

    async fn stop_recording(&mut self) {
        let Some(recorder) = self.recorder.take() else {
            return;
        };

        match recorder.finish() {
            Ok(path) => {
                let path = path.to_string_lossy().to_string();
                self.mode = "TRANSCRIBING".into();
                self.events
                    .push("VOICE_END", EventStatus::Completed, path.clone());

                if let Some(client) = &mut self.client {
                    let _ = client.send_voice_end(path).await;
                }
            }
            Err(err) => {
                self.mode = format!("REC ERROR: {}", err);
                self.events.push("VOICE_END", EventStatus::Failed, err);
            }
        }
    }

    /// Interrupt any assistant speech currently playing.
    pub fn interrupt_speech(&self) {
        self.speaker.stop();
    }

    pub fn handle_runtime_event(&mut self, event: RuntimeEvent) {
        match event {
            RuntimeEvent::Connected => self.on_connected(),

            RuntimeEvent::Disconnected => {
                self.mode = "DISCONNECTED".into();
                self.effects.on_status_change(theme::DANGER);
                self.events
                    .push("DISCONNECTED", EventStatus::Failed, "runtime disconnected");
            }

            RuntimeEvent::AssistantStart => {
                self.mode = "RESPONDING".into();
                self.msg_counter += 1;

                // Begin a single message bubble for the streaming response
                self.conversation
                    .begin_assistant_message(format!("msg-{}", self.msg_counter));
                self.effects.on_message();
                self.events
                    .push("RESPONSE", EventStatus::Running, "assistant responding");
            }

            RuntimeEvent::AssistantChunk(text) => {
                self.conversation.append_assistant_chunk(&text);
                // Coalesce chunk spam onto the running RESPONSE trace line.
                self.events
                    .bump_last("RESPONSE", EventStatus::Running, "streaming…");
            }

            RuntimeEvent::AssistantEnd => {
                self.mode = "IDLE".into();
                self.conversation.finish_assistant_message();
                self.events
                    .bump_last("RESPONSE", EventStatus::Completed, "response complete");
                // Client-side TTS: speak the completed response.
                self.speaker.speak(&self.conversation.last_assistant_text());
            }

            RuntimeEvent::ToolStarted { name } => {
                self.mode = format!("TOOL: {}", name);
                self.events
                    .push("TOOL_STARTED", EventStatus::Running, name.clone());
                self.add_activity(format!("Running {}…", name), ActivityKind::Running);
            }

            RuntimeEvent::ToolFinished { name, success } => {
                let label = if success { "OK" } else { "FAILED" };
                self.mode = format!("TOOL {}: {}", label, name);

                let status = if success {
                    EventStatus::Completed
                } else {
                    EventStatus::Failed
                };
                self.events.push("TOOL_FINISHED", status, name.clone());

                if success {
                    self.add_activity(format!("Finished {}", name), ActivityKind::Done);
                } else {
                    self.add_activity(format!("Failed {}", name), ActivityKind::Failed);
                }
            }

            RuntimeEvent::Status(status) => {
                self.mode = status.clone();
                self.events.push("STATUS", EventStatus::Info, status);
            }

            RuntimeEvent::Error { code, message } => {
                self.mode = format!("ERROR: {}", message);
                self.effects.on_status_change(theme::DANGER);
                self.events.push(
                    "ERROR",
                    EventStatus::Failed,
                    format!("{}: {}", code, message),
                );
            }

            // Heartbeat — intentionally not traced (too noisy).
            RuntimeEvent::Ping | RuntimeEvent::Pong => {}

            RuntimeEvent::VoiceStart => {
                self.mode = "VOICE RECORDING".into();
                self.events
                    .push("VOICE_START", EventStatus::Running, "recording");
            }

            RuntimeEvent::VoiceChunk { .. } => {}

            RuntimeEvent::VoiceEnd => {
                self.mode = "PROCESSING VOICE".into();
                self.events
                    .push("VOICE_END", EventStatus::Info, "processing");
            }

            RuntimeEvent::Unknown(_) => {}
        }
    }

    /// Append a Copilot-style activity log line to the conversation.
    fn add_activity(&mut self, text: String, kind: ActivityKind) {
        self.msg_counter += 1;
        self.conversation.add_message(Message::activity(
            format!("act-{}", self.msg_counter),
            text,
            kind,
        ));
        self.effects.on_message();
    }

    /// Runtime socket connected (called from the event loop on startup).
    pub fn on_connected(&mut self) {
        self.mode = "CONNECTED".into();
        self.effects.on_status_change(theme::OK);
        self.events
            .push("CONNECTED", EventStatus::Completed, "runtime connected");
    }

    /// Runtime socket unavailable at startup.
    pub fn on_offline(&mut self, detail: String) {
        self.mode = format!("OFFLINE ({})", detail);
        self.effects.on_status_change(theme::DANGER);
        self.events.push("OFFLINE", EventStatus::Failed, detail);
    }

    /// IPC stream error while running.
    pub fn on_ipc_error(&mut self, detail: String) {
        self.mode = format!("IPC ERROR: {}", detail);
        self.effects.on_status_change(theme::DANGER);
        self.events.push("IPC_ERROR", EventStatus::Failed, detail);
    }
}
