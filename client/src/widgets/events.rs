use ratatui::{
    style::Stylize, // Fix E0599: Import Stylize for .bg()
    text::Line,
    widgets::{Block, Borders, Paragraph},
};

use crate::theme::{PANEL_BG, border_style};

pub struct EventStreamWidget;

impl EventStreamWidget {
    pub fn render() -> Paragraph<'static> {
        let events = vec![
            Line::from("[15:31:00] INFO: App initialized"),
            Line::from("[15:31:05] OK: Connection established"),
        ];

        Paragraph::new(events).block(
            Block::default()
                .title(" Event Stream ")
                .borders(Borders::ALL)
                .border_style(border_style())
                .bg(PANEL_BG),
        )
    }
}
