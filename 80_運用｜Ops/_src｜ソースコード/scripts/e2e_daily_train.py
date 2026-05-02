#!/usr/bin/env python3
# PROOF: [L2/FEP] <- scripts/
# PURPOSE: 日次Dirichletトレーニングを自動実行し、Attractor精度を育てる
"""
FEP Daily Training — セッション間自律学習

Handoff の最新テーマを入力として E2E v2 ループを回し、
A行列の Dirichlet パラメータを持続的に育てる。

## 自律化の設計

- n8n cron (毎日6:00) または systemd timer から起動
- Handoff から自動でコンテキストを取得
- 結果を JSONL ログに追記
- Slack Webhook で結果を通知 (optional)

Usage:
    python scripts/e2e_daily_train.py
    python scripts/e2e_daily_train.py --rounds 10 --cpu
    python scripts/e2e_daily_train.py --notify  # Slack通知付き

REASON: /bou ③「E2E Loop自律化」から生成。
        e2e_endurance.py (30min) は耐久テスト用。
        daily_train は軽量5分のデイリー学習用。
"""

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("e2e_daily")


# ---------------------------------------------------------------------------
# Handoff からコンテキストを自動取得
# ---------------------------------------------------------------------------


def _get_handoff_contexts(max_count: int = 5) -> list[str]:
    """最新の Handoff ファイルから主題を抽出する。"""
    sess_dir = Path.home() / "oikos/mneme/.hegemonikon/sessions"
    if not sess_dir.exists():
        return []

    handoffs = sorted(
        sess_dir.glob("handoff_*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:max_count]

    contexts = []
    for hf in handoffs:
        try:
            content = hf.read_text(encoding="utf-8")
            # 主題行を探す
            for line in content.splitlines():
                if "主題" in line or "Subject" in line:
                    topic = line.split(":", 1)[-1].strip().strip("*")
                    if topic and len(topic) > 5:
                        contexts.append(topic)
                        break
            else:
                # 主題行がなければ最初の数行をコンテキストに
                first_lines = [
                    l.strip() for l in content.splitlines()[:10]
                    if l.strip() and not l.startswith("#") and not l.startswith("---")
                ]
                if first_lines:
                    contexts.append(" ".join(first_lines[:2])[:100])
        except Exception:
            continue

    return contexts


# ---------------------------------------------------------------------------
# Built-in training corpus (Handoff がない場合のフォールバック)
# ---------------------------------------------------------------------------

FALLBACK_INPUTS = [
    "なぜこのプロジェクトは存在するのか",
    "アーキテクチャを設計して構造を決める",
    "不安で仕方がない、大丈夫だろうか",
    "スコープと対象範囲を明確に定義する",
    "今がこの機能を開発する適切なタイミングか",
    "この実装は正しいか検証してレビューする",
    "目標を再定義したい。今の方向性は正しいか",
    "モチベーションが下がって疲れた",
]


# ---------------------------------------------------------------------------
# Daily Training Runner
# ---------------------------------------------------------------------------


def run_daily_training(
    rounds: int = 5,
    force_cpu: bool = False,
    notify: bool = False,
) -> dict:
    """日次トレーニングを実行する。"""
    from mekhane.fep.e2e_loop import run_loop_v2

    # Persistent A matrix
    a_matrix_dir = Path.home() / "oikos/01_ヘゲモニコン｜Hegemonikon/data/fep"
    a_matrix_dir.mkdir(parents=True, exist_ok=True)
    a_matrix_path = str(a_matrix_dir / "endurance_A.npy")

    # Log file
    log_dir = Path.home() / "oikos/01_ヘゲモニコン｜Hegemonikon/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"e2e_daily_{ts}.jsonl"

    # Get training inputs
    handoff_contexts = _get_handoff_contexts()
    inputs = handoff_contexts + FALLBACK_INPUTS
    random.shuffle(inputs)
    inputs = inputs[:rounds]

    logger.info("═══ FEP Daily Training ═══")
    logger.info(f"Rounds: {rounds}")
    logger.info(f"Handoff contexts: {len(handoff_contexts)}")
    logger.info(f"A-matrix: {a_matrix_path}")

    start = time.time()
    results_summary = []
    errors = 0

    with open(log_path, "w") as f:
        for i, text in enumerate(inputs):
            try:
                result = run_loop_v2(
                    text,
                    cycles=2,
                    a_matrix_path=a_matrix_path,
                    force_cpu=force_cpu,
                )

                last_cycle = result.cycles[-1]
                entry = {
                    "ts": datetime.now().isoformat(),
                    "round": i,
                    "input": text[:60],
                    "action": last_cycle.action_name,
                    "series": last_cycle.selected_series,
                    "attractor": last_cycle.attractor_series,
                    "entropy": round(last_cycle.fep_entropy, 4),
                    "confidence": round(last_cycle.fep_confidence, 3),
                    "a_updated": last_cycle.a_matrix_updated,
                    "learning": result.learning_proof,
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                f.flush()

                action_emoji = "🟢" if last_cycle.action_name != "observe" else "🔴"
                logger.info(
                    f"  [{i+1}/{rounds}] {action_emoji} {last_cycle.action_name} "
                    f"[{last_cycle.selected_series or '-'}] "
                    f"← '{text[:30]}...'"
                )
                results_summary.append(entry)

            except Exception as e:
                errors += 1
                logger.warning(f"  [{i+1}/{rounds}] ❌ Error: {e}")
                f.write(json.dumps({
                    "ts": datetime.now().isoformat(),
                    "round": i,
                    "input": text[:60],
                    "error": str(e),
                }, ensure_ascii=False) + "\n")
                f.flush()

    elapsed = time.time() - start

    # Summary stats
    act_count = sum(1 for r in results_summary if r["action"] != "observe")
    obs_count = sum(1 for r in results_summary if r["action"] == "observe")
    avg_entropy = (
        sum(r["entropy"] for r in results_summary) / len(results_summary)
        if results_summary else 0
    )

    summary = {
        "date": datetime.now().isoformat()[:10],
        "rounds": rounds,
        "elapsed_sec": round(elapsed, 1),
        "act": act_count,
        "observe": obs_count,
        "errors": errors,
        "avg_entropy": round(avg_entropy, 3),
        "handoff_contexts": len(handoff_contexts),
        "log_path": str(log_path),
    }

    logger.info("")
    logger.info("═══ Training Complete ═══")
    logger.info(f"Elapsed: {elapsed:.1f}s")
    logger.info(f"Act: {act_count} | Observe: {obs_count} | Errors: {errors}")
    logger.info(f"Avg entropy: {avg_entropy:.3f}")
    logger.info(f"Log: {log_path}")

    # Slack notification (optional)
    if notify:
        _notify_slack(summary)

    return summary


def _notify_slack(summary: dict):
    """結果を Slack Webhook で通知する。"""
    import urllib.request

    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook or not webhook.startswith("http"):
        logger.info("Slack notification skipped (no SLACK_WEBHOOK_URL)")
        return

    text = (
        f"🧠 *FEP Daily Training* ({summary['date']})\n"
        f"Rounds: {summary['rounds']} | "
        f"Act: {summary['act']} | Observe: {summary['observe']}\n"
        f"Avg entropy: {summary['avg_entropy']} | "
        f"Elapsed: {summary['elapsed_sec']}s"
    )

    try:
        payload = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(
            webhook,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        logger.info("📡 Slack notification sent")
    except Exception as e:
        logger.warning(f"Slack notification failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="FEP Daily Training")
    parser.add_argument(
        "--rounds", type=int, default=5,
        help="Number of training rounds (default: 5)",
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU mode")
    parser.add_argument("--notify", action="store_true", help="Send Slack notification")
    args = parser.parse_args()

    run_daily_training(
        rounds=args.rounds,
        force_cpu=args.cpu,
        notify=args.notify,
    )


if __name__ == "__main__":
    main()
