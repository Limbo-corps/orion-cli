use ratatui::style::{Color, Style};

// Colors matching theme.py
pub const BG: Color = Color::Rgb(0x0b, 0x0c, 0x0e);
pub const PANEL_BG: Color = Color::Rgb(0x10, 0x12, 0x16);
pub const FG: Color = Color::Rgb(0xe2, 0xe6, 0xea);
pub const MUTED: Color = Color::Rgb(0x8a, 0x92, 0x9c);
pub const DIM: Color = Color::Rgb(0x4a, 0x4f, 0x57);
pub const BORDER: Color = Color::Rgb(0x24, 0x2a, 0x31);

// Status colors
pub const DANGER: Color = Color::Rgb(0xe0, 0x73, 0x6f);
pub const OK: Color = Color::Rgb(0x8f, 0xce, 0x9b);

// Identity colors
pub const ORION_ACCENT: Color = Color::Rgb(0x35, 0xc9, 0xff);
pub const ORION_EDGE: Color = Color::Rgb(0x25, 0x97, 0xc9);
pub const ORION_BUBBLE: Color = Color::Rgb(0x0d, 0x1a, 0x22);
pub const ORION_ICON: &str = "◉";

pub const USER_ACCENT: Color = Color::Rgb(0xb9, 0xa7, 0xff);
pub const USER_EDGE: Color = Color::Rgb(0x7c, 0x5c, 0xff);
pub const USER_BUBBLE: Color = Color::Rgb(0x14, 0x13, 0x27);
pub const USER_NAME: &str = "Me";

pub fn state_color(mode: &str) -> Color {
    match mode {
        "IDLE" => MUTED,
        "RECORDING" | "ERROR" => DANGER,
        "TRANSCRIBING" | "THINKING" | "SYNTHESIZING" => ORION_ACCENT,
        _ => FG,
    }
}

pub fn default_style() -> Style {
    Style::default().fg(FG).bg(BG)
}

pub fn border_style() -> Style {
    Style::default().fg(BORDER)
}
