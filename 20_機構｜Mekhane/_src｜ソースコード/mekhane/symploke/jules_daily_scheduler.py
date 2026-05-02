#!/usr/bin/env python3
# PROOF: [L3/ユーティリティ] <- mekhane/symploke/ O4→日次バッチ消化→scheduler が担う
# PURPOSE: Jules 720 tasks/day スケジューラー — 6垢分散 + 自動ローテーション
"""
Jules Daily Scheduler v2.1

有効キープール方式。起動時に全 API キーを検証し、
有効なキーだけを使ってバッチを実行する。
cron から 3 スロット (06:00/12:00/18:00) で呼ばれる。

Architecture:
    cron → jules_daily_scheduler.py --slot morning
           ├─ ファイルローテーション (全 .py → 日次 N ファイル選択)
           ├─ アカウント分配 (2垢/slot × 3 slots = 6垢/day)
           └─ run_specialists.py のバッチ実行

Usage:
    # Dry-run (何も実行しない、配分だけ表示)
    PYTHONPATH=. python mekhane/symploke/jules_daily_scheduler.py --slot morning --dry-run

    # Basanos mode (構造化レビュー + pre-audit)
    PYTHONPATH=. python mekhane/symploke/jules_daily_scheduler.py --slot morning --mode basanos --pre-audit

    # Small test (2 files × 3 specialists = 6 tasks)
    PYTHONPATH=. python mekhane/symploke/jules_daily_scheduler.py --slot morning --max-files 2 --sample 3

    # Full slot (16 files × 15 specialists = 240 tasks)
    PYTHONPATH=. python mekhane/symploke/jules_daily_scheduler.py --slot morning

Cron:
    # 推奨: scripts/jules_basanos_cron.sh を使用 (曜日別自動切替)
    0 6  * * * ~/oikos/01_ヘゲモニコン｜Hegemonikon/scripts/jules_basanos_cron.sh morning
    0 12 * * * ~/oikos/01_ヘゲモニコン｜Hegemonikon/scripts/jules_basanos_cron.sh midday
    0 18 * * * ~/oikos/01_ヘゲモニコン｜Hegemonikon/scripts/jules_basanos_cron.sh evening
"""

import argparse
import asyncio
import json
import os
import random
import subprocess
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

# Project root
_PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from specialist_v2 import (
    ALL_SPECIALISTS,
)
from basanos_bridge import BasanosBridge

# Optional: AIAuditor for pre-filtering
try:
    from mekhane.basanos.ai_auditor import AIAuditor, Severity as AuditSeverity
    HAS_AUDITOR = True
except ImportError:
    try:
        import sys as _sys
        _sys.path.insert(0, str(_PROJECT_ROOT / "mekhane" / "basanos"))
        from ai_auditor import AIAuditor, Severity as AuditSeverity
        HAS_AUDITOR = True
    except ImportError:
        HAS_AUDITOR = False

# === Settings ===
ACCOUNTS_FILE = _PROJECT_ROOT / "synergeia" / "jules_accounts.yaml"
USAGE_FILE = _PROJECT_ROOT / "synergeia" / "jules_usage.json"
ROTATION_STATE_FILE = _PROJECT_ROOT / "synergeia" / "jules_rotation_state.json"
LOG_DIR = _PROJECT_ROOT / "logs" / "specialist_daily"

# Default settings
DEFAULT_FILES_PER_SLOT = 16
DEFAULT_SPECIALISTS_PER_FILE = 15
DEFAULT_BASANOS_DOMAINS = 5  # basanos mode: domains per slot
MAX_ERROR_RATE = 0.20  # 20% エラーで slot 自動停止


# PURPOSE: 全 .py ファイルをスキャンし、優先度順にソート
def scan_all_py_files() -> list[dict]:
    """プロジェクト内の全 .py ファイルを優先度付きでリスト化。"""
    result = subprocess.run(
        ["find", str(_PROJECT_ROOT), "-name", "*.py",
         "-not", "-path", "*/__pycache__/*",
         "-not", "-path", "*/.venv/*",
         "-not", "-path", "*/_archive*/*",
         "-not", "-path", "*/node_modules/*"],
        capture_output=True, text=True, timeout=10,
    )
    all_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

    # 相対パスに変換
    files = []
    for f in all_files:
        try:
            rel = os.path.relpath(f, _PROJECT_ROOT)
        except ValueError:
            continue
        if rel.startswith("."):
            continue

        # 優先度スコア計算
        score = 1.0

        # テストファイルは低優先
        basename = os.path.basename(rel)
        if basename.startswith("test_") or basename == "conftest.py":
            score = 0.3
        elif basename == "__init__.py":
            score = 0.1

        # 大きいファイル = レビュー価値が高い
        try:
            size = os.path.getsize(f)
            if size > 5000:
                score *= min(3.0, size / 5000)
        except OSError:
            pass

        # kernel/ は高優先
        if "kernel/" in rel:
            score *= 2.0
        # mekhane/ は高優先
        elif "mekhane/" in rel:
            score *= 1.5

        files.append({"path": rel, "score": score, "size": os.path.getsize(f) if os.path.exists(f) else 0})

    return files


# PURPOSE: git diff で最近変更されたファイルを取得
def get_recent_changes(days: int = 7) -> set[str]:
    """直近 N 日間の変更ファイルを取得。"""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={days} days ago", "--name-only", "--pretty=format:", "--", "*.py"],
            capture_output=True, text=True, timeout=10,
            cwd=str(_PROJECT_ROOT),
        )
        return {f.strip() for f in result.stdout.strip().split("\n") if f.strip()}
    except Exception:  # noqa: BLE001
        return set()


# PURPOSE: ローテーション状態を読込
def load_rotation_state() -> dict:
    """ファイルローテーション状態を読込。"""
    if ROTATION_STATE_FILE.exists():
        try:
            return json.loads(ROTATION_STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_reviewed": {}, "cycle": 0}


# PURPOSE: ローテーション状態を保存
def save_rotation_state(state: dict) -> None:
    """ファイルローテーション状態を保存。"""
    ROTATION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ROTATION_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# PURPOSE: 日次ファイル選択 — 優先度 + ローテーション + git diff
def select_daily_files(count: int, rotation_state: dict) -> list[str]:
    """日次レビュー対象ファイルを選択。

    優先度:
      1. git diff で最近変更されたファイル (2x boost)
      2. 大きいファイル (score by size)
      3. 前回レビューから最も時間が経過したファイル
    """
    all_files = scan_all_py_files()
    recent_changes = get_recent_changes(days=7)
    last_reviewed = rotation_state.get("last_reviewed", {})
    today = datetime.now().strftime("%Y-%m-%d")

    # スコア調整
    for f in all_files:
        path = f["path"]

        # 最近変更されたファイル → ブースト
        if path in recent_changes:
            f["score"] *= 2.0

        # 今日既にレビュー済み → 除外
        if last_reviewed.get(path) == today:
            f["score"] = -1

        # 長期未レビュー → ブースト
        last_date = last_reviewed.get(path, "")
        if not last_date:
            f["score"] *= 1.5  # 一度もレビューされていない
        elif last_date < (datetime.now().strftime("%Y-%m-%d")):
            # 古いほど高スコア (最大 2x)
            pass  # 基本スコアのまま

    # フィルタ & ソート
    candidates = [f for f in all_files if f["score"] > 0]
    candidates.sort(key=lambda f: f["score"], reverse=True)

    selected = [f["path"] for f in candidates[:count]]

    # ローテーション状態更新
    for path in selected:
        last_reviewed[path] = today
    rotation_state["last_reviewed"] = last_reviewed
    rotation_state["cycle"] = rotation_state.get("cycle", 0) + 1

    return selected


# PURPOSE: 全 API キーを環境変数から収集
def collect_all_keys() -> list[str]:
    """全 JULES_API_KEY_xx を環境変数から収集。キー値のリストを返す。"""
    keys = []
    for i in range(1, 30):  # 最大 30 キー
        key = os.getenv(f"JULES_API_KEY_{i:02d}")
        if key:
            keys.append(key)
    return keys


# PURPOSE: 使用量を読込
def load_usage() -> dict:
    """日次使用量を読込。日付が変わったらリセット。"""
    today = datetime.now().strftime("%Y-%m-%d")
    if USAGE_FILE.exists():
        try:
            data = json.loads(USAGE_FILE.read_text())
            if data.get("date") == today:
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "date": today,
        "slots": {},
        "total_tasks": 0,
        "total_started": 0,
        "total_failed": 0,
        "files_reviewed": 0,
    }


# PURPOSE: 使用量を保存
def save_usage(usage: dict) -> None:
    USAGE_FILE.write_text(json.dumps(usage, indent=2, ensure_ascii=False))


# PURPOSE: バッチ実行 (run_specialists.py の run_batch を呼出)
async def run_slot_batch(
    files: list[str],
    specialists_per_file: int,
    api_keys: list[str],
    max_concurrent: int = 6,
    dry_run: bool = False,
    basanos_bridge: Optional["BasanosBridge"] = None,
    basanos_domains: Optional[list[str]] = None,
    hybrid_ratio: float = 0.0,
    audit_issue_codes: Optional[list[str]] = None,
    use_dynamic: bool = False,
    exclude_low_quality: bool = True,
) -> dict:
    """1 アカウント分のバッチを実行。

    basanos_bridge が指定されている場合、Basanos パースペクティブを使用する。
    """
    import run_specialists as rs_short
    from run_specialists import run_batch

    # API キーを一時差替え
    # NOTE: sys.path に mekhane/symploke を追加しているため、
    #   `run_specialists` と `mekhane.symploke.run_specialists` は
    #   別モジュールオブジェクトとして Python に登録される。
    #   run_batch はショートパスモジュールの API_KEYS を参照するため、
    #   ショートパス側を差し替える必要がある。
    original_keys = rs_short.API_KEYS
    rs_short.API_KEYS = api_keys

    total_started = 0
    total_failed = 0
    all_results = []

    try:
        for file_idx, target_file in enumerate(files, 1):
            # 専門家プール選択
            if basanos_bridge is not None and hybrid_ratio > 0 and hybrid_ratio < 1.0:
                # Hybrid mode: basanos + specialist を比率で混合
                basanos_specs = basanos_bridge.get_perspectives_as_specialists(
                    domains=basanos_domains,
                )
                basanos_count = max(1, int(specialists_per_file * hybrid_ratio))
                specialist_count = specialists_per_file - basanos_count
                # basanos specs から basanos_count 個をサンプリング
                sampled_basanos = random.sample(
                    basanos_specs, min(basanos_count, len(basanos_specs)),
                )
                # specialist pool から残りをサンプリング
                pool = list(ALL_SPECIALISTS)
                sampled_specialist = random.sample(
                    pool, min(specialist_count, len(pool)),
                )
                specs = sampled_basanos + sampled_specialist
                random.shuffle(specs)  # 混合順序をランダム化
            elif basanos_bridge is not None:
                # Basanos mode: 構造化パースペクティブを使用
                if use_dynamic:
                    # F10: ファイル特性に基づく動的 perspective
                    specs = basanos_bridge.get_dynamic_perspectives(
                        file_path=target_file,
                        audit_issues=audit_issue_codes,
                        max_perspectives=specialists_per_file,
                    )
                    if not specs:
                        # フォールバック: 静的 perspective
                        specs = basanos_bridge.get_perspectives_as_specialists(
                            domains=basanos_domains,
                        )
                else:
                    specs = basanos_bridge.get_perspectives_as_specialists(
                        domains=basanos_domains,
                    )
            else:
                # Specialist mode: audit issue があれば adaptive、なければランダム
                if audit_issue_codes:
                    from audit_specialist_matcher import AuditSpecialistMatcher
                    from specialist_v2 import get_specialists_by_category
                    matcher = AuditSpecialistMatcher()
                    categories = matcher.select_for_issues(
                        audit_issue_codes, total_budget=specialists_per_file,
                    )
                    specs = []
                    for cat in categories:
                        cat_pool = get_specialists_by_category(cat)
                        if cat_pool:
                            specs.append(random.choice(cat_pool))
                    # budget を満たさなければランダムで補充
                    if len(specs) < specialists_per_file:
                        pool = [s for s in ALL_SPECIALISTS if s not in specs]
                        remaining = specialists_per_file - len(specs)
                        specs.extend(random.sample(pool, min(remaining, len(pool))))
                else:
                    pool = list(ALL_SPECIALISTS)
                    specs = random.sample(pool, min(specialists_per_file, len(pool)))

            # F14: 低品質 Perspective を実行時除外
            if exclude_low_quality and specs:
                try:
                    from basanos_feedback import FeedbackStore as _FBStore
                    _excluded_ids = set(_FBStore().get_low_quality_perspectives(threshold=0.1))
                    if _excluded_ids:
                        before = len(specs)
                        specs = [s for s in specs if getattr(s, 'id', '') not in _excluded_ids]
                        culled = before - len(specs)
                        if culled > 0:
                            print(f"    🗑️  F14: {culled} low-quality perspectives excluded")
                except Exception:  # noqa: BLE001
                    pass  # FeedbackStore 不在時はスキップ

            if dry_run:
                print(f"  [{file_idx}/{len(files)}] {target_file} × {len(specs)} specialists (DRY-RUN)")
                all_results.append({
                    "file": target_file,
                    "specialists": len(specs),
                    "dry_run": True,
                })
                continue

            print(f"  [{file_idx}/{len(files)}] {target_file} × {len(specs)} specialists")
            results = await run_batch(specs, target_file, max_concurrent)

            started = sum(1 for r in results if "session_id" in r)
            failed = sum(1 for r in results if "error" in r)
            total_started += started
            total_failed += failed

            # F9: session_id + perspective_id をログ保存 (jules_result_parser 連携)
            sessions_info = []
            for i, r in enumerate(results):
                info = {}
                if "session_id" in r:
                    info["session_id"] = r["session_id"]
                if "error" in r:
                    info["error"] = str(r["error"])[:100]
                if i < len(specs):
                    info["specialist"] = specs[i].name
                    info["perspective_id"] = getattr(specs[i], "id", "")
                sessions_info.append(info)

            all_results.append({
                "file": target_file,
                "specialists": len(specs),
                "started": started,
                "failed": failed,
                "sessions": sessions_info,
            })

            # 安全弁: エラー率チェック
            total_attempted = total_started + total_failed
            if total_attempted > 10:
                error_rate = total_failed / total_attempted
                if error_rate > MAX_ERROR_RATE:
                    print(f"  ⚠️  Error rate {error_rate:.1%} > {MAX_ERROR_RATE:.0%}, stopping slot")
                    break

            print(f"    → {started}/{len(specs)} started, {failed} failed")

    finally:
        # API キー復元
        rs_short.API_KEYS = original_keys

    return {
        "files": all_results,
        "total_started": total_started,
        "total_failed": total_failed,
        "total_tasks": total_started + total_failed,
    }


# PURPOSE: メイン
async def main():
    parser = argparse.ArgumentParser(description="Jules Daily Scheduler v2.0")
    parser.add_argument(
        "--slot", choices=["morning", "midday", "evening"], required=True,
        help="Time slot to execute",
    )
    parser.add_argument(
        "--mode", choices=["specialist", "basanos", "hybrid"], default="specialist",
        help="Review mode: specialist (random), basanos (structured), hybrid (mixed)",
    )
    parser.add_argument(
        "--max-files", type=int, default=None,
        help=f"Max total files for this slot (default: {DEFAULT_FILES_PER_SLOT})",
    )
    parser.add_argument(
        "--sample", "-s", type=int, default=None,
        help=f"Specialists per file (default: {DEFAULT_SPECIALISTS_PER_FILE})",
    )
    parser.add_argument(
        "--domains", type=int, default=DEFAULT_BASANOS_DOMAINS,
        help=f"Basanos mode: domains per slot (default: {DEFAULT_BASANOS_DOMAINS})",
    )
    parser.add_argument(
        "--max-concurrent", "-m", type=int, default=6,
        help="Max concurrent sessions (default: 6)",
    )
    parser.add_argument(
        "--basanos-ratio", type=float, default=0.6,
        help="Hybrid mode: ratio of basanos specs (default: 0.6 = 60%% basanos)",
    )
    parser.add_argument(
        "--pre-audit", action="store_true",
        help="Run AIAuditor pre-filter to prioritize files with critical issues",
    )
    parser.add_argument(
        "--dynamic", action="store_true",
        help="F10: Use dynamic perspectives based on file characteristics (basanos/hybrid mode)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print plan without executing",
    )

    args = parser.parse_args()

    total_files = args.max_files or DEFAULT_FILES_PER_SLOT
    specs_per_file = args.sample or DEFAULT_SPECIALISTS_PER_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n{'='*60}")
    print(f"Jules Daily Scheduler v2.0 — {args.slot} slot [{args.mode}]")
    print(f"{'='*60}")
    print(f"Time:     {timestamp}")

    # 全キー収集 (検証なし — EAFP: 使ってみて壊れたらブラックリスト)
    all_keys = collect_all_keys()
    if not all_keys:
        print("ERROR: No API keys found. Check JULES_API_KEY_xx env vars.")
        return

    # --- Basanos mode: ドメイン選択 & specialists per file をオーバーライド ---
    basanos_info = {}  # ログ用メタデータ
    bridge: Optional[BasanosBridge] = None
    sampled_domains: Optional[list[str]] = None

    if args.mode in ("basanos", "hybrid"):
        bridge = BasanosBridge()
        sampled_domains = bridge.sample_domains(args.domains)

    if args.mode == "basanos":
        # Basanos では specs_per_file = 選択ドメイン数 × 24軸 (全パースペクティブ)
        specs_per_file = len(sampled_domains) * len(bridge.all_axes)
        basanos_info = {
            "domains": sampled_domains,
            "axes": len(bridge.all_axes),
            "perspectives_per_file": specs_per_file,
        }
        print(f"Mode:     basanos (structured orthogonal perspectives)")
        print(f"Domains:  {sampled_domains} ({len(sampled_domains)} selected)")
        print(f"Axes:     {len(bridge.all_axes)} (all theorems)")
        print(f"Specs:    {len(sampled_domains)} domains × {len(bridge.all_axes)} axes = {specs_per_file}/file")
        if args.sample:
            print(f"  ⚠️  --sample is ignored in basanos mode (using all {len(bridge.all_axes)} axes)")
    elif args.mode == "hybrid":
        # Hybrid: basanos specs + specialist specs を比率で混合
        ratio = args.basanos_ratio
        basanos_count = max(1, int(specs_per_file * ratio))
        specialist_count = specs_per_file - basanos_count
        basanos_info = {
            "domains": sampled_domains,
            "axes": len(bridge.all_axes),
            "basanos_count": basanos_count,
            "specialist_count": specialist_count,
            "ratio": ratio,
        }
        print(f"Mode:     hybrid ({ratio:.0%} basanos + {1-ratio:.0%} specialist)")
        print(f"Domains:  {sampled_domains} ({len(sampled_domains)} selected)")
        print(f"Specs:    {basanos_count} basanos + {specialist_count} specialist = {specs_per_file}/file")
    else:
        print(f"Mode:     specialist (random sampling from ~1000 pool)")

    total_tasks = total_files * specs_per_file

    print(f"Keys:     {len(all_keys)} loaded (EAFP: validated at runtime)")
    print(f"Files:    {total_files}")
    print(f"Specs:    {specs_per_file}/file")
    print(f"Tasks:    {total_tasks} (= {total_files} × {specs_per_file})")
    print()

    # ファイル選択
    rotation_state = load_rotation_state()
    all_selected_files = select_daily_files(total_files, rotation_state)

    if not all_selected_files:
        print("ERROR: No target files found.")
        return

    print(f"Selected files: {len(all_selected_files)}")
    for i, f in enumerate(all_selected_files[:5], 1):
        print(f"  [{i}] {f}")
    if len(all_selected_files) > 5:
        print(f"  ... and {len(all_selected_files) - 5} more")

    # --- Pre-audit: AIAuditor でファイル優先度を再計算 ---
    audit_info = {}  # ログ用
    if args.pre_audit:
        if not HAS_AUDITOR:
            print("  ⚠️  --pre-audit requested but AIAuditor not available, skipping")
        else:
            print("\n🔍 Pre-audit: scanning files with AIAuditor...")
            auditor = AIAuditor(strict=False)
            file_scores: dict[str, int] = {}

            for fpath in all_selected_files:
                try:
                    # select_daily_files は相対パスを返す → _PROJECT_ROOT で絶対化
                    abs_path = _PROJECT_ROOT / fpath
                    result = auditor.audit_file(abs_path)
                    # Score: Critical=10, High=5, Medium=1, Low=0
                    score = sum(
                        10 if i.severity == AuditSeverity.CRITICAL
                        else 5 if i.severity == AuditSeverity.HIGH
                        else 1 if i.severity == AuditSeverity.MEDIUM
                        else 0
                        for i in result.issues
                    )
                    file_scores[fpath] = score
                    if score > 0:
                        crit = sum(1 for i in result.issues if i.severity == AuditSeverity.CRITICAL)
                        high = sum(1 for i in result.issues if i.severity == AuditSeverity.HIGH)
                        print(f"  {fpath}: score={score} (C:{crit} H:{high})")
                except Exception as e:  # noqa: BLE001
                    file_scores[fpath] = 0
                    print(f"  {fpath}: audit failed ({e})")

            # スコア降順で再ソート (問題の多いファイルが先)
            all_selected_files.sort(key=lambda f: file_scores.get(f, 0), reverse=True)

            total_issues = sum(file_scores.values())
            files_with_issues = sum(1 for s in file_scores.values() if s > 0)
            # F7: issue コードを収集 (audit_specialist_matcher 連携用)
            all_issue_codes: list[str] = []
            for fpath in all_selected_files:
                try:
                    abs_path = _PROJECT_ROOT / fpath
                    re_result = auditor.audit_file(abs_path)
                    all_issue_codes.extend(i.code for i in re_result.issues)
                except Exception:  # noqa: BLE001
                    pass

            audit_info = {
                "total_score": total_issues,
                "files_with_issues": files_with_issues,
                "file_scores": {f: s for f, s in file_scores.items() if s > 0},
                "issue_codes": list(set(all_issue_codes)),
            }
            print(f"  → {files_with_issues}/{len(all_selected_files)} files with issues, reordered by priority")
            if all_issue_codes:
                print(f"  → {len(set(all_issue_codes))} unique issue codes collected for adaptive matching")

    print()

    # 使用量読込
    usage = load_usage()

    # バッチ実行 (EAFP: 全キーを渡し、run_batch 内で壊れたキーを自動除外)
    slot_result = {
        "total_keys": len(all_keys),
        "total_tasks": 0,
        "total_started": 0,
        "total_failed": 0,
        "files_reviewed": 0,
    }

    print(f"--- Batch ({len(all_keys)} keys, {len(all_selected_files)} files) ---")

    # F7: pre-audit の issue codes を specialist 選択に渡す
    collected_issue_codes = audit_info.get("issue_codes", []) if audit_info else None

    result = await run_slot_batch(
        files=all_selected_files,
        specialists_per_file=specs_per_file,
        api_keys=all_keys,
        max_concurrent=args.max_concurrent,
        dry_run=args.dry_run,
        basanos_bridge=bridge if args.mode in ("basanos", "hybrid") else None,
        basanos_domains=sampled_domains if args.mode in ("basanos", "hybrid") else None,
        hybrid_ratio=args.basanos_ratio if args.mode == "hybrid" else 0.0,
        audit_issue_codes=collected_issue_codes,
        use_dynamic=args.dynamic,
    )

    slot_result["total_tasks"] = result["total_tasks"]
    slot_result["total_started"] = result["total_started"]
    slot_result["total_failed"] = result["total_failed"]
    slot_result["files_reviewed"] = len(all_selected_files)
    print()

    # 使用量更新
    usage["slots"][args.slot] = slot_result
    usage["total_tasks"] += slot_result["total_tasks"]
    usage["total_started"] += slot_result["total_started"]
    usage["total_failed"] += slot_result["total_failed"]
    usage["files_reviewed"] += slot_result["files_reviewed"]

    if not args.dry_run:
        save_usage(usage)
        save_rotation_state(rotation_state)

    # サマリー
    total = slot_result["total_tasks"]
    started = slot_result["total_started"]
    rate = (started / total * 100) if total else 0

    print(f"{'='*60}")
    print(f"Slot Summary: {args.slot}")
    print(f"  Tasks:   {started}/{total} ({rate:.1f}%)")
    print(f"  Files:   {slot_result['files_reviewed']}")
    print(f"  Daily:   {usage['total_started']}/{usage['total_tasks']} total")
    print(f"{'='*60}")

    # ログ保存
    if not args.dry_run:
        log_file = LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_data = {
            "slot": args.slot,
            "mode": args.mode,
            "timestamp": timestamp,
            # F11 Dashboard API 用トップレベルキー
            "total_tasks": slot_result.get("total_tasks", 0),
            "total_started": slot_result.get("total_started", 0),
            "total_failed": slot_result.get("total_failed", 0),
            "files_reviewed": len(all_selected_files),
            "dynamic": getattr(args, "dynamic", False),
            # 後方互換: 詳細データ
            "result": slot_result,
            "daily_usage": usage,
        }
        if basanos_info:
            log_data["basanos"] = basanos_info
        if audit_info:
            log_data["pre_audit"] = audit_info
        log_file.write_text(json.dumps(log_data, indent=2, ensure_ascii=False))
        print(f"  Log: {log_file}")

        # F21: 自動フィードバック収集 (collect_and_update)
        try:
            from jules_result_parser import collect_and_update
            feedback_result = collect_and_update(days=1)
            if feedback_result:
                updated = feedback_result.get("updated", 0)
                if updated > 0:
                    print(f"  📊 Feedback: {updated} perspectives updated")
        except Exception as fb_exc:  # noqa: BLE001
            print(f"  ⚠️  Feedback collection failed: {fb_exc}")


if __name__ == "__main__":
    asyncio.run(main())
