#!/usr/bin/env python3
"""
Dual Chat Stream v3 — http.client 版 (chunked encoding 自動処理)
"""
import http.client
import struct
import json
import subprocess
import re
import signal
import sys
import time
import base64
import threading

signal.signal(signal.SIGALRM, lambda s,f: (print("\n⏰ Timeout."), sys.exit(0)))
signal.alarm(25)

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

def stream_listener(port, csrf, results):
    """ストリーム購読 (別スレッド)"""
    import socket
    conn = http.client.HTTPConnection(f'127.0.0.1:{port}', timeout=60)
    envelope = grpc_envelope({'clientType': 1})
    
    headers = {
        'Content-Type': 'application/grpc-web+json',
        'x-codeium-csrf-token': csrf,
        'x-grpc-web': '1',
    }
    
    conn.request('POST',
        '/exa.chat_client_server_pb.ChatClientServerService/StartChatClientRequestStream',
        body=envelope, headers=headers)
    
    resp = conn.getresponse()
    print(f"📡 Stream: {resp.status} {resp.reason}")
    
    # Set shorter read timeout for polling
    conn.sock.settimeout(5.0)
    
    chunk_count = 0
    start = time.time()
    
    while time.time() - start < 55:
        try:
            # http.client は chunked encoding を自動でデコード
            data = resp.read(65535)
            if not data:
                print("📡 Stream ended (empty read)")
                break
        except socket.timeout:
            elapsed = int(time.time() - start)
            print(f"  ⏳ Waiting... ({elapsed}s)")
            continue
        except Exception as e:
            print(f"📡 Read error: {e}")
            break
        
        frames = parse_grpc_frames(data)
        for flag, msg_data in frames:
            chunk_count += 1
            try:
                text = msg_data.decode('utf-8', errors='strict')
                j = json.loads(text)
                at = j.get('sendActionToChatPanel', {}).get('actionType', '')
                
                if at in ('updateUserStatus', 'pollMcpServerStates', 'setApiKey'):
                    if chunk_count <= 3:
                        print(f"  [{chunk_count}] {at} (init)")
                    continue
                
                ts = time.strftime('%H:%M:%S')
                payload_list = j.get('sendActionToChatPanel', {}).get('payload', [])
                print(f"  [{ts}] action={at} payloads={len(payload_list)}")
                
                for p in payload_list[:2]:
                    if isinstance(p, str) and len(p) > 20:
                        try:
                            dec = base64.b64decode(p).decode('utf-8', errors='replace')
                            kw = ['think', '2+2', 'answer', 'step', '=', 'raw']
                            if any(k in dec.lower() for k in kw):
                                print(f"    🧠 {dec[:300]}")
                            else:
                                print(f"    📦 {dec[:100]}")
                        except: pass
                    elif isinstance(p, str):
                        print(f"    → {p}")
                
                results.append(j)
                
            except (json.JSONDecodeError, UnicodeDecodeError):
                if chunk_count <= 5:
                    print(f"  [{chunk_count}] proto ({len(msg_data)}B) f={flag} hex={msg_data[:16].hex()}")
    
    print(f"  📡 Total chunks: {chunk_count}")
    conn.close()

def main():
    port, csrf = detect_ls()
    print(f"LS: fd10={port}, csrf={csrf[:8]}...")
    
    results = []
    print("\n📡 Listening to ChatClientServerService stream for 60 seconds...")
    print("   👉 PLEASE SEND A CLAUDE MESSAGE FROM THE IDE UI NOW 👈")
    
    # Run synchronously with a longer timeout
    global stream_timeout
    stream_timeout = 60
    
    stream_listener(port, csrf, results)
    
    print(f"\n✅ Done. Captured {len(results)} non-init events.")

if __name__ == '__main__':
    # Increase the global alarm timeout
    signal.alarm(65)
    main()
