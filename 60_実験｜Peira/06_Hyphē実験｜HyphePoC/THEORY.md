# Hyphē 理論的基盤 — 溶媒仕様としての Embedding 設計
## THEORY.md v0.3

> **目的**: Hyphē の embedding 設計判断の理論的根拠を提供する
> **前提知識**: F: Chem → Cog (関手), VFE (変分自由エネルギー), Fix(G∘F) (不動点)
> **親文書**: [知性は溶媒である (draft)](../../10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/知性は溶媒である_草稿.md)

---

## §1. 核心命題

**Embedding モデルは溶媒である。**

| 化学 | Hyphē |
|:-----|:------|
| 溶媒 | embedding モデル (gemini-embedding-001, 768d) |
| 溶質 | セッションログ (テキストデータ) |
| 溶解 | F: テキスト → embedding ベクトル (場化) |
| 結晶化 | G: チャンク境界の検出 (similarity < τ) |
| 飽和溶液 | Context Rot (コンテキストウィンドウの上限) |
| 相転移温度 | **τ* ≈ 0.720** (実測, 858 similarity 点) |
| 不動点 | **Fix(G∘F)**: 全310実験で1-2回で収束 |

溶媒が溶質を選ぶように、embedding モデルは「溶かせる情報構造」を選ぶ。
この選択性が Hyphē の品質を決定する。

---

## §2. 温度 ↔ 精度 — 制御パラメータの対応

### 2.1. Gibbs ↔ VFE の同型

| Gibbs 自由エネルギー | 変分自由エネルギー |
|:---------------------|:-------------------|
| G = H − TS | F = −Accuracy + Complexity |
| 最小化 → 平衡状態 | 最小化 → 信念の更新 |

温度パラメータ化:

$$F_\beta = -\beta \cdot \text{Accuracy} + \text{Complexity} \quad (\beta = 1/T)$$

### 2.2. Hyphē への適用

| Gibbs (T) | VFE (β = 1/T) | Hyphē での意味 |
|:-----------|:---------------|:-------------|
| T → 0 (結晶化) | β → ∞ (高精度) | τ を上げる → チャンク数が増える → 細かい結晶 |
| T → ∞ (溶解) | β → 0 (低精度) | τ を下げる → チャンク数が減る → 粗い結晶 |
| 外部制御 | 外部制御 | **τ パラメータが温度に対応する** |

**帰結**: τ は Hyphē における逆温度 β の操作的実装である。τ を上げることは系を「冷やす」(結晶化を促進する) ことに相当し、τ を下げることは「加熱する」(溶解を促進する) ことに相当する。

---

## §3. ker(G) — 溶媒が溶かせない構造

### 3.1. 定義

ker(G) = 結晶化関手 G の核 = G が零に送る座標
= **embedding が保存できない情報構造**
= **溶媒が溶かせない溶質**

### 3.2. 実測結果

HGK の6修飾座標 (Value, Function, Precision, Temporality, Scale, Valence) について:

```
6座標:  Value  Function  Precision  Temporality  Scale  Valence
Desc:    保      保        保          捨         捨      保
Link:    保      保        保          捨         保      捨
Sess:    保      保        保          保         捨      捨
```

**ker(G)_{Session} = {Scale, Valence}**

### 3.3. 溶媒アナロジーによる解釈

| ker(G) の座標 | なぜ溶けないか (溶媒アナロジー) | 技術的原因 |
|:-------------|:---------------------------|:----------|
| **Scale** (粒度) | 局所溶媒は局所的にしか溶かせない。「Sprint のどこにいるか」という巨視的位置は、チャンク単位の embedding では捕捉できない | チャンクレベルの embedding には global position 情報がない。文脈窓 ≪ 全体 |
| **Valence** (評価) | 溶媒は中性。溶質の善悪を区別しない。cosine similarity は方向のみを見て「良い/悪い」を区別しない | 汎用 embedding は evaluative dimension が弱い。sentiment ≠ quality |

### 3.4. 設計指針

ker(G) を縮小するための戦略:

| 座標 | 対策 | 化学的アナロジー |
|:-----|:-----|:--------------|
| Scale | 階層的 embedding (チャンク + セクション + 全体) | **混合溶媒**: 異なるスケールの溶媒を混ぜて溶解度を拡げる |
| Valence | task_type="CLASSIFICATION" + 評価ラベル付き fine-tuning | **極性の調整**: 特定の溶質を溶かせる極性を溶媒に付与する |

---

## §4. Embedding Anisotropy — 溶媒の極性不足

### 4.1. 問題

Hyphē 実験 §12 の知見:

- precision gradient が検出できない (cosine similarity の分散が圧縮)
- 根本原因: **embedding anisotropy**
- 3072次元中の有効次元 k_eff_90 ≈ 33 (1.1%)
- 全ベクトルが狭い円錐内に集中

### 4.2. 溶媒アナロジーでの解釈

> **embedding anisotropy = 溶媒の極性が一方向に偏っている**

溶媒の極性が一方向に偏っている (anisotropic) ため、溶質の多様な構造を均等に溶解できない。水がヘキサンを溶かせないのと同じ構造的理由で、gemini-embedding-001 は Scale/Valence を溶かせない。

### 4.3. 対策

| 対策 | 化学的アナロジー | 実装 | Phase | 優先度 | 状態 |
|:-----|:--------------|:-----|:------|:------|:-----|
| **Whitening (ZCA)** | 溶媒の精製 | 後処理で等方性回復 | — | P1 | **✅ 実験済** [6] |
| task_type 指定 | 極性の調整 | `CLUSTERING`, `CLASSIFICATION` の使い分け | — | P1 | 未着手 |
| Fine-tuning (ローカル PoC) | 特注溶媒の合成 (小規模) | sentence-transformers + Valence-aware loss | **Phase 1** [5] | P2 | 未着手 |
| Fine-tuning (スケールアップ) | 特注溶媒の合成 (大規模) | Qwen3-Embedding-8B on Spot VM | **Phase 2** [5] | P2 | 未着手 |
| 多モデル ensemble | 混合溶媒 | 異なる embedding モデルの結合 | Phase 3 [5] | P3 | 未着手 |

### 4.4. ZCA Whitening 実験結果 [6]

**実験条件**: 365 embeddings (768d), 5 sessions, embedding_cache.npz から読み込み

#### スペクトル統計 (anisotropy の定量化)

| メトリクス | 値 | 意味 |
|:----------|:----|:-----|
| D_eff / d | 0.156 | 768 次元中 **84% が冗長** |
| Top-1 分散説明率 | 6.31% | 第一主成分の支配 |
| 90% 到達 | 136 成分 | 有効次元数 ≈ 136 |

#### 等方性指標 (cos_sim)

| | mean | std |
|:--|:-----|:----|
| Before (raw) | 0.726 | 0.042 |
| After (ZCA) | **-0.003** | **0.011** |

**効果**: ZCA 後の cos_sim ≈ 0 は **等方性の回復** を示す。Ruff cone (cos_sim ≈ 0.72 に集中する円錐構造) が解消された。溶媒精製は成功。

#### ker(G) への影響 (precision 分布)

| | mean | var | BC (二峰性) |
|:--|:-----|:----|:-----------|
| Before | 0.449 | 0.126 | 0.615 (bimodal) |
| After | 0.440 | 0.142 | **0.717** (bimodal ↑) |

**結論**: ZCA は **溶媒の均質化** (等方性) には有効だが、**溶質の分離** (Scale/Valence の区別) には無力。

> ZCA は回転変換であり、次元間の意味的区別を導入しない。ker(G) = {Scale, Valence} の解消には **教師信号** (supervised/contrastive signal) が必要。

化学的アナロジー: 純水の精製 (不純物除去) は溶媒を均質にするが、非極性溶質 (Scale, Valence) を溶かせるようにはならない。極性の調整 (§3.4) が必要。

### 4.5. FIM 固有ベクトル分析 — ker(G) の定量化

**目的**: ker(G) の次元を FIM (Fisher Information Matrix) の固有値構造から定量化する。

#### 手法

embedding_cache.npz (n=365, d=768) に対して:
1. 共分散行列の固有値スペクトル分析
2. k-NN FIM (k=10) の上位固有値分析 (PCA-200 射影空間)

#### 共分散スペクトル

| 指標 | 値 | 意味 |
|:-----|:---|:-----|
| D_eff | 60.5 | 有効次元数 |
| D_eff/d | 0.079 | 全 768 次元の 7.9% のみ有効 |
| dim50 | 24 | 分散の 50% が 24 次元に集中 |
| dim90 | 136 | 分散の 90% が 136 次元に集中 |
| 最大固有値比 | 1.37 (λ₀/λ₁) | **明確な sloppy gap なし** |

注目点: 共分散には明確な断崖がない (最大比 = 1.37)。**連続的な減衰** ─ 低ランク構造だが、区切り線がない。

#### FIM 固有値 (局所的情報構造)

| FIM λ | 値 | 分散比 |
|:------|:---|:-------|
| λ₀ | 0.003217 | 11.2% |
| λ₁ | 0.002907 | 10.1% |
| λ₂ | 0.002335 | 8.1% |
| λ₃ | 0.002304 | 8.0% |

**FIM sloppy gap**: λ₁/λ₂ = **1.25** → **stiff modes = 2**

これは前回 `e6_whitened_fim.py` の k_signal = 2 と一致。

#### 解釈

```
embedding 空間の局所構造:
  固い方向 (stiff modes) = 2  ← embedding が区別できる方向
  柔らかい方向 (sloppy modes) = 残り ← 区別不能な方向

HGK precision の構成:
  π = f(Scale, Valence, Temporality)  ← 3 座標

結論:
  dim(stiff) = 2 < dim(座標) = 3
  → ker(G) ≥ 1 次元
  → 少なくとも 1 座標が embedding で区別不能
```

**共分散 vs FIM の乖離** が示す構造:
- 共分散: 連続的な減衰 (sloppy gap なし) → 全体的には多方向に分布
- FIM: 局所的には 2 方向のみ「固い」 → 近傍点間で区別可能な方向は 2 つだけ

→ embedding は**大域的**には多方向に散布するが、**局所的**には 2 方向の変分しか使えない。これが ker(G) の本質: **precision 計算に使われる k-NN 密度は局所構造に依存するため、FIM の stiff modes 数が精度の上限を決める**。

### 4.6. FIM × precision 構成要素 — ker(G) 座標の特定

**目的**: §4.5 で定量化した stiff modes 2 方向が、precision の 3 構成要素 (Scale/Valence/Temporality) のどれに対応するかを特定する。

#### 手法

5 セッション × 19 チャンク (v07 精度データ) に対して:
1. チャンクごとの precision 構成要素を取得 (v07 results)
   - density (Scale 対応), coherence (Valence 対応), drift (Temporality 対応)
2. 各チャンクの centroid を FIM 固有空間に射影
3. FIM 上位固有ベクトル φ_i との Spearman ρ を計算

#### 結果

| FIM mode | density (Scale) | coherence (Val) | drift (Temp) |
|:---------|:---------------|:----------------|:-------------|
| φ₀ (λ=0.0032) | +0.175 | +0.115 | +0.133 |
| φ₁ (λ=0.0029) | +0.246 | +0.284 | +0.209 |

**全構成要素が弱い相関** (max|ρ| = 0.18〜0.28)。統計的に有意な相関は φ₄-coherence (r=+0.505, p<0.05) のみだが、φ₄ は sloppy mode。

#### 構成要素間相関

| 組み合わせ | Spearman ρ | p 値 |
|:----------|:-----------|:-----|
| density × coherence | **+0.653** | **0.002** |
| density × drift | +0.063 | 0.797 |
| coherence × drift | −0.380 | 0.108 |

**density と coherence が強い共線形性** (r=0.65) → embedding 空間では Scale と Valence が独立に表現されていない。

#### 解釈

§4.5「ker(G) ≥ 1 次元」の精緻化:

```
仮説 A (当初):「3 座標のうち 1 つが潰れている」
    → 棄却: 3 座標全てが stiff modes と弱い相関

仮説 B (データ支持):「3 座標が 2 方向に圧縮射影されている」
    → density と coherence の共線形 (r=0.65) が証拠:
       embedding は Scale と Valence を同一方向で表現
       drift (Temporality) は独立だが、それ自体も弱い表現
```

ker(G) の構造: **特定 1 座標の完全な崩壊ではなく、3 座標 → 2 方向への非可逆な射影**。Scale と Valence が潰れて 1 方向になり、Temporality はかろうじて残る (しかし弱い)。

⚠️ **注意**: n=19 チャンク (5 セッション) のため統計検出力が低い。N>50 での追試が必要。

---

## §5. Coherence Invariance — 溶液の均質性

### 5.1. 実験事実

τ (相転移温度) を変えても coherence は 0.807-0.815 で一定:

| 条件 | coherence range | τ 依存性 |
|:-----|:--------------|:---------|
| G∘F ON | 0.008 | **不変** |
| G∘F OFF | 0.121 | 依存 |

### 5.2. 溶媒アナロジーでの意味

溶液の浸透圧は、溶液を小分けにしても各容器で同じ (均質性)。

**Coherence Invariance は embedding 溶液の均質性を実証する。**

G∘F (merge/split 不動点操作) が「撹拌」の役割を果たし、チャンクサイズに依らない品質の均一性を保証する。

### 5.3. 設計的帰結

τ の選択は「結晶の粒度」を決めるが、「結晶の純度」は決めない。
→ τ は利用目的 (粗い要約 vs 細かい検索) で自由に選べる。品質は Fix(G∘F) が保証する。

---

## §6. 溶媒仕様書 — Embedding モデルへの要求

Hyphē 実験結果 (310+ 実験) から導出される、理想的な「認知的溶媒」への要求:

| # | 要求 | 化学的根拠 | 現状 | 対策 | 優先度 |
|:--|:-----|:---------|:-----|:-----|:------|
| 1 | **等方性** (isotropic) | 良い溶媒は全方向に均等に溶解する | ⚠️ ZCA で回復可 [6] | Whitening 済 / fine-tuning | P1 |
| 2 | **適切な極性** | like dissolves like | ❌ Scale/Valence 不溶 | task_type / fine-tuning | P1 |
| 3 | **適切な融点** | 相転移温度が制御可能 | ✅ τ* ≈ 0.720 安定 | — | — |
| 4 | **高純度** | 不純物は結晶純度を下げる | ✅ TAINT 混入 low | — | — |
| 5 | **適切な粘度** | 粘度が高いと溶解が遅い | ✅ Fix(G∘F) 1-2回収束 | — | — |
| 6 | **広い温度範囲** | 広範囲で液体を維持 | ⚠️ τ < 0.65 で崩壊 | 相転移マップの拡張 | P2 |

### 6.1. 優先順位の根拠

P1 (#1, #2) を最優先とする理由: ker(G) の2座標 (Scale, Valence) が溶けないことは Hyphē の情報保存品質の上限を規定する。τ の調整 (#3) や Fix(G∘F) (#5) は既に十分であり、ボトルネックは溶媒自体の性質。

**v0.2 更新**: #1 (等方性) は ZCA Whitening で回復可能と実験的に確認 [6]。ただし #2 (極性) は ZCA では解決不能。P1 の焦点は **#2 に移行**。

---

## 参考文献

[1] K. Friston, "The free-energy principle: a unified brain theory?," *Nature Reviews Neuroscience*, 11(2), 127–138, 2010.
[2] Hyphē PoC 実験結果分析 v2.0 — 310+ 実験, 2026-03-15.
[3] ker(G)_{Session} 分析, 2026-03-16.
[4] makaron8426, "知性は溶媒である (draft)," 2026-03-16.
[5] ROM: Hyphē 溶媒設計 — カスタム Embedding モデル・ロードマップ, Session ee3169c3, 2026-03-16. See `30_記憶｜Mneme/01_記録｜Records/g_実行痕跡｜traces/rom/rom_2026-03-16_hyphe_solvent_design.md`
[6] ZCA Whitening 実験, 365 embeddings × 768d, 5 sessions, 2026-03-16. See `60_実験｜Peira/06_Hyphē実験｜HyphePoC/whitening_results.json`
[7] FIM × precision 構成要素相関分析, 5 sessions × 19 chunks, Spearman ρ, 2026-03-16.

---

*THEORY.md v0.4 — 2026-03-16*
*Hyphē: 場⊣結晶理論 — Embedding as Solvent*

