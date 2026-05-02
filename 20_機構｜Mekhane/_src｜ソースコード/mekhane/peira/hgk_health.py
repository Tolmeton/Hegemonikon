#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/peira/ A0→システム可観測性が必要→hgk_healthが担う
"""
Hegemonikón Health Dashboard — 全サービスの死活と品質を一覧表示

Usage:
    python -m mekhane.peira.hgk_health          # ターミナル出力
    python -m mekhane.peira.hgk_health --json   # JSON出力 (監視連携用)
    python -m mekhane.peira.hgk_health --slack  # Slack通知
    python -m mekhane.peira.hgk_health --n8n   # n8n WF-05 webhook送信
"""

import json
import locale
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from mekhane.paths import MNEME_STATE, HGK_ROOT, HANDOFF_DIR
from mekhane.subprocess_utils import get_utf8_env, run_utf8


# PURPOSE: ヘルスチェック結果を統一的に扱い、レポート生成と判定分岐を可能にする
@dataclass
class HealthItem:
    name: str
    status: str  # "ok" | "warn" | "error" | "unknown"
    detail: str = ""
    metric: Optional[float] = None

    # PURPOSE: emoji の処理
    @property
    def emoji(self) -> str:
        return {"ok": "🟢", "warn": "🟡", "error": "🔴", "unknown": "⚪"}.get(self.status, "❓")


# PURPOSE: 全体のヘルスレポートを保持
@dataclass
class HealthReport:
    timestamp: str = ""
    effective_profile: str = "full"
    items: list[HealthItem] = field(default_factory=list)

    # PURPOSE: 0.0-1.0 の総合スコア
    @property
    def score(self) -> float:
        """0.0-1.0 の総合スコア"""
        if not self.items:
            return 0.0
        weights = {"ok": 1.0, "warn": 0.6, "error": 0.0, "unknown": 0.3}
        return sum(weights.get(i.status, 0) for i in self.items) / len(self.items)


def get_effective_health_profile() -> str:
    """監査用: 実効プロファイル名。

    - 未設定 … ``full`` (厳格が既定)
    - ``full`` / ``linux`` / ``production`` … ``full``
    - ``cursor`` … 運用系のみスキップ/緩和 (品質行の閾値は緩めない)
    """
    p = os.environ.get("HGK_HEALTH_PROFILE", "").strip().lower()
    if p == "cursor":
        return "cursor"
    if p in ("full", "linux", "production"):
        return "full"
    return "full"


def use_ops_relaxed_checks() -> bool:
    """True のときのみ Linux 専用運用 (systemd/cron/ローカル Digestor 等) をスキップまたは緩和。

    ``HGK_HEALTH_PROFILE=cursor`` のときだけ True。品質ゲート (Dendron/Kalon/定理活性等) には使わない。
    """
    return os.environ.get("HGK_HEALTH_PROFILE", "").strip().lower() == "cursor"


def _schtasks_query_verbose() -> str:
    """Windows Task Scheduler 一覧 (LIST /V)。出力はコンソールロケール (cp932 等) のため UTF-8 固定 decode は不可。"""
    if sys.platform != "win32":
        return ""
    try:
        enc = locale.getpreferredencoding(False) or "utf-8"
        r = subprocess.run(
            ["schtasks", "/Query", "/FO", "LIST", "/V"],
            timeout=45,
            capture_output=True,
            text=True,
            encoding=enc,
            errors="replace",
            env=get_utf8_env(),
        )
        return (r.stdout or "") + (r.stderr or "")
    except Exception:  # noqa: BLE001
        return ""


def check_gnosis_index_schedule() -> HealthItem:
    """Gnosis インデックス周期実行: Linux は systemd、Windows は Task Scheduler 相当。"""
    if sys.platform == "win32":
        blob = _schtasks_query_verbose()
        low = blob.lower()
        if "gnosis" in low:
            return HealthItem(
                "Gnosis Index Timer",
                "ok",
                "Task Scheduler lists gnosis-related task (Windows)",
            )
        return HealthItem(
            "Gnosis Index Timer",
            "warn",
            "no gnosis task in schtasks — add Task Scheduler job or use WSL/Linux",
        )
    return check_systemd_service("Gnosis Index Timer", "gnosis-index.timer", is_user=True)


def check_tier1_daily_schedule() -> HealthItem:
    """Tier1 日次: Linux は crontab、Windows は Task Scheduler 相当。"""
    if sys.platform == "win32":
        blob = _schtasks_query_verbose()
        low = blob.lower()
        if "run_tier1" in low or "tier1" in low:
            return HealthItem(
                "Tier 1 Daily Cron",
                "ok",
                "Task Scheduler lists run_tier1/tier1 (Windows)",
            )
        return HealthItem(
            "Tier 1 Daily Cron",
            "warn",
            "no run_tier1/tier1 task in schtasks — add Task Scheduler or crontab on WSL",
        )
    return check_cron("Tier 1 Daily Cron", "run_tier1")


def _check_hermeneus_windows() -> HealthItem:
    """Windows: CIM で CommandLine に hermeneus を含むプロセスを検出。"""
    try:
        r = run_utf8(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Process | "
                "Where-Object { $_.CommandLine -and ($_.CommandLine -match 'hermeneus') }).ProcessId",
            ],
            timeout=25,
        )
        raw = (r.stdout or "").strip()
        pids = [x for x in raw.replace("\n", " ").split() if x.isdigit()]
        if pids:
            return HealthItem(
                "Hermēneus MCP",
                "ok",
                f"running ({len(pids)} process(es), PIDs: {','.join(pids[:3])})",
            )
    except Exception as e:  # noqa: BLE001
        return HealthItem("Hermēneus MCP", "unknown", str(e))
    if use_ops_relaxed_checks():
        return HealthItem(
            "Hermēneus MCP",
            "ok",
            "IDE-managed (cursor ops — Hermēneus not in process scan)",
        )
    return HealthItem(
        "Hermēneus MCP",
        "warn",
        "no hermeneus in process CommandLine (start IDE MCP or run server)",
    )


# PURPOSE: systemd サービスの死活チェック
def check_systemd_service(name: str, unit: str, is_user: bool = False) -> HealthItem:
    try:
        cmd = ["systemctl"]
        if is_user:
            cmd.append("--user")
        cmd.extend(["is-active", unit])
        result = run_utf8(cmd, timeout=5)
        active = result.stdout.strip() == "active"
        return HealthItem(name, "ok" if active else "error", result.stdout.strip())
    except Exception as e:  # noqa: BLE001
        return HealthItem(name, "unknown", str(e))


# PURPOSE: PID ファイルベースのプロセス死活チェック (systemd を使わないデーモン用)
def check_pid_process(name: str, pid_file: str) -> HealthItem:
    pid_path = Path(pid_file).expanduser()
    if not pid_path.exists():
        return HealthItem(name, "error", "PID file not found — not running")
    try:
        pid = int(pid_path.read_text().strip())
        # /proc/<pid> の存在でプロセス死活を判定
        if Path(f"/proc/{pid}").exists():
            return HealthItem(name, "ok", f"running (PID {pid})")
        else:
            return HealthItem(name, "error", f"stale PID {pid} — process dead")
    except (ValueError, OSError) as e:
        return HealthItem(name, "unknown", str(e))


# PURPOSE: n8n の死活チェック (HTTP ベース — リモートホスト対応)
_N8N_HOSTS = ["127.0.0.1", "hgk.tail3b6058.ts.net"]  # ローカル優先、Tailscale フォールバック
_N8N_PORT = 5678

def check_n8n(name: str = "n8n Container") -> HealthItem:
    """n8n の /healthz エンドポイントで死活チェック。

    Docker コンテナではなくリモートホスト (Tailscale) で稼働している場合にも対応。
    """
    for host in _N8N_HOSTS:
        try:
            url = f"http://{host}:{_N8N_PORT}/healthz"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return HealthItem(name, "ok", f"healthy ({host}:{_N8N_PORT})")
        except Exception:  # noqa: BLE001
            continue
    return HealthItem(name, "error", f"unreachable on {_N8N_HOSTS}")


# PURPOSE: crontab エントリの存在チェック
def check_cron(name: str, pattern: str) -> HealthItem:
    try:
        result = run_utf8(["crontab", "-l"], timeout=5)
        lines = [l for l in result.stdout.split("\n") if pattern in l and not l.strip().startswith("#")]
        if lines:
            return HealthItem(name, "ok", f"{len(lines)} entry(ies)")
        return HealthItem(name, "error", "not found in crontab")
    except Exception as e:  # noqa: BLE001
        return HealthItem(name, "unknown", str(e))


def check_handoff() -> HealthItem:
    handoff_dir = HANDOFF_DIR
    if not handoff_dir.exists():
        return HealthItem("Handoff", "error", "directory does not exist")

    files = sorted(handoff_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return HealthItem("Handoff", "error", "0 files — /bye→handoff path broken?")

    latest = files[0]
    age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600
    detail = f"{len(files)} files, latest: {latest.name} ({age_hours:.0f}h ago)"

    if age_hours < 24:
        return HealthItem("Handoff", "ok", detail, metric=age_hours)
    elif age_hours < 72:
        return HealthItem("Handoff", "warn", detail, metric=age_hours)
    else:
        return HealthItem("Handoff", "error", detail, metric=age_hours)


# PURPOSE: Digestor の最新実行状態チェック
def check_digestor_log() -> HealthItem:
    log_file = Path.home() / ".hegemonikon" / "digestor" / "scheduler.log"
    if not log_file.exists():
        if use_ops_relaxed_checks():
            return HealthItem(
                "Digestor Log",
                "ok",
                "no local scheduler log (cursor ops — optional; run on server/WSL)",
            )
        return HealthItem("Digestor Log", "error", "log file not found")

    try:
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        last_lines = lines[-5:] if len(lines) >= 5 else lines
        last_text = "\n".join(last_lines)

        # 成功条件を先にチェック (フォールバック成功も含む)
        if "Digestor complete" in last_text and "Scheduler running" in last_text:
            return HealthItem("Digestor Log", "ok", "last run successful, scheduler alive")

        if "Digestor complete" in last_text:
            return HealthItem("Digestor Log", "ok", "last run successful")

        if "Scheduler running" in last_text:
            # エラーがあるが scheduler は生きている
            if "error" in last_text.lower() or "Error" in last_text:
                return HealthItem("Digestor Log", "warn", "last run had errors but scheduler alive")
            return HealthItem("Digestor Log", "ok", "scheduler waiting for next run")

        # エラーのみ
        if "error" in last_text.lower() or "Error" in last_text:
            return HealthItem("Digestor Log", "error", "errors in last run")

        return HealthItem("Digestor Log", "warn", "unknown state")
    except Exception as e:  # noqa: BLE001
        return HealthItem("Digestor Log", "unknown", str(e))


# PURPOSE: Dendron カバレッジチェック
def check_dendron() -> HealthItem:
    try:
        project_root = Path(__file__).parent.parent.parent
        result = run_utf8(
            [sys.executable, "-m", "mekhane.dendron.cli", "check", "mekhane/", "--format", "ci"],
            timeout=30,
            cwd=str(project_root),
            extra_env={"PYTHONPATH": str(project_root)}
        )
        output = result.stdout + result.stderr

        # カバレッジ率をパース (例: "Purpose: 3667 ok, 0 weak, 512 missing")
        import re
        ok_match = re.search(r"Purpose:\s*(\d+)\s*ok", output)
        missing_match = re.search(r"missing", output) # This is less precise, let's use full group
        purpose_match = re.search(r"Purpose:\s*(\d+)\s*ok,\s*(?:\d+\s*weak,\s*)?(\d+)\s*missing", output)
        
        if purpose_match:
            ok = int(purpose_match.group(1))
            missing = int(purpose_match.group(2))
            total = ok + missing
            coverage = (ok / total * 100) if total > 0 else 100.0
            
            detail = f"Purpose: {ok} ok, {missing} missing ({coverage:.0f}%)"

            if coverage >= 90:
                return HealthItem("Dendron L1", "ok", detail, metric=coverage / 100)
            elif coverage >= 70:
                return HealthItem("Dendron L1", "warn", detail, metric=coverage / 100)
            else:
                return HealthItem("Dendron L1", "error", detail, metric=coverage / 100)

        # フォールバック: 旧判定
        if "✅" in output:
            return HealthItem("Dendron L1", "ok", "PROOF coverage ok")
        elif "❌" in output:
            # 数値抽出を試みる
            lines = output.strip().split("\n")
            detail = lines[-3] if len(lines) >= 3 else "failures"
            return HealthItem("Dendron L1", "warn", detail)
        return HealthItem("Dendron L1", "unknown", "could not parse output")
    except Exception as e:  # noqa: BLE001
        return HealthItem("Dendron L1", "unknown", str(e))


# PURPOSE: 定理活性度チェック (Theorem Activity Report)
def check_theorem_activity() -> HealthItem:
    """24定理の活性度を集計し、体系の健全性を判定

    DX-008 R4: 直接発動と間接発動(ハブ経由)を分離し、
    「真の需要」と「ハブ依存生存」を区別する。
    """
    try:
        from mekhane.peira.theorem_activity import (
            scan_handoffs, classify_activity, THEOREM_WORKFLOWS
        )
        data = scan_handoffs(days=90)
        months = sorted(data["wf_by_month"].keys())
        months_span = max(len(months), 1)

        alive = dormant = dead = 0
        direct_alive = 0   # 直接発動で alive
        hub_only = 0        # ハブ経由のみで alive
        for wf_id in THEOREM_WORKFLOWS:
            direct = data["wf_counts"].get(wf_id, 0)
            via_hub = data["hub_counts"].get(wf_id, 0)
            total = direct + via_hub
            status = classify_activity(wf_id, total, months_span)
            if "alive" in status:
                alive += 1
                # 直接発動だけで alive 基準を満たすか判定
                direct_status = classify_activity(wf_id, direct, months_span)
                if "alive" in direct_status:
                    direct_alive += 1
                else:
                    hub_only += 1
            elif "death" in status:
                dead += 1
            else:
                dormant += 1

        total_theorems = len(THEOREM_WORKFLOWS)
        alive_rate = alive / total_theorems if total_theorems else 0
        detail = f"{alive}/{total_theorems} alive"
        if hub_only:
            detail += f" ({direct_alive} direct, {hub_only} hub-only)"
        if dormant:
            detail += f", {dormant} dormant"
        if dead:
            detail += f", {dead} dead"
        detail += f" ({alive_rate:.0%})"

        if alive >= 20:  # 83%+
            return HealthItem("Theorem Activity", "ok", detail, metric=alive_rate)
        elif alive >= 16:  # 66%+
            return HealthItem("Theorem Activity", "warn", detail, metric=alive_rate)
        else:
            return HealthItem("Theorem Activity", "error", detail, metric=alive_rate)
    except Exception as e:  # noqa: BLE001
        return HealthItem("Theorem Activity", "unknown", str(e))


# PURPOSE: Digest レポートの鮮度チェック
def check_digest_reports() -> HealthItem:
    report_dir = Path.home() / ".hegemonikon" / "digestor"
    reports = sorted(report_dir.glob("digest_report_*.json"), reverse=True)
    if not reports:
        if use_ops_relaxed_checks():
            return HealthItem(
                "Digest Reports",
                "ok",
                "skipped — no local digest JSON (cursor ops; optional)",
            )
        return HealthItem("Digest Reports", "warn", "no reports yet (first run pending)")

    latest = reports[0]
    age_hours = (datetime.now().timestamp() - latest.stat().st_mtime) / 3600

    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
        candidates = data.get("candidates", [])
        detail = f"{len(reports)} reports, latest: {len(candidates)} candidates ({age_hours:.0f}h ago)"
    except Exception:  # noqa: BLE001
        detail = f"{len(reports)} reports ({age_hours:.0f}h ago)"

    if age_hours < 26:  # ~daily
        return HealthItem("Digest Reports", "ok", detail, metric=age_hours)
    elif age_hours < 72:
        return HealthItem("Digest Reports", "warn", detail, metric=age_hours)
    else:
        return HealthItem("Digest Reports", "error", detail, metric=age_hours)


# PURPOSE: Kalon (圏論的構造) 品質チェック
def check_kalon() -> HealthItem:
    """category.py の圏論的構造が Fix(G∘F) 品質基準を満たすか検証"""
    try:
        from mekhane.fep.kalon_checker import KalonChecker, KalonLevel

        checker = KalonChecker()
        report = checker.check_all()

        # KalonLevel → HealthItem status mapping
        level_map = {
            KalonLevel.KALON: "ok",
            KalonLevel.APPROACHING: "warn",
            KalonLevel.INCOMPLETE: "error",
            KalonLevel.ABSENT: "error",
        }
        status = level_map.get(report.overall_level, "unknown")

        kalon_count = sum(1 for r in report.results if r.level == KalonLevel.KALON)
        total = len(report.results)
        detail = f"{kalon_count}/{total} KALON ({report.overall_score:.2f})"

        if report.all_issues:
            detail += f", {len(report.all_issues)} issues"

        return HealthItem("Kalon Quality", status, detail, metric=report.overall_score)
    except Exception as e:  # noqa: BLE001
        return HealthItem("Kalon Quality", "unknown", str(e))


# PURPOSE: 認知品質チェック (cognitive_quality.py 統合)
def check_cognitive_quality() -> HealthItem:
    """Handoff から認知品質指標を集計し、ダッシュボード品質を判定"""
    try:
        from mekhane.peira.cognitive_quality import scan_all
        data = scan_all(days=30)
        scores = data["quality_scores"]
        avg = sum(scores) / len(scores) if scores else 0.0
        violations = data["violations"]
        total_v = sum(violations)
        sessions = data["total"]
        compliance = (1 - sum(1 for v in violations if v > 0) / sessions) * 100 if sessions else 0
        direct_used = sum(1 for c in data["theorems_direct"].values() if c > 0)

        detail = (
            f"Q:{avg:.1f}/5 BC:{compliance:.0f}% T:{direct_used}/24"
        )
        status = "ok" if avg >= 3.5 and compliance >= 80 else "warn"
        return HealthItem(
            name="Cognitive Quality",
            status=status,
            detail=detail,
            metric=avg / 5.0,
        )
    except Exception as e:  # noqa: BLE001
        return HealthItem(
            name="Cognitive Quality",
            status="warn",
            detail=f"scan error: {e}",
        )


# PURPOSE: Krisis 随伴の健全性チェック
def check_krisis_adjunctions() -> HealthItem:
    """Krisis族の二重随伴 (K⊣E, P⊣D) の健全性を判定"""
    try:
        from mekhane.fep.krisis_adjunction_builder import check_krisis_adjunction_health
        results = check_krisis_adjunction_health()
        if not results:
            return HealthItem("Krisis Adjunctions", "unknown", "no data")

        statuses = [r[1] for r in results]
        details = "; ".join(r[2] for r in results)
        metrics = [r[3] for r in results if r[3] is not None]
        avg_metric = sum(metrics) / len(metrics) if metrics else None

        if all(s == "OK" for s in statuses):
            return HealthItem("Krisis Adjunctions", "ok", details, metric=avg_metric)
        elif any(s == "ERROR" for s in statuses):
            return HealthItem("Krisis Adjunctions", "error", details, metric=avg_metric)
        return HealthItem("Krisis Adjunctions", "warn", details, metric=avg_metric)
    except Exception as e:  # noqa: BLE001
        return HealthItem("Krisis Adjunctions", "unknown", str(e))


# PURPOSE: Hermēneus MCP サーバーの死活チェック
def check_hermeneus() -> HealthItem:
    """Hermēneus MCP サーバーのプロセス死活を確認。

    hermeneus_mcp_server.py / hermeneus_mcp.py プロセスを pgrep で検索。
    MCP は stdio/streamable-http ベースのため HTTP ping は不可。
    IDE (Gemini CLI) が起動する MCP プロセスなので、IDE 未起動時は error ではなく warn。
    """
    if sys.platform == "win32":
        return _check_hermeneus_windows()
    try:
        # 複数のプロセス名パターンを検索
        for pattern in ["hermeneus_mcp_server", "hermeneus_mcp.py", "hermeneus"]:
            result = run_utf8(
                ["pgrep", "-f", pattern],
                timeout=5
            )
            pids = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
            if pids:
                detail = f"running ({len(pids)} process(es), PIDs: {','.join(pids[:3])})"
                return HealthItem("Hermēneus MCP", "ok", detail)
        # MCP は IDE 起動型。未検出は IDE 未使用時の正常状態
        return HealthItem("Hermēneus MCP", "warn", "process not found (IDE-managed, may be normal)")
    except Exception as e:  # noqa: BLE001
        return HealthItem("Hermēneus MCP", "unknown", str(e))



# PURPOSE: Dendron MECE (概念的 ME/CE) チェック
def check_dendron_mece() -> HealthItem:
    """ディレクトリ構造の MECE 品質を判定 (テキストベースのみ — 速度優先)"""
    try:
        project_root = Path(__file__).parent.parent.parent
        src_dir = project_root / "mekhane"

        if not src_dir.exists():
            return HealthItem("Dendron MECE", "unknown", "mekhane/ not found")

        result = run_utf8(
            [sys.executable, "-m", "mekhane.dendron.cli", "mece", str(src_dir), "--ci"],
            timeout=60,
            cwd=str(project_root),
            extra_env={"PYTHONPATH": str(project_root)}
        )

        output = result.stdout + result.stderr
        import re

        # サマリ行をパース: "📊 合計: N issues (E errors, W warnings)"
        summary_match = re.search(r"合計:\s*(\d+)\s*issues\s*\((\d+)\s*errors,\s*(\d+)\s*warnings\)", output)
        if summary_match:
            total = int(summary_match.group(1))
            errors = int(summary_match.group(2))
            warnings = int(summary_match.group(3))

            # ME/CE 行をパース: "ME: M | CE: C"
            me_ce_match = re.search(r"ME:\s*(\d+)\s*\|\s*CE:\s*(\d+)", output)
            me_count = int(me_ce_match.group(1)) if me_ce_match else 0
            ce_count = int(me_ce_match.group(2)) if me_ce_match else 0

            detail = f"ME:{me_count} CE:{ce_count} ({errors}E, {warnings}W)"

            if errors == 0 and warnings < 50:
                return HealthItem("Dendron MECE", "ok", detail, metric=1.0 - (errors + warnings * 0.1) / max(total, 1))
            elif errors <= 2:
                return HealthItem("Dendron MECE", "warn", detail, metric=max(0.0, 1.0 - errors * 0.2))
            else:
                return HealthItem("Dendron MECE", "error", detail, metric=max(0.0, 1.0 - errors * 0.2))

        # "✅ MECE — issue なし" をチェック
        if "✅" in output and "MECE" in output:
            return HealthItem("Dendron MECE", "ok", "no issues", metric=1.0)

        return HealthItem("Dendron MECE", "unknown", "could not parse output")
    except subprocess.TimeoutExpired:
        return HealthItem("Dendron MECE", "warn", "timeout (>60s)")
    except Exception as e:  # noqa: BLE001
        return HealthItem("Dendron MECE", "unknown", str(e))


# PURPOSE: HGK API サーバーの死活チェック (HTTP ベース)
_HGK_API_HOSTS = ["127.0.0.1", "hgk.tail3b6058.ts.net"]  # ローカル優先、Tailscale フォールバック
_HGK_API_PORT = 9696

def check_hgk_backend(name: str = "HGK Backend (Digestor)") -> HealthItem:
    """HGK API サーバーの /api/health で死活チェック。

    systemd サービスではなく直接起動されている場合にも対応。
    """
    for host in _HGK_API_HOSTS:
        try:
            url = f"http://{host}:{_HGK_API_PORT}/api/health"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if body.get("status") == "ok":
                    return HealthItem(name, "ok", f"healthy ({host}:{_HGK_API_PORT})")
                return HealthItem(name, "warn", f"responded but status={body.get('status')}")
        except Exception:  # noqa: BLE001
            continue
    if use_ops_relaxed_checks():
        return HealthItem(
            name,
            "ok",
            "API not listening (cursor ops — start stack on host or use full on Linux)",
        )
    if sys.platform == "win32":
        return HealthItem(
            name,
            "warn",
            "API not listening on loopback — start HGK backend or use WSL/Linux systemd",
        )
    return check_systemd_service(name, "hgk-api.service", is_user=True)


# PURPOSE: 全ヘルスチェックを実行してレポートを生成
def run_health_check() -> HealthReport:
    prof = get_effective_health_profile()
    report = HealthReport(
        timestamp=datetime.now().isoformat(),
        effective_profile=prof,
    )

    # Service checks
    report.items.append(check_hgk_backend())
    report.items.append(check_n8n())
    if use_ops_relaxed_checks():
        report.items.append(
            HealthItem(
                "Gnosis Index Timer",
                "ok",
                "skipped — cursor ops (use full profile or WSL for systemd check)",
            )
        )
        report.items.append(
            HealthItem(
                "Tier 1 Daily Cron",
                "ok",
                "skipped — cursor ops (use full profile or WSL for crontab check)",
            )
        )
    else:
        report.items.append(check_gnosis_index_schedule())
        report.items.append(check_tier1_daily_schedule())
    report.items.append(check_hermeneus())

    # Data checks
    report.items.append(check_handoff())
    report.items.append(check_digestor_log())
    report.items.append(check_digest_reports())

    # Quality checks (optional, slower)
    report.items.append(check_dendron())
    report.items.append(check_dendron_mece())
    report.items.append(check_theorem_activity())
    report.items.append(check_kalon())
    report.items.append(check_cognitive_quality())
    report.items.append(check_krisis_adjunctions())

    return report


# PURPOSE: テキスト形式でレポートを表示
def format_terminal(report: HealthReport) -> str:
    lines = []
    lines.append("╔══════════════════════════════════════════╗")
    lines.append("║  Hegemonikón Health Dashboard            ║")
    lines.append(f"║  profile: {report.effective_profile:<28s} ║")
    lines.append(f"║  {report.timestamp[:19]:>38s}  ║")
    lines.append("╠══════════════════════════════════════════╣")

    for item in report.items:
        name = f"{item.name:.<25s}"
        lines.append(f"║  {item.emoji} {name} {item.detail[:30]:30s} ║")

    lines.append("╠══════════════════════════════════════════╣")
    score = report.score
    bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
    emoji = "🟢" if score >= 0.8 else "🟡" if score >= 0.5 else "🔴"
    lines.append(f"║  {emoji} Score: {score:.0%}  [{bar}]     ║")
    lines.append("╚══════════════════════════════════════════╝")
    return "\n".join(lines)


# PURPOSE: Slack webhook にレポートを送信
def send_slack(report: HealthReport):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        env_file = HGK_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().split("\n"):
                if line.startswith("SLACK_WEBHOOK_URL="):
                    webhook_url = line.split("=", 1)[1].strip().strip('"')

    if not webhook_url:
        print("⚠️ SLACK_WEBHOOK_URL not found", file=sys.stderr)
        return

    score = report.score
    emoji = "🟢" if score >= 0.8 else "🟡" if score >= 0.5 else "🔴"
    items_text = "\n".join(f"{i.emoji} {i.name}: {i.detail[:40]}" for i in report.items)
    text = f"{emoji} *HGK Health* — Score: {score:.0%}\n```\n{items_text}\n```"

    run_utf8(
        ["curl", "-s", "-X", "POST", webhook_url,
         "-H", "Content-type: application/json",
         "-d", json.dumps({"text": text})],
        timeout=10
    )


# PURPOSE: n8n WF-05 Health Alert webhook にレポートを送信
def send_n8n_alert(report: HealthReport) -> bool:
    """n8n の health-alert webhook にデータを送信。n8n 側で重大度分類と通知を行う。

    Returns:
        True if n8n accepted the alert, False otherwise.
    """
    url = "http://localhost:5678/webhook/health-alert"
    payload = json.dumps({
        "effective_profile": report.effective_profile,
        "items": [asdict(i) for i in report.items],
        "score": report.score,
        "timestamp": report.timestamp,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            severity = result.get("severity", "?")
            print(f"📡 n8n WF-05: severity={severity}", file=sys.stderr)
            return True
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ n8n WF-05 failed: {e}", file=sys.stderr)
        return False


# PURPOSE: CLI エントリポイント
def main():
    # Windows コンソール (cp932): JSON/詳細に U+2014 等が含まれると print が落ちる
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    import argparse
    parser = argparse.ArgumentParser(description="Hegemonikón Health Dashboard")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--slack", action="store_true", help="Send directly to Slack (bypass n8n)")
    parser.add_argument("--n8n", action="store_true", help="Send to n8n WF-05")
    parser.add_argument("--auto", action="store_true", help="n8n first, Slack fallback (for cron)")
    parser.add_argument("--no-n8n", action="store_true", help="Suppress auto n8n send")
    args = parser.parse_args()

    report = run_health_check()

    if args.json:
        out = {
            "effective_profile": report.effective_profile,
            "timestamp": report.timestamp,
            "score": report.score,
            "items": [asdict(i) for i in report.items],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    elif args.auto:
        # cron 用: n8n 優先 → 失敗時に Slack 直送フォールバック
        print(format_terminal(report))
        n8n_ok = send_n8n_alert(report)
        if not n8n_ok and report.score < 0.7:
            print("🔄 n8n unreachable, falling back to direct Slack", file=sys.stderr)
            send_slack(report)
    elif args.slack:
        # 直接 Slack送信 (n8n 未起動時のフォールバック)
        send_slack(report)
        print(format_terminal(report))
    else:
        print(format_terminal(report))

    # n8n 通知: n8n が Slack 通知の一元窓口
    # --n8n 明示指定 or スコア低下時は自動送信 (--slack/--auto との二重送信を回避)
    if not args.no_n8n and not args.slack and not args.auto:
        if args.n8n or report.score < 0.7:
            send_n8n_alert(report)

    # Exit code: 0 if score > 0.7, 1 otherwise
    sys.exit(0 if report.score >= 0.7 else 1)


if __name__ == "__main__":
    main()
