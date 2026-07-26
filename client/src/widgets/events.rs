//! Real-time event stream panel.
//!
//! [`EventLog`] is a scrollable, auto-following trace of runtime events. Each
//! entry carries a timestamp, an event type (e.g. `TOOL_STARTED`), an
//! execution status, and an optional detail. The app pushes entries as
//! [`crate::ipc::events::RuntimeEvent`]s arrive; the panel auto-scrolls to the
//! tail unless the user has scrolled up (manual scrolling is preserved).

use ratatui::{
    Frame,
    layout::Rect,
    style::{Color, Style, Stylize},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
};

use crate::theme::{DANGER, DIM, MUTED, OK, ORION_ACCENT, PANEL_BG, border_style};

/// Cap on retained entries so a long session doesn't grow unbounded.
const MAX_ENTRIES: usize = 500;

/// Execution status of an event, driving its icon and color.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EventStatus {
    Info,
    Running,
    Completed,
    Failed,
}

impl EventStatus {
    fn icon(self) -> &'static str {
        match self {
            EventStatus::Info => "·",
            EventStatus::Running => "◐",
            EventStatus::Completed => "✓",
            EventStatus::Failed => "✕",
        }
    }

    fn color(self) -> Color {
        match self {
            EventStatus::Info => MUTED,
            EventStatus::Running => ORION_ACCENT,
            EventStatus::Completed => OK,
            EventStatus::Failed => DANGER,
        }
    }
}

#[derive(Debug, Clone)]
pub struct EventEntry {
    pub time: String,
    pub kind: String,
    pub status: EventStatus,
    pub detail: String,
}

/// Scrollable, auto-following log of runtime events.
#[derive(Default)]
pub struct EventLog {
    entries: Vec<EventEntry>,
    /// Lines above the bottom; `0` follows the tail (auto-scroll).
    scroll_offset: u16,
}

impl EventLog {
    pub fn new() -> Self {
        Self::default()
    }

    /// Append a new event. If the user has scrolled up, the viewport is
    /// preserved; otherwise the panel keeps following the tail.
    pub fn push(
        &mut self,
        kind: impl Into<String>,
        status: EventStatus,
        detail: impl Into<String>,
    ) {
        self.entries.push(EventEntry {
            time: now_hms(),
            kind: kind.into(),
            status,
            detail: detail.into(),
        });

        if self.entries.len() > MAX_ENTRIES {
            let overflow = self.entries.len() - MAX_ENTRIES;
            self.entries.drain(0..overflow);
        }

        if self.scroll_offset > 0 {
            self.scroll_offset = self.scroll_offset.saturating_add(1);
        }
    }

    /// Update the most recent entry if it shares `kind` (used to coalesce
    /// high-frequency events like response chunks); otherwise push a new one.
    pub fn bump_last(&mut self, kind: &str, status: EventStatus, detail: impl Into<String>) {
        if let Some(last) = self.entries.last_mut() {
            if last.kind == kind {
                last.status = status;
                last.detail = detail.into();
                last.time = now_hms();
                return;
            }
        }
        self.push(kind, status, detail);
    }

    pub fn scroll_up(&mut self, lines: u16) {
        self.scroll_offset = self.scroll_offset.saturating_add(lines);
    }

    pub fn scroll_down(&mut self, lines: u16) {
        self.scroll_offset = self.scroll_offset.saturating_sub(lines);
    }

    pub fn render(&self, frame: &mut Frame, area: Rect) {
        let block = Block::default()
            .title(" event stream ")
            .borders(Borders::ALL)
            .border_style(border_style())
            .bg(PANEL_BG);

        let inner = block.inner(area);
        frame.render_widget(block, area);

        if inner.height == 0 {
            return;
        }

        let lines: Vec<Line> = self
            .entries
            .iter()
            .map(|e| {
                let detail = if e.detail.is_empty() {
                    String::new()
                } else {
                    format!("  {}", e.detail)
                };
                Line::from(vec![
                    Span::styled(format!("{} ", e.time), Style::default().fg(DIM)),
                    Span::styled(
                        format!("{} {}", e.status.icon(), e.kind),
                        Style::default().fg(e.status.color()),
                    ),
                    Span::styled(detail, Style::default().fg(MUTED)),
                ])
            })
            .collect();

        // Auto-follow the tail; `scroll_offset` moves the viewport upward.
        let total = lines.len() as u16;
        let max_scroll = total.saturating_sub(inner.height);
        let offset = self.scroll_offset.min(max_scroll);
        let scroll_y = max_scroll.saturating_sub(offset);

        frame.render_widget(Paragraph::new(lines).scroll((scroll_y, 0)), inner);
    }
}

/// UTC `HH:MM:SS` timestamp for the trace (monotonic, timezone-agnostic).
fn now_hms() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    format!(
        "{:02}:{:02}:{:02}",
        (secs / 3600) % 24,
        (secs / 60) % 60,
        secs % 60
    )
}
