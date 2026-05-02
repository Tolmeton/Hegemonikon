#!/usr/bin/env python3
"""
InternalAtomicAgenticChat gRPC テスト

LS バイナリから発見した /google.internal.cloud.code.v1internal.CloudCode/InternalAtomicAgenticChat
エンドポイントを直接 gRPC で呼び出し、Claude ルーティングが発動するかテストする。

発見の経緯:
  strings "$LS_BIN" | grep InternalAtomicAgentic で以下のメソッドが見つかった:
  - GetProject, GetUserMessage, GetHistory, GetMetadata, GetRequestId
  - GetIdeContext, GetToolDefinitions, GetEnablePromptEnhancement
"""

import grpc
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- protobuf helpers ---
def varint(n):
    b = bytearray()
    while n >= 0x80:
        b.append((n & 0x7F) | 0x80)
        n >>= 7
    b.append(n)
    return bytes(b)

def fs(tag, s):
    """protobuf string field."""
    e = s.encode('utf-8')
    return varint((tag << 3) | 2) + varint(len(e)) + e

def fb(tag, b):
    """protobuf bytes field."""
    return varint((tag << 3) | 2) + varint(len(b)) + b

def fv(tag, v):
    """protobuf varint field."""
    return varint((tag << 3) | 0) + varint(v)

def fbool(tag, v):
    """protobuf bool field."""
    return varint((tag << 3) | 0) + varint(1 if v else 0)


def get_token():
    """OAuth ya29 token を取得."""
    from mekhane.ochema.token_vault import TokenVault
    vault = TokenVault()
    token = vault.get_token()
    print(f"Token: {token[:15]}...{token[-5:]}")
    return token


def get_project_id():
    """loadCodeAssist から project ID を取得 (or cached)."""
    # DX-010 から既知の project ID を使用
    return "driven-circlet-rgkmt"


def build_request(project: str, user_message: str, model: str = "") -> bytes:
    """InternalAtomicAgenticChatRequest を手動で構築.
    
    フィールド番号は strings 出力から推測:
    - GetProject → field 1 (string, 慣例)
    - GetUserMessage → field 2 or 3 (string)
    - GetHistory → field 4 (repeated bytes)
    - GetMetadata → field 5 (bytes)
    - GetRequestId → field 6 (string)
    - GetIdeContext → field 7 (bytes)
    - GetToolDefinitions → field 8 (repeated bytes)
    - GetEnablePromptEnhancement → field 9 (bool)
    
    ※ フィールド番号は推測。エラーメッセージで調整する。
    """
    req = b""
    
    # field 1: project (string)
    req += fs(1, project)
    
    # field 2: user_message (string) — 推測
    req += fs(2, user_message)
    
    # field 6: request_id (string) — UUID
    req += fs(6, str(uuid.uuid4()))
    
    # model_config_id (field 14, oneof) — 推測
    if model:
        req += fs(14, model)
    
    return req


def test_grpc_method(token: str, project: str, method: str, request: bytes):
    """gRPC メソッドを直接呼び出す."""
    target = "daily-cloudcode-pa.googleapis.com:443"
    
    channel = grpc.secure_channel(target, grpc.ssl_channel_credentials())
    
    # Server streaming (Response に GetDone があるため streaming の可能性)
    try:
        # まず Unary で試す
        stub = channel.unary_unary(
            method,
            request_serializer=lambda x: x,
            response_deserializer=lambda x: x,
        )
        print(f"\n--- Unary call: {method} ---")
        response = stub(
            request,
            metadata=[
                ('authorization', f'Bearer {token}'),
                ('x-goog-api-client', 'gl-go grpc-go'),
            ],
            timeout=30,
        )
        print(f"Response: {len(response)} bytes")
        print(f"Response hex: {response[:200].hex()}")
        # Try to decode as UTF-8
        try:
            text = response.decode('utf-8', errors='replace')
            print(f"Response text: {text[:500]}")
        except:
            pass
        return response
        
    except grpc.RpcError as e:
        print(f"gRPC Error: code={e.code()}, details={e.details()}")
        # Extract error metadata
        trailing = e.trailing_metadata() if hasattr(e, 'trailing_metadata') else []
        for key, value in trailing:
            print(f"  Trailing: {key}={value[:100] if isinstance(value, str) else value}")
        
        # Try server streaming instead
        if e.code() == grpc.StatusCode.UNIMPLEMENTED:
            print("\n--- Trying server streaming ---")
            try:
                stub_stream = channel.unary_stream(
                    method,
                    request_serializer=lambda x: x,
                    response_deserializer=lambda x: x,
                )
                responses = stub_stream(
                    request,
                    metadata=[
                        ('authorization', f'Bearer {token}'),
                        ('x-goog-api-client', 'gl-go grpc-go'),
                    ],
                    timeout=30,
                )
                for i, resp in enumerate(responses):
                    print(f"  Stream chunk {i}: {len(resp)} bytes")
                    print(f"  Hex: {resp[:100].hex()}")
                    try:
                        text = resp.decode('utf-8', errors='replace')
                        print(f"  Text: {text[:200]}")
                    except:
                        pass
                    if i >= 10:
                        print("  (truncated)")
                        break
            except grpc.RpcError as e2:
                print(f"  Stream Error: code={e2.code()}, details={e2.details()}")
        
        return None
    finally:
        channel.close()


def main():
    print("=== InternalAtomicAgenticChat gRPC Test ===\n")
    
    token = get_token()
    project = get_project_id()
    print(f"Project: {project}")
    
    # Test 1: InternalAtomicAgenticChat without model
    print("\n" + "="*60)
    print("Test 1: InternalAtomicAgenticChat (no model)")
    print("="*60)
    method = "/google.internal.cloud.code.v1internal.CloudCode/InternalAtomicAgenticChat"
    req = build_request(project, "Say just OK")
    test_grpc_method(token, project, method, req)
    
    # Test 2: InternalAtomicAgenticChat with Claude model
    print("\n" + "="*60)
    print("Test 2: InternalAtomicAgenticChat (claude-sonnet-4-5)")
    print("="*60)
    req2 = build_request(project, "Say just OK", model="claude-sonnet-4-5")
    test_grpc_method(token, project, method, req2)
    
    # Test 3: StreamGenerateChat (for comparison)
    print("\n" + "="*60)
    print("Test 3: StreamGenerateChat (Claude model)")
    print("="*60)
    method3 = "/google.internal.cloud.code.v1internal.CloudCode/StreamGenerateChat"
    # Use the generateChat request format from DX-010
    req3 = fs(1, project) + fs(3, "Say just OK") + fs(14, "claude-sonnet-4-5")
    test_grpc_method(token, project, method3, req3)
    
    # Test 4: LoadCodeAssist (to get fresh project ID)
    print("\n" + "="*60)
    print("Test 4: LoadCodeAssist (project discovery)")
    print("="*60)
    method4 = "/google.internal.cloud.code.v1internal.CloudCode/LoadCodeAssist"
    req4 = fs(1, project)  # minimal request
    test_grpc_method(token, project, method4, req4)
    
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
