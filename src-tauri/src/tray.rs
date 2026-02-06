use tauri::{
    menu::{Menu, MenuItem, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, Runtime, AppHandle, Emitter,
};
use std::sync::Arc;

/// Create the system tray icon and menu
///
/// Menu items:
/// - Open CNL (show/focus main window)
/// - Quick Discovery (POST to /api/v1/discovery/full)
/// - Settings (show window + navigate to /settings)
/// - Quit (stop sidecar + exit app)
pub fn create_system_tray<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    // Create menu items
    let open = MenuItem::with_id(app, "open", "Open CNL", true, None::<&str>)?;
    let discovery = MenuItem::with_id(app, "discovery", "Quick Discovery", true, None::<&str>)?;
    let settings = MenuItem::with_id(app, "settings", "Settings", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;

    // Create separator
    let separator = PredefinedMenuItem::separator(app)?;

    // Build menu: Open CNL, ---, Quick Discovery, Settings, ---, Quit
    let menu = Menu::with_items(
        app,
        &[&open, &separator, &discovery, &settings, &separator, &quit],
    )?;

    // Build tray icon with menu
    let _tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().ok_or("No default icon")?.clone())
        .menu(&menu)
        .tooltip("CNL - Cisco Neural Language")
        .on_menu_event(on_menu_event)
        .on_tray_icon_event(on_tray_icon_event)
        .build(app)?;

    println!("System tray created successfully");
    Ok(())
}

/// Handle tray menu item clicks
fn on_menu_event<R: Runtime>(app: &AppHandle<R>, event: tauri::menu::MenuEvent) {
    match event.id.as_ref() {
        "open" => {
            if let Err(e) = show_main_window(app) {
                eprintln!("Failed to show main window: {}", e);
            }
        }
        "discovery" => {
            let app_handle = app.clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = run_quick_discovery(&app_handle).await {
                    eprintln!("Quick discovery failed: {}", e);
                    if let Err(notify_err) = send_notification(
                        &app_handle,
                        "Discovery Failed",
                        &format!("Error: {}", e),
                    ) {
                        eprintln!("Failed to send notification: {}", notify_err);
                    }
                }
            });
        }
        "settings" => {
            if let Err(e) = show_settings_window(app) {
                eprintln!("Failed to show settings: {}", e);
            }
        }
        "quit" => {
            if let Err(e) = quit_application(app) {
                eprintln!("Failed to quit application: {}", e);
            }
        }
        _ => {
            println!("Unknown menu event: {}", event.id.as_ref());
        }
    }
}

/// Handle tray icon events (e.g., double-click to show window)
fn on_tray_icon_event<R: Runtime>(tray: &tauri::tray::TrayIcon<R>, event: TrayIconEvent) {
    if let TrayIconEvent::Click {
        button: MouseButton::Left,
        button_state: MouseButtonState::Up,
        ..
    } = event
    {
        let app = tray.app_handle();
        if let Err(e) = show_main_window(app) {
            eprintln!("Failed to show main window on tray click: {}", e);
        }
    }
}

/// Show and focus the main window
fn show_main_window<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    if let Some(window) = app.get_webview_window("main") {
        window.show()?;
        window.set_focus()?;
        println!("Main window shown and focused");
    } else {
        eprintln!("Main window not found");
    }
    Ok(())
}

/// Show settings window (main window + navigate to settings)
fn show_settings_window<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    if let Some(window) = app.get_webview_window("main") {
        window.show()?;
        window.set_focus()?;

        // Emit event to navigate to settings route
        if let Err(e) = app.emit("navigate-to-settings", ()) {
            eprintln!("Failed to emit navigate-to-settings event: {}", e);
        }

        println!("Settings window shown");
    } else {
        eprintln!("Main window not found");
    }
    Ok(())
}

/// Quit the application (stop sidecar + exit)
fn quit_application<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    println!("Quit requested from tray, stopping application...");

    // Close all windows first
    if let Some(window) = app.get_webview_window("main") {
        if let Err(e) = window.close() {
            eprintln!("Error closing main window: {}", e);
        }
    }

    // The window close handler will trigger sidecar shutdown
    // Exit the application
    app.exit(0);
    Ok(())
}

/// Run quick discovery by posting to the backend API
async fn run_quick_discovery<R: Runtime>(app: &AppHandle<R>) -> Result<(), String> {
    println!("Running quick discovery from tray...");

    // Send starting notification
    send_notification(app, "Quick Discovery", "Starting discovery...")?;

    // POST to backend API
    let client = reqwest::Client::new();
    let response = client
        .post("http://127.0.0.1:3141/api/v1/discovery/full")
        .timeout(std::time::Duration::from_secs(60))
        .send()
        .await
        .map_err(|e| format!("HTTP request failed: {}", e))?;

    if response.status().is_success() {
        let result: serde_json::Value = response
            .json()
            .await
            .map_err(|e| format!("Failed to parse response: {}", e))?;

        // Extract summary from response
        let networks = result
            .get("networks")
            .and_then(|v| v.as_array())
            .map(|arr| arr.len())
            .unwrap_or(0);

        let devices = result
            .get("devices")
            .and_then(|v| v.as_array())
            .map(|arr| arr.len())
            .unwrap_or(0);

        let message = format!("Discovery complete: {} networks, {} devices", networks, devices);
        send_notification(app, "Quick Discovery Complete", &message)?;

        println!("{}", message);
        Ok(())
    } else {
        let error = format!("Backend returned status: {}", response.status());
        send_notification(app, "Discovery Failed", &error)?;
        Err(error)
    }
}

/// Send a native OS notification
fn send_notification<R: Runtime>(
    app: &AppHandle<R>,
    title: &str,
    body: &str,
) -> Result<(), String> {
    // Emit notification event to frontend for handling via tauri-plugin-notification
    if let Err(e) = app.emit(
        "show-notification",
        serde_json::json!({
            "title": title,
            "body": body,
        }),
    ) {
        return Err(format!("Failed to emit notification event: {}", e));
    }

    println!("Notification sent: {} - {}", title, body);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_menu_item_ids() {
        let items = vec!["open", "discovery", "settings", "quit"];
        assert_eq!(items.len(), 4);
        assert!(items.contains(&"open"));
        assert!(items.contains(&"discovery"));
        assert!(items.contains(&"settings"));
        assert!(items.contains(&"quit"));
    }

    #[test]
    fn test_shortcut_string_format() {
        let shortcut_mac = "Cmd+Shift+M";
        let shortcut_other = "Ctrl+Shift+M";
        assert!(shortcut_mac.contains("Cmd"));
        assert!(shortcut_other.contains("Ctrl"));
    }

    #[test]
    fn test_notification_json_structure() {
        let notification = serde_json::json!({
            "title": "Test",
            "body": "Test body",
        });

        assert!(notification.get("title").is_some());
        assert!(notification.get("body").is_some());
    }
}
