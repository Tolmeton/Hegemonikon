from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/fep/ A-series深層吸収→Krisis族随伴の実装が必要→krisis_adjunction_builderが担う
"""
Krisis Adjunction Builder — Krisis族の Precision 軸随伴を構築する

Problem: KRISIS_ADJUNCTIONS は静的定義 (η=0, ε=0)。
         WF 実行結果から η/ε を計算し、ランタイムで随伴を構築する必要がある。

Solution: adjunction_builder.py (/boot⊣/bye) と対称的に設計。
          WF 出力の品質スコア (QS) に基づいて η/ε を計算する。

Architecture:
    adjunction_builder:  boot report + handoff → Adjunction (η, ε, drift)
    krisis_adjunction_builder: WF output + QS → Adjunction (η, ε, drift)

Krisis族の二重随伴:
    K⊣E: Katalēpsis ⊣ Epochē    (確定 ⊣ 保留, 推論軸)
    P⊣D: Proairesis ⊣ Dokimasia  (決断 ⊣ 打診, 行為軸)

Usage:
    from mekhane.fep.krisis_adjunction_builder import (
        build_krisis_adjunction,
        describe_krisis_pair,
        get_adjunction_for_wf,
    )
    adj = build_krisis_adjunction("K⊣E", kat_output="...", epo_output="...")
    print(describe_krisis_pair("K⊣E"))
"""


import re
from typing import Dict, Optional

from mekhane.fep.category import (
    Adjunction,
    KRISIS_ADJUNCTIONS,
    KRISIS_WF_TO_ADJUNCTION,
)


# =============================================================================
# Pair metadata (enriched descriptions for each adjunction)
# =============================================================================

# PURPOSE: Human-readable metadata for each Krisis adjunction pair
KRISIS_PAIR_METADATA: Dict[str, Dict[str, str]] = {
    "K⊣E": {
        "name": "Katalēpsis ⊣ Epochē",
        "axis": "推論 (Inference)",
        "left_description": "K: Evidence → Commitment. argmax Q(H) — 確信の1点集中",
        "right_description": "E: Hypotheses → Suspension. Q(H) 全体保持 — argmax 拒否",
        "eta_meaning": "確定→保留→元の根拠？ 確信が可逆であれば η は高い",
        "epsilon_meaning": "保留→確定 → 妥当か？ ε 崩壊 = 早すぎるコミット",
        "drift_meaning": "確定すべき時に保留 or 保留すべき時に確定するギャップ",
        "fep": "π集中 (K) ⊣ π分散 (E)",
        "algebra": "K = C_fix × E_evidence  |  E = O_open × T_tolerance",
    },
    "P⊣D": {
        "name": "Proairesis ⊣ Dokimasia",
        "axis": "行為 (Activity)",
        "left_description": "P: Confidence → ResourceAllocation. 確信に基づく全力投入",
        "right_description": "D: Uncertainty → MinimalAction. 最小行動でEIG最大化",
        "eta_meaning": "不確実性→打診→投入 → 解消？ 打診が有効な情報を提供すれば η は高い",
        "epsilon_meaning": "投入→打診に縮退 → 妥当か？ ε 崩壊 = 過剰投入の後悔",
        "drift_meaning": "打診で十分なのに全力投入 or 全力投入すべきなのに打診するギャップ",
        "fep": "Pragmatic Value (P) ⊣ Epistemic Value (D)",
        "algebra": "P = R_invest × C_confidence  |  D = A_min × I_gained",
    },
}


# =============================================================================
# WF-Specific Rubric Extractors — η/ε の実質的な計算
# =============================================================================


# PURPOSE: 汎用 - CHECKPOINT の通過数から基礎点を計算
def _checkpoint_score(wf_output: str, max_phases: int) -> float:
    """CHECKPOINT PHASE X/N markers count → normalized score."""
    count = len(re.findall(r"CHECKPOINT PHASE \d+", wf_output))
    if max_phases <= 0:
        return 0.0
    return min(count / max_phases, 1.0)


# PURPOSE: 汎用 - 確信度パーセンテージを抽出
def _extract_confidence_pct(wf_output: str) -> Optional[float]:
    """Extract confidence percentage from output text.

    Looks for patterns like:
      - [確信] 85%
      - [推定] 70%
      - 確信度: 90%
      - {X}%
    Returns float 0-1, or None if not found.
    """
    # [確信/推定/仮説] X%
    m = re.search(r"\[(?:確信|推定|仮説)\]\s*(\d+)%", wf_output)
    if m:
        return int(m.group(1)) / 100.0
    # 確信度: X% or 確信度: {X}%
    m = re.search(r"確信度[:\s]*(?:\{?)?(\d+)(?:\}?)?%", wf_output)
    if m:
        return int(m.group(1)) / 100.0
    # 📌 判定: [確信/推定/仮説] X%
    m = re.search(r"判定.*?(\d+)%", wf_output)
    if m:
        return int(m.group(1)) / 100.0
    return None


# ---- /kat (Katalēpsis) ルーブリック ----

# PURPOSE: /kat の η (忠実度) を WF 出力から計算
def _compute_eta_kat(wf_output: str) -> float:
    """Compute η for /kat (Katalēpsis) from output rubric.

    Components:
    - Checkpoint passage (max 0.3)
    - Evidence quality: SOURCE/(SOURCE+TAINT) ratio (max 0.3)
    - Falsification quality: HIGH/MED/LOW (max 0.4)
    """
    eta = 0.0
    # 1. Checkpoint passage (4 phases)
    eta += _checkpoint_score(wf_output, 4) * 0.3

    # 2. Evidence quality: SOURCE/(SOURCE+TAINT) ratio
    source_count = len(re.findall(r"SOURCE", wf_output))
    taint_count = len(re.findall(r"TAINT", wf_output))
    total_refs = source_count + taint_count
    if total_refs > 0:
        eta += (source_count / total_refs) * 0.3

    # 3. Falsification quality
    m = re.search(r"反証試行の品質[:\s]*\[?(HIGH|MED|LOW)\]?", wf_output, re.IGNORECASE)
    if m:
        grade = m.group(1).upper()
        eta += {"HIGH": 0.4, "MED": 0.2, "LOW": 0.0}.get(grade, 0.0)
    else:
        # Fallback: presence of 反証 section
        if "反証" in wf_output or "falsif" in wf_output.lower():
            eta += 0.15

    return min(eta, 1.0)


# PURPOSE: /kat の ε (精度) を WF 出力から計算
def _compute_epsilon_kat(wf_output: str) -> float:
    """Compute ε for /kat: extracts actual confidence percentage."""
    pct = _extract_confidence_pct(wf_output)
    if pct is not None:
        return min(max(pct, 0.0), 1.0)
    # Fallback: N-10 label presence
    if "[確信]" in wf_output:
        return 0.85
    if "[推定]" in wf_output:
        return 0.65
    if "[仮説]" in wf_output:
        return 0.35
    return 0.0


# ---- /epo (Epochē) ルーブリック ----

# PURPOSE: /epo の η (忠実度) を WF 出力から計算
def _compute_eta_epo(wf_output: str) -> float:
    """Compute η for /epo (Epochē) from output rubric.

    Components:
    - Checkpoint passage (max 0.3)
    - Revisit protocol: trigger + timebox present (max 0.3)
    - Anti-procrastination: score N/5 → (5-N)/5 * 0.4 (max 0.4)
    """
    eta = 0.0
    # 1. Checkpoint passage (4 phases, phase 4 is + only)
    eta += _checkpoint_score(wf_output, 4) * 0.3

    # 2. Revisit protocol
    has_trigger = bool(re.search(r"トリガー条件", wf_output))
    has_timebox = bool(re.search(r"タイムボックス", wf_output))
    revisit_score = (0.15 if has_trigger else 0) + (0.15 if has_timebox else 0)
    eta += revisit_score

    # 3. Anti-procrastination score
    m = re.search(r"先延ばしスコア[:\s]*(\d+)/5", wf_output)
    if m:
        procrastination = int(m.group(1))
        eta += ((5 - procrastination) / 5) * 0.4
    else:
        # Fallback: if 先延ばし section exists at all, give partial credit
        if "先延ばし" in wf_output:
            eta += 0.2

    return min(eta, 1.0)


# PURPOSE: /epo の ε (精度) を WF 出力から計算
def _compute_epsilon_epo(wf_output: str) -> float:
    """Compute ε for /epo: max hypothesis probability in the tableau.

    Lower ε = more evenly distributed = proper suspension.
    Higher ε = one hypothesis dominates = maybe should commit.
    """
    # Extract hypothesis percentages: H1={X}%, H2={Y}%...
    matches = re.findall(r"H\d+\s*=\s*(\d+)%", wf_output)
    if matches:
        max_pct = max(int(x) for x in matches) / 100.0
        return min(max_pct, 1.0)
    # Fallback: 暫定確信度: {X}%
    matches = re.findall(r"暫定確信度[:\s]*(\d+)%", wf_output)
    if matches:
        max_pct = max(int(x) for x in matches) / 100.0
        return min(max_pct, 1.0)
    # Default: suspension = low precision
    return 0.3


# ---- /pai (Proairesis) ルーブリック ----

# PURPOSE: /pai の η (忠実度) を WF 出力から計算
def _compute_eta_pai(wf_output: str) -> float:
    """Compute η for /pai (Proairesis) from output rubric.

    Components:
    - Checkpoint passage (max 0.4, 5 phases)
    - Pre-Mortem: failure causes enumerated (max 0.3)
    - Retreat conditions: defined (max 0.3)
    """
    eta = 0.0
    # 1. Checkpoint passage (5 phases)
    eta += _checkpoint_score(wf_output, 5) * 0.4

    # 2. Pre-Mortem: count failure causes (失敗原因N:)
    failure_causes = len(re.findall(r"失敗原因\d*[:\s]", wf_output))
    eta += min(failure_causes / 3.0, 1.0) * 0.3

    # 3. Retreat conditions: count (撤退条件 or 条件N → 撤退)
    retreat_conditions = len(re.findall(r"(?:撤退条件|条件\d*\s*→\s*撤退|条件\d+[:\s])", wf_output))
    # Also check the structured output format
    retreat_conditions += len(re.findall(r"^\s*\d+\..*撤退", wf_output, re.MULTILINE))
    retreat_conditions = min(retreat_conditions, 3)  # cap
    eta += min(retreat_conditions / 2.0, 1.0) * 0.3

    return min(eta, 1.0)


# PURPOSE: /pai の ε (精度) を WF 出力から計算
def _compute_epsilon_pai(wf_output: str) -> float:
    """Compute ε for /pai: extracts confidence percentage (base of investment)."""
    pct = _extract_confidence_pct(wf_output)
    if pct is not None:
        return min(max(pct, 0.0), 1.0)
    # Fallback: recommends invest level
    lower = wf_output.lower()
    if "invest" in lower:
        return 0.85
    if "stage" in lower:
        return 0.70
    if "bet" in lower:
        return 0.50
    return 0.3


# ---- /dok (Dokimasia) ルーブリック ----

# PURPOSE: /dok の η (忠実度) を WF 出力から計算
def _compute_eta_dok(wf_output: str) -> float:
    """Compute η for /dok (Dokimasia) from output rubric.

    Components:
    - Checkpoint passage (max 0.4, 5 phases)
    - Design quality: success + failure criteria defined (max 0.3)
    - EIG evaluation (max 0.3)
    """
    eta = 0.0
    # 1. Checkpoint passage (5 phases)
    eta += _checkpoint_score(wf_output, 5) * 0.4

    # 2. Design quality: success and failure criteria
    has_success = bool(re.search(r"成功基準", wf_output))
    has_failure = bool(re.search(r"失敗基準", wf_output))
    eta += (0.15 if has_success else 0) + (0.15 if has_failure else 0)

    # 3. EIG
    m = re.search(r"EIG[:\s]*\[?(HIGH|MED|LOW)\]?", wf_output, re.IGNORECASE)
    if m:
        grade = m.group(1).upper()
        eta += {"HIGH": 0.3, "MED": 0.15, "LOW": 0.05}.get(grade, 0.0)
    else:
        # Fallback: if design section exists
        if "打診行動" in wf_output or "打診設計" in wf_output:
            eta += 0.1

    return min(eta, 1.0)


# PURPOSE: /dok の ε (精度) を WF 出力から計算
def _compute_epsilon_dok(wf_output: str) -> float:
    """Compute ε for /dok: inherently low precision. Uses cumulative confidence."""
    # Phase 5 cumulative confidence
    m = re.search(r"累積確信度[:\s]*(\d+)", wf_output)
    if m:
        return min(int(m.group(1)) / 100.0, 1.0)
    # Fallback: probes are inherently uncertain
    return 0.2


# =============================================================================
# WF-aware η/ε dispatcher
# =============================================================================

# PURPOSE: WF ID に基づいて適切な η/ε 計算を呼び分ける
_ETA_COMPUTERS = {
    "kat": _compute_eta_kat,
    "epo": _compute_eta_epo,
    "pai": _compute_eta_pai,
    "dok": _compute_eta_dok,
}

_EPSILON_COMPUTERS = {
    "kat": _compute_epsilon_kat,
    "epo": _compute_epsilon_epo,
    "pai": _compute_epsilon_pai,
    "dok": _compute_epsilon_dok,
}


def compute_wf_eta(wf_id: str, wf_output: str) -> float:
    """Compute η for a specific WF using its rubric."""
    fn = _ETA_COMPUTERS.get(wf_id)
    if fn is None:
        return 0.0
    return fn(wf_output)


def compute_wf_epsilon(wf_id: str, wf_output: str) -> float:
    """Compute ε for a specific WF using its rubric."""
    fn = _EPSILON_COMPUTERS.get(wf_id)
    if fn is None:
        return 0.0
    return fn(wf_output)



# =============================================================================
# Builder (Adjunction Builder と対称)
# =============================================================================


# PURPOSE: Krisis 随伴をビルドする
def build_krisis_adjunction(
    pair: str,
    left_output: str = "",
    right_output: str = "",
) -> Adjunction:
    """Build a Krisis Adjunction from WF execution outputs.

    Design symmetry with adjunction_builder:
        adjunction_builder.build_adjunction(boot_report) → Adjunction
        krisis_adjunction_builder.build_krisis_adjunction("K⊣E", ...) → Adjunction

    Args:
        pair: "K⊣E" or "P⊣D"
        left_output: Output of the left adjoint WF (/kat or /pai)
        right_output: Output of the right adjoint WF (/epo or /dok)

    Returns:
        Adjunction with computed η and ε
    """
    template = KRISIS_ADJUNCTIONS.get(pair)
    if template is None:
        raise ValueError(f"Unknown Krisis adjunction pair: {pair}. Use 'K⊣E' or 'P⊣D'")

    # η: compute from WF-specific rubrics
    left_eta = compute_wf_eta(template.left_name, left_output) if left_output else 0.0
    right_eta = compute_wf_eta(template.right_name, right_output) if right_output else 0.0
    # Use the max of the two sides (whichever was actually executed)
    if left_output and right_output:
        eta = (left_eta + right_eta) / 2.0
    elif left_output:
        eta = left_eta
    elif right_output:
        eta = right_eta
    else:
        eta = 0.0

    # ε: compute from WF-specific rubrics
    left_eps = compute_wf_epsilon(template.left_name, left_output) if left_output else 0.0
    right_eps = compute_wf_epsilon(template.right_name, right_output) if right_output else 0.0
    if left_output and right_output:
        epsilon = (left_eps + right_eps) / 2.0
    elif left_output:
        epsilon = left_eps
    elif right_output:
        epsilon = right_eps
    else:
        epsilon = 0.0

    return Adjunction(
        left_name=template.left_name,
        right_name=template.right_name,
        source_category=template.source_category,
        target_category=template.target_category,
        eta_quality=eta,
        epsilon_precision=epsilon,
    )


# =============================================================================
# Display (describe_adjunction と対称)
# =============================================================================


# PURPOSE: Krisis 随伴ペアの状態を表示
def describe_krisis_pair(pair: str, adj: Optional[Adjunction] = None) -> str:
    """Human-readable description of a Krisis adjunction pair.

    Symmetric with adjunction_builder.describe_adjunction().
    """
    meta = KRISIS_PAIR_METADATA.get(pair, {})
    template = KRISIS_ADJUNCTIONS.get(pair)

    if template is None:
        return f"Unknown pair: {pair}"

    target = adj if adj is not None else template
    name = meta.get("name", pair)
    axis = meta.get("axis", "")
    fep = meta.get("fep", "")

    lines = [
        f"⊣ Krisis Adjunction: {name}",
        f"  軸: {axis}",
        f"  FEP: {fep}",
        f"  L ({target.left_name}): {target.source_category} → {target.target_category}",
        f"  R ({target.right_name}): {target.target_category} → {target.source_category}",
        f"  η (unit quality): {target.eta_quality:.2f}",
        f"  ε (counit precision): {target.epsilon_precision:.2f}",
        f"  drift: {target.drift:.2f}",
    ]

    if target.is_faithful:
        lines.append("  ✅ faithful (η > 0.8)")
    else:
        lines.append("  ⚠️ not faithful (η ≤ 0.8)")

    return "\n".join(lines)


# =============================================================================
# Lookup (WF ID → Adjunction pair)
# =============================================================================


# PURPOSE: WF ID から所属する Krisis 随伴ペアを返す
def get_adjunction_for_wf(wf_id: str) -> Optional[str]:
    """Get the Krisis adjunction pair for a given WF id.

    Args:
        wf_id: Workflow id (e.g. "kat", "epo", "pai", "dok")

    Returns:
        Pair name (e.g. "K⊣E") or None if not a Krisis WF
    """
    return KRISIS_WF_TO_ADJUNCTION.get(wf_id)


# PURPOSE: WF ID がどちらの adjoint か (left/right) を返す
def get_adjoint_role(wf_id: str) -> Optional[str]:
    """Get whether a WF is the left or right adjoint in its pair.

    Returns:
        "left" or "right", or None if not a Krisis WF
    """
    pair_name = get_adjunction_for_wf(wf_id)
    if pair_name is None:
        return None
    pair = KRISIS_ADJUNCTIONS[pair_name]
    if wf_id == pair.left_name:
        return "left"
    elif wf_id == pair.right_name:
        return "right"
    return None


# =============================================================================
# Drift Detection (ランタイム適切性判定)
# =============================================================================


# PURPOSE: 実行前に「逆の adjoint が適切か」を検出する
def detect_drift(
    wf_id: str,
    context: str = "",
) -> Optional[Dict[str, str]]:
    """Detect if the opposite adjoint would be more appropriate.

    FEP interpretation:
    - K⊣E drift: /kat を使おうとしているが、根拠不十分で /epo が適切
    - P⊣D drift: /pai を使おうとしているが、確信不十分で /dok が適切

    Args:
        wf_id: The WF about to be executed (e.g. "kat", "epo")
        context: Execution context text

    Returns:
        Dict with drift warning, or None if no drift detected
    """
    pair_name = get_adjunction_for_wf(wf_id)
    if pair_name is None:
        return None

    role = get_adjoint_role(wf_id)
    pair = KRISIS_ADJUNCTIONS[pair_name]
    meta = KRISIS_PAIR_METADATA.get(pair_name, {})

    # — Metrics-based drift detection —
    # Extract ε (confidence) from context to judge appropriateness
    epsilon = compute_wf_epsilon(wf_id, context)

    # K⊣E drift detection
    if pair_name == "K⊣E":
        if role == "left":  # /kat — committing
            # Drift if: low confidence but trying to commit
            # Also check TAINT ratio
            source_count = len(re.findall(r"SOURCE", context))
            taint_count = len(re.findall(r"TAINT", context))
            total = source_count + taint_count
            taint_ratio = taint_count / total if total > 0 else 0

            if epsilon < 0.6 or taint_ratio > 0.8:
                reasons = []
                if epsilon < 0.6:
                    reasons.append(f"確信度 {epsilon:.0%} < 60%")
                if taint_ratio > 0.8:
                    reasons.append(f"TAINT比率 {taint_ratio:.0%} > 80%")
                reason_str = ", ".join(reasons)
                return {
                    "drift_type": "premature_commitment",
                    "current_wf": wf_id,
                    "suggested_wf": pair.right_name,
                    "warning": f"⚠️ Drift 検出: {reason_str}。"
                               f"/epo (保留) が適切な可能性。",
                    "fep": meta.get("drift_meaning", ""),
                    "epsilon": epsilon,
                }
        elif role == "right":  # /epo — suspending
            # Drift if: high confidence or dominant hypothesis
            if epsilon > 0.9:
                return {
                    "drift_type": "unnecessary_suspension",
                    "current_wf": wf_id,
                    "suggested_wf": pair.left_name,
                    "warning": f"⚠️ Drift 検出: 確信度 {epsilon:.0%} が十分高いのに /epo (保留)。"
                               f"/kat (確定) が適切な可能性。",
                    "fep": meta.get("drift_meaning", ""),
                    "epsilon": epsilon,
                }
            # Procrastination check
            m = re.search(r"先延ばしスコア[:\s]*(\d+)/5", context)
            if m and int(m.group(1)) >= 3:
                return {
                    "drift_type": "procrastination",
                    "current_wf": wf_id,
                    "suggested_wf": pair.left_name,
                    "warning": f"⚠️ Drift 検出: 先延ばしスコア {m.group(1)}/5。"
                               f"/kat (確定) が適切な可能性。",
                    "fep": meta.get("drift_meaning", ""),
                    "epsilon": epsilon,
                }

    # P⊣D drift detection
    elif pair_name == "P⊣D":
        if role == "left":  # /pai — full investment
            if epsilon < 0.6:
                return {
                    "drift_type": "premature_investment",
                    "current_wf": wf_id,
                    "suggested_wf": pair.right_name,
                    "warning": f"⚠️ Drift 検出: 確信度 {epsilon:.0%} が低いのに /pai (全力投入)。"
                               f"/dok (打診) が適切な可能性。",
                    "fep": meta.get("drift_meaning", ""),
                    "epsilon": epsilon,
                }
        elif role == "right":  # /dok — minimal action
            if epsilon > 0.9:
                return {
                    "drift_type": "unnecessary_caution",
                    "current_wf": wf_id,
                    "suggested_wf": pair.left_name,
                    "warning": f"⚠️ Drift 検出: 確信度 {epsilon:.0%} が十分高いのに /dok (打診)。"
                               f"/pai (全力投入) が適切な可能性。",
                    "fep": meta.get("drift_meaning", ""),
                    "epsilon": epsilon,
                }

    return None


# =============================================================================
# Hermēneus execute 統合 — 実行後のη/ε自動計算
# =============================================================================


# PURPOSE: WF 実行結果から随伴メトリクスを計算し、結果テキストに付加するセクションを生成
def compute_adjunction_from_execution(
    wf_id: str,
    wf_output: str,
) -> Optional[Dict[str, object]]:
    """Compute adjunction metrics after WF execution.

    Called by Hermēneus _handle_execute to enrich the output.

    Args:
        wf_id: Executed WF id (e.g. "kat")
        wf_output: The text output of the WF

    Returns:
        Dict with adjunction, pair_name, role, and display section,
        or None if not a Krisis WF
    """
    pair_name = get_adjunction_for_wf(wf_id)
    if pair_name is None:
        return None

    role = get_adjoint_role(wf_id)
    if role == "left":
        adj = build_krisis_adjunction(pair_name, left_output=wf_output)
    else:
        adj = build_krisis_adjunction(pair_name, right_output=wf_output)

    return {
        "adjunction": adj,
        "pair_name": pair_name,
        "role": role,
        "section": format_adjunction_section(pair_name, adj, role, wf_id),
    }


# PURPOSE: 随伴セクションのテキスト表示 (Hermēneus/Boot 共用)
def format_adjunction_section(
    pair_name: str,
    adj: "Adjunction",
    role: Optional[str] = None,
    wf_id: Optional[str] = None,
) -> str:
    """Format adjunction metrics as a display section.

    Used by both Hermēneus execute output and /boot report.
    """
    meta = KRISIS_PAIR_METADATA.get(pair_name, {})
    name = meta.get("name", pair_name)

    faith = "✅ faithful" if adj.is_faithful else "⚠️ not faithful"
    drift_bar = _drift_bar(adj.drift)

    lines = [
        f"### ⊣ Krisis Adjunction: {name}",
        f"| 指標 | 値 |",
        f"|:-----|:---|",
        f"| η (unit quality) | {adj.eta_quality:.2f} |",
        f"| ε (counit precision) | {adj.epsilon_precision:.2f} |",
        f"| drift | {drift_bar} {adj.drift:.2f} |",
        f"| faithfulness | {faith} |",
    ]

    if role and wf_id:
        dual = adj.right_name if role == "left" else adj.left_name
        lines.append(f"\n→ 次の射提案: `/{dual}` ({_role_label(role)} → {_role_label('right' if role == 'left' else 'left')})")

    return "\n".join(lines)


# PURPOSE: Drift のビジュアルバー
def _drift_bar(drift: float) -> str:
    if drift <= 0.2:
        return "🟢"
    elif drift <= 0.5:
        return "🟡"
    elif drift <= 0.8:
        return "🟠"
    return "🔴"


# PURPOSE: Role のラベル
def _role_label(role: str) -> str:
    return {"left": "確定/投入", "right": "保留/打診"}.get(role, role)


# =============================================================================
# MorphismProposer 統合 — dual WF 提案
# =============================================================================


# PURPOSE: Krisis WF 完了後のdual提案と I→A 遷移提案を生成
def propose_dual_wf(wf_id: str) -> Optional[str]:
    """Generate morphism proposal text for Krisis WF completion.

    Two types of proposals:
    1. Dual: /kat → /epo (same pair, opposite adjoint)
    2. I→A transition: /kat → /pai (K⊣E → P⊣D, inference → action)

    Args:
        wf_id: Completed WF id

    Returns:
        Proposal text, or None if not a Krisis WF
    """
    pair_name = get_adjunction_for_wf(wf_id)
    if pair_name is None:
        return None

    role = get_adjoint_role(wf_id)
    pair = KRISIS_ADJUNCTIONS[pair_name]
    meta = KRISIS_PAIR_METADATA.get(pair_name, {})

    # 1. Dual proposal (same pair, opposite adjoint)
    dual_wf = pair.right_name if role == "left" else pair.left_name
    dual_role = "right" if role == "left" else "left"

    lines = [
        f"🔀 Krisis 射提案 (/{wf_id} 完了)",
        f"├─ 双対 ⊣ /{dual_wf}: {meta.get('name', pair_name)} の {_role_label(dual_role)} 側",
    ]

    # 2. I→A transition (K⊣E ↔ P⊣D)
    if pair_name == "K⊣E":
        # Inference complete → propose Action
        if role == "left":  # /kat (確定) → /pai (全力投入)
            lines.append(f"├─ I→A遷移 ⊣ /pai: 推論の確定 → 行為の全力投入")
        else:  # /epo (保留) → /dok (打診)
            lines.append(f"├─ I→A遷移 ⊣ /dok: 推論の保留 → 行為の打診")
    elif pair_name == "P⊣D":
        # Action complete → propose Inference review
        if role == "left":  # /pai (投入) → /kat (確定)
            lines.append(f"├─ A→I遷移 ⊣ /kat: 行為後 → 推論の確定 (振り返り)")
        else:  # /dok (打診) → /epo (保留)
            lines.append(f"├─ A→I遷移 ⊣ /epo: 打診後 → 推論の保留 (さらなる探索)")

    lines.append("└─ (完了)")

    return "\n".join(lines)


# =============================================================================
# Peira Health 統合 — HealthItem 生成
# =============================================================================


# PURPOSE: Krisis 随伴の健全性チェック結果を HealthItem で返す
def check_krisis_adjunction_health() -> list:
    """Check health of Krisis adjunctions using persistent metrics.

    Returns a list of tuples: (name, status, detail, metric)
    compatible with HealthItem constructor.
    """
    try:
        from mekhane.fep.krisis_metrics_store import aggregate_metrics
    except ImportError:
        return []

    results = []
    for pair_name, meta in KRISIS_PAIR_METADATA.items():
        name = meta.get("name", pair_name)
        agg = aggregate_metrics(pair_name)

        count = agg["count"]
        if count == 0:
            results.append((
                f"Adjunction {pair_name}",
                "WARN",
                f"{name}: 未計算 (WF 未実行)",
                None,
            ))
            continue

        eta = agg["avg_eta"]
        eps = agg["avg_epsilon"]
        drift = agg["avg_drift"]
        trend = agg["trend"]

        trend_icon = {"improving": "📈", "degrading": "📉", "stable": "→", "insufficient_data": "…", "no_data": "∅"}.get(trend, "?")

        # 80% 이상의 η を忠実とみなす
        if eta > 0.8:
            results.append((
                f"Adjunction {pair_name}",
                "OK",
                f"{name}: η={eta:.2f}, ε={eps:.2f} ({count}件, {trend_icon}{trend})",
                eta,
            ))
        else:
            results.append((
                f"Adjunction {pair_name}",
                "WARN",
                f"{name}: η={eta:.2f} (not faithful), drift={drift:.2f} ({count}件, {trend_icon}{trend})",
                eta,
            ))
    return results


if __name__ == "__main__":
    # Demo: describe both pairs
    for pair_name in KRISIS_ADJUNCTIONS:
        print(describe_krisis_pair(pair_name))
        print()

    # Demo: WF lookup
    for wf in ["kat", "epo", "pai", "dok", "noe"]:
        pair = get_adjunction_for_wf(wf)
        role = get_adjoint_role(wf)
        print(f"  {wf} → pair={pair}, role={role}")

    # Demo: Drift detection
    print("\n--- Drift Detection ---")
    drift = detect_drift("kat", "これは仮説ですが...")
    if drift:
        print(drift["warning"])

    # Demo: Dual proposal
    print("\n--- Dual Proposal ---")
    proposal = propose_dual_wf("kat")
    if proposal:
        print(proposal)

