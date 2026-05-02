// Generic API Proxy — Rust から Python API を叩く汎用コマンド
// フロントエンドから HTTP を完全に排除するための中間レイヤー
//
// JS: invoke('api_proxy', { request: { path, method, body } })
//   → Rust: reqwest → Python API (127.0.0.1:9696)
//   → JSON を JS に返す

use reqwest::Client;
use serde::{Deserialize, Serialize};

const API_BASE: &str = "http://127.0.0.1:9696";

#[derive(Debug, Deserialize)]
pub struct ProxyRequest {
    pub path: String,
    pub method: Option<String>,
    pub body: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct ProxyError {
    pub status: u16,
    pub message: String,
}

/// Generic API proxy: forwards requests from JS to Python API via Rust
pub async fn proxy_request(req: ProxyRequest) -> Result<serde_json::Value, String> {
    let url = format!("{}{}", API_BASE, req.path);
    let method = req.method.as_deref().unwrap_or("GET");
    let client = Client::new();

    let request_builder = match method {
        "POST" => {
            let mut rb = client.post(&url)
                .header("Content-Type", "application/json");
            if let Some(ref body) = req.body {
                rb = rb.body(body.clone());
            }
            rb
        }
        "PUT" => {
            let mut rb = client.put(&url)
                .header("Content-Type", "application/json");
            if let Some(ref body) = req.body {
                rb = rb.body(body.clone());
            }
            rb
        }
        "DELETE" => client.delete(&url),
        _ => client.get(&url), // GET is default
    };

    let response = request_builder
        .send()
        .await
        .map_err(|e| format!("Proxy request failed: {}", e))?;

    let status = response.status();
    let body_text = response.text().await
        .map_err(|e| format!("Failed to read response body: {}", e))?;

    if !status.is_success() {
        return Err(format!("API Error {}: {}", status.as_u16(), body_text));
    }

    // Parse as JSON, fall back to wrapping text in a JSON object
    serde_json::from_str(&body_text)
        .or_else(|_| Ok(serde_json::json!({ "text": body_text })))
}
