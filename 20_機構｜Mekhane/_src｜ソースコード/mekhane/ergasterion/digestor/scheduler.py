# PURPOSE: Digestor 定時収集デーモン — OS 非依存の論文消化スケジューラ
# PROOF: [L2/インフラ] <- mekhane/ergasterion/digestor/ A0→消化処理が必要→scheduler が担う
#!/usr/bin/env python3
"""
Digestor Scheduler

定期的に (毎日 06:00) 論文の digestor を実行する。

Usage:
  このモジュールは FastAPI hgk-backend (mekhane.api.server) の lifespan に
  統合されており、API サーバー起動時に自動的にバックグラウンド実行されます。
  手動でスタンドアロン実行することも可能ですが、基本的には不要です。
"""

from mekhane.paths import MNEME_STATE
import gc

import os
import sys
import time
import signal
import subprocess

from datetime import datetime
from pathlib import Path

# Import path setup — project root + mekhane dir
_mekhane_dir = Path(__file__).parent.parent.parent
_project_root = _mekhane_dir.parent
for _p in [str(_project_root), str(_mekhane_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import schedule



# 設定
SCHEDULE_TIME = "06:00"  # 毎日実行時刻
MAX_PAPERS = 30  # 取得論文数
DRY_RUN = False  # Live mode — 候補リスト生成 + /eat バッチ入力も生成
from mekhane.paths import OUTPUTS_DIR
LOG_DIR = OUTPUTS_DIR / "digestor"
PID_FILE = LOG_DIR / "scheduler.pid"
LOG_FILE = LOG_DIR / "scheduler.log"


# PURPOSE: ログ出力
def log(msg: str):
    """ログ出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)

    # ファイルにも書き込み
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# PURPOSE: GNOME デスクトップ通知
def notify_desktop(title: str, body: str):
    """GNOME デスクトップ通知を送信"""
    try:
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        subprocess.run(
            ["notify-send", "--urgency=normal",
             "--icon=dialog-information", title, body],
            env=env,
            timeout=5,
            check=False,
        )
        log(f"Desktop notification sent: {title}")
    except Exception as e:  # noqa: BLE001
        log(f"Desktop notification failed: {e}")


# Cooldown: 最小実行間隔 (秒) — 暴走防止
MIN_RUN_INTERVAL_SECONDS = 6 * 3600  # 6時間


# PURPOSE: 消化パイプライン実行 (APIサーバー内部から直接実行)
def run_digestor():
    """消化パイプライン実行 — FastAPI lifespan に統合されたため直接実行する

    戦略:
      APIサーバー (hgk-backend) 内部でバックグラウンドスレッドとして実行される。
      Embedder はすでにプロセス内でロード済みのため、オーバーヘッドなく
      安全にパイプラインを実行できる。

    暴走防止:
      state.json の last_run を確認し、MIN_RUN_INTERVAL_SECONDS (6h) 以内の
      再実行をスキップする。V-2026-03-02/06 暴走事件 (470/641 runs) への対策。
    """
    from mekhane.ergasterion.digestor.pipeline import DigestorPipeline
    from mekhane.ergasterion.digestor.state import record_run, load_state

    # === Cooldown guard ===
    try:
        state = load_state()
        last_run = state.get("last_run")
        if last_run:
            from datetime import datetime, timezone
            last_dt = datetime.fromisoformat(last_run)
            now = datetime.now(timezone.utc)
            elapsed = (now - last_dt).total_seconds()
            if elapsed < MIN_RUN_INTERVAL_SECONDS:
                remaining_h = (MIN_RUN_INTERVAL_SECONDS - elapsed) / 3600
                log(f"Cooldown active: last run {elapsed/3600:.1f}h ago, "
                    f"next allowed in {remaining_h:.1f}h — skipping")
                return
    except Exception as e:  # noqa: BLE001
        log(f"Cooldown check failed (proceeding anyway): {e}")

    log("Starting scheduled digestor run...")

    try:
        pipeline = DigestorPipeline()
        result = pipeline.run(max_papers=MAX_PAPERS, max_candidates=10, dry_run=DRY_RUN)
        
        log(f"Digestor complete: {result.total_papers} papers, {result.candidates_selected} candidates")
        record_run(total_papers=result.total_papers, candidates_selected=result.candidates_selected)

        # デスクトップ通知
        if result.candidates_selected > 0:
            titles = [c.paper.title for c in result.candidates[:3]]
            body = f"{result.candidates_selected} 件の消化候補\n" + "\n".join(
                f"• {t[:40]}..." for t in titles
            )
            notify_desktop("📥 Digestor", body)
            
    except Exception as e:  # noqa: BLE001
        log(f"Digestor error: {e}")
        record_run(total_papers=0, candidates_selected=0, errors=[str(e)])
    finally:
        # 明示的 GC — メモリリーク防止のため
        gc.collect()


# PURPOSE: 古い候補の自動クリーンアップ
def cleanup_expired(max_age_days: int = 30):
    """30日以上 incoming/ に放置された候補を expired/ に移動する。"""
    incoming = MNEME_STATE / "incoming"
    expired = MNEME_STATE / "expired"

    if not incoming.exists():
        return

    now = time.time()
    threshold = max_age_days * 86400  # seconds
    moved = 0

    for f in incoming.glob("eat_*.md"):
        age = now - f.stat().st_mtime
        if age > threshold:
            expired.mkdir(parents=True, exist_ok=True)
            f.rename(expired / f.name)
            log(f"Expired: {f.name} ({int(age / 86400)}d old) → expired/")
            moved += 1

    if moved:
        log(f"Cleanup: {moved} expired candidates moved")


# PURPOSE: PID ファイル保存
def save_pid():
    """PID ファイル保存"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    log(f"PID saved: {PID_FILE}")


# PURPOSE: クリーンアップ
def cleanup(signum=None, frame=None):
    """クリーンアップ"""
    log("Scheduler stopping...")
    if PID_FILE.exists():
        PID_FILE.unlink()
    sys.exit(0)


# PURPOSE: メインループ
def main():
    """メインループ"""
    log("=" * 50)
    log("Digestor Scheduler starting")
    log(f"Schedule: daily at {SCHEDULE_TIME}")
    log(f"Max papers: {MAX_PAPERS}")
    log(f"Log file: {LOG_FILE}")
    log("=" * 50)

    # シグナルハンドラ
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    # PID 保存
    save_pid()

    # スケジュール設定
    schedule.every().day.at(SCHEDULE_TIME).do(run_digestor)

    # 古い候補のクリーンアップ
    cleanup_expired()

    # 初回実行（確認用）
    log("Running initial check...")
    run_digestor()

    # メインループ
    log(f"Scheduler running. Next run at {SCHEDULE_TIME}")

    while True:
        schedule.run_pending()
        time.sleep(60)  # 1分ごとにチェック


# PURPOSE: FastAPI lifespan 用の非同期スケジューラーループ
async def start_async_scheduler_loop():
    """FastAPI の lifespan から asyncio.create_task で起動される非同期ループ。

    既存の schedule ライブラリを使いつつ、asyncio.to_thread でブロッキング部分を
    オフロードする。PID 管理は不要 (プロセスは FastAPI が管理)。

    Usage (server.py lifespan 内):
        app.state._scheduler_task = asyncio.create_task(start_async_scheduler_loop())
    """
    import asyncio

    log("=" * 50)
    log("Digestor Scheduler starting (API-integrated mode)")
    log(f"Schedule: daily at {SCHEDULE_TIME}")
    log(f"Max papers: {MAX_PAPERS}")
    log("=" * 50)

    # スケジュール設定
    schedule.every().day.at(SCHEDULE_TIME).do(run_digestor)

    # 古い候補のクリーンアップ (非同期にラップしてI/Oブロックを防ぐ)
    await asyncio.to_thread(cleanup_expired)

    # 初回実行
    log("Running initial digestor check...")
    await asyncio.to_thread(run_digestor)

    log(f"Scheduler loop running. Next run at {SCHEDULE_TIME}")
    while True:
        await asyncio.to_thread(schedule.run_pending)
        await asyncio.sleep(60)  # 1分ごとにチェック


if __name__ == "__main__":
    main()
