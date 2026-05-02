from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/taxis/morphism_proposer.py A0→X-series射提案が必要→morphism_proposerが担う
"""
morphism_proposer.py — X-series 射提案エンジン

PURPOSE: WF完了時に trigonon frontmatter を読み、
         射の提案ツリーを自動生成する。
         N-8 の計算的強制レイヤー。

Usage:
    python mekhane/taxis/morphism_proposer.py noe
    python mekhane/taxis/morphism_proposer.py met --confidence=low
"""


import argparse
import sys
from pathlib import Path
from typing import Optional


# PURPOSE: WF名からシリーズ名へのマッピング (v4.1 新体系)
SERIES_NAMES = {
    "Tel": "Telos (目的)",
    "Met": "Methodos (方法)",
    "Kri": "Krisis (確信)",
    "Dia": "Diástasis (空間)",
    "Ore": "Orexis (傾向)",
    "Chr": "Chronos (時間)",
}

# PURPOSE: 旧略称 → 新略称の後方互換マッピング (移行期間用)
LEGACY_SERIES_MAP = {
    "O": "Tel",
    "S": "Met",
    "H": "Kri",  # 旧 Hormē → Krisis (Precision 軸に再配置)
    "P": "Dia",  # 旧 Perigraphē → Diástasis (Scale 軸)
    "K": "Chr",  # 旧 Kairos → Chronos (Temporality 軸)
    "A": "Ore",  # 旧 Akribeia → Orexis (Valence 軸)
}


# PURPOSE: WF 略称 (36動詞) → Series コードのマッピング
# 6族 × 6動詞 = 36。dispatch.py / tape_parser_poc.py と共有。
WF_TO_SERIES = {
    # Tel (目的) = Flow × Value
    "noe": "Tel", "bou": "Tel", "zet": "Tel", "ene": "Tel", "the": "Tel", "ant": "Tel",
    # Met (方法) = Flow × Function
    "ske": "Met", "sag": "Met", "pei": "Met", "tek": "Met", "ere": "Met", "agn": "Met",
    # Kri (判断) = Flow × Precision
    "kat": "Kri", "epo": "Kri", "pai": "Kri", "dok": "Kri", "sap": "Kri", "ski": "Kri",
    # Dia (拡張) = Flow × Scale
    "lys": "Dia", "ops": "Dia", "akr": "Dia", "arc": "Dia", "prs": "Dia", "per": "Dia",
    # Ore (欲求) = Flow × Valence
    "beb": "Ore", "ele": "Ore", "kop": "Ore", "dio": "Ore", "apo": "Ore", "exe": "Ore",
    # Chr (時間) = Flow × Temporality
    "hyp": "Chr", "prm": "Chr", "ath": "Chr", "par": "Chr", "his": "Chr", "prg": "Chr",
}

# PURPOSE: 各 Series の代表 WF (I-verb = 推論の頂点)
_SERIES_LEAD_WF = {
    "Tel": "/noe",   # Noēsis — 認識
    "Met": "/ske",   # Skepsis — 発散
    "Kri": "/kat",   # Katalēpsis — 確定
    "Dia": "/lys",   # Analysis — 詳細分析
    "Ore": "/ele",   # Elenchos — 批判
    "Chr": "/hyp",   # Hypomnēsis — 想起
}


def suggest_from_xseries(
    wf_names: list[str],
    *,
    max_complement: int = 3,
    max_tension: int = 2,
) -> Optional[str]:
    """X-series K₆ エッジから次の WF 候補を提案する。

    trigonon frontmatter がない WF に対するフォールバック提案エンジン。
    complement (協調的) エッジを優先し、tension (対立的) エッジを検証用に提示する。

    Args:
        wf_names: WF 略称のリスト (例: ["noe", "ele"])
        max_complement: complement 候補の最大数
        max_tension: tension 候補の最大数

    Returns:
        提案テキスト。候補がない場合は None。
    """
    # ax_pipeline.py の X_SERIES_EDGES を遅延 import (循環 import 回避)
    try:
        from hermeneus.src.ax_pipeline import X_SERIES_EDGES
    except ImportError:
        # hermeneus が import できない場合のフォールバック
        X_SERIES_EDGES = []

    # 参加している Series を特定
    series_set = set()
    for wf in wf_names:
        clean = wf.lstrip("/").rstrip("+-")
        s = WF_TO_SERIES.get(clean)
        if s:
            series_set.add(s)

    if not series_set:
        return None

    complement_targets = []
    tension_targets = []

    for edge_def in X_SERIES_EDGES:
        edge = edge_def["edge"]
        ttype = edge_def["type"]
        hint = edge_def["hint"]
        a, b = edge

        other = None
        if a in series_set and b not in series_set:
            other = b
        elif b in series_set and a not in series_set:
            other = a

        if other:
            lead = _SERIES_LEAD_WF.get(other, f"/{other.lower()}")
            _, series_name = _resolve_series(other)
            entry = f"{lead} ({series_name}): {hint}"
            if ttype == "complement":
                complement_targets.append(entry)
            else:
                tension_targets.append(entry)

    if not complement_targets and not tension_targets:
        return None

    lines = ["🧭 【→次 WF 候補】(θ7.3 X-series フォールバック提案)"]
    if complement_targets:
        lines.append("  協調的 (complement):")
        lines.extend(f"    {t}" for t in complement_targets[:max_complement])
    if tension_targets:
        lines.append("  検証的 (tension):")
        lines.extend(f"    {t}" for t in tension_targets[:max_tension])
    lines.append(
        "  → なぜ: WF 間の X-series 関係から自動生成。"
        "確信ありなら Anchor (同系)、なければ Bridge (異系) を選べ。"
    )
    return "\n".join(lines)


def _resolve_series(code: str) -> tuple[str, str]:
    """略称を解決し (正規化コード, 表示名) を返す。旧略称は警告付きで変換。"""
    if code in SERIES_NAMES:
        return code, SERIES_NAMES[code]
    if code in LEGACY_SERIES_MAP:
        new_code = LEGACY_SERIES_MAP[code]
        import sys
        print(f"WARNING: 旧略称 '{code}' を検出。新略称 '{new_code}' に変換します。",
              file=sys.stderr)
        return new_code, SERIES_NAMES[new_code]
    return code, code


# PURPOSE: trigonon frontmatter をパースして射の提案を生成する
def parse_trigonon(wf_path: Path) -> Optional[dict]:
    """WF ファイルから trigonon セクションを抽出する"""
    try:
        content = wf_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None

    # YAML frontmatter を簡易パース (yaml ライブラリなしで動作)
    if not content.startswith("---"):
        return None

    end = content.index("---", 3)
    frontmatter = content[3:end]

    result = {}
    in_trigonon = False
    in_morphisms = False

    for line in frontmatter.split("\n"):
        stripped = line.strip()
        # YAML コメントを除去
        if "#" in stripped and not stripped.startswith('"'):
            stripped = stripped[: stripped.index("#")].strip()

        if stripped == "trigonon:":
            in_trigonon = True
            continue

        if in_trigonon:
            if stripped.startswith("series:"):
                result["series"] = stripped.split(":")[1].strip()
            elif stripped.startswith("type:"):
                result["type"] = stripped.split(":")[1].strip()
            elif stripped.startswith("theorem:"):
                result["theorem"] = stripped.split(":")[1].strip()
            elif stripped.startswith("bridge:"):
                val = stripped.split(":")[1].strip()
                result["bridge"] = [
                    s.strip() for s in val.strip("[]").split(",") if s.strip()
                ]
            elif stripped.startswith("anchor_via:"):
                val = stripped.split(":")[1].strip()
                result["anchor_via"] = [
                    s.strip() for s in val.strip("[]").split(",") if s.strip()
                ]
            elif stripped == "morphisms:":
                in_morphisms = True
                result["morphisms"] = {}
            elif in_morphisms and stripped.startswith('">>'):
                key, val = stripped.split(":", 1)
                key = key.strip().strip('"')
                wfs = [
                    w.strip() for w in val.strip().strip("[]").split(",") if w.strip()
                ]
                result["morphisms"][key] = wfs
            elif not stripped.startswith('">>') and ":" not in stripped and stripped:
                in_trigonon = False
                in_morphisms = False

    return result if result else None


# PURPOSE: 射の提案ツリーをフォーマットして出力する
def format_proposal(
    wf_name: str,
    trigonon: dict,
    confidence: Optional[str] = None,
) -> str:
    """射の提案ツリーを生成する"""
    series = trigonon.get("series", "?")
    theorem = trigonon.get("theorem", "?")
    stype = trigonon.get("type", "?")
    bridges = trigonon.get("bridge", [])
    anchors = trigonon.get("anchor_via", [])
    morphisms = trigonon.get("morphisms", {})

    # 確信度ラベル
    if confidence == "high":
        mode = "⚓ 収束モード: Anchor 優先"
    elif confidence == "low":
        mode = "🔍 探索モード: Bridge 優先"
    else:
        mode = "⚖️ 均衡モード"

    lines = [
        f"🔀 射の提案 (trigonon: {series}/{theorem}/{stype})",
        mode,
    ]

    # Bridge 射
    for b in bridges:
        key = f">>{b}"
        wfs = morphisms.get(key, [])
        wf_str = " ".join(wfs) if wfs else f"/{b.lower()} 系全般"
        resolved_code, series_name = _resolve_series(b)
        lines.append(f"├─ Bridge >> {resolved_code}: {wf_str}  ({series_name})")

    # Anchor 射
    for a in anchors:
        resolved_code, series_name = _resolve_series(a)
        lines.append(f"├─ Anchor >> {resolved_code}: via 中継  ({series_name})")

    lines.append("└─ (完了)")
    lines.append("")
    lines.append("→ 結果に確信がありますか？ (Y: Anchor優先 / N: Bridge優先 / 完了)")

    return "\n".join(lines)


# PURPOSE: CLI エントリーポイント
def main() -> None:
    parser = argparse.ArgumentParser(
        description="X-series 射提案エンジン (θ8.1)",
    )
    parser.add_argument("wf", help="WF名 (例: noe, met, dia)")
    parser.add_argument(
        "--confidence",
        choices=["high", "low", "neutral"],
        default=None,
        help="確信度 (high=Anchor優先, low=Bridge優先)",
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent
        / "nous"
        / "workflows",
        help="ワークフローディレクトリ",
    )

    args = parser.parse_args()

    wf_path = args.workflows_dir / f"{args.wf}.md"
    trigonon = parse_trigonon(wf_path)

    if trigonon is None:
        # フォールバックチェーン: krisis_adjunction → X-series → ERROR

        # 1. Krisis WF のフォールバック: trigonon がなくても随伴提案を生成
        try:
            from mekhane.fep.krisis_adjunction_builder import propose_dual_wf
            krisis_proposal = propose_dual_wf(args.wf)
            if krisis_proposal:
                print(krisis_proposal)
                sys.exit(0)
        except ImportError:
            pass

        # 2. X-series フォールバック: K₆ エッジから次 WF 候補を生成
        xseries_suggestion = suggest_from_xseries([args.wf])
        if xseries_suggestion:
            print(xseries_suggestion)
            sys.exit(0)

        print(f"ERROR: {wf_path} に trigonon frontmatter が見つかりません",
              file=sys.stderr)
        sys.exit(1)

    proposal = format_proposal(args.wf, trigonon, args.confidence)
    print(proposal)


if __name__ == "__main__":
    main()
