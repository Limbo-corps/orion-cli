//! Animated visual effects, powered by [`tachyonfx`].
//!
//! Effects are post-processing passes applied to the already-rendered frame
//! buffer each tick. [`Effects`] owns the named effects, exposes small
//! `on_*` triggers that [`crate::app::App`] calls on state changes, and
//! `render_*` passes that [`crate::ui`] calls with the relevant screen region
//! and the frame's elapsed time.
//!
//! The recipes are adapted from junkdog's `exabind` tachyonfx tech demo:
//! a layered sweep+coalesce intro (its `open_category`), a per-keystroke
//! "click" flash (its `key_press`), and a border glow that pulses while the
//! assistant is busy (its LED-border idea, scoped to border cells via
//! [`CellFilter::Outer`]).

use ratatui::{
    Frame,
    layout::{Margin, Rect},
    style::Color,
};
use tachyonfx::{CellFilter, Duration, Effect, EffectRenderer, Interpolation, Motion, Shader, fx};

use crate::theme;

/// Owns every animation in the client and drives it frame by frame.
pub struct Effects {
    /// One-shot full-screen reveal played once on launch.
    startup: Effect,
    /// Endless, gentle "breathing" glow on the header accent.
    header_shimmer: Effect,
    /// Endless cyan border pulse — rendered only while the assistant is busy.
    thinking: Effect,
    /// Brief "materialize" pass when a new message bubble appears.
    message_in: Option<Effect>,
    /// Brief tint flash on the status bar for connection / state changes.
    status_pulse: Option<Effect>,
    /// Brief accent flash on the prompt for each keystroke.
    prompt_flash: Option<Effect>,
}

impl Effects {
    pub fn new() -> Self {
        Self {
            startup: startup_effect(),
            header_shimmer: header_shimmer_effect(),
            thinking: thinking_effect(),
            message_in: None,
            status_pulse: None,
            prompt_flash: None,
        }
    }

    // --- triggers: called from `App` when state changes -------------------

    /// A new message appeared — play a short materialize over the transcript.
    pub fn on_message(&mut self) {
        self.message_in = Some(message_in_effect());
    }

    /// Connection / activity state changed — flash the status bar in `color`.
    pub fn on_status_change(&mut self, color: Color) {
        self.status_pulse = Some(status_pulse_effect(color));
    }

    /// A key was typed into the prompt — flash the input accent.
    pub fn on_keystroke(&mut self) {
        self.prompt_flash = Some(prompt_flash_effect());
    }

    // --- render passes: called from `ui::draw` after widgets render -------

    pub fn render_startup(&mut self, frame: &mut Frame, area: Rect, dt: Duration) {
        if self.startup.running() {
            frame.render_effect(&mut self.startup, area, dt);
        }
    }

    pub fn render_header(&mut self, frame: &mut Frame, area: Rect, dt: Duration) {
        frame.render_effect(&mut self.header_shimmer, area, dt);
    }

    /// Pulse the transcript border while `active` (assistant busy).
    pub fn render_thinking(&mut self, frame: &mut Frame, area: Rect, dt: Duration, active: bool) {
        if active {
            frame.render_effect(&mut self.thinking, area, dt);
        }
    }

    pub fn render_conversation(&mut self, frame: &mut Frame, area: Rect, dt: Duration) {
        Self::render_optional(&mut self.message_in, frame, area, dt);
    }

    pub fn render_status(&mut self, frame: &mut Frame, area: Rect, dt: Duration) {
        Self::render_optional(&mut self.status_pulse, frame, area, dt);
    }

    pub fn render_prompt(&mut self, frame: &mut Frame, area: Rect, dt: Duration) {
        Self::render_optional(&mut self.prompt_flash, frame, area, dt);
    }

    /// Render a one-shot effect if it is still running, otherwise drop it.
    fn render_optional(slot: &mut Option<Effect>, frame: &mut Frame, area: Rect, dt: Duration) {
        if let Some(effect) = slot.as_mut() {
            if effect.running() {
                frame.render_effect(effect, area, dt);
            } else {
                *slot = None;
            }
        }
    }
}

impl Default for Effects {
    fn default() -> Self {
        Self::new()
    }
}

// --- effect recipes -------------------------------------------------------

/// Layered intro: a left-to-right reveal with the whole frame coalescing in
/// underneath it (adapted from exabind's `open_category`).
fn startup_effect() -> Effect {
    fx::parallel(&[
        fx::sweep_in(
            Motion::LeftToRight,
            25,
            10,
            theme::BG,
            (850, Interpolation::QuadOut),
        ),
        fx::coalesce((900, Interpolation::SineOut)),
    ])
}

/// A hue/lightness ping-pong on the header — a clearly visible "breathing"
/// glow so the UI reads as alive even while idle and offline.
fn header_shimmer_effect() -> Effect {
    fx::repeating(fx::ping_pong(fx::hsl_shift(
        Some([28.0, 0.0, 32.0]),
        None,
        (1100, Interpolation::SineInOut),
    )))
}

/// Endless cyan pulse restricted to the border ring of whatever area it is
/// rendered on. Used on the transcript panel while the assistant is busy.
fn thinking_effect() -> Effect {
    fx::repeating(fx::ping_pong(
        fx::fade_to_fg(theme::ORION_ACCENT, (700, Interpolation::SineInOut))
            .with_filter(CellFilter::Outer(Margin::new(1, 1))),
    ))
}

/// New bubbles coalesce into place rather than snapping in.
fn message_in_effect() -> Effect {
    fx::coalesce((380, Interpolation::SineOut))
}

/// A short foreground tint that fades back to normal.
fn status_pulse_effect(color: Color) -> Effect {
    fx::fade_from_fg(color, (500, Interpolation::SineOut))
}

/// A quick "click" flash on the prompt for tactile keystroke feedback
/// (adapted from exabind's `key_press`).
fn prompt_flash_effect() -> Effect {
    fx::fade_from_fg(theme::ORION_ACCENT, (220, Interpolation::SineOut))
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::{Terminal, backend::TestBackend};

    /// Every effect must process over a real buffer without panicking.
    #[test]
    fn effects_render_without_panicking() {
        let mut terminal = Terminal::new(TestBackend::new(80, 24)).unwrap();
        let mut effects = Effects::new();
        effects.on_message();
        effects.on_status_change(theme::OK);
        effects.on_keystroke();

        // Drive several frames so one-shot effects run to completion.
        for _ in 0..20 {
            terminal
                .draw(|frame| {
                    let area = frame.area();
                    let dt = Duration::from_millis(16);
                    effects.render_startup(frame, area, dt);
                    effects.render_header(frame, area, dt);
                    effects.render_thinking(frame, area, dt, true);
                    effects.render_conversation(frame, area, dt);
                    effects.render_status(frame, area, dt);
                    effects.render_prompt(frame, area, dt);
                })
                .unwrap();
        }
    }
}
