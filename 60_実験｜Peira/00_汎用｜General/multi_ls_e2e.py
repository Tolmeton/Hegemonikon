#!/usr/bin/env python3
# PROOF: [L2-E2E] <- experiments/ E2E検証
# PURPOSE: マルチアカウント並列 LS 推論のE2Eテスト
# NOTE: GetCascadeModelConfigData は空を返すが ask() 推論は正常動作する。
#       モデルキー解決はサーバーサイドで行われるため、クライアント側での待機は不要。

import sys
import os
import concurrent.futures

# パス追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mekhane.ochema.ls_manager import NonStandaloneLSManager
from mekhane.ochema.antigravity_client import AntigravityClient


def run_ls_session(account_id: str, prompt: str) -> str:
    print(f"[{account_id}] Starting LS Manager...")
    mgr = NonStandaloneLSManager(workspace_id=f"ws_{account_id}")
    try:
        ls_info = mgr.start()
        print(f"[{account_id}] LS Started: port={ls_info.port}, pid={ls_info.pid}")
        
        client = AntigravityClient(ls_info=ls_info)
        print(f"[{account_id}] Sending ask()...")
        resp = client.ask(prompt, timeout=60.0)
        
        return f"[{account_id}] Response ({len(resp.text)} chars): {resp.text[:100]}..."
    finally:
        print(f"[{account_id}] Stopping LS Manager...")
        mgr.stop()


def main():
    print("=== Multi-Account Parallel LS Inference E2E Test ===")
    
    # 2つの異なるコンテキスト (アカウント) で並列実行
    tasks = [
        ("Alice", "Write a short haiku about cats."),
        ("Bob", "Write a short haiku about dogs."),
    ]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_ls_session, acct, prompt): acct
            for acct, prompt in tasks
        }
        
        for future in concurrent.futures.as_completed(futures):
            acct = futures[future]
            try:
                res = future.result()
                print(f"SUCCESS {acct}:\n{res}")
            except Exception as e:
                print(f"FAILED {acct}: {e}")
                
if __name__ == "__main__":
    main()
