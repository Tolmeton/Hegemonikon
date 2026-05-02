#!/usr/bin/env python3
"""
4-Step LLM Flow via LS ConnectRPC (gRPC-web+json)

Step 1: StartCascade → cascadeId
Step 2: SendUserCascadeMessage → queued
Step 3: GetAllCascadeTrajectories → trajectoryId  
Step 4: GetCascadeTrajectorySteps → LLM response + thinking
"""
import http.client
import struct
import json
import subprocess
import re
import signal
import sys
import time

signal.signal(signal.SIGALRM, lambda s,f: (print("\n⏰ Timeout."), sys.exit(0)))
signal.alarm(45)

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

def grpc_web_call(port, csrf, method, request):
    """gRPC-web+json unary call"""
    payload = json.dumps(request).encode()
    envelope = struct.pack('>BI', 0, len(payload)) + payload
    
    conn = http.client.HTTPConnection(f'127.0.0.1:{port}', timeout=10)
    conn.request('POST',
        f'/exa.language_server_pb.LanguageServerService/{method}',
        body=envelope,
        headers={
            'Content-Type': 'application/grpc-web+json',
            'x-codeium-csrf-token': csrf,
            'x-grpc-web': '1',
        })
    
    resp = conn.getresponse()
    body = resp.read()
    
    grpc_status = resp.getheader('grpc-status', '0')
    grpc_msg = resp.getheader('grpc-message', '')
    
    result = None
    if body and len(body) >= 5:
        length = struct.unpack('>I', body[1:5])[0]
        if 5+length <= len(body):
            try:
                result = json.loads(body[5:5+length])
            except:
                result = {'_raw': body[5:5+length].hex()[:100]}
    
    conn.close()
    return {
        'status': resp.status,
        'grpc_status': grpc_status,
        'grpc_message': grpc_msg,
        'body': result,
    }

def main():
    port, csrf = detect_ls()
    print(f"LS: fd10={port}, csrf={csrf[:8]}...")
    
    # ══════════════════════════════════════
    # Step 1: StartCascade
    # ══════════════════════════════════════
    print("\n═══ Step 1: StartCascade ═══")
    r1 = grpc_web_call(port, csrf, 'StartCascade', {
        'metadata': {},
    })
    print(f"  HTTP: {r1['status']}, gRPC: {r1['grpc_status']} {r1['grpc_message']}")
    
    if r1['body']:
        print(f"  Body: {json.dumps(r1['body'], ensure_ascii=False)[:200]}")
        cascade_id = r1['body'].get('cascadeId', '')
    else:
        print("  ❌ No cascadeId returned")
        # Try without metadata
        print("  Retrying without metadata...")
        r1b = grpc_web_call(port, csrf, 'StartCascade', {})
        print(f"  HTTP: {r1b['status']}, gRPC: {r1b['grpc_status']} {r1b['grpc_message']}")
        if r1b['body']:
            print(f"  Body: {json.dumps(r1b['body'], ensure_ascii=False)[:200]}")
            cascade_id = r1b['body'].get('cascadeId', '')
        else:
            print("  ❌ Failed to get cascadeId. Aborting.")
            sys.exit(1)
    
    print(f"  ✅ cascadeId = {cascade_id}")
    
    # ══════════════════════════════════════
    # Step 2: SendUserCascadeMessage
    # ══════════════════════════════════════
    print("\n═══ Step 2: SendUserCascadeMessage ═══")
    r2 = grpc_web_call(port, csrf, 'SendUserCascadeMessage', {
        'cascadeId': cascade_id,
        'metadata': {},
        'items': [{'text': 'What is 2+2? Think step by step and give the answer.'}],
        'cascadeConfig': {
            'plannerConfig': {
                'plannerTypeConfig': {'conversational': {}},
                'planModel': 4
            },
            'executorConfig': {
                'maxGeneratorInvocations': 1
            }
        }
    })
    print(f"  HTTP: {r2['status']}, gRPC: {r2['grpc_status']} {r2['grpc_message']}")
    if r2['body']:
        print(f"  Body: {json.dumps(r2['body'], ensure_ascii=False)[:200]}")
    
    if r2['grpc_status'] != '0':
        print(f"  ⚠️ gRPC error. Trying with minimal request...")
        r2b = grpc_web_call(port, csrf, 'SendUserCascadeMessage', {
            'cascadeId': cascade_id,
            'metadata': {},
            'items': [{'text': 'hi'}],
        })
        print(f"  HTTP: {r2b['status']}, gRPC: {r2b['grpc_status']} {r2b['grpc_message']}")
        if r2b['body']:
            print(f"  Body: {json.dumps(r2b['body'], ensure_ascii=False)[:200]}")
    
    # Wait for LLM processing
    print("\n  ⏳ Waiting 8s for LLM to process...")
    time.sleep(8)
    
    # ══════════════════════════════════════
    # Step 3: GetAllCascadeTrajectories
    # ══════════════════════════════════════
    print("\n═══ Step 3: GetAllCascadeTrajectories ═══")
    r3 = grpc_web_call(port, csrf, 'GetAllCascadeTrajectories', {})
    print(f"  HTTP: {r3['status']}, gRPC: {r3['grpc_status']} {r3['grpc_message']}")
    
    trajectory_id = None
    if r3['body']:
        trajectories = r3['body'].get('trajectories', [])
        print(f"  Trajectories: {len(trajectories)}")
        # Find our cascade
        for t in trajectories:
            tid = t.get('trajectoryId', '')
            cid = t.get('cascadeId', '')
            title = t.get('title', t.get('displayTitle', ''))
            if cid == cascade_id:
                trajectory_id = tid
                print(f"  ✅ Found: trajectoryId={tid} title={title}")
                break
            else:
                print(f"  - {tid[:12]}... cascade={cid[:12]}... title={title[:30]}")
        
        if not trajectory_id and trajectories:
            # Use the most recent one
            trajectory_id = trajectories[-1].get('trajectoryId', '')
            print(f"  Using latest: {trajectory_id}")
    
    if not trajectory_id:
        print("  ❌ No trajectory found")
        sys.exit(1)
    
    # ══════════════════════════════════════
    # Step 4: GetCascadeTrajectorySteps
    # ══════════════════════════════════════
    print("\n═══ Step 4: GetCascadeTrajectorySteps ═══")
    r4 = grpc_web_call(port, csrf, 'GetCascadeTrajectorySteps', {
        'trajectoryId': trajectory_id,
    })
    print(f"  HTTP: {r4['status']}, gRPC: {r4['grpc_status']} {r4['grpc_message']}")
    
    if r4['body']:
        steps = r4['body'].get('steps', [])
        print(f"  Steps: {len(steps)}")
        for i, step in enumerate(steps[-5:]):  # Last 5 steps
            role = step.get('role', step.get('type', '?'))
            text = step.get('text', step.get('content', ''))
            thinking = step.get('rawThinking', step.get('raw_thinking', ''))
            model = step.get('model', '')
            
            print(f"\n  --- Step {i} (role={role}, model={model}) ---")
            if text:
                print(f"  📝 Text: {str(text)[:300]}")
            if thinking:
                print(f"  🧠 THINKING: {str(thinking)[:500]}")
            
            # Check all keys for thinking-related fields
            for k, v in step.items():
                if 'think' in k.lower() or 'raw' in k.lower():
                    print(f"  🔑 {k}: {str(v)[:200]}")
    else:
        print("  ❌ No steps returned")
    
    print("\n✅ 4-Step flow complete.")

if __name__ == '__main__':
    main()
