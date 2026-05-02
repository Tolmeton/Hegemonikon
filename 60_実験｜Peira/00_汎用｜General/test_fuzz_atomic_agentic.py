#!/usr/bin/env python3
import grpc
import uuid
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mekhane.ochema.token_vault import TokenVault

def varint(n):
    b = bytearray()
    while n >= 0x80:
        b.append((n & 0x7F) | 0x80)
        n >>= 7
    b.append(n)
    return bytes(b)

def fs(tag, s):
    e = s.encode('utf-8')
    return varint((tag<<3)|2) + varint(len(e)) + e

def fb(tag, b):
    return varint((tag<<3)|2) + varint(len(b)) + b

def fv(tag, v):
    return varint((tag<<3)|0) + varint(v)

def build_client_metadata(ide_type=3, platform=1):
    m = b''
    m += fv(1, ide_type)
    m += fv(4, platform)
    return m

def execute_chat(req_bytes, desc):
    print(f"\n=== {desc} ===")
    project = 'driven-circlet-rgkmt'
    target = 'daily-cloudcode-pa.googleapis.com:443'
    method = '/google.internal.cloud.code.v1internal.CloudCode/InternalAtomicAgenticChat'
    token = TokenVault().get_token()
    
    ch = grpc.secure_channel(target, grpc.ssl_channel_credentials())
    fn = ch.unary_stream(method, request_serializer=lambda x: x, response_deserializer=lambda x: x)
    
    try:
        chunks = []
        for i, r in enumerate(fn(req_bytes, metadata=[('authorization', f'Bearer {token}')], timeout=30)):
            if len(r) > 0:
                print(f'  ✅ Chunk {i}: {len(r)}b | {r.decode("utf-8", errors="replace")[:100]}')
                chunks.append(r)
            if i >= 10: break
        
        if not chunks:
            print("  Empty stream (0 bytes)")
        return chunks
    except grpc.RpcError as e:
        print(f"  Error {e.code()}: {e.details()[:200]}")
        return None
    finally:
        ch.close()

def main():
    project = 'driven-circlet-rgkmt'
    msg = fs(1, project) + fs(3, 'Say just OK')
    
    # 1. Base test (empty response expected based on previous runs)
    execute_chat(msg, "Base Project + UserMessage")
    
    # 2. Add client metadata to various fields
    meta = build_client_metadata()
    for field in [6, 7, 8, 9, 55]:
        req = msg + fb(field, meta)
        execute_chat(req, f"Base + ClientMetadata at tag {field}")
        
    # 3. Add model_config_id directly to request (field 14)
    req = msg + fs(14, 'claude-sonnet-4-5')
    execute_chat(req, "Base + model_config_id(14)")
    
    # 4. Add model_config submessage (field 12 or 27)
    # the submessage probably has model_config_id inside it at field 14 or 1
    for mc_tag in [12, 27]:
        for inner_tag in [1, 2, 14]:
            mc = fs(inner_tag, 'claude-sonnet-4-5')
            req = msg + fb(mc_tag, mc)
            execute_chat(req, f"Base + ModelConfig({mc_tag}) containing model({inner_tag})")

if __name__ == '__main__':
    main()
