#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/symploke/tests/
# PURPOSE: Boot THEOREM_REGISTRY の包括テスト — 32実体体系 (v4.2) の Boot 時参照を検証
"""Boot THEOREM_REGISTRY Tests — axiom_hierarchy.md v4.2 準拠"""

from mekhane.symploke.boot_integration import (
    THEOREM_REGISTRY,
    SERIES_INFO,
)


# ── THEOREM_REGISTRY ─────────────────────

# PURPOSE: 32実体体系 v4.2 の36動詞レジストリ正当性検証
class TestTheoremRegistry:
    """THEOREM_REGISTRY 定数のテスト (6族×4 = 36動詞)"""

    # ── 構造テスト ──

    # PURPOSE: 動詞総数が24であることを検証
    def test_total_count(self):
        """動詞総数 = 24 (6族×4極)"""
        assert len(THEOREM_REGISTRY) == 36

    # PURPOSE: T-series (Telos族) の存在と series コードを検証
    def test_t_series(self):
        """Telos族 (目的) — Flow × Value"""
        for tid in ["T1", "T2", "T3", "T4"]:
            assert tid in THEOREM_REGISTRY
            assert THEOREM_REGISTRY[tid]["series"] == "T"

    # PURPOSE: M-series (Methodos族) の存在と series コードを検証
    def test_m_series(self):
        """Methodos族 (戦略) — Flow × Function"""
        for tid in ["M1", "M2", "M3", "M4"]:
            assert tid in THEOREM_REGISTRY
            assert THEOREM_REGISTRY[tid]["series"] == "M"

    # PURPOSE: K-series (Krisis族) の存在と series コードを検証
    def test_k_series(self):
        """Krisis族 (判断) — Flow × Precision"""
        for tid in ["K1", "K2", "K3", "K4"]:
            assert tid in THEOREM_REGISTRY
            assert THEOREM_REGISTRY[tid]["series"] == "K"

    # PURPOSE: D-series (Diástasis族) の存在と series コードを検証
    def test_d_series(self):
        """Diástasis族 (拡張) — Flow × Scale"""
        for tid in ["D1", "D2", "D3", "D4"]:
            assert tid in THEOREM_REGISTRY
            assert THEOREM_REGISTRY[tid]["series"] == "D"

    # PURPOSE: O-series (Orexis族) の存在と series コードを検証
    def test_o_series(self):
        """Orexis族 (欲求) — Flow × Valence"""
        for tid in ["O1", "O2", "O3", "O4"]:
            assert tid in THEOREM_REGISTRY
            assert THEOREM_REGISTRY[tid]["series"] == "O"

    # PURPOSE: C-series (Chronos族) の存在と series コードを検証
    def test_c_series(self):
        """Chronos族 (時間) — Flow × Temporality"""
        for tid in ["C1", "C2", "C3", "C4"]:
            assert tid in THEOREM_REGISTRY
            assert THEOREM_REGISTRY[tid]["series"] == "C"

    # PURPOSE: 全エントリに name フィールドが存在することを検証
    def test_all_have_name(self):
        """全動詞に name フィールドがある"""
        for tid, info in THEOREM_REGISTRY.items():
            assert "name" in info, f"{tid} missing name"
            assert len(info["name"]) > 0

    # PURPOSE: 全エントリに wf フィールドが / で始まることを検証
    def test_all_have_wf(self):
        """全動詞に wf フィールドがあり / で始まる"""
        for tid, info in THEOREM_REGISTRY.items():
            assert "wf" in info, f"{tid} missing wf"
            assert info["wf"].startswith("/")

    # PURPOSE: 全エントリに level フィールドが d で始まることを検証
    def test_all_have_level(self):
        """全動詞に level フィールドがあり d で始まる (構成距離)"""
        for tid, info in THEOREM_REGISTRY.items():
            assert "level" in info, f"{tid} missing level"
            assert info["level"].startswith("d")

    # PURPOSE: 全エントリに series フィールドが正規コードであることを検証
    def test_all_have_series(self):
        """全動詞に series フィールドがある (T/M/K/D/O/C)"""
        for tid, info in THEOREM_REGISTRY.items():
            assert "series" in info, f"{tid} missing series"
            assert info["series"] in "TMKDOC"

    # PURPOSE: 全エントリに ja (日本語名) フィールドが存在することを検証
    def test_all_have_ja(self):
        """全動詞に ja (日本語動詞名) フィールドがある"""
        for tid, info in THEOREM_REGISTRY.items():
            assert "ja" in info, f"{tid} missing ja"
            assert len(info["ja"]) > 0

    # PURPOSE: 全エントリに pole フィールドが存在することを検証
    def test_all_have_pole(self):
        """全動詞に pole (Flow×修飾座標極) フィールドがある"""
        for tid, info in THEOREM_REGISTRY.items():
            assert "pole" in info, f"{tid} missing pole"
            assert "×" in info["pole"]

    # ── Telos 族：個別名称検証 ──
    # SOURCE: axiom_hierarchy.md L322-L325

    # PURPOSE: T1 Noēsis の名称を検証
    def test_t1_noesis(self):
        """T1 = Noēsis (理解する) — I×E"""
        assert THEOREM_REGISTRY["T1"]["name"] == "Noēsis"
        assert THEOREM_REGISTRY["T1"]["wf"] == "/noe"

    # PURPOSE: T2 Boulēsis の名称を検証
    def test_t2_boulesis(self):
        """T2 = Boulēsis (意志する) — I×P"""
        assert THEOREM_REGISTRY["T2"]["name"] == "Boulēsis"
        assert THEOREM_REGISTRY["T2"]["wf"] == "/bou"

    # PURPOSE: T3 Zētēsis の名称を検証
    def test_t3_zetesis(self):
        """T3 = Zētēsis (探求する) — A×E"""
        assert THEOREM_REGISTRY["T3"]["name"] == "Zētēsis"
        assert THEOREM_REGISTRY["T3"]["wf"] == "/zet"

    # PURPOSE: T4 Energeia の名称を検証
    def test_t4_energeia(self):
        """T4 = Energeia (実行する) — A×P"""
        assert THEOREM_REGISTRY["T4"]["name"] == "Energeia"
        assert THEOREM_REGISTRY["T4"]["wf"] == "/ene"

    # ── Methodos 族：個別名称検証 ──

    # PURPOSE: M1 Skepsis の名称を検証
    def test_m1_skepsis(self):
        """M1 = Skepsis (発散する) — I×Explore"""
        assert THEOREM_REGISTRY["M1"]["name"] == "Skepsis"
        assert THEOREM_REGISTRY["M1"]["wf"] == "/ske"

    # PURPOSE: M2 Synagōgē の名称を検証
    def test_m2_synagoge(self):
        """M2 = Synagōgē (収束する) — I×Exploit"""
        assert THEOREM_REGISTRY["M2"]["name"] == "Synagōgē"
        assert THEOREM_REGISTRY["M2"]["wf"] == "/sag"

    # ── Krisis 族：個別名称検証 ──

    # PURPOSE: K1 Katalēpsis の名称を検証
    def test_k1_katalepsis(self):
        """K1 = Katalēpsis (確定する) — I×C"""
        assert THEOREM_REGISTRY["K1"]["name"] == "Katalēpsis"
        assert THEOREM_REGISTRY["K1"]["wf"] == "/kat"

    # PURPOSE: K4 Dokimasia の名称を検証
    def test_k4_dokimasia(self):
        """K4 = Dokimasia (打診する) — A×U"""
        assert THEOREM_REGISTRY["K4"]["name"] == "Dokimasia"
        assert THEOREM_REGISTRY["K4"]["wf"] == "/dok"

    # ── Diástasis 族：個別名称検証 ──

    # PURPOSE: D1 Analysis の名称を検証
    def test_d1_analysis(self):
        """D1 = Analysis (詳細分析する) — I×Mi"""
        assert THEOREM_REGISTRY["D1"]["name"] == "Analysis"
        assert THEOREM_REGISTRY["D1"]["wf"] == "/lys"

    # ── Orexis 族：個別名称検証 ──

    # PURPOSE: O2 Elenchos の名称を検証
    def test_o2_elenchos(self):
        """O2 = Elenchos (批判する) — I×-"""
        assert THEOREM_REGISTRY["O2"]["name"] == "Elenchos"
        assert THEOREM_REGISTRY["O2"]["wf"] == "/ele"

    # ── Chronos 族：個別名称検証 ──

    # PURPOSE: C1 Hypomnēsis の名称を検証
    def test_c1_hypomnesis(self):
        """C1 = Hypomnēsis (想起する) — I×Past"""
        assert THEOREM_REGISTRY["C1"]["name"] == "Hypomnēsis"
        assert THEOREM_REGISTRY["C1"]["wf"] == "/hyp"

    # PURPOSE: C4 Proparaskeuē の名称を検証
    def test_c4_proparaskeve(self):
        """C4 = Proparaskeuē (仕掛ける) — A×Future"""
        assert THEOREM_REGISTRY["C4"]["name"] == "Proparaskeuē"
        assert THEOREM_REGISTRY["C4"]["wf"] == "/par"

    # ── Level Consistency (構成距離 d-level) ──

    # PURPOSE: T-series の level が d2 であることを検証 (Value 座標 = d=2)
    def test_t_series_levels(self):
        """Telos族 = d2 (Value 座標の構成距離)"""
        for tid in ["T1", "T2", "T3", "T4"]:
            assert THEOREM_REGISTRY[tid]["level"] == "d2"

    # PURPOSE: M-series の level が d2 であることを検証 (Function 座標 = d=2)
    def test_m_series_levels(self):
        """Methodos族 = d2 (Function 座標の構成距離)"""
        for tid in ["M1", "M2", "M3", "M4"]:
            assert THEOREM_REGISTRY[tid]["level"] == "d2"

    # PURPOSE: K-series の level が d2 であることを検証 (Precision 座標 = d=2)
    def test_k_series_levels(self):
        """Krisis族 = d2 (Precision 座標の構成距離)"""
        for tid in ["K1", "K2", "K3", "K4"]:
            assert THEOREM_REGISTRY[tid]["level"] == "d2"

    # PURPOSE: D-series の level が d3 であることを検証 (Scale 座標 = d=3)
    def test_d_series_levels(self):
        """Diástasis族 = d3 (Scale 座標の構成距離)"""
        for tid in ["D1", "D2", "D3", "D4"]:
            assert THEOREM_REGISTRY[tid]["level"] == "d3"

    # PURPOSE: O-series の level が d3 であることを検証 (Valence 座標 = d=3)
    def test_o_series_levels(self):
        """Orexis族 = d3 (Valence 座標の構成距離)"""
        for tid in ["O1", "O2", "O3", "O4"]:
            assert THEOREM_REGISTRY[tid]["level"] == "d3"

    # PURPOSE: C-series の level が d2 であることを検証 (Temporality 座標 = d=2)
    def test_c_series_levels(self):
        """Chronos族 = d2 (Temporality 座標の構成距離)"""
        for tid in ["C1", "C2", "C3", "C4"]:
            assert THEOREM_REGISTRY[tid]["level"] == "d2"

    # ── WF ユニーク性 ──

    # PURPOSE: 全 WF パスが一意であることを検証 (重複なし)
    def test_wf_unique(self):
        """全36動詞の wf パスが一意"""
        wfs = [info["wf"] for info in THEOREM_REGISTRY.values()]
        assert len(wfs) == len(set(wfs)), f"重複 WF: {[w for w in wfs if wfs.count(w) > 1]}"

    # ── 旧体系キーの不在検証 ──

    # PURPOSE: 旧体系のキー (S1-S4, H1-H4, P1-P4, A1-A4) が存在しないことを検証
    def test_no_legacy_keys(self):
        """旧体系の S/H/P/A シリーズキーが存在しない"""
        for prefix in ["S", "H", "P", "A"]:
            for i in range(1, 5):
                assert f"{prefix}{i}" not in THEOREM_REGISTRY, \
                    f"旧体系キー {prefix}{i} が残存"


# ── SERIES_INFO ──────────────────────────

# PURPOSE: 族メタデータの正当性検証
class TestSeriesInfo:
    """SERIES_INFO 定数のテスト (6族)"""

    # PURPOSE: 族数が6であることを検証
    def test_total_count(self):
        """族数 = 6"""
        assert len(SERIES_INFO) == 6

    # PURPOSE: 全族コードが揃っていることを検証
    def test_all_series_present(self):
        """T/M/K/D/O/C の全族が存在"""
        expected = {"T", "M", "K", "D", "O", "C"}
        assert set(SERIES_INFO.keys()) == expected

    # PURPOSE: T族ラベルに Telos が含まれることを検証
    def test_t_label(self):
        """T族 = Telos"""
        assert "Telos" in SERIES_INFO["T"]

    # PURPOSE: M族ラベルに Methodos が含まれることを検証
    def test_m_label(self):
        """M族 = Methodos"""
        assert "Methodos" in SERIES_INFO["M"]

    # PURPOSE: K族ラベルに Krisis が含まれることを検証
    def test_k_label(self):
        """K族 = Krisis"""
        assert "Krisis" in SERIES_INFO["K"]

    # PURPOSE: D族ラベルに Diástasis が含まれることを検証
    def test_d_label(self):
        """D族 = Diástasis"""
        assert "Diástasis" in SERIES_INFO["D"]

    # PURPOSE: O族ラベルに Orexis が含まれることを検証
    def test_o_label(self):
        """O族 = Orexis"""
        assert "Orexis" in SERIES_INFO["O"]

    # PURPOSE: C族ラベルに Chronos が含まれることを検証
    def test_c_label(self):
        """C族 = Chronos"""
        assert "Chronos" in SERIES_INFO["C"]

    # PURPOSE: 全族ラベルに日本語が含まれることを検証
    def test_all_have_japanese(self):
        """全族ラベルに日本語 (括弧内) が含まれる"""
        for key, label in SERIES_INFO.items():
            assert "(" in label, f"{key} missing Japanese in parentheses"

    # PURPOSE: 旧体系の族コード (S/H/P/A) が存在しないことを検証
    def test_no_legacy_series(self):
        """旧体系の S/H/P/A 族コードが存在しない"""
        for legacy in ["S", "H", "P", "A"]:
            assert legacy not in SERIES_INFO, f"旧族コード {legacy} が残存"
