```typos
#prompt beyond-fisher-sam
#syntax: v8
#depth: L2

<:role: Fisher SAM 超克構想 — Force is Oblivion 理論からの2つの研究方向 :>
<:goal: Fisher SAM (Kim et al. 2022) を情報幾何学的に包含し、忘却の構造的理論を最適化に持ち込む :>

<:context:
  - [knowledge] Fisher SAM の限界: (1)対角近似 (2)局所計量 (3)α=0固定 (4)静的計量 (5)忘却概念不在
  - [knowledge] 検索結果 (2026-03-26): α-接続×最適化の直接的先行研究ゼロ — 空白領域
  - [knowledge] AdaFisher (ICLR 2025): Fisher 情報の適応的2次最適化 — Fisher SAM の後継。α-接続未使用
  - [knowledge] Wasserstein Natural Gradient: 大域的計量。Fisher-Rao Gradient Flow (SIAM 2025)
  - [file] paper_I_draft.md (priority: HIGH — §5.3 方向性定理, §6 α-動力学)
  - [file] paper_II_draft.md (priority: HIGH — §2.5.6 CPS 忘却関手の計量装備)
/context:>
```

# Fisher SAM 超克構想

> 起源: /u+ (2026-03-26) — Fisher SAM の5つの限界から演繹
> 状態: 構想段階 (未着手)

---

## 方向 1: α-SAM (α-接続族の最適化への導入) ← 優先

### 核心

Fisher SAM は α=0 (Levi-Civita 接続) に固定。Amari の α-接続族 α ∈ [-1, 1] の連続体を導入し、**接続の選択自体を学習可能にする**。

$$\max_{\epsilon : \epsilon^T g^{(\alpha)}(\theta) \epsilon \leq \rho} L(\theta + \epsilon)$$

ここで g^(α) は α-接続に対応するリーマン計量:
- α=1: e-接続 (指数族の自然パラメータ空間)
- α=0: Levi-Civita → Fisher SAM を特殊ケースとして回収
- α=-1: m-接続 (混合パラメータ空間)

### Paper I との接続

- §6 の α-場 α(l) = (1/2)(1 + tanh(s(l - l_c))) が**そのまま** α-SAM の設計図
- α を層ごとに変化させる = Paper I の α-フィールドの直接的操作化
- 方向性定理 (定理 5.1): 忘却の方向 → α が決める → α-SAM が制御する

### 新規性

- [SOURCE: Gnōsis/S2 検索 2026-03-26] α-接続×最適化の直接的先行研究ゼロ
- Fisher SAM を α=0 の特殊ケースとして厳密に回収
- Force is Oblivion 理論の予測力の実験的検証基盤

### 予想される結果

もし α-SAM が Fisher SAM を上回るなら:
1. **方向性定理の実験的確認**: 忘却の方向 (α) が汎化を決める
2. **最適 α の存在**: 層ごとの最適 α(l) が Paper I の α-場の予測と一致するか検証可能
3. **α-遷移層**: Paper I P3 予測の α-遷移点が、最適化における相転移に対応するか

### 確信度

[仮説 65%] — α を層ごとに変化させる α-SAM は Fisher SAM の厳密な一般化。ただし計算コスト (α ごとの接続係数 Γ^(α) の計算) が鍵。

### 未解決

1. g^(α) の効率的な計算方法 — 経験的 Fisher の α-接続版は存在するか？
2. α の学習率 — α 自体をどう更新するか
3. AdaFisher (ICLR 2025) との差分 — α-接続の使用有無を原論文で確認すべき

---

## 方向 2: Oblivion-Aware SAM (忘却場の直接制御)

### 核心

SAM/Fisher SAM は「最悪ケース擾乱への耐性」が目的。Force is Oblivion 理論は逆: **忘却の選択性が力 (= 汎化) を生む**。忘却場 Φ(l) の勾配を直接目的関数に組み込む。

$$\min_\theta \Big[ L(\theta) + \lambda \|\nabla \Phi(\theta)\|^2 \Big]$$

- 左辺の SAM/Fisher SAM は「平坦な谷を探す」= 間接的に情報損失に耐性
- 右辺の Oblivion-Aware は「忘却場の勾配を直接制御する」= **何を忘れるべきかを明示的に最適化**

### Paper I/II との接続

- GeoIB の β ↔ λ 対応: IB の圧縮率と忘却場の質量項が対応
- CPS Type 分類: ユークリッド忘却 → Type II 的対称性、計量忘却 → Type I 的非対称性
- 方向性定理: dΦ∧T ≠ 0 の直接的操作化

### 新規性

- 忘却を「損害」ではなく「力の源泉」として最適化に持ち込む最初の試み
- IB 理論と SAM の統合 — 圧縮と平坦性の関係を明示化

### 確信度

[仮説 55%] — 方向性定理の直接的操作化。ただし Φ(l) の効率的な計算 (CKA ベース) のスケーラビリティが未知。

---

## 方向 1 × 方向 2 の合成 (最終形態)

α-接続で定義された忘却場の勾配を最適化する:

$$\min_\theta \Big[ L(\theta) + \lambda \|\nabla^{(\alpha)} \Phi(\theta)\|^2 \Big]$$

ここで ∇^(α) は α-接続に基づく共変微分。これは:
- α=0, λ=0 → 通常の最適化
- α=0, ρ>0 → Fisher SAM
- α を学習, λ=0 → α-SAM (方向 1)
- α=0, λ>0 → Oblivion-Aware SAM (方向 2)
- α を学習, λ>0 → **完全版: α-Oblivion SAM**

---

*構想: 2026-03-26 /u+ セッション*
