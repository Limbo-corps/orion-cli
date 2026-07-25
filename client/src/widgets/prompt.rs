use ratatui::{
    Frame,
    layout::Rect,
    style::{Modifier, Style, Stylize},
    text::{Line, Span},
    widgets::{Block, BorderType, Borders, Paragraph, Wrap},
};

use crate::theme::{FG, ORION_ACCENT, PANEL_BG, border_style};

pub struct PromptWidget;

impl PromptWidget {
    pub fn render(
        frame: &mut Frame,
        area: Rect,
        input: &str,
        cursor_position: usize,
        is_focused: bool,
    ) {
        let border_color = if is_focused {
            ORION_ACCENT
        } else {
            border_style().fg.unwrap_or(ORION_ACCENT)
        };

        let prompt_prefix = "> ";
        let prompt_text = vec![Line::from(vec![
            Span::styled(
                prompt_prefix,
                Style::default()
                    .fg(ORION_ACCENT)
                    .add_modifier(Modifier::BOLD),
            ),
            Span::styled(input, Style::default().fg(FG)),
        ])];

        let widget = Paragraph::new(prompt_text)
            .wrap(Wrap { trim: false })
            .block(
                Block::default()
                    .title(" prompt ")
                    .borders(Borders::ALL)
                    .border_type(BorderType::Rounded)
                    .border_style(Style::default().fg(border_color))
                    .bg(PANEL_BG),
            );

        frame.render_widget(widget, area);

        // Place terminal cursor at active cursor_position index
        if is_focused {
            let cursor_x = area.x + 1 + prompt_prefix.len() as u16 + cursor_position as u16;
            let cursor_y = area.y + 1;

            if cursor_x < area.x + area.width - 1 {
                frame.set_cursor_position((cursor_x, cursor_y));
            }
        }
    }
}
