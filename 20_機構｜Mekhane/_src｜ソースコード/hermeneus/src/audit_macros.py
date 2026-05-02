# PROOF: [L2/ツール] <- hermeneus/src/audit_macros.py CCL マクロ忘却スコア監査
"""
CCL マクロ忘却スコア バッチ監査ツール

.agents/workflows/ccl-*.md から CCL 式を抽出し、
明示座標スコア S_explicit と暗黙座標スコア S_implicit を一括計算する。

Usage:
    python -m hermeneus.src.audit_macros [--json] [--macros-dir PATH]

Origin: 2026-03-18 Creator × Claude — Theorema Egregium Cognitionis の実用化
"""

import json
import re
import signal
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .forgetfulness_score import (
    COORDINATES,
    VERB_IMPLICIT_COORDINATES,
    ImplicitScoreResult,
    score_ccl_implicit,
)


# =============================================================================
# 定数
# =============================================================================

# PURPOSE: デフォルトのマクロ定義ディレクトリ
DEFAULT_MACROS_DIR = Path(__file__).resolve().parents[4] / ".agents" / "workflows"

# PURPOSE: 6族の定義 (axiom_hierarchy.md §Poiesis 準拠)
SERIES_MAP: Dict[str, str] = {
    "Va": "Telos",
    "Fu": "Methodos",
    "Pr": "Krisis",
    "Sc": "Diástasis",
    "Vl": "Orexis",
    "Te": "Chronos",
}


# =============================================================================
# データ型
# =============================================================================

# PURPOSE: 個別マクロの監査結果
@dataclass
class MacroAuditResult:
    """個別マクロの監査結果"""
    name: str                    # マクロ名 (e.g., "@fix")
    ccl_expression: str          # CCL 式
    s_explicit: float            # 明示座標のみのスコア
    s_implicit: float            # 暗黙座標込みのスコア
    explicit_coords: List[str]   # 明示座標リスト
    implicit_coords: List[str]   # 暗黙座標リスト
    all_coords: List[str]        # 全座標リスト (明示 ∪ 暗黙)
    missing_coords: List[str]    # 暗黙込みでも欠落する座標
    verb_coverage: Dict[str, int]  # 各座標の動詞カバレッジ
    u_patterns: List[str]        # 欠落座標に対応する U パターン
    parse_error: Optional[str] = None  # パースエラー (あれば)


# PURPOSE: バッチ監査の集計結果
@dataclass
class AuditSummary:
    """バッチ監査の集計結果"""
    total_macros: int
    parsed_macros: int
    failed_macros: int
    avg_s_explicit: float
    avg_s_implicit: float
    series_coverage: Dict[str, float]  # 族名 → 全マクロでの出現率
    results: List[MacroAuditResult]


# =============================================================================
# CCL 式の抽出
# =============================================================================

# PURPOSE: description から CCL 式を抽出する (YAML frontmatter から)
def extract_ccl_from_file(filepath: Path) -> Optional[Tuple[str, str]]:
    """マクロ定義ファイルから名前と CCL 式を抽出する。

    Args:
        filepath: .md ファイルのパス

    Returns:
        (マクロ名, CCL 式) のタプル。CCL 式がなければ None
    """
    text = filepath.read_text(encoding="utf-8")

    # マクロ名: ファイル名から "ccl-" を除去し "@" を付与
    name = "@" + filepath.stem.replace("ccl-", "")

    # --- description フィールドから CCL 式を抽出 ---
    # パターン 1: description: に直接 CCL 式がある場合
    # 例: description: 直す — /ops+_/bou+_/tek+_C:{/ele+_/dio+}_/akr+_I:[✓]{/kat+}
    desc_match = re.search(
        r"^description:\s*(.+)$", text, re.MULTILINE
    )
    if not desc_match:
        return None

    desc = desc_match.group(1).strip()

    # PURPOSE: YAML クオートの残りを除去するユーティリティ
    def _clean_ccl(s: str) -> str:
        return s.strip().strip('"').strip("'").strip()

    # パターン A: "名前 — CCL式" の形式
    if "—" in desc:
        parts = desc.split("—", 1)
        if len(parts) == 2:
            ccl_part = _clean_ccl(parts[1])
            # CCL 式は / で始まるか、@ で始まるか、マクロ定義 (@name = ...) の形式
            if ccl_part.startswith("/") or ccl_part.startswith("@") or ccl_part.startswith("("):
                # @xxx = ... の形式なら = 以降を取得
                if "=" in ccl_part and ccl_part.startswith("@"):
                    ccl_part = _clean_ccl(ccl_part.split("=", 1)[1])
                return (name, ccl_part)

    # パターン B: description が直接 CCL 式
    if desc.startswith("/") or desc.startswith("("):
        return (name, _clean_ccl(desc))

    # パターン C: CCL 式が本文中に記載されている場合
    # ```ccl ブロックを探す
    ccl_block = re.search(r"```ccl\s*\n(.+?)\n```", text, re.DOTALL)
    if ccl_block:
        return (name, _clean_ccl(ccl_block.group(1)))

    return None


# =============================================================================
# バッチ監査
# =============================================================================

# PURPOSE: 全マクロをバッチで監査する
def audit_all_macros(
    macros_dir: Optional[Path] = None,
) -> AuditSummary:
    """全 CCL マクロの忘却スコアをバッチ計算する。

    Args:
        macros_dir: マクロ定義ディレクトリ (.agents/workflows/)

    Returns:
        AuditSummary: 集計結果
    """
    if macros_dir is None:
        macros_dir = DEFAULT_MACROS_DIR

    # CCL マクロファイルを収集
    macro_files = sorted(macros_dir.glob("ccl-*.md"))

    results: List[MacroAuditResult] = []
    parsed = 0
    failed = 0

    # PURPOSE: パーサーがハングした場合のタイムアウト機構
    PARSE_TIMEOUT = 5  # 秒

    class ParseTimeoutError(Exception):
        pass

    def _timeout_handler(signum, frame):
        raise ParseTimeoutError("パースタイムアウト (5秒超過)")

    for filepath in macro_files:
        extracted = extract_ccl_from_file(filepath)
        if extracted is None:
            continue

        name, ccl_expr = extracted

        try:
            # タイムアウト設定 (Unix のみ)
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(PARSE_TIMEOUT)
            try:
                result = score_ccl_implicit(ccl_expr)
            finally:
                signal.alarm(0)  # タイムアウト解除
                signal.signal(signal.SIGALRM, old_handler)

            parsed += 1

            # U パターン名を集める
            u_patterns = [
                d.u_pattern
                for d in result.explicit.diagnoses
                if d.coordinate in result.missing_implicit
            ]

            results.append(MacroAuditResult(
                name=name,
                ccl_expression=ccl_expr,
                s_explicit=result.explicit.score,
                s_implicit=result.s_implicit,
                explicit_coords=sorted(result.explicit.present_coordinates),
                implicit_coords=sorted(result.implicit_coordinates),
                all_coords=sorted(result.all_coordinates),
                missing_coords=sorted(result.missing_implicit),
                verb_coverage=result.verb_coverage,
                u_patterns=u_patterns,
            ))
        except Exception as e:  # noqa: BLE001
            failed += 1
            results.append(MacroAuditResult(
                name=name,
                ccl_expression=ccl_expr,
                s_explicit=-1.0,
                s_implicit=-1.0,
                explicit_coords=[],
                implicit_coords=[],
                all_coords=[],
                missing_coords=[],
                verb_coverage={},
                u_patterns=[],
                parse_error=str(e),
            ))

    # 族別カバレッジ統計
    series_coverage: Dict[str, float] = {}
    valid = [r for r in results if r.parse_error is None]
    for coord, series_name in SERIES_MAP.items():
        if valid:
            count = sum(1 for r in valid if coord in r.all_coords)
            series_coverage[series_name] = count / len(valid)
        else:
            series_coverage[series_name] = 0.0

    avg_explicit = sum(r.s_explicit for r in valid) / len(valid) if valid else 0.0
    avg_implicit = sum(r.s_implicit for r in valid) / len(valid) if valid else 0.0

    return AuditSummary(
        total_macros=len(macro_files),
        parsed_macros=parsed,
        failed_macros=failed,
        avg_s_explicit=avg_explicit,
        avg_s_implicit=avg_implicit,
        series_coverage=series_coverage,
        results=results,
    )


# =============================================================================
# レポート出力
# =============================================================================

# PURPOSE: 人間可読なテーブル形式でレポートを生成する
def format_report(summary: AuditSummary) -> str:
    """人間可読なテーブル形式でレポートを生成する"""
    lines = []
    lines.append("# CCL マクロ忘却スコア監査レポート")
    lines.append("")
    lines.append(f"## 概要")
    lines.append(f"- 総マクロ数: {summary.total_macros}")
    lines.append(f"- 正常パース: {summary.parsed_macros}")
    lines.append(f"- パース失敗: {summary.failed_macros}")
    lines.append(f"- 平均 S_explicit: {summary.avg_s_explicit:.3f}")
    lines.append(f"- 平均 S_implicit: {summary.avg_s_implicit:.3f}")
    lines.append("")

    # --- 族別カバレッジ ---
    lines.append("## 族別カバレッジ (暗黙座標込み)")
    lines.append("")
    lines.append("| 族 | 座標 | 出現率 |")
    lines.append("|:---|:-----|-------:|")
    for coord in sorted(SERIES_MAP.keys()):
        series_name = SERIES_MAP[coord]
        rate = summary.series_coverage.get(series_name, 0.0)
        bar = "█" * int(rate * 20) + "░" * (20 - int(rate * 20))
        lines.append(f"| {series_name} | {coord} | {rate:.0%} {bar} |")
    lines.append("")

    # --- 個別マクロ結果 ---
    lines.append("## 個別マクロ")
    lines.append("")
    lines.append("| マクロ | S_explicit | S_implicit | 明示座標 | 暗黙座標 | 欠落(暗黙込) | U パターン |")
    lines.append("|:-------|----------:|----------:|:---------|:---------|:------------|:-----------|")

    for r in sorted(summary.results, key=lambda x: x.s_implicit):
        if r.parse_error:
            lines.append(f"| {r.name} | ❌ | ❌ | | | | `{r.parse_error[:40]}` |")
            continue

        explicit = "{" + ",".join(r.explicit_coords) + "}" if r.explicit_coords else "∅"
        implicit = "{" + ",".join(r.implicit_coords) + "}" if r.implicit_coords else "∅"
        missing = "{" + ",".join(r.missing_coords) + "}" if r.missing_coords else "∅"
        u_pats = ", ".join(r.u_patterns) if r.u_patterns else "—"

        lines.append(
            f"| {r.name} | {r.s_explicit:.3f} | {r.s_implicit:.3f} "
            f"| {explicit} | {implicit} | {missing} | {u_pats} |"
        )

    lines.append("")

    # --- 座標カバレッジヒートマップ ---
    lines.append("## 座標カバレッジヒートマップ (動詞カバレッジ数)")
    lines.append("")
    header = "| マクロ | " + " | ".join(sorted(COORDINATES)) + " |"
    lines.append(header)
    lines.append("|:-------|" + "|".join(["---:" for _ in COORDINATES]) + "|")

    for r in sorted(summary.results, key=lambda x: x.name):
        if r.parse_error:
            continue
        cells = []
        for c in sorted(COORDINATES):
            count = r.verb_coverage.get(c, 0)
            if count == 0:
                cells.append(" · ")
            elif count <= 2:
                cells.append(f" {count} ")
            else:
                cells.append(f"**{count}**")
        lines.append(f"| {r.name} | " + " | ".join(cells) + " |")

    lines.append("")
    return "\n".join(lines)


# =============================================================================
# Q15 脆弱性対策: 補完提案機能
# =============================================================================

# PURPOSE: Q-series の15循環対の定義 (K₆ の辺)
Q_SERIES_PAIRS: List[Tuple[str, str, str]] = [
    # (循環名, 座標1, 座標2) — K₆ 完全グラフの全15辺
    ("Q1",  "Va", "Fu"),
    ("Q2",  "Va", "Fu"),  # Q1/Q2 は同一ペア (方向が異なる)
    ("Q3",  "Va", "Pr"),
    ("Q4",  "Fu", "Pr"),
    ("Q5",  "Va", "Sc"),
    ("Q6",  "Fu", "Sc"),
    ("Q7",  "Va", "Vl"),
    ("Q8",  "Fu", "Vl"),
    ("Q9",  "Te", "Fu"),
    ("Q10", "Va", "Te"),
    ("Q11", "Pr", "Sc"),
    ("Q12", "Pr", "Vl"),
    ("Q13", "Pr", "Te"),
    ("Q14", "Sc", "Vl"),
    ("Q15", "Sc", "Te"),
]


# PURPOSE: マクロの欠落座標を補完する相手マクロを提案する
@dataclass
class ComplementSuggestion:
    """補完候補の提案"""
    target_macro: str          # 補完相手のマクロ名
    fills: List[str]           # 補完される座標リスト
    remaining: List[str]       # 補完後も残る欠落座標
    combined_score: float      # 結合後の S(e)
    heals_q15: bool            # Q15 (Sc-Te) を修復するか


def suggest_complements(
    macro_name: str,
    summary: AuditSummary,
    top_k: int = 5,
) -> List[ComplementSuggestion]:
    """指定マクロの欠落座標を補完する相手マクロを提案する。

    Args:
        macro_name: 対象マクロ名 (e.g., "@build")
        summary: audit_all_macros() の結果
        top_k: 返す候補数

    Returns:
        ComplementSuggestion のリスト (combined_score 昇順)
    """
    # 対象マクロを検索
    target = None
    for r in summary.results:
        if r.name == macro_name and r.parse_error is None:
            target = r
            break
    if target is None:
        return []

    target_missing = set(target.missing_coords)
    if not target_missing:
        return []  # 欠落なし

    suggestions = []
    for r in summary.results:
        if r.name == macro_name or r.parse_error is not None:
            continue

        partner_coords = set(r.all_coords)
        fills = sorted(target_missing & partner_coords)
        if not fills:
            continue  # この相手では何も補完されない

        remaining = sorted(target_missing - partner_coords)
        combined_score = len(remaining) / len(COORDINATES)

        # Q15 修復判定: Sc と Te の両方が欠落 → 補完後に少なくとも一方がカバー
        heals_q15 = (
            {"Sc", "Te"}.issubset(target_missing) and
            bool({"Sc", "Te"} & partner_coords)
        )

        suggestions.append(ComplementSuggestion(
            target_macro=r.name,
            fills=fills,
            remaining=remaining,
            combined_score=combined_score,
            heals_q15=heals_q15,
        ))

    # ソート: Q15修復優先 → combined_score 昇順 → 補完数降順
    suggestions.sort(key=lambda s: (not s.heals_q15, s.combined_score, -len(s.fills)))
    return suggestions[:top_k]


# PURPOSE: Q15 断絶マクロ一覧と補完提案をレポートに追加する
def format_complement_report(summary: AuditSummary, top_k: int = 3) -> str:
    """Q15 脆弱性対策セクションを含むレポートを生成する。"""
    lines = []
    lines.append("## 🔧 Q15 脆弱性対策 — 補完提案")
    lines.append("")
    lines.append("> Q15 (Sc-Te) 循環 = Scale × Temporality の同時欠落。")
    lines.append("> 最も脆弱な循環 (10マクロで断絶)。")
    lines.append("")

    # Q15 断絶マクロを特定
    q15_broken = []
    for r in summary.results:
        if r.parse_error is not None:
            continue
        missing = set(r.missing_coords)
        if "Sc" in missing and "Te" in missing:
            q15_broken.append(r)

    if not q15_broken:
        lines.append("✅ **Q15 断絶マクロなし** — 全マクロが Sc または Te をカバー")
        return "\n".join(lines)

    lines.append(f"⚠️ **{len(q15_broken)} マクロが Q15 循環を断絶**")
    lines.append("")
    lines.append("| マクロ | 欠落座標 | 補完候補 TOP 3 |")
    lines.append("|:-------|:---------|:---------------|")

    for r in sorted(q15_broken, key=lambda x: x.name):
        missing = "{" + ",".join(r.missing_coords) + "}"
        suggestions = suggest_complements(r.name, summary, top_k=top_k)

        if suggestions:
            # 各候補を表示
            complements = []
            for s in suggestions:
                fills_str = "+".join(s.fills)
                q15_badge = " 🩹" if s.heals_q15 else ""
                complements.append(f"`{s.target_macro}` ({fills_str}, S→{s.combined_score:.2f}{q15_badge})")
            comp_str = " / ".join(complements)
        else:
            comp_str = "—"

        lines.append(f"| {r.name} | {missing} | {comp_str} |")

    lines.append("")

    # 完全補完ペア (S→0) を追加表示
    lines.append("### 完全補完ペア (結合で S=0)")
    lines.append("")
    perfect_pairs = set()
    for r in summary.results:
        if r.parse_error is not None or not r.missing_coords:
            continue
        suggestions = suggest_complements(r.name, summary, top_k=50)
        for s in suggestions:
            if s.combined_score == 0.0:
                pair = tuple(sorted([r.name, s.target_macro]))
                perfect_pairs.add(pair)

    if perfect_pairs:
        for a, b in sorted(perfect_pairs):
            lines.append(f"- `{a}` + `{b}`")
    else:
        lines.append("— 完全補完ペアなし")

    lines.append("")
    return "\n".join(lines)


# =============================================================================
# メイン
# =============================================================================

def main():
    """コマンドラインから実行する"""
    output_json = "--json" in sys.argv
    complement_mode = "--complement" in sys.argv

    # マクロディレクトリの指定
    macros_dir = None
    for i, arg in enumerate(sys.argv):
        if arg == "--macros-dir" and i + 1 < len(sys.argv):
            macros_dir = Path(sys.argv[i + 1])

    summary = audit_all_macros(macros_dir)

    if output_json:
        # JSON 出力 (MCP 連携用)
        data = {
            "total_macros": summary.total_macros,
            "parsed_macros": summary.parsed_macros,
            "failed_macros": summary.failed_macros,
            "avg_s_explicit": summary.avg_s_explicit,
            "avg_s_implicit": summary.avg_s_implicit,
            "series_coverage": summary.series_coverage,
            "results": [
                {
                    "name": r.name,
                    "ccl_expression": r.ccl_expression,
                    "s_explicit": r.s_explicit,
                    "s_implicit": r.s_implicit,
                    "explicit_coords": r.explicit_coords,
                    "implicit_coords": r.implicit_coords,
                    "all_coords": r.all_coords,
                    "missing_coords": r.missing_coords,
                    "verb_coverage": r.verb_coverage,
                    "u_patterns": r.u_patterns,
                    "parse_error": r.parse_error,
                }
                for r in summary.results
            ],
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif complement_mode:
        # Q15 補完レポート出力
        print(format_complement_report(summary))
    else:
        # Markdown レポート出力
        print(format_report(summary))


if __name__ == "__main__":
    main()
