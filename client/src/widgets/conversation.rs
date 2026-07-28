use std::time::{SystemTime, UNIX_EPOCH};

use ratatui::{
    Frame,
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Modifier, Style, Stylize},
    text::{Line, Span},
    widgets::{Block, BorderType, Borders, Paragraph, Wrap},
};
use serde::{Deserialize, Serialize};

use crate::theme::{
    DANGER, FG, MUTED, OK, ORION_ACCENT, ORION_BUBBLE, ORION_EDGE, ORION_ICON, PANEL_BG,
    USER_ACCENT, USER_BUBBLE, USER_EDGE, USER_NAME, border_style,
};

/// IPC-friendly payload enum for identifying sender roles
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum Author {
    Orion,
    User,
    /// A Copilot-style inline activity log, not a chat bubble.
    Activity,
}

/// Status of a Copilot-style activity log line.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum ActivityKind {
    Running,
    Done,
    Failed,
}

/// Dynamic message model designed to be serialized/deserialized over IPC channels
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: String,
    pub author: Author,
    pub content: String,
    pub timestamp: u64,
    /// Present only for `Author::Activity` messages.
    pub activity: Option<ActivityKind>,
}

impl Message {
    pub fn new(id: String, author: Author, content: String) -> Self {
        Self {
            id,
            author,
            content,
            timestamp: now_secs(),
            activity: None,
        }
    }

    /// Build a concise activity log line (rendered inline, not as a bubble).
    pub fn activity(id: String, content: String, kind: ActivityKind) -> Self {
        Self {
            id,
            author: Author::Activity,
            content,
            timestamp: now_secs(),
            activity: Some(kind),
        }
    }
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

#[derive(Default)]
pub struct ConversationWidget {
    pub messages: Vec<Message>,
    pub scroll_offset: usize,
}

impl ConversationWidget {
    /// Creates a clean, empty conversation state
    pub fn new() -> Self {
        Self {
            messages: Vec::new(),
            scroll_offset: 0,
        }
    }

    /// Demo constructor for local development and UI testing
    pub fn with_demo_messages() -> Self {
        Self {
            messages: vec![
                Message::new(
                    "1".to_string(),
                    Author::User,
                    "What is the current system status?".to_string(),
                ),
                Message::new(
                    "2".to_string(),
                    Author::Orion,
                    "All systems operational. Listening for event triggers...".to_string(),
                ),
            ],
            scroll_offset: 0,
        }
    }

    /// Scroll up by N items
    pub fn scroll_up(&mut self, lines: usize) {
        self.scroll_offset = self.scroll_offset.saturating_add(lines);
    }

    /// Scroll down by N items
    pub fn scroll_down(&mut self, lines: usize) {
        self.scroll_offset = self.scroll_offset.saturating_sub(lines);
    }

    /// Reset scroll to the most recent messages at the bottom
    pub fn scroll_to_bottom(&mut self) {
        self.scroll_offset = 0;
    }

    /// Public interface for adding a complete message
    pub fn add_message(&mut self, message: Message) {
        self.messages.push(message);
        self.scroll_to_bottom();
    }

    /// Starts streaming a new assistant message
    pub fn begin_assistant_message(&mut self, id: String) {
        self.messages
            .push(Message::new(id, Author::Orion, String::new()));
        self.scroll_to_bottom();
    }

    /// Appends incoming streamed chunk to the active assistant response bubble
    pub fn append_assistant_chunk(&mut self, chunk: &str) {
        if let Some(last_msg) = self.messages.last_mut() {
            if last_msg.author == Author::Orion {
                last_msg.content.push_str(chunk);
                self.scroll_to_bottom();
                return;
            }
        }

        // Robust fallback: if chunk arrives without AssistantStart, allocate new unique message ID
        let fallback_id = format!("msg-{}", self.messages.len() + 1);
        self.messages
            .push(Message::new(fallback_id, Author::Orion, chunk.to_string()));
        self.scroll_to_bottom();
    }

    /// Called when streaming response terminates
    pub fn finish_assistant_message(&mut self) {
        // Reserved for post-processing, completion timestamp recording, or token metrics
    }

    pub fn clear(&mut self) {
        self.messages.clear();
        self.scroll_offset = 0;
    }

    /// Text of the most recent user message, if any.
    pub fn last_user_text(&self) -> Option<String> {
        self.messages
            .iter()
            .rev()
            .find(|m| m.author == Author::User)
            .map(|m| m.content.clone())
    }

    /// Text of the most recent assistant message (for TTS), or empty.
    pub fn last_assistant_text(&self) -> String {
        self.messages
            .iter()
            .rev()
            .find(|m| m.author == Author::Orion)
            .map(|m| m.content.clone())
            .unwrap_or_default()
    }

    pub fn render(&mut self, frame: &mut Frame, area: Rect) {
        // Outer Panel Block
        let outer_block = Block::default()
            .title(" conversation ")
            .borders(Borders::ALL)
            .border_style(border_style())
            .bg(PANEL_BG);

        let inner_area = outer_block.inner(area);
        frame.render_widget(outer_block, area);

        if inner_area.height == 0 || self.messages.is_empty() {
            return;
        }

        let max_bubble_width = ((inner_area.width as f32) * 0.74) as u16;

        // Calculate height for each message bubble taking \n AND word-wrapping into account
        let message_heights: Vec<u16> = self
            .messages
            .iter()
            .map(|msg| {
                // Activity logs are single compact lines, not bubbles.
                if msg.author == Author::Activity {
                    return 1;
                }

                let text_width = max_bubble_width.saturating_sub(4).max(1) as usize;

                let lines: usize = msg
                    .content
                    .lines()
                    .map(|line| {
                        if line.is_empty() {
                            1
                        } else {
                            (line.len() + text_width - 1) / text_width
                        }
                    })
                    .sum();

                // 1 line header + wrapped lines + 2 border padding
                (lines.max(1) as u16 + 3).max(4)
            })
            .collect();

        let total_height: u16 = message_heights.iter().sum();
        let available_height = inner_area.height;

        // Clamp scroll offset to prevent scrolling past the top message boundary
        let max_scroll = if total_height > available_height {
            self.messages.len().saturating_sub(1)
        } else {
            0
        };
        self.scroll_offset = self.scroll_offset.min(max_scroll);

        // Calculate bottom-up visible window including scroll offset
        let mut start_idx = 0;
        let end_idx = self.messages.len().saturating_sub(self.scroll_offset);
        let mut accumulated_height = 0;

        for (i, &h) in message_heights[..end_idx].iter().enumerate().rev() {
            if accumulated_height + h > available_height {
                start_idx = i + 1;
                break;
            }
            accumulated_height += h;
        }

        if start_idx > end_idx {
            start_idx = end_idx;
        }

        let visible_messages = &self.messages[start_idx..end_idx];
        let visible_heights = &message_heights[start_idx..end_idx];

        let constraints: Vec<Constraint> = visible_heights
            .iter()
            .map(|&h| Constraint::Length(h))
            .collect();

        let rows = Layout::default()
            .direction(Direction::Vertical)
            .constraints(constraints)
            .split(inner_area);

        for (i, msg) in visible_messages.iter().enumerate() {
            if i >= rows.len() {
                break;
            }

            match msg.author {
                Author::Activity => {
                    let (icon, color) = match msg.activity {
                        Some(ActivityKind::Running) => ("◐", ORION_ACCENT),
                        Some(ActivityKind::Done) => ("✓", OK),
                        Some(ActivityKind::Failed) => ("✕", DANGER),
                        None => ("·", MUTED),
                    };
                    let text_color = if color == DANGER { DANGER } else { MUTED };
                    let line = Line::from(vec![
                        Span::styled(format!("  {} ", icon), Style::default().fg(color)),
                        Span::styled(&msg.content, Style::default().fg(text_color)),
                    ]);
                    frame.render_widget(Paragraph::new(line), rows[i]);
                }
                Author::User => {
                    let content_len =
                        (msg.content.len() as u16 + 4).max(USER_NAME.len() as u16 + 4);
                    let bubble_width = content_len.min(max_bubble_width);

                    let cols = Layout::default()
                        .direction(Direction::Horizontal)
                        .constraints([Constraint::Min(0), Constraint::Length(bubble_width)])
                        .split(rows[i]);

                    let user_text = vec![
                        Line::from(Span::styled(
                            USER_NAME,
                            Style::default()
                                .fg(USER_ACCENT)
                                .add_modifier(Modifier::BOLD),
                        )),
                        Line::from(Span::styled(&msg.content, Style::default().fg(FG))),
                    ];

                    let user_bubble = Paragraph::new(user_text)
                        .alignment(Alignment::Right)
                        .wrap(Wrap { trim: true })
                        .block(
                            Block::default()
                                .borders(Borders::ALL)
                                .border_type(BorderType::Rounded)
                                .border_style(Style::default().fg(USER_EDGE))
                                .bg(USER_BUBBLE),
                        );

                    frame.render_widget(user_bubble, cols[1]);
                }
                Author::Orion => {
                    let header_len = (ORION_ICON.len() + 1 + "ORION".len()) as u16;
                    let content_len = (msg.content.len() as u16 + 4).max(header_len + 4);
                    let bubble_width = content_len.min(max_bubble_width);

                    let cols = Layout::default()
                        .direction(Direction::Horizontal)
                        .constraints([Constraint::Length(bubble_width), Constraint::Min(0)])
                        .split(rows[i]);

                    let orion_text = vec![
                        Line::from(vec![
                            Span::styled(
                                format!("{} ", ORION_ICON),
                                Style::default().fg(ORION_ACCENT),
                            ),
                            Span::styled(
                                "ORION",
                                Style::default()
                                    .fg(ORION_ACCENT)
                                    .add_modifier(Modifier::BOLD),
                            ),
                        ]),
                        Line::from(Span::styled(&msg.content, Style::default().fg(FG))),
                    ];

                    let orion_bubble = Paragraph::new(orion_text).wrap(Wrap { trim: true }).block(
                        Block::default()
                            .borders(Borders::ALL)
                            .border_type(BorderType::Rounded)
                            .border_style(Style::default().fg(ORION_EDGE))
                            .bg(ORION_BUBBLE),
                    );

                    frame.render_widget(orion_bubble, cols[0]);
                }
            }
        }
    }
}
