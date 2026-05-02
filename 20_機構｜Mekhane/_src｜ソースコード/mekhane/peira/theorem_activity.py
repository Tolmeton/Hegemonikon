#!/usr/bin/env python3
# PROOF: [L2/検証] <- A0→体系の健全性検証が必要→使われない定理=dead parameter
"""
Theorem Activity Report — 定理活性度レポート

Handoff ファイルから WF 発動頻度を集計し、「生存/休眠/死亡候補」を判定する。
Desktop Claude DX-008 の指摘に基づき実装。

Usage:
    python3 theorem_activity.py                  # 全期間レポート
    python3 theorem_activity.py --days 30        # 過去30日
    python3 theorem_activity.py --days 90        # 過去90日 (死亡候補検出)
    python3 theorem_activity.py --json           # JSON 出力
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# --- Configuration ---

from mekhane.paths import HANDOFF_DIR
from mekhane.symploke.handoff_files import list_handoff_files

# 24 定理 WF (Δ層) — ベースID のみ
# 正本: kernel/doctrine.md 統一随伴表 + nous/skills/*/SKILL.md
THEOREM_WORKFLOWS = {
    # Telos
    "noe": "V01 Noesis",
    "bou": "V02 Boulesis",
    "zet": "V03 Zetesis",
    "ene": "V04 Energeia",
    # Methodos
    "ske": "V05 Skepsis",
    "sag": "V06 Synagoge",
    "pei": "V07 Peira",
    "tek": "V08 Tekhne",
    # Krisis
    "kat": "V09 Katalepsis",
    "epo": "V10 Epoche",
    "pai": "V11 Proairesis",
    "dok": "V12 Dokimasia",
    # Diastasis
    "lys": "V13 Analysis",
    "ops": "V14 Synopsis",
    "akr": "V15 Akribeia",
    "arc": "V16 Architektonike",
    # Orexis
    "beb": "V17 Bebaiosis",
    "ele": "V18 Elenchos",
    "kop": "V19 Prokope",
    "dio": "V20 Diorthosis",
    # Chronos
    "hyp": "V21 Hypomnesis",
    "prm": "V22 Prometheia",
    "ath": "V23 Anatheoresis",
    "par": "V24 Proparaskeue",
}

# Ω層 Peras WF
PERAS_WORKFLOWS = {
    "o": "O Peras",
    "s": "S Peras",
    "h": "H Peras",
    "p": "P Peras",
    "k": "K Peras",
    "a": "A Peras",
    "x": "X-series",
    "ax": "AX Peras",
}

# 族 → 定理キーのマッピング (テスト・レポート用)
FAMILY_THEOREMS = {
    "Telos":     ["noe", "bou", "zet", "ene"],
    "Methodos":  ["ske", "sag", "pei", "tek"],
    "Krisis":    ["kat", "epo", "pai", "dok"],
    "Diastasis": ["lys", "ops", "akr", "arc"],
    "Orexis":    ["beb", "ele", "kop", "dio"],
    "Chronos":   ["hyp", "prm", "ath", "par"],
}

# Peras → 内部定理のハブ展開マッピング
# /o を実行すれば Telos 族が暗黙的に発動する
# 正本: kernel/doctrine.md 統一随伴表
HUB_EXPANSION = {
    "o": ["noe", "bou", "zet", "ene"],       # Telos
    "s": ["ske", "sag", "pei", "tek"],       # Methodos
    "h": ["kat", "epo", "pai", "dok"],       # Krisis
    "p": ["lys", "ops", "akr", "arc"],       # Diastasis
    "k": ["beb", "ele", "kop", "dio"],       # Orexis
    "a": ["hyp", "prm", "ath", "par"],       # Chronos
    "ax": list(THEOREM_WORKFLOWS.keys()),     # 全24定理
}

# マクロ → 内部定理のマッピング (明示的に定理を呼ぶマクロ)
MACRO_EXPANSION = {
    "dig": ["ops", "lys"],         # @dig — 分析・俯瞰
    "vet": ["dok", "ene", "akr"],  # @vet — 検証
    "proof": ["noe", "dok", "ene"],  # @proof = V:{/noe~/dia}
    "plan": ["bou", "dok"],         # @plan = /bou+_V:{/dia}
    "build": ["bou", "ene", "dok", "tek"],  # @build
    "ready": ["ops", "akr", "arc", "tek"],  # @ready
    "feel": ["beb", "ele", "kop"],  # @feel
    "clean": ["kat", "epo"],       # @clean
}

# τ層 タスクWF
TAU_WORKFLOWS = {
    "boot": "Boot",
    "bye": "Bye",
    "dev": "Dev",
    "now": "Now",
    "plan": "Plan",
    "eat": "Eat",
    "why": "Why",
    "vet": "Vet",
    "rev": "Rev",
    "exp": "Exp",
    "lib": "Lib",
    "lex": "Lex",
}

# 活性度の閾値
THRESHOLDS = {
    "alive": 1,         # 月1回以上 = 生存
    "dormant_months": 3, # 3ヶ月 0回 = 死亡候補
}

# WF 名にマッチするパターン（ファイルパス断片を除外）
# /xxx, /xxx+, /xxx- を対象。先頭が / で直前が空白か行頭
WF_PATTERN = re.compile(
    r'(?:^|(?<=\s))/(' +
    '|'.join(sorted(
        list(THEOREM_WORKFLOWS.keys()) +
        list(PERAS_WORKFLOWS.keys()) +
        list(TAU_WORKFLOWS.keys()),
        key=len, reverse=True  # longer matches first
    )) +
    r')([+\-]?)(?=\s|$|[,.\)}\]|])',
    re.MULTILINE
)


# PURPOSE: [L2-auto] Handoff ファイル名から日付を抽出
def parse_date_from_filename(path: Path) -> Optional[datetime]:
    """Handoff / session log ファイル名から日付を抽出"""
    patterns = [
        r'handoff_(\d{4}-\d{2}-\d{2})',       # handoff_2026-02-11_...
        r'handoff_(\d{8})',                     # handoff_20260210_...
        r'^(\d{4}-\d{2}-\d{2})_conv_',         # 2026-02-28_conv_...
        r'handoff_.*?(\d{4}-\d{2}-\d{2})',     # fallback
        r'(\d{4}-\d{2}-\d{2})',                 # any date in filename
    ]
    name = path.stem
    for pat in patterns:
        m = re.search(pat, name)
        if m:
            date_str = m.group(1)
            try:
                if '-' in date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    return datetime.strptime(date_str, "%Y%m%d")
            except ValueError:
                continue
    return None


# PURPOSE: [L2-auto] Handoff ファイルを走査し、WF 発動を集計
def scan_handoffs(days: Optional[int] = None) -> dict:
    """Handoff ファイルを走査し、WF 発動を集計

    検索対象:
    - sessions/handoff_*.md (直下およびサブディレクトリ)
    """
    cutoff = None
    if days:
        cutoff = datetime.now() - timedelta(days=days)

    # sessions/ 直下 + handoff/ サブディレクトリを検索
    all_wfs = list_handoff_files(HANDOFF_DIR)
    total_files = 0
    skipped = 0
    wf_counts: Counter = Counter()       # 直接発動
    hub_counts: Counter = Counter()       # ハブ経由の暗黙発動
    wf_by_month: dict[str, Counter] = defaultdict(Counter)

    for f in sorted(all_wfs):
        fdate = parse_date_from_filename(f)
        if cutoff and fdate and fdate < cutoff:
            skipped += 1
            continue

        total_files += 1
        content = f.read_text(errors="replace")

        month_key = fdate.strftime("%Y-%m") if fdate else "unknown"

        # WF 名を抽出
        for match in WF_PATTERN.finditer(content):
            wf_id = match.group(1)
            # base ID で集計
            wf_counts[wf_id] += 1
            wf_by_month[month_key][wf_id] += 1

            # ハブ展開: Peras の発動を内部定理にも加算
            if wf_id in HUB_EXPANSION:
                for sub_wf in HUB_EXPANSION[wf_id]:
                    hub_counts[sub_wf] += 1

    return {
        "total_files": total_files,
        "skipped": skipped,
        "wf_counts": wf_counts,
        "hub_counts": hub_counts,
        "wf_by_month": dict(wf_by_month),
    }


# PURPOSE: [L2-auto] 活性度を3段階で分類
def classify_activity(wf_id: str, count: int, months_span: int) -> str:
    """活性度を3段階で分類"""
    if months_span == 0:
        months_span = 1
    monthly_rate = count / months_span
    if monthly_rate >= THRESHOLDS["alive"]:
        return "🟢 alive"
    elif count == 0:
        return "🔴 death-candidate"
    else:
        return "🟡 dormant"


# PURPOSE: [L2-auto] 活性度レポートを生成
def generate_report(days: Optional[int] = None, as_json: bool = False) -> str:
    """活性度レポートを生成"""
    data = scan_handoffs(days)
    period_label = f"過去{days}日" if days else "全期間"

    # 月数の推定
    months = sorted(data["wf_by_month"].keys())
    if months:
        months_span = len(months)
    else:
        months_span = 1

    # --- Theorem Activity ---
    theorem_rows = []
    alive_count = 0
    dormant_count = 0
    dead_count = 0

    for wf_id, label in sorted(THEOREM_WORKFLOWS.items(), key=lambda x: x[1]):
        direct = data["wf_counts"].get(wf_id, 0)
        via_hub = data["hub_counts"].get(wf_id, 0)
        total_count = direct + via_hub
        status = classify_activity(wf_id, total_count, months_span)
        monthly = total_count / months_span if months_span else 0
        theorem_rows.append({
            "id": wf_id,
            "label": label,
            "direct": direct,
            "via_hub": via_hub,
            "count": total_count,
            "monthly": round(monthly, 1),
            "status": status,
        })
        if "alive" in status:
            alive_count += 1
        elif "death" in status:
            dead_count += 1
        else:
            dormant_count += 1

    if as_json:
        return json.dumps({
            "period": period_label,
            "total_handoffs": data["total_files"],
            "months_span": months_span,
            "theorems": theorem_rows,
            "summary": {
                "alive": alive_count,
                "dormant": dormant_count,
                "dead": dead_count,
                "total": len(THEOREM_WORKFLOWS),
            },
            "thresholds": THRESHOLDS,
        }, ensure_ascii=False, indent=2)

    # --- Text Format ---
    lines = []
    lines.append(f"# 定理活性度レポート — {period_label}")
    lines.append(f"")
    lines.append(f"> 分析対象: Handoff {data['total_files']}件 ({months_span}ヶ月間)")
    lines.append(f"> 閾値: 月1回以上=生存, 3ヶ月0回=死亡候補")
    lines.append(f"> ハブ展開: Peras (Ω層) の発動を内部定理にも加算")
    lines.append(f"> 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"")
    lines.append(f"## サマリー")
    lines.append(f"")
    lines.append(f"| 状態 | 数 | 割合 |")
    lines.append(f"|:-----|:---|:-----|")
    total = len(THEOREM_WORKFLOWS)
    lines.append(f"| 🟢 alive | {alive_count} | {alive_count*100//total}% |")
    lines.append(f"| 🟡 dormant | {dormant_count} | {dormant_count*100//total}% |")
    lines.append(f"| 🔴 death-candidate | {dead_count} | {dead_count*100//total}% |")
    lines.append(f"")
    lines.append(f"## 詳細")
    lines.append(f"")
    lines.append(f"| WF | 定理 | 直接 | Hub経由 | 合計 | 月平均 | 状態 |")
    lines.append(f"|:---|:-----|:-----|:--------|:-----|:-------|:-----|")
    for row in sorted(theorem_rows, key=lambda r: r["count"], reverse=True):
        lines.append(
            f"| /{row['id']} | {row['label']} | {row['direct']} | "
            f"{row['via_hub']} | {row['count']} | "
            f"{row['monthly']}/月 | {row['status']} |"
        )

    # --- Dead candidates ---
    dead_wfs = [r for r in theorem_rows if "death" in r["status"]]
    if dead_wfs:
        lines.append(f"")
        lines.append(f"## ⚠️ 死亡候補 (直接+Hub経由ともに0回)")
        lines.append(f"")
        lines.append(f"> 以下の定理は直接発動もハブ経由発動もゼロ。")
        lines.append(f"> **忘却の可能性**: マクロへの統合で復活を検討。")
        lines.append(f"")
        for r in dead_wfs:
            lines.append(f"- **{r['label']}** (`/{r['id']}`) — マクロ統合候補")

    # --- Peras & Tau (summary only) ---
    lines.append(f"")
    lines.append(f"## 補足: Ω層・τ層")
    lines.append(f"")
    for wf_id, label in sorted(PERAS_WORKFLOWS.items()):
        count = data["wf_counts"].get(wf_id, 0)
        if count > 0:
            lines.append(f"- /{wf_id} ({label}): {count}回")
    for wf_id, label in sorted(TAU_WORKFLOWS.items()):
        count = data["wf_counts"].get(wf_id, 0)
        if count > 0:
            lines.append(f"- /{wf_id} ({label}): {count}回")

    return "\n".join(lines)


# PURPOSE: [L2-auto] 関数: main
def main():
    parser = argparse.ArgumentParser(
        description="定理活性度レポート — Handoff からWF発動頻度を集計"
    )
    parser.add_argument("--days", type=int, default=None,
                        help="過去N日間に限定 (default: 全期間)")
    parser.add_argument("--json", action="store_true",
                        help="JSON 形式で出力")
    args = parser.parse_args()

    report = generate_report(days=args.days, as_json=args.json)
    print(report)


if __name__ == "__main__":
    main()
