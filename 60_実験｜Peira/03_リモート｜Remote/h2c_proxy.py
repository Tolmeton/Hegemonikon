#!/usr/bin/env python3
"""
h2c (平文 HTTP/2) 透過プロキシ — LS → cloudcode-pa 全メタデータキャプチャ。

LS は --cloud_code_endpoint に対して h2c (cleartext HTTP/2) で接続する。
このプロキシは:
  1. LS からの h2c 接続を受け付ける (TCP, 平文)
  2. HTTP/2 フレームを h2 ライブラリで完全にパースし、全ヘッダーをログ
  3. cloudcode-pa に TLS gRPC 接続を確立し、リクエストを転送
  4. レスポンスも同様にログ

Usage:
    .venv/bin/python experiments/h2c_proxy.py
    
    別ターミナルで:
    SSL_CERT_FILE=/tmp/combined_ca.pem PYTHONPATH=. .venv/bin/python experiments/ls_mitm_test.py
"""

import asyncio
import ssl
import json
import sys
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("/tmp/h2c_capture.jsonl")
LISTEN_PORT = 8443
TARGET_HOST = "daily-cloudcode-pa.googleapis.com"
TARGET_PORT = 443

# HTTP/2 preface
H2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"

# HTTP/2 frame header: 3 bytes length + 1 byte type + 1 byte flags + 4 bytes stream_id
FRAME_HEADER_SIZE = 9
FRAME_TYPES = {
    0x0: "DATA", 0x1: "HEADERS", 0x2: "PRIORITY", 0x3: "RST_STREAM",
    0x4: "SETTINGS", 0x5: "PUSH_PROMISE", 0x6: "PING", 0x7: "GOAWAY",
    0x8: "WINDOW_UPDATE", 0x9: "CONTINUATION",
}

captured_frames = []

try:
    import hpack
    HPACK_AVAILABLE = True
except ImportError:
    HPACK_AVAILABLE = False


def decode_hpack_headers(raw: bytes, decoder=None) -> list[tuple[str, str]]:
    """HPACK エンコードされたヘッダーをデコード."""
    if not HPACK_AVAILABLE or decoder is None:
        return []
    try:
        return decoder.decode(raw)
    except Exception as e:
        return [("__decode_error__", str(e))]


def parse_h2_frames(data: bytes, direction: str, hpack_dec=None) -> tuple[list[dict], bytes]:
    """HTTP/2 フレームをパースし、残りの不完全データを返す."""
    frames = []
    pos = 0
    
    while pos + FRAME_HEADER_SIZE <= len(data):
        length = int.from_bytes(data[pos:pos+3], 'big')
        frame_type = data[pos+3]
        flags = data[pos+4]
        stream_id = int.from_bytes(data[pos+5:pos+9], 'big') & 0x7FFFFFFF
        
        # 不完全フレーム
        if pos + FRAME_HEADER_SIZE + length > len(data):
            break
            
        payload = data[pos+FRAME_HEADER_SIZE:pos+FRAME_HEADER_SIZE+length]
        
        frame_info = {
            "ts": datetime.now().isoformat(),
            "dir": direction,
            "type": FRAME_TYPES.get(frame_type, f"UNKNOWN({frame_type})"),
            "stream": stream_id,
            "len": length,
            "flags": f"0x{flags:02x}",
        }
        
        if frame_type == 0x1:  # HEADERS
            # HPACK デコード
            # flags bit 0x20 = PRIORITY  - if set, skip 5 bytes (stream dep + weight)
            header_data = payload
            if flags & 0x20:  # PRIORITY flag
                header_data = payload[5:]  # skip StreamDependency(4) + Weight(1)
                
            headers = decode_hpack_headers(header_data, hpack_dec)
            if headers:
                frame_info["headers"] = {k: v for k, v in headers}
                # Pretty print important headers
                for k, v in headers:
                    if k in [':method', ':path', ':authority', ':scheme', ':status',
                             'content-type', 'user-agent', 'authorization',
                             'te', 'grpc-timeout'] or k.startswith('x-'):
                        print(f"    🔑 {k}: {v[:100]}{'...' if len(v) > 100 else ''}", flush=True)
            else:
                frame_info["headers_hex"] = header_data[:200].hex()
                
        elif frame_type == 0x0:  # DATA
            if len(payload) >= 5:
                compressed = payload[0]
                msg_len = int.from_bytes(payload[1:5], 'big')
                frame_info["grpc_compressed"] = compressed
                frame_info["grpc_msg_len"] = msg_len
                frame_info["payload_hex"] = payload[5:min(105, len(payload))].hex()
                
        elif frame_type == 0x4:  # SETTINGS
            settings = []
            for i in range(0, len(payload), 6):
                if i + 6 <= len(payload):
                    sid = int.from_bytes(payload[i:i+2], 'big')
                    val = int.from_bytes(payload[i+2:i+6], 'big')
                    settings.append(f"{sid}={val}")
            if settings:
                frame_info["settings"] = settings
                
        elif frame_type == 0x7:  # GOAWAY
            if len(payload) >= 8:
                last_stream = int.from_bytes(payload[:4], 'big') & 0x7FFFFFFF
                error_code = int.from_bytes(payload[4:8], 'big')
                debug_data = payload[8:].decode('utf-8', errors='replace')
                frame_info["goaway"] = {
                    "last_stream": last_stream,
                    "error_code": error_code,
                    "debug": debug_data[:200],
                }
        
        type_str = frame_info["type"]
        print(f"  [{direction}] {type_str} stream={stream_id} len={length} flags={frame_info['flags']}", flush=True)
        
        frames.append(frame_info)
        pos += FRAME_HEADER_SIZE + length
    
    remaining = data[pos:]
    return frames, remaining


async def handle_connection(ls_reader: asyncio.StreamReader, ls_writer: asyncio.StreamWriter):
    """LS からの接続をハンドル."""
    peer = ls_writer.get_extra_info('peername')
    print(f"\n{'='*70}")
    print(f"[{datetime.now().isoformat()}] LS 接続: {peer}")
    print(f"{'='*70}", flush=True)
    
    # HPACK decoders (方向別)
    ls_dec = hpack.Decoder() if HPACK_AVAILABLE else None
    srv_dec = hpack.Decoder() if HPACK_AVAILABLE else None
    
    # cloudcode-pa に TLS 接続
    ssl_ctx = ssl.create_default_context()
    try:
        srv_reader, srv_writer = await asyncio.open_connection(
            TARGET_HOST, TARGET_PORT, ssl=ssl_ctx
        )
        print(f"[OK] Upstream 接続: {TARGET_HOST}:{TARGET_PORT}", flush=True)
    except Exception as e:
        print(f"[ERROR] Upstream 接続失敗: {e}", flush=True)
        ls_writer.close()
        return
    
    async def proxy_ls_to_server():
        """LS → cloudcode-pa (平文 → TLS)"""
        buf = b""
        preface_seen = False
        try:
            while True:
                data = await ls_reader.read(65536)
                if not data:
                    break
                    
                buf += data
                
                # HTTP/2 preface チェック
                if not preface_seen:
                    if buf.startswith(H2_PREFACE):
                        print(f"\n  [LS→Server] ✅ HTTP/2 Connection Preface detected", flush=True)
                        preface_seen = True
                        buf = buf[len(H2_PREFACE):]
                        # Forward preface to server
                        srv_writer.write(H2_PREFACE)
                        await srv_writer.drain()
                    elif len(buf) > len(H2_PREFACE):
                        # Not HTTP/2
                        print(f"  [LS→Server] ⚠️ Not HTTP/2 preface: {buf[:50]}", flush=True)
                        srv_writer.write(buf)
                        buf = b""
                        await srv_writer.drain()
                        continue
                    else:
                        continue  # Wait for more data
                
                # Parse HTTP/2 frames
                if buf:
                    frames, buf = parse_h2_frames(buf, "LS→Server", ls_dec)
                    for f in frames:
                        captured_frames.append(f)
                        with open(LOG_FILE, "a") as logf:
                            logf.write(json.dumps(f, ensure_ascii=False) + "\n")
                
                # Forward raw data to upstream (the original data, not parsed)
                srv_writer.write(data)
                await srv_writer.drain()
                
        except Exception as e:
            print(f"  [LS→Server] Error: {e}", flush=True)
        finally:
            try:
                srv_writer.close()
            except:
                pass
    
    async def proxy_server_to_ls():
        """cloudcode-pa → LS (TLS → 平文)"""
        buf = b""
        preface_seen = False
        try:
            while True:
                data = await srv_reader.read(65536)
                if not data:
                    break
                
                buf += data
                
                # Server response: may start with SETTINGS frame directly (no preface from server)
                # Actually, server sends connection preface = SETTINGS frame
                if buf:
                    frames, buf = parse_h2_frames(buf, "Server→LS", srv_dec)
                    for f in frames:
                        captured_frames.append(f)
                        with open(LOG_FILE, "a") as logf:
                            logf.write(json.dumps(f, ensure_ascii=False) + "\n")
                
                # Forward to LS
                ls_writer.write(data)
                await ls_writer.drain()
                
        except Exception as e:
            print(f"  [Server→LS] Error: {e}", flush=True)
        finally:
            try:
                ls_writer.close()
            except:
                pass
    
    await asyncio.gather(proxy_ls_to_server(), proxy_server_to_ls())
    print(f"\n[CLOSED] 接続終了 (captured {len(captured_frames)} frames)", flush=True)


async def main():
    # Clear previous capture
    LOG_FILE.unlink(missing_ok=True)
    
    server = await asyncio.start_server(
        handle_connection,
        "127.0.0.1", LISTEN_PORT
    )
    
    print(f"h2c Proxy listening on 127.0.0.1:{LISTEN_PORT} (plaintext)")
    print(f"Target: {TARGET_HOST}:{TARGET_PORT} (TLS)")
    print(f"Capture: {LOG_FILE}")
    print(f"HPACK: {'✅' if HPACK_AVAILABLE else '❌'}")
    print(f"Waiting for LS connections...\n", flush=True)
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
