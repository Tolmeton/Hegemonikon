# PROOF: [L3/テスト] <- hermeneus/tests/test_verifier_integration.py 統合テスト
"""
Hermēneus Verifier Integration Tests — Convergent Debate

実際の LLM (Cortex API) を使って収束型ラリーを実行し、
ラリーの質・収束挙動・レイテンシを観察する。

前提: Cortex API が認証済みであること
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermeneus.src.verifier import (
    AgentRole,
    DebateAgent,
    DebateEngine,
    ConvergenceDetector,
)


def check_cortex_available() -> bool:
    """Cortex API が利用可能か確認"""
    try:
        from mekhane.ochema.service import OchemaService
        svc = OchemaService.get()
        return svc.cortex_available
    except Exception as e:
        print(f"⚠️  Cortex API 未接続: {e}")
        return False


_cortex_available = check_cortex_available()
_skip_no_cortex = pytest.mark.skipif(not _cortex_available, reason="Cortex API 未接続")


@pytest.mark.asyncio
@_skip_no_cortex
async def test_single_agent_generate():
    """単一エージェントの LLM 生成テスト"""
    print("\n" + "=" * 60)
    print("Test 1: 単一エージェント LLM 生成")
    print("=" * 60)
    
    agent = DebateAgent(AgentRole.PROPOSER)
    
    start = time.time()
    turn = await agent.respond(
        claim="FEP (Free Energy Principle) は認知科学の統一理論として有効である",
        rally_history=[],
        context="Hegemonikón は FEP に基づく認知ハイパーバイザーフレームワーク",
    )
    elapsed = time.time() - start
    
    print(f"\n📝 @Proposer (Turn {turn.turn_number}):")
    print(f"   確信度: {turn.confidence:.2f}")
    print(f"   レイテンシ: {elapsed:.1f}s")
    print(f"   内容 (先頭200字):\n   {turn.content[:200]}...")
    
    assert turn.speaker == AgentRole.PROPOSER
    assert len(turn.content) > 10, "応答が短すぎる"
    assert turn.confidence > 0, "確信度が0"
    
    print("   ✅ passed")
    return turn


@pytest.mark.asyncio
@_skip_no_cortex
async def test_two_agent_rally():
    """Proposer ↔ Critic のラリーテスト (3ターン)"""
    print("\n" + "=" * 60)
    print("Test 2: Proposer ↔ Critic ラリー (3ターン)")
    print("=" * 60)
    
    proposer = DebateAgent(AgentRole.PROPOSER)
    critic = DebateAgent(AgentRole.CRITIC)
    
    claim = "CCL の収束型ラリー (~*) は単発ラウンドより検証精度が高い"
    context = "Multi-Agent Debate for LLM validation"
    
    rally_history = []
    total_start = time.time()
    
    for turn_idx in range(3):
        agent = proposer if turn_idx % 2 == 0 else critic
        role_name = "@Proposer" if turn_idx % 2 == 0 else "@Critic"
        
        start = time.time()
        turn = await agent.respond(claim, rally_history, context)
        elapsed = time.time() - start
        
        rally_history.append(turn)
        
        print(f"\n📝 {role_name} (Turn {turn.turn_number}):")
        print(f"   確信度: {turn.confidence:.2f}")
        print(f"   レイテンシ: {elapsed:.1f}s")
        print(f"   内容 (先頭150字):\n   {turn.content[:150]}...")
    
    total_elapsed = time.time() - total_start
    
    # 収束判定を試行
    converged, reason = ConvergenceDetector.check(rally_history, min_turns=3)
    
    print(f"\n📊 ラリー統計:")
    print(f"   総ターン数: {len(rally_history)}")
    print(f"   総レイテンシ: {total_elapsed:.1f}s")
    print(f"   平均レイテンシ: {total_elapsed / len(rally_history):.1f}s/turn")
    print(f"   収束判定: {'✅ 収束' if converged else '❌ 未収束'}")
    if reason:
        print(f"   理由: {reason}")
    
    # 検証: ラリー履歴の引用が行われているか
    for turn in rally_history[1:]:
        has_reference = any(
            keyword in turn.content
            for keyword in ["@Proposer", "@Critic", "指摘", "反論", "主張", "批判"]
        )
        print(f"   Turn {turn.turn_number} 文脈参照: {'✅' if has_reference else '⚠️ 弱い'}")
    
    print("   ✅ passed")
    return rally_history


@pytest.mark.asyncio
@_skip_no_cortex
async def test_full_debate():
    """フル debate エンジンテスト (ラリー + Arbiter)"""
    print("\n" + "=" * 60)
    print("Test 3: フル Debate エンジン (ラリー + Arbiter)")
    print("=" * 60)
    
    engine = DebateEngine()
    
    claim = "Hegemonikón の 24 定理体系は FEP から数学的に導出可能である"
    context = (
        "Hegemonikón は 1公理 (FEP) + 7座標 + 36動詞 + 15結合規則の体系。"
        "数学的導出は距離 d=0,1,2 で配置されている。"
    )
    
    start = time.time()
    result = await engine.debate(
        claim=claim,
        context=context,
        max_rounds=1,
        max_rally_turns=4,
        min_rally_turns=3,
    )
    elapsed = time.time() - start
    
    print(f"\n🏛️ Debate 結果:")
    print(f"   判定: {'✅ ACCEPT' if result.accepted else '❌ REJECT'}")
    print(f"   確信度: {result.confidence:.2f}")
    print(f"   ラウンド数: {len(result.rounds)}")
    
    if result.rounds:
        r = result.rounds[0]
        print(f"   ラリーターン数: {len(r.rally)}")
        print(f"   収束: {'✅' if r.converged else '❌'} ({r.convergence_reason})")
    
    print(f"   総レイテンシ: {elapsed:.1f}s")
    print(f"   メタデータ: {result.metadata}")
    
    if result.dissent_reasons:
        print(f"   反対理由:")
        for dr in result.dissent_reasons:
            print(f"     - {dr}")
    
    # ラリーの各ターンをダンプ
    if result.rounds:
        print(f"\n📜 ラリー履歴:")
        for turn in result.rounds[0].rally:
            role_label = {
                AgentRole.PROPOSER: "@Proposer",
                AgentRole.CRITIC: "@Critic",
                AgentRole.ARBITER: "@Arbiter",
            }.get(turn.speaker, "???")
            print(f"\n   --- Turn {turn.turn_number}: {role_label} (conf={turn.confidence:.2f}) ---")
            print(f"   {turn.content[:200]}...")
    
    assert result.confidence > 0, "確信度が0"
    assert len(result.rounds) > 0, "ラウンドが空"
    
    print("\n   ✅ passed")
    return result


async def main():
    print("🔬 Hermēneus Convergent Debate 統合テスト")
    print("=" * 60)
    
    # LS チェック
    if not check_cortex_available():
        print("\n❌ Cortex API が利用できません。統合テストをスキップします。")
        print("   フォールバック: LLM なしでのプレースホルダー応答を検証します。")
        
        # Fallback: LLM なしでの動作確認
        engine = DebateEngine()
        result = await engine.debate(
            claim="テスト主張",
            context="",
            max_rounds=1,
            max_rally_turns=4,
            min_rally_turns=3,
        )
        print(f"\n   フォールバック結果: accepted={result.accepted}, conf={result.confidence:.2f}")
        print(f"   ラリーターン数: {len(result.rounds[0].rally) if result.rounds else 0}")
        print("   ✅ フォールバックテスト passed")
        return
    
    print("✅ Cortex API に接続成功")
    
    results = {}
    
    # Test 1: 単一エージェント
    try:
        results["single"] = await test_single_agent_generate()
    except Exception as e:
        print(f"\n   ❌ Test 1 failed: {e}")
        results["single"] = None
    
    # Test 2: ラリー
    try:
        results["rally"] = await test_two_agent_rally()
    except Exception as e:
        print(f"\n   ❌ Test 2 failed: {e}")
        results["rally"] = None
    
    # Test 3: フル debate
    try:
        results["debate"] = await test_full_debate()
    except Exception as e:
        print(f"\n   ❌ Test 3 failed: {e}")
        results["debate"] = None
    
    # サマリー
    print("\n" + "=" * 60)
    print("📊 統合テスト サマリー")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v is not None)
    total = len(results)
    print(f"   合格: {passed}/{total}")
    
    for name, result in results.items():
        status = "✅" if result is not None else "❌"
        print(f"   {status} {name}")


if __name__ == "__main__":
    asyncio.run(main())
