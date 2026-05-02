from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/fep/ A0→Adjunction型の消費者が必要→adjunction_builderが担う
"""
Adjunction Builder — /boot ⊣ /bye の随伴構造を Adjunction 型で構築する

Origin: /zet+ Q1, Q4 (2026-02-08)
Problem: Adjunction は Layer C (Operational) だが消費者コードがゼロだった。
         boot_integration.py の ε 計算は float 直書きで、Adjunction 型を使っていない。
         これは Q16 の分類で「乖離＝バグ」に該当する。

Solution: boot/bye の実績から Adjunction 型を構築する最初の消費者コード。

Design (Cone Builder との対称性):
    cone_builder:  WF outputs → Cone (C0-C3)
    adjunction_builder:  boot report + handoff → Adjunction (η, ε, drift)

    Cone は「4つの定理出力を統合する」
    Adjunction は「2つのセッション境界を接続する」

DAPL Note:
    η/ε の計算には dirty adapter (PenaltyMultiplier) を内部で使用。
    Adjunction 型はその出力を包む clean interface。

Usage:
    from mekhane.fep.adjunction_builder import build_adjunction, describe_adjunction
    adj = build_adjunction(boot_report="...", handoff="...")
    print(describe_adjunction(adj))
"""


import re
from typing import Dict, Optional

from mekhane.fep.category import Adjunction


# =============================================================================
# η (unit) computation: boot preservation quality
# =============================================================================


# PURPOSE: boot レポートから η (preservation rate) を計算
def compute_eta(boot_report: str, handoff: Optional[str] = None) -> float:
    """Compute η: how well /boot preserved the previous session's context.

    η = Id_Mem → R∘L — boot が前回 handoff をどれだけ再現したか。

    Measurement:
        1. Handoff のキーポイントが boot レポートに反映されているか
        2. boot レポートの構造的完全性 (セクション充足率)
        3. 引き継ぎ事項の消化率

    Returns:
        η quality score (0.0-1.0). 1.0 = perfect preservation.
    """
    if not boot_report:
        return 0.0

    score = 0.0
    checks = 0

    # Check 1: boot レポートの長さ (最低限のコンテンツ)
    checks += 1
    if len(boot_report) > 500:
        score += 1.0
    elif len(boot_report) > 200:
        score += 0.5

    # Check 2: 構造的セクション (Handoff, Sophia, Safety, etc.)
    structural_markers = [
        r"handoff|引き継ぎ",
        r"sophia|知識|KI",
        r"safety|安全",
        r"attractor|定理",
        r"persona|ペルソナ",
    ]
    checks += len(structural_markers)
    for marker in structural_markers:
        if re.search(marker, boot_report, re.IGNORECASE):
            score += 1.0

    # Check 3: handoff キーポイントの反映 (handoff がある場合)
    if handoff:
        # handoff から主要キーワードを抽出
        handoff_keywords = _extract_keywords(handoff)
        if handoff_keywords:
            checks += 1
            reflected = sum(
                1 for kw in handoff_keywords
                if kw.lower() in boot_report.lower()
            )
            score += reflected / len(handoff_keywords)

    return min(score / max(checks, 1), 1.0)


# PURPOSE: handoff からキーワードを抽出
def _extract_keywords(handoff: str) -> list[str]:
    """Extract key terms from handoff for preservation checking."""
    # YAML frontmatter 後のマークダウンからヘッダーを抽出
    headers = re.findall(r'^#{1,3}\s+(.+)$', handoff, re.MULTILINE)
    # 太字テキストも抽出
    bold = re.findall(r'\*\*(.+?)\*\*', handoff)
    # 重複除去
    keywords = list(dict.fromkeys(headers + bold))
    return keywords[:20]  # 最大20個


# =============================================================================
# ε (counit) computation: bye restoration precision
# =============================================================================


# PURPOSE: boot レポートから ε (restoration rate) を計算
def compute_epsilon(boot_report: str) -> float:
    """Compute ε: how precisely /bye→/boot can restore session state.

    ε = L∘R → Id_Ses — bye で圧縮したものを boot で復元したとき、
    元のセッション状態にどれだけ近いか。

    Measurement:
        1. boot レポート内の具体的な数値/メトリクスの有無
        2. FILL マーカーの残存 (未記入 = 復元不完全)
        3. Adjunction メトリクス (ε, drift) の自己報告値

    DAPL: PenaltyMultiplier パターンを内部使用 (FILL ペナルティ)
    """
    if not boot_report:
        return 0.0

    score = 0.0
    checks = 0

    # Check 1: 数値メトリクスの存在
    checks += 1
    metrics_patterns = [
        r"ε\s*[=:]\s*[\d.]+",          # ε = 0.85
        r"drift\s*[=:]\s*[\d.]+",      # drift = 0.15
        r"η\s*[=:]\s*[\d.]+",          # η = 0.90
        r"V\[.*?\]\s*[=:]\s*[\d.]+",   # V[outputs] = 0.3
        r"confidence\s*[=:]\s*[\d.]+",  # confidence = 85
    ]
    metric_count = sum(
        1 for p in metrics_patterns
        if re.search(p, boot_report, re.IGNORECASE)
    )
    score += min(metric_count / 3, 1.0)  # 3つ以上あれば満点

    # Check 2: FILL ペナルティ (DAPL: PenaltyMultiplier)
    checks += 1
    fill_remaining = boot_report.count("<!-- FILL -->")
    if fill_remaining == 0:
        score += 1.0
    else:
        estimated_total = max(fill_remaining, 25)
        fill_ratio = 1.0 - (fill_remaining / estimated_total)
        score += max(fill_ratio, 0.0)

    # Check 3: セッション固有情報の存在 (日付, コミットハッシュ等)
    checks += 1
    specific_patterns = [
        r"\d{4}-\d{2}-\d{2}",          # 日付
        r"[0-9a-f]{7,40}",             # git hash
        r"commit|コミット",             # commit 言及
    ]
    specific_count = sum(
        1 for p in specific_patterns
        if re.search(p, boot_report, re.IGNORECASE)
    )
    score += min(specific_count / 2, 1.0)

    return min(score / max(checks, 1), 1.0)


# =============================================================================
# Builder (Cone Builder と対称)
# =============================================================================


# PURPOSE: boot/bye の実績から Adjunction を構築
def build_adjunction(
    boot_report: str,
    handoff: Optional[str] = None,
    left_name: str = "boot",
    right_name: str = "bye",
) -> Adjunction:
    """Build an Adjunction from boot/bye artifacts.

    Design symmetry with cone_builder:
        cone_builder.converge(outputs) → Cone
        adjunction_builder.build_adjunction(boot_report) → Adjunction

    Args:
        boot_report: The formatted boot output
        handoff: Previous session's handoff (if available)
        left_name: Left adjoint name (default: "boot")
        right_name: Right adjoint name (default: "bye")

    Returns:
        Adjunction with computed η and ε
    """
    eta = compute_eta(boot_report, handoff)
    epsilon = compute_epsilon(boot_report)

    return Adjunction(
        left_name=left_name,
        right_name=right_name,
        source_category="Mem",
        target_category="Ses",
        eta_quality=eta,
        epsilon_precision=epsilon,
    )


# =============================================================================
# Display (Cone の describe_cone と対称)
# =============================================================================


# PURPOSE: Adjunction の状態を表示
def describe_adjunction(adj: Adjunction) -> str:
    """Human-readable description of an Adjunction.

    Symmetric with cone_builder.describe_cone().
    """
    lines = [
        f"⊣ Adjunction: {adj.left_name} ⊣ {adj.right_name}",
        f"  {adj.source_category} ⇄ {adj.target_category}",
        f"  η (preservation): {adj.eta_quality:.1%}",
        f"  ε (restoration):  {adj.epsilon_precision:.1%}",
        f"  drift:            {adj.drift:.1%}",
    ]

    # Faithfulness check
    if adj.is_faithful:
        lines.append("  ✅ R is faithful (η > 80%)")
    else:
        lines.append("  ⚠️ R is not faithful (η ≤ 80%)")

    # Drift warning
    if adj.drift > 0.3:
        lines.append(f"  🔴 High drift! {adj.drift:.0%} of context lost in cycle")
    elif adj.drift > 0.15:
        lines.append(f"  🟡 Moderate drift: {adj.drift:.0%} context loss")
    else:
        lines.append(f"  🟢 Low drift: {adj.drift:.0%} — good preservation")

    return "\n".join(lines)


# =============================================================================
# Integration point for boot_integration.py
# =============================================================================


# PURPOSE: boot_integration から呼ばれる統合 API
def adjunction_from_boot(
    boot_formatted: str,
    handoff_path: Optional[str] = None,
) -> Dict:
    """Integration API for boot_integration.py.

    Returns a dict suitable for inclusion in boot context.
    """
    handoff = None
    if handoff_path:
        from pathlib import Path
        p = Path(handoff_path)
        if p.exists():
            handoff = p.read_text(encoding="utf-8")

    adj = build_adjunction(boot_formatted, handoff)

    return {
        "adjunction": adj,
        "eta": adj.eta_quality,
        "epsilon": adj.epsilon_precision,
        "drift": adj.drift,
        "is_faithful": adj.is_faithful,
        "formatted": describe_adjunction(adj),
    }


if __name__ == "__main__":
    # Demo with a synthetic boot report
    demo_report = """
    📋 Handoff loaded: handoff_2026-02-08_1332.md
    🔬 Sophia KI: 5 items loaded
    🛡️ Safety: OK
    🎯 Attractor: O1(0.85), S2(0.72), K4(0.68)
    👤 Persona: standard
    ε = 0.82, drift = 0.18
    Date: 2026-02-08
    Commit: abc1234
    """

    adj = build_adjunction(demo_report)
    print(describe_adjunction(adj))
