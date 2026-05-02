#!/usr/bin/env python3
"""
Non-Standalone LS をプロキシ経由で起動し、Claude リクエストを送信して
gRPC メタデータをキャプチャする統合スクリプト。

Usage:
    1. MITM proxy が port 8443 で稼働していることを確認
    2. このスクリプトを実行:
       SSL_CERT_FILE=/tmp/combined_ca.pem .venv/bin/python experiments/ls_mitm_test.py
"""
import os
import sys
import time
import subprocess
import signal
import json
import re

# SSL_CERT_FILE を設定して Go が自己署名証明書を受け入れるようにする
os.environ["SSL_CERT_FILE"] = "/tmp/combined_ca.pem"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LS_BIN = "/usr/share/antigravity/resources/app/extensions/antigravity/bin/language_server_linux_x64"
PROXY_ENDPOINT = "https://localhost:8443"
LOG_PATH = "/tmp/ls_mitm_test.log"
WORKSPACE_ID = "mitm_capture_test"


def main():
    import mekhane.ochema.ls_manager as lm
    from mekhane.ochema.ext_server import DummyExtServer

    # Step 1: DummyExtServer 起動
    print("[1/5] DummyExtServer 起動中...")
    nonstd_db_path = lm._bootstrap_nonstd_state()
    dummy = DummyExtServer(db_path=nonstd_db_path)
    dummy.start()
    print(f"  DummyExtServer: port={dummy.port}, csrf={dummy.csrf}")

    # Step 2: metadata protobuf 生成
    metadata = lm.build_metadata()
    print(f"  Metadata: {len(metadata)} bytes")

    # Step 3: Non-Standalone LS 起動 (プロキシ経由)
    print(f"[2/5] LS 起動中 (endpoint={PROXY_ENDPOINT})...")
    log_file = open(LOG_PATH, "w")
    
    # 生成する csrf_token
    csrf_token = "mitm_test_csrf_42"
    
    cmd = [
        LS_BIN,
        "--enable_lsp",
        "--random_port",
        f"--extension_server_port={dummy.port}",
        f"--cloud_code_endpoint={PROXY_ENDPOINT}",
        f"--csrf_token={csrf_token}",
        f"--workspace_id={WORKSPACE_ID}",
        "--app_data_dir=antigravity",
        "-v=2",
    ]

    env = os.environ.copy()
    env["SSL_CERT_FILE"] = "/tmp/combined_ca.pem"

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
    )

    # stdin に metadata 注入
    proc.stdin.write(metadata)
    proc.stdin.close()
    print(f"  LS PID: {proc.pid}")

    # Step 4: ポート取得 (ポーリング)
    print("[3/5] LS ポート取得中...")
    http_port = None
    for _ in range(30):
        if proc.poll() is not None:
            with open(LOG_PATH) as f:
                log = f.read()
            print(f"  LS died! exit={proc.returncode}")
            print(f"  Log:\n{log}")
            dummy.stop()
            return
        try:
            with open(LOG_PATH) as f:
                log = f.read()
            m = re.search(r"at (\d+) for HTTP\b", log)
            if m:
                http_port = int(m.group(1))
                break
        except Exception:
            pass
        time.sleep(0.5)
    
    if not http_port:
        print("  ERROR: LS port not found!")
        proc.terminate()
        dummy.stop()
        return
    
    print(f"  LS HTTP port: {http_port}")

    # Step 5: Claude リクエスト送信
    print("[4/5] GetUserStatus を送信してプロキシでキャプチャ...")
    import urllib.request
    import urllib.error

    # GetUserStatus (これで cloudcode-pa への接続が発生する)
    url = f"http://localhost:{http_port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
    headers = {
        "Content-Type": "application/json",
        "x-csrf-token": csrf_token,
    }
    req = urllib.request.Request(url, data=b'{}', headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
            print(f"  GetUserStatus response: {len(body)} bytes")
            # JSON decode
            try:
                data = json.loads(body)
                print(f"  Response (first 500 chars): {json.dumps(data, ensure_ascii=False)[:500]}")
            except:
                print(f"  Response (raw): {body[:200]}")
    except urllib.error.URLError as e:
        print(f"  GetUserStatus error: {e}")
    except Exception as e:
        print(f"  GetUserStatus error: {e}")

    # Wait a bit for proxy to capture
    time.sleep(2)

    # Claude リクエスト (StartCascade)
    print("[5/5] StartCascade を送信...")
    url2 = f"http://localhost:{http_port}/exa.language_server_pb.LanguageServerService/StartCascade"
    cascade_data = json.dumps({
        "metadata": {
            "ideType": "IDE_UNSPECIFIED",
        },
        "source": 12,
        "trajectoryType": 17,
    })
    req2 = urllib.request.Request(url2, data=cascade_data.encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req2, timeout=15) as resp:
            body = resp.read()
            print(f"  StartCascade response: {len(body)} bytes")
            try:
                data = json.loads(body)
                cascade_id = data.get("cascadeId", "")
                print(f"  cascadeId: {cascade_id}")
                
                if cascade_id:
                    # SendUserCascadeMessage
                    url3 = f"http://localhost:{http_port}/exa.language_server_pb.LanguageServerService/SendUserCascadeMessage"
                    msg_data = json.dumps({
                        "cascadeId": cascade_id,
                        "userMessage": "Say OK",
                        "requestedModel": {"model": "MODEL_PLACEHOLDER_M35"},
                    })
                    req3 = urllib.request.Request(url3, data=msg_data.encode(), headers=headers, method='POST')
                    with urllib.request.urlopen(req3, timeout=15) as resp3:
                        body3 = resp3.read()
                        print(f"  SendUserCascadeMessage response: {len(body3)} bytes")
                        
                    # Wait for processing
                    time.sleep(5)
                    
            except json.JSONDecodeError:
                print(f"  Response (raw): {body[:200]}")
    except Exception as e:
        print(f"  StartCascade error: {e}")

    # Check proxy capture
    print("\n--- プロキシキャプチャ結果 ---")
    capture_path = "/tmp/grpc_mitm_capture.jsonl"
    if os.path.exists(capture_path):
        with open(capture_path) as f:
            lines = f.readlines()
        print(f"  キャプチャフレーム数: {len(lines)}")
        for line in lines[:20]:
            frame = json.loads(line)
            print(f"  {frame.get('direction', '?')} | {frame.get('type', '?')} "
                  f"stream={frame.get('stream_id', '?')} len={frame.get('length', '?')}")
            if frame.get("detected_strings"):
                print(f"    strings: {frame['detected_strings']}")
    else:
        print("  キャプチャファイルなし — プロキシに接続が到達していない")

    # LS ログも出力
    print("\n--- LS ログ (最後の 30 行) ---")
    with open(LOG_PATH) as f:
        log_lines = f.readlines()
    for line in log_lines[-30:]:
        print(f"  {line.rstrip()}")

    # Cleanup
    print("\n--- クリーンアップ ---")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except:
        proc.kill()
    dummy.stop()
    print("  Done.")


if __name__ == "__main__":
    main()
