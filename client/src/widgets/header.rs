use ratatui::{
    layout::Rect,
    style::{Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Paragraph},
};

use crate::theme::{DIM, MUTED, ORION_ACCENT, ORION_EDGE, ORION_ICON};

pub struct BannerWidget;

impl BannerWidget {
    pub fn render(area: Rect) -> Paragraph<'static> {
        // Line 1: ◉ ORION   ·   voice-native assistant
        let header_line = Line::from(vec![
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
            Span::styled("   ·   ", Style::default().fg(DIM)),
            Span::styled("voice-native assistant", Style::default().fg(MUTED)),
        ]);

        // Line 2: Dynamic horizontal rule stretching across the available width
        let width = area.width.max(24) as usize;
        let rule_line = Line::from(Span::styled(
            "─".repeat(width),
            Style::default().fg(ORION_EDGE),
        ));

        Paragraph::new(vec![header_line, rule_line]).block(Block::default())
    }
}
