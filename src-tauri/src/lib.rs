use serde_json::{json, Value};
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use tauri::path::BaseDirectory;
use tauri::AppHandle;
use tauri::Manager;

/// Helper to resolve sidecar path across different build environments (Dev vs Production)
fn resolve_sidecar(app: &AppHandle, name: &str) -> Result<PathBuf, String> {
    let triple = env!("TAURI_ENV_TARGET_TRIPLE");
    let paths = [
        app.path().resolve(name, BaseDirectory::Resource),
        app.path().resolve(
            format!("binaries/{}-{}", name, triple),
            BaseDirectory::Resource,
        ),
        app.path()
            .resolve(format!("binaries/{}", name), BaseDirectory::Resource),
    ];

    for path_res in paths {
        if let Ok(p) = path_res {
            if p.exists() {
                return Ok(p);
            }
        }
    }

    let dev_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("binaries");
    let dev_paths = [
        dev_dir.join(format!("{}-{}", name, triple)),
        dev_dir.join(name),
    ];
    for p in dev_paths {
        if p.exists() {
            return Ok(p);
        }
    }

    Err(format!("Sidecar {} not found", name))
}

#[tauri::command]
fn list_sessions(app: AppHandle) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;
    let output = Command::new(&exe)
        .arg("list_sessions")
        .output()
        .map_err(|e| e.to_string())?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

#[tauri::command]
fn get_session_results(app: AppHandle, folder_id: String) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;
    let output = Command::new(&exe)
        .arg("get_session_results")
        .arg(folder_id)
        .output()
        .map_err(|e| e.to_string())?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

#[tauri::command]
fn save_credentials(app: AppHandle, file_path: String) -> Result<String, String> {
    let content = fs::read_to_string(&file_path).map_err(|e| e.to_string())?;

    // Validate JSON structure locally before saving
    let _: Value =
        serde_json::from_str(&content).map_err(|_| "Invalid JSON format in credentials file")?;

    let app_data_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    fs::create_dir_all(&app_data_dir).map_err(|e| e.to_string())?;
    let saved_path = app_data_dir.join("credentials.json");
    fs::write(&saved_path, content).map_err(|e| e.to_string())?;

    Ok(json!({"status": "success", "location": saved_path.to_string_lossy()}).to_string())
}

#[tauri::command]
fn authenticate_google(app: AppHandle, credentials_path: Option<String>) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;
    let creds_path = match credentials_path {
        Some(path) => path,
        None => {
            let p = app
                .path()
                .app_data_dir()
                .map_err(|e| e.to_string())?
                .join("credentials.json");
            if !p.exists() {
                return Err("No credentials found. Please upload credentials.json first.".into());
            }
            p.to_string_lossy().to_string()
        }
    };

    let output = Command::new(&exe)
        .arg("authenticate")
        .arg(&creds_path)
        .output()
        .map_err(|e| format!("Failed to run authenticator: {}", e))?;

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

#[tauri::command]
fn check_auth_status(app: AppHandle) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;
    let output = Command::new(&exe)
        .arg("check_status")
        .output()
        .map_err(|e| e.to_string())?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();

    if stdout.trim().is_empty() {
        return Ok(
            json!({"status": "not_authenticated", "message": "No response from sidecar"})
                .to_string(),
        );
    }
    Ok(stdout)
}

#[tauri::command]
fn start_batch_generation(
    app: AppHandle,
    template_name: String,
    group_data_json: String,
    variables_json: String,
) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;

    let output = Command::new(&exe)
        .arg("batch_generate")
        .arg(&template_name)
        .arg(&group_data_json)
        .arg(&variables_json)
        .output()
        .map_err(|e| format!("Sidecar execution error: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if !output.status.success() {
        return Err(format!("Sidecar failed: {}", stderr));
    }

    Ok(stdout)
}

#[tauri::command]
fn save_email_settings(app: AppHandle, settings: String) -> Result<String, String> {
    let app_data_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    fs::create_dir_all(&app_data_dir).map_err(|e| e.to_string())?;

    let settings_path = app_data_dir.join("email_settings.json");
    fs::write(&settings_path, settings).map_err(|e| e.to_string())?;

    Ok(json!({"status": "success"}).to_string())
}

#[tauri::command]
fn get_email_settings(app: AppHandle) -> Result<String, String> {
    let app_data_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let settings_path = app_data_dir.join("email_settings.json");

    if !settings_path.exists() {
        return Ok("{}".into());
    }

    let content = fs::read_to_string(settings_path).map_err(|e| e.to_string())?;
    Ok(content)
}

#[tauri::command]
fn send_emails(
    app: tauri::AppHandle,
    email_settings_json: String,
    group_data_json: String,
    form_results_json: String,
) -> Result<String, String> {
    let exe = resolve_sidecar(&app, "google_auth")?;

    let output = std::process::Command::new(&exe)
        .arg("send_emails")
        .arg(email_settings_json)
        .arg(group_data_json)
        .arg(form_results_json)
        .output()
        .map_err(|e| format!("Failed to execute sidecar: {}", e))?;

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            save_credentials,
            authenticate_google,
            check_auth_status,
            start_batch_generation,
            list_sessions,
            get_session_results,
            save_email_settings,
            get_email_settings,
            send_emails,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
