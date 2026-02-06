use tauri::{AppHandle, Manager};
use tauri_plugin_updater::UpdaterExt;
use std::time::Duration;

/// Check for updates in the background on app startup
pub async fn check_for_updates_on_startup(app: AppHandle) {
    println!("Starting background update check...");

    // Spawn non-blocking update check
    tauri::async_runtime::spawn(async move {
        if let Err(e) = check_and_notify_update(&app).await {
            eprintln!("Update check failed: {}", e);
            // Don't crash the app on update check failures
        }
    });
}

/// Periodically check for updates (called from setup)
pub fn start_periodic_update_check(app: AppHandle) {
    tauri::async_runtime::spawn(async move {
        loop {
            // Wait 24 hours
            tokio::time::sleep(Duration::from_secs(24 * 60 * 60)).await;

            println!("Running periodic update check...");
            if let Err(e) = check_and_notify_update(&app).await {
                eprintln!("Periodic update check failed: {}", e);
            }
        }
    });
}

/// Check for updates and emit event to frontend if available
async fn check_and_notify_update(app: &AppHandle) -> Result<(), String> {
    let updater = app.updater();

    match updater {
        Ok(updater_instance) => {
            match updater_instance.check().await {
                Ok(Some(update)) => {
                    let version = update.version.clone();
                    let body = update.body.clone().unwrap_or_default();

                    println!("Update available: version {}", version);

                    // Emit event to frontend
                    if let Err(e) = app.emit("update-available", serde_json::json!({
                        "version": version,
                        "notes": body,
                        "date": update.date.clone(),
                    })) {
                        eprintln!("Failed to emit update-available event: {}", e);
                    }

                    Ok(())
                }
                Ok(None) => {
                    println!("No update available");
                    Ok(())
                }
                Err(e) => {
                    Err(format!("Failed to check for updates: {}", e))
                }
            }
        }
        Err(e) => {
            Err(format!("Failed to get updater instance: {}", e))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_updater_module_compiles() {
        // Just verify the module compiles correctly
        assert!(true);
    }
}
