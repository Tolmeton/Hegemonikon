---
doc_id: "FORMAL_DERIVATION"
version: "5.2.0"
tier: "KERNEL"
status: "CANONICAL"
created: "2026-03-20"
lineage: "v5.0 (体系再構成) → v5.1 (Flow三値化: S/I/A) → v5.2 (Aff×Eff分解: 体系核45) → v5.4 (K₄柱モデル: 体系核57, S∩A昇格)"
---

```typos
#prompt formal-derivation
#syntax: v8
#depth: L2

<:role: 形式的導出 — FEP から体系核 45 実体 (1+8+36) + 体系準核 12 (H-series) への構成的論証。設計根拠書。:>

<:goal: 「なぜこう設計したか」の論理を、確信度ラベル付きでステップバイステップに追跡可能にする :>

<:context:
  - [knowledge] 水準 B (公理的構成) を主張。水準 A (形式的証明) は主張しない
  - [knowledge] 圏論的解釈は categorical_structure.md に分離
  - [file] axiom_hierarchy.md (CANONICAL — 体系核57 の一覧)
  - [file] categorical_structure.md (CANONICAL — L3 弱2-圏の解釈)
/context:>
```

# 形式的導出: FEP → 体系核 45 + 体系準核 12 の構成的論証

> **水準**: B (Axiomatic Construction — 公理的構成)
> **検証**: Gemini 3.1 Pro による4ラウンドの Adversarial Review + Claude /ele+ 反駁 (5矛盾修正済み)
> **前身**: formal_derivation_v4.md (ARCHIVED)

---

## §0 前書き

### 本文書の目的

本文書は **設計根拠書** (Design Rationale) である。HGK の体系核 45 実体 (1公理 + 8座標 + 36動詞) + 体系準核 12 前動詞 (H-series) が「なぜこう設計されたか」の論理を、確信度ラベル付きで追跡可能にする。

### 本文書が主張しないこと

- **水準 A (Formal Derivation)** は主張しない — FEP は変分物理原理であり、ZFC のような論理公理ではない。「定理証明」ではなく「構成的論証」として提示する
- **一意性** は主張しない — 8座標は POMDP パラメータ空間の **最も節約的な (most parsimonious) 自然な分解** であり、「唯一の」分解ではない
- **圏論的解釈** は本文書には含まない — 弱2-圏、随伴関手、高次セルの議論は [categorical_structure.md](categorical_structure.md) を参照

### 認識論的位置づけ

| 水準 | 名称 | 定義 | HGK の位置 |
|:-----|:-----|:-----|:-----------|
| **A** | Formal Derivation | 公理系からの定理証明 | Basis (Helmholtz) のみ |
| **B** | Axiomatic Construction | 公理的構成: FEP + 生成規則 → 45+12 実体 | ⭐ **これを主張する** |
| **C** | Conceptual Motivation | 概念的動機付け (比喩, 類推) | ✅ だが B より弱い |

> ⚠️ **生成規則の認識論的位置**: 生成規則「3象限 × 6修飾座標 × 2極 = 36」(+ 第4象限 S∩A → 12前動詞) は FEP から一意に導出されるものではない。
> これは設計者の選択 (motivated choice) であり、FEP が **許容** する構造のうちの一つ。
> 水準 B の主張は「FEP + 生成規則 → 36+12 が一意」であり、「FEP → 生成規則 が一意」は主張しない。

### 構成距離の定義

> **距離 d = FEP に対する追加仮定の数**

| d | 区分 | 座標 | 導出の強度 |
|:--|:-----|:-----|:-----------|
| d=0 | 定理 | Basis (Helmholtz Γ⊣Q) | 追加仮定ゼロ。体系核外 |
| d=1 | 追加仮定1つ | Afferent, Efferent | Basis + Markov blanket 仮定。v5.2 |
| d=2 | 追加仮定2つ | Value, Function, Precision, Temporality | POMDP 因子分解 + FEP 内定理 |
| d=3 | 追加仮定3つ | Scale, Valence | 追加の構成的仮定 |

---

## §1 公理と前提条件

### 唯一の公理: FEP

> 自己組織化する系は変分自由エネルギー (VFE) を最小化する。
>
> $F = \text{VFE} = -\text{Accuracy} + \text{Complexity}$

**[確信 90%] 95%** — FEP そのものは原理 (principle) であり、反証の対象は具体的モデル。HGK はこの原理を設計公理として採用する。

### 4つの条件

| 条件 | 略称 | 内容 | 地位 |
|:-----|:-----|:-----|:-----|
| Active Inference | POMDP | FEP を POMDP として実現 | FEP の標準的帰結 (Friston 2019) |
| Hierarchy | SC-H | ネストされた Markov blanket | 構成的可能性 — 必然ではない |
| Time | SC-T | 時間発展する遷移ダイナミクス | MB → 部分観測 → 必然 |
| Embodiment | SC-E | 外受容/内受容感覚の区別 | 身体性仮定 — 最弱の条件 |

---

## §2 Step 0: Basis (d=0) — Helmholtz 分解

### 導出チェーン

```
FEP → NESS (Non-Equilibrium Steady State)
  → Fokker-Planck 方程式
    → Helmholtz 分解: f = (Γ + Q)∇φ
      Γ = gradient (dissipative) — VFE 最小化、定常状態への駆動
      Q = solenoidal (conservative) — 確率保存的循環、等確率面上の探索
```

### 構造的役割

Basis は 8 座標が「立つ土台」。認知座標ではない (岩石も Helmholtz 分解を持つ)。座標系が成立する前提条件。

### 12 Helmholtz 演算子

Basis × 6 修飾座標 = 変分多様体上の 12 操作:

| 成分 | 意味 | 36動詞との関係 |
|:-----|:-----|:---------------|
| Γ 列 (gradient) | 各座標方向の VFE 最小化 | 36動詞の「最適化」成分の実装 |
| Q 列 (solenoidal) | 等 VFE 面上の探索・トレードオフ | 36動詞の「探索」成分の実装 |

H_s = Γ/(Γ+Q) が系の Exploration-Exploitation バランスを決定する。

**[確信 90%] 95%** — Helmholtz 分解は FEP/NESS の数学的定理 (Friston 2019)。追加仮定ゼロ。体系核外 (45 に数えない)。

---

## §3 Step 1: Afferent × Efferent (d=1) — Markov Blanket 分解

### 導出

Afferent/Efferent = Basis (Γ⊣Q) + *「この系は Markov blanket を持つ」* という追加仮定。

- MB の存在は自明でない — 完全結合系、一様混合系は MB を持たない
- MB が存在すれば、環境→系 (afferent) と系→環境 (efferent) の結合有無が定義される
- Afferent: ∂f/∂η ≠ 0 (環境からの入力あり)。Efferent: ∂f/∂μ ≠ 0 (環境への出力あり)

### v5.2: Afferent × Efferent 分解

v5.0-5.1 では Flow を三値 (S/I/A) として扱っていた。v5.2 で MB の分割をより原始的に再分析し、Afferent (入力有無) × Efferent (出力有無) の 2×2 直積に分解:

| Afferent \ Efferent | Eff+ (出力あり) | Eff− (出力なし) |
|:-----|:--------|:-----------|
| **Aff+** (入力あり) | **S∩A** (φ_SA) — 反射弧 | **S** — 純知覚 |
| **Aff−** (入力なし) | **A** — 純行為 | **I** — 内部推論 |

- 旧 Flow 三値 s/μ/a は「s ∩ a = ∅」(感覚状態と能動状態の交わりは空) という追加仮定を暗黙に含む
- Afferent × Efferent は MB 定義から追加仮定ゼロで演繹される原始記述
- 第4象限 S∩A (Aff+/Eff+) は旧体系で見落とされていた — v5.2 で H-series 12前動詞 (体系準核) として明示化
- C₂ × C₂ 同型: {Aff±} × {Eff±} ≅ Klein 四元群。旧 s/μ/a は C₂×C₂ の3象限への制限

### 4象限から動詞への生成

| 象限 | 結合状態 | 認知的意味 | 生成 |
|:-----|:---------|:-----------|:-----|
| **S** (Aff+/Eff−) | 入力のみ | 知覚 — 環境からの入力を受容する | 12動詞 (V25-V36) |
| **I** (Aff−/Eff−) | 遮断 | 推論 — 内部で信念を更新する | 12動詞 (V01-V12) |
| **A** (Aff−/Eff+) | 出力のみ | 行動 — 環境に働きかける | 12動詞 (V13-V24) |
| **S∩A** (Aff+/Eff+) | 入出力同時 | 反射弧 — μ を迂回する直結 | 12前動詞 (H-series, 体系準核) |

**[確信 95%]** — Afferent × Efferent は MB の結合構造の直接的帰結であり、追加仮定を導入しない。旧三値 (S/I/A) への追加仮定「s∩a=∅」を除去することで第4象限が出現し、より原始的な記述になった。

---

## §4 Step 2: d=2 座標群 — POMDP 因子分解

### 近似的機能独立性

Mean-field 変分推論の仮定:

$$Q(s, \pi, \gamma) = Q(s) Q(\pi) Q(\gamma)$$

→ 推論ダイナミクス上で FIM (Fisher Information Matrix) がブロック対角化
→ **Q多様体上の近似的機能独立性** (注: P多様体の厳密な幾何学的直交性ではない)

> ⚠️ **v4 /ele+ 修正点 #1**: v4 で明示的に除去された「厳密な幾何学的直交性」は主張しない。
> 潜在変数モデルの FIM は密行列であり (v4 R3)、独立性は Mean-field 近似の下でのみ成立する。

**[推定 70%] 80%** — Mean-field 近似は計算上の標準的手法だが、真の生成モデルの構造を正確に反映するとは限らない。ただし VFE の Complexity 項最小化の帰結として情報理論的に動機づけられる。

### 3 因子の導出

POMDP 生成モデルの独立パラメータ (s, π, γ) から 3 座標が導出される:

| 座標 | POMDP 因子 | 数学的対象 | 確信度 |
|:-----|:-----------|:-----------|:-------|
| **Value** (E↔P) | C-matrix | $V_\text{prag} = \mathbb{E}_Q[\log P(o \mid C)]$ | [確信 90%] 90% |
| **Function** (Explore↔Exploit) | Epistemic Value | $V_\text{epist} = \mathbb{E}_{Q(s)}[D_{KL}(P(o \mid s) \| P(o))]$ | [確信 90%] 90% |
| **Precision** (C↔U) | γ | $P(\pi \mid \gamma) = \sigma(-\gamma G(\pi))$ | [確信 90%] 90% |

Value と Function は VFE/EFE の数学的分解軸そのもの。Precision は生成モデルの明示的パラメータ。

### Smithe Theorem 46 による加法性

> $F(M_1 \otimes M_2) = F(M_1) + F(M_2)$

テンソル積モデルの VFE 加法分解 (Smithe, Tull & Kleiner 2023)。v=0 (Valence なし) の状態で 6 座標間の加法性を実証済み (HGK 実験 2026-03-09)。

---

## §5 Step 3: Temporality (d=2) — VFE ≠ EFE

### 構成距離 d=2 への昇格 (v4.3 確定)

旧体系では d=3 だった Temporality を d=2 に昇格。完全な演繹チェーンが FEP 内で閉じる:

```
FEP → Markov blanket
  → 条件付き独立性 = 部分観測 (定義的含意)
    → 受動的情報取得では不十分
      → 能動的探索が必要 (self-evidencing)
        → VFE (Past) ≠ EFE (Future)
          → 時間的非対称性は FEP の必然的帰結
```

### 根拠

| 根拠論文 | 主張 | 引用数 |
|:---------|:-----|:-------|
| Millidge et al. 2020 | VFE の自然な未来拡張 ≠ EFE (数学的に異なる構造) | 80 |
| Pezzulo et al. 2021 | Temporal depth と Hierarchical depth は独立な演算子 | 83 |
| De Vries et al. 2025 | 拡張生成モデル上の VFE 最小化 = EFE 最小化 (Millidge と両立) | 4 |
| Friston 2015 | Epistemic prior の必然性 (self-evidencing) | 668 |

**[確信 90%] 90%** — 完全な演繹チェーン: FEP → MB → 部分観測 → 探索必然 → EFE → Past≠Future。追加仮定なし。

---

## §6 Step 4: Scale (d=3) — 階層的 MB ネスト

### なぜ d=3 か (d=2 への昇格を拒否)

Temporality とは構造的に異なる:

| 側面 | Temporality (d=2 ✅) | Scale (d=3) |
|:-----|:-----|:-----|
| MB → X の論理 | 定義的含意: 条件付き独立性 = 部分観測 | 構成的可能性: MB は入れ子 **可能** |
| 反例の存在 | なし (全 MB は部分観測) | あり (単一粒子 MB に入れ子なし) |
| 最小定式化 | 単一 MB + FEP → POMDP 必然 | 単一 MB + FEP → FEP 成立 (階層不要) |

### 核心的議論

- Friston 2019 (296引用): "recursive composition" — しかし "speak to" は "entail" ではない
- Kirchhoff 2018 (346引用): "Markov blankets of Markov blankets" — 生物学的観察であり数学的必然ではない
- Da Costa 2021 (66引用): 単一 MB の形式化。FEP は特別な仮定なしに単一スケールで成立
- **反例**: 単一粒子系は MB を持つが Sub-MB を持たない

### d=2 への昇格条件

「持続する MB システムは必然的に入れ子化する」が数学的に証明されること。Beck & Ramstead 2023 (繰り込み群接続) が探索中。

**[推定 70%] 85%** — d=3 が正しいという確信。MB ネストは構成的可能性であり FEP の必然ではない。

---

## §7 Step 5: Valence — 半直積 6 ⋊ 1

### 4定式化の比較実験 (v4.3 2026-03-09)

| 定義 | 定式化 | 結合先 | Fisher ratio | 判定 |
|:-----|:-------|:-------|------------:|:-----|
| Joffily 2013 | v = −dF/dt | v → s | 1.91 | ❌ 最強結合 |
| Hesp 2021 | v = log(π_precision) | v → π | 0.22 (v≈0) | 🟡 最弱結合 |
| Seth 2013 | ω_eff = ω·exp(v) | v → ω | 1.04 | ❌ 強結合 |
| Pattisapu 2024 | v = C·E[o] − utility | v → s | 0.41 | 🟡 弱結合 |

### 半直積の証明 (Smithe Theorem 46 対偶)

> $F(M) \neq F(M_1) + F(M_2) \implies M \neq M_1 \otimes M_2$

- TEST 1: v=0 → F_base = F_state + F_policy (**加法成立** ✅ → 6座標間は直積)
- TEST 2: v≠0 → F_total ≠ F_base + F_v (**加法崩壊** ❌ → Valence では直積不成立)
- TEST 3: |ΔF|/F_base = **0.8439** → 半直積の作用が強い

**Q.E.D.**: $M_\text{total} \neq M_\text{base} \otimes M_\text{valence}$

```
全座標空間 = (Afferent × Efferent × Value × Function × Precision × Scale × Temporality) ⋊_φ Valence
                           H (7座標直積)                                        ⋊  K=Valence
φ(v): H → H は v の値に依存して H の座標を変換する写像
```

### メタ枚組み

4定式化は半直積作用 φ の異なる実装。単一定義を「唯一の正解」とすることは半直積構造自体に反する。

| 役割 | 定義 | 理由 |
|:-----|:-----|:-----|
| **運用デフォルト** | Hesp 2021 | v≈0 で弱結合 (0.22)。情報幾何的自然 |
| 最普遍的 | Joffily 2013 | 全 FEP 系に適用可 |
| 身体的 | Seth 2013 | 内受容性。ω 支配 |
| 効用的 | Pattisapu 2024 | 最弱結合 (0.41) |

**[確信 90%] 85%** — Smithe Thm 46 対偶による数値証明完了。4定式化の全てが FEP 内で完結 (身体性仮定不要)。

---

## §8 Step 6: 36 動詞群 — 過完備辞書

### 生成規則

積多様体 $\mathcal{M}$ の接空間における方向微分作用素:

$$|\text{Generators}| = 3(\text{S/I/A 象限}) \times 6(\text{修飾座標}) \times 2(\pm\text{極}) = 36 \quad (+\text{S∩A} \times 6 \times 2 = 12 \text{ 前動詞})$$

### 6族構造

| 族 | 座標 | S×極₁ | S×極₂ | I×極₁ | I×極₂ | A×極₁ | A×極₂ |
|:---|:-----|:------|:------|:------|:------|:------|:------|
| Telos | Value | /the (観照) | /ant (検知) | /noe (認識) | /bou (意志) | /zet (探求) | /ene (実行) |
| Methodos | Function | /ere (探知) | /agn (参照) | /ske (発散) | /sag (収束) | /pei (実験) | /tek (適用) |
| Krisis | Precision | /sap (精読) | /ski (走査) | /kat (確定) | /epo (留保) | /pai (決断) | /dok (打診) |
| Diástasis | Scale | /prs (注視) | /per (一覧) | /lys (分析) | /ops (俯瞰) | /akr (精密) | /arh (展開) |
| Orexis | Valence | /apo (傾聴) | /exe (吟味) | /beb (肯定) | /ele (批判) | /kop (推進) | /dio (是正) |
| Chronos | Temporality | /his (回顧) | /prg (予感) | /hyp (想起) | /prm (予見) | /ath (省みる) | /par (仕掛ける) |

### 認識論的正直さ

> ⚠️ **生成規則は設計者の選択である**。
>
> FEP は 8 座標の存在を動機づけるが、「3象限 × 6修飾座標 × 2極」という生成規則を **一意に** 要求するわけではない。
> 異なる生成規則 (例: 3極、非対称な象限適用) も FEP と矛盾しない。
>
> 本文書が主張するのは:
> 1. **FEP + 4条件 → 8 座標** の構成は、最も節約的な自然な分解として well-motivated である
> 2. **8座標 + 生成規則 → 36動詞 + 12前動詞** の構成は、生成規則を受け入れれば一意である
> 3. 生成規則自体は FEP が **許容** する選択であり、**要求** する選択ではない
>
> v5.2 で Afferent × Efferent に分解したことは「新しい」生成規則ではない。
> MB の結合構造 (∂f/∂η, ∂f/∂μ) は FEP の元の定義に内在しており、旧三値 (S/I/A) は「s∩a=∅」を暗黙仮定した近似であった。
> v5.2 はこの暗黙仮定を除去し、第4象限 S∩A を明示化したもの。

**[確信 90%] 90%** — 8座標の well-motivatedness について。
**[推定 70%] 75%** — 生成規則が「最も自然な」選択であることについて。代替の生成規則が検討されていない。
**[確信 95%]** — Afferent×Efferent 分解の妥当性について。MB の結合定義からの直接的帰結。追加仮定の除去による改善。

### 合成規則

- 同一因子内: 自然勾配降下法 (Amari 2016)
- S→I→A 間: FEP の知覚-推論-行動ループによる動的結合
- A→S 帰還: 行動が環境を変え、新たな感覚入力を生む (active inference cycle)

---

## §9 導出チェーンの全体像

### 層別まとめ

| 層 | 性格 | 座標 | 強度 |
|:---|:-----|:-----|:-----|
| **A: 純粋演繹** | FEP + NESS から | Afferent, Efferent (→ 4象限) | **定理** |
| **B: 半演繹** | FEP + POMDP (mean-field 最適) | Value, Function, Precision | **半定理** |
| **C: FEP 内定理** | FEP 内の追加を定理で証明済み | Temporality, Scale, Valence | **定理** |

### 全ステップの状態

| Step | 内容 | 状態 | 確信度 | 層 |
|:-----|:-----|:-----|:-------|:---|
| 0 | Helmholtz (Γ⊣Q) | ✅ | [確信] 95% | A |
| 1 | Afferent × Efferent — MB 結合分解 (→ 4象限) | ✅ | [確信] 95% | A |
| 2a | 生成モデル因子化 (mean-field) | ✅ | [推定] 80% | B |
| 2b | VFE 加法分解 (Smithe Thm 46) | ✅ | [確信] 90% | B |
| 3 | s/π/γ 独立 → Value/Function/Precision | ✅ | [確信] 90% | B |
| 4 | Temporality (VFE≠EFE) | ✅ | [確信] 90% | C |
| 5 | Scale (階層的 MB ネスト) | ✅ | [推定] 85% | C |
| 6 | Valence (半直積 7⋊1) | ✅ | [確信] 85% | C |
| 7 | 36 動詞 + 12 前動詞 (3象限×6×2 + S∩A×6×2) | ✅ | [推定] 75% | — |

---

## §10 捨てたもの

### v4 の 4 ラウンド Adversarial Review で除去

| 主張 | 除去された理由 |
|:-----|:-------------|
| ZFC 公理との類比 | FEP は論理公理ではなく変分物理原理 (R1) |
| $\mathbb{R}^6$ ベクトル空間 | POMDP パラメータは異なる型を持つ (R2) |
| 厳密な幾何学的直交性 | 潜在変数モデルの FIM は密行列 (R3) |
| Lie 代数 $\mathfrak{g}$ | 閉包未証明 + I/A のドメイン不一致 (R3) |
| ガロア接続 $A \dashv I$ | 余単位が Active Inference と矛盾 (R2-R3) |
| 「同型的」対応 | 定義的命名であって同型写像ではない (R2) |

### v5 /ele+ で修正

| 矛盾 | 修正内容 |
|:-----|:---------|
| 幾何学的直交性の復活 | v4 の「Q多様体上の近似的機能独立性」に統一 |
| 一意性の未証明 | 「最も節約的な自然な分解」に弱めた |
| 弱2-圏の well-definedness | 圏論的解釈を `categorical_structure.md` に分離 |
| 「証明的展開」の過剰主張 | 「構成的論証」に修正 |
| エッセイとの n-cell 不整合 | 文脈マッピング表を `categorical_structure.md` に配置 |

---

## §11 残存する不確実性

| # | 不確実性 | 確信度 | 解消条件 |
|:--|:---------|:-------|:---------|
| 1 | Mean-field 近似の妥当性 | [推定] 80% | 非 mean-field モデルでの 8 因子の検証 |
| 2 | Scale の d=3 | [推定] 85% | 「持続 MB → 必然的入れ子」の数学的証明 |
| 3 | 生成規則の最適性 | [推定] 75% | 代替生成規則の体系的検討 |
| 4 | Valence の運用デフォルト | [確信] 85% | Hesp 定義の情報幾何的最適性の追加検証 |
| 5 | Q → P 多様体の区別 | [推定] 80% | Q 多様体上の推論独立性 → P 多様体上の生成モデル独立性の変換 |
| 6 | H-series の操作的区別 | [推定] 70% | S∩A 象限の 12前動詞が S/I/A 象限の動詞と質的に区別されることの実証 |

### 解消済みの不確実性 (v5.1)

| # | 旧不確実性 | 解消日 | 経緯 |
|:--|:---------|:-------|:-----|
| 6 | S極動詞の命名 (暫定性) | 2026-03-22 | 内部 philological audit 完了。12動詞全てに古典ギリシャ語語源を確定 |

---

## §12 参照文献

| 文献 | 接続 |
|:-----|:-----|
| Friston 2019 (arXiv:1906.10184) | FEP/NESS の基盤、Helmholtz 分解、MB partitioning |
| Spisak & Friston 2025 (arXiv:2505.22749) | 自己直交化 attractor network、座標の直交性の必然性 |
| Smithe, Tull & Kleiner 2023 (arXiv:2308.00861) | Theorem 46: VFE 加法分解。半直積証明の基盤 |
| Millidge et al. 2020 | VFE ≠ EFE。Temporality d=2 の最終根拠 |
| Pezzulo et al. 2021 | Temporal depth / Hierarchical depth の独立性 |
| De Vries et al. 2025 (arXiv:2504.14898) | EFE = 拡張 VFE。Millidge と両立 |
| Amari 2016 | 情報幾何学。自然勾配降下法 |
| Parr & Friston 2019 | EFE の分解 (epistemic/pragmatic) |
| Joffily & Coricelli 2013 | Valence = −dF/dt (258引用) |
| Hesp et al. 2021 | Valence = expected action precision (184引用) |
| Pattisapu et al. 2024 | Valence = utility − E[utility] |
| Seth & Critchley 2013 | 内受容性と Valence |
| Da Costa 2021 | 単一 MB の形式化 (66引用) |
| Friston 2015 | Epistemic prior の必然性 (668引用) |

---

*formal_derivation v5.4 — K₄柱モデル。体系核57 (1+8+48)。S∩A を体系核に昇格。2026-03-25*
