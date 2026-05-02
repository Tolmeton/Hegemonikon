#!/usr/bin/env python3
"""
E7c: Q 構成法の最終形 — 方法 C+D ハイブリッド

設計原理:
  方法 C の d-level 階層 (構造的頑健性) 
    + 方法 D の認知サイクル非均質性 (意味的豊かさ)
    = ハイブリッド構成

具体的には:
  1. d-level 階層で Q の大域的スケールを決定 (α > β > γ)
  2. d2-d2 辺内の非均質性を認知サイクル Va→Fu→Pr→Va で設定
  3. d2-d3 辺の非均質性を Stoicheia Γ/Q 割当で設定

追加テスト:
  - 4D 部分シンプレクティック (Π₁+Π₂) の頑健性
  - 方法 F の taxis.md 更新候補としての妥当性
"""
import random, math

N = 6
Va, Fu, Pr, Sc, Vl, Te = 0, 1, 2, 3, 4, 5
ABBR = ['Va', 'Fu', 'Pr', 'Sc', 'Vl', 'Te']
D_VAL = {Va:2, Fu:2, Pr:2, Sc:3, Vl:3, Te:2}

DIRS = [
    (Va,Pr,+1),(Va,Fu,+1),(Fu,Pr,+1),
    (Va,Sc,+1),(Va,Vl,+1),(Va,Te,+1),
    (Fu,Sc,+1),(Fu,Vl,+1),(Fu,Te,+1),
    (Pr,Sc,+1),(Pr,Vl,+1),(Pr,Te,+1),
    (Sc,Vl,+1),(Sc,Te,+1),(Vl,Te,+1),
]

G_W = {
    (Va,Fu):0.40,(Va,Pr):0.40,(Fu,Pr):0.60,
    (Va,Sc):0.20,(Va,Vl):0.40,(Va,Te):0.35,
    (Fu,Sc):0.30,(Fu,Vl):0.35,(Fu,Te):0.35,
    (Pr,Sc):0.50,(Pr,Vl):0.50,(Pr,Te):0.35,
    (Sc,Vl):0.30,(Sc,Te):0.30,(Vl,Te):0.20,
}

def pf6(a):
    return (
        a[0][1]*a[2][3]*a[4][5]-a[0][1]*a[2][4]*a[3][5]+a[0][1]*a[2][5]*a[3][4]
       -a[0][2]*a[1][3]*a[4][5]+a[0][2]*a[1][4]*a[3][5]-a[0][2]*a[1][5]*a[3][4]
       +a[0][3]*a[1][2]*a[4][5]-a[0][3]*a[1][4]*a[2][5]+a[0][3]*a[1][5]*a[2][4]
       -a[0][4]*a[1][2]*a[3][5]+a[0][4]*a[1][3]*a[2][5]-a[0][4]*a[1][5]*a[2][3]
       +a[0][5]*a[1][2]*a[3][4]-a[0][5]*a[1][3]*a[2][4]+a[0][5]*a[1][4]*a[2][3]
    )

def mkQ(weights):
    Q = [[0.0]*N for _ in range(N)]
    for i,j,s in DIRS:
        w = weights.get((i,j)) or weights.get((j,i),0.0)
        Q[i][j] = s*w; Q[j][i] = -s*w
    return Q

def robustness_test(weights, delta=0.2, trials=5000):
    pos = 0
    for _ in range(trials):
        pw = {k: v*(1+random.uniform(-delta,delta)) for k,v in weights.items()}
        if pf6(mkQ(pw)) > 0: pos += 1
    return pos / trials

def solve_cubic(a, b, c, d):
    b, c, d = b/a, c/a, d/a
    p = c - b*b/3.0
    q = 2*b*b*b/27.0 - b*c/3.0 + d
    disc = q*q/4.0 + p*p*p/27.0
    if disc < 0:
        r = math.sqrt(-p*p*p/27.0)
        theta = math.acos(max(-1, min(1, -q/(2*r)))) if r > 1e-15 else 0
        m = 2 * r**(1.0/3.0) if r > 0 else 0
        return [m*math.cos(theta/3.0)-b/3.0, m*math.cos((theta+2*math.pi)/3.0)-b/3.0, m*math.cos((theta+4*math.pi)/3.0)-b/3.0]
    else:
        sqrt_disc = math.sqrt(max(disc, 0))
        u = (-q/2.0 + sqrt_disc); v = (-q/2.0 - sqrt_disc)
        u = math.copysign(abs(u)**(1/3), u) if abs(u) > 1e-15 else 0
        v = math.copysign(abs(v)**(1/3), v) if abs(v) > 1e-15 else 0
        return [u+v-b/3.0, u+v-b/3.0, u+v-b/3.0]

def darboux_lambdas(Q):
    """Q² の固有値から λ₁,λ₂,λ₃ を求める"""
    QsQ = [[sum(Q[i][k]*Q[k][j] for k in range(N)) for j in range(N)] for i in range(N)]
    A = [[-QsQ[i][j] for j in range(N)] for i in range(N)]
    trA = sum(A[i][i] for i in range(N))
    A2 = [[sum(A[i][k]*A[k][j] for k in range(N)) for j in range(N)] for i in range(N)]
    trA2 = sum(A2[i][i] for i in range(N))
    A3 = [[sum(A2[i][k]*A[k][j] for k in range(N)) for j in range(N)] for i in range(N)]
    trA3 = sum(A3[i][i] for i in range(N))
    p1, p2, p3 = trA/2, trA2/2, trA3/2
    e1 = p1; e2 = (e1*p1-p2)/2; e3 = (p3-e1*p2+e2*p1)/3
    roots = solve_cubic(1, -e1, e2, -e3)
    return sorted([math.sqrt(max(r,0)) for r in roots], reverse=True)

# ============================================================
# 方法 F: C+D ハイブリッド
# ============================================================

def method_F(alpha=0.6, beta=0.3, gamma=0.15):
    """方法 F: C+D ハイブリッド
    
    層1 (d-level 階層, 方法C): スケール制約
      d2×d2: α 帯域内で変動
      d2×d3: β 帯域内で変動
      d3×d3: γ 帯域内で変動
    
    層2 (認知サイクル, 方法D): d2×d2 内の非均質性
      Fu→Pr: 最大 (Explore/Exploit 核心, S-III 直結)
      Va→Pr: 中 (S-I/S-III の作用面)
      Va→Fu: やや低 (目的→戦略は間接的)
    
    層3 (Stoicheia 波及, 方法B): d2×d3 内の非均質性
      Pr→d3: 最大 (S-III = 精度最適化 → 全修飾座標に波及)
      Fu→d3: 中 (S-II = 能動推論 → 状況に応じた修飾)
      Va→d3: 最小 (S-I = 知覚推論 → 修飾座標への直接影響小)
    """
    weights = {}
    
    # 層2: d2×d2 の認知サイクル構造
    # α 帯域内の比率: Fu→Pr > Va→Pr > Va→Fu
    d2_ratios = {
        (Fu,Pr): 1.0,    # 基準 (最大)
        (Va,Pr): 0.85,   # S-I/S-III 作用面
        (Va,Fu): 0.70,   # 間接的結合
    }
    for (i,j), r in d2_ratios.items():
        weights[(i,j)] = alpha * r
    
    # 層3: d2×d3 の Stoicheia 波及構造
    # β 帯域内の比率: Pr>d3 > Fu>d3 > Va>d3 
    d2_influence = {Pr: 1.0, Fu: 0.8, Va: 0.6}
    # d3 座標の受容性 (仮定: 均等)
    for d2 in [Va, Fu, Pr]:
        infl = d2_influence[d2]
        for d3 in [Sc, Vl, Te]:
            weights[(d2, d3)] = beta * infl
    
    # d3×d3: γ (均等 — d3間の循環は弱い)
    for a in [Sc, Vl, Te]:
        for b in [Sc, Vl, Te]:
            if a < b:
                weights[(a,b)] = gamma
    
    return weights

# ============================================================
# テスト
# ============================================================

random.seed(42)
print("="*70)
print("E7c: Q 構成法の最終形 — C+D ハイブリッド")
print("="*70)

# まずハイブリッドの基本テスト
w_F = method_F()
Q_F = mkQ(w_F)
p_F = pf6(Q_F)
lambdas_F = darboux_lambdas(Q_F)

print(f"\n--- 方法 F (C+D ハイブリッド) ---")
print(f"  α=0.6 (d2-d2), β=0.3 (d2-d3), γ=0.15 (d3-d3)")
print(f"  Pf(Q) = {p_F:.6f}")
print(f"  Darboux: λ₁={lambdas_F[0]:.4f}, λ₂={lambdas_F[1]:.4f}, λ₃={lambdas_F[2]:.4f}")
if lambdas_F[2] > 1e-8:
    print(f"  条件数 λ₁/λ₃ = {lambdas_F[0]/lambdas_F[2]:.1f}")

# 頑健性テスト
r20_F = robustness_test(w_F, 0.2, 10000)
r50_F = robustness_test(w_F, 0.5, 10000)
print(f"  ±20% 保存率: {r20_F*100:.1f}%")
print(f"  ±50% 保存率: {r50_F*100:.1f}%")

# Q 行列表示
print(f"\n  Q 行列:")
for i in range(N):
    row = " ".join(f"{Q_F[i][j]:+6.3f}" for j in range(N))
    print(f"    {ABBR[i]}: {row}")

# α:β:γ の最適化 (非均質性を保ちつつ)
print(f"\n--- α:β:γ 最適化 (ハイブリッド) ---")
best_r20 = 0
best_params = None
results_grid = []

for a10 in range(3, 10):       # α: 0.3-0.9
    for b10 in range(1, a10):   # β < α
        for g10 in range(1, b10+1): # γ ≤ β
            a, b, g = a10/10, b10/10, g10/10
            w = method_F(a, b, g)
            p = pf6(mkQ(w))
            if abs(p) > 1e-10:
                r = robustness_test(w, 0.2, 2000)
                results_grid.append((a, b, g, p, r))
                if r > best_r20:
                    best_r20 = r
                    best_params = (a, b, g, p)

if best_params:
    a, b, g, p = best_params
    print(f"  最適: α={a:.1f}, β={b:.1f}, γ={g:.1f}")
    print(f"  Pf = {p:.6f}, ±20% 保存率 = {best_r20*100:.1f}%")
    
    # 最適パラメータで詳細テスト
    w_opt = method_F(a, b, g)
    Q_opt = mkQ(w_opt)
    l_opt = darboux_lambdas(Q_opt)
    r50_opt = robustness_test(w_opt, 0.5, 10000)
    print(f"  Darboux: λ₁={l_opt[0]:.4f}, λ₂={l_opt[1]:.4f}, λ₃={l_opt[2]:.4f}")
    print(f"  条件数 λ₁/λ₃ = {l_opt[0]/l_opt[2]:.1f}")
    print(f"  ±50% 保存率: {r50_opt*100:.1f}%")

# 比較表
print(f"\n--- 全方法比較 (最終) ---")
methods_compare = {
    'A: |Q|=w': dict(G_W),
}
for name, w in methods_compare.items():
    Q = mkQ(w)
    p = pf6(Q)
    r20 = robustness_test(w, 0.2, 5000)
    l = darboux_lambdas(Q)
    print(f"  {name}: Pf={p:.4f}, λ₁/λ₃={l[0]/max(l[2],1e-10):.1f}, ±20%={r20*100:.1f}%")

# 方法 C
w_C = {}
for i,j,_ in DIRS:
    pair = tuple(sorted([D_VAL[i], D_VAL[j]]))
    if pair==(2,2): w_C[(i,j)]=0.6
    elif pair==(2,3): w_C[(i,j)]=0.3
    else: w_C[(i,j)]=0.2
Q_C = mkQ(w_C); p_C = pf6(Q_C)
r20_C = robustness_test(w_C, 0.2, 5000)
l_C = darboux_lambdas(Q_C)
print(f"  C: d-level最適: Pf={p_C:.4f}, λ₁/λ₃={l_C[0]/max(l_C[2],1e-10):.1f}, ±20%={r20_C*100:.1f}%")

# 方法 F (デフォルト)
print(f"  F: C+D hybrid: Pf={p_F:.4f}, λ₁/λ₃={lambdas_F[0]/max(lambdas_F[2],1e-10):.1f}, ±20%={r20_F*100:.1f}%")

if best_params:
    a,b,g,p = best_params
    w_Fo = method_F(a,b,g); Q_Fo = mkQ(w_Fo); l_Fo = darboux_lambdas(Q_Fo)
    r20_Fo = robustness_test(w_Fo, 0.2, 5000)
    r50_Fo = robustness_test(w_Fo, 0.5, 5000)
    print(f"  F*: hybrid最適: Pf={p:.4f}, λ₁/λ₃={l_Fo[0]/max(l_Fo[2],1e-10):.1f}, ±20%={r20_Fo*100:.1f}%, ±50%={r50_Fo*100:.1f}%")

# 4D 部分シンプレクティック (Π₁+Π₂) の頑健性
print(f"\n--- 4D 部分シンプレクティック (d2 座標のみ) ---")
print(f"  Π₁+Π₂ = Va, Fu, Pr + 最強の d3 座標")

# d2 のみの 3×3 部分行列の Pfaffian は?
# 3×3 反対称行列は Pf = 0 (奇数次元)
# → 4×4 部分行列 (d2 + 最強の d3)
d2_set = [Va, Fu, Pr]
# 最強 d3 = Sc (Pr→Sc が w=0.50 で最強)
for extra in [Sc, Vl, Te]:
    coords = d2_set + [extra]
    # 4×4 部分 Q の Pfaffian: a[0][1]*a[2][3] - a[0][2]*a[1][3] + a[0][3]*a[1][2]
    idx = {c:i for i,c in enumerate(coords)}
    
    # 方法 F の部分行列
    sub = [[0.0]*4 for _ in range(4)]
    for i,j,s in DIRS:
        if i in idx and j in idx:
            wv = w_F.get((i,j)) or w_F.get((j,i),0.0)
            sub[idx[i]][idx[j]] = s*wv
            sub[idx[j]][idx[i]] = -s*wv
    pf4 = sub[0][1]*sub[2][3] - sub[0][2]*sub[1][3] + sub[0][3]*sub[1][2]
    
    # 部分行列の頑健性
    pos4 = 0
    for _ in range(5000):
        pw = {k:v*(1+random.uniform(-0.2,0.2)) for k,v in w_F.items()}
        sub_p = [[0.0]*4 for _ in range(4)]
        for ii,jj,ss in DIRS:
            if ii in idx and jj in idx:
                wv = pw.get((ii,jj)) or pw.get((jj,ii),0.0)
                sub_p[idx[ii]][idx[jj]] = ss*wv
                sub_p[idx[jj]][idx[ii]] = -ss*wv
        if sub_p[0][1]*sub_p[2][3] - sub_p[0][2]*sub_p[1][3] + sub_p[0][3]*sub_p[1][2] > 0:
            pos4 += 1
    
    print(f"  {'+'.join(ABBR[c] for c in coords)}: Pf₄={pf4:.4f}, ±20% 保存率={pos4/5000*100:.1f}%")

# 最終的な Q 値の提案
print(f"\n" + "="*70)
print(f"最終提案: Q-series (循環強度)")
print(f"="*70)
print(f"\n方法 F (C+D ハイブリッド) による Q 値:")
print(f"  構造: d-level 階層 × 認知サイクル × Stoicheia 波及")
print()
print(f"  {'辺':<10s} {'方法A (旧)':<12s} {'方法F (新)':<12s} {'理論的根拠'}")
print(f"  {'-'*60}")
for i,j,s in DIRS:
    w_old = G_W.get((i,j)) or G_W.get((j,i),0)
    w_new = w_F.get((i,j)) or w_F.get((j,i),0)
    
    # グループ判定
    di, dj = D_VAL[i], D_VAL[j]
    if di==2 and dj==2: grp = "d2×d2 核心循環"
    elif di==2 or dj==2: grp = "d2×d3 Stoicheia波及"
    else: grp = "d3×d3 弱循環"
    
    print(f"  {ABBR[i]}→{ABBR[j]:<5s}  {w_old:<12.2f} {w_new:<12.3f} {grp}")

print(f"\n[要約]")
print(f"  旧 (方法A): |Q|=w → Pf=0.004, ±20%保存=57%")
print(f"  新 (方法F): C+D hybrid → Pf={p_F:.3f}, ±20%保存={r20_F*100:.0f}%")
print(f"  改善: 条件数 {227.5:.0f} → {lambdas_F[0]/max(lambdas_F[2],1e-10):.0f}")

print("\n" + "="*70)
