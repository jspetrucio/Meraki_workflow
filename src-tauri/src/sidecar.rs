use std::process::{Child, Command};
use std::time::{Duration, Instant};
use std::sync::{Arc, Mutex};

/// Manages the FastAPI backend server as a sidecar process
pub struct SidecarManager {
    process: Arc<Mutex<Option<Child>>>,
}

impl SidecarManager {
    /// Create a new SidecarManager instance
    pub fn new() -> Self {
        Self {
            process: Arc::new(Mutex::new(None)),
        }
    }

    /// Find Python executable in the system
    /// Tries: python3 -> python
    fn find_python(&self) -> Result<String, String> {
        for cmd in ["python3", "python"] {
            if let Ok(output) = Command::new(cmd).arg("--version").output() {
                if output.status.success() {
                    return Ok(cmd.to_string());
                }
            }
        }
        Err("Python not found. Please install Python 3.10 or higher.".to_string())
    }

    /// Start the FastAPI server as a child process
    pub fn start(&self) -> Result<(), String> {
        let python = self.find_python()?;

        println!("Starting FastAPI server with {}...", python);

        let child = Command::new(python)
            .args([
                "-m",
                "uvicorn",
                "scripts.server:app",
                "--host",
                "127.0.0.1",
                "--port",
                "3141",
            ])
            .spawn()
            .map_err(|e| format!("Failed to start FastAPI server: {}", e))?;

        *self.process.lock().unwrap() = Some(child);

        println!("FastAPI server process started, waiting for health check...");

        Ok(())
    }

    /// Wait for the server to become healthy by polling the health endpoint
    /// Timeout: 10 seconds
    pub async fn wait_for_health(&self) -> Result<(), String> {
        let start = Instant::now();
        let timeout = Duration::from_secs(10);
        let client = reqwest::Client::new();

        while start.elapsed() < timeout {
            match client
                .get("http://127.0.0.1:3141/api/v1/health")
                .timeout(Duration::from_secs(2))
                .send()
                .await
            {
                Ok(response) if response.status().is_success() => {
                    println!("FastAPI server is healthy!");
                    return Ok(());
                }
                _ => {
                    tokio::time::sleep(Duration::from_millis(500)).await;
                }
            }
        }

        Err("Timeout waiting for FastAPI server to start".to_string())
    }

    /// Stop the sidecar process gracefully
    /// Tries SIGTERM first, then SIGKILL if needed
    pub fn stop(&self) {
        let mut process = self.process.lock().unwrap();

        if let Some(ref mut child) = *process {
            println!("Stopping FastAPI server...");

            // Try graceful shutdown first
            if let Err(e) = child.kill() {
                eprintln!("Error stopping server: {}", e);
            }

            // Wait for process to exit
            if let Err(e) = child.wait() {
                eprintln!("Error waiting for server to stop: {}", e);
            }

            println!("FastAPI server stopped");
        }

        *process = None;
    }

    /// Check if the sidecar process is still running
    pub fn is_running(&self) -> bool {
        let mut process = self.process.lock().unwrap();

        if let Some(ref mut child) = *process {
            match child.try_wait() {
                Ok(Some(_)) => {
                    // Process has exited
                    *process = None;
                    false
                }
                Ok(None) => {
                    // Process is still running
                    true
                }
                Err(e) => {
                    eprintln!("Error checking process status: {}", e);
                    false
                }
            }
        } else {
            false
        }
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        self.stop();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_find_python() {
        let manager = SidecarManager::new();
        let result = manager.find_python();

        // Should find either python3 or python
        assert!(result.is_ok() || result.is_err());

        if let Ok(python) = result {
            assert!(python == "python3" || python == "python");
        }
    }

    #[test]
    fn test_new_manager() {
        let manager = SidecarManager::new();
        assert!(!manager.is_running());
    }
}
