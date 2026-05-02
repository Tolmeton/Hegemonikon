#!/usr/bin/env python3
"""
E7b: Q 行列の理論的構成法の比較

問題: |Q_{ij}| = w_{ij} (方法A) は Pf(Q) = 0.00425 と微小で、
      ±20% 摂動で符号保存率 56.7%。構造的に頑健ではない。

原因分析:
  G (結合強度, 対称) と Q (循環強度, 反対称) は同じ K₆ 辺に定義されるが
  測定する量が異なる:
    G = スプリング定数 (均衡的結合の強さ)
    Q = 確率流束 (非均衡的循環の方向と強さ)

  |Q| = |G| は「結合が強い辺ほど循環も強い」と仮定するが、
  物理的には Q は G とは独立に決まる:
    Q = B - Γ  (NESS: drift B から dissipative Γ を引いた残り)

代替構成法:
  B: Stoicheia 構造 — 3原理が定める循環の階層
  C: d-level 階層 — d値の組合せで Q の強度を決定
  D: Lyapunov 導出 — NESS 条件から Q を逆算
  E: 認知サイクル — Va→Fu→Pr の循環を基底とする構成

[SOURCE: circulation_taxis.md, taxis.md, episteme-entity-map.md, episteme-fep-lens.md]
"""
import random
import math

# === 座標定義 ===
Va, Fu, Pr, Sc, Vl, Te = 0, 1, 2, 3, 4, 5
N = 6
ABBR = ['Va', 'Fu', 'Pr', 'Sc', 'Vl', 'Te']
D_VAL = {Va:2, Fu:2, Pr:2, Sc:3, Vl:3, Te:2}  # d 値

# 全 15辺の方向 (circulation_taxis.md — 全て先→後で正)
DIRS = [
    (Va,Pr,+1),(Va,Fu,+1),(Fu,Pr,+1),
    (Va,Sc,+1),(Va,Vl,+1),(Va,Te,+1),
    (Fu,Sc,+1),(Fu,Vl,+1),(Fu,Te,+1),
    (Pr,Sc,+1),(Pr,Vl,+1),(Pr,Te,+1),
    (Sc,Vl,+1),(Sc,Te,+1),(Vl,Te,+1),
]

# X-series 張力 [SOURCE: taxis.md]
G_W = {
    (Va,Fu):0.40,(Va,Pr):0.40,(Fu,Pr):0.60,
    (Va,Sc):0.20,(Va,Vl):0.40,(Va,Te):0.35,
    (Fu,Sc):0.30,(Fu,Vl):0.35,(Fu,Te):0.35,
    (Pr,Sc):0.50,(Pr,Vl):0.50,(Pr,Te):0.35,
    (Sc,Vl):0.30,(Sc,Te):0.30,(Vl,Te):0.20,
}

def pf6(a):
    """6×6 反対称行列の Pfaffian"""
    return (
        a[0][1]*a[2][3]*a[4][5]-a[0][1]*a[2][4]*a[3][5]+a[0][1]*a[2][5]*a[3][4]
       -a[0][2]*a[1][3]*a[4][5]+a[0][2]*a[1][4]*a[3][5]-a[0][2]*a[1][5]*a[3][4]
       +a[0][3]*a[1][2]*a[4][5]-a[0][3]*a[1][4]*a[2][5]+a[0][3]*a[1][5]*a[2][4]
       -a[0][4]*a[1][2]*a[3][5]+a[0][4]*a[1][3]*a[2][5]-a[0][4]*a[1][5]*a[2][3]
       +a[0][5]*a[1][2]*a[3][4]-a[0][5]*a[1][3]*a[2][4]+a[0][5]*a[1][4]*a[2][3]
    )

def mkQ(weights):
    """重み辞書から Q 行列を構成"""
    Q = [[0.0]*N for _ in range(N)]
    for i,j,s in DIRS:
        w = weights.get((i,j)) or weights.get((j,i),0.0)
        Q[i][j] = s*w; Q[j][i] = -s*w
    return Q

def robustness_test(weights, delta=0.2, trials=5000):
    """摂動頑健性テスト。Pf>0 の割合を返す"""
    pos = 0
    for _ in range(trials):
        pw = {k: v*(1+random.uniform(-delta,delta)) for k,v in weights.items()}
        if pf6(mkQ(pw)) > 0: pos += 1
    return pos / trials

# ============================================================
# 構成法の定義
# ============================================================

def method_A():
    """方法 A: |Q| = w (現行)"""
    return dict(G_W)

def method_B():
    """方法 B: Stoicheia 構造
    
    3 Stoicheia が定める循環の階層:
      S-I  (Γ:Va, Q:Pr) → Va-Pr 面が S-I の作用面
      S-III (Γ:Pr, Q:Va) → Pr-Va 面が S-III の作用面 (S-I の逆)
      S-II (Γ:Fu, Q:Flow) → Fu は K₆ 内で Function として現れる
    
    原理: 
      Stoicheia の Γ/Q 割当に直接関わる辺 → 強 (0.8)
      Stoicheia の Γ/Q の一方に関わる辺 → 中 (0.4)
      Stoicheia に関わらない辺 → 弱 (0.15)
    
    [SOURCE: episteme-entity-map.md の Stoicheia 定義]
    """
    weights = {}
    
    # Stoicheia 直接関与座標
    stoicheia_coords = {Va, Fu, Pr}  # S-I/S-II/S-III の Γ/Q 座標
    
    for i,j,_ in DIRS:
        both_core = (i in stoicheia_coords) and (j in stoicheia_coords)
        one_core = (i in stoicheia_coords) or (j in stoicheia_coords)
        
        if both_core:
            # S-I/S-III: Va↔Pr, S-II 的: Fu↔Va, Fu↔Pr
            # Va-Pr は S-I+S-III の直接対象 → 最強
            if (i,j) == (Va,Pr) or (i,j) == (Pr,Va):
                weights[(i,j)] = 0.9
            # Fu-Pr は Explore/Exploit + Precision の核心循環
            elif (i,j) == (Fu,Pr) or (i,j) == (Pr,Fu):
                weights[(i,j)] = 0.8
            else:  # Va-Fu
                weights[(i,j)] = 0.7
        elif one_core:
            weights[(i,j)] = 0.35
        else:
            weights[(i,j)] = 0.10
    
    return weights

def method_C():
    """方法 C: d-level 階層導出
    
    原理: Q の強度は座標ペアの d-level の組合せで決まる。
    d 値が低い (= VFE に近い) ほど非均衡度が高く、循環が強い。
    
    Q_{ij} = c(d_i, d_j) × direction
    
    c(2,2) = α (核心パラメータ間 — 最大循環)
    c(2,3) = β (核心 × 修飾 — 中程度)  
    c(3,3) = γ (修飾間 — 最小)
    
    α > β > γ の序列は FEP から演繹的。
    比率: α:β:γ を自由パラメータとして走査する。
    """
    weights = {}
    for i,j,_ in DIRS:
        di, dj = D_VAL[i], D_VAL[j]
        pair = tuple(sorted([di, dj]))
        if pair == (2,2):
            weights[(i,j)] = 0.7  # α
        elif pair == (2,3):
            weights[(i,j)] = 0.3  # β
        else:  # (3,3)
            weights[(i,j)] = 0.1  # γ
    return weights

def method_D():
    """方法 D: 認知サイクル基底
    
    原理: 認知の核心循環は Va→Fu→Pr→Va の三角循環。
    これは「目的→戦略→確信→(新たな)目的」のループ。
    
    Q を 3つの独立な回転生成子の線形結合として構成:
      J₁: Va ↔ Fu 面の回転 (目的-戦略循環)
      J₂: Fu ↔ Pr 面の回転 (戦略-確信循環)  
      J₃: Va ↔ Pr 面の回転 (目的-確信循環)
    
    ω₁, ω₂, ω₃ は各循環の回転速度。
    
    d3 座標 (Sc, Vl, Te) への波及は、d2 座標との結合で
    「引きずられる」形で発生する → F2 関手的構成。
    """
    weights = {}
    
    # 核心三角: Va→Fu→Pr→Va
    omega = {
        (Va,Fu): 0.6,   # ω₁: 目的→戦略
        (Fu,Pr): 0.8,   # ω₂: 戦略→確信 (最も動的 — Explore/Exploit)
        (Va,Pr): 0.7,   # ω₃: 目的→確信 (S-I/S-III)
    }
    
    # 核心辺
    for (i,j), w in omega.items():
        weights[(i,j)] = w
    
    # d2→d3 への波及: 各 d2 座標からの「引きずり」
    # 波及強度 = 元の循環の 30-40%
    d3_coords = [Sc, Vl, Te]
    d2_coords = [Va, Fu, Pr]
    
    for d2 in d2_coords:
        # d2 座標が持つ循環の平均強度
        d2_circ = sum(omega.get((d2,j), omega.get((j,d2), 0)) for j in d2_coords if j != d2) / 2
        for d3 in d3_coords:
            weights[(d2, d3)] = d2_circ * 0.35  # 35% 波及
    
    # d3-d3: 最も弱い。d2 からの間接的波及
    for idx_a, a in enumerate(d3_coords):
        for b in d3_coords[idx_a+1:]:
            weights[(a,b)] = 0.05  # ほぼ無循環
    
    return weights

def method_E():
    """方法 E: NESS ε-展開
    
    原理: 均衡状態 (Q=0) からの非均衡パラメータ ε による展開。
    
    Q = ε₁ Q₁ + ε₂ Q₂ + ε₃ Q₃
    
    Q₁: d2 内循環 (3辺) の生成子
    Q₂: d2×d3 循環 (9辺) の生成子  
    Q₃: d3 内循環 (3辺) の生成子
    
    ε₁ >> ε₂ >> ε₃ (非均衡度の階層)
    
    各 Q_k 内では全辺均等 (群内の対称性仮定)。
    """
    weights = {}
    eps = {(2,2): 0.8, (2,3): 0.25, (3,3): 0.05}
    
    for i,j,_ in DIRS:
        di, dj = D_VAL[i], D_VAL[j]
        pair = tuple(sorted([di, dj]))
        weights[(i,j)] = eps[pair]
    
    return weights

# ============================================================
# テスト実行
# ============================================================

random.seed(42)
methods = {
    'A: |Q|=w (現行)': method_A,
    'B: Stoicheia構造': method_B,
    'C: d-level階層': method_C,
    'D: 認知サイクル': method_D,
    'E: NESS ε-展開': method_E,
}

print("="*70)
print("E7b: Q 行列の理論的構成法の比較")
print("="*70)

results = {}
for name, fn in methods.items():
    w = fn()
    Q = mkQ(w)
    p = pf6(Q)
    
    # 頑健性テスト
    r20 = robustness_test(w, 0.2, 5000)
    r50 = robustness_test(w, 0.5, 5000)
    
    # 方向反転テスト
    flips = 0
    for idx in range(15):
        fd = list(DIRS)
        i,j,s = fd[idx]; fd[idx] = (i,j,-s)
        Qf = [[0.0]*N for _ in range(N)]
        for ii,jj,ss in fd:
            wv = w.get((ii,jj)) or w.get((jj,ii),0.0)
            Qf[ii][jj] = ss*wv; Qf[jj][ii] = -ss*wv
        if pf6(Qf) > 0: flips += 1
    
    results[name] = {'pf': p, 'r20': r20, 'r50': r50, 'flips': flips}

# 結果表示
print(f"\n{'構成法':<24s} {'Pf(Q)':>12s} {'±20%保存':>10s} {'±50%保存':>10s} {'方向保存':>8s}")
print("-"*70)
for name, r in results.items():
    pf_str = f"{r['pf']:.6f}"
    r20_str = f"{r['r20']*100:.1f}%"
    r50_str = f"{r['r50']*100:.1f}%"
    flip_str = f"{r['flips']}/15"
    marker = " ★" if r['r20'] > 0.9 else ""
    print(f"  {name:<22s} {pf_str:>12s} {r20_str:>10s} {r50_str:>10s} {flip_str:>8s}{marker}")

# 最良の方法の詳細
best_name = max(results, key=lambda k: results[k]['r20'])
best = results[best_name]
print(f"\n最も頑健: {best_name}")
print(f"  Pf = {best['pf']:.6f}, ±20% 保存率 = {best['r20']*100:.1f}%")

# 方法 Dの詳細 (認知サイクル)
print(f"\n--- 方法 D (認知サイクル) の Q 行列 ---")
w_D = method_D()
Q_D = mkQ(w_D)
for i in range(N):
    row = " ".join(f"{Q_D[i][j]:+6.3f}" for j in range(N))
    print(f"  {ABBR[i]}: {row}")

# 方法 C の α:β:γ 最適化
print(f"\n--- 方法 C: α:β:γ 比率の走査 ---")
best_c_r20 = 0
best_c_params = None
for alpha_10 in range(3, 10):     # α: 0.3-0.9
    for beta_10 in range(1, alpha_10):  # β < α
        for gamma_10 in range(1, beta_10):  # γ < β
            alpha = alpha_10 / 10.0
            beta = beta_10 / 10.0
            gamma = gamma_10 / 10.0
            wc = {}
            for i,j,_ in DIRS:
                di, dj = D_VAL[i], D_VAL[j]
                pair = tuple(sorted([di, dj]))
                if pair == (2,2): wc[(i,j)] = alpha
                elif pair == (2,3): wc[(i,j)] = beta
                else: wc[(i,j)] = gamma
            p = pf6(mkQ(wc))
            if abs(p) > 1e-10:
                r = robustness_test(wc, 0.2, 1000)
                if r > best_c_r20:
                    best_c_r20 = r
                    best_c_params = (alpha, beta, gamma, p)

if best_c_params:
    a, b, g, p = best_c_params
    print(f"  最適 α={a:.1f}, β={b:.1f}, γ={g:.1f}")
    print(f"  Pf = {p:.6f}, ±20% 保存率 = {best_c_r20*100:.1f}%")
else:
    print(f"  有効な組合せなし")

# α:β:γ の比率の意味
print(f"\n--- 理論的考察 ---")
print(f"  G (均衡的結合) と Q (非均衡的循環) は独立に定義されるべき:")
print(f"  G: 2座標がどれくらい影響し合うか (スプリング定数)")
print(f"  Q: 定常状態で確率流束がどちら向きに流れるか (電流)")
print(f"  |Q| = |G| は「スプリングが強い = 電流が強い」と仮定するに等しい")
print(f"  より正しい関係: Q = B - Γ (NESS drift から散逸を引いた残り)")
print(f"  → Q の強度は「系がどれだけ非均衡か」に依存する")
print(f"  → d2 座標間 (VFE 核心) が最も非均衡 → Q が最大")

print("\n" + "="*70)
