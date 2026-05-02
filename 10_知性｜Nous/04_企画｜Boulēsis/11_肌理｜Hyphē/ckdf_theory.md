# CKDF — Categorical Kalon Detection Framework

> **構造検出 (P) はなぜ最適化 (NP) を回避できるのか。**
> **Kalon は最適化を包含する。逆は成り立たない。**

**ステータス**: 仮説段階 (理論骨格)
**起源**: 2026-03-13 UnifiedIndex 深化セッション
**依存**: kalon.md (§2), axiom_hierarchy.md (§Basis, §座標)

---

## §1 動機 — 2つの問い

### 問い1: なぜ構造検出は P なのに最適分割は NP なのか？

| 操作 | 例 | 計算量 | 本質 |
|:-----|:---|:-------|:-----|
| **構造検出** (Detection) | PCA, Fourier, Fisher 固有分解, HGK 座標 | P | 場の内在構造を読む |
| **最適分割** (Search) | k-means最適化, TSP, SAT, 最適クラスタリング | NP | 全候補から最良を選ぶ |

直感: Detection は「場に聞く」。Search は「場を探す」。
聞くのは1回。探すのは指数回。

### 問い2: Kalon と最適化はどう違うのか？

| | 最適化 | Kalon |
|:--|:------|:------|
| 要件 | コスト関数 f: S → ℝ | 随伴 F⊣G |
| 解 | argmin f(x) | Fix(G∘F) |
| 方法 | 全候補の比較 | G∘F 反復 (局所操作) |
| 計算量 | NP-hard (一般) | P (ガロア接続 + 完備束) |

**主張: Kalon ⊃ Optimization。最適化はコスト関数を持つ Kalon の特殊ケース。**

---

## §2 Kalon▽ と Kalon△ — 狭義と広義の定義

### §2.1 定義

**Kalon▽ (狭義, 客観普遍的)**:
```
Kalon▽(x) ⟺ x = Fix(G∘F) in C  (C = 全空間)

- S → Ω (全命題空間)
- 一意 (完備束 + Knaster-Tarski)
- 到達不能 (Ω は有限時間で走査不可能)
- 計算量: NP (全空間の探索が必要)
- 存在論: 真理そのもの。主体に依存しない
```

**Kalon△ (広義, 主観局所的)**:
```
Kalon△(x, A) ⟺ x = Fix(G∘F)|_{MB(A)}  for agent A

- S = MB(A) (agent A の Markov blanket)
- A に対して一意 (MB(A) 内で Knaster-Tarski)
- 到達可能 (G∘F 反復で収束)
- 計算量: P (局所反復)
- 存在論: 真理への接近。A の認知的地平内での最善
```

**関係**:
```
Kalon△(·, A) → Kalon▽  as  MB(A) → Ω

「答えは常にそこにある (▽)。ただそれを知覚できていないだけ (△)。」
```

### §2.2 混同の3類型

| 誤り | 内容 | 帰結 | 対策 |
|:-----|:-----|:-----|:-----|
| **Type 1** | △を▽と誤認 | 過信。局所解を真理と断言 | S-I: 自分の MB の有限性を自覚 |
| **Type 2** | ▽不可能 → 虚無 | △の価値を過小評価 | △は P で到達可能。実用的に十分 |
| **Type 3** | △非一意 → 相対主義 | 「何でもいい」 | MB 内では一意。恣意ではない |

---

## §3 CKDF レイヤー構造

```
L0  場 ────────── 完備束 C (あるいは完備半順序集合)
 │                条件: 順序が定義されている
 │
L1  随伴 ─────── ガロア接続 F⊣G on C
 │                F = 発散 (Explore, 左随伴)
 │                G = 収束 (Exploit, 右随伴)
 │                非退化: F ≠ Id, G ≠ Id
 │
L2  座標検出 ─── 場の内在構造の固有分解 .......... P
 │                手法: Fisher 情報, スペクトル, PCA 等
 │                結果: d 本の座標 (場が決定)
 │
L3  Kalon△ ───── G∘F 反復 → 局所不動点 ........... P
 │                MB(A) 内で単調収束
 │                = 構造検出の結実
 │                注: Fix = 到達先 (what)。到達経路の
 │                非結合性 (how) は chunk_ckdf_bridge §2.4b
 │
L∞  Kalon▽ ───── 全空間の不動点 ................... NP
                  = 到達不能な理想
                  = △ の極限 (lim_{MB→Ω})
```

### Instantiation の例

| ドメイン | C | F⊣G | 座標 (L2) | Kalon△ (L3) |
|:---------|:--|:-----|:----------|:------------|
| **FEP/HGK** | VFE 空間 | Helmholtz Γ⊣Q | 6+1 本 (Fisher 固有) | VFE 最小化の不動点 |
| **PCA** | 共分散空間 | 射影⊣包含 | d 本 (主成分) | 低次元表現 |
| **Fourier** | L² 関数空間 | 分解⊣合成 | 周波数成分 | 有限級数近似 |
| **ゲーム理論** | 戦略空間 | 逸脱⊣最適応答 | 純戦略 | Nash 均衡 |
| **熱力学** | 相空間 | 膨張⊣圧縮 | 温度, 圧力, エントロピー | 熱平衡 |

---

## §4 Kalon ⊃ Optimization — 包含定理

> **v1.1** (2026-03-18): 元の構成 (f-下閉包) を撤回。近傍関数による修正構成。
> 核心の洞察: 最適化も F⊣G (発散⊣収束) を持つ。差は G が操作する順序構造。
> 詳細: [chunk_ckdf_bridge.md](chunk_ckdf_bridge.md) §3

### §4.1 主張

```
定理 (Kalon-Optimization 包含, [推定] 80%):

任意の最適化問題 (S, f, N) — S: 候補集合, f: S→ℝ, N: 近傍関数 — に対し、
非退化なガロア接続 F_f ⊣ G_f が構成可能であり、かつ:

  Fix(G_f ∘ F_f) = {f の局所最小点}

逆は一般に成り立たない:
  G が半順序上の蒸留である Kalon の Fix は、
  一般にスカラーコスト関数に還元できない。
```

### §4.2 構成

```
与えられた最適化問題 (S, f, N):

F_f(x) = N(x) ∪ {x}                    # 近傍探索 (広げる)
G_f(Y) = argmin_{y ∈ Y} f(y)           # f-最小化 (絞る)

非退化条件:
  F_f ≠ Id  ✓  (近傍は x 以外を含む)
  G_f ≠ Id  ✓  (argmin は集合全体ではなく1元を選ぶ)

Fix(G_f ∘ F_f)(x) ⟺ x = argmin_{y ∈ N(x)∪{x}} f(y)
                    ⟺ 近傍に x より良い候補がない
                    ⟺ x は f の局所最小  ✓
```

### §4.3 包含の本質 — G の順序構造の退化

```
最適化も Kalon も非退化な F⊣G を持つ。差はどこか？

  最適化の G: スカラー f による全順序 (total order) で判定
    → 判断基準が 1次元。任意の2元が比較可能
    
  Kalon の G: 半順序 (partial order) 上の蒸留で判定
    → 判断基準が 多次元。比較不能な元が存在する

  全順序 ⊂ 半順序  →  Optimization ⊂ Kalon  ✓
  
  CKDF L2 (座標検出) との接続:
    d = 0 (座標なし) = 全順序 = 最適化
    d > 0 (座標あり) = 半順序 = Kalon
    → d は「最適化からの距離」を測る指標
```

### §4.4 逆が成り立たない反例

```
(1) CCL の ~ の不動点:
    F=/noe, G=/ene。Fix(G∘F)=認識と実行が安定する不動点
    /noe の軸 (Value-E) と /ene の軸 (Value-P) は比較不能 (半順序)
    → 単一スカラーに縮退しない

(2) Hyphē の Fix(G∘F):
    Fix=「冗長ゼロ・不足ゼロ」= Pareto 最適 (2目的)
    → 2目的の Pareto 最適は単一コスト関数の argmin ではない

(3) Coherence Invariance:
    C̄(Fix(G∘F; τ)) ≈ const — 保存量であり最小化対象ではない
```

---

## §5 P の十分条件 — なぜ Kalon△ は計算可能か

### §5.1 Knaster-Tarski 定理の適用

```
定理 (Knaster-Tarski):
  C が完備束、φ: C → C が単調写像 ⟹ Fix(φ) は空でない完備束。

適用:
  φ = G∘F
  G∘F が単調 ← F⊣G がガロア接続 → F, G はともに単調 → G∘F も単調 ✓
  C が完備束 ← 仮定 (実用上: 有限半順序は自動的に完備束) ✓
  ∴ Fix(G∘F) は存在 ✓
```

### §5.2 反復到達 (P の根拠)

```
任意の x₀ ∈ C から出発:
  x₀ ≤ G∘F(x₀) ≤ (G∘F)²(x₀) ≤ ... ≤ (G∘F)ⁿ(x₀) = Fix

単調増加列が C の上界に収束。
C が有限 (|C| = N) なら、最大 N 回の反復で Fix に到達。
∴ 計算量 = O(N × cost(G∘F)) = P (G∘F が P なら)
```

### §5.3 P でない場合 (制限)

| 不動点の種類 | 計算量 | なぜ |
|:-------------|:-------|:-----|
| ガロア接続の Fix | **P** | 単調 + 完備束 → 反復到達 |
| Brouwer 不動点 | **PPAD** | 連続写像。方向がない |
| Nash 均衡 | **PPAD** | 多主体。単調性なし |
| 一般不動点 | **?** | 構造依存 |

**結論**: CKDF は「ガロア接続 + 完備束」に限定して P を主張する。
一般の圏や連続写像には拡張しない (拡張には追加条件が必要)。

---

## §6 Coordinate Detection Theorem (仮)

### §6.1 主張

```
定理 (座標検出, 仮):

(C, F⊣G) がガロア接続を持つ完備束であるとき、
C の構造に内在する d 本の座標が存在し、以下を満たす:

(1) d は C の構造が決定する (外部から課さない)
(2) 各座標は F⊣G の固有方向に対応する
(3) 座標の検出は O(d³) = P

ここで d の決定原理は以下の候補 (未確定):
  (a) Fisher 情報行列の有意な固有値の数
  (b) C の対称群のリー代数の次元
  (c) C の Betti 数 (位相的不変量)
  (d) Kleinberg 不可能性の回避に必要な最小仮定数
```

### §6.2 HGK での具体化

```
C = VFE 空間 (場)
F⊣G = Helmholtz 分解 (Γ⊣Q)

Fisher 情報行列の固有分解 → 候補方向 (潜在的に無限)
妥当性テスト 3条件で篩う:
  (1) FEP 導出可能性
  (2) Helmholtz 射影可能性
  (3) Euporía 射影可能性

生き残り = 7 本 (Flow + 6修飾座標)
d = 7 は FEP 空間の構造が決定した数。恣意的選択ではない。
```

---

## §7 Kleinberg 不可能性との接続

### §7.1 Kleinberg の3公理

```
いかなるクラスタリング関数 f も以下を同時に満たせない:
(K1) Scale-Invariance: f(αd) = f(d)
(K2) Richness: 全分割が到達可能
(K3) Consistency: クラスタ内↓ + クラスタ間↑ → 結果不変
```

### §7.2 CKDF の応答

```
CKDF は「クラスタリング」ではなく「MB 検出」を行う。
MB 検出は Kleinberg の3公理のうち2つを構造的に "放棄" する:

(K1) Scale-Invariance: ✗ 放棄。Scale は座標 (L2 で検出)
(K2) Richness: ✗ 放棄。G∘F で到達可能な分割のみ
(K3) Consistency: ✅ 保持。不動点の安定性 = Consistency

放棄は「失敗」ではない。放棄する性質の選択自体が座標情報を生む:
  Scale-Invariance の放棄 → Scale 座標の必然性
  Richness の放棄 → Kalon△ が Kalon▽ より小さい候補集合を探索
```

---

## §8 未解決問題

| # | 問題 | 優先度 | 状態 |
| :-- | :---- | :----- | :---- |
| Q1 | Kalon ⊃ Optimization — 近傍関数構成完了。← 方向の厳密証明が残存 | 高 | → 方向 ✓ / ← 方向: 反例3つ (80%) |
| Q2 | 座標数 d の決定原理 — 構成距離 (e) が最堅。(a)(d) は補助的 | 高 | 候補 5つ → 評価完了 |
| Q3 | 一般の圏への拡張 (PPAD との境界) | 中 | 制限条件のみ |
| Q4 | FEP 以外のドメインでの worked examples | 中 | テーブルのみ |
| Q5 | Kleinberg (K1)(K2) 放棄の必然性の証明 | 中 | 直感のみ |
| Q6 | 「Kalon△ → Kalon▽」の収束速度 | 低 | 未着手 |
| Q7 | η MB 4区画 × Γ/Q = 7 の偶然性 vs 構造的必然 | 低 | 新規 (30%) |

---

## §9 論文化への道筋 (改訂)

### タイトル案 (一般化後)

"From Search to Detection: A Category-Theoretic Account of
Why Structure Finding is Polynomial While Optimization is Hard"

### 構成案

1. **Introduction**: Optimization is NP. But structure detection is P. Why?
2. **Background**: Complete lattices, Galois connections, Knaster-Tarski
3. **CKDF**: The framework (L0-L∞)
4. **Kalon▽/△**: Two notions of fixed point and their complexity gap
5. **Embedding theorem**: Optimization ⊂ Kalon (proof)
6. **Kleinberg resolution**: Which axioms to drop, and why
7. **Instantiations**: FEP (6 coords), PCA, Fourier, game theory
8. **Discussion**: What this means for AI, cognition, and knowledge organization

### 対象

- Applied Category Theory (ACT) ワークショップ/ジャーナル
- 理論計算機科学 (Kleinberg 接続)
- 人工知能 (構造検出 vs 最適化)

---

## §10 忘却論・結晶化との接続 (2026-03-29 追記)

### CKDF と忘却関手

CKDF の G (収束関手) は忘却論における忘却関手 U の構造的対応物:

| CKDF | 忘却論 | 構造的対応 |
|:--|:--|:--|
| G: P → P (収束) | U: C_D → A (忘却) | 構造を削り本質を残す |
| F: P → P (発散) | F: A → C_D (自由) | 構造を増殖する |
| Fix(G∘F) = Kalon | ker(U) = 忘却される構造 | 安定な不動点 |
| Kalon△ (MB内, P) | α > 0 の Markov 領域 | Copy/Index が可能な領域 |
| Kalon▽ (全空間, NP) | α ≤ 0 の non-Markov 領域 | Copy 不可能 → 全探索必要 |

**核心的洞察**: Kalon△ が P であるのは、α > 0 (Markov 構造) の領域に限定されるから。
Paper III の「α ≤ 0 で Copy 不可能」= CKDF の「Kalon▽ が NP」の別表現。

**定理的基盤 (2026-03-30 追記)**: Paper III §5.5 定理 5.5.1 (Copy-Computability 対応) で厳密化:
- α > 0: copy → 情報の分岐 → 条件付き独立性 → 動的計画法 → P
- α ≤ 0: anti-copy (幂零性 e∧e=0) → 分岐不在 → 最適部分構造の崩壊 → 全探索 → NP
- P/NP 分離は離散的分類ではなく α=0 を臨界点とする連続的相転移 (§4.8 の平方根則と接続)
- Q3 への部分応答: PPAD 境界は α(θ) が空間的に不均一な場合に対応

### 結晶化モデルとの統合

CKDF の L0-L∞ 層は結晶化過程の段階に対応:

| CKDF 層 | 結晶化比喩 | 忘却論 |
|:--|:--|:--|
| L0 (Field) | 溶液 (高エントロピー場) | Φ 忘却場の定義域 |
| L1 (Adjoint) | 溶解 (F) ⊣ 結晶化 (G) | d ⊣ ∫ |
| L2 (Coordinate) | 結晶軸の検出 | 固有分解 (P) |
| L3 (Kalon△) | 結晶の析出 (局所) | ρ_MB > τ |
| L∞ (Kalon▽) | 完全結晶 (到達不能) | Φ = 0 (忘却なし) |

### 参照

- [linkage_crystallization.md](linkage_crystallization.md) — G∘F = 結晶化の本質定義
- [linkage_hyphe.md](../../../00_核心｜Kernel/A_公理｜Axioms/linkage_hyphe.md) — 正典 v7, §3 (F⊣G), §7 (場⊣結晶)
- 忘却論 Paper III — α > 0 / α ≤ 0 の相転移 → Kalon△/▽ の P/NP 分離の物理的基盤
