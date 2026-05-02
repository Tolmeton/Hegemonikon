#!/usr/bin/env python3
"""
gRPC MITM Proxy for LS → cloudcode-pa traffic capture.

PURPOSE: LS が cloudcode-pa に送信する全 HTTP/2 ヘッダー・メタデータを
キャプチャし、Claude ルーティングに必要な情報を特定する。

Architecture:
    LS --TLS--> [This Proxy :8443] --TLS--> daily-cloudcode-pa.googleapis.com:443

Usage:
    1. Generate self-signed cert:
       openssl req -x509 -newkey rsa:2048 -keyout /tmp/proxy_key.pem \
         -out /tmp/proxy_cert.pem -days 1 -nodes \
         -subj '/CN=daily-cloudcode-pa.googleapis.com'
    
    2. Create CA bundle with our cert + system CAs:
       cat /tmp/proxy_cert.pem /etc/ssl/certs/ca-certificates.crt > /tmp/combined_ca.pem
    
    3. Start this proxy:
       python3 grpc_mitm_proxy.py
    
    4. Start Non-Standalone LS with:
       SSL_CERT_FILE=/tmp/combined_ca.pem \
       language_server_linux_x64 \
         --cloud_code_endpoint=https://localhost:8443 \
         ...
    
    5. Send a request through the LS and observe captured headers.
"""

import asyncio
import ssl
import struct
import sys
import json
from datetime import datetime
from pathlib import Path

# HTTP/2 frame types
FRAME_TYPES = {
    0x0: "DATA",
    0x1: "HEADERS",
    0x2: "PRIORITY",
    0x3: "RST_STREAM",
    0x4: "SETTINGS",
    0x5: "PUSH_PROMISE",
    0x6: "PING",
    0x7: "GOAWAY",
    0x8: "WINDOW_UPDATE",
    0x9: "CONTINUATION",
}

PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"

LOG_FILE = Path("/tmp/grpc_mitm_capture.jsonl")


class HTTP2FrameLogger:
    """HTTP/2 フレームの低レベル解析・ログ."""
    
    def __init__(self, direction: str):
        self.direction = direction  # "LS→Proxy" or "Proxy→LS"
        self.hpack_decoder = None
        
    def log_frame(self, data: bytes, offset: int = 0) -> list[dict]:
        """HTTP/2 フレームをパースしてログ."""
        frames = []
        pos = offset
        while pos + 9 <= len(data):
            # Frame header: 3 bytes length + 1 byte type + 1 byte flags + 4 bytes stream_id
            length = int.from_bytes(data[pos:pos+3], 'big')
            frame_type = data[pos+3]
            flags = data[pos+4]
            stream_id = int.from_bytes(data[pos+5:pos+9], 'big') & 0x7FFFFFFF
            
            payload = data[pos+9:pos+9+length] if pos+9+length <= len(data) else data[pos+9:]
            
            frame_info = {
                "direction": self.direction,
                "type": FRAME_TYPES.get(frame_type, f"UNKNOWN({frame_type})"),
                "type_id": frame_type,
                "flags": flags,
                "stream_id": stream_id,
                "length": length,
                "timestamp": datetime.now().isoformat(),
            }
            
            if frame_type == 0x1:  # HEADERS
                # HPACK encoded headers - log raw bytes for external decoding
                frame_info["headers_hex"] = payload.hex()
                frame_info["headers_raw"] = repr(payload[:200])
                # Try to extract :path and other pseudo-headers from raw bytes
                self._extract_grpc_path(payload, frame_info)
                
            elif frame_type == 0x0:  # DATA
                frame_info["data_length"] = len(payload)
                # gRPC: 1 byte compressed flag + 4 bytes message length + message
                if len(payload) >= 5:
                    compressed = payload[0]
                    msg_len = int.from_bytes(payload[1:5], 'big')
                    frame_info["grpc_compressed"] = compressed
                    frame_info["grpc_msg_length"] = msg_len
                    # Log first 100 bytes of protobuf as hex for analysis
                    frame_info["grpc_payload_hex"] = payload[5:105].hex()
                    
            elif frame_type == 0x4:  # SETTINGS
                frame_info["settings"] = self._parse_settings(payload)
                
            frames.append(frame_info)
            
            # Pretty print
            type_str = frame_info["type"]
            print(f"  [{self.direction}] {type_str} stream={stream_id} "
                  f"len={length} flags=0x{flags:02x}", flush=True)
            if "headers_raw" in frame_info:
                print(f"    headers(raw): {frame_info['headers_raw']}", flush=True)
            if "grpc_msg_length" in frame_info:
                print(f"    grpc: compressed={compressed} msg_len={msg_len}", flush=True)
                
            pos += 9 + length
            
        return frames
    
    def _extract_grpc_path(self, payload: bytes, info: dict):
        """HPACK エンコードされたヘッダーから :path を推測抽出."""
        # Static table indexed headers for common gRPC headers
        # This is a rough heuristic - HPACK decoding is complex
        try:
            text = payload.decode('utf-8', errors='replace')
            # Look for path-like strings
            for known in ['/google.', '/exa.', '/v1internal', 'cloudcode',
                         'grpc-', 'content-type', 'authorization', 'user-agent',
                         'x-goog-', 'x-client-']:
                idx = text.find(known)
                if idx >= 0:
                    # Extract surrounding context
                    start = max(0, idx - 5)
                    end = min(len(text), idx + 80)
                    info.setdefault("detected_strings", []).append(text[start:end])
        except Exception:
            pass
            
    def _parse_settings(self, payload: bytes) -> list:
        """SETTINGS フレームのパラメータをパース."""
        settings = []
        for i in range(0, len(payload), 6):
            if i + 6 <= len(payload):
                param_id = int.from_bytes(payload[i:i+2], 'big')
                value = int.from_bytes(payload[i+2:i+6], 'big')
                settings.append({"id": param_id, "value": value})
        return settings


class GRPCMITMProxy:
    """LS ↔ cloudcode-pa の gRPC MITM プロキシ."""
    
    def __init__(self, listen_port: int = 8443,
                 target_host: str = "daily-cloudcode-pa.googleapis.com",
                 target_port: int = 443,
                 cert_file: str = "/tmp/proxy_cert.pem",
                 key_file: str = "/tmp/proxy_key.pem"):
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.cert_file = cert_file
        self.key_file = key_file
        self.ls_logger = HTTP2FrameLogger("LS→Proxy")
        self.server_logger = HTTP2FrameLogger("Server→LS")
        self.capture_count = 0
        
    async def handle_client(self, ls_reader: asyncio.StreamReader,
                            ls_writer: asyncio.StreamWriter):
        """LS からの接続を処理."""
        peer = ls_writer.get_extra_info('peername')
        print(f"\n{'='*60}")
        print(f"[{datetime.now().isoformat()}] New connection from {peer}")
        print(f"{'='*60}", flush=True)
        
        # Connect to real cloudcode-pa
        ssl_ctx = ssl.create_default_context()
        try:
            server_reader, server_writer = await asyncio.open_connection(
                self.target_host, self.target_port, ssl=ssl_ctx
            )
        except Exception as e:
            print(f"[ERROR] Failed to connect to upstream: {e}", flush=True)
            ls_writer.close()
            return
            
        print(f"[OK] Connected to upstream {self.target_host}:{self.target_port}", flush=True)
        
        # Bidirectional proxy with logging
        await asyncio.gather(
            self._proxy_with_log(ls_reader, server_writer, "LS→Server", self.ls_logger),
            self._proxy_with_log(server_reader, ls_writer, "Server→LS", self.server_logger),
        )
        
        print(f"\n[CLOSED] Connection from {peer} closed", flush=True)
        
    async def _proxy_with_log(self, reader: asyncio.StreamReader,
                              writer: asyncio.StreamWriter,
                              direction: str,
                              logger: HTTP2FrameLogger):
        """データを中継しながらログ."""
        preface_seen = False
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                    
                # Check for HTTP/2 connection preface
                if not preface_seen and data.startswith(PREFACE):
                    print(f"\n  [{direction}] HTTP/2 Connection Preface", flush=True)
                    preface_seen = True
                    # Log frames after preface
                    frames = logger.log_frame(data, offset=len(PREFACE))
                else:
                    frames = logger.log_frame(data)
                
                # Save to JSONL
                for frame in frames:
                    frame["direction"] = direction
                    with open(LOG_FILE, "a") as f:
                        f.write(json.dumps(frame, ensure_ascii=False) + "\n")
                    self.capture_count += 1
                
                # Forward data unchanged
                writer.write(data)
                await writer.drain()
                
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass
        except Exception as e:
            print(f"  [{direction}] Error: {e}", flush=True)
        finally:
            try:
                writer.close()
            except Exception:
                pass
                
    async def start(self):
        """プロキシサーバーを起動."""
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain(self.cert_file, self.key_file)
        # Allow HTTP/2
        ssl_ctx.set_alpn_protocols(["h2", "http/1.1"])
        
        server = await asyncio.start_server(
            self.handle_client,
            "127.0.0.1", self.listen_port,
            ssl=ssl_ctx
        )
        
        # Clear previous capture
        LOG_FILE.unlink(missing_ok=True)
        
        print(f"gRPC MITM Proxy listening on 127.0.0.1:{self.listen_port}")
        print(f"Target: {self.target_host}:{self.target_port}")
        print(f"Capture log: {LOG_FILE}")
        print(f"Waiting for LS connections...\n", flush=True)
        
        async with server:
            await server.serve_forever()


async def main():
    proxy = GRPCMITMProxy()
    
    # Check cert files exist
    if not Path(proxy.cert_file).exists():
        print("ERROR: Certificate files not found. Generate them first:")
        print(f"  openssl req -x509 -newkey rsa:2048 -keyout {proxy.key_file} \\")
        print(f"    -out {proxy.cert_file} -days 1 -nodes \\")
        print(f"    -subj '/CN={proxy.target_host}'")
        sys.exit(1)
        
    await proxy.start()


if __name__ == "__main__":
    asyncio.run(main())
