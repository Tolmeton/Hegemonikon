#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→安全な永続化が必要→persist_runner が担う
"""
Persist Runner — /bye 永続化を軽量/重量で分離実行する

PURPOSE:
    GPU リソース競合によるハングを防止しつつ、可能な限り多くの永続化ステップを実行する。

DESIGN:
    - Phase 1 (CPU のみ): Persona, WF Inventory — 常に成功
    - Phase 2 (embedding): Handoff Index, Sophia — GPU 不可時は CPU フォールバック
    - GPU プリフライトチェック付き

USAGE:
    python persist_runner.py              # 全ステップ実行
    python persist_runner.py --light      # Phase 1 のみ
    python persist_runner.py --force-cpu  # 全ステップを CPU で強制実行
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# PURPOSE: Phase 1: CPU のみのステップ (常に成功するはず)
def run_phase1(insight: str = None) -> dict:
    """Phase 1: CPU のみのステップ (常に成功するはず)"""
    results = {}

    # Step 1: Persona
    print("  [P1] 👤 Persona...", end="", flush=True)
    try:
        from mekhane.symploke.persona import update_persona
        persona = update_persona(session_increment=1, trust_delta=0.01, new_insight=insight)
        sessions = persona.get("relationship", {}).get("sessions_together", "?")
        print(f" ✅ {sessions} sessions")
        results["persona"] = {"success": True, "sessions": sessions}
    except Exception as e:  # noqa: BLE001
        print(f" ❌ {e}")
        results["persona"] = {"success": False, "error": str(e)}

    # Step 2: WF Inventory
    print("  [P1] 📂 WF Inventory...", end="", flush=True)
    try:
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "mekhane/anamnesis/workflow_inventory.py")],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            print(" ✅")
            results["wf_inventory"] = {"success": True}
        else:
            print(f" ❌ {r.stderr[:80]}")
            results["wf_inventory"] = {"success": False, "error": r.stderr[:200]}
    except Exception as e:  # noqa: BLE001
        print(f" ❌ {e}")
        results["wf_inventory"] = {"success": False, "error": str(e)}

    return results


# PURPOSE: Phase 2: embedding が必要なステップ (GPU 不可時は CPU フォールバック)
def run_phase2(force_cpu: bool = False) -> dict:
    """Phase 2: embedding が必要なステップ (GPU 不可時は CPU フォールバック)"""
    results = {}

    if force_cpu:
        import os
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        print("  [P2] 🔧 CPU mode forced (CUDA_VISIBLE_DEVICES=\"\")")

    # Step 3: Handoff Index
    print("  [P2] 📋 Handoff Index...", end="", flush=True)
    try:
        from mekhane.symploke.handoff_search import build_handoff_index
        adapter = build_handoff_index()
        count = adapter.count() if adapter else 0
        print(f" ✅ {count} docs")
        results["handoff_index"] = {"success": True, "count": count}
    except Exception as e:  # noqa: BLE001
        print(f" ❌ {e}")
        results["handoff_index"] = {"success": False, "error": str(e)}

    # Step 4: Sophia Ingest
    print("  [P2] 📚 Sophia Ingest...", end="", flush=True)
    try:
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "mekhane/symploke/sophia_ingest.py")],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode == 0:
            print(" ✅")
            results["sophia"] = {"success": True}
        else:
            # Extract last meaningful error line
            err_lines = [l for l in r.stderr.strip().split("\n") if l.strip()]
            err_msg = err_lines[-1] if err_lines else "Unknown error"
            print(f" ❌ {err_msg[:80]}")
            results["sophia"] = {"success": False, "error": err_msg[:200]}
    except subprocess.TimeoutExpired:
        print(" ⏰ Timeout")
        results["sophia"] = {"success": False, "error": "Timeout (60s)"}
    except Exception as e:  # noqa: BLE001
        print(f" ❌ {e}")
        results["sophia"] = {"success": False, "error": str(e)}

    return results


# PURPOSE: main の処理
def main():
    parser = argparse.ArgumentParser(description="/bye 永続化ランナー")
    parser.add_argument("--light", action="store_true", help="Phase 1 のみ (CPU、軽量)")
    parser.add_argument("--force-cpu", action="store_true", help="全ステップを CPU で強制実行")
    parser.add_argument("--insight", type=str, help="Persona に追加する insight")
    args = parser.parse_args()

    t0 = time.time()
    print("🔄 永続化開始")

    # GPU プリフライトチェック
    gpu_ok = True
    if not args.light and not args.force_cpu:
        try:
            from mekhane.symploke.gpu_guard import gpu_preflight
            status = gpu_preflight()
            gpu_ok = status.gpu_available
            icon = "🟢" if gpu_ok else "🔴"
            print(f"  {icon} GPU: {status.reason}")
            if not gpu_ok:
                print("  → Phase 2 は CPU フォールバックで実行")
                args.force_cpu = True
        except Exception:  # noqa: BLE001
            pass

    # Phase 1: CPU のみ (常に実行)
    print("\n📦 Phase 1 (CPU only)")
    p1 = run_phase1(insight=args.insight)

    # Phase 2: embedding (--light でなければ)
    p2 = {}
    if not args.light:
        print(f"\n📦 Phase 2 (embedding, {'CPU' if args.force_cpu else 'GPU'})")
        p2 = run_phase2(force_cpu=args.force_cpu)

    # Summary
    elapsed = time.time() - t0
    total = len(p1) + len(p2)
    success = sum(1 for v in {**p1, **p2}.values() if v.get("success"))
    print(f"\n{'─' * 40}")
    print(f"✅ {success}/{total} steps completed ({elapsed:.1f}s)")

    if success < total:
        failed = [k for k, v in {**p1, **p2}.items() if not v.get("success")]
        print(f"❌ Failed: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
