use std::env;
use std::path::PathBuf;

fn main() {
    // Copy Python scripts to the bundle
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").unwrap();
    let src_dir = PathBuf::from(&manifest_dir).join("src");

    // Copy Python scripts to bundle directory
    let python_files = vec!["google_auth.py", "json_processor.py"];
    for file in python_files {
        let src = src_dir.join(file);
        println!("cargo:rerun-if-changed={}", src.display());
    }

    tauri_build::build()
}
