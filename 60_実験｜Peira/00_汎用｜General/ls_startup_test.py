#!/usr/bin/env python3
"""Non-Standalone LS 起動テスト — force_dummy + DummyExtServer."""
import sys, os, time

OUT = "/tmp/ls_force_dummy_test.txt"
f = open(OUT, "w")
def log(msg):
    f.write(msg + "\n"); f.flush()

log(f"=== force_dummy Test === {time.strftime('%H:%M:%S')}")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import logging
logging.basicConfig(level=logging.INFO, stream=f, format='%(levelname)s: %(message)s')

from mekhane.ochema.ls_manager import NonStandaloneLSManager

mgr = NonStandaloneLSManager(workspace_id='ls-force-test', force_dummy=True)
log("Phase 1: LS 起動 (force_dummy=True)...")

try:
    ls_info = mgr.start()
    log(f"✅ 起動成功: PID={mgr.pid} PORT={mgr.port} HTTPS={ls_info.is_https}")
except Exception as e:
    log(f"❌ 起動失敗: {e}")
    import traceback; traceback.print_exc(file=f)
    if mgr._log_path:
        with open(mgr._log_path) as lf:
            for l in lf.readlines()[-15:]: log(l.rstrip())
    mgr.stop(); f.close(); sys.exit(1)

# 3秒待ってLSログの認証状態を確認
time.sleep(3)
log("\nPhase 2: LS ログの認証状態...")
if mgr._log_path:
    with open(mgr._log_path) as lf:
        for l in lf.readlines()[:30]: log(f"  {l.rstrip()}")

log("\nPhase 3: HTTP API テスト...")
try:
    from mekhane.ochema.antigravity_client import AntigravityClient
    client = AntigravityClient(workspace='ls-force-test', ls_info=ls_info)
    log(f"Client: PORT={client.port} HTTPS={client.ls.is_https}")

    # StartCascade だけ試す (認証不要で動くか確認)
    cascade_id = client._start_cascade()
    log(f"✅ StartCascade 成功: {cascade_id}")

    # Claude に ask
    t0 = time.time()
    resp = client.ask('Say exactly: DUMMY_EXT_OK', model='MODEL_PLACEHOLDER_M35', timeout=60)
    t1 = time.time()
    log(f"✅ ask 成功!")
    log(f"  応答: {resp.text[:200]}")
    log(f"  モデル: {resp.model}")
    log(f"  Thinking: {len(resp.thinking)} chars")
    log(f"  時間: {t1-t0:.1f}秒")
except Exception as e:
    log(f"❌ API失敗: {e}")
    import traceback; traceback.print_exc(file=f)
    # 追加: LS ログの最新部分
    if mgr._log_path:
        log("\n--- LS LOG (tail) ---")
        with open(mgr._log_path) as lf:
            for l in lf.readlines()[-20:]: log(l.rstrip())

log(f"\nPhase 4: 停止")
mgr.stop()
log(f"✅ DONE {time.strftime('%H:%M:%S')}")
f.close()
