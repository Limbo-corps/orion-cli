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
use crate::widgets::{header::BannerWidget, prompt::PromptWidget, status::StatusWidget};

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

    // Cache panel bounds for mouse hit-testing / scroll routing.
    app.prompt_area = prompt_area;
    app.events_area = events_area;

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

    app.events.render(frame, events_area);
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::app::App;
    use crate::ipc::events::RuntimeEvent;
    use ratatui::{Terminal, backend::TestBackend};
    use tachyonfx::Duration;

    /// Feed a realistic sequence of runtime events through the app and render
    /// several frames — the event stream, activity logs, and effects must all
    /// process without panicking.
    #[test]
    fn renders_events_and_activities_without_panicking() {
        let mut app = App::new();
        app.handle_runtime_event(RuntimeEvent::Connected);
        app.handle_runtime_event(RuntimeEvent::ToolStarted {
            name: "read_file".into(),
        });
        app.handle_runtime_event(RuntimeEvent::ToolFinished {
            name: "read_file".into(),
            success: true,
        });
        app.handle_runtime_event(RuntimeEvent::ToolFinished {
            name: "write_file".into(),
            success: false,
        });
        app.handle_runtime_event(RuntimeEvent::AssistantStart);
        app.handle_runtime_event(RuntimeEvent::AssistantChunk("hello".into()));
        app.handle_runtime_event(RuntimeEvent::AssistantEnd);

        let mut terminal = Terminal::new(TestBackend::new(100, 30)).unwrap();
        for _ in 0..5 {
            terminal
                .draw(|frame| draw(&mut app, frame, Duration::from_millis(16)))
                .unwrap();
        }
    }
}
