#!/usr/bin/env python3
"""TensionPreScorer unit test — zero external dependencies"""
import sys
sys.path.insert(0, '.')
exec(open('hermeneus/src/ax_pipeline.py', encoding='utf-8').read())

def test_english():
    scorer = TensionPreScorer()
    data = {
        'Tel': 'The goal is to build a reliable automated analysis system.',
        'Met': 'We should use simple heuristic rules and optimization methods.',
        'Kri': 'Confidence moderate. Evidence insufficient for strong claims.',
        'Dia': 'Applies locally to the hermeneus module only.',
        'Ore': 'Desire maximum efficiency and minimal waste in processes.',
        'Chr': 'Need this completed by next week. Long-term three months.',
    }
    scores = scorer.compute(data)
    assert len(scores) == 15, f"Expected 15 scores, got {len(scores)}"
    assert all(0 <= s <= 1 for s in scores.values()), "Scores out of range"
    print(f"✅ English: {len(scores)} scores, range [{min(scores.values()):.3f}, {max(scores.values()):.3f}]")

def test_japanese():
    scorer = TensionPreScorer()
    data = {
        'Tel': '目的は信頼性の高い自動分析システムを構築し深い洞察を得ること',
        'Met': '実装にはヒューリスティックルールと勾配降下法を組み合わせる',
        'Kri': '確信度は中程度で根拠データ不十分のため強い主張に至らない',
        'Dia': '適用範囲はヘルメーネウスモジュール内の局所変更に限定',
        'Ore': '効率最大化と無駄排除を望み品質と速度のバランスが重要',
        'Chr': '来週完成必要で長期ビジョンは3ヶ月の段階リリース計画',
    }
    scores = scorer.compute(data)
    assert len(scores) == 15, f"Expected 15 scores, got {len(scores)}"
    spread = max(scores.values()) - min(scores.values())
    assert spread > 0.01, f"Spread too small: {spread:.4f}"
    print(f"✅ Japanese: {len(scores)} scores, range [{min(scores.values()):.3f}, {max(scores.values()):.3f}], spread={spread:.3f}")
    # Show top 3 and bottom 3
    top = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for (a,b),s in top[:3]: print(f"   HIGH {a}-{b}: {s:.3f}")
    for (a,b),s in top[-3:]: print(f"   LOW  {a}-{b}: {s:.3f}")

def test_edge_cases():
    scorer = TensionPreScorer()
    # Empty input
    assert scorer.compute({}) == {}
    # Single entry
    assert scorer.compute({'Tel': 'test'}) == {}
    print("✅ Edge cases: OK")

if __name__ == '__main__':
    test_english()
    test_japanese()
    test_edge_cases()
    print("\n🎉 All tests passed")
