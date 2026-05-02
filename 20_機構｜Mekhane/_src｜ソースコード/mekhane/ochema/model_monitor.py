# PROOF: [L2/インフラ] <- mekhane/ochema/ DX-010 N.8/N.11→新モデル早期検出モニター
# PURPOSE: GetUserStatus をポーリングし、モデル一覧の変更をリアルタイムで検出する。
#   MODEL_ANTHROPIC_ANTIGRAVITY_RESEARCH 等の新モデル追加を即座に通知。
#   DX-010 §N.11: Unleash Feature Flag polling で routing/flag 変更も検出。
from __future__ import annotations
from typing import Optional
"""model_monitor — 新モデル早期検出モニター。

Usage:
    # 単発チェック
    python -m mekhane.ochema.model_monitor

    # デーモンモード (5分間隔)
    python -m mekhane.ochema.model_monitor --daemon --interval 300

    # cron (毎5分)
    */5 * * * * cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && PYTHONPATH=. .venv/bin/python -m mekhane.ochema.model_monitor
"""


import hashlib
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Config ---

STATE_DIR = Path.home() / ".cache" / "ochema" / "model_monitor"
STATE_FILE = STATE_DIR / "last_models.json"
HISTORY_FILE = STATE_DIR / "model_history.jsonl"

# Watch targets: models containing these substrings trigger HIGH alert
WATCH_PATTERNS = [
    "ANTHROPIC_ANTIGRAVITY",
    "ANTHROPIC_RESEARCH",
    "CLAUDE",
    "GPT",
    "DEEPSEEK",
    "O1",
    "O3",
    "O4",        # DX-010 §N.11: MODEL_CHAT_O4_MINI
    "M38",       # DX-010 §N.11.5: 新モデル (16K tokens)
    "M39",       # DX-010 §N.11.5: 新モデル (10K tokens)
    "M40",       # 予備: 将来の新モデル
    "HAIKU",     # Claude Haiku variants
]

# --- DX-010 §N.11: Unleash Feature Flag Polling ---
# Production token (gcore メモリダンプから抽出, 2026-03-04)
_UNLEASH_URL = "https://antigravity-unleash.goog/api/client/features"
_UNLEASH_TOKEN = "*:production.853c3f3dde009b1db67a70e1de9cfff6e3e373524f451b88b8846542"

# Unleash flags to watch for changes
UNLEASH_WATCH_FLAGS = [
    "api-provider-routing-config",
    "CASCADE_PREMIUM_CONFIG_OVERRIDE",
    "ANTHROPIC_ACCESS_ACL_GROUPS",
    "MODEL_PLACEHOLDER_M38_TOKENS",
    "MODEL_PLACEHOLDER_M39_TOKENS",
    "recommended-model",
    "vista-model-id",
    "cascade-knowledge-config",
]


# --- Core ---


# PURPOSE: 現在の全モデル構成を LS から取得する
def fetch_model_snapshot() -> dict:
    """LS の GetUserStatus から全モデル構成を取得する。

    Returns:
        dict: {models: [...], digest: "sha256...", timestamp: "ISO"}
    """
    from mekhane.ochema.antigravity_client import AntigravityClient

    client = AntigravityClient()
    status = client.get_status()

    # cascadeModelConfigData から全モデルを抽出
    config_data = (
        status.get("userStatus", {})
        .get("cascadeModelConfigData", {})
    )
    client_configs = config_data.get("clientModelConfigs", [])

    models = []
    for c in client_configs:
        model_id = c.get("modelOrAlias", {}).get("model", "")
        quota = c.get("quotaInfo", {})
        models.append({
            "id": model_id,
            "label": c.get("label", ""),
            "remaining_pct": round(quota.get("remainingFraction", 0) * 100),
            "images": c.get("supportsImages", False),
            "recommended": c.get("isRecommended", False),
            "has_quota": bool(quota),
        })

    # SHA256 ダイジェスト (モデル ID のみで計算 — quota 変動は無視)
    model_ids = sorted(m["id"] for m in models)
    digest = hashlib.sha256(json.dumps(model_ids).encode()).hexdigest()[:16]

    return {
        "models": models,
        "model_ids": model_ids,
        "digest": digest,
        "timestamp": datetime.now().isoformat(),
        "total": len(models),
    }


# PURPOSE: 差分を検出し、追加・削除されたモデルを返す
def detect_changes(current: dict, previous: dict) -> dict:
    """前回のスナップショットとの差分を検出する。

    Returns:
        dict: {changed: bool, added: [...], removed: [...], alerts: [...]}
    """
    prev_ids = set(previous.get("model_ids", []))
    curr_ids = set(current.get("model_ids", []))

    added = curr_ids - prev_ids
    removed = prev_ids - curr_ids

    # Alert レベル判定
    alerts = []
    for model_id in added:
        level = "HIGH" if any(p in model_id.upper() for p in WATCH_PATTERNS) else "INFO"
        # モデルの詳細を取得
        model_info = next((m for m in current["models"] if m["id"] == model_id), {})
        alerts.append({
            "type": "MODEL_ADDED",
            "level": level,
            "model_id": model_id,
            "label": model_info.get("label", ""),
            "message": f"{'🚨' if level == 'HIGH' else '📦'} 新モデル: {model_info.get('label', model_id)}",
        })

    for model_id in removed:
        alerts.append({
            "type": "MODEL_REMOVED",
            "level": "INFO",
            "model_id": model_id,
            "message": f"🗑️ モデル削除: {model_id}",
        })

    return {
        "changed": bool(added or removed),
        "added": list(added),
        "removed": list(removed),
        "alerts": alerts,
        "prev_digest": previous.get("digest", ""),
        "curr_digest": current.get("digest", ""),
    }


# PURPOSE: デスクトップ通知を送信する (notify-send)
def send_notification(title: str, body: str, urgency: str = "normal") -> None:
    """デスクトップ通知 (notify-send) を送信する。"""
    try:
        subprocess.run(
            ["notify-send", f"--urgency={urgency}", title, body],
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        logger.debug("notify-send not available")
    except OSError as e:
        logger.debug("Notification failed: %s", e)


# PURPOSE: 状態を永続化する
def save_state(snapshot: dict) -> None:
    """最新のスナップショットを状態ファイルに保存する。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))


# PURPOSE: 前回の状態を読み込む
def load_previous_state() -> Optional[dict]:
    """前回のスナップショットを読み込む。"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


# PURPOSE: 変更履歴を JSONL に追記する
def append_history(entry: dict) -> None:
    """変更履歴を JSONL に追記する。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# PURPOSE: メインのモニタリングロジック
def check_once(verbose: bool = True) -> dict:
    """1回のモニタリングチェックを実行する。

    Returns:
        dict: {snapshot, changes, alerts}
    """
    snapshot = fetch_model_snapshot()

    if verbose:
        print(f"📊 モデル数: {snapshot['total']}  ダイジェスト: {snapshot['digest']}")
        for m in snapshot["models"]:
            quota_str = f" [{m['remaining_pct']}%]" if m["has_quota"] else ""
            rec = " ⭐" if m["recommended"] else ""
            img = " 🖼️" if m["images"] else ""
            print(f"  {m['label']:40s} {m['id']:45s}{quota_str}{rec}{img}")

    previous = load_previous_state()
    if previous is None:
        # 初回実行
        save_state(snapshot)
        if verbose:
            print("\n✅ 初回スナップショット保存完了")
        return {"snapshot": snapshot, "changes": None, "first_run": True}

    changes = detect_changes(snapshot, previous)

    if changes["changed"]:
        if verbose:
            print(f"\n🔔 変更検出! (prev={changes['prev_digest']} → curr={changes['curr_digest']})")
            for alert in changes["alerts"]:
                print(f"  {alert['message']}")

        # デスクトップ通知
        for alert in changes["alerts"]:
            urgency = "critical" if alert["level"] == "HIGH" else "normal"
            send_notification(
                "🔔 Ochēma Model Monitor",
                alert["message"],
                urgency=urgency,
            )

        # 履歴追記
        append_history({
            "timestamp": snapshot["timestamp"],
            "added": changes["added"],
            "removed": changes["removed"],
            "digest": snapshot["digest"],
        })
    else:
        if verbose:
            print(f"\n✅ 変更なし (digest: {snapshot['digest']})")

    # 状態更新 (毎回保存)
    save_state(snapshot)

    return {"snapshot": snapshot, "changes": changes}


# --- Unleash Feature Flag Polling ---


def fetch_unleash_flags() -> dict | None:
    """Unleash production API から feature flags を取得する。

    DX-010 §N.11: gcore メモリダンプから抽出した production トークンを使用。

    Returns:
        dict: {features: [...], total: N, enabled: N} or None on error
    """
    import urllib.request
    import urllib.error

    req = urllib.request.Request(
        _UNLEASH_URL,
        headers={"Authorization": _UNLEASH_TOKEN},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, OSError) as e:
        logger.warning("Unleash fetch failed: %s", e)
        return None

    features = data.get("features", [])
    return {
        "features": features,
        "total": len(features),
        "enabled": sum(1 for f in features if f.get("enabled")),
    }


def check_unleash_changes(verbose: bool = True) -> dict | None:
    """Unleash feature flag の変更を検出する。

    UNLEASH_WATCH_FLAGS に指定されたフラグの enabled 状態と variant を監視。
    """
    flags_data = fetch_unleash_flags()
    if flags_data is None:
        return None

    features = {f["name"]: f for f in flags_data["features"]}

    # Watch flags の現在値を抽出
    watched = {}
    for name in UNLEASH_WATCH_FLAGS:
        f = features.get(name)
        if f:
            # 重要な variant の値を抽出 (最初の strategy の最初の variant)
            variant_val = None
            for s in f.get("strategies", []):
                for v in s.get("variants", []):
                    payload = v.get("payload", {}).get("value", "")
                    if payload:
                        variant_val = payload[:200]  # Truncate for digest
                        break
                if variant_val:
                    break
            watched[name] = {
                "enabled": f.get("enabled", False),
                "variant_preview": variant_val,
            }

    # Digest for change detection
    digest = hashlib.sha256(json.dumps(watched, sort_keys=True).encode()).hexdigest()[:16]

    # Compare with previous
    unleash_state_file = STATE_DIR / "last_unleash.json"
    prev_digest = ""
    if unleash_state_file.exists():
        try:
            prev = json.loads(unleash_state_file.read_text())
            prev_digest = prev.get("digest", "")
        except (json.JSONDecodeError, OSError):
            pass

    changed = digest != prev_digest and prev_digest != ""

    if verbose:
        print(f"\n🏴 Unleash: {flags_data['enabled']}/{flags_data['total']} enabled (digest: {digest})")
        for name, info in watched.items():
            status = "✅" if info["enabled"] else "❌"
            print(f"  {status} {name}")

    if changed:
        msg = f"🏴 Unleash flag 変更検出 (prev={prev_digest} → curr={digest})"
        if verbose:
            print(f"\n{msg}")
        send_notification("🏴 Unleash Flag Change", msg, urgency="critical")
        append_history({
            "timestamp": datetime.now().isoformat(),
            "type": "unleash_change",
            "digest": digest,
            "watched": watched,
        })

    # Save state
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    unleash_state_file.write_text(json.dumps(
        {"digest": digest, "watched": watched, "timestamp": datetime.now().isoformat()},
        ensure_ascii=False, indent=2,
    ))

    return {"digest": digest, "changed": changed, "watched": watched}


# PURPOSE: デーモンモードで定期実行する
def daemon_mode(interval: int = 300, verbose: bool = False) -> None:
    """デーモンモードで定期的にモニタリングする。

    Args:
        interval: チェック間隔 (秒, デフォルト 300 = 5分)
        verbose: 詳細出力
    """
    print(f"🔄 Model Monitor デーモン開始 (間隔: {interval}秒)")
    while True:
        try:
            result = check_once(verbose=verbose)
            changes = result.get("changes")
            if changes and changes.get("changed"):
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"🔔 変更検出: +{len(changes['added'])} -{len(changes['removed'])}"
                )
            elif verbose:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 変更なし")
        except OSError as e:
            logger.error("Monitor check failed: %s", e)
            if verbose:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ エラー: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ochēma Model Monitor")
    parser.add_argument("--daemon", action="store_true", help="デーモンモード")
    parser.add_argument("--interval", type=int, default=300, help="チェック間隔 (秒)")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument("--history", action="store_true", help="変更履歴を表示")
    args = parser.parse_args()

    if args.history:
        if HISTORY_FILE.exists():
            for line in HISTORY_FILE.read_text().strip().split("\n"):
                entry = json.loads(line)
                print(f"{entry['timestamp']}: +{entry.get('added', [])} -{entry.get('removed', [])}")
        else:
            print("履歴なし")
        sys.exit(0)

    if args.daemon:
        daemon_mode(interval=args.interval, verbose=args.verbose)
    else:
        check_once(verbose=True)
