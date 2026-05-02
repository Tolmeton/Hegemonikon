# チャンク公理: FEP 演繹による NP 困難回避仮説

> **日付**: 2026-03-13
> **起源**: UnifiedIndex 深化セッション
> **ステータス**: 仮説段階 (新規性確認済み)

---

## 1. 核心の主張

### 主張 (Claim)

> **FEP の場の構造から座標/チャンクを演繹的に導出するアプローチは、
> 最適クラスタリング (NP-hard) を構造的に回避し、多項式時間 (P) でチャンクを同定できる。**

根拠: 不動点探索 Fix(G∘F) は反復収束であり P。最適化 (argmin) は全探索が必要で NP。

### Creator の洞察

> 答え（真理）はね、生み出すものではない、見つけるもの。
> 真理は常にそこにある、ただそれを知覚できていないだけ。

数学的翻訳: 座標は「設計」(NP) ではなく「検出」(P)。
FEP 空間の構造に内在する固有方向を Fisher 情報行列の固有分解で同定する。

---

## 2. 問題の定式化

### 2.1 クラスタリングの不可能性定理 (Kleinberg 2002)

いかなるクラスタリング関数 f も以下の3性質を同時に満たせない:

| 性質 | 定義 |
|:-----|:-----|
| Scale-Invariance | f(αd) = f(d) — 距離をスケーリングしても結果不変 |
| Richness | 全ての分割が何らかの距離関数で到達可能 |
| Consistency | クラスタ内↓ + クラスタ間↑ → 結果不変 |

### 2.2 NP 困難

- 最適 k-clustering (ℓ₂²-min-sum): NP-hard to approximate below factor 1.056
- 最適 k-matching (Euclidean): NP-hard for k ≥ 3
- 一般的な最適分割: 組合せ爆発

### 2.3 FEP のアプローチ

| 操作 | 計算量 | 根拠 |
|:-----|:-------|:-----|
| Fisher 情報行列の固有分解 | O(N³) = P | 線形代数 |
| 座標妥当性テスト (3条件) | O(K) = P | フィルタリング |
| VFE 勾配降下 | P (局所最適) | 凸近似 |
| Fix(G∘F) 反復 | P (不動点定理) | Banach の不動点定理 |
| **全体** | **P** | **最適ではなく Kalon を探す** |

---

## 3. HGK の座標導出フロー

📖 参照: axiom_hierarchy.md L486-519

```
FEP 空間 (場)
  │
  ↓ Fisher 情報行列 (場の曲率構造)
  │
  ↓ 固有分解 → 固有ベクトル群 (潜在的に無限)
  │
  ↓ 座標妥当性テスト 3条件:
  │   (1) FEP 導出可能性
  │   (2) Helmholtz 射影可能性 (Γ_X と Q_X が区別可能)
  │   (3) Euporía 射影可能性 (AY_X > 0 が規範的)
  │
  ↓ 生き残り = 7 本 (Flow + 6修飾座標)
  │
  ↓ 6座標 × 4極 = 24動詞 (Poiesis)
```

**各ステップが P (多項式時間)**:
- 固有分解: O(d³) where d = VFE パラメータ数
- 妥当性テスト: O(K) where K = 候補座標数
- 4極の展開: O(1) (構造的)

---

## 4. チャンクへの適用

### 4.1 アナロジー

| HGK 座標導出 | チャンク同定 |
|:-------------|:------------|
| FEP 空間 | 意味空間 Ω (embedding) |
| Fisher 情報行列 | 共分散/相互情報量行列 |
| 固有ベクトル | MB 境界の候補方向 |
| 妥当性テスト | AY > 0 フィルタ |
| Fix(G∘F) | Search⊣index_op のサイクル収束 |

### 4.2 チャンク同定アルゴリズム (仮)

```
入力: 意味空間 Ω の N 個の要素 (embedding ベクトル)

1. 共分散行列 C = cov(Ω) を計算           ... O(N²d) = P
2. 条件付き独立性テスト: C_{ij|rest} ≈ 0  ... O(N²) = P
3. 条件付き独立性が成立する境界 = MB 候補   ... P
4. AY(MB_k) > 0 をフィルタ                 ... P
5. G∘F 反復で Fix に収束                   ... P (不動点)

出力: Kalon なチャンク分割 (最適ではないが安定)
```

### 4.3 「最適」vs「Kalon」

| 最適クラスタリング | Kalon チャンキング |
|:-------------------|:-------------------|
| 目標: argmin コスト関数 | 目標: Fix(G∘F) 不動点 |
| 計算量: NP-hard | 計算量: P (反復) |
| 保証: 大域最適 | 保証: 局所安定 (もう動かない) |
| Kleinberg: 不可能 | Kleinberg: 2性質を放棄して回避 |
| 生物学的非現実的 | 生物学的に自然 (VFE 最小化) |

---

## 5. Kleinberg 不可能性への FEP の応答

FEP はクラスタリングではなく **MB 検出** を行う。
MB 検出は Kleinberg の3公理のうち2つを構造的に放棄する:

| Kleinberg 性質 | FEP の態度 | 理由 |
|:---------------|:-----------|:-----|
| Scale-Invariance | ✗ 放棄 | Scale 座標 (d=3) で明示的にスケール依存 |
| Richness | ✗ 放棄 | VFE最小化する分割のみ到達可能 |
| Consistency | ✅ 保持 | MB の安定性条件 = Consistency |

### Creator 仮説: Scale 座標は不可能性定理の「代価」

> 6座標のうち Scale (d=3) が追加仮定を必要とするのは、
> Kleinberg の Scale-Invariance を放棄する代価を支払っているからではないか。

---

## 6. 新規性の評価

### 6.1 先行研究調査 (2026-03-13 実施)

**調査範囲**: Semantic Scholar 6クエリ + Periskopē 1クエリ, 130+ 件

| 先行研究 | 内容 | ギャップ |
|:---------|:-----|:---------|
| Kleinberg (2002) | クラスタリング不可能性定理 | FEP との接続なし |
| Friston (2019) "Particular Physics" (296 cit.) | MB の再帰的構成 (particular partition) | Kleinberg/NP困難の議論なし |
| "Clustering Redemption" (NIPS 2018) | Kleinberg 緩和 → 可能性定理 | FEP 接続なし |
| MB Density (2025, arXiv:2506.05794) | MB を連続化 (graded) | Kleinberg/NP困難の議論なし |
| Sittel & Stock (2018, 124 cit.) | 自由エネルギー面のクラスタリング | 分子動力学文脈のみ。認知/情報空間なし |

**結論**: FEP × Kleinberg × NP困難 を結合する論文は **確認できず**。

### 6.2 新規性の評価

| 側面 | 既存研究との関係 | 判定 |
|:-----|:---------------|:-----|
| MB = クラスタ | Friston (2019) で暗黙的 | 部分的に既知 |
| FEP の Fix(G∘F) で P | HGK 独自 (axiom_hierarchy) | **新規** |
| Kleinberg を FEP の Scale 座標で説明 | **先行研究なし** | **新規** |
| NP-hard 回避を Fix(G∘F) で定式化 | **先行研究なし** | **新規** |
| 座標 = FEP 空間のクラスタリング (制約付与) | **先行研究なし** | **新規** |

**[推定 70%] 論文化の価値がある。**

### 6.3 リスク要因

| リスク | 対策 |
|:-------|:-----|
| Fix(G∘F) の収束保証が厳密でない | Banach 不動点定理の条件確認 |
| 「意味空間の Fisher 行列」が定義できるか | embedding の共分散で近似 |
| FEP 自体への批判 (Markov blanket trick 論争) | MB density (2025) の graded 拡張を採用 |
| Kleinberg との接触が表層的 | 厳密な定式化が必要 |

---

## 7. 論文化への道筋 (仮)

### タイトル案
"From Optimization to Fixed Points: How the Free Energy Principle
Circumvents Clustering Impossibility"

### 構成案
1. Introduction: Kleinberg 不可能性 + NP困難 = クラスタリングの根本的限界
2. Background: FEP, Markov blankets, Fisher information geometry
3. Main result: Fix(G∘F) by VFE minimization achieves P-time MB detection
4. Kleinberg resolution: Scale-Invariance 放棄 = Scale 座標の必然性
5. Application: Chunk-based DB (Hyphē) as worked example
6. Discussion: "Kalon vs Optimal" — 不動点と最適点の棲み分け

### 必要な追加作業
- [ ] Banach 不動点定理の適用条件の検証
- [ ] 人工データでの PoC (Fix(G∘F) 反復が P で収束するか)
- [ ] Kleinberg の3性質と FEP の対応の厳密な証明
- [ ] 既存の MB 検出アルゴリズムとの比較実験
