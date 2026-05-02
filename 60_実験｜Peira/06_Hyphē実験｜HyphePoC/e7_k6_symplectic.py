#!/usr/bin/env python3
"""
E7: K₆ シンプレクティック構造検証実験

目的: HGK の 6修飾座標が形成する K₆ 上の Q-series (反対称テンソル) が
      非退化なシンプレクティック形式を定義するか検証する。

理論的背景:
  - Helmholtz 分解: f = (Γ + Q)∇φ
  - G_{ij} (X-series): 対称テンソル — 結合強度 [SOURCE: taxis.md]
  - Q_{ij} (Q-series): 反対称テンソル — 循環方向 [SOURCE: circulation_taxis.md]
  - 6次元空間上の反対称2形式 ω ∈ Λ²(R⁶)
  - ダルブーの定理: Pf(ω) ≠ 0 ⟺ 非退化 ⟺ 3共役ペア

構成原理 (アプローチ A — "理論的構成"):
  Q 行列の値を HGK 体系から演繹する:
  1. Stoicheia (S-I/S-II/S-III) が主要循環方向を決定
  2. taxis.md の張力 w が結合強度の指標 → Q の相対強度に転用
  3. circulation_taxis.md の方向定義 (Q > 0 の方向) が符号を決定
  4. d-level 階層: d2内 > d2×d3 > d3内 の序列

著者: Claude (Antigravity AI)
日時: 2026-03-15
"""

import json
import numpy as np
from pathlib import Path

# === 座標定義 ===
COORDS = ['Value', 'Function', 'Precision', 'Scale', 'Valence', 'Temporality']
COORD_ABBR = ['Va', 'Fu', 'Pr', 'Sc', 'Vl', 'Te']
N = len(COORDS)  # 6

# 座標インデックス
Va, Fu, Pr, Sc, Vl, Te = 0, 1, 2, 3, 4, 5

# d値
D_VALUES = {Va: 2, Fu: 2, Pr: 2, Sc: 3, Vl: 3, Te: 2}

# === X-series G 値 (張力 w) ===
# [SOURCE: taxis.md v4.2.0 — 操作的判定の w 値]
# 明示的に w が記載されていない辺は 3群分類の範囲から推定
G_WEIGHTS = {
    # 群 I: d2 内結合 (高: 0.3-0.6)
    (Va, Fu): 0.40,  # [推定] V×F "目的と戦略" 明示 w なし → 群 I 中間
    (Va, Pr): 0.40,  # [推定] V×P "目的と確信" 明示 w なし → 群 I 中間
    (Fu, Pr): 0.60,  # [SOURCE] "★高張力 w=0.6" (taxis.md L101)
    # 群 II: d2×d3 結合 (中: 0.3-0.5)
    (Va, Sc): 0.20,  # [SOURCE] "独立度が比較的高い w=0.2" (L147)
    (Va, Vl): 0.40,  # [推定] 半直積メタ変数 → 中程度
    (Va, Te): 0.35,  # [推定] VFE/EFE 区分 → 中程度
    (Fu, Sc): 0.30,  # [推定] 戦略と空間 → 群 II 下位
    (Fu, Vl): 0.35,  # [推定] 戦略と感情 → 群 II 中間
    (Fu, Te): 0.35,  # [推定] 戦略と時間 → 群 II 中間
    (Pr, Sc): 0.50,  # [SOURCE] "★高張力 w=0.5" (L199)
    (Pr, Vl): 0.50,  # [SOURCE] "★高張力 w=0.5" (L212)
    (Pr, Te): 0.35,  # [推定] 確信と時間 → 群 II 中間
    # 群 III: d3 内結合 (低: 0.2-0.3)
    (Sc, Vl): 0.30,  # [SOURCE] "w=0.3" (L247)
    (Sc, Te): 0.30,  # [SOURCE] "w=0.3" (L260)
    (Vl, Te): 0.20,  # [SOURCE] "w=0.2 最も独立度が高い" (L268,273)
}


def construct_Q_matrix(scale_factor: float = 1.0) -> np.ndarray:
    """
    Stoicheia + 張力 w + 循環方向から Q 行列を構成する。

    構成原理:
      |Q_{ij}| = w_{ij} × scale_factor  (張力が循環強度に比例すると仮定)
      sign(Q_{ij}) = circulation_taxis.md の方向定義

    [SOURCE: circulation_taxis.md v1.0.0]
    全 15辺で Q > 0 の方向が定義されている:
      Q1: Va→Pr (+), Q2: Va→Fu (+), Q3: Fu→Pr (+)
      Q4: Va→Sc (+), Q5: Va→Vl (+), Q6: Va→Te (+)
      Q7: Fu→Sc (+), Q8: Fu→Vl (+), Q9: Fu→Te (+)
      Q10: Pr→Sc (+), Q11: Pr→Vl (+), Q12: Pr→Te (+)
      Q13: Sc→Vl (+), Q14: Sc→Te (+), Q15: Vl→Te (+)

    注意: 全方向が "行→列" で正 → Q は上三角が全正。
    これは circulation_taxis.md の定義順 (Va,Fu,Pr,Sc,Vl,Te) が
    "情報の自然な流れ" (d=2 → d=3, 先→後) に沿っているため。
    """
    Q = np.zeros((N, N))

    # 循環方向: (i, j) で Q[i,j] > 0 — 全て "先→後" 方向が正
    # [SOURCE: circulation_taxis.md の各 Q1-Q15 定義]
    directions = [
        # 群 I: d2 内
        (Va, Pr,  +1),  # Q1: 認識が確信を形成
        (Va, Fu,  +1),  # Q2: 目的が戦略を駆動
        (Fu, Pr,  +1),  # Q3: 行動が確信を検証 ★
        # 群 II: d2×d3
        (Va, Sc,  +1),  # Q4: 目的が粒度を決定
        (Va, Vl,  +1),  # Q5: 目的が感情を方向付け
        (Va, Te,  +1),  # Q6: 目的が時間軸を設定
        (Fu, Sc,  +1),  # Q7: 戦略が規模を決定
        (Fu, Vl,  +1),  # Q8: 戦略が感情を誘導
        (Fu, Te,  +1),  # Q9: 戦略が時間を消費
        (Pr, Sc,  +1),  # Q10: 確信が視野を制約
        (Pr, Vl,  +1),  # Q11: 確信が感情を生む
        (Pr, Te,  +1),  # Q12: 確信が時間的安定性を与える
        # 群 III: d3 内
        (Sc, Vl,  +1),  # Q13: 規模が感情的反応を決める
        (Sc, Te,  +1),  # Q14: 粒度が時間スケールを決める
        (Vl, Te,  +1),  # Q15: 感情が時間方向を決める
    ]

    for i, j, sign in directions:
        w = G_WEIGHTS.get((i, j)) or G_WEIGHTS.get((j, i), 0.3)
        Q[i, j] = sign * w * scale_factor
        Q[j, i] = -sign * w * scale_factor

    return Q


def pfaffian_6x6(A: np.ndarray) -> float:
    """
    6×6 反対称行列の Pfaffian を計算する。

    Pf(A) = A[0,1]*A[2,3]*A[4,5]
           - A[0,1]*A[2,4]*A[3,5]
           + A[0,1]*A[2,5]*A[3,4]
           - A[0,2]*A[1,3]*A[4,5]
           + A[0,2]*A[1,4]*A[3,5]
           - A[0,2]*A[1,5]*A[3,4]
           + A[0,3]*A[1,2]*A[4,5]
           - A[0,3]*A[1,4]*A[2,5]
           + A[0,3]*A[1,5]*A[2,4]
           - A[0,4]*A[1,2]*A[3,5]
           + A[0,4]*A[1,3]*A[2,5]
           - A[0,4]*A[1,5]*A[2,3]
           + A[0,5]*A[1,2]*A[3,4]
           - A[0,5]*A[1,3]*A[2,4]
           + A[0,5]*A[1,4]*A[2,3]

    性質: Pf(A)² = det(A)
    """
    a = A
    pf = (
        a[0,1]*a[2,3]*a[4,5] - a[0,1]*a[2,4]*a[3,5] + a[0,1]*a[2,5]*a[3,4]
      - a[0,2]*a[1,3]*a[4,5] + a[0,2]*a[1,4]*a[3,5] - a[0,2]*a[1,5]*a[3,4]
      + a[0,3]*a[1,2]*a[4,5] - a[0,3]*a[1,4]*a[2,5] + a[0,3]*a[1,5]*a[2,4]
      - a[0,4]*a[1,2]*a[3,5] + a[0,4]*a[1,3]*a[2,5] - a[0,4]*a[1,5]*a[2,3]
      + a[0,5]*a[1,2]*a[3,4] - a[0,5]*a[1,3]*a[2,4] + a[0,5]*a[1,4]*a[2,3]
    )
    return pf


def darboux_decomposition(Q: np.ndarray):
    """
    反対称行列 Q の Darboux (正準) 分解を行う。

    反対称行列の固有値は純虚数ペア ±iλ_k (k=1,2,3)。
    各 λ_k に対応する2次元平面が共役ペア (回転面)。

    返値:
        lambdas: [λ₁, λ₂, λ₃] (降順)
        planes: [(i, j), ...] — 各回転面に最も寄与する座標ペア
    """
    # 反対称行列の固有値は純虚数
    eigvals = np.linalg.eigvals(Q)

    # 虚部を抽出し正の値のみ (|λ_k|)
    imag_parts = np.abs(eigvals.imag)
    # 重複を除去 (ペアなので N/2 個)
    lambdas_raw = sorted(imag_parts, reverse=True)
    lambdas = []
    for v in lambdas_raw:
        if v > 1e-10 and (not lambdas or abs(v - lambdas[-1]) > 1e-10):
            lambdas.append(v)

    # 共役ペアの座標帰属を推定
    # Q² の固有ベクトル分析 (Q² は対称半負定値)
    Q_sq = Q @ Q
    eigvals_sq, eigvecs_sq = np.linalg.eigh(-Q_sq)  # -Q² は半正定値

    # 固有値を降順ソート
    idx = np.argsort(eigvals_sq)[::-1]
    eigvals_sq = eigvals_sq[idx]
    eigvecs_sq = eigvecs_sq[:, idx]

    # 各回転面を同定: 隣接する固有ベクトルペア
    planes = []
    for k in range(0, min(len(lambdas) * 2, N), 2):
        v1 = eigvecs_sq[:, k]
        v2 = eigvecs_sq[:, k + 1] if k + 1 < N else np.zeros(N)

        # 各座標への寄与度
        contrib = v1**2 + v2**2

        # 上位2座標を共役ペアとして同定
        top2 = np.argsort(contrib)[-2:][::-1]
        planes.append({
            'coords': (COORDS[top2[0]], COORDS[top2[1]]),
            'coord_idx': (int(top2[0]), int(top2[1])),
            'contributions': {COORDS[c]: round(float(contrib[c]), 4) for c in range(N)},
            'eigenvalue_sq': float(eigvals_sq[k]) if k < len(eigvals_sq) else 0.0,
        })

    return lambdas, planes, eigvals_sq, eigvecs_sq


def analyze_gq_compatibility(G_sym: np.ndarray, Q: np.ndarray):
    """
    G (対称) と Q (反対称) の整合性を検証。

    Helmholtz 条件: B = G + Q, det(B) > 0 (安定性)
    交換子 [G, Q] の構造
    """
    B = G_sym + Q

    # Helmholtz 安定性
    det_B = np.linalg.det(B)
    eigvals_B = np.linalg.eigvals(B)

    # 交換子
    commutator = G_sym @ Q - Q @ G_sym
    comm_norm = np.linalg.norm(commutator, 'fro')

    # [G,Q] = 0 ⟺ G と Q が同時対角化可能
    return {
        'det_B': float(det_B),
        'eigvals_B_real': sorted([float(e.real) for e in eigvals_B], reverse=True),
        'commutator_norm': float(comm_norm),
        'commutator_relative': float(comm_norm / (np.linalg.norm(G_sym, 'fro') * np.linalg.norm(Q, 'fro') + 1e-10)),
        'is_stable': all(e.real > 0 for e in eigvals_B),
    }


def construct_G_symmetric() -> np.ndarray:
    """
    X-series の張力 w から対称行列 G を構成する。

    G_{ij} = G_{ji} = w_{ij}
    """
    G = np.zeros((N, N))
    for (i, j), w in G_WEIGHTS.items():
        G[i, j] = w
        G[j, i] = w
    return G


def main():
    print("=" * 60)
    print("E7: K₆ シンプレクティック構造検証実験")
    print("目的: 仮説 2A (K₆ 共役ペア) の検証")
    print("方法: アプローチ A (理論的構成)")
    print("=" * 60)

    # === Phase 1: Q 行列の構成 ===
    print("\n[Phase 1] Q 行列の理論的構成")
    Q = construct_Q_matrix()
    print("  Q 行列 (6×6 反対称):")
    for i in range(N):
        row = " ".join(f"{Q[i,j]:+6.3f}" for j in range(N))
        print(f"    {COORD_ABBR[i]}: {row}")

    # 反対称性の検証
    assert np.allclose(Q, -Q.T), "Q は反対称でない！"
    print("  ✓ 反対称性確認済み")

    # === Phase 2: Pfaffian 計算 ===
    print("\n[Phase 2] Pfaffian 非退化性検証")
    pf = pfaffian_6x6(Q)
    det_Q = np.linalg.det(Q)
    print(f"  Pf(Q) = {pf:.6f}")
    print(f"  det(Q) = {det_Q:.6f}")
    print(f"  Pf(Q)² = {pf**2:.6f}")
    print(f"  |Pf(Q)² - det(Q)| = {abs(pf**2 - det_Q):.2e}")

    if abs(pf) > 1e-10:
        print(f"  ✅ Pf(Q) ≠ 0 → Q は非退化 → シンプレクティック形式が存在する！")
        is_nondegenerate = True
    else:
        print(f"  ❌ Pf(Q) ≈ 0 → Q は退化 → 完全なシンプレクティック構造は成立しない")
        is_nondegenerate = False

    # === Phase 3: Darboux 分解 ===
    print("\n[Phase 3] Darboux 基底 (共役ペア) の同定")
    lambdas, planes, eigvals_sq, eigvecs_sq = darboux_decomposition(Q)

    print(f"  回転周波数 (λ_k): {[round(l, 4) for l in lambdas]}")
    if len(lambdas) >= 2:
        print(f"  λ₁/λ₂ 比率: {lambdas[0]/lambdas[1]:.2f}")
    if len(lambdas) >= 3:
        print(f"  λ₁/λ₃ 比率: {lambdas[0]/lambdas[2]:.2f}")

    print(f"\n  共役ペア (回転面):")
    for k, plane in enumerate(planes):
        print(f"    Π_{k+1}: {plane['coords'][0]} ↔ {plane['coords'][1]}")
        print(f"         λ² = {plane['eigenvalue_sq']:.4f}")
        top_contribs = sorted(plane['contributions'].items(), key=lambda x: x[1], reverse=True)
        print(f"         寄与: {', '.join(f'{c}={v:.3f}' for c, v in top_contribs[:3])}")

    # === Phase 4: Stoicheia 対応の検証 ===
    print("\n[Phase 4] Stoicheia 対応の検証")
    stoicheia_pairs = {
        'S-I (Γ:Value, Q:Precision)': (Va, Pr),
        'S-II (Γ:Function, Q:Flow→?)': (Fu, None),
        'S-III (Γ:Precision, Q:Value)': (Pr, Va),
    }

    for name, (i, j) in stoicheia_pairs.items():
        if j is not None:
            # 回転面で (i,j) が同じペアに入っているか確認
            found = False
            for k, plane in enumerate(planes):
                ci, cj = plane['coord_idx']
                if (ci == i and cj == j) or (ci == j and cj == i):
                    print(f"  ✅ {name} → 回転面 Π_{k+1} に対応")
                    found = True
                    break
            if not found:
                print(f"  ⚠️ {name} → 単一回転面に収まっていない")
                # どの面に分散しているか確認
                for k, plane in enumerate(planes):
                    ci, cj = plane['coord_idx']
                    if ci == i or cj == i or ci == j or cj == j:
                        print(f"       → 部分的に Π_{k+1} ({plane['coords']}) に含まれる")

    # === Phase 5: G-Q 整合性 ===
    print("\n[Phase 5] G-Q 整合性検証")
    G_sym = construct_G_symmetric()
    compat = analyze_gq_compatibility(G_sym, Q)

    print(f"  det(G+Q) = {compat['det_B']:.6f}")
    print(f"  B=G+Q の固有値 (実部): {[round(v, 4) for v in compat['eigvals_B_real']]}")
    print(f"  ||[G,Q]||_F = {compat['commutator_norm']:.4f}")
    print(f"  ||[G,Q]||_F / (||G||·||Q||) = {compat['commutator_relative']:.4f}")
    if compat['is_stable']:
        print(f"  ✅ B = G + Q は安定 (全実部 > 0)")
    else:
        print(f"  ⚠️ B = G + Q に不安定固有値あり")

    # === Phase 6: 特異構造の分析 ===
    print("\n[Phase 6] 構造解析")

    # Q 行列の全方向が正 → 何を意味するか
    print("  Q の構造的特徴:")
    print(f"    上三角が全て正 → 座標順 (Va,Fu,Pr,Sc,Vl,Te) が情報流の自然順序")
    print(f"    これは座標の d 値 (d=2→d=3) と一致する「カスケード構造」")

    # Pfaffian の絶対値の解釈
    if is_nondegenerate:
        print(f"\n  ★ シンプレクティック体積 = |Pf(Q)| = {abs(pf):.6f}")
        print(f"    → K₆ 上の認知空間は非退化な向き付けを持つ")
        print(f"    → ダルブーの定理により 3 共役ペアが存在する")

    # === 結果保存 ===
    output_path = Path.home() / "Sync/oikos/01_ヘゲモニコン｜Hegemonikon/60_実験｜Peira/06_Hyphē実験｜HyphePoC/e7_k6_symplectic.json"

    results = {
        'experiment': 'e7_k6_symplectic',
        'approach': 'A_theoretical',
        'Q_matrix': Q.tolist(),
        'G_matrix': G_sym.tolist(),
        'pfaffian': float(pf),
        'det_Q': float(det_Q),
        'is_nondegenerate': is_nondegenerate,
        'rotation_frequencies': [float(l) for l in lambdas],
        'conjugate_pairs': [
            {'coords': p['coords'], 'eigenvalue_sq': p['eigenvalue_sq'],
             'contributions': p['contributions']}
            for p in planes
        ],
        'gq_compatibility': compat,
        'G_weights': {f"{COORD_ABBR[i]}-{COORD_ABBR[j]}": w for (i,j), w in G_WEIGHTS.items()},
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n  結果保存: {output_path}")

    # === 最終判定 ===
    print("\n" + "=" * 60)
    print("最終判定")
    print("=" * 60)
    if is_nondegenerate:
        print(f"  ✅ K₆ はシンプレクティック構造を持つ")
        print(f"  ✅ Pf(Q) = {pf:.6f} ≠ 0")
        print(f"  ✅ 3 共役ペア (回転面) が同定された:")
        for k, plane in enumerate(planes):
            lk = lambdas[k] if k < len(lambdas) else 0
            print(f"     Π_{k+1}: {plane['coords'][0]} ↔ {plane['coords'][1]} (λ={lk:.4f})")
        dominance = lambdas[0] / lambdas[-1] if len(lambdas) >= 2 and lambdas[-1] > 0 else float('inf')
        print(f"  支配度 (λ₁/λ₃): {dominance:.2f}")
        print(f"  → 仮説 2A 支持: K₆ のシンプレクティック構造が存在し、")
        print(f"    支配的ペアが k_signal の低次元性に寄与する可能性")
    else:
        print(f"  ❌ K₆ は完全なシンプレクティック構造を持たない")
        print(f"  → 仮説 2A は現在の Q 構成では棄却")


if __name__ == '__main__':
    main()
