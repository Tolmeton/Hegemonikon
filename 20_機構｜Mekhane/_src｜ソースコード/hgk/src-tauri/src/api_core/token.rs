// Token cache reader — Python cortex_client.py が書いた
// /tmp/.cortex_token_cache を Rust が読む共有方式

use std::fs;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

const TOKEN_CACHE_PATH: &str = "/tmp/.cortex_token_cache";
const TOKEN_TTL_SECS: u64 = 3300; // 55 minutes (same as Python)

/// Read cached OAuth token from shared file cache.
/// Returns None if cache is missing, expired, or malformed.
pub fn read_cached_token() -> Option<String> {
    let path = Path::new(TOKEN_CACHE_PATH);
    if !path.exists() {
        return None;
    }

    let content = fs::read_to_string(path).ok()?;
    let mut lines = content.lines();

    let token = lines.next()?.trim().to_string();
    let timestamp_str = lines.next()?.trim().to_string();
    let cached_at: f64 = timestamp_str.parse().ok()?;

    // Check expiry
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()?
        .as_secs_f64();

    if (now - cached_at) > TOKEN_TTL_SECS as f64 {
        return None; // Expired
    }

    if token.is_empty() || !token.starts_with("ya29.") {
        return None; // Invalid token format
    }

    Some(token)
}

/// Get Cortex project ID from loadCodeAssist cache
pub fn read_cached_project() -> Option<String> {
    let cache_path = "/tmp/.cortex_project_cache";
    let path = Path::new(cache_path);
    if !path.exists() {
        return None;
    }
    fs::read_to_string(path).ok().map(|s| s.trim().to_string()).filter(|s| !s.is_empty())
}
