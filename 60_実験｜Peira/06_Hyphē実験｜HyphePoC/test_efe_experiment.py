"""v0.4 EFE 弁別力検証 — pytest 経由のシンセティック実験。"""
import random
from hyphe_chunker import (
    Step, chunk_session, compute_lambda_schedule, _l2_normalize,
)


def _make_session(n=12, dim=16, topics=3):
    """トピックごとにクラスタ化されたシンセティックセッションを生成。"""
    random.seed(42)
    steps, embs = [], []
    sz = n // topics
    for t in range(topics):
        center = _l2_normalize([random.gauss(0, 1) for _ in range(dim)])
        for j in range(sz):
            noise = 0.1 + 0.05 * t
            vec = _l2_normalize([c + random.gauss(0, noise) for c in center])
            embs.append(vec)
            steps.append(Step(index=t * sz + j, text=f"Topic {t} step {j}: " + "x" * 50))
    return steps, embs


class TestEFEDiscrimination:
    """v0.4 EFE 弁別力のシンセティック検証。"""

    def test_multi_tau_efe(self):
        """複数 τ で EFE メトリクスが計算できることを確認。"""
        steps, embs = _make_session()
        results = {}
        for tau in [0.50, 0.70, 0.90]:
            r = chunk_session(
                steps, embs, tau=tau, min_steps=2,
                max_iterations=3, auto_lambda=True,
            )
            m = r.metrics
            results[tau] = m
            assert m["num_chunks"] >= 1
            assert 0.0 <= m["mean_coherence"] <= 1.0
            assert m["mean_epistemic"] >= 0.0
            assert m["mean_pragmatic"] >= 0.0
            assert m["mean_efe"] >= 0.0

        # 結果を表示 (pytest -s で確認可能)
        print("\n--- v0.4 EFE 弁別力シンセティック実験 ---")
        print(f"{'tau':>5} {'ch':>3} {'coh':>6} {'drift':>6} {'epi':>7} {'prag':>7} "
              f"{'efe':>7} {'L':>7} {'V(efe)':>9} {'λ1':>5} {'λ2':>5}")
        print("-" * 80)
        for tau in [0.50, 0.70, 0.90]:
            m = results[tau]
            l1, l2 = compute_lambda_schedule(tau)
            print(f"{tau:.2f} {m['num_chunks']:3d} {m['mean_coherence']:6.3f} "
                  f"{m['mean_drift']:6.3f} {m['mean_epistemic']:7.4f} "
                  f"{m['mean_pragmatic']:7.4f} {m['mean_efe']:7.4f} "
                  f"{m['mean_loss']:7.4f} {m['efe_var']:9.6f} "
                  f"{l1:5.3f} {l2:5.3f}")

    def test_lambda_schedule_varies(self):
        """λ₁, λ₂ が τ に応じて変化することを確認。"""
        l1_50, l2_50 = compute_lambda_schedule(0.50)
        l1_90, l2_90 = compute_lambda_schedule(0.90)
        # 高τ → λ₁↓ (Drift 軽視), λ₂↑ (EFE 重視)
        assert l1_90 < l1_50, f"λ₁: τ=0.9({l1_90}) should < τ=0.5({l1_50})"
        assert l2_90 > l2_50, f"λ₂: τ=0.9({l2_90}) should > τ=0.5({l2_50})"

    def test_coherence_invariance(self):
        """シンセティックデータでの Coherence Invariance 傾向チェック。"""
        steps, embs = _make_session()
        cohs = []
        for tau in [0.50, 0.70, 0.90]:
            r = chunk_session(steps, embs, tau=tau, min_steps=2, max_iterations=3)
            cohs.append(r.metrics["mean_coherence"])

        coh_range = max(cohs) - min(cohs)
        print(f"\nCoherence range: {coh_range:.4f}")
        # シンセティックでは不変量は弱いが 0.3 以下を期待
        assert coh_range < 0.3, f"Coherence range {coh_range:.4f} が大きすぎる"
