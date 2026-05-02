# PROOF: [L2/FEP] <- mekhane/fep/krisis_helmholtz.py
# PURPOSE: /k (Krisis Peras) 実行の事後 Helmholtz Score 計算 — Poiesis WF への最初の bridge

from __future__ import annotations

from dataclasses import dataclass

from .basis import HelmholtzScore, helmholtz_score


@dataclass(frozen=True)
class KrisisExecution:
    """/k 実行トレースから収集した signal collection.

    Source: ~/.claude/skills/k/SKILL.md の C0/C2/C3 既出指標。
    PW は C0.S[0.3] (Certain/Uncertain 弁別) の重みづけから収集。
    """

    pw_kat: float       # V09 Katalēpsis の PW (0-1)
    pw_epo: float       # V10 Epochē の PW (0-1)
    pw_pai: float       # V11 Proairesis の PW (0-1)
    pw_dok: float       # V12 Dokimasia の PW (0-1)
    source_ratio: float           # ρ₁: SOURCE/(SOURCE+TAINT) ∈ [0,1]
    falsification_quality: float  # ρ₂: H=1.0 / M=0.5 / L=0.0
    revocation_clarity: float     # ρ₃: 1.0=機械的 / 0.5=曖昧 / 0=なし
    v4: float                     # kat⇔epo 矛盾度 ∈ [0,1]


def compute_krisis_helmholtz(ex: KrisisExecution) -> HelmholtzScore:
    """4動詞 (kat/epo/pai/dok) の intrinsic Γ/Q を PW × 品質指標で集約。

    - Γ (Exploit pole): kat (intrinsic Γ) + pai (intrinsic Γ) を
      SOURCE 裏付け + 撤回明確度で実効化
    - Q (Explore pole): epo (intrinsic Q) + dok (intrinsic Q) を
      反証品質 + 矛盾保存度で実効化

    H_s > 0.7: Exploit (確信収束) / H_s < 0.3: Explore (留保循環) / 0.3-0.7: Balance

    撤回条件: 1ヶ月運用で H_s と /k 判断品質に相関なし → formula 再設計 or 撤去。

    Args:
        ex: KrisisExecution signal

    Returns:
        HelmholtzScore(gamma, q, score) — score ∈ [0, 1]

    Examples:
        # 確信主体 (kat/pai 高、SOURCE 多、撤回明確)
        ex = KrisisExecution(pw_kat=0.4, pw_epo=0.1, pw_pai=0.4, pw_dok=0.1,
                             source_ratio=0.9, falsification_quality=1.0,
                             revocation_clarity=1.0, v4=0.2)
        hs = compute_krisis_helmholtz(ex)
        assert hs.score > 0.7  # Exploit 領域
    """
    gamma = (ex.pw_kat + ex.pw_pai) * 0.5 * (ex.source_ratio + ex.revocation_clarity)
    q = (ex.pw_epo + ex.pw_dok) * 0.5 * (ex.falsification_quality + ex.v4)
    return helmholtz_score(gamma=gamma, q=q)


__all__ = ["KrisisExecution", "compute_krisis_helmholtz"]
