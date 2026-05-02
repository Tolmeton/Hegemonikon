// LLM Streaming — Cortex API (cloudcode-pa) を reqwest で叩き、
// Tauri Channel でフロントエンドにストリーミングする
//
// HTTP を完全に排除: JS → invoke("cortex_stream") → Rust reqwest → Cortex API
// SSE パースは Rust 側で行い、チャンクごとに Channel.send() で JS に push

use reqwest::Client;
use serde::{Deserialize, Serialize};
use tauri::ipc::Channel;

use super::token;

const CORTEX_BASE_URL: &str = "https://cloudcode-pa.googleapis.com/v1internal";

/// Request from frontend
#[derive(Debug, Deserialize)]
pub struct StreamRequest {
    pub message: String,
    #[serde(default = "default_model")]
    pub model: String,
    pub system_instruction: Option<String>,
    pub temperature: Option<f64>,
    pub max_tokens: Option<u32>,
    pub thinking_budget: Option<u32>,
}

fn default_model() -> String {
    "gemini-2.5-flash".to_string()
}

/// Chunk sent to frontend via Channel
#[derive(Debug, Clone, Serialize)]
pub struct StreamChunk {
    pub text: String,
    pub done: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

/// Build the Cortex generateContent request body
fn build_request_body(req: &StreamRequest, project: &str) -> serde_json::Value {
    let mut body = serde_json::json!({
        "model": format!("models/{}", req.model),
        "contents": [{
            "role": "user",
            "parts": [{"text": &req.message}]
        }],
        "generationConfig": {
            "temperature": req.temperature.unwrap_or(1.0),
            "maxOutputTokens": req.max_tokens.unwrap_or(8192),
        },
        "project": project,
    });

    // System instruction
    if let Some(ref si) = req.system_instruction {
        body["systemInstruction"] = serde_json::json!({
            "parts": [{"text": si}]
        });
    }

    // Thinking budget
    if let Some(budget) = req.thinking_budget {
        body["generationConfig"]["thinkingConfig"] = serde_json::json!({
            "thinkingBudget": budget
        });
    }

    body
}

/// Stream Cortex API response and push chunks via Tauri Channel
pub async fn stream_cortex(
    req: StreamRequest,
    on_chunk: Channel<StreamChunk>,
) -> Result<(), String> {
    // 1. Get token from shared cache
    let token = token::read_cached_token()
        .ok_or_else(|| "OAuth token not available. Run Python API server first to populate cache.".to_string())?;

    // 2. Get project
    let project = token::read_cached_project()
        .unwrap_or_else(|| "cloudaicompanion".to_string());

    // 3. Build request
    let body = build_request_body(&req, &project);
    let url = format!("{}:streamGenerateContent?alt=sse", CORTEX_BASE_URL);

    // 4. Send request via reqwest
    let client = Client::new();
    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("Content-Type", "application/json")
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body_text = response.text().await.unwrap_or_default();
        return Err(format!("Cortex API error {}: {}", status, body_text));
    }

    // 5. Stream SSE response
    let mut buffer = String::new();
    let mut stream = response.bytes_stream();

    use futures_util::StreamExt;

    while let Some(chunk_result) = stream.next().await {
        let chunk_bytes = chunk_result.map_err(|e| format!("Stream read error: {}", e))?;
        let chunk_str = String::from_utf8_lossy(&chunk_bytes);
        buffer.push_str(&chunk_str);

        // Process complete SSE events
        while let Some(boundary) = buffer.find("\n\n") {
            let event_block = buffer[..boundary].to_string();
            buffer = buffer[boundary + 2..].to_string();

            for line in event_block.lines() {
                if let Some(data) = line.strip_prefix("data: ") {
                    if let Ok(parsed) = serde_json::from_str::<serde_json::Value>(data) {
                        // Extract text from Cortex response format
                        if let Some(candidates) = parsed
                            .pointer("/response/candidates")
                            .or_else(|| parsed.get("candidates"))
                            .and_then(|c| c.as_array())
                        {
                            for candidate in candidates {
                                if let Some(parts) = candidate
                                    .pointer("/content/parts")
                                    .and_then(|p| p.as_array())
                                {
                                    for part in parts {
                                        if let Some(text) = part.get("text").and_then(|t| t.as_str()) {
                                            let _ = on_chunk.send(StreamChunk {
                                                text: text.to_string(),
                                                done: false,
                                                model: None,
                                                error: None,
                                            });
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // 6. Send done signal
    let _ = on_chunk.send(StreamChunk {
        text: String::new(),
        done: true,
        model: Some(req.model),
        error: None,
    });

    Ok(())
}
