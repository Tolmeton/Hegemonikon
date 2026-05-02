#!/usr/bin/env python3
"""
Stream Listener v4 — raw socket で gRPC-web ストリームを監視。
IDE から送信されたチャットのイベントを観測する。
安全: read-only (StartChatClientRequestStream は subscribe のみ)
"""
import socket
import struct
import json
import subprocess
import re
import signal
import sys
import time
import base64

LISTEN_SECONDS = 90

signal.signal(signal.SIGALRM, lambda s, f: (print("\n⏰ Timeout."), sys.exit(0)))
signal.alarm(LISTEN_SECONDS + 5)


def detect_ls():
    pid = subprocess.check_output(
        "pgrep -f 'language_server_linux.*workspace_id' | head -1",
        shell=True, text=True).strip()
    cmdline = open(f'/proc/{pid}/cmdline').read().replace('\0', '\n')
    csrf = re.search(r'--csrf_token\n(.+)', cmdline).group(1)
    port = subprocess.check_output(
        f"ss -tlnp --no-header | grep 'pid={pid}' | grep -P 'fd=10\\b' | grep -oP ':\\K\\d+' | head -1",
        shell=True, text=True).strip()
    return int(port), csrf


def grpc_envelope(data: dict) -> bytes:
    payload = json.dumps(data).encode()
    return struct.pack('>BI', 0, len(payload)) + payload


def parse_grpc_frames(raw: bytes):
    """gRPC-web フレームをパース"""
    frames = []
    pos = 0
    while pos + 5 <= len(raw):
        flag = raw[pos]
        length = struct.unpack('>I', raw[pos+1:pos+5])[0]
        if length > 500000:
            pos += 1
            continue
        if pos + 5 + length > len(raw):
            break
        data = raw[pos+5:pos+5+length]
        frames.append((flag, data))
        pos += 5 + length
    return frames


def read_chunked_frame(sock, timeout=5.0):
    """chunked transfer encoding から 1 チャンクを読む。タイムアウトで None 返却。"""
    sock.settimeout(timeout)
    try:
        # Read chunk size line
        size_line = b''
        while not size_line.endswith(b'\r\n'):
            b = sock.recv(1)
            if not b:
                return None  # Connection closed
            size_line += b
        
        chunk_size = int(size_line.strip(), 16)
        if chunk_size == 0:
            return None  # End of chunks
        
        # Read chunk data
        data = b''
        while len(data) < chunk_size:
            remaining = chunk_size - len(data)
            part = sock.recv(min(remaining, 65535))
            if not part:
                return None
            data += part
        
        # Read trailing \r\n
        sock.recv(2)
        return data
    
    except socket.timeout:
        return b'__timeout__'
    except Exception as e:
        print(f"  ❌ Read error: {e}")
        return None


def main():
    port, csrf = detect_ls()
    print(f"LS: fd10={port}, csrf={csrf[:8]}...")

    # Build raw HTTP request
    envelope = grpc_envelope({'clientType': 1})
    path = '/exa.chat_client_server_pb.ChatClientServerService/StartChatClientRequestStream'
    
    request = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        f"Content-Type: application/grpc-web+json\r\n"
        f"x-codeium-csrf-token: {csrf}\r\n"
        f"x-grpc-web: 1\r\n"
        f"Content-Length: {len(envelope)}\r\n"
        f"\r\n"
    ).encode() + envelope

    # Connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', port))
    sock.sendall(request)

    # Read HTTP response headers
    sock.settimeout(10)
    header_data = b''
    while b'\r\n\r\n' not in header_data:
        b = sock.recv(1)
        if not b:
            print("❌ Connection closed during headers")
            return
        header_data += b

    headers = header_data.decode('utf-8', errors='replace')
    status_line = headers.split('\r\n')[0]
    print(f"📡 Stream: {status_line}")

    if '200' not in status_line:
        print(f"❌ Non-200: {headers}")
        return

    print(f"📡 Listening for {LISTEN_SECONDS}s...")
    print("   👉 IDE のチャットパネルから何か送信してください 👈\n")

    chunk_count = 0
    event_count = 0
    start = time.time()

    while time.time() - start < LISTEN_SECONDS:
        data = read_chunked_frame(sock)
        
        if data is None:
            print("📡 Stream closed.")
            break
        
        if data == b'__timeout__':
            elapsed = int(time.time() - start)
            if elapsed % 15 == 0:
                print(f"  ⏳ Waiting... ({elapsed}s)")
            continue
        
        chunk_count += 1
        
        # Parse gRPC frames
        frames = parse_grpc_frames(data)
        for flag, msg_data in frames:
            try:
                text = msg_data.decode('utf-8', errors='strict')
                j = json.loads(text)
                at = j.get('sendActionToChatPanel', {}).get('actionType', '')
                
                # Skip noisy init events
                if at in ('updateUserStatus', 'pollMcpServerStates', 'setApiKey',
                          'initialAck', 'setServerModelConfig', 'setPanelAction'):
                    if chunk_count <= 10:
                        print(f"  [{chunk_count}] {at} (init)")
                    continue
                
                ts = time.strftime('%H:%M:%S')
                event_count += 1
                
                # ChatClientRequest / sendActionToChatPanel
                payload_list = j.get('sendActionToChatPanel', {}).get('payload', [])
                print(f"\n  🔔 [{ts}] #{event_count} action={at} payloads={len(payload_list)}")
                
                # Print the raw JSON keys at top level
                top_keys = list(j.keys())
                if top_keys != ['sendActionToChatPanel']:
                    print(f"     keys: {top_keys}")
                
                # Look for interesting data
                for pi, p in enumerate(payload_list[:5]):
                    if isinstance(p, str) and len(p) > 20:
                        try:
                            dec = base64.b64decode(p).decode('utf-8', errors='replace')
                            kw = ['think', 'raw_thinking', 'answer', 'step', 'model',
                                  'claude', 'gemini', 'response', 'content']
                            if any(k in dec.lower() for k in kw):
                                print(f"     🧠 PAYLOAD[{pi}]: {dec[:500]}")
                            else:
                                print(f"     📦 PAYLOAD[{pi}]: {dec[:200]}")
                        except:
                            print(f"     📦 PAYLOAD[{pi}]: (base64 decode failed) {p[:60]}")
                    elif isinstance(p, dict):
                        print(f"     📋 PAYLOAD[{pi}]: {json.dumps(p, ensure_ascii=False)[:300]}")
                    elif isinstance(p, str):
                        print(f"     → PAYLOAD[{pi}]: {p}")
                    else:
                        print(f"     ? PAYLOAD[{pi}]: {type(p).__name__} = {str(p)[:100]}")
                
                # Also dump full JSON for truly interesting events
                if at not in ('', 'updatePanelState') and event_count <= 20:
                    print(f"     📄 FULL: {json.dumps(j, ensure_ascii=False)[:600]}")
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                print(f"  [{chunk_count}] proto binary ({len(msg_data)}B) flag={flag} hex={msg_data[:20].hex()}")

    elapsed = int(time.time() - start)
    print(f"\n📡 Done. {chunk_count} chunks, {event_count} events in {elapsed}s.")
    sock.close()


if __name__ == '__main__':
    main()
