# Linkage = 結晶化 — G∘F の本質定義

> **起源**: AY-2 セッション (2026-03-29) での Creator 指摘 4件による再構築。
> 旧理解「G∘F = テキストの機械的分割」を破壊し、「G∘F = 結晶化」に到達。

---

## 核心命題

**Linkage (Hyphē) における G∘F は、もっとも Kalon な（行為可能性という力のインスタンスを最大化させる）チャンク（情報単位）の「結晶化」（演繹的な生成）である。**

単なるテキスト分割ではない。結晶化 = 場 (意味空間) から最適な結晶 (情報単位) を析出する過程。

---

## 結晶化モデル (3ドメイン共通)

```
F (溶解): 結晶を場に戻す — 境界を溶かして自由度を回復
G (結晶化): 場から結晶を析出 — 自由度を固定して形を与える

Fix(G∘F) = これ以上溶けない結晶 = Kalon
         = AY を最大化する情報単位
```

### 忘却論との接続

G = ker(G) への商写像 = 忘却。忘却は情報を「殺す」のではなく「商空間を開く」。
商空間 = 新しい行為可能性の場。

> **忘却 (G) が行為可能性 (AY) を増大させる** — Euporía と忘却論の合流点。
> **正典参照**: linkage_hyphe.md §3 (index_op ⊣ Search), §7 (場⊣結晶), §9.1 (CPS7 定式化)

| 忘却論 (Paper II) | G∘F (Hyphē) | linkage_hyphe.md |
|:--|:--|:--|
| d = ker(d) への商写像 | G = coherence threshold への商写像 | §3 G の定義 |
| ker(d) = ℝ (定数のみ失われる) | ~~ker(G) = {Scale, Valence}~~ → **image(G) ⊇ {Scale, Temporality, Valence}** (E9c で修正) | §5 DP-3, DP-6 |
| 三角関数ループ: d の可逆性 | Fix(G∘F) の 1-2 反復収束 | §3.7 Coherence Invariance |
| d ⊣ ∫ の障害 = η の非自然性 | F ⊣ G の η も非自然的 | §3 η/ε |
| 四則演算 = 忘却の選択 (たたき台) | F/G の選択 = どの座標を忘却するかの選択 | §5 (6座標設計原則) |

### Papers I-V との拡張対応

| Paper | 核心概念 | Hyphē 射影 |
|:--|:--|:--|
| I (力としての忘却) | Φ (忘却場): 方向性忘却 → 曲率 → 力 | G の蒸留方向 = η 上の方向性忘却。F_{ij} ≠ 0 ⟺ G の蒸留に異方性がある。**E10**: image(G) 方向の ablation で因果証明 (Cohen's d=0.6-0.8)。**定理 5.8.1**: Coherence Invariance。**定理 5.9.3**: 忘却-抽象化定理。**‖F‖=g_eff·‖T‖_g** (Appendix D)。**E15**: R_crit 単調性 (87%) + 脱落順序 (rho=0.73) + Last Survivor |
| II (相補性は忘却) | CPS: U_A, U_B で二項対立を統一 | index_op ⊣ Search = CPS 事例: U_write (行為忘却), U_read (観測忘却) |
| III (Markov 圏の向こう) | α > 0 でのみ Copy/Index 可能 | ρ_MB > τ でのみ結晶化可能。**E11**: N(τ) にシグモイド型相転移、τ_c≈0.75 = α=0 臨界点 |
| IV (効果量は小さい) | Ξ spectrum の射影 → 小効果量 | Coherence Invariance = spectrum の安定性の η 射影 |
| V (繰り込みは忘却) | RG: scale μ に依存する Φ(θ,μ) | τ_cos の scale 依存 = μ_noise (linkage_hyphe.md §3.4a) |

### E9c: ker(G) の実測と仮説修正 (2026-03-29)

初期仮説「ker(G) = {Scale, Valence}」は E9c 実験で **棄却** された。

**実測結果** (13 sessions, 871 steps, 768d, τ ∈ {0.70, 0.75, 0.80}):
- **image(G) ⊇ {Scale, Temporality, Valence}**: Fisher ratio 上位 2-3 方向が 3τ で安定的にこの 3座標と相関 (Bonferroni 有意)
- **ker(G) = 座標外ノイズ**: Fisher ratio 下位方向はどの座標 proxy とも無相関
- G は embedding 空間の ~765/768 方向を事実上無視し、2-3 方向の座標的構造だけを保存する

**修正された理解**: G (結晶化/蒸留) は座標を捨てるのではなく、**座標的構造を保存し、座標に乗らないノイズを捨てる**。
ker(G) への商写像 = 忘却 → 忘却されるのはノイズであり、座標ではない。

**Paper I §5.7 に反映済み** (方向性定理 Theorem 5.1 の embedding 空間における直接検証)。

**制限**: |r| = 0.2-0.4 は弱-中程度の相関。proxy の質に律速。Function, Value, Precision の 3座標は proxy 不在。

### E10: direction-level ablation — image(G) 方向の因果的必要性 (2026-03-30)

E9 M1 PCA の上位 k 方向 (= image(G)) を embedding から射影除去し、chunker を再実行。

**核心的発見**: image(G) 方向除去 → coherence 偽上昇 + **chunk 数激減** (13→7, 20→13, 9→2)。隣接ランク方向除去ではこの現象は起きない。

| 対照群 | k=10 ΔC (τ=0.75) | chunk 数への影響 |
|:--|:--|:--|
| image(G) | +2.2% | **激減** |
| adjacent (同等分散) | +0.9% | 微減 |
| mid (中位ランク) | +0.5% | なし |
| rand768d | 0.0% | なし |

Cohen's d (image(G) vs adjacent, session pooled SD): **0.6-0.8** (中-大効果)

**解釈**: image(G) 方向 = G∘F の結晶化に因果的に必要な方向。除去すると結晶核が消失し結晶化が起きない。

**Paper I §5.7 結果2 に反映済み。**

### E11: α-τ 相転移 — 結晶化の臨界点 (2026-03-30)

τ を 0.50~0.95 (46 点, 13 sessions) で連続掃引。

| レジーム | τ | N (chunks) | Paper III 対応 |
|:--|:--|:--|:--|
| 未分化 | ≤ 0.62 | 1.0 | α < 0 (anti-copy) |
| 相転移 | 0.63-0.75 | 1→11 | α ≈ 0 (臨界) |
| 構造化 | > 0.75 | 11→33 | α > 0 (copy 可能) |

**τ_c = 0.75** (max |dN/dτ| = 223)。N が 1→33 と 33 倍変動する間、coherence は **0.806-0.818 (±0.7%)** で不変 → **Coherence Invariance Theorem (Paper I 定理 5.8.1)** の τ 全域版。

**Paper I §6.7.1 に反映済み。**

### E15+E16: R_crit 単調性 + Last Survivor (Fixed Basis) (2026-03-31)

Paper I §5.9.3 の定量的予想「α↑ → dim(image(G))↓」を直接検証。
**Fixed Basis 設計**: τ=0.65 の PCA 基底を固定し、全 τ 点で同一方向を追跡。正規化 Fisher ratio (FR/mean(FR)) で粒度 confound を除去。30 sessions, 200 PCA 方向, 46 τ 点。

| 検証項目 | 結果 | Paper I 接続 |
|:--|:--|:--|
| **A1: 単調性** | dim(image(G)) 非増加率 **86.7%** | 定量的予想 (§5.9.3) を支持 |
| **A2: 脱落順序** | Spearman(dropout_τ, FR_base) = **0.73** (p=0.011) | 公理 5.9.2 の $\mathcal{C}_E$ 実証 |
| **A3: Last Survivor** | τ=0.90 生存者 top-3 = baseline FR rank {0,1,2} | 定理 5.9.3 の実験的対応 |
| **A4: 順序安定性** | FR 順位 $\bar{\rho}$ = **0.90**, 91.3% で rho>0.7 | 公理 5.9.2 順序保存 |
| **A8: 閾値ロバスト性** | 閾値 1.5-3.0 全てで rho<-0.84, 単調率≥80% | 閾値非依存 |

核心的発見: **脱落順序が baseline FR の逆順** (rho=0.73) — 射が疎な方向から先に忘却される。定理 5.9.3 が保証する「普遍的構造の生存」の定量的メカニズムが可視化された。

**Paper I §5.9.3 に反映済み (v0.13)。**

### τ-invariance の再結晶精製モデル

τ = 結晶化温度。G∘F = 再結晶精製 (溶解→再析出の反復)。

再結晶精製が温度非依存になる条件:
**保存量 (Coherence) が制御パラメータ τ ではなく場の内在的構造 (similarity 分布の平均) で決まるとき。**

**E11 で実証**: τ = 0.50~0.95 の 46 点で coherence ≈ 0.81 ± 0.7%。G∘F の不動点 coherence $c^*$ は embedding 分布の固有量 $[C_\text{global}, \bar{s}_\text{adj}]$ 内の引力点 (Paper I 定理 5.8.1 証明)。

これは Linkage に限らない — 3ドメイン共通:

| ドメイン | 溶質 | 溶媒 | 結晶 | τ |
|:--|:--|:--|:--|:--|
| **Linkage** | テキスト内容 | embedding 空間 | チャンク | similarity threshold |
| **Cognition** | 認知操作 | WF 空間 | WF ステージ | depth (連続量) |
| **Description** | 指示内容 | 読者の解釈空間 | 指示単位 | granularity |

### Creator の4つの指摘 (2026-03-29)

1. **離散は幻想**: WF 深度 L0-L3 は恣意的離散化。連続的制御パラメータは全ドメインに存在
2. **split = 忘却 = 力の生成**: G は削るのではなく解放する (忘却論参照)
3. **統計で測れる**: 「一般論」での一貫性は統計的に問える。測定不能は怠慢
4. **Linkage も結晶化**: 3ドメインは同型。「具体/簡単」vs「抽象/難しい」の二項対立は幻影

### E14: Description ドメインの τ-Invariance (2026-03-30)

**設計**: EXPERIMENT_paper_vi.md E3' の縮小版。3 SKILL (tek/bou/noe) × 4 N (3,5,10,20) × 5 τ (0.3-0.7)。ρ = LLM-as-judge (Gemini 2.5 Flash)。120 データポイント。

**結果**:

| τ | C̄ (G∘F ON) | mean chunks |
|:--|:--|:--|
| 0.3 | 0.6599 | 1.0 |
| 0.4 | 0.6599 | 1.0 |
| 0.5 | 0.6599 | 1.0 |
| 0.6 | 0.7293 | 3.7 |
| 0.7 | 0.7293 | 3.7 |

**τ-Range (ON) = 0.070** — E11 の 0.012 より大きいが、2レジーム構造 (未分割/分割後) による段差。分割後レジーム内 (τ ∈ {0.6, 0.7}) では Range = 0.000。

| N | C̄ (G∘F ON) |
|:--|:--|
| 3 | 0.7250 |
| 5 | 0.7028 |
| 10 | 0.6583 |
| 20 | 0.6646 |

**N-Range = 0.067** — 粒度が大きい (N=3) ほど coherence が高く、細かくなると低下。ただし N=10→20 で下げ止まり (0.658→0.665)。

**解釈**:
- **τ-Invariance**: Linkage の E11 ほど精密ではないが (0.070 vs 0.012)、**G∘F が分割を実行する τ 領域内では不変** (Range=0.000)。未分割域 (τ < 0.6) ではG∘Fが恒等写像なので不変は自明。
- **N-Invariance**: 基準 0.05 を超える (0.067)。N が小さい (各チャンクが大きい) ほど「溶媒の量が多い」ので coherence が高い。これは Linkage の E11 で τ_cos が高いほど coherence が微増する傾向と同型。
- **G∘F OFF の τ-Range = 0.000**: OFF では τ を変えても何も起きない (構造探索なし)。
- **分割と coherence の関係**: G∘F が分割すると coherence が **上昇** (0.66 → 0.73)。E11 と定性的に一致 — G∘F は低 coherence 領域を切り離すことで全体の coherence を改善する。

**E11 との構造的同型**:
- Linkage E11: τ_cos が上がる → N が増える → coherence はほぼ一定 (0.806-0.818)
- Description E14: τ_ρ が上がる → chunks が増える → coherence はほぼ一定 (τ ≥ 0.6 内)

**制限事項**: E14 は縮小版 (3 SKILL, 120点)。完全版 (10 SKILL × 5 N × 5 τ = 500点、E2' Cognition の 500点) は EXPERIMENT_paper_vi.md に定義済み。LLM-as-judge の ρ が離散的 (0.5 刻みで応答する傾向) なため、Linkage の embedding cosine sim ほど滑らかな τ 掃引が得られない。

### E14b: 3ドメイン統合 CI 検証 — embedding ベース (2026-03-31)

**設計**: 同一 chunker (G∘F) + 同一 embedding モデル (all-MiniLM-L6-v2, 384d) を3種のコンテンツに適用し、CI がコンテンツタイプに依存しないことを示す。τ sweep: 0.50-0.95 (46点)。

| ドメイン | データソース | セッション数 | ステップ数 |
|:--|:--|:--|:--|
| **Linkage** | embedding_cache.pkl (セッションログ) | 13 | 871 |
| **Cognition** | Handoff ファイル (認知操作記録) | 20 | 415 |
| **Description** | Paper ドラフト + 仕様書 (構造化文書) | 20 | 2,000 |

**結果**:

| ドメイン | C̄ | CV(struct, τ>0.60) | Range(struct) | CI? |
|:--|:--|:--|:--|:--|
| **Linkage** | 0.4866 | 1.43% | 0.023 | **PASS** |
| **Cognition** | 0.3957 | 0.32% | 0.006 | **PASS** |
| **Description** | 0.4536 | 0.44% | 0.009 | **PASS** |

CI 判定基準: CV(structured) < 2%。**3ドメイン全て PASS**。

**解釈**:
- **CI は G∘F (演算子) の性質であり、溶質 (コンテンツ) の性質ではない**。重力がリンゴにも月にも等しく作用するように、G∘F はセッションログにも Handoff にも論文にも等しく CI を生じさせる。
- **C̄ の絶対値はドメインにより異なる** (0.40-0.49)。これは embedding 空間上のコンテンツの内在的構造 (similarity 分布の平均) による。CI は「C̄ が τ 非依存」であって「全ドメインで同じ C̄」ではない。
- **Cognition が最も安定** (CV=0.32%)。Handoff は S/B/A/R の構造的均質性を持つため、チャンク間の coherence 変動が小さい。
- **E14 (LLM-as-judge) との整合**: 両者とも CI を確認。E14 は離散的 ρ で段差が生じたが、E14b は連続的 cosine sim で滑らかな invariance を実証。

**Paper I §5.8 (Coherence Invariance Theorem) への含意**: 定理 5.8.1 の証明は embedding 分布の固有量に依存するが、ドメインが変わっても同じ不変性が成立する。これは証明の前提 (隣接 similarity 分布の定常性) がドメイン横断的に成立することを示す。

**関連ファイル**: `60_実験｜Peira/06_Hyphē実験｜HyphePoC/e14_3domain_ci.py`, `e14_3domain_ci_results.json`, `e14_embedding_cache.pkl`

---

## 参照

### 正典
- [linkage_hyphe.md](../../../00_核心｜Kernel/A_公理｜Axioms/linkage_hyphe.md) — **正典** (v7)。§3 (index_op ⊣ Search), §7 (場⊣結晶)

### PJ 内文書
- [TASKS_euporia_hyphe_fusion.md](../07_行為可能性｜Euporia/TASKS_euporia_hyphe_fusion.md) — AY-2 タスク定義
- [euporia_blindspots.md](../07_行為可能性｜Euporia/euporia_blindspots.md) — 結晶化モデル (C1'.1)
- [chunk_axiom_theory.typos](chunk_axiom_theory.typos) — チャンク公理 (AY 極小元定義 + v3/τ/λ/忘却接続)

### 忘却論
- Paper I draft — 力としての忘却 (Φ, F_{ij}, 方向性忘却)
- Paper II draft §1.1 — d = ker(d) への商写像, CPS 構造
- Paper III draft — α > 0 でのみ Copy 可能 (α-τ 対応)
- Paper IV draft — 効果量が小さい理由 (Ξ spectrum 射影)
- Paper V draft — 繰り込みは忘却である (RG, μ_noise)
- 四則演算は忘却の選択である (たたき台) — 忘却関手 U_abs, U_rel とセル次元階層

*Created: 2026-03-29 | Updated: 2026-03-31 (E14b 3ドメイン統合 CI + E15/E16 R_crit 単調性・Last Survivor 追記)*
*Sessions: AY-2, AY-3, AY-4*
