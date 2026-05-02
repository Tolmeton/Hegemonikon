#!/usr/bin/env python3
"""
テスト: hgk_concept_loader — kernel/ → HGK 概念定義の動的生成

PURPOSE: load_hgk_concepts, compute_source_hash, check_drift,
         self_verify, _extract_kalon_definition の正常動作を検証する。
"""

import sys
from pathlib import Path

# パスを解決してインポート
_SRC_ROOT = Path(__file__).resolve().parents[1]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from mekhane.mcp.hgk_concept_loader import (
    load_hgk_concepts,
    compute_source_hash,
    check_drift,
    self_verify,
    _extract_kalon_definition,
    _KERNEL_ROOT,
    _FALLBACK_CONCEPTS,
    _DYNAMIC_SECTIONS,
    _STATIC_SECTIONS,
)


def test_normal_load():
    """正常読込: kernel/ パスから動的生成し、必須キーワードが含まれることを検証。"""
    result = load_hgk_concepts(_KERNEL_ROOT)
    assert len(result) > 0, "生成結果が空"

    # 必須キーワード
    required_keywords = [
        "Kalon",
        "Fix(G∘F)",
        "Stoicheia",
        "Poiesis",
        "CCL",
        "Nomoi",
        "FEP",
        "N-9",
        "N-1",
    ]
    missing = [kw for kw in required_keywords if kw not in result]
    assert not missing, f"必須キーワード欠落: {missing}"

    # 36動詞の CCL コマンドがいくつか抽出されているか
    ccl_cmds = ["/noe", "/bou", "/zet", "/ene", "/ske", "/sag"]
    found_cmds = [cmd for cmd in ccl_cmds if cmd in result]
    assert len(found_cmds) >= 4, f"CCL コマンド不足: found={found_cmds}"

    # 座標が抽出されているか
    coords = ["Flow", "Value", "Function", "Precision"]
    found_coords = [c for c in coords if c in result]
    assert len(found_coords) >= 3, f"座標不足: found={found_coords}"

    print(f"✅ 正常読込: {len(result)} 文字, 全必須キーワード含有")


def test_fallback():
    """フォールバック: 存在しないパスで静的定義が返ることを検証。"""
    fake_root = Path("/tmp/nonexistent_kernel_root_hgk_test")
    result = load_hgk_concepts(fake_root)
    assert result == _FALLBACK_CONCEPTS, "フォールバックが返されていない"
    assert "Kalon" in result, "フォールバックに Kalon が含まれていない"
    print("✅ フォールバック: 静的定義が正しく返却")


def test_hash_stability():
    """ハッシュ安定性: 同一ファイルで同一ハッシュを返すことを検証。"""
    h1 = compute_source_hash(_KERNEL_ROOT)
    h2 = compute_source_hash(_KERNEL_ROOT)
    assert h1 == h2, f"ハッシュ不安定: {h1} != {h2}"
    assert len(h1) == 16, f"ハッシュ長異常: {len(h1)}"
    print(f"✅ ハッシュ安定: {h1}")


def test_drift_detection():
    """ドリフト検出: 同一ハッシュで False、異なるハッシュで True を返すことを検証。"""
    current_hash = compute_source_hash(_KERNEL_ROOT)

    # 同一ハッシュ: ドリフトなし
    assert not check_drift(_KERNEL_ROOT, current_hash), "同一ハッシュでドリフト検出は誤り"

    # 異なるハッシュ: ドリフトあり
    assert check_drift(_KERNEL_ROOT, "0000000000000000"), "異なるハッシュでドリフト未検出は誤り"

    print("✅ ドリフト検出: 正常動作")


def test_output_is_formattable():
    """出力形式: 生成結果が format() テンプレートで展開可能なことを検証。"""
    result = load_hgk_concepts(_KERNEL_ROOT)
    # プロンプトテンプレートの展開をシミュレート
    template = "HGK概念:\n{hgk_concepts}\n---"
    formatted = template.format(hgk_concepts=result)
    assert "HGK概念:" in formatted
    assert "Kalon" in formatted
    print("✅ 出力形式: format() テンプレート展開成功")


def test_dynamic_vs_static_equivalence():
    """同等性: 動的生成の内容が静的フォールバックと同等の情報を含むことを検証。"""
    dynamic = load_hgk_concepts(_KERNEL_ROOT)
    static = _FALLBACK_CONCEPTS

    # 両方に共通する核心キーワード
    core_keywords = ["Kalon", "Fix(G∘F)", "Stoicheia", "Poiesis", "Nomoi", "FEP", "Dokimasia", "Hóros"]
    for kw in core_keywords:
        assert kw in dynamic, f"動的生成に {kw} が欠落"
        assert kw in static, f"静的フォールバックに {kw} が欠落"

    # 動的生成は静的より情報量が多い (36動詞の CCL コマンド等)
    assert len(dynamic) >= len(static) * 0.8, (
        f"動的生成の情報量が不足: dynamic={len(dynamic)}, static={len(static)}"
    )

    print(f"✅ 同等性: dynamic={len(dynamic)}文字, static={len(static)}文字")


# ── 新規テスト (Elenchos G∘F 修正) ──


def test_kalon_parser_extracts_from_source():
    """パーサー検証: _extract_kalon_definition が kalon.typos を実際にパースすることを検証。"""
    kalon_path = _KERNEL_ROOT / "kalon.typos"
    if not kalon_path.exists():
        print("⚠️ kalon.typos が存在しないためスキップ")
        return

    content = kalon_path.read_text(encoding="utf-8")
    result = _extract_kalon_definition(content)

    # パース結果に公理が含まれるか
    assert "Fix(G∘F)" in result, "Fix(G∘F) が抽出されていない"
    assert "καλόν" in result, "ギリシャ語名が抽出されていない"

    # フォールバックではなく実際にパースされたか
    # (パース成功時は fact_match から抽出されるので公理テキストが含まれる)
    assert "不動点" in result, "不動点の定義が抽出されていない"
    assert "操作判定" in result, "操作的判定が含まれていない"

    print(f"✅ パーサー検証: kalon.typos から {len(result)} 文字を抽出")


def test_self_verify_all_attributes():
    """自己検証: self_verify() が Kalon 三属性を全て充足することを検証。"""
    result = self_verify(_KERNEL_ROOT)

    # 三属性の検証
    assert result["fix"] is True, "Fix(G∘F) 冪等性が不成立"
    assert result["generative"] is True, "Generative (3導出以上) が不成立"
    assert result["self_referential"] is True, "Self-referential が不成立"
    assert result["kalon"] is True, "Kalon 三属性のいずれかが欠如"

    # 導出数の検証
    derivations = result["derivations"]
    assert len(derivations) >= 3, f"導出不足: {derivations}"
    assert "self_verify" in derivations, "self_verify が導出に含まれていない"

    print(f"✅ 自己検証: Kalon={result['kalon']}, 導出={derivations}")


def test_dynamic_static_ratio():
    """動的/静的比率: セクション分類が正確であることを検証。"""
    # 動的セクションの確認 (v2: SACRED_TRUTH 追加で 6/8 に拡大)
    for sect in ("kalon", "poiesis", "coordinates", "stoicheia", "nomoi", "fep"):
        assert sect in _DYNAMIC_SECTIONS, f"{sect} が動的セクションに含まれていない"

    # 静的セクションの確認 (v2: 2/8 のみ残存)
    for sect in ("dokimasia", "horos"):
        assert sect in _STATIC_SECTIONS, f"{sect} が静的セクションに含まれていない"

    # 重複がないこと
    overlap = _DYNAMIC_SECTIONS & _STATIC_SECTIONS
    assert len(overlap) == 0, f"動的/静的に重複: {overlap}"

    # 比率の計算: 6/8 = 0.75
    total = len(_DYNAMIC_SECTIONS) + len(_STATIC_SECTIONS)
    dynamic_ratio = len(_DYNAMIC_SECTIONS) / total
    assert 0.7 <= dynamic_ratio <= 0.8, f"動的比率異常: {dynamic_ratio:.2f}"

    print(f"✅ 動的/静的比率: {dynamic_ratio:.2f} ({len(_DYNAMIC_SECTIONS)}:{len(_STATIC_SECTIONS)})")


def test_sacred_truth_parsers():
    """SACRED_TRUTH.md パーサー: Stoicheia/Nomoi/FEP が動的に抽出されること。"""
    concepts = load_hgk_concepts()

    # Stoicheia の S-I, S-II, S-III が含まれている
    assert "S-I" in concepts, "S-I が出力に含まれていない"
    assert "S-II" in concepts, "S-II が出力に含まれていない"
    assert "S-III" in concepts, "S-III が出力に含まれていない"

    # Nomoi の N-1 〜 N-12 が含まれている
    for n in range(1, 13):
        assert f"N-{n}" in concepts, f"N-{n} が出力に含まれていない"

    # FEP が含まれている
    assert "FEP" in concepts, "FEP が概念出力に含まれていない"
    assert "予測誤差最小化" in concepts, "FEP の定義テキストが出力に含まれていない"

    print("✅ SACRED_TRUTH パーサー: Stoicheia/Nomoi/FEP 動的抽出確認")


if __name__ == "__main__":
    tests = [
        test_normal_load,
        test_fallback,
        test_hash_stability,
        test_drift_detection,
        test_output_is_formattable,
        test_dynamic_vs_static_equivalence,
        test_kalon_parser_extracts_from_source,
        test_self_verify_all_attributes,
        test_dynamic_static_ratio,
        test_sacred_truth_parsers,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"結果: {passed} passed, {failed} failed / {len(tests)} total")
    sys.exit(0 if failed == 0 else 1)

