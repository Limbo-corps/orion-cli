mod app;
mod audio;
mod effects;
mod ipc;
mod theme;
mod ui;
mod widgets;

use std::error::Error;
use std::time::{Duration, Instant};

use crossterm::{
    event::{DisableMouseCapture, EnableMouseCapture, Event, EventStream, KeyCode, KeyModifiers},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use futures_util::StreamExt;
use ratatui::{Terminal, backend::CrosstermBackend};
use tokio::time::interval;

use app::{App, InputMode};
use ipc::client::OrionClient;

const SOCKET_PATH: &str = "/tmp/orion.sock";
// ~30 FPS so tachyonfx effects animate smoothly instead of stepping.
const TICK_RATE: Duration = Duration::from_millis(33);

// Single-threaded runtime: the audio input stream is `!Send`, so the app
// state (which owns it) must stay on one thread.
#[tokio::main(flavor = "current_thread")]
async fn main() -> Result<(), Box<dyn Error>> {
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = std::io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;

    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut app = App::new();

    // Initialize async terminal event stream
    let mut reader = EventStream::new();
    let mut tick_interval = interval(TICK_RATE);

    // Attempt initial socket connection to Python runtime
    match OrionClient::connect(SOCKET_PATH).await {
        Ok(client) => {
            app.client = Some(client);
            app.on_connected();
        }
        Err(err) => {
            app.on_offline(err.to_string());
        }
    }

    // Main Async Event Loop
    let mut last_frame = Instant::now();
    loop {
        let dt = last_frame.elapsed();
        last_frame = Instant::now();
        terminal.draw(|f| ui::draw(&mut app, f, dt.into()))?;

        if app.should_quit {
            break;
        }

        tokio::select! {
            _ = tick_interval.tick() => {
                app.on_tick();
            }

            // Read terminal/crossterm input events
            maybe_event = reader.next() => {
                if let Some(Ok(event)) = maybe_event {
                    match event {
                        Event::Key(key) => {
                            if key.modifiers.contains(KeyModifiers::CONTROL)
                                && key.code == KeyCode::Char('c')
                            {
                                app.should_quit = true;
                            } else {
                                match app.input_mode {
                                    InputMode::Normal => match key.code {
                                        // Entering Insert Mode
                                        KeyCode::Char('i') | KeyCode::Char('a') => {
                                            app.input_mode = InputMode::Insert;
                                        }
                                        // Quit
                                        KeyCode::Char('q') | KeyCode::Esc => {
                                            app.should_quit = true;
                                        }
                                        // Push-to-talk: toggle voice recording
                                        KeyCode::Char('v') => {
                                            app.toggle_recording().await;
                                        }
                                        // Interrupt assistant speech
                                        KeyCode::Char('s') => {
                                            app.interrupt_speech();
                                        }
                                        // Conversation Scrolling (Vim keys & standard navigation)
                                        KeyCode::Up | KeyCode::Char('k') => {
                                            app.conversation.scroll_up(1);
                                        }
                                        KeyCode::Down | KeyCode::Char('j') => {
                                            app.conversation.scroll_down(1);
                                        }
                                        KeyCode::PageUp => {
                                            app.conversation.scroll_up(5);
                                        }
                                        KeyCode::PageDown => {
                                            app.conversation.scroll_down(5);
                                        }
                                        KeyCode::Home => {
                                            app.conversation.scroll_up(usize::MAX);
                                        }
                                        KeyCode::End | KeyCode::Char('G') => {
                                            app.conversation.scroll_to_bottom();
                                        }
                                        _ => {}
                                    },
                                    InputMode::Insert => match key.code {
                                        KeyCode::Esc => {
                                            app.input_mode = InputMode::Normal;
                                        }
                                        KeyCode::Enter => {
                                            app.submit_prompt().await;
                                        }
                                        KeyCode::Left => {
                                            app.move_cursor_left();
                                        }
                                        KeyCode::Right => {
                                            app.move_cursor_right();
                                        }
                                        KeyCode::Backspace => {
                                            app.delete_char();
                                        }
                                        KeyCode::Char(c) => {
                                            app.enter_char(c);
                                        }
                                        _ => {}
                                    },
                                }
                            }
                        }
                        Event::Mouse(mouse_event) => {
                            app.handle_mouse(mouse_event);
                        }
                        _ => {}
                    }
                }
            }

            // Receive IPC stream events from Orion Python Runtime
            runtime_event = async {
                if let Some(client) = &mut app.client {
                    Some(client.next_event().await)
                } else {
                    tokio::time::sleep(Duration::from_secs(3600)).await;
                    None
                }
            } => {
                match runtime_event {
                    Some(Ok(event)) => app.handle_runtime_event(event),
                    Some(Err(err)) => app.on_ipc_error(err.to_string()),
                    None => {}
                }
            }
        }
    }

    // Restore terminal state on exit
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    Ok(())
}
