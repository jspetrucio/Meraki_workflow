use tauri::{AppHandle, Manager, State};
use tauri_plugin_autostart::AutoLaunchManager;
use tauri_plugin_notification::NotificationExt;
use tauri_plugin_updater::UpdaterExt;

/// Tauri command to check if autostart is enabled
#[tauri::command]
pub fn is_autostart_enabled(autostart: State<'_, AutoLaunchManager>) -> Result<bool, String> {
    autostart
        .is_enabled()
        .map_err(|e| format!("Failed to check autostart status: {}", e))
}

/// Tauri command to enable autostart
#[tauri::command]
pub fn enable_autostart(autostart: State<'_, AutoLaunchManager>) -> Result<(), String> {
    autostart
        .enable()
        .map_err(|e| format!("Failed to enable autostart: {}", e))
}

/// Tauri command to disable autostart
#[tauri::command]
pub fn disable_autostart(autostart: State<'_, AutoLaunchManager>) -> Result<(), String> {
    autostart
        .disable()
        .map_err(|e| format!("Failed to disable autostart: {}", e))
}

/// Tauri command to show a native notification
#[tauri::command]
pub fn show_notification(
    app: tauri::AppHandle,
    title: String,
    body: String,
) -> Result<(), String> {
    app.notification()
        .builder()
        .title(title)
        .body(body)
        .show()
        .map_err(|e| format!("Failed to show notification: {}", e))
}

/// Tauri command to check notification permission status (macOS specific)
#[tauri::command]
pub async fn check_notification_permission() -> Result<String, String> {
    // On macOS, notifications require explicit permission
    // On other platforms, they work by default
    #[cfg(target_os = "macos")]
    {
        // For now, return "granted" - proper permission check requires additional APIs
        // In production, you'd use macOS specific APIs to check permission
        Ok("granted".to_string())
    }

    #[cfg(not(target_os = "macos"))]
    {
        Ok("granted".to_string())
    }
}

/// Tauri command to update global shortcut
#[tauri::command]
pub fn update_global_shortcut(
    app: tauri::AppHandle,
    new_shortcut: String,
) -> Result<(), String> {
    use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};

    // Unregister all existing shortcuts first
    if let Err(e) = app.global_shortcut().unregister_all() {
        eprintln!("Failed to unregister existing shortcuts: {:?}", e);
    }

    // Parse and register new shortcut
    let shortcut: Shortcut = new_shortcut
        .parse()
        .map_err(|e| format!("Invalid shortcut format: {:?}", e))?;

    let app_handle = app.clone();
    app.global_shortcut()
        .on_shortcut(shortcut, move |_app, _shortcut, _event| {
            if let Some(window) = app_handle.get_webview_window("main") {
                if window.is_visible().unwrap_or(false) {
                    if let Err(e) = window.set_focus() {
                        eprintln!("Failed to focus window: {}", e);
                    }
                } else {
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

    println!("Global shortcut updated to: {}", new_shortcut);
    Ok(())
}

/// Tauri command to get application version
#[tauri::command]
pub fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// Tauri command to manually check for updates
#[tauri::command]
pub async fn check_for_updates(app: AppHandle) -> Result<serde_json::Value, String> {
    let updater = app.updater().map_err(|e| format!("Failed to get updater: {}", e))?;

    match updater.check().await {
        Ok(Some(update)) => {
            let version = update.version.clone();
            Ok(serde_json::json!({
                "available": true,
                "version": version,
            }))
        }
        Ok(None) => {
            Ok(serde_json::json!({
                "available": false,
            }))
        }
        Err(e) => Err(format!("Failed to check for updates: {}", e)),
    }
}

/// Tauri command to install a pending update
#[tauri::command]
pub async fn install_update(app: AppHandle) -> Result<(), String> {
    let updater = app.updater().map_err(|e| format!("Failed to get updater: {}", e))?;

    match updater.check().await {
        Ok(Some(update)) => {
            println!("Downloading and installing update...");
            update
                .download_and_install(|chunk_length, content_length| {
                    if let Some(total) = content_length {
                        let progress = (chunk_length as f64 / total as f64) * 100.0;
                        println!("Download progress: {:.1}%", progress);
                    }
                })
                .await
                .map_err(|e| format!("Failed to install update: {}", e))?;

            println!("Update installed successfully");
            Ok(())
        }
        Ok(None) => Err("No update available".to_string()),
        Err(e) => Err(format!("Failed to check for updates: {}", e)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_notification_permission_check() {
        // Test that the function exists and returns a valid result
        let runtime = tokio::runtime::Runtime::new().unwrap();
        let result = runtime.block_on(check_notification_permission());
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "granted");
    }

    #[test]
    fn test_shortcut_string_parsing() {
        use tauri_plugin_global_shortcut::Shortcut;

        // Test valid shortcut strings
        let shortcuts = vec!["Cmd+Shift+M", "Ctrl+Shift+M", "Alt+N"];
        for shortcut_str in shortcuts {
            let result: Result<Shortcut, _> = shortcut_str.parse();
            assert!(result.is_ok(), "Failed to parse: {}", shortcut_str);
        }
    }
}
