#!/usr/bin/env python3
"""LS Cascade 性能実測 & 機能拡張検証 — Non-Standalone LS 使用.

Non-Standalone LS を独立起動し、oikos ワークスペースを汚さずにテストする。

テスト項目:
  1. レイテンシ測定
  2. plannerConfig 拡張 — systemInstruction
  3. plannerConfig 拡張 — thinkingBudget
  4. Stream RPC の存在確認
  5. コンテキスト上限実測
"""
import json
import sys
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mekhane.ochema.ls_manager import NonStandaloneLSManager
from mekhane.ochema.antigravity_client import AntigravityClient
from mekhane.ochema.proto import (
    RPC_SEND_MESSAGE,
    RPC_GET_TRAJECTORIES,
    RPC_GET_STEPS,
    STEP_TYPE_PLANNER,
    STEP_STATUS_DONE,
    TURN_STATES_DONE,
    extract_planner_response,
)

# ============================================================
# Setup: Non-Standalone LS を独立起動
# ============================================================

print("=" * 60)
print("LS Cascade Capability Test (Non-Standalone LS)")
print("=" * 60)

mgr = NonStandaloneLSManager(workspace_id="ls-test-workspace")
print("Non-Standalone LS を起動中...")
try:
    ls_info = mgr.start()
    print(f"✅ LS 起動成功: PID={mgr.pid} PORT={mgr.port} HTTP={not ls_info.is_https}")
except Exception as e:
    print(f"❌ LS 起動失敗: {e}")
    print("IDE LS にフォールバックしてテストを続行します")
    mgr = None

if mgr:
    client = AntigravityClient(workspace="ls-test-workspace", ls_info=ls_info)
else:
    client = AntigravityClient(workspace="oikos")

print(f"Client: PID={client.pid} PORT={client.port}")
print()


# --- ヘルパー ---

def send_extended(client, cascade_id, text, model, **extra):
    """拡張 plannerConfig で SendMessage."""
    payload = {
        "cascadeId": cascade_id,
        "items": [{"text": text}],
        "cascadeConfig": {
            "plannerConfig": {
                "plannerTypeConfig": {"conversational": {}},
                "requestedModel": {"model": model},
                **extra,
            },
        },
    }
    return client._rpc(RPC_SEND_MESSAGE, payload)


def poll(client, cascade_id, timeout=60):
    """ポーリングで応答取得."""
    start = time.time()
    tid = ""
    while time.time() - start < timeout:
        if not tid:
            try:
                d = client._rpc(RPC_GET_TRAJECTORIES, {})
                cs = d.get("trajectorySummaries", {}).get(cascade_id, {})
                if cs:
                    tid = cs.get("trajectoryId", "")
            except Exception:
                pass
        if tid:
            try:
                r = client._rpc(RPC_GET_STEPS, {
                    "cascadeId": cascade_id, "trajectoryId": tid,
                })
                steps = r.get("steps", [])
                ts = r.get("turnState", "")
                for s in steps:
                    if s.get("type") == STEP_TYPE_PLANNER and s.get("status") == STEP_STATUS_DONE:
                        return extract_planner_response(s)
                if ts in TURN_STATES_DONE:
                    for s in steps:
                        if s.get("type") == STEP_TYPE_PLANNER:
                            return extract_planner_response(s)
            except Exception:
                pass
        time.sleep(0.5)
    return {"error": "timeout"}


MODEL = "MODEL_PLACEHOLDER_M35"  # Claude Sonnet 4.6

results = {}

# ============================================================
# Test 1: レイテンシ測定
# ============================================================

print("─" * 60)
print("TEST 1: レイテンシ測定 (Claude Sonnet 4.6)")
print("─" * 60)

t0 = time.time()
resp = client.ask("Say exactly: 'LATENCY_TEST_OK'", model=MODEL, timeout=60)
t1 = time.time()

print(f"  応答: {resp.text[:100]}")
print(f"  モデル: {resp.model}")
print(f"  Thinking: {len(resp.thinking)} chars")
print(f"  全行程: {t1 - t0:.2f} 秒")
results["latency"] = {"time": t1 - t0, "model": resp.model, "ok": bool(resp.text)}
print()


# ============================================================
# Test 2: systemInstruction
# ============================================================

print("─" * 60)
print("TEST 2: systemInstruction を plannerConfig に送信")
print("─" * 60)

si_tests = [
    ("systemInstruction (string)", {"systemInstruction": "You MUST answer as a pirate. Use 'Arrr' and 'matey'."}),
    ("system_instruction (snake)", {"system_instruction": "You MUST answer as a pirate. Use 'Arrr' and 'matey'."}),
    ("systemInstructions (plural)", {"systemInstructions": "You MUST answer as a pirate. Use 'Arrr' and 'matey'."}),
]

for name, extra in si_tests:
    print(f"\n  --- {name} ---")
    try:
        cid = client._start_cascade()
        send_extended(client, cid, "What is 2+2?", MODEL, **extra)
        r = poll(client, cid, 45)
        if "error" in r:
            print(f"  ❌ {r['error']}")
            results[name] = "error"
        else:
            txt = r.get("text", "")[:200]
            pirate = any(w in txt.lower() for w in ["arr", "matey", "ye", "ahoy", "aye"])
            print(f"  応答: {txt}")
            print(f"  海賊語: {'✅ YES' if pirate else '❌ NO'}")
            results[name] = "pirate" if pirate else "no_effect"
    except Exception as e:
        print(f"  ❌ {e}")
        results[name] = f"exception: {e}"

print()


# ============================================================
# Test 3: thinkingBudget
# ============================================================

print("─" * 60)
print("TEST 3: thinkingBudget / thinkingConfig")
print("─" * 60)

tb_tests = [
    ("thinkingBudget=100", {"thinkingBudget": 100}),
    ("thinkingConfig={budget:100}", {"thinkingConfig": {"thinkingBudget": 100}}),
    ("includeThinkingSummaries=true", {"includeThinkingSummaries": True}),
]

for name, extra in tb_tests:
    print(f"\n  --- {name} ---")
    try:
        cid = client._start_cascade()
        send_extended(client, cid, "What is 2+2? Answer in one word.", MODEL, **extra)
        r = poll(client, cid, 45)
        if "error" in r:
            print(f"  ❌ {r['error']}")
            results[name] = "error"
        else:
            txt = r.get("text", "")[:150]
            thinking = r.get("thinking", "")
            print(f"  応答: {txt}")
            print(f"  Thinking: {len(thinking)} chars")
            results[name] = {"text_len": len(txt), "thinking_len": len(thinking)}
    except Exception as e:
        print(f"  ❌ {e}")
        results[name] = f"exception: {e}"

print()


# ============================================================
# Test 4: Stream RPC
# ============================================================

print("─" * 60)
print("TEST 4: Stream RPC の存在確認")
print("─" * 60)

for rpc in ["StreamCascadeReactiveUpdates", "StreamCascadeUpdates", "SubscribeCascadeUpdates"]:
    rpc_path = f"exa.language_server_pb.LanguageServerService/{rpc}"
    try:
        r = client._rpc(rpc_path, {})
        print(f"  {rpc}: ✅ 応答あり → {str(r)[:80]}")
        results[rpc] = "exists"
    except Exception as e:
        es = str(e)
        if "404" in es:
            print(f"  {rpc}: ❌ 404")
            results[rpc] = "not_found"
        else:
            print(f"  {rpc}: ⚠️ {es[:80]}")
            results[rpc] = f"error: {es[:60]}"

print()


# ============================================================
# Test 5: コンテキスト上限 (新規 cascade で段階テスト)
# ============================================================

print("─" * 60)
print("TEST 5: コンテキスト上限 (単一メッセージサイズ)")
print("─" * 60)

sizes = [50_000, 100_000, 200_000, 500_000, 1_000_000, 2_000_000]

for size in sizes:
    padding = "A" * size
    prompt = f"I sent {size} bytes. Reply ONLY with 'OK_{size}'. Data: {padding}"
    print(f"\n  --- {size:,} bytes ({size/1024:.0f} KB) ---")
    t0 = time.time()
    try:
        cid = client._start_cascade()
        send_extended(client, cid, prompt, MODEL)
        r = poll(client, cid, 120)
        t1 = time.time()
        if "error" in r:
            print(f"  ❌ {r['error']}")
            results[f"ctx_{size}"] = "error"
            # Don't break — try next size too (maybe single message limit)
        else:
            txt = r.get("text", "")[:100]
            print(f"  ✅ 応答: {txt}")
            print(f"  時間: {t1 - t0:.1f} 秒")
            results[f"ctx_{size}"] = {"ok": True, "time": t1 - t0}
    except Exception as e:
        t1 = time.time()
        print(f"  ❌ Exception: {e}")
        results[f"ctx_{size}"] = f"exception: {e}"
        break

print()


# ============================================================
# Cleanup & Summary
# ============================================================

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(json.dumps(results, indent=2, default=str))

if mgr:
    print("\nNon-Standalone LS を停止中...")
    mgr.stop()
    print("✅ 停止完了")

print("\n全テスト完了")
