use std::path::PathBuf;
use std::process::Command;
use std::fs;
use tauri::path::BaseDirectory;
use tauri::AppHandle;
use tauri::Manager;

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

fn resolve_sidecar(app: &AppHandle, name: &str) -> Result<PathBuf, String> {
    let triple = env!("TAURI_ENV_TARGET_TRIPLE");
    
    // Try plain name in resource bin directory (how Tauri v2 bundles for AppImage)
    if let Ok(p) = app.path().resolve(name, BaseDirectory::Resource) {
        if p.exists() {
            return Ok(p);
        }
    }
    
    // Try target-triple suffixed path in binaries subdirectory (for other bundle types)
    let rel_suffixed = format!("binaries/{}-{}", name, triple);
    if let Ok(p) = app.path().resolve(rel_suffixed, BaseDirectory::Resource) {
        if p.exists() {
            return Ok(p);
        }
    }
    
    // Try non-suffixed resource path in binaries subdirectory
    let rel = format!("binaries/{}", name);
    if let Ok(p) = app.path().resolve(rel, BaseDirectory::Resource) {
        if p.exists() {
            return Ok(p);
        }
    }
    
    // Fallback to workspace path in dev (check both suffixed and plain)
    let dev_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("binaries");
    let dev_suffixed = dev_dir.join(format!("{}-{}", name, triple));
    if dev_suffixed.exists() {
        return Ok(dev_suffixed);
    }
    let dev_plain = dev_dir.join(name);
    if dev_plain.exists() {
        return Ok(dev_plain);
    }
    
    Err(format!(
        "Sidecar not found: {} (checked resource and dev paths)",
        name
    ))
}

#[tauri::command]
fn validate_credentials_file(app: AppHandle, file_path: String) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "json_processor")?;

    let output = Command::new(&exe)
        .arg(&file_path)
        .output()
        .map_err(|e| format!("Failed to execute sidecar: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Sidecar failed: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

#[tauri::command]
fn save_credentials(app: AppHandle, file_path: String) -> Result<String, String> {
    // First validate the credentials file
    let validation_result = validate_credentials_file(app.clone(), file_path.clone())?;
    
    // Parse validation result to check status
    let validation: serde_json::Value = serde_json::from_str(&validation_result)
        .map_err(|e| format!("Failed to parse validation result: {}", e))?;
    
    if validation["status"] != "success" {
        return Err(validation["message"].as_str().unwrap_or("Validation failed").to_string());
    }
    
    // Read the credentials file
    let credentials_content = fs::read_to_string(&file_path)
        .map_err(|e| format!("Failed to read credentials file: {}", e))?;
    
    // Get app data directory
    let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;
    
    // Ensure the directory exists
    fs::create_dir_all(&app_data_dir)
        .map_err(|e| format!("Failed to create app data directory: {}", e))?;
    
    // Save to app data directory
    let saved_path = app_data_dir.join("credentials.json");
    fs::write(&saved_path, credentials_content)
        .map_err(|e| format!("Failed to save credentials: {}", e))?;
    
    let result = serde_json::json!({
        "status": "success",
        "message": "Credentials saved successfully",
        "location": saved_path.to_string_lossy()
    });
    
    Ok(result.to_string())
}

#[tauri::command]
fn get_saved_credentials(app: AppHandle) -> Result<String, String> {
    let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;
    
    let saved_path = app_data_dir.join("credentials.json");
    
    if !saved_path.exists() {
        let result = serde_json::json!({
            "status": "not_found",
            "message": "No saved credentials found"
        });
        return Ok(result.to_string());
    }
    
    let result = serde_json::json!({
        "status": "found",
        "path": saved_path.to_string_lossy()
    });
    
    Ok(result.to_string())
}

#[tauri::command]
fn authenticate_google(app: AppHandle, credentials_path: Option<String>) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;
    
    // Use provided path or get saved credentials
    let creds_path = if let Some(path) = credentials_path {
        path
    } else {
        let app_data_dir = app.path().app_data_dir()
            .map_err(|e| format!("Failed to get app data directory: {}", e))?;
        let saved_path = app_data_dir.join("credentials.json");
        
        if !saved_path.exists() {
            return Err("No credentials found. Please save credentials first.".to_string());
        }
        
        saved_path.to_string_lossy().to_string()
    };

    let output = Command::new(&exe)
        .arg("authenticate")
        .arg(&creds_path)
        .output()
        .map_err(|e| format!("Failed to execute sidecar: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Sidecar failed: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

#[tauri::command]
fn check_auth_status(app: AppHandle) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;

    let output = Command::new(&exe)
        .arg("check_status")
        .output()
        .map_err(|e| format!("Failed to execute sidecar: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Sidecar failed: {}", stderr));
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    Ok(stdout.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            validate_credentials_file,
            save_credentials,
            get_saved_credentials,
            authenticate_google,
            check_auth_status
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
