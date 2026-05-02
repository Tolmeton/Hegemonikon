#!/usr/bin/env python3
# PROOF: [L2/テスト] <- CCL 型推論 (Aletheia フィルトレーション n=2) の検証
"""
CCL 型推論テスト — TypeSeq (Aletheia フィルトレーション n=2)

ccl_infer_type, ccl_type_seq, ccl_type_features の正確性を検証する。
VISION §1.6 の型システム S/T/P/M に基づく。
"""
import ast
import pytest
import sys
from pathlib import Path

# mekhane パスを追加
_MEKHANE_SRC = Path(__file__).resolve().parents[2] / "20_機構｜Mekhane" / "_src｜ソースコード"
if str(_MEKHANE_SRC) not in sys.path:
    sys.path.insert(0, str(_MEKHANE_SRC))

from mekhane.symploke.code_ingest import (
    ccl_infer_type,
    ccl_type_seq,
    ccl_type_features,
    ccl_feature_vector,
    python_to_ccl,
)


# ============================================================
# ccl_infer_type テスト
# ============================================================

class TestCclInferType:
    """個別トークンの型推論テスト。"""

    def test_state_tokens(self):
        """S 型: データ・状態トークン"""
        assert ccl_infer_type('¥') == 'S'
        assert ccl_infer_type('#') == 'S'
        assert ccl_infer_type('()') == 'S'
        assert ccl_infer_type('str_') == 'S'
        assert ccl_infer_type('num_') == 'S'
        assert ccl_infer_type('nil_') == 'S'
        assert ccl_infer_type('bool_') == 'S'

    def test_transform_tokens(self):
        """T 型: 変換トークン"""
        assert ccl_infer_type('fn') == 'T'
        assert ccl_infer_type('fn2') == 'T'
        assert ccl_infer_type('.append') == 'T'
        assert ccl_infer_type('.method') == 'T'
        assert ccl_infer_type('sorted') == 'T'
        assert ccl_infer_type('len') == 'T'
        assert ccl_infer_type('pred') == 'T'
        assert ccl_infer_type('.attr') == 'T'

    def test_process_tokens(self):
        """P 型: プロセストークン"""
        assert ccl_infer_type('~') == 'P'

    def test_meta_tokens(self):
        """M 型: メタトークン"""
        assert ccl_infer_type('^') == 'M'
        assert ccl_infer_type('[def]') == 'M'

    def test_structural_tokens_none(self):
        """構造子は型付けしない"""
        assert ccl_infer_type('>>') is None
        assert ccl_infer_type('(') is None
        assert ccl_infer_type(')') is None
        assert ccl_infer_type('{') is None
        assert ccl_infer_type('}') is None
        assert ccl_infer_type('%') is None
        assert ccl_infer_type('*') is None


# ============================================================
# ccl_type_seq テスト
# ============================================================

class TestCclTypeSeq:
    """TypeSeq 生成テスト。"""

    def test_simple_pipeline(self):
        """単純パイプライン: S→T→S"""
        # ¥ >> sorted
        seq = ccl_type_seq("¥ >> sorted")
        assert seq == ['S', 'T']

    def test_multi_transform(self):
        """複数変換: S→T→T→T→S"""
        seq = ccl_type_seq("¥ >> fn >> V:{pred} >> F:[each]{fn} >> return")
        # ¥=S, fn=T, V:{pred}=T, F:[each]{fn}=T, return=S (※ return は None → S)
        assert seq == ['S', 'T', 'T', 'T', 'S']

    def test_empty_input(self):
        """空入力"""
        assert ccl_type_seq("") == ['S']
        assert ccl_type_seq("  ") == ['S']

    def test_single_state(self):
        """単一状態 (空関数)"""
        assert ccl_type_seq("#") == ['S']

    def test_with_oscillation(self):
        """振動 (~) を含む式"""
        seq = ccl_type_seq("¥ >> fn ~ fn >> return")
        # ¥=S, "fn ~ fn"=P (~ が最優先), return=S
        assert seq == ['S', 'P', 'S']

    def test_with_meta(self):
        """メタ ([def]) を含む式"""
        seq = ccl_type_seq("[def]{fn >> fn}")
        # [def]{fn は M, fn} は T に分割される
        assert seq == ['M', 'T']

    def test_real_function(self):
        """実際の Python 関数から TypeSeq を生成"""
        code = """
def process(items):
    filtered = [x for x in items if x > 0]
    return sorted(filtered)
"""
        tree = ast.parse(code)
        func = tree.body[0]
        ccl = python_to_ccl(func)
        seq = ccl_type_seq(ccl)
        # ccl は "¥ >> V:{...} >> F:[each]{...} >> sorted" のような形
        # 各セグメントに T が含まれるはず
        assert len(seq) >= 2
        assert all(t in ('S', 'T', 'P', 'M') for t in seq)

    def test_conditional_function(self):
        """条件分岐のある関数"""
        code = """
def check(x):
    if x > 0:
        return x
    else:
        return 0
"""
        tree = ast.parse(code)
        func = tree.body[0]
        ccl = python_to_ccl(func)
        seq = ccl_type_seq(ccl)
        assert len(seq) >= 2
        assert 'T' in seq  # I:[ok] = T


# ============================================================
# ccl_type_features テスト
# ============================================================

class TestCclTypeFeatures:
    """型特徴量 (8d) テスト。"""

    def test_dimension(self):
        """8 次元であること"""
        features = ccl_type_features("¥ >> fn >> return")
        assert len(features) == 8

    def test_distribution_sums_to_one(self):
        """型分布 (先頭 4d) の合計が 1.0"""
        features = ccl_type_features("¥ >> fn >> V:{pred} >> return")
        dist = features[:4]
        assert abs(sum(dist) - 1.0) < 1e-10

    def test_pure_transform_chain(self):
        """変換のみの連鎖: T率が高い"""
        features = ccl_type_features("fn >> fn >> fn >> fn")
        s_rate, t_rate, p_rate, m_rate = features[:4]
        assert t_rate == 1.0
        assert s_rate == 0.0
        assert p_rate == 0.0

    def test_flow_metrics(self):
        """型フロー指標"""
        features = ccl_type_features("¥ >> fn >> fn >> return")
        seq_len = features[4]
        max_t_run = features[5]
        st_transitions = features[6]
        ts_transitions = features[7]

        assert seq_len == 4.0  # S, T, T, S
        assert max_t_run == 2.0  # T, T の連続
        assert st_transitions == 1.0  # S→T
        assert ts_transitions == 1.0  # T→S


# ============================================================
# ccl_feature_vector テスト (53d)
# ============================================================

class TestCclFeatureVector:
    """53d ベクトル全体のテスト。"""

    def test_dimension_53(self):
        """49 次元であること (29d ccl + 12d structural + 8d type)"""
        code = "def f(x): return x + 1"
        tree = ast.parse(code)
        func = tree.body[0]
        vec = ccl_feature_vector(func)
        assert len(vec) == 49, f"Expected 49d, got {len(vec)}d"

    def test_all_float_or_int(self):
        """全要素が int または float"""
        code = "def f(x): return sorted(x)"
        tree = ast.parse(code)
        func = tree.body[0]
        vec = ccl_feature_vector(func)
        assert all(isinstance(v, (int, float)) for v in vec)

    def test_type_features_appended(self):
        """末尾 8 要素が型特徴量"""
        code = "def f(x, y): return x + y"
        tree = ast.parse(code)
        func = tree.body[0]
        vec = ccl_feature_vector(func)

        # 末尾 8 要素 = ccl_type_features の出力と一致すべき
        ccl_text = python_to_ccl(func)
        tf = ccl_type_features(ccl_text)
        assert vec[-8:] == tf


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
