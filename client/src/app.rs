use crossterm::event::{MouseButton, MouseEvent, MouseEventKind};
use ratatui::{
    Frame,
    layout::{Constraint, Direction, Layout, Position, Rect},
};

use crate::widgets::{
    conversation::{Author, ConversationWidget, Message},
    events::EventStreamWidget,
    header::BannerWidget,
    prompt::PromptWidget,
    status::StatusWidget,
};
use crate::{
    ipc::{client::OrionClient, events::RuntimeEvent},
    theme::default_style,
};

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
    pub msg_counter: usize,

    // Client
    pub client: Option<OrionClient>,

    // Store layout bounds for mouse click target checks
    pub prompt_area: Rect,
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
            msg_counter: 0,
            client: None,
            prompt_area: Rect::default(),
        }
    }

    pub fn on_tick(&mut self) {
        self.frame_tick = self.frame_tick.wrapping_add(1);
    }

    pub fn handle_mouse(&mut self, event: MouseEvent) {
        if event.kind == MouseEventKind::Down(MouseButton::Left) {
            let click_pos = Position::new(event.column, event.row);

            // If user clicks inside the prompt box -> Enter Insert mode
            if self.prompt_area.contains(click_pos) {
                self.input_mode = InputMode::Insert;
            } else {
                // Clicking anywhere else switches back to Normal mode
                self.input_mode = InputMode::Normal;
            }
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

        self.input.clear();
        self.events_count += 1;
        self.mode = "THINKING".into();
    }

    pub fn handle_runtime_event(&mut self, event: RuntimeEvent) {
        match event {
            RuntimeEvent::Connected => {
                self.mode = "CONNECTED".into();
            }

            RuntimeEvent::Disconnected => {
                self.mode = "DISCONNECTED".into();
            }

            RuntimeEvent::AssistantStart => {
                self.mode = "RESPONDING".into();
                self.msg_counter += 1;

                // Begin a single message bubble for the streaming response
                self.conversation
                    .begin_assistant_message(format!("msg-{}", self.msg_counter));
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

    pub fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        frame.render_widget(
            ratatui::widgets::Block::default().style(default_style()),
            area,
        );

        // Main Vertical Split
        let main_chunks = Layout::default()
            .direction(Direction::Vertical)
            .margin(1)
            .constraints([
                Constraint::Length(2), // Banner
                Constraint::Min(0),    // Content
                Constraint::Length(1), // Status Bar
            ])
            .split(area);

        // Horizontal Middle Split: Left Column (66%), Right Column (34%)
        let content_chunks = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Percentage(66), Constraint::Percentage(34)])
            .split(main_chunks[1]);

        // Left Column Vertical Split: Conversation Area (Flex) + Prompt Box (3 rows)
        let left_chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Min(0),    // Conversation
                Constraint::Length(3), // Prompt input box
            ])
            .split(content_chunks[0]);

        // Cache prompt area for mouse click collision detection
        self.prompt_area = left_chunks[1];

        // 1. Render Banner
        frame.render_widget(BannerWidget::render(main_chunks[0]), main_chunks[0]);

        // 2. Render Left Column
        self.conversation.render(frame, left_chunks[0]);

        // Render Prompt (Highlight border when focused in Insert mode)
        let is_focused = self.input_mode == InputMode::Insert;
        frame.render_widget(
            PromptWidget::render(&self.input, is_focused),
            left_chunks[1],
        );

        // 3. Render Right Column
        frame.render_widget(EventStreamWidget::render(), content_chunks[1]);

        // 4. Render Status Bar (with updated input mode indicator)
        frame.render_widget(
            StatusWidget::update_status(
                &self.mode,
                &self.input_mode,
                self.events_count,
                self.frame_tick,
            ),
            main_chunks[2],
        );
    }
}
