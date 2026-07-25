mod app;
mod ipc;
mod theme;
mod widgets;

use std::error::Error;
use std::time::Duration;

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
const TICK_RATE: Duration = Duration::from_millis(100);

#[tokio::main]
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
            app.mode = "CONNECTED".to_string();
        }
        Err(err) => {
            app.mode = format!("OFFLINE ({})", err);
        }
    }

    // Main Async Event Loop
    loop {
        terminal.draw(|f| app.draw(f))?;

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
                                        KeyCode::Char('i') | KeyCode::Char('a') => {
                                            app.input_mode = InputMode::Insert;
                                        }
                                        KeyCode::Char('q') | KeyCode::Esc => {
                                            app.should_quit = true;
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
                                        KeyCode::Backspace => {
                                            app.input.pop();
                                        }
                                        KeyCode::Char(c) => {
                                            app.input.push(c);
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
                    // Wrap in Some() so this branch returns Option<Result<RuntimeEvent, IpcError>>
                    Some(client.next_event().await)
                } else {
                    // Returns Option<Result<RuntimeEvent, IpcError>>
                    tokio::time::sleep(Duration::from_secs(3600)).await;
                    None
                }
            } => {
                match runtime_event {
                    Some(Ok(event)) => app.handle_runtime_event(event),
                    Some(Err(err)) => app.mode = format!("IPC ERROR: {}", err),
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
