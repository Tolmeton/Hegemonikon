---
doc_id: "TYPOS-HYPHE-MAP"
version: "2.0.0"
tier: "NOUS"
status: "CONFIRMED"
created: "2026-03-13"
updated: "2026-03-17"
origin: "Session df9fdd10 (Euporía 盲点分析) → Session 37b0b80c (Basis 同定・Creator 確定)"
---

# Týpos = Hyphē|_{1D-faithful}

> Týpos は Hyphē (場の結晶化理論) の **1次元 (テキスト) への忠実充満射影** である。
> Hyphē が一般的な「多次元情報の結晶化理論」なら、Týpos はそのテキスト記述への特殊化。

## 0. 理念定義 — TYPOS とは何か

> **[DECISION]** Creator 確定 (2026-03-17, Session 37b0b80c)
> SOURCE: `rom_2026-03-17_typos_basis_universality.md` §3, §7

### 一語定義

**TYPOS = 多次元の情報 (溶液) を 1次元 (テキスト) に結晶化する、最も Kalon な記述方式**

### 狭義/広義

| 定義 | 内容 | 圏論的表現 |
|:-----|:-----|:-----------|
| **狭義** | 最も Kalon な右随伴 G (結晶化関手) | argmax_G Fix(G∘F) |
| **広義** | Hyphē の構造を忠実充満に射影した「1次元の射」 | Hyphē\|_{1D-faithful} |

- 狭義の TYPOS は **G (結晶化)** のみ — 「テキストにどう書くか」の方式
- 広義の TYPOS は F (溶解/読取) も含む — 読み手が結晶から構造を復元する過程も含む
- F は読み手に依存 → 左随伴の不確定性として許容
- 良い G は F の選び方を構造的にガイドする (Python の「読みやすさ」と同構造)

### 随伴構造: F ⊣ G

```
F (溶解 = 読取)         G (結晶化 = 記述)
1DText ──────────→ CogSpace ──────────→ 1DText
       左随伴 (自由)           右随伴 (忘却)

F ⊣ G:
  η: Id_{1DText} → G∘F  — テキストを読んで再記述 ≥ 元テキスト (情報が増える)
  ε: F∘G → Id_{CogSpace} — 認知を記述して再読取 ≤ 元認知 (情報が減る)
```

| 射 | 方向 | 意味 |
|:---|:-----|:-----|
| **F** | Text → CogSpace | テキストを読み、多次元の認知空間に展開 (溶解) |
| **G** | CogSpace → Text | 認知空間からテキストに結晶化 (記述) |
| **Fix(G∘F)** | G∘F(t) = t | 読んで書き直しても変わらないテキスト = **Kalon な記述** |

### Basis: 結晶化関手 G⊣F

TYPOS の Basis = **結晶化関手 G⊣F** (CogSpace → Text ⊣ Text → CogSpace)

- HGK の Basis = Helmholtz **分解** (ベクトル場 → Γ + Q)
- TYPOS の Basis = 結晶化 **射影** (多次元場 → 1次元テキスト)
- 「分解 vs 射影」は左右随伴の始点の違い:
  - 右随伴 (G) から見る → 射影 (多 → 少)
  - 左随伴 (F) から見る → 分解 (少 → 多の逆)

### Hyphē の次元族としての TYPOS

```
Hyphē (多次元場の結晶化理論)
  │
  │── |_{1D-faithful}  ← TYPOS (テキスト記述)
  │
  │── |_{2D-faithful}  ← (仮想: 図表・ダイアグラム記述理論)
  │
  └── |_{nD-faithful}  ← (仮想: 多感覚伝達理論)
```

### 「最も Kalon な」の意味

TYPOS が argmax_G であるとは:

- 候補集合 S = {Markdown, XML, YAML, plain text, ...} の中で
- Fix(G∘F) の不動点が最も豊か (Generative) であり
- 構造の忘却が最も少ない (faithful) もの
- [仮説 50%]: 定量的実証は未完了 (比較実験 `typos_current_state.md` §6 参照)

### §0.1. F ⊣ G の定式化 — 読取と記述の随伴

> Linkage §3 (index_op ⊣ Search) と同構造。TYPOS ドメインへの射影。

#### 前順序圏 T

```text
T = (テキスト空間, ≤)
  対象: t = (構文木, 意味構造, ディレクティブ集合, メタデータ) の各構成
  順序: t₁ ≤ t₂ ⟺ Sem(t₁) ⊆ Sem(t₂)
  Sem(t) = {s ∈ CogSpace | 読み手 r が t から復元可能な意味の集合}
         = ディレクティブ解釈 ∪ 構造的関係 ∪ 暗黙の前提 ∪ 実行可能な行動
         (読み手 r に依存 — 理想的読み手 r* で不動点を定義)
```

#### F, G の定義

```text
F: T → T  (左随伴 = 溶解/読取)
  F(t) = t を読み、認知空間で展開し、再構成したテキスト
       = ディレクティブの意味展開, 暗黙の前提の明示化, 構造的関係の追加
       ≠ 外部知識の追加 (← 入力は t のみ)

G: T → T  (右随伴 = 結晶化/記述)
  G(t) = t の意味を保存しつつ、最小かつ構造的なテキストに蒸留
       = 冗長表現の除去, ディレクティブへの構造化, 意味の圧縮
```

> **endofunctor 選択の根拠**: Linkage §3 と同じく endofunctor (F, G: T → T) を採用。
> 異圏間定式化 (F: T → CogSpace, G: CogSpace → T) では η の方向が反転する。
> endofunctor にすることで η: Id ≤ G∘F (HGK 標準) と一致。

#### η/ε の成立根拠

```text
η: t ≤ G(F(t))  — 読解→再記述 ≥ 元  (意味が増える)
ε: F(G(t)) ≤ t  — 蒸留→再読解 ≤ 元  (意味を超えない)
```

**η 成立根拠**: t を読んで認知空間で展開 (F) すると暗黙の構造が顕在化する。
それを再記述 (G) すると `<:context:>` や `<:constraints:>` として明示化される。
→ Sem(G(F(t))) ⊇ Sem(t)。読んで書き直すと**情報が増える**。

**ε 成立根拠**: G(t) は t の意味を圧縮するため Sem(G(t)) ⊆ Sem(t)。
F は入力テキストのみから再構成するため (外部知識不使用)、
F(G(t)) は G(t) の内容を超えない → Sem(F(G(t))) ⊆ Sem(t)。

> **ε の成立条件**: F が「テキストの内容のみから再構成」に限定されるとき成立。
> Periskopē 等の外部検索を許すと ε は破れる。Linkage の F_semantic 制約と同構造。

#### Fix(G∘F) = TYPOS の Kalon

```text
Fix: G(F(t)) = t
= 読んで書き直しても変わらない
= 全ての意味が構造として明示され、全ての構造が意味を持つ
```

**三属性の TYPOS 版**:

| 属性 | TYPOS 射影 | Linkage 射影 (参照) |
|:-----|:-----------|:-------------------|
| Fix(G∘F) | 読んで書き直しても変わらない | リンクを足しても刈っても変わらない |
| Generative | この記述から3つ以上の使用・解釈・展開が生まれる | 3つ以上の検索・発見パターン |
| Self-referential | TYPOS が自身のディレクティブで自身の規則を定義する | 索引自体がメタデータとして機能 |

#### Drift 定義

```text
Drift(t) = d(G∘F(t), t) / d_max
  d は意味的距離 (例: embedding cosine distance, 構造差分)
  < 0.1: 良好 (Fix に近い) / 0.1-0.3: 注意 / > 0.3: 要改善

Fix 条件: Drift = 0 ⟺ Sem(G∘F(t)) = Sem(t) ⟺ G(F(t)) = t
```

η: t ≤ G∘F(t) は Sem(t) ⊆ Sem(G∘F(t)) を保証する。
Drift は **G∘F が t をどれだけ超えるか** (情報の増分) を測る。
Fix では増分 = 0 なので Drift = 0。Fix 接近を検出可能。

#### η/ε の実装的意味

| 射 | 方向 | 意味 | TYPOS 実装 |
|:---|:-----|:-----|:-----------|
| **η: Id ≤ G∘F** | 読解→再記述 ≥ 元 | 読んで再構成すると意味が**増える** | `<:context:>` 等の暗黙知が明示化される |
| **ε: F∘G ≤ Id** | 蒸留→再読解 ≤ 元 | 蒸留→再読解は元を**超えない** | F がテキスト内容限定なら Sem ⊆ 元 |
| **Fix** | G∘F = Id | 読んで書き直しても不変 | **冗長ゼロ・欠落ゼロ** |

#### Linkage §3 との対応

| 構造 | Linkage (索引ドメイン) | TYPOS (記述ドメイン) |
|:-----|:-----|:-----|
| 前順序圏 | P = (知識状態, ⊆ by Disc) | T = (テキスト空間, ⊆ by Sem) |
| 左随伴 F | index_op (構文的索引追加) | 読取 (意味展開 + 再構成) |
| 右随伴 G | search-distill (蒸留) | 記述 (構造化 + 圧縮) |
| η | Disc が拡張 | Sem が拡張 (暗黙知の明示化) |
| ε | F が構文的なら Disc ⊆ 元 | F がテキスト内容限定なら Sem ⊆ 元 |
| Fix | 冗長ゼロ・不足ゼロ (索引) | 冗長ゼロ・欠落ゼロ (記述) |
| Drift | \|Disc 増分\| / \|Disc 全体\| | d(G∘F(t), t) / d_max |

> [推定 80%]: 定式化は Linkage §3 との構造的対応が明確。
> ε の成立条件 (F の入力限定) は Linkage の F_syntactic 制約と同型。
> 定量的 Drift の測定は未実装 ([仮説] §0 の argmax 実証と連動)。

---

## 1. 結晶化モデル

```
F (溶解 = Explore)        G (結晶化 = Exploit)
CogSpace (多次元) ──→ Hyphē field (潜在空間) ──→ .typos (1次元テキスト)
```

- **F**: 認知的意図を多次元の場に展開する (溶解)
- **G**: 場から Týpos 文法に従って結晶化する (収束)
- **Fix(G∘F)**: Kalon な `.typos` ファイル — 溶かして再結晶化してもこれ以上変わらない

### Description = スナップショット

Creator の定式化: 「その場その場の結晶、いわばスナップショットが記述だ」

`.typos` ファイルは場の特定時点のスナップショット結晶。
時間的変化や空間的整合は結晶の中にはない — **ker(G) = {Temporality, Scale}**。

## 2. 実装対応: `generate_typos()` = G (結晶化関手)

`typos_mcp_server.py` の `generate_typos()` (L392-693) は G の実装:

### F (溶解): 入力 → 場

| F のステップ | 実装 | 意味 |
|:--|:--|:--|
| 自然言語の分解 | `extract_task_context()` | 動詞・対象・タスクタイプに展開 |
| ドメイン検出 | `detect_domain()` | 4ドメインの場の座標を決定 |
| 収束/発散判定 | `classify_task()` | Function 軸 (Explore↔Exploit) の位置を決定 |

### G (結晶化): 場 → .typos

| G のステップ | 実装 | 意味 |
|:--|:--|:--|
| ロール結晶化 | `<:role:>` 生成 | 場の Value 座標を 1 行に凝縮 |
| 制約結晶化 | `<:constraints:>` 生成 | 場の Precision 座標を制約リストに凝縮 |
| 文脈結晶化 | `<:context:>` 生成 | 場の参照構造を宣言的に凝縮 |
| 評価結晶化 | `<:rubric:>` 生成 | 場の Valence 座標をスケールに凝縮 |
| 例示結晶化 | `<:examples:>` 生成 | 場の Function 座標を具体インスタンスに凝縮 |
| 活性化結晶化 | `<:activation:>` 生成 | 場の Scale 座標を適用条件に凝縮 |

### 他形式 → Týpos = アニーリング (再結晶化)

```
Markdown (非 Kalon 結晶) → F⁻¹ (融解) → Hyphē field → G_typos → .typos (Kalon 結晶)
```

MCP ツール `generate` の入力は自然言語 requirements (非 Kalon な 1D テキスト)。
これを場に溶かし (extract_task_context)、Týpos 文法で再結晶化する (generate_typos)。

## 3. ker(G) と盲点の再分類

### ker(G) = 結晶が「正しく捨てる」もの

| ker(G) | 意味 | 担当 |
|:--|:--|:--|
| Temporality | 結晶は時刻を持たない | Mneme (ROM/Handoff) |
| Scale | 個別結晶は体系を知らない | Dendron (MECE チェック) |

### 射の不在 = Hyphē field 界面の課題

| 射 | 不在 | 解決案 |
|:--|:--|:--|
| Týpos → Mneme | `.typos` の意味的変更履歴 | Git semantic diff + 24 命題によるフラクタル記録 |
| Dendron → Týpos | `.typos` 群の制約 MECE 検査 | Hyphē field 内での結晶間干渉検査 |

## 4. Hyphē field の形式化

> SOURCE: `rom_2026-03-13_hyphe_field_crystal.md` (session 164ceafc)

### 場の定義 (Hyphē §1)

> **[DEF]** 場 = 情報の embedding 空間。テキストをベクトル化して高次元空間に配置。
> 情報はこの空間内の密度分布として存在する。

> **[DEF]** 結晶化 = Markov Blanket の自発形成。
> 場の中で統計的独立性の境界が自己組織化される過程。

Týpos における解釈:

| Hyphē 一般 | Týpos (Description 射影) |
|:--|:--|
| 場 = embedding 空間 | 認知的意図の潜在表現 (CogSpace) |
| 結晶 = MB が形成された領域 | `.typos` ファイル (1D テキスト) |
| 温度 T = Scale パラメータ | Týpos の深度 (`#depth: L0-L3`) |
| ΔG < 0 = 結晶化条件 | L(c) < threshold |

### L(c) 損失関数 (Hyphē §2 — 正式定義)

```
L(c) = λ₁ · ||G∘F(c) - c||²  +  λ₂ · (-EFE(c))
       ─────────────────────     ──────────────────
       Drift項 (不動点距離)        EFE項 (展開可能性)
```

> **[DEF]** L(c) = 0 ⟺ c は Kalon

| 項 | 数式 | Týpos での操作的意味 |
|:--|:--|:--|
| **Drift** | ‖G∘F(c) - c‖² | `.typos` を溶かして再結晶化したとき、どれだけ変わるか |
| **I_epistemic** | KL[P(world\|c) ‖ P(world)] | `.typos` を読むと認知モデルがどう変わるか |
| **I_pragmatic** | \|Hom(F(c), −)\| | `.typos` から何ができるか (compile, expand, generate) |

Týpos 固有の解釈:
- **Drift ≈ 0**: `.typos` を generate → parse → compile → expand → re-generate しても同じ構造に戻る
- **EFE > 0**: `.typos` は compile して使える、expand して読める、parse して検証できる
- **argmin L(c)**: 最小十分な構造で最大の意図再現 = Kalon な `.typos`

### 結晶化 = 射影 + Kalon 選択

G: H → Text は全射 (surjective) だが単射 (injective) ではない。
複数の場の状態が同一のテキストに射影される。
Kalon な結晶 = G の右逆 (section) の中で Fix(G∘F) を満たすもの。

### 4.5 Hyphē 場の PDE (反証4 への回答)

> SOURCE: Possati 2025 (arXiv:2506.05794) "Markov Blanket Density and Free Energy Minimization"

**[DISCOVERY]** Hyphē 場の駆動力方程式は **MB density で調節された勾配降下** (Modulated Gradient Descent)。

#### 場の数学的構造

| 概念 | 数学 | Hyphē での意味 |
|:--|:--|:--|
| 空間 Ω | 統計多様体 X (Fisher-Rao 計量装備) | embedding 空間 |
| MB density ρ(x) | ρ(x) = 1 - I(I;E\|B) / (I(I;E) + ε) | 点 x での情報的遮蔽度 |
| VFE 場 F(x) | F(x) = E_q[ln q_μ(s\|x) - ln p(s,η\|x)] | 点 x での予測と実際の乖離 |

#### 駆動力方程式 (PDE)

```
ẋ(t) = -(1 - ρ(x)) · ∇F(x)
```

| 条件 | ρ(x) | 動き | Hyphē 解釈 |
|:--|:--|:--|:--|
| 完全結合 | 0 | 最大勾配降下 | 情報が「液体」→ 自由に流れる |
| 部分遮蔽 | 0〜1 | スロットリング | 結晶化の途中 — 一部固化、一部流動 |
| 完全分離 | 1 | 運動停止 (ẋ=0) | **結晶完成** — MB が完全に閉じた |

> **[INSIGHT]** 結晶化 = ρ(x) が 0 → 1 に遷移する過程。
> ρ = 1 の領域 = Markov Blanket が閉じた = **チャンク (結晶)** が形成された。
> Fix(G∘F) = ρ(x*) = 1 かつ ∇F(x*) = 0 の点 = **Kalon な結晶**。

#### Týpos への移植

| Possati | Hyphē 一般 | Týpos (Description) |
|:--|:--|:--|
| ρ(x) → 1 | MB 形成 → 結晶化 | `.typos` ファイルの構造が安定 |
| ρ(x) → 0 | 結合 → 溶解 | 記述が流動的 (draft 段階) |
| ∇F(x) = 0 | VFE 極小 | 意図の再現誤差が最小 |
| ẋ = 0 | 不動点 | generate → parse → compile → expand → re-generate で不変 |
| 温度 T ↑ | ρ を下げる擾乱 | `#depth: L0` (粗い結晶化) |
| 温度 T ↓ | ρ を上げる駆動 | `#depth: L3` (精密な結晶化) |

#### L(c) と PDE の接続

```
L(c) = λ₁ · ||G∘F(c) - c||²  +  λ₂ · (-EFE(c))
         ↕                         ↕
      ∇F(x*) = 0 の条件        ρ(x*) = 1 の条件
      (予測誤差最小)            (MB が閉じた)
```

L(c) の2項は PDE の2つの停止条件に対応する:
- **Drift = 0** ⟺ ∇F(x) = 0 (VFE 勾配がゼロ = 極小点)
- **EFE 最大** ⟺ ρ(x) → 1 (結晶が閉じて展開可能な内部構造を持つ)

#### 参考文献

- Possati 2025 (arXiv:2506.05794): MB density の定義・PDE 導出・FEP との接続
- Beck & Ramstead 2025 (arXiv:2502.21217): Dynamic MB Detection アルゴリズム

### 4.6 結晶化アルゴリズム (未解決問題 #4 への回答)

> SOURCE: Beck & Ramstead 2025 (arXiv:2502.21217) "Dynamic Markov Blanket Detection for Macroscopic Physics Discovery"

**[DISCOVERY]** Beck & Ramstead の Dynamic MB Detection は Hyphē の結晶化アルゴリズムの直接的候補。

#### Beck & Ramstead アルゴリズムの核心

```
微視的観測 (particle dynamics)
    → variational Bayesian EM
    → Bayesian attention でラベリング (internal / boundary / external)
    → 巨視的オブジェクト (MB が閉じた領域) を検出
    → 巨視的法則 (オブジェクト間相互作用) を識別
```

##### 3つの構成要素

1. **Generative Model**: 微視的要素の振る舞いを確率的に記述
2. **Variational Bayesian EM**: 潜在変数 (どの要素がどのオブジェクトに属するか) を推論
3. **Bayesian Attention**: 各要素を internal / boundary / external に動的にラベリング

##### 特徴
- **教師なし** — ラベルは事前に与えない
- **動的** — ラベルは時間とともに変化 (物体が移動・変形する)
- **階層的** — 巨視的 "法則" も同時に推論

#### Hyphē 結晶化への移植

| Beck & Ramstead | Hyphē |
|:--|:--|
| 微視的要素 (particles) | embedding 空間上のトークン / 文 / 段落 |
| 巨視的オブジェクト (MB) | **チャンク (結晶)** |
| Bayesian attention ラベル | internal (チャンク内部) / boundary (チャンク境界) / external (チャンク外) |
| 巨視的法則 | **チャンク間の関係** (リンク、参照構造) |
| 時間的動態 | 情報追加時のチャンク境界の再編成 |

#### Týpos 結晶化への特殊化

| Hyphē 一般 | Týpos (Description) |
|:--|:--|
| 微視的要素 = トークン | requirements テキストの語彙単位 |
| MB 検出 = チャンク形成 | generate_typos() の domain/task 分類 |
| Bayesian attention | ディレクティブ型分類 (`<:role:>`, `<:constraints:>`, etc.) |
| 巨視的法則 | `.typos` 間の `@extends`, `@mixin` 関係 |
| 動的再編成 | `generate` → `validate` → `parse` → `re-generate` ループ |

#### Possati PDE + Beck & Ramstead の統合

```
Phase 1: ρ(x) の計算 (Possati)
  → embedding 空間の各点で MB density を推定

Phase 2: MB 検出 (Beck & Ramstead)
  → ρ(x) ≈ 1 の領域を自動的に検出・ラベリング
  → variational Bayesian EM で最適な境界を決定

Phase 3: 結晶化 (Hyphē → G)
  → 検出された MB 領域を .typos ディレクティブに射影
  → L(c) を最小化する結晶を選択
```

> **[INSIGHT]** Possati が「場はどう動くか」(PDE)、Beck & Ramstead が「結晶はどこにできるか」(検出)。
> 2つの論文は Hyphē の異なる側面を解決する相補的な理論。

#### 実装可能性の評価

| 側面 | 評価 | 根拠 |
|:--|:--|:--|
| 理論的妥当性 | [推定 70%] | FEP に立脚。embedding 空間の MB 検出は概念的に自然 |
| 計算可能性 | [仮説 45%] | variational Bayesian EM は embedding 空間で重い。近似が必要 |
| Týpos への適用 | [推定 60%] | generate_typos() は既に暗黙的に MB 検出を行っている (classify_task) |
| PoC 実現 | [推定 55%] | 小規模データ (100 chunks) なら FAISS + variational EM で試行可能 |

### 未解決問題 (Hyphē §8 + 反証 §6 由来)

| # | 問題 | 状態 | Týpos への影響 |
|:--|:--|:--|:--|
| 3 | **場の PDE** | **[部分解決]** Possati PDE (§4.5) | CogSpace 上の勾配計算の実装 |
| 4 | **MB 自動検出** | **[部分解決]** Beck & Ramstead (§4.6) | variational Bayesian EM の計算コスト |
| 反証1 | LLM と Hyphē は比喩的類似 | 残存 | attention ≠ MB 検出 |
| 反証4 | 場に PDE がない | **[部分解決]** Possati + Beck & Ramstead で理論的枠組み確保 |

## 5. フラクタル自己参照

`.typos` の変更を `.typos` の 24 命題で記述可能:

| 座標 | `.typos` 変更の記述 |
|:--|:--|
| Value | 認識的 vs 実用的な変更 |
| Function | 探索的 vs 収束的な変更 |
| Precision | 精度上昇 vs 精度緩和 |
| Temporality | 過去反映 vs 未来対応 |
| Scale | 局所修正 vs 体系的修正 |
| Valence | 追加 vs 削除 |

メタレベル ≅ オブジェクトレベル = **Fix(G∘F)** — Týpos が正しい体系であることの形式的証拠。

## 参照

- `euporia_blindspots.md` (C1'.1): 盲点の再分類
- `rom_2026-03-13_typos_hyphe_crystallization.md`: 発見の ROM
- `typos_mcp_server.py` L392-693: `generate_typos()` 実装
- `typos_mcp_server.py` L148-217: `classify_task()` (Explore↔Exploit)
