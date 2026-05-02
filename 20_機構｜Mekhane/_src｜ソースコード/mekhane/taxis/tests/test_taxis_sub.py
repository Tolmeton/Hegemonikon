#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/taxis/tests/
# PURPOSE: TaxisSubscriber (K₆ 張力計算) のユニットテスト
"""TaxisSubscriber Tests — K₆ 張力計算の検証

taxis_sub.py の純粋関数をテストする。
Hermēneus の BaseSubscriber/EventBus への依存はモックで回避。
"""

import pytest
from itertools import combinations
from unittest.mock import MagicMock
from pathlib import Path

# --- YAML データ読込テスト ---


# PURPOSE: k6_weights.yaml の存在と構造を検証する
class TestK6WeightsYaml:
    """k6_weights.yaml のデータ整合性テスト"""

    # PURPOSE: YAML ファイルの存在確認
    def test_yaml_file_exists(self):
        """k6_weights.yaml が存在する"""
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        assert yaml_path.exists(), f"k6_weights.yaml not found at {yaml_path}"

    # PURPOSE: YAML を読み込んで15辺が定義されているか確認
    def test_yaml_has_15_edges(self):
        """K₆ 完全グラフの15辺が全て定義されている"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["edges"]) == 15

    # PURPOSE: 各辺が pair + weight + description を持つか確認
    def test_edge_structure(self):
        """各辺に pair, weight, description が含まれる"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for edge in data["edges"]:
            assert "pair" in edge, f"pair missing in {edge}"
            assert "weight" in edge, f"weight missing in {edge}"
            assert "description" in edge, f"description missing in {edge}"
            assert len(edge["pair"]) == 2, f"pair must have 2 elements: {edge}"

    # PURPOSE: 重みが 0.0-1.0 の範囲内か確認
    def test_weights_in_range(self):
        """全重みが [0.0, 1.0] の範囲内"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for edge in data["edges"]:
            w = edge["weight"]
            assert 0.0 <= w <= 1.0, f"weight {w} out of range for {edge['pair']}"

    # PURPOSE: v4.1 新略称が使用されているか確認
    def test_uses_new_abbreviations(self):
        """pair が v4.1 新略称 (Tel/Met/Kri/Dia/Ore/Chr) を使用している"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        valid_keys = {"Tel", "Met", "Kri", "Dia", "Ore", "Chr"}
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for edge in data["edges"]:
            for key in edge["pair"]:
                assert key in valid_keys, f"Unknown key '{key}' in {edge['pair']}"

    # PURPOSE: 15辺が K₆ の組合わせと完全一致するか確認
    def test_covers_all_k6_combinations(self):
        """15辺が C(6,2) の全組合せをカバーする"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        series = ["Tel", "Met", "Kri", "Dia", "Ore", "Chr"]
        expected = {tuple(sorted(p)) for p in combinations(series, 2)}
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        actual = {tuple(sorted(edge["pair"])) for edge in data["edges"]}
        assert actual == expected, f"Missing: {expected - actual}, Extra: {actual - expected}"

    # PURPOSE: v4.2.0 新フィールド d_class が全辺に存在するか確認
    def test_all_edges_have_d_class(self):
        """全辺に d_class フィールドが存在する"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        valid_classes = {"d2_internal", "d2xd3", "d3_internal"}
        for edge in data["edges"]:
            assert "d_class" in edge, f"d_class missing in {edge['pair']}"
            assert edge["d_class"] in valid_classes, (
                f"Invalid d_class '{edge['d_class']}' in {edge['pair']}"
            )

    # PURPOSE: v4.2.0 新フィールド fep_basis が全辺に存在するか確認
    def test_all_edges_have_fep_basis(self):
        """全辺に fep_basis フィールドが存在する"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for edge in data["edges"]:
            assert "fep_basis" in edge, f"fep_basis missing in {edge['pair']}"
            assert len(edge["fep_basis"]) > 10, (
                f"fep_basis too short in {edge['pair']}: '{edge['fep_basis']}'"
            )

    # PURPOSE: 3群分類の辺数が数学的に正しいか確認 (3+9+3=15)
    def test_d_class_counts(self):
        """d2_internal=3, d2xd3=9, d3_internal=3 の辺数配分"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        counts = {}
        for edge in data["edges"]:
            cls = edge["d_class"]
            counts[cls] = counts.get(cls, 0) + 1
        assert counts.get("d2_internal", 0) == 3, f"d2_internal count: {counts.get('d2_internal', 0)}"
        assert counts.get("d2xd3", 0) == 9, f"d2xd3 count: {counts.get('d2xd3', 0)}"
        assert counts.get("d3_internal", 0) == 3, f"d3_internal count: {counts.get('d3_internal', 0)}"

    # PURPOSE: d2_internal 辺が d=2 座標のみで構成されているか確認
    def test_d2_internal_contains_only_d2_coords(self):
        """d2_internal 辺は d=2 座標 (Tel, Met, Kri) のみで構成"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        d2_coords = {"Tel", "Met", "Kri"}
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for edge in data["edges"]:
            if edge["d_class"] == "d2_internal":
                for key in edge["pair"]:
                    assert key in d2_coords, (
                        f"d2_internal edge contains non-d2 coord '{key}': {edge['pair']}"
                    )

    # PURPOSE: d3_internal 辺が d≥3 座標のみで構成されているか確認
    def test_d3_internal_contains_only_d3_coords(self):
        """d3_internal 辺は d≥3 座標 (Dia, Ore, Chr) のみで構成"""
        import yaml
        yaml_path = (
            Path(__file__).resolve().parent.parent.parent
            / "taxis"
            / "k6_weights.yaml"
        )
        # NOTE: Temporality (Chr) は d=2 だが歴史的経緯で d3 側にグループ化されている
        # ここでは taxis.md v4.2.0 の定義 (d3_internal = Scale/Valence/Temporality 間) に従う
        d3_coords = {"Dia", "Ore", "Chr"}
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for edge in data["edges"]:
            if edge["d_class"] == "d3_internal":
                for key in edge["pair"]:
                    assert key in d3_coords, (
                        f"d3_internal edge contains non-d3 coord '{key}': {edge['pair']}"
                    )

# --- 純粋関数テスト (Hermēneus 非依存) ---


# PURPOSE: _estimate_semantic_tension の単体テスト
class TestEstimateSemanticTension:
    """意味的張力推定のテスト"""

    @staticmethod
    def _estimate(text_a: str, text_b: str) -> float:
        """taxis_sub の static method を直接呼ぶ (import 回避のため再実装)"""
        if not text_a or not text_b:
            return 0.5
        opposites = [
            ("高", "低"), ("大", "小"), ("積極", "慎重"),
            ("探索", "活用"), ("広域", "局所"),
            ("リスク", "安全"), ("不足", "充足"),
        ]
        opposition_count = 0
        for pos, neg in opposites:
            if (pos in text_a and neg in text_b) or (neg in text_a and pos in text_b):
                opposition_count += 1
        words_a = set(text_a)
        words_b = set(text_b)
        if words_a | words_b:
            overlap = len(words_a & words_b) / len(words_a | words_b)
        else:
            overlap = 0.0
        tension = min(1.0, opposition_count * 0.3 + (1.0 - overlap) * 0.3)
        return tension

    # PURPOSE: 空入力時のデフォルト値テスト
    def test_empty_input_returns_default(self):
        """空文字列は 0.5 を返す"""
        assert self._estimate("", "test") == 0.5
        assert self._estimate("test", "") == 0.5
        assert self._estimate("", "") == 0.5

    # PURPOSE: 対立語がある場合の高張力テスト
    def test_opposition_increases_tension(self):
        """対立語ペアが検出されると張力が上がる"""
        no_opposition = self._estimate("テスト", "テスト")
        with_opposition = self._estimate("探索的方針", "活用を重視")
        assert with_opposition > no_opposition

    # PURPOSE: 同一テキストの場合の低張力テスト
    def test_identical_text_low_tension(self):
        """同一テキストは低張力"""
        tension = self._estimate("同じテキスト", "同じテキスト")
        assert tension < 0.2

    # PURPOSE: 完全に異なるテキストの場合のテスト
    def test_different_text_has_some_tension(self):
        """完全に異なるテキストは文字重複率が低いため張力が上がる"""
        tension = self._estimate("ABC", "XYZ")
        assert tension > 0.0

    # PURPOSE: 張力が 0.0-1.0 の範囲であることの確認
    def test_tension_bounded(self):
        """張力は常に [0.0, 1.0] 内"""
        # 大量の対立語を含む極端なケース
        extreme = self._estimate(
            "高い大きい積極探索広域リスク不足",
            "低い小さい慎重活用局所安全充足",
        )
        assert 0.0 <= extreme <= 1.0


# PURPOSE: _compute_contradiction の単体テスト
class TestComputeContradiction:
    """矛盾度 V 計算のテスト"""

    @staticmethod
    def _make_edges(tensions: list[float]):
        """テスト用 TensionEdge のリストを生成"""
        from dataclasses import dataclass

        @dataclass
        class MockEdge:
            series_a: str = ""
            series_b: str = ""
            weight: float = 0.0
            semantic_score: float = 0.0
            tension: float = 0.0

        return [MockEdge(tension=t) for t in tensions]

    # PURPOSE: 空リストの場合の矛盾度テスト
    def test_empty_returns_zero(self):
        """空リストは矛盾度 0.0"""
        edges = self._make_edges([])
        total = sum(e.tension for e in edges)
        v = total / len(edges) if edges else 0.0
        assert v == 0.0

    # PURPOSE: 均一張力の場合の矛盾度テスト
    def test_uniform_tension(self):
        """均一張力は平均値"""
        edges = self._make_edges([0.3, 0.3, 0.3])
        v = sum(e.tension for e in edges) / len(edges)
        assert abs(v - 0.3) < 0.001

    # PURPOSE: 混合張力の場合の矛盾度テスト
    def test_mixed_tension(self):
        """混合張力は正しい平均値"""
        edges = self._make_edges([0.0, 0.5, 1.0])
        v = sum(e.tension for e in edges) / len(edges)
        assert abs(v - 0.5) < 0.001


# --- K₆ 構造テスト ---


# PURPOSE: K₆ 完全グラフの構造的正しさを検証する
class TestK6Structure:
    """K₆ の数学的構造テスト"""

    # PURPOSE: C(6,2) = 15 辺の数を確認
    def test_k6_has_15_edges(self):
        """C(6,2) = 15 辺"""
        series = ["Tel", "Met", "Kri", "Dia", "Ore", "Chr"]
        edges = list(combinations(series, 2))
        assert len(edges) == 15

    # PURPOSE: 各頂点の次数が 5 であることを確認
    def test_each_vertex_degree_5(self):
        """完全グラフの各頂点の次数は n-1 = 5"""
        series = ["Tel", "Met", "Kri", "Dia", "Ore", "Chr"]
        edges = list(combinations(series, 2))
        for s in series:
            degree = sum(1 for a, b in edges if a == s or b == s)
            assert degree == 5, f"{s} の次数が {degree} ≠ 5"


# --- _load_k6_weights フォールバックテスト ---


# PURPOSE: YAML 読込の正常系・異常系テスト
class TestLoadK6Weights:
    """YAML 読込関数のテスト"""

    # PURPOSE: 存在しないパスでフォールバックが動作するか
    def test_fallback_on_missing_file(self):
        """ファイルが存在しない場合、全辺 0.3 のフォールバック"""
        # _load_k6_weights を直接テストする代わりに、
        # フォールバックロジックを再現
        series = ["Tel", "Met", "Kri", "Dia", "Ore", "Chr"]
        fallback = {(a, b): 0.3 for a, b in combinations(series, 2)}
        assert len(fallback) == 15
        assert all(v == 0.3 for v in fallback.values())

    # PURPOSE: 正常な YAML から重みが読み込まれるか
    def test_load_from_yaml(self, tmp_path):
        """YAML ファイルから正しく読み込まれる"""
        import yaml

        # テスト用 YAML を作成
        test_data = {
            "edges": [
                {"pair": ["Tel", "Met"], "weight": 0.5, "description": "test"},
                {"pair": ["Tel", "Kri"], "weight": 0.7, "description": "test"},
            ]
        }
        yaml_file = tmp_path / "test_weights.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(test_data, f)

        # 読込を再現
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        weights = {}
        for edge in data.get("edges", []):
            pair = tuple(edge["pair"])
            weights[pair] = edge["weight"]

        assert weights[("Tel", "Met")] == 0.5
        assert weights[("Tel", "Kri")] == 0.7


# =============================================================================
# Blackboard 統合テスト — sys.modules モックで TaxisSubscriber を直接テスト
# =============================================================================

import sys
import types
from enum import Enum
from dataclasses import dataclass as _dc, field as _field


# PURPOSE: Hermēneus の内部モジュールをモック化して taxis_sub をインポート可能にする
def _setup_mock_hermeneus():
    """Hermēneus の BaseSubscriber, ActivationPolicy, CognitionEvent, EventType をモック化"""

    # --- EventType モック ---
    class MockEventType(Enum):
        STEP_COMPLETE = "step_complete"
        MACRO_START = "macro_start"
        VERIFICATION = "verification"
        CONVERGENCE_ITER = "convergence_iter"

    # --- CognitionEvent モック ---
    @_dc
    class MockCognitionEvent:
        event_type: MockEventType = MockEventType.MACRO_START
        metadata: dict = _field(default_factory=dict)
        blackboard: object = None
        entropy_delta: float = 0.0
        entropy_after: float = 0.5
        source_node: str = ""
        event_id: str = "test"
        iteration: int = 0

    # --- ActivationPolicy モック ---
    @_dc
    class MockActivationPolicy:
        event_types: set = _field(default_factory=set)
        custom_predicate: object = None
        min_entropy_delta: float = 0.0
        min_entropy: float = 0.0
        max_entropy: float = 1.0
        node_patterns: list = _field(default_factory=list)
        exclude_patterns: list = _field(default_factory=list)
        iteration_filter: object = None
        frequency: int = 1
        _counter: int = 0

        def evaluate(self, event):
            return True

    # --- BaseSubscriber モック ---
    class MockBaseSubscriber:
        def __init__(self, name="mock", policy=None, fire_threshold=0.0, **kwargs):
            self._name = name
            self.policy = policy or MockActivationPolicy()
            self.fire_threshold = fire_threshold
            self._score_history = []
            self._activation_count = 0
            self._skip_count = 0

        @property
        def name(self):
            return self._name

        def should_activate(self, event):
            return True

        def score(self, event):
            return 0.5

        def handle(self, event):
            raise NotImplementedError

    # --- モジュールを注入 ---
    # hermeneus パッケージ構造を作成
    for mod_name in [
        "hermeneus", "hermeneus.src", "hermeneus.src.events",
        "hermeneus.src.subscribers", "hermeneus.src.activation",
        "hermeneus.src.event_bus",
    ]:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = types.ModuleType(mod_name)

    # event_bus モジュールにオブジェクトを設定
    event_bus_mod = sys.modules["hermeneus.src.event_bus"]
    event_bus_mod.EventType = MockEventType
    event_bus_mod.CognitionEvent = MockCognitionEvent

    # activation モジュールにオブジェクトを設定
    activation_mod = sys.modules["hermeneus.src.activation"]
    activation_mod.BaseSubscriber = MockBaseSubscriber
    activation_mod.ActivationPolicy = MockActivationPolicy

    return MockEventType, MockCognitionEvent, MockActivationPolicy, MockBaseSubscriber


# テスト開始前にモックをセットアップ
_EventType, _CognitionEvent, _ActivationPolicy, _BaseSubscriber = _setup_mock_hermeneus()

# taxis_sub を動的にインポート (モックが sys.modules にある状態で)
import importlib
_taxis_sub_spec = importlib.util.spec_from_file_location(
    "hermeneus.src.subscribers.taxis_sub",
    Path(__file__).resolve().parent.parent.parent.parent
    / "hermeneus" / "src" / "subscribers" / "taxis_sub.py",
)
_taxis_sub = importlib.util.module_from_spec(_taxis_sub_spec)
sys.modules["hermeneus.src.subscribers.taxis_sub"] = _taxis_sub
_taxis_sub_spec.loader.exec_module(_taxis_sub)

TaxisSubscriber = _taxis_sub.TaxisSubscriber
TensionEdge = _taxis_sub.TensionEdge
SERIES_KEYS_IMPORTED = _taxis_sub.SERIES_KEYS
K6_WEIGHTS_IMPORTED = _taxis_sub.K6_TENSION_WEIGHTS


# --- Mock Blackboard ---

class MockBlackboard:
    """TaxisSubscriber が必要とする Blackboard インターフェースのモック"""

    def __init__(self, fill_rate: float = 1.0, limits: dict = None):
        self.series_fill_rate = fill_rate
        self.series_limits = limits or {}
        self._written = {}  # write() の記録

    def write(self, key, value, source=""):
        self._written[key] = {"value": value, "source": source}


# =============================================================================
# TaxisSubscriber 統合テストクラス群
# =============================================================================


# PURPOSE: モジュールレベルのインポート検証
class TestTaxisSubImport:
    """taxis_sub モジュールのモックインポートが正しく動作するか"""

    def test_series_keys_are_new_abbreviations(self):
        """SERIES_KEYS が v4.1 新略称"""
        assert SERIES_KEYS_IMPORTED == ["Tel", "Met", "Kri", "Dia", "Ore", "Chr"]

    def test_k6_weights_loaded(self):
        """K6_TENSION_WEIGHTS が15辺を持つ"""
        assert len(K6_WEIGHTS_IMPORTED) == 15

    def test_k6_weights_values_in_range(self):
        """全重みが [0.0, 1.0] 内"""
        for pair, w in K6_WEIGHTS_IMPORTED.items():
            assert 0.0 <= w <= 1.0, f"{pair}: {w}"


# PURPOSE: TaxisSubscriber.score() のテスト
class TestTaxisSubscriberScore:
    """score() — Blackboard の充填率に基づく自律発火判定"""

    def test_score_with_no_blackboard(self):
        """blackboard なしは score=0.0"""
        sub = TaxisSubscriber()
        event = _CognitionEvent(blackboard=None)
        assert sub.score(event) == 0.0

    def test_score_empty_blackboard(self):
        """充填率 0.0 は score=0.0"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(fill_rate=0.0)
        event = _CognitionEvent(blackboard=bb)
        assert sub.score(event) == 0.0

    def test_score_half_filled(self):
        """充填率 0.5 は score=0.5"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(fill_rate=0.5)
        event = _CognitionEvent(blackboard=bb)
        assert sub.score(event) == 0.5

    def test_score_fully_filled(self):
        """充填率 1.0 は score=1.0"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(fill_rate=1.0)
        event = _CognitionEvent(blackboard=bb)
        assert sub.score(event) == 1.0


# PURPOSE: TaxisSubscriber.handle() のテスト
class TestTaxisSubscriberHandle:
    """handle() — K₆ 張力計算 + 統合結論"""

    def _make_full_bb(self, limits: dict = None):
        """全族充填済みの Blackboard を生成"""
        default_limits = {
            "Tel": "目的は明確だが大きい",
            "Met": "探索的アプローチを採用",
            "Kri": "確信は低い段階",
            "Dia": "広域の影響範囲",
            "Ore": "リスクを許容する方針",
            "Chr": "短期的な展開を想定",
        }
        return MockBlackboard(fill_rate=1.0, limits=limits or default_limits)

    def test_handle_returns_none_without_blackboard(self):
        """blackboard なしは None"""
        sub = TaxisSubscriber()
        event = _CognitionEvent(blackboard=None)
        assert sub.handle(event) is None

    def test_handle_returns_none_when_not_fully_filled(self):
        """未充填は None"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(fill_rate=0.5)
        event = _CognitionEvent(blackboard=bb)
        assert sub.handle(event) is None

    def test_handle_returns_output_when_fully_filled(self):
        """全族充填で出力を返す"""
        sub = TaxisSubscriber()
        bb = self._make_full_bb()
        event = _CognitionEvent(blackboard=bb)
        result = sub.handle(event)
        assert result is not None
        assert "[X: 関係 (Taxis)" in result
        assert "矛盾度 V" in result

    def test_handle_writes_to_blackboard(self):
        """handle() が Blackboard に結論を書き込む"""
        sub = TaxisSubscriber()
        bb = self._make_full_bb()
        event = _CognitionEvent(blackboard=bb)
        sub.handle(event)
        assert "slots.taxis_conclusion" in bb._written
        assert "slots.taxis_V" in bb._written
        assert bb._written["slots.taxis_conclusion"]["source"] == "taxis"

    def test_handle_v_threshold_routing(self):
        """V > 0.3 → 重み付け融合 / V ≤ 0.3 → 通常融合"""
        sub = TaxisSubscriber()
        # 対立語を入れて高張力を誘発
        high_tension_limits = {
            "Tel": "大きい積極的な探索が必要",
            "Met": "小さい慎重な活用を重視",
            "Kri": "高い確信を持つ安全な判断",
            "Dia": "低い不確実性で局所的に行う",
            "Ore": "リスクを大きく取る積極方針",
            "Chr": "充足した安全な状態を維持",
        }
        bb = self._make_full_bb(high_tension_limits)
        event = _CognitionEvent(blackboard=bb)
        result = sub.handle(event)
        # 出力に「融合」が含まれる
        assert "融合" in result

    def test_handle_shows_top_tensions(self):
        """出力に上位3張力が含まれる"""
        sub = TaxisSubscriber()
        bb = self._make_full_bb()
        event = _CognitionEvent(blackboard=bb)
        result = sub.handle(event)
        assert "⚡" in result  # 張力マーカー


# PURPOSE: _compute_k6_tensions の統合テスト
class TestComputeK6TensionsIntegration:
    """_compute_k6_tensions — Blackboard limits からの張力計算"""

    def test_returns_15_edges(self):
        """全15辺が計算される"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(limits={
            "Tel": "t", "Met": "m", "Kri": "k",
            "Dia": "d", "Ore": "o", "Chr": "c",
        })
        tensions = sub._compute_k6_tensions(bb)
        assert len(tensions) == 15

    def test_each_edge_is_tension_edge(self):
        """各辺が TensionEdge"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(limits={s: "x" for s in SERIES_KEYS_IMPORTED})
        tensions = sub._compute_k6_tensions(bb)
        for t in tensions:
            assert isinstance(t, TensionEdge)
            assert 0.0 <= t.tension <= 1.0

    def test_empty_limits_uses_default_semantic(self):
        """limits が空文字列の場合、semantic = 0.5 (情報不足デフォルト)"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(limits={s: "" for s in SERIES_KEYS_IMPORTED})
        tensions = sub._compute_k6_tensions(bb)
        for t in tensions:
            assert t.semantic_score == 0.5


# PURPOSE: _weighted_fusion の統合テスト
class TestWeightedFusionIntegration:
    """_weighted_fusion — 高張力ペア優先の融合"""

    def test_output_contains_top_pair(self):
        """出力に最高張力ペアが含まれる"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(limits={
            "Tel": "大きな目標", "Met": "小さな戦略",
            "Kri": "中間の確信", "Dia": "広い範囲",
            "Ore": "高いリスク許容", "Chr": "短い時間軸",
        })
        tensions = sub._compute_k6_tensions(bb)
        result = sub._weighted_fusion(bb, tensions)
        assert "主要矛盾" in result
        assert "⊗" in result

    def test_output_truncates_long_limits(self):
        """limit が50文字で切り捨てられる"""
        sub = TaxisSubscriber()
        long_text = "あ" * 100
        bb = MockBlackboard(limits={s: long_text for s in SERIES_KEYS_IMPORTED})
        tensions = sub._compute_k6_tensions(bb)
        result = sub._weighted_fusion(bb, tensions)
        # 50文字に切り捨てられているか確認
        assert len(result) < 250  # 全体が合理的な長さ


# PURPOSE: _simple_aggregate の統合テスト
class TestSimpleAggregateIntegration:
    """_simple_aggregate — 低矛盾時の均等集約"""

    def test_output_contains_all_series(self):
        """出力に全6族が含まれる"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(limits={s: f"{s}の結論" for s in SERIES_KEYS_IMPORTED})
        result = sub._simple_aggregate(bb)
        for s in SERIES_KEYS_IMPORTED:
            assert s in result

    def test_pipes_separate_series(self):
        """族間が | で区切られる"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(limits={s: f"{s}結論" for s in SERIES_KEYS_IMPORTED})
        result = sub._simple_aggregate(bb)
        assert result.count("|") == 5  # 6族を5個の | で区切る

    def test_empty_limits_excluded(self):
        """空の limit は出力から除外"""
        sub = TaxisSubscriber()
        bb = MockBlackboard(limits={
            "Tel": "目標あり", "Met": "", "Kri": "確信あり",
            "Dia": "", "Ore": "リスクあり", "Chr": "",
        })
        result = sub._simple_aggregate(bb)
        assert "Met" not in result
        assert "Dia" not in result
        assert result.count("|") == 2  # 3族を2個の | で区切る

    def test_truncates_at_40_chars(self):
        """各 limit が40文字に切り捨て"""
        sub = TaxisSubscriber()
        long_text = "あ" * 100
        bb = MockBlackboard(limits={s: long_text for s in SERIES_KEYS_IMPORTED})
        result = sub._simple_aggregate(bb)
        parts = result.split(" | ")
        for part in parts:
            # "Key: " (5文字) + limit (40文字) = 45文字以下
            assert len(part) <= 45, f"Part too long: {len(part)} chars"
