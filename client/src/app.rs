use crossterm::event::{MouseButton, MouseEvent, MouseEventKind};
use ratatui::layout::{Position, Rect};

use crate::effects::Effects;
use crate::ipc::{client::OrionClient, events::RuntimeEvent};
use crate::theme;
use crate::widgets::conversation::{Author, ConversationWidget, Message};

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

    // Store layout bounds for mouse click target checks
    pub prompt_area: Rect,

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
            prompt_area: Rect::default(),
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
            // Vertical scroll wheel support
            MouseEventKind::ScrollUp => {
                self.conversation.scroll_up(2);
            }
            MouseEventKind::ScrollDown => {
                self.conversation.scroll_down(2);
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

    pub fn handle_runtime_event(&mut self, event: RuntimeEvent) {
        match event {
            RuntimeEvent::Connected => {
                self.mode = "CONNECTED".into();
                self.effects.on_status_change(theme::OK);
            }

            RuntimeEvent::Disconnected => {
                self.mode = "DISCONNECTED".into();
                self.effects.on_status_change(theme::DANGER);
            }

            RuntimeEvent::AssistantStart => {
                self.mode = "RESPONDING".into();
                self.msg_counter += 1;

                // Begin a single message bubble for the streaming response
                self.conversation
                    .begin_assistant_message(format!("msg-{}", self.msg_counter));
                self.effects.on_message();
            }

            RuntimeEvent::AssistantChunk(text) => {
                // Append text chunk directly to active message bubble
                self.conversation.append_assistant_chunk(&text);
            }

            RuntimeEvent::AssistantEnd => {
                self.mode = "IDLE".into();
                self.conversation.finish_assistant_message();
            }

            RuntimeEvent::ToolStarted { name } => {
                self.mode = format!("TOOL: {}", name);
            }

            RuntimeEvent::ToolFinished { name, success } => {
                let status = if success { "OK" } else { "FAILED" };
                self.mode = format!("TOOL {}: {}", status, name);
            }

            RuntimeEvent::Status(status) => {
                self.mode = status;
            }

            RuntimeEvent::Error { message, .. } => {
                self.mode = format!("ERROR: {}", message);
                self.effects.on_status_change(theme::DANGER);
            }

            RuntimeEvent::Ping => {
                // Heartbeat ping received from runtime
            }

            RuntimeEvent::Pong => {
                // Heartbeat pong response
            }

            RuntimeEvent::VoiceStart => {
                self.mode = "VOICE RECORDING".into();
            }

            RuntimeEvent::VoiceChunk { .. } => {
                // Voice stream data chunk received
            }

            RuntimeEvent::VoiceEnd => {
                self.mode = "PROCESSING VOICE".into();
            }

            RuntimeEvent::Unknown(_) => {}
        }
    }
}
