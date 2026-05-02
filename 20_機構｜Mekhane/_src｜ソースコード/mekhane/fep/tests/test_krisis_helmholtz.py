# PROOF: [L2/テスト] <- mekhane/fep/tests/test_krisis_helmholtz.py
# PURPOSE: krisis_helmholtz の compute_krisis_helmholtz テスト
"""Tests for mekhane.fep.krisis_helmholtz — /k post-hoc Helmholtz Score."""

import pytest

from mekhane.fep.basis import HelmholtzScore
from mekhane.fep.krisis_helmholtz import KrisisExecution, compute_krisis_helmholtz


# ---------------------------------------------------------------------------
# compute_krisis_helmholtz
# ---------------------------------------------------------------------------

# PURPOSE: kat/pai 優位 + SOURCE 多 + 撤回明確 → H_s > 0.7 (Exploit)
class TestExploitDominant:
    """確信主体 (kat/pai 高 PW、SOURCE 多、反証は流す)"""

    def test_exploit_dominant_score_above_07(self):
        ex = KrisisExecution(
            pw_kat=0.4, pw_epo=0.1, pw_pai=0.4, pw_dok=0.1,
            source_ratio=0.9, falsification_quality=1.0,
            revocation_clarity=1.0, v4=0.2,
        )
        hs = compute_krisis_helmholtz(ex)
        assert isinstance(hs, HelmholtzScore)
        assert hs.score > 0.7

    def test_exploit_returns_helmholtz_score(self):
        ex = KrisisExecution(
            pw_kat=0.5, pw_epo=0.0, pw_pai=0.5, pw_dok=0.0,
            source_ratio=1.0, falsification_quality=0.5,
            revocation_clarity=1.0, v4=0.0,
        )
        hs = compute_krisis_helmholtz(ex)
        assert hs.gamma >= 0.0
        assert hs.q >= 0.0


# PURPOSE: epo/dok 優位 + 反証 HIGH + 矛盾高 → H_s < 0.3 (Explore)
class TestExploreDominant:
    """留保主体 (epo/dok 高 PW、反証 HIGH、矛盾保存)"""

    def test_explore_dominant_score_below_03(self):
        ex = KrisisExecution(
            pw_kat=0.1, pw_epo=0.4, pw_pai=0.1, pw_dok=0.4,
            source_ratio=0.5, falsification_quality=1.0,
            revocation_clarity=0.5, v4=0.8,
        )
        hs = compute_krisis_helmholtz(ex)
        assert hs.score < 0.3


# PURPOSE: 4動詞均等 + 中程度 signals → 0.3 ≤ H_s ≤ 0.7 (Balance)
class TestBalanced:
    """4動詞均等 PW、中程度の signals → Balance"""

    def test_balanced_in_range(self):
        ex = KrisisExecution(
            pw_kat=0.25, pw_epo=0.25, pw_pai=0.25, pw_dok=0.25,
            source_ratio=0.5, falsification_quality=0.5,
            revocation_clarity=0.5, v4=0.5,
        )
        hs = compute_krisis_helmholtz(ex)
        assert 0.3 <= hs.score <= 0.7


# PURPOSE: 全 signal=0 → helmholtz_score の定義により H_s == 0.5
class TestZeroSignals:
    """全 PW=0 → neutral fallback"""

    def test_zero_returns_half(self):
        ex = KrisisExecution(
            pw_kat=0.0, pw_epo=0.0, pw_pai=0.0, pw_dok=0.0,
            source_ratio=0.0, falsification_quality=0.0,
            revocation_clarity=0.0, v4=0.0,
        )
        hs = compute_krisis_helmholtz(ex)
        assert hs.score == 0.5
        assert hs.gamma == 0.0
        assert hs.q == 0.0
