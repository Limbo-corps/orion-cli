//! Layout and rendering for the ORION client.
//!
//! Keeps all geometry in one place: [`App`] holds state, this module turns
//! that state into a frame, then lets [`crate::effects`] post-process it.

use ratatui::{
    Frame,
    layout::{Constraint, Direction, Layout},
    widgets::Block,
};
use tachyonfx::Duration;

use crate::app::{App, InputMode};
use crate::theme::default_style;
use crate::widgets::{
    events::EventStreamWidget, header::BannerWidget, prompt::PromptWidget, status::StatusWidget,
};

/// Render one frame: widgets first, then the animated effect passes.
pub fn draw(app: &mut App, frame: &mut Frame, dt: Duration) {
    let area = frame.area();

    // Base background fill.
    frame.render_widget(Block::default().style(default_style()), area);

    // Vertical: header · content · status.
    let main = Layout::default()
        .direction(Direction::Vertical)
        .margin(1)
        .constraints([
            Constraint::Length(2),
            Constraint::Min(0),
            Constraint::Length(1),
        ])
        .split(area);

    // Content: conversation column (66%) · event stream (34%).
    let content = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(66), Constraint::Percentage(34)])
        .split(main[1]);

    // Left column: transcript (flex) · prompt (3 rows).
    let left = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(0), Constraint::Length(3)])
        .split(content[0]);

    let header_area = main[0];
    let convo_area = left[0];
    let prompt_area = left[1];
    let events_area = content[1];
    let status_area = main[2];

    // Cache prompt bounds for mouse hit-testing.
    app.prompt_area = prompt_area;

    // --- widgets --------------------------------------------------------
    frame.render_widget(BannerWidget::render(header_area), header_area);
    app.conversation.render(frame, convo_area);

    let is_focused = app.input_mode == InputMode::Insert;
    PromptWidget::render(
        frame,
        prompt_area,
        &app.input,
        app.cursor_position,
        is_focused,
    );

    frame.render_widget(EventStreamWidget::render(), events_area);
    frame.render_widget(
        StatusWidget::render(&app.mode, &app.input_mode, app.events_count, app.frame_tick),
        status_area,
    );

    // --- effects (post-process the composed buffer) ---------------------
    let busy =
        matches!(app.mode.as_str(), "THINKING" | "RESPONDING") || app.mode.starts_with("TOOL");

    app.effects.render_header(frame, header_area, dt);
    app.effects.render_thinking(frame, convo_area, dt, busy);
    app.effects.render_conversation(frame, convo_area, dt);
    app.effects.render_prompt(frame, prompt_area, dt);
    app.effects.render_status(frame, status_area, dt);
    app.effects.render_startup(frame, area, dt);
}
