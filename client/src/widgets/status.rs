use ratatui::{
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::Paragraph,
};

use crate::app::InputMode;
use crate::theme::{DIM, MUTED, ORION_ACCENT, state_color};

pub const SPINNER: [&str; 10] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

pub struct StatusWidget;

impl StatusWidget {
    /// Renders the status bar given the app's current state variables
    pub fn render(
        mode: &str,
        input_mode: &InputMode,
        events_count: usize,
        frame_tick: usize,
    ) -> Paragraph<'static> {
        let sep = Span::styled("   ·   ", Style::default().fg(DIM));

        // 1. Connection Indicator (Separate)
        let is_connected = !mode.starts_with("OFFLINE") && !mode.starts_with("DISCONNECTED");
        let (conn_marker, conn_text, conn_color) = if is_connected {
            ("●", "connected", Color::Green)
        } else {
            ("○", "disconnected", Color::Red)
        };

        // 2. Task/Activity State Marker (IDLE gets static dot, active tasks get spinner)
        let activity_color = state_color(mode);
        let activity_marker = if mode == "IDLE" || mode == "CONNECTED" {
            "●".to_string()
        } else {
            SPINNER[frame_tick % SPINNER.len()].to_string()
        };

        // Format Vim Input Mode label (NORMAL vs INSERT)
        let (mode_label, mode_style) = match input_mode {
            InputMode::Normal => (
                "NORMAL",
                Style::default().fg(MUTED).add_modifier(Modifier::BOLD),
            ),
            InputMode::Insert => (
                "INSERT",
                Style::default()
                    .fg(ORION_ACCENT)
                    .add_modifier(Modifier::BOLD),
            ),
        };

        let content = Line::from(vec![
            // 1. Vim Input Mode (NORMAL / INSERT)
            Span::styled(mode_label, mode_style),
            sep.clone(),
            // 2. Connection Indicator
            Span::styled(
                format!("{} {}", conn_marker, conn_text),
                Style::default().fg(conn_color),
            ),
            sep.clone(),
            // 3. Activity State Indicator (e.g. idle, responding, thinking)
            Span::styled(
                format!("{} {}", activity_marker, mode.to_lowercase()),
                Style::default().fg(activity_color),
            ),
            sep.clone(),
            // 4. Provider
            Span::styled("groq", Style::default().fg(MUTED)),
            sep.clone(),
            // 5. Events Counter
            Span::styled(
                format!("{} events", events_count),
                Style::default().fg(MUTED),
            ),
            sep.clone(),
            // 6. Keybindings info depending on mode
            if *input_mode == InputMode::Normal {
                Span::styled(
                    "i insert  ·  v talk  ·  s stop  ·  q quit",
                    Style::default().fg(DIM),
                )
            } else {
                Span::styled("esc normal  ·  enter send", Style::default().fg(DIM))
            },
        ]);

        Paragraph::new(content)
    }
}
