# PROOF: mekhane/ochema/capture_ls_metadata.py
# PURPOSE: ochema モジュールの capture_ls_metadata
"""mitmdump addon: LS → cloudcode-pa gRPC メタデータキャプチャ。

LS が cloudcode-pa に送信する全ての HTTP/2 ヘッダーとリクエストボディを
JSONL ファイルにダンプする。Claude リクエスト時の認証ヘッダーと
ルーティングメタデータを特定するのが目的。

Usage:
    mitmdump -s capture_ls_metadata.py -p 8888 --set confdir=~/.mitmproxy

Then set LS environment:
    HTTPS_PROXY=http://127.0.0.1:8888

DX-010 §N.9 T6b: LS は cloudcode-pa (2404:6800:4004:*) のみに接続。
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from mitmproxy import http, ctx

OUTPUT_DIR = Path.home() / ".cache" / "ochema" / "ls_capture"
JSONL_FILE = OUTPUT_DIR / "ls_metadata.jsonl"

# Hosts to capture (from DX-010 §N.9 dynamic analysis + §N.10 mitmproxy discovery)
CAPTURE_HOSTS = {
    "daily-cloudcode-pa.googleapis.com",
    "cloudaicompanion.googleapis.com",
    "us-east5-aiplatform.googleapis.com",
    "iamcredentials.googleapis.com",  # SA Impersonation (if any)
    "oauth2.googleapis.com",
    "antigravity-unleash.goog",  # Feature flag server (Unleash) — DX-010 §N.10
    "otel.gitkraken.com",  # Telemetry (OpenTelemetry)
}

# gRPC-specific headers of interest
GRPC_HEADERS = {
    "grpc-encoding", "grpc-accept-encoding", "grpc-timeout",
    "grpc-message-type", "te", "content-type",
    "x-goog-request-params", "x-goog-api-client",
    "x-goog-user-project", "x-goog-api-key",
    "authorization", "x-gfe-request-context",
}


def _should_capture(flow: http.HTTPFlow) -> bool:
    """Check if this flow should be captured."""
    host = flow.request.pretty_host
    return any(h in host for h in CAPTURE_HOSTS) or "googleapis.com" in host


def _sanitize_auth(value: str) -> str:
    """Truncate long auth tokens for safety."""
    if len(value) > 50:
        return value[:20] + "..." + value[-10:]
    return value


class LSMetadataCapture:
    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self._count = 0
        ctx.log.info(f"LS Metadata Capture: output → {JSONL_FILE}")

    def request(self, flow: http.HTTPFlow) -> None:
        if not _should_capture(flow):
            return

        self._count += 1
        req = flow.request

        # Extract all headers
        headers = {}
        for k, v in req.headers.items():
            k_lower = k.lower()
            if k_lower == "authorization":
                headers[k] = _sanitize_auth(v)
            else:
                headers[k] = v

        # Extract body (truncated for large payloads)
        body_text = ""
        body_json = None
        if req.content:
            try:
                body_json = json.loads(req.content)
                body_text = json.dumps(body_json, ensure_ascii=False)[:5000]
            except (json.JSONDecodeError, UnicodeDecodeError):
                body_text = f"<binary {len(req.content)} bytes>"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "seq": self._count,
            "method": req.method,
            "url": req.pretty_url,
            "host": req.pretty_host,
            "path": req.path,
            "http_version": req.http_version,
            "headers": headers,
            "body_preview": body_text[:2000] if body_text else None,
            "body_json": body_json,
            "content_length": len(req.content) if req.content else 0,
        }

        # Highlight important findings
        grpc_meta = {k: v for k, v in headers.items() if k.lower() in GRPC_HEADERS}
        if grpc_meta:
            entry["grpc_metadata"] = grpc_meta

        # Log to console
        ctx.log.info(
            f"[{self._count}] {req.method} {req.pretty_host}{req.path} "
            f"({len(headers)} headers, {len(req.content or b'')} bytes)"
        )

        # Append to JSONL
        with open(JSONL_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def response(self, flow: http.HTTPFlow) -> None:
        if not _should_capture(flow):
            return

        resp = flow.response
        if resp is None:
            return

        # Log response status
        ctx.log.info(
            f"  → {resp.status_code} ({len(resp.content or b'')} bytes)"
        )

        # Capture full response for important endpoints
        resp_body = None
        resp_json = None
        if resp.content:
            try:
                resp_json = json.loads(resp.content)
                resp_body = json.dumps(resp_json, ensure_ascii=False)[:50000]
            except (json.JSONDecodeError, UnicodeDecodeError):
                resp_body = f"<binary {len(resp.content)} bytes>"

        # Also capture request headers that we might have missed
        req_headers = {}
        for k, v in flow.request.headers.items():
            k_lower = k.lower()
            if k_lower == "authorization":
                req_headers[k] = _sanitize_auth(v)
            else:
                req_headers[k] = v

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "url": flow.request.pretty_url,
            "path": flow.request.path,
            "status": resp.status_code,
            "request_headers": req_headers,
            "response_headers": dict(resp.headers),
            "response_body_preview": resp_body[:5000] if resp_body else None,
            "response_json": resp_json if resp_json and len(json.dumps(resp_json)) < 100000 else None,
            "response_size": len(resp.content or b''),
        }

        with open(JSONL_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


addons = [LSMetadataCapture()]
