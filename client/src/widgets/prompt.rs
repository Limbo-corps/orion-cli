use ratatui::{
    style::{Modifier, Style, Stylize},
    text::{Line, Span},
    widgets::{Block, BorderType, Borders, Paragraph}
};

use crate::theme::{border_style, FG, ORION_ACCENT, PANEL_BG};

pub struct PromptWidget;

impl PromptWidget {
    pub fn render(input:&str, is_focused: bool) -> Paragraph<'static> {
        let border_color = if is_focused {
            ORION_ACCENT
        } else {
            border_style().fg.unwrap_or(ORION_ACCENT)
        };

        let prompt_text = vec![Line::from(vec![
                    Span::styled(
                        "> ",
                        Style::default().fg(ORION_ACCENT).add_modifier(Modifier::BOLD),
                    ),
                    Span::styled(input.to_string(), Style::default().fg(FG)),
                ])];

        Paragraph::new(prompt_text).block(
                    Block::default()
                        .title(" prompt ")
                        .borders(Borders::ALL)
                        .border_type(BorderType::Rounded)
                        .border_style(Style::default().fg(border_color))
                        .bg(PANEL_BG),
                )
    }
}
