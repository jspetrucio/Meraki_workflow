// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;
mod tray;
mod commands;
mod updater;

use sidecar::SidecarManager;
use std::sync::Arc;
use tauri::{Manager, State};

/// Tauri state for the sidecar manager
struct AppState {
    sidecar: Arc<SidecarManager>,
}

/// Tauri command to check if the backend is healthy
#[tauri::command]
async fn check_backend_health() -> Result<String, String> {
    let client = reqwest::Client::new();

    match client
        .get("http://127.0.0.1:3141/api/v1/health")
        .send()
        .await
    {
        Ok(response) if response.status().is_success() => {
            Ok("Backend is healthy".to_string())
        }
        Ok(response) => Err(format!("Backend returned status: {}", response.status())),
        Err(e) => Err(format!("Backend is not responding: {}", e)),
    }
}

/// Tauri command to check if sidecar is running
#[tauri::command]
fn is_backend_running(state: State<AppState>) -> bool {
    state.sidecar.is_running()
}

/// Setup global keyboard shortcut (Cmd+Shift+M on macOS, Ctrl+Shift+M on others)
fn setup_global_shortcut(app: &tauri::AppHandle) -> Result<(), String> {
    use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};

    // Determine platform-specific shortcut
    let shortcut_str = if cfg!(target_os = "macos") {
        "Cmd+Shift+M"
    } else {
        "Ctrl+Shift+M"
    };

    let shortcut: Shortcut = shortcut_str
        .parse()
        .map_err(|e| format!("Failed to parse shortcut: {:?}", e))?;

    let app_handle = app.clone();
    app.global_shortcut()
        .on_shortcut(shortcut, move |_app, _shortcut, _event| {
            if let Some(window) = app_handle.get_webview_window("main") {
                if window.is_visible().unwrap_or(false) {
                    // Window is visible, focus it
                    if let Err(e) = window.set_focus() {
                        eprintln!("Failed to focus window: {}", e);
                    }
                } else {
                    // Window is hidden, show it
                    if let Err(e) = window.show() {
                        eprintln!("Failed to show window: {}", e);
                    }
                    if let Err(e) = window.set_focus() {
                        eprintln!("Failed to focus window: {}", e);
                    }
                }
            }
        })
        .map_err(|e| format!("Failed to register shortcut: {:?}", e))?;

    println!("Global shortcut registered: {}", shortcut_str);
    Ok(())
}

#[tokio::main]
async fn main() {
    // Create sidecar manager
    let sidecar = Arc::new(SidecarManager::new());
    let sidecar_clone = Arc::clone(&sidecar);

    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(move |app| {
            println!("CNL Application starting...");

            // Start the FastAPI sidecar
            if let Err(e) = sidecar_clone.start() {
                eprintln!("Failed to start backend server: {}", e);
                return Err(e.into());
            }

            // Wait for the backend to be ready
            let sidecar_for_health = Arc::clone(&sidecar_clone);
            tauri::async_runtime::spawn(async move {
                if let Err(e) = sidecar_for_health.wait_for_health().await {
                    eprintln!("Backend health check failed: {}", e);
                }
            });

            // Create system tray
            if let Err(e) = tray::create_system_tray(&app.handle()) {
                eprintln!("Failed to create system tray: {}", e);
                return Err(e.into());
            }

            // Handle window close event - minimize to tray instead of quitting
            let sidecar_for_close = Arc::clone(&sidecar_clone);
            let window = app.get_webview_window("main").unwrap();

            window.on_window_event(move |event| {
                match event {
                    tauri::WindowEvent::CloseRequested { api, .. } => {
                        // Hide window instead of closing (minimize to tray)
                        if let Some(window) = api.window() {
                            if let Err(e) = window.hide() {
                                eprintln!("Failed to hide window: {}", e);
                            } else {
                                println!("Window hidden (minimized to tray)");
                            }
                        }
                        // Prevent the window from actually closing
                        api.prevent_close();
                    }
                    tauri::WindowEvent::Destroyed => {
                        // Only stop sidecar when window is actually destroyed (app quit)
                        println!("Window destroyed, stopping backend...");
                        sidecar_for_close.stop();
                    }
                    _ => {}
                }
            });

            // Register global keyboard shortcut
            let app_handle = app.handle().clone();
            if let Err(e) = setup_global_shortcut(&app_handle) {
                eprintln!("Failed to register global shortcut: {}", e);
                // Non-critical error, continue startup
            }

            // Start background update check
            let app_for_updates = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                updater::check_for_updates_on_startup(app_for_updates).await;
            });

            // Start periodic update checks (every 24 hours)
            let app_for_periodic = app.handle().clone();
            updater::start_periodic_update_check(app_for_periodic);

            println!("CNL Application started successfully");
            Ok(())
        })
        .manage(AppState { sidecar })
        .invoke_handler(tauri::generate_handler![
            check_backend_health,
            is_backend_running,
            commands::is_autostart_enabled,
            commands::enable_autostart,
            commands::disable_autostart,
            commands::show_notification,
            commands::check_notification_permission,
            commands::update_global_shortcut,
            commands::get_version,
            commands::check_for_updates,
            commands::install_update
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
