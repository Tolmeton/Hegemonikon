# PROOF: [L3/テスト] <- hermeneus/tests/test_ccl_normalizer.py CCL Input Normalizer ユニットテスト
"""
CCL Input Normalizer Tests

- /ccl-xxx -> @xxx への正規化
- →, ⟹, ⇒ から _ へのシーケンス演算子正規化
"""

import pytest
from hermeneus.src.ccl_normalizer import normalize_ccl_input, is_ccl_macro, parse_ccl_macro

class TestCCLNormalizer:
    
    def test_normalize_ccl_input_macro(self):
        """マクロの正規化テスト"""
        assert normalize_ccl_input("/ccl-plan") == "@plan"
        assert normalize_ccl_input("/ccl-plan-") == "@plan-"
        assert normalize_ccl_input("/ccl-dig+") == "@dig+"
        assert normalize_ccl_input("/ccl-cross-review") == "@cross-review"
        
        # 変換不要
        assert normalize_ccl_input("/noe+") == "/noe+"
        assert normalize_ccl_input("@plan") == "@plan"

    def test_normalize_ccl_input_unicode_arrows(self):
        """Unicode 矢印の正規化テスト"""
        assert normalize_ccl_input("/ops → /dio") == "/ops _ /dio"
        assert normalize_ccl_input("/ops ⟹ /dio") == "/ops _ /dio"
        assert normalize_ccl_input("/ops ⇒ /dio") == "/ops _ /dio"
        
        # 複合 (全体がマクロ指定じゃない場合はマクロ変換されないのが現在の正規表現 ^...$ の仕様)
        assert normalize_ccl_input("/ccl-ops → /dio") == "/ccl-ops _ /dio"

    def test_is_ccl_macro(self):
        """マクロ判定テスト"""
        assert is_ccl_macro("/ccl-plan") is True
        assert is_ccl_macro("/ccl-plan+") is True
        assert is_ccl_macro("@plan") is True
        assert is_ccl_macro("@plan-") is True
        
        # マクロではない
        assert is_ccl_macro("/noe") is False
        assert is_ccl_macro("/dia+") is False
        
    def test_parse_ccl_macro(self):
        """マクロ分解テスト"""
        assert parse_ccl_macro("/ccl-plan") == ("plan", "")
        assert parse_ccl_macro("/ccl-plan-") == ("plan", "-")
        assert parse_ccl_macro("/ccl-dig+") == ("dig", "+")
        assert parse_ccl_macro("@plan") == ("plan", "")
        assert parse_ccl_macro("@dig+") == ("dig", "+")
        
        # マクロではない
        assert parse_ccl_macro("/noe") is None
        assert parse_ccl_macro("/noe+") is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
