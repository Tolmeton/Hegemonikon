#!/usr/bin/env python3
"""
H2 Stream Probe — fd10 ConnectRPC bidirectional stream via HTTP/2

Probes:
  1. HTTP/2 unary (GetCascadeModelConfigData) — 接続確認
  2. HTTP/2 stream (StartChatClientRequestStream) — thinking ストリーム受信
  3. HTTP/2 stream (StreamCascadePanelReactiveUpdates) — パネル更新ストリーム
"""

import subprocess
import re
import json
import sys
import asyncio

import httpx


def detect_ls():
    """LS PID, fd10 port, CSRF token を自動検出"""
    r = subprocess.run(
        ['pgrep', '-f', 'language_server_linux.*workspace_id'],
        capture_output=True, text=True
    )
    pid = r.stdout.strip().split('\n')[0]
    if not pid:
        raise RuntimeError("LS process not found")

    # CSRF
    cmdline = open(f'/proc/{pid}/cmdline').read().replace('\0', '\n')
    csrf_match = re.search(r'--csrf_token\n(.+)', cmdline)
    if not csrf_match:
        raise RuntimeError("CSRF token not found in cmdline")
    csrf = csrf_match.group(1)

    # fd10 port via ss
    ss_r = subprocess.run(['ss', '-tlnp', '--no-header'], capture_output=True, text=True, timeout=5)
    port = None
    for line in ss_r.stdout.strip().split('\n'):
        if f'pid={pid}' in line and 'fd=10' in line:
            m = re.search(r':(\d+)\s', line)
            if m:
                port = int(m.group(1))
                break

    if not port:
        raise RuntimeError(f"fd10 port not found for PID {pid}")

    return {
        'pid': pid,
        'port': port,
        'csrf': csrf,
        'base_url': f'http://127.0.0.1:{port}',
    }


def get_headers(csrf: str) -> dict:
    return {
        'content-type': 'application/json',
        'x-codeium-csrf-token': csrf,
    }


async def test_h2_unary(ls_info: dict):
    """Test 1: HTTP/2 unary request"""
    print("\n=== Test 1: HTTP/2 Unary (GetCascadeModelConfigData) ===")
    async with httpx.AsyncClient(
        base_url=ls_info['base_url'],
        http2=True,
        timeout=10.0,
    ) as client:
        resp = await client.post(
            '/exa.language_server_pb.LanguageServerService/GetCascadeModelConfigData',
            headers=get_headers(ls_info['csrf']),
            json={},
        )
        print(f"HTTP version: {resp.http_version}")
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            models = data.get('modelConfigData', {}).get('modelConfigs', [])
            print(f"Models: {len(models)}")
            for m in models[:3]:
                print(f"  - {m.get('displayLabel', '?')} ({m.get('model', '?')})")
        else:
            print(f"Body: {resp.text[:200]}")


async def test_h2_stream_start_chat(ls_info: dict):
    """Test 2: HTTP/2 streaming (StartChatClientRequestStream)"""
    print("\n=== Test 2: HTTP/2 Stream (StartChatClientRequestStream) ===")

    # ConnectRPC bidirectional stream request
    # The request body for a client stream in ConnectRPC JSON format
    request_payload = {
        "userMessage": "What is 2+2? Think step by step.",
        "modelConfigId": "MODEL_PLACEHOLDER_M35",  # Claude Sonnet 4.6 Thinking
        "thinkingConfig": {
            "thinkingLevel": "THINKING_LEVEL_MEDIUM",
        },
    }

    try:
        async with httpx.AsyncClient(
            base_url=ls_info['base_url'],
            http2=True,
            timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0),
        ) as client:
            # Try streaming POST
            async with client.stream(
                'POST',
                '/exa.language_server_pb.LanguageServerService/StartChatClientRequestStream',
                headers=get_headers(ls_info['csrf']),
                json=request_payload,
            ) as resp:
                print(f"HTTP version: {resp.http_version}")
                print(f"Status: {resp.status_code}")
                print(f"Headers: {dict(resp.headers)}")

                if resp.status_code == 200:
                    chunk_count = 0
                    async for chunk in resp.aiter_bytes():
                        chunk_count += 1
                        # Try to decode as JSON (ConnectRPC JSON format)
                        try:
                            text = chunk.decode('utf-8', errors='replace')
                            print(f"\n--- Chunk {chunk_count} ({len(chunk)} bytes) ---")
                            # ConnectRPC uses NDJSON for streaming
                            for line in text.strip().split('\n'):
                                if line.strip():
                                    try:
                                        data = json.loads(line)
                                        # Look for thinking fields
                                        if 'rawThinking' in str(data):
                                            print(f"  🧠 THINKING FOUND!")
                                        print(f"  {json.dumps(data, ensure_ascii=False)[:300]}")
                                    except json.JSONDecodeError:
                                        print(f"  [raw] {line[:200]}")
                        except Exception as e:
                            print(f"  [binary] {len(chunk)} bytes: {chunk[:50].hex()}")

                        if chunk_count >= 50:
                            print("\n[Stopped after 50 chunks]")
                            break
                else:
                    body = await resp.aread()
                    print(f"Error body: {body.decode('utf-8', errors='replace')[:500]}")
    except httpx.ReadTimeout:
        print("[ReadTimeout — server may require different request format]")
    except Exception as e:
        print(f"[Error: {type(e).__name__}: {e}]")


async def test_h2_stream_panel(ls_info: dict):
    """Test 3: HTTP/2 streaming (StreamCascadePanelReactiveUpdates)"""
    print("\n=== Test 3: HTTP/2 Stream (StreamCascadePanelReactiveUpdates) ===")

    try:
        async with httpx.AsyncClient(
            base_url=ls_info['base_url'],
            http2=True,
            timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
        ) as client:
            async with client.stream(
                'POST',
                '/exa.language_server_pb.LanguageServerService/StreamCascadePanelReactiveUpdates',
                headers=get_headers(ls_info['csrf']),
                json={},
            ) as resp:
                print(f"HTTP version: {resp.http_version}")
                print(f"Status: {resp.status_code}")
                print(f"Content-Type: {resp.headers.get('content-type', 'N/A')}")

                if resp.status_code == 200:
                    chunk_count = 0
                    async for chunk in resp.aiter_bytes():
                        chunk_count += 1
                        text = chunk.decode('utf-8', errors='replace')
                        print(f"  Chunk {chunk_count}: {text[:200]}")
                        if chunk_count >= 10:
                            break
                else:
                    body = await resp.aread()
                    print(f"Error: {body.decode('utf-8', errors='replace')[:300]}")
    except httpx.ReadTimeout:
        print("[ReadTimeout — stream may be idle]")
    except Exception as e:
        print(f"[Error: {type(e).__name__}: {e}]")


async def main():
    ls_info = detect_ls()
    print(f"LS detected: PID={ls_info['pid']}, Port={ls_info['port']}")
    print(f"CSRF: {ls_info['csrf'][:8]}...")
    print(f"Base URL: {ls_info['base_url']}")

    # Test 1: HTTP/2 unary — 接続確認
    await test_h2_unary(ls_info)

    # Test 2: StartChatClientRequestStream — thinking ストリーム
    await test_h2_stream_start_chat(ls_info)

    # Test 3: Panel reactive updates
    await test_h2_stream_panel(ls_info)


if __name__ == '__main__':
    asyncio.run(main())
