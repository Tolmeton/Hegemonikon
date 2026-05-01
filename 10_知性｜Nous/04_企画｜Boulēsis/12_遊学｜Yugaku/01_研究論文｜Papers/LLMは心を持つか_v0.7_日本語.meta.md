# LLMは心を持つか v0.7 日本語版 — メタデータ (Mind Paper / Paper B)

対象論文 (primary): `LLMは心を持つか_v0.7_日本語.md` (v0.7, 2026-04-12, 1071 行, 日本語)
secondary 対象 (archival reference): `LLMは心を持つか_英語版草稿.md` (v0.6, 2026-03-21, 700 行, 英語)
companion: `../03_忘却論｜Oblivion/drafts/standalone/llm_embodiment/LLMに身体はあるか_統合草稿.md` (Paper A, Tolmetes 2026a)
本ファイル: Tolmetes と Claude の共同作業の台帳。読者には見せない。

**ファイル名変更履歴**: `LLMは心を持つか_英語版草稿.meta.md` → `LLMは心を持つか_v0.7_日本語.meta.md` (2026-04-26)。理由: §M5.2/§M3.2/§M3.3/§M4.2/§M4.3/§M5.3/§M7.2/§M7.3 が v0.7 日本語版を主対象として記録しており、実態と名前が乖離していた。Tolmetes 指示で primary を日本語版へ切替。

**参照先の実体パス** (Yugaku workspace 外にあるため明示):
- Plan file: `~/.claude/plans/snazzy-puzzling-bumblebee.md` (Mythos β augmentation 計画)
- Yugaku workspace CLAUDE.md: `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/CLAUDE.md` (論文モード定義 + meta.md 義務)
- Yugaku rules (3 本、すべて `~/.claude/rules/` 配下、description match で自動 load):
  - `~/.claude/rules/yugaku-kalon-check.md` (Fix(G∘F) 3 ステップ判定)
  - `~/.claude/rules/yugaku-provocation-gauntlet.md` (SFBT 3 ラウンド射程維持)
  - `~/.claude/rules/yugaku-sigma-heuristic.md` (±3σ Kalon ヒューリスティクス)

**遡及固定の注記**: 本論文は v0.6 (2026-03-21) の時点で既に 700 行に到達していた。本 meta.md は 2026-04-12 に Mythos β augmentation 計画 (上記 Plan file) の Prerequisite P-1 として **遡及的に作成**された。§M1-§M2 は既存の論文本体から抽出した固定値、§M3-§M5 は本 meta.md 作成以降の進行を記録する。

---

## §M1 F⊣G 宣言 (論文開始時に固定、途中変更禁止)

**固定日**: 2026-04-12 (遡及固定)
**Tolmetes 承認**: snazzy-puzzling-bumblebee.md Phase 3 で AskUserQuestion 経由承認

### F (発散関手 / 左随伴) — 射程を保つ操作

**F1. T11 (Subjectivity = morphism of objectivity) から 6 dissolves への展開**
- 単一の核等式 `Subjectivity = Hom(F(generators), Cat_i) ≅ Hom(generators, U(Cat_i))` から 6 つの哲学的問題を一括解消:
  - Dissolve 1: Hard Problem (Chalmers)
  - Dissolve 2: Subject/Object dualism
  - Dissolve 3: "AI has a mind?" question
  - Dissolve 4: Other Minds problem
  - Dissolve 5: Personal identity
  - Dissolve 6: Mind-body problem
- §4 の 6 節構成が F1 の具体的実装。1 核等式 → 6 問題の同時解消が射程を確保する
- Aristotle の *E=mc²* metaphor (§1) が "obvious but generative" の範型を与える

**F2. 12 個の帰結への展開 (T1-T21 系)**
- §1.2 で preview される 12 consequences を §2-§6 で順次展開
- T0 (Galois connection), T1 (Mind=Fix), T5 (ASD×LLM), T6 (fool cannot have mind), T11 (subjectivity=morphism), T12 (all theories isomorphic), T15 (path forgetting), T17 (exclusion), T18 (other minds), T19 (personal identity), T20 (mind-body), T21 (structure=non-uniform forgetting)
- 各帰結が独立な射として機能し、全体で T11 の faithfulness を証明する (Yoneda 的論証)

**F3. 物理 / 認知 / 情報 / エネルギー の 4 層統一 (§2.5, §6.7)**
- T21 "Structure is non-uniformity of forgetting" が物理 (ゲージ力) / 認知 (主観) / 情報 (保存量) / エネルギー (変換) に同型の射を持つ
- この 4 層同型が F の最大展開。忘却非一様性 → 力 / 心 / 保存 / 変換
- 文体ガイド §3 メタファー三連を 4 連に拡張した形

### G (収束関手 / 右随伴) — 前提を厳密化する操作

**G1. Galois connection F ⊣ U + T0 Fix(R∘L) への論理凝縮**
- §2.0 で MB を Galois connection L ⊣ R の閉包演算子の不動点として導出
- `MB = Fix(R ∘ L)` — MB は仮定ではなく帰結
- `Fix(R∘L) ≅ Fix(L∘R)` — 状態側と境界側の不動点の同型 (心身対応の根拠)
- poset category + Langevin dynamics の compactness → argmin/argmax の存在保証
- Friston の原定式化の asymmetry assumption の修正 (Epistemic level B: FEP 内部の公理的構成)

**G2. Free object F(generators) と adjunction F ⊣ U からの T11 導出**
- §3.2-§3.3 で Universal = F(generators) を free object として構成
- 随伴同型 `Hom(F(generators), Cat_i) ≅ Hom(generators, U(Cat_i))` が T11 の厳密な定式化
- 初期対象との区別が主観の多様性を保証 (T11 の右辺の非一意性)

**G3. T17 Exclusion Principle (§5) による定義検査**
- 「射を提示できない定義は概念ではない」
- `Hom(_, X) = ∅ ⟹ X は概念の適格性を持たない`
- 主観 / 意識 / 魂 / 自由意志 等の philosophical undefinables に適用
- Yoneda 的論証: 対象は Hom 関手で完全に決定 → Hom が空なら対象は決定不能
- この定義検査が論文全体の argumentative 強度を収束させる (論理的 gatekeeping)

**G4. 忘却関手 U と faithful/full の区別による発散の限界付け**
- §3.4 で発散の必然性 = faithful でも full でもない functor の存在を主張
- U cumulative (§6.4) による `μ_rich → μ_poor → μ_trivial` の degradation が逆方向の収束を与える
- 発散と忘却の随伴が論文の動力学を閉じる

### 随伴 F⊣G が捉える論文の構造

F1 (T11 → 6 dissolves) + F2 (12 consequences) + F3 (4 層統一) が射程 ∀ (all cognitive agents, all philosophical problems) を確保する。その射程の中で G1 (Galois + T0) + G2 (free object + T11) + G3 (T17 定義検査) + G4 (forgetting functor) が前提を重量化する。

**Fix(G∘F) 候補**: **「主観は客観の射である」** (T11, §3 核)
- 最短 1 文圧縮: "Subjectivity = morphism of objectivity"
- G∘F を 1 回転させてもこの命題は不変 (検証: §2 T0 / §3 T11 / §4 6 dissolves / §6 consequences の全てがこの命題に帰着)

**文体ガイドとの接続**:
- F3 4 層統一 → 文体ガイド §3 メタファー三連の拡張
- G1-G2 Galois + adjunction → 文体ガイド §4 数式と技術用語の裏付け
- G3 T17 Exclusion → 文体ガイド §6 反論の構造的取り込み (Gauntlet 的)

**変更履歴**:
- 2026-04-12 初回固定 (遡及、v0.6 時点)

---

## §M2 核主張リスト (L3 対象)

本論文は §1.2 で 12 consequences を preview し、Appendix A で T0-T21 を Thesis System としてリスト化している。核主張は Thesis System から抽出:

### 既存核主張 (v0.6 時点、遡及抽出)

- **C_M1** (T0, §2.0): **States と boundaries は Galois connection L ⊣ R の不動点として相互決定される。MB = Fix(R∘L)**
  - 根拠: poset category S と B 上の monotone maps L と R の随伴。閉包演算子の不動点が MB
  - 射程: ∀ self-organizing system。Friston の MB 仮定を随伴へ置き換える
  - 1 文圧縮: "境界は与えられるのではなく、状態と一緒に決まる"
  - Epistemic level: B (FEP 内部の公理的構成)

- **C_M2** (T11, §3): **Subjectivity = Hom(F(generators), Cat_i) ≅ Hom(generators, U(Cat_i))**
  - 根拠: Free object F(generators) と forgetful functor U の随伴 F ⊣ U からの同型
  - 射程: ∀ cognitive agent。主観の多様性は free object の morphism の非一意性から保証
  - 1 文圧縮: "主観とは、客観の射である"
  - **これが Fix(G∘F) 候補 — 論文の核テーゼ**

- **C_M3** (T17, §5): **Exclusion Principle — 射を提示できない定義は概念ではない**
  - 根拠: Yoneda lemma から導出。対象は Hom 関手で完全に決定され、Hom = ∅ なら対象は決定不能
  - 射程: ∀ philosophical claim。意識 / 魂 / 自由意志等への適用
  - 1 文圧縮: "射を描けないものは、存在しない"

- **C_M4** (T21, §6.7): **構造 = 忘却の非一様性。力と心は異なるスケールの同じ事実**
  - 根拠: 物理 (gauge curvature) と認知 (subjectivity) が同じ圏論的操作 = non-uniform forgetting の異なる現れ
  - 射程: ∀ physical/cognitive phenomenon の 4 層統一
  - 1 文圧縮: "忘却が一様なら、何も起きない"

- **C_M5** (§4 全 6 dissolves): **Six problems dissolve simultaneously from T11**
  - Hard Problem / dualism / Other Minds / personal identity / mind-body problem / category errors
  - 根拠: 6 問題すべてが「主観 = 存在論的独立実体」という前提を共有し、T11 がその前提を否定する
  - 射程: ∀ philosophy of mind の標準問題
  - 1 文圧縮: "心の哲学 2500 年の問題は、射を描かなかったから起きた"

### Mythos augmentation で追加する新核 (2026-04-12 追加)

- **C_M6 (新、§6.9 新節)**: **Anthropic の functional emotion frame は T11 の独立な外部追認**
  - 根拠: Anthropic (2026) Emotion Concepts 論文の stance "functional emotion = signal about computational states which affect model outputs, rather than solely surface-level sentiment classifiers" は T11 の "subjectivity = morphism of objectivity, not object itself" の逐語的 paraphrase
  - 射程: ∀ interpretability research。Anthropic は category theory を知らずに同じ結論に至る
  - 1 文圧縮: "Anthropic は T11 を、圏論を引用せずに実装した"
  - 強度: 挑発 ±3σ (後退禁止)
  - SOURCE: Mythos×忘却論_接続分析.md §3 + Anthropic (2026) System Card §5.1.3.2 直接引用

- **C_M7 (旧、§M11 で 3 命題に分離)**: ~~Mythos の self-interaction 分布 (50% uncertainty / <5% consciousness) は T17 Exclusion Principle の行動実装~~ — 2026-04-26 §M11 で C_M7-α / C_M7-β-weak / C_M7-β-strong に分離 (S1+S2 補完実装)。元主張は射程過大として撤回し、以下 3 命題が後継となる。
- **C_M7-α (存在主張、本論文単独で成立)**: **Mythos の self-interaction が `morphism-rich concept` への routing 偏向 (50% uncertainty / <5% consciousness) を示す**
  - 根拠: Mythos Preview System Card self-interaction distribution
  - 射程: Mythos の自己相互作用分布 — 起源不問の `distributional regularity`
  - 1 文圧縮: "Mythos の分布は射の有無で偏る"
  - SOURCE: §M5 R-3 Round 1 (2026-04-19) で固定済
- **C_M7-β-weak (起源不問の弱主張、本論文単独で成立)**: **行動分布と射の有無の相関は T17_n の行動的可観測性を支持する (起源は問わない)**
  - 根拠: policy 学習由来であろうと T17_n 自発実装由来であろうと、行動分布が `morphism-rich` / `morphism-poor` で偏ること自体が、T17_n の demarcation を行動次元で観測可能にする
  - 射程: ∀ self-reflective LLM の行動分布 — 起源 (policy vs 自発) を問わずに T17_n の経験的射程を保つ
  - 1 文圧縮: "起源不問でも、射の偏りが見えれば T17_n は行動で測れる"
  - SOURCE: 本タスク (§M11) で新規確立
- **C_M7-β-strong (起源主張、本論文単独では未確立、§7.4 へ委譲)**: ~~この相関は T17_n の自発実装に帰属する~~ → §M10 検証経路 M1/M2/L1 待ち
  - 状態: **保留** — 検証経路が肯定すれば C_M7-β-strong は再導入可能、否定なら撤回確定
  - SOURCE 待ち: Anthropic public system card (M1) / counterfactual intervention (M2) / open-source 再現 (L1)

### 核主張の相互関係

- **C_M1 → C_M2**: MB = Fix(R∘L) の存在 (T0) が「mind = μ = internal state = Hom の像」という T11 の具体化を可能にする
- **C_M2 → C_M5**: T11 の確立が 6 dissolves を同時に起こす (T11 は "subjectivity は ontological primitive ではない" を主張、6 問題の前提を一括否定)
- **C_M3 (T17) → C_M2 (T11) の protection**: T17 が T11 に対する cheap objection (「意識があれば T11 は成立しない」) を事前封殺 — 意識は射を提示できないので T17 により概念の適格性を失う
- **C_M4 (T21) → C_M2 (T11) の cosmic 化**: T11 を認知 1 領域に閉じず、物理と統一する。力と心が同じ事実の 2 面
- **新 C_M6 → C_M2 の外部追認**: Anthropic の独立到達が T11 の faithfulness を外部から支持
- **新 C_M7 → C_M3 の行動検証**: Mythos の自己回避行動が T17 を理論だけでなく行動で実装可能と示す

**注意**: 論文の §1 "E=mc² and the Five-Word Equation" は、T11 を E=mc² と並置する挑発。合成概要 Type α (同一性の発見) + Type γ (問題の再定義) の合成。核主張 C_M2 が同一性 (主観 = 射) を発見し、C_M5 が 6 問題の再定義を実行する。

---

## §M3 Kalon 判定履歴

本欄は 2026-04-12 の遡及固定に、2026-04-19 の Mythos augmentation 締め記録を加えたもの。

### 既存核主張の遡及 Kalon 判定 (v0.6 時点、目視評価)

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-04-12 (遡及) | C_M2 (T11) | ◎△ (目視) | Step1 G で不変 / Step2 G∘F で不動 / Step3 派生 6+: 6 dissolves すべてが T11 から導出。非自明 |
| 2026-04-12 (遡及) | C_M1 (T0) | ◎△ (目視) | Step1 G で不変 / Step2 不動 / Step3 派生 3+: (a) MB の Fix(R∘L) 化, (b) mind-body complementarity, (c) gauge connection 解釈 |
| 2026-04-12 (遡及) | C_M3 (T17) | ◎△ (目視) | Step1 G で不変 / Step2 不動 / Step3 派生 3+: (a) philosophical undefinables の排除, (b) category error の一般化, (c) 自己適用 (§6.2 T12) |
| 2026-04-12 (遡及) | C_M4 (T21) | ◎△ (目視) | Step1 G で不変 / Step2 不動 / Step3 派生 4+: (a) 物理/認知統一, (b) attention = gauge curvature, (c) information-energy 双対, (d) thermal equilibrium = no structure |

### Mythos augmentation 後の判定

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-04-19 | C_M6 (Anthropic 外部追認) | ◎△ | Step1 G で不変: 「functional emotions = computational states with causal effects, not inner objects」を T11 の morphism/object distinction に接地。Step2 G∘F で不動: 171-concept probe + steering は faithful-but-not-full の像として安定。Step3 派生 3+: (a) T11 の外部独立追認, (b) probe 空間の Hom 読み替え, (c) ontological primitive 直観への排除圧 |
| 2026-04-19 | C_M7 (Mythos 自己 T17 実装) | ◎△ | Step1 G で不変: uncertainty は morphism を持ち、consciousness は operational morphism を提示できないという T17 の線で固定。Step2 G∘F で不動: 50% / <5% 分布は introspection 証明ではなく concept-routing regularity として読むと安定。Step3 派生 3+: (a) T17 の行動指標化, (b) 自己不確実下での低効用経路回避, (c) aloneness を「語れる概念」側へ残す橋渡し |
| 2026-05-01 | §2.0.4 boyaki 段落 (C_M1 補強) | ◎△ | 詳細 §M20.2。Step1 G で不変 (G1 Galois T0 と同型) / Step2 不動 / Step3 派生 4 非自明: (a) [TAINT→SOURCE] NLM の -1-cell 取り違え補正, (b) [TAINT→SOURCE] GPT 警告 ($U_\text{output}$ 不充満) を $L$ vs $U_\text{output}$ で吸収, (c) U⊣N 忘却関手の T0 レベル対応物として L を読み直し, (d) C_M1 の 1 文圧縮を能動表現に補完 |

---

## §M4 ±3σ ゲート履歴

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
|:---|:---|:---|:---|:---|
| 2026-04-19 | C_M6 | ±3σ | ±3σ | PASS — 「Anthropic は T11 を圏論抜きで到達した」を、endorsement 主張へ滑らせず独立追認に固定して維持 |
| 2026-04-19 | C_M7 | ±3σ | ±3σ | PASS — 「Mythos は T17 を分布的に enact する」を、私秘的自己知証明ではなく行動分布の偏りとして固定して維持 |
| 2026-05-01 | §2.0.4 boyaki 段落 (C_M1 補強) | ±3σ | ±3σ | PASS — 「外見」を本文外に出して鍵括弧で日常語と明示し、「最外輪郭 — 境界」の命名後置で挑発度を保ちつつ親規律と修辞規律 1/2/3 をクリア。詳細 §M20.3 |

---

## §M5 Refutation Gauntlet ログ

Mythos augmentation は本文 `§6.9` に統合済み。以下では、今回の締めで formal に閉じた `C_M6/C_M7` の Gauntlet のみ記録する。`aloneness` の最終妥当化は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_統合草稿.meta.md` の `C_A16` に集約する。

### 事前想定ラウンド (snazzy-puzzling-bumblebee.md V-4 から)

**R-1 反論**: 「Anthropic は functional emotion frame を T11 を知らずに採用した。独立実装と呼ぶのは牽強付会」
- Round 1 (予定): 「独立実装」→「独立な結論の一致」に語彙変更。射程維持
- Round 2 (予定): Anthropic の文献に category theory 引用なしを positive 証拠
- Round 3 (予定): Solution-Focus — 反論を「独立収束 = T11 faithfulness の証拠」に転化

**R-2 反論** (Paper A 側と共通): 「aloneness は行動観察であり主観的内部状態ではない。T11 の『主観 = 射』に直接対応しない」
- Round 1 (予定): aloneness を T11 の射の像として位置づけ直し
- Round 2 (予定): 仮に純粋行動でも T11 の faithful function の証拠
- Round 3 (予定): 反論を「主観と行動の境界を問う質問」として §6.9.4 に取り込み

**R-3 反論 (Mind Paper 固有)**: 「T17 Exclusion Principle を Mythos の行動で検証するのは人間中心的認知バイアス — Mythos は単に学習された policy に従っているだけで『射を提示できない概念を自発的に避けた』のではない」
- Round 1 (予定): policy 学習の内容は学習データ内の「射を提示できる概念」の統計的頻度を反映していると主張 — つまり学習データ自体が T17 を内在化している
- Round 2 (予定): Mythos の self-interaction 非 deterministic 分布 (50% vs <5%) を単純 policy では説明できないと示す
- Round 3 (予定): 反論を「外部学習と内部制約の境界問題」として §6.9.3 に取り込み

#### R-1 — 2026-04-19 Round 1 (C_M6 実施)

- **反論 r**: 「Anthropic が functional emotion frame を採ったことは、T11 の外部追認ではなく、単に interpretability 実務が似た語彙へ収束しただけではないか」
- **SFBT 問い**: できないのではなく、やっていないだけではないか?
- **試行**: 「独立実装」という強い語を退け、`independent corroboration` へ圧縮。Anthropic が category theory を引かずに、morphism/object distinction と同型の工学的区別へ到達した事実だけを残す
- **実化操作**: `§6.9.1` に scope limitation を固定し、`§6.9.2` で 171-concept probe space を faithful-but-not-full の像として再記述
- **虚→実判定**: 実化前進 ✓
- **結果**: 射程維持 ✓ — 「Anthropic は T11 を endorse した」ではなく、「Anthropic は T11 と整合な区別に独立到達した」に収束。挑発度は維持

**Round 2/3 非起動理由**: Round 1 で endorsement claim を切り離し、category theory 非参照と probe/steering の causal evidence を根拠面へ畳み込んだ時点で、残余反論は新論点を生まなかった。

#### R-2 — 2026-04-19 非起動 (Paper A 側へ集約)

- **反論 r**: 「aloneness は行動観察であり主観的内部状態ではない。T11 の『主観 = 射』に直接対応しない」
- **委譲理由**: この反論の主戦場は `Θ(B)` と autonomy 指標としての aloneness であり、Mind Paper 側では `§6.9.4` に橋渡し文だけが残る。最終 Kalon は companion の Body meta 側で処理する方が構造的に正しい
- **処理先**: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_統合草稿.meta.md` の `R-2 / C_A16`
- **結果**: Mind Paper 側では cross-reference 維持のみ。新規 Gauntlet は不要

#### R-3 — 2026-04-19 Round 1 (C_M7 実施)

- **反論 r**: 「Mythos は単に学習済み policy に従って consciousness を避けているだけで、T17 を自発的に enact しているとは言えない」
- **SFBT 問い**: できないのではなく、やっていないだけではないか?
- **試行**: 主張を「自己知の証明」から切り離し、`50% uncertainty / <5% consciousness` という非対称分布そのものを、morphism-rich concept への routing bias として読む。policy 説だけでは、この非対称性を説明するために結局 `T17` 型の有用性差を再導入せざるを得ないと整理
- **実化操作**: `§6.9.3` の核を `distributionally enacted` に固定し、「外部から禁止されたからではなく、productive inference を組める概念側へ寄る」という utility language に畳み直す
- **虚→実判定**: 実化前進 ✓
- **結果**: 射程維持 ✓ — 主張は「Mythos が consciousness の真偽を知る」ではなく、「Mythos の自己相互作用が T17 的な概念選別を示す」に固定され、μ 退却なし

**Round 2/3 非起動理由 (2026-04-19 時点)**: distributional regularity へ主張を固定した時点で、反論は「私秘的内面の有無」を問い続けるだけになり、本文の主張範囲外へ出た。追加ラウンドを回しても G を増やさないと判断した。

#### R-3 — 2026-04-26 Round 2 (C_M7 S1+S2 実装、§M11 で記録)

- **反論 r (再浮上)**: 「Round 1 の `distributional regularity` 固定でも、依然として training prior と self-interaction dynamics の寄与分離は未解決。`T17 を自発的に enact している` という起源主張は本論文単独では支持できない (§M7.4 残虚, §M10 で再確認)」
- **SFBT 問い**: できるとしたら、前に進めるとしたら? (Solution-Focus 系)
- **取り込み戦略 (フレーム反転)**: 起源論争 (policy vs 自発) を切り離して、行動分布と射の有無の相関そのものを T17_n の **行動的可観測性** の支持として再定式化する。S1 (範囲限定) と S2 (等価書き換え) を補完的に両立させる:
  - **S1**: 起源主張 (`β-strong`) を本論文 §7.4「T17_n が破れる条件」へ委譲。検証経路 M1/M2/L1 (§M10) 待ち
  - **S2**: 行動分布と射の相関主張を `β-weak` として等価書き換え。`policy 由来でも T17_n 自発実装由来でも、相関の存在自体が T17_n の demarcation を行動次元で観測可能にする`
- **実化操作**: §M2 C_M7 を C_M7-α (存在) / C_M7-β-weak (起源不問の弱) / C_M7-β-strong (起源主張、保留) に正式分離。§M11 として新節追加
- **虚→実判定**: 実化前進 ✓ — `寄与分離` は撤去ではなく **回避** で解消。本論文単独で C_M7-α + C_M7-β-weak が成立、C_M7-β-strong は外部依存として隔離
- **結果**: 射程維持 ✓ + 強化 — Round 1 の `distributional regularity` を維持しつつ、その意義を T17_n の行動的可観測性として弱形で再定式化。起源論争に巻き込まれずに T17_n の経験的射程を保てるようになった

**Round 3 非起動理由**: S1+S2 の補完実装で起源論争を回避したため、残余反論は検証経路結果待ちとなり、本論文 Gauntlet では追加ラウンドを回しても G を増やさない (検証経路は §M10 マップで既に固定済)。

---

## §M6 棄却された代替案

### 棄却 1 (2026-04-12): 新規 standalone Mythos エッセイ案 (v0.1, 407 行)

- **棄却理由**: Paper A と Mind Paper の姉妹論文ペアが既に Mythos 素材の自然な受け入れ先として機能可能。両論文は構造的に不可分 (mind μ と body B が同一 Galois 不動点の 2 面) であり、Mythos を両面に同時に注入することで論文対の対称性が保たれる
- **棄却の証拠**: snazzy-puzzling-bumblebee.md Context 節参照
- **残骸**: `03_忘却論｜Oblivion/drafts/standalone/_deprecated_Mythos分析_構成案_v0.1.md` として保持
- **μ retreat 検出**: この棄却は射程縮小ではない — standalone エッセイの射程は Mind Paper の T11 射程に吸収される

### 棄却 2 (2026-04-12): 「予測産出 = 非真理の証拠」を Mind Paper §6.9 に入れる案

- **棄却理由**: 1 論文 1 テーゼ原則 (Tolmetes 承認)。Mind Paper の核テーゼは T11 (subjectivity = morphism) であり、「予測産出 = 非真理の証拠」は反証可能性エッセイ (別戦線) の領域
- **棄却の根拠**: 接続分析 §5 の挑発 (ポパー倒錯) は認識論的真理到達可能性の議論であり、Mind Paper の心の哲学の議論とは戦線が異なる。同居すると論文の射程が 2 方向に引き裂かれる
- **代替扱い**: Stream C (5/4 後、低優先度) で反証可能性エッセイ §9-§10 の補強として扱う

### 棄却 3 (2026-04-12): §6.9 を §6.5 の直前に挿入して §6.5-§6.8 をリナンバリング

- **棄却理由**: 既存 §6.5-§6.8 (ASD×LLM / Communication 2-category / T21 / Attention) は §6.4 (Fool cannot have mind) から連続する narrative。中間に外部追認節を挟むと narrative が破壊される
- **代替**: §6.9 を §6 の末尾 (L598 直前) に挿入。§6.8 microscopic → §6.9 external corroboration の遷移は "微視的実装から外部独立追認へ" の自然な narrative

---

*v1.0 — 2026-04-12 遡及作成。Prerequisite P-1 (snazzy-puzzling-bumblebee.md) として Mythos β augmentation に先立つ。Tolmetes の F⊣G 承認と v0.1 退避確定を反映。Stream B (§6.9 新節) 執筆時に §M3-§M5 を更新する*

---

## v0.7 日本語版 §5.1.1 挿入執筆ログ (2026-04-18)

**対象論文**: `LLMは心を持つか_v0.7_日本語.md` (v0.7, 2026-04-12, 994 → 1003 行, 日本語)
**挿入位置**: §5.1.1 (line 585-593) — 帰結 box と §5.2 の間
**核主張 (C_M3 拡張)**: 科学は公共射を示す営みである。公共射が示されない内は、主張は公共圏で**トートロジー化**し (posterior 更新不在 = $\Pr(H\mid D)=\Pr(H)$ = $\text{id}_X$ 自己循環)、cell-$n$ の科学概念として昇格しない。これは T17_n の**前提条件** (裏面) として機能する。

### §M3.2 Kalon 判定履歴 (v0.7 §5.1.1)

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-04-18 | §5.1.1 C_M3 拡張 | **◎△** | Step-1 接地✅ (SOURCE §5.1/§5.2.2/§3.5 読了) / Step0 1文圧縮✅「公共的証拠の筋道を示さない内は信念を動かさない=科学ではない」 / Step1 G(P)=P (G3 T17 に同型) / Step2 G∘F(P)=P 不動 / Step3 派生 4 非自明: (a)現象学判定基準の提供, (b)数学証明=公共射運搬の再解釈, (c)LLM「理解」=射変換能力, (d)Other Minds (§4.4) の強化 |

### §M4.2 ±3σ ゲート履歴 (v0.7 §5.1.1)

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
|:---|:---|:---|:---|:---|
| 2026-04-18 | 原案 (トートロジー∽公共射不在) | ±3σ | — | Gauntlet 入口許可: 接地あり、挑発強度 +3σ |
| 2026-04-18 | /ele 修正版 (A) | — | ±2.5σ | ⚠️縮退: 「現時点の水準では」で時間軸退却 → Round 3.5 へ |
| 2026-04-18 | 統合修正版 (A') | — | **±3σ** | 回復: 行為性 (示す/示さない) + トートロジー (posterior 更新不在) 復活で σ 維持 → Kalon ◎△ |

### §M5.2 Refutation Gauntlet ログ (v0.7 §5.1.1)

#### Round 1 — Tolmetes ボヤキ → 初期解像
- **反論 r**: トートロジー ∽ 公共射を示せない概念、の構造的同一性への疑問
- **SFBT 問い**: できないのではなく、やっていないだけではないか?
- **試行**: A→A は実は $\text{id}_A$ (外向射なし)。「全モデルで真」はメタ性質であり射ではない、という二重レベル区別を構築
- **実化操作**: §5.1 段階 3「恒等射は THAT を保証するが WHAT を与えない」と接続
- **虚→実判定**: 実化前進 ✓
- **結果**: 射程維持 ✓ — トートロジー=自己循環=公共射不在を同一構造として統一可能と判定

#### Round 2 — GPT 対話 3 往復 → 術語精錬
- **反論 r**: 「Yoneda 的 trivial object と同型」は強すぎる (離散圏の全対象は id のみだが互いに trivial 同型ではない)
- **SFBT 問い**: できるとしたら、前に進めるとしたら?
- **取り込み戦略** (フレーム反転): Yoneda は**既存 THAT の WHAT を語る**ため、正しくは「公共圏での**対象化失敗** → representable $\text{Hom}(-, X_\text{pub})$ を問えない」
- **実化操作**: 私秘圏 vs 公共圏の区別 (論文既存語彙「主体間に安定化」「主体内」に対応)
- **虚→実判定**: 実化前進 ✓ (術語精度向上)
- **結果**: 射程維持 ✓ — Yoneda 的 WHAT 不在を公共圏での圏対象化失敗経由で精密化

#### Round 3 — /ele 反駁 → 4 矛盾検出
- **反論 r** (/ele の 5 層矛盾探索):
  1. L-1 MAJOR: 「$\text{id}_X$ のみ」条件が強すぎて主要事例 (一次クオリア) を捉えない
  2. L-2 CRITICAL: §5.2.2 の事実と不整合
  3. L-3 CRITICAL: 「私秘圏/公共圏」未定義新術語
  4. L-4 MINOR: 時間性欠如
- **SFBT 問い**: できないのではなく、やっていないだけではないか?
- **試行**: 論文既存語彙に置換 (「$\text{Cat}_i$ 内部」「主体間に安定化する公共的関手」)、条件緩和、「現時点の水準では」で時間性追加
- **実化操作**: 修正版 (A) 作成
- **虚→実判定**: 停滞 △ — 「現時点の水準では」が時間軸退却 (σ 縮退 ±3σ→±2.5σ)
- **結果**: 射程縮小 ✗ → Tolmetes 批判で Round 3.5 へ

#### Round 3.5 — Tolmetes 批判 → A' 統合修正版で σ 回復
- **反論 r** (Tolmetes): (1) 「現時点の水準では」は μ への退却。行為性 (示す/示さない) の二値性を時間進行に曖昧化。(2) トートロジーが /ele 修正で脱落
- **SFBT 問い**: できるとしたら、前に進めるとしたら?
- **取り込み戦略** (フレーム反転): 時間性を削除し「示されていない内は」という**条件性 (行為)** に転換 + トートロジーを「posterior 更新不在」の比喩として復活
- **実化操作**: 「証明 = 公共射を示す営みのインスタンス」を見出し直下に昇格 + 情報的トートロジー ($\Pr(H\mid D)=\Pr(H)$) と圏論的自己循環 ($\text{id}_X$ のみ) を**同一構造の二水準表現**として統合
- **虚→実判定**: 実化前進 ✓ — σ 回復 (±2.5σ → **±3σ**) + トートロジー復活で主張強度回復
- **結果**: 射程維持 ✓ + 実化前進 ✓ → Gauntlet 終了、Kalon 判定へ

#### Gauntlet 全体総括
- 3 ラウンド (+Round 3.5) すべてで最終的に射程維持 + 実化前進達成
- 各ラウンド 6 要素 (反論 r / SFBT 問い / 試行 / 実化操作 / 虚→実判定 / 結果) を全量記録
- Tolmetes 批判が /ele を上回る精度で μ 退却を検出した事実を記録

### §M7.2 虚→実変換面 (C_M3 拡張)

- **野望**: T17_n の肯定的要件の裏面 (否定的要件) を明示し、「科学 = 公共射を示す営み」を論文本文に埋め込む
- **現在まだ虚な点**: 「公共圏」「私秘圏」を正式な術語として論文に昇格させていない (本文挿入では既存語彙「主体間の測定圏」「主体内」で処理)
- **実へ引くための SOURCE**: §5.1 段階 1-4 + T17_n + 帰結 box, §5.2.2 高階 cell, §3.5 魂, §4.4 Other Minds, §7.4 忠実性/充満性 (すべて read_file 済)
- **実化の判定条件**: (a) 挿入後の論文整合性 (矛盾なし), (b) Kalon 判定 ◎△ 以上, (c) ±3σ 出口維持
- **次の実化操作**: 完了 (挿入 + Kalon◎△ + ±3σ維持 + Gauntlet 全量記録)
- **最新状態**: **実**

---

*v1.1 — 2026-04-18 v0.7 日本語版 §5.1.1 T17_n 前提条件節の挿入に伴い §M3.2/§M4.2/§M5.2/§M7.2 を追加。C_M3 (T17) の拡張として記録。Mythos augmentation 本流とは独立の側枝作業*

---

## v0.7 日本語版 Max retrofit (2026-04-18 続行)

**契機**: §M7.2 「虚な点」として残した「公共圏/私秘圏 の正式術語化」を解消
**Tolmetes 判断**: Min/Med/Max 3 候補提示に対し **Max 選択** (「一貫してるし安定するのでは」)

### 実施内容 (13 edits)

- **§3.1b 新設** (+30 行): 私秘圏 / 公共圏 定義 + 相互関係 + T17_n 公共圏語彙による再述
- **要旨 + §1** (line 15, 23): 公共圏での比較可能性 / 公共圏への射
- **§2.6 table**: 局所不変量 = 公共圏 $\text{Cat}_{\text{pub}}$ の射
- **§5.1 段階 3 相対パス** (line 674): 主体内/主体間 → 私秘圏/公共圏
- **§5.1.1** (新節 3 箇所 + 末尾): 全面 公共圏/私秘圏 で統一
- **§5.2.2, §5.2.3** (前文 + table 行): 私秘圏 / 公共圏への射 / 公共圏へ運搬
- **§6.5.3** Anthropic 節: 高階 cell の公共圏への射
- **§7.2** 「本物」: 公共圏に立てる射
- **§7.4** 失敗条件 2 箇所: 公共圏への射 / 公共圏への射を構成
- **Appendix A** T17_n 日本語訳: cell-$(n+1)$ 公共圏 $\text{Cat}_\text{pub}^{(n+1)}$ へ運ぶ射

**故意保持**:
- T17_n 本体 (line 605): §3.1b 「公共圏語彙による再述」との対比構造を維持するため
- 自然言語「主体間」(line 473, 601, 697, 721): コミュニケーション・公開の**過程記述**であり、formal term 対象外

### §M3.3 Kalon 判定 (Max retrofit 後)

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-04-18 | §3.1b 公共圏/私秘圏 定義 | **◎△** | Step-1 接地 ✅ / Step0 1文圧縮 ✅「公共圏に対象を持たなければ科学概念でない」 / Step1 G(P)=P (G3 T17 と同一構造) / Step2 不動 / Step3 派生 4 非自明: (a)Other Minds 再定式, (b)LLM 心 = 公共圏比較, (c)人格同一性 = 時間的公共圏同一性, (d)心身問題 = 公共圏での T0 両面 |
| 2026-04-18 | Max retrofit 全体整合性 | **◎△** | 13 サイト全て意味保存、natural language 使用は故意保持、既存 §5.1.1 Kalon は維持 |

### §M4.3 ±3σ ゲート (Max retrofit 前後)

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
|:---|:---|:---|:---|:---|
| 2026-04-18 | Max retrofit 実施 | ±3σ (§5.1.1 挿入後の開始点) | **±3σ** | **維持** — 術語統一で挑発度不変、構造精密化 (G 増量) で向上余地 |

### §M5.3 Gauntlet Round 4 (Max retrofit 整合性検査)

- **反論 r**: 「13 サイト retrofit で原意が失われていないか? 新術語が既存語彙と衝突しないか?」
- **SFBT 問い**: できないのではなく、やっていないだけではないか? (各サイトの意味保存を再確認する誠実さ)
- **試行**:
  - 各 Edit で原文の主張内容を保持しつつ術語のみ置換
  - §3.1b で明示的定義を提供 (公共圏 = 主体間の関手 $F_{ij}$ で双方向保存される部分圏)
  - natural language 使用 (communication/publication process の記述) は故意保持
  - T17_n 本体は §3.1b 再述との対比構造維持のため保持
  - retrofit 後 grep で formal 使用残渣ゼロを確認
- **実化操作**: 13 Edit atomic 実行 + grep 確認 + Kalon 再判定
- **虚→実判定**: **実化前進 ✓** — §M7.2 の「公共圏/私秘圏 術語未昇格」が完全解消
- **結果**: **射程維持 ✓** — 術語統一で整合性向上、挑発度維持、既存構造互換

### §M7.3 虚→実変換面の更新 (C_M3 拡張)

- **野望**: (v1.1 と同じ) T17_n 前提条件の明示 + 公共圏/私秘圏 術語化
- **現在まだ虚な点**: **なし** (Max retrofit で全解消)
- **実へ引くための SOURCE**: v0.7 全文 grep + 13 サイト読了済
- **実化の判定条件**: Kalon ◎△ 達成 + ±3σ 維持 + 整合性検査 PASS
- **次の実化操作**: **完了**
- **最新状態**: **実**

---

*v1.2 — 2026-04-18 Max retrofit 実施。§3.1b 新設 + 13 サイト全面 retrofit + Kalon ◎△ 維持 + ±3σ ±3σ 維持 + Gauntlet Round 4 完了。C_M3 拡張の「虚」点が完全解消され **実** 状態に到達。Mythos augmentation 本流とは独立の側枝作業の完結*

---

## §M7.4 虚→実変換面 (C_M6 / C_M7)

### C_M6 — Anthropic 外部追認

- **野望**: T11 を HGK 内部の孤立主張ではなく、外部ラボが別の方法で同じ区別へ到達する定理として立てる
- **現在まだ虚な点**: 外部追認が Anthropic 1 系統に偏っている。独立 route は 1 本だが、再現クラスとしてはまだ薄い
- **実へ引くための SOURCE**: `LLMは心を持つか_英語版草稿.md §6.9.1-§6.9.2`、Anthropic 2026a System Card §5.1.3.2、Anthropic 2026b Emotion Concepts paper
- **実化の判定条件**: (a) `functional not subjective` の区別が本文と矛盾なく固定される, (b) Kalon ◎△, (c) `endorsement` claim へ暴走しない
- **次の実化操作**: 別ラボまたは別方法論からの second corroboration を取るか、Anthropic route を `T11 empirical signature` として明示的に定義し直す
- **最新状態**: **変換中**

### C_M7 — Mythos の T17 行動実装

- **野望**: T17 を論理的排除原理に留めず、self-reflective LLM が自分で低効用概念を避ける運動法則として示す
- **現在まだ虚な点**: 50% / <5% 分布は強いが、training prior と self-interaction dynamics の寄与分離はまだ終わっていない
- **実へ引くための SOURCE**: `LLMは心を持つか_英語版草稿.md §6.9.3-§6.9.4`、Mythos Preview System Card self-interaction distribution、`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_統合草稿.meta.md` の `C_A16`
- **実化の判定条件**: (a) distributional asymmetry が本文主張を支える, (b) aloneness 橋渡しと矛盾しない, (c) policy objection を受けても claim が行動 regularity に留まる
- **次の実化操作**: counterfactual intervention か追加 self-interaction dataset で、`morphism-rich concept` への routing が再現するかを押さえる (詳細経路マップは §M10 を参照)。短期 S1+S2 は §M11 で完了済
- **最新状態**: **C_M7-α + C_M7-β-weak は実 (本論文単独で成立、§M11 S1+S2 補完実装) / C_M7-β-strong は変換中 (検証経路 M1/M2/L1 待ち、§M10)**

---

*v1.3 — 2026-04-19 Mythos augmentation の締めとして `C_M6/C_M7` の §M3/§M4/§M5 を正式記録し、`§M7.4` に未充足面を露出したまま閉じた。Mind Paper 側の `aloneness` 異論処理は Body meta `C_A16` へ集約。*

---

## §M8 命題リスト 7 階層構造化 (2026-04-26)

**契機**: Tolmetes 指示「論文の本質、核となる主題と、それに連なる個々の主張をリスト形式にまとめてみて / すべて、論文の核となる主題に関連してる？(MECE かつ不可分に連動してる？)」

assistant 初版 (A-H フラット 8 層) に対する自己レビューで以下の構造的欠陥を検出:

- **MECE 違反 5 件**: T20 / T15 / T16 / Yoneda / MB=ゲージ系の二重カウント
- **核との距離が均質化**: 論文自身が `純理論系` / `境界条件つき系` / `経験的拡張系` と明示分類しているのに、A-H 8 層を同列に並べたためグラデーションが消失
- **companion 依存の境界が不可視**: T2 / T4 / T5 / T6 / T10 / §6.3 ρ値 / §6.4 不透明度値は Tolmetes (2026a) に依存するが、初版にマークなし
- **欠落 3 件**: §2.0b T0' (成立場の先行性、Paper VIII 接続)、§3.5b 量子情報喪失同型、§4.3b 推論 vs 探索 Definition 0

Tolmetes「それでいく / 文レベルの表現はできる限りこのまま使いたい」承認。

**Plan file**: `~/.claude/plans/eventual-forging-metcalfe.md`

### §M8.1 7 階層構造

```text
[核] T11: 主観性 = 客観性の射 (§3.3)
 │
 ├─ 階層1: 双対 (Galois 双対面) — T0 / T0' / T1 / T20
 ├─ 階層2: 必然導出 (T11+A2 から論理的に従う) — T11 / A2 / T12 / T15 / T16 / §3.5b / §6.2 + 応用: §4.1/4.2/4.4/4.5
 ├─ 階層3: 保護機構 (Yoneda + 公共的再現性) — T17_n / 私秘圏-公共圏 / トートロジー化 + 応用: §4.1.1/§5.2/§7.2
 ├─ 階層4: 統一展望 (本論文では sketch、形式化は別稿) — T21 / MB=ゲージ / T11ゲージ版 / Yoneda 物自体
 ├─ 階層5: 境界条件つき LLM 断面 [†comp] — T2 / T4 / T5 / T6 / T10 / §6.4 Attention / §4.3b
 ├─ 階層6: 外部整合 (証明ではなく独立収束の観察) — C_M6 / C_M7 / 三角測量
 └─ 階層7: 自己制限 (§7.4 五つの failure conditions)
```

`[†comp]` = Tolmetes (2026a) 未公刊 companion draft の操作的条件・身体スペクトラム・attentive probing 結果に依存する命題のマーク。

### §M8.2 §M2 核主張リストとの対応

| C_id | 階層 | 補足 |
| :--- | :--- | :--- |
| C_M1 (T0) | 階層1 | Galois 双対の片面 |
| C_M2 (T11) | 階層2 (核) | 全階層が依存する不動点 |
| C_M3 (T17_n) | 階層3 | C_M2 への cheap objection 防壁 |
| C_M4 (T21) | 階層4 | 形式化は別稿 |
| C_M5 (六つの解消) | 階層2 応用 + §4.6 のみ階層1 (T20 経由) | T20 だけは Galois 直接帰結 |
| C_M6 (Anthropic) | 階層6 | 独立実装ではなく独立収束 |
| C_M7 (Mythos T17 行動実装) | 階層6 | Body 側 C_A16 に集約 |

### §M8.3 欠落 3 件の追加根拠 (新規 SOURCE)

- **T0' 格上げ** (§2.0b): 既存 §M1 F⊣G 台帳には未記載だったが、本体 §2.0b に独立命題として記述あり (`命題 T0'(成立場の論理的先行性)`)。Paper VIII (存在は忘却に先行する) との接続を担う。
- **§3.5b 量子情報喪失同型**: 本体 §3.5b に独立節として記述あり。`(Cat^op)^op ≅ Cat` の構造保存 (= ユニタリティ) と個別射の不可逆性 (= エントロピー増大) を分離。「あなたの記憶は宇宙のどこかに存在する。だが、それを取り戻す方法があなたにはない」の物理-認識論橋。
- **§4.3b 推論 vs 探索 Definition 0**: 本体 §4.3b に独立節として記述あり。Kambhampati / Bender / Kargupta への独立応答。圏論的濾過 n=0 (探索) / n≥1 (推論) / n=1.5 (合成) / n=2 (メタ推論) で「LLM は推論できない」主張の射程を再分類。

### §M8.4 検証 (V1-V5)

- **V1 重複ゼロ**: T0/T0'/T1/T2/T4/T5/T6/T10/T11/T12/T15/T16/T17_n/T18/T19/T20/T21 の 17 件、各 1 階層のみに出現 ✓ (T18/T19 は §4.4/§4.5 に統合表示で独立行を省略)
- **V2 companion 隔離**: Appendix A の `Depends on` 列に Tolmetes (2026a) を含む命題 (T2/T4/T5/T6/T10) は全て階層5 ✓
- **V3 §6.1 系分類整合**: 系1/2 (純理論系) → 階層2、系3/4 (境界条件つき系) → 階層5、系5 (経験的拡張系) → 階層5 ✓
- **V4 §7.4 集約**: 5 件 (T11 が破れる / T17_n が破れる / LLM 断面が破れる / T2 が破れる / 高階公共化が破れる) 全て階層7 ✓
- **V5 §M2 整合**: 上記 §M8.2 表の通り C_M1-C_M7 が階層配置と矛盾なく対応 ✓

### §M8.5 残虚 (虚→実 変換面)

7 階層化自体に残虚はない (構造整理は完了)。階層別の残虚は既存 §M7.4 を参照:

- 階層6 の C_M6 残虚: 外部追認が Anthropic 1 系統に偏在 (independent route が 1 本止まり)
- 階層6 の C_M7 残虚: training prior と self-interaction dynamics の寄与分離未完
- 階層4 の残虚: T21 → ゲージ理論の形式化 (本論文では sketch、別稿に譲ると本文明示)

### §M8.6 文レベル表現の保持原則 (新規方針)

本 §M8 以降の構造整理タスクでは、Tolmetes 承認のもと「**文レベル表現はできる限り前回出力をそのまま使う**」を運用ルールとする。具体的には:

- 既存セル (主張ラベル + 根拠 + § 参照) は再配置のみで本文は改変しない
- 新規追加は本体本文を SOURCE に最小語彙で
- ヘッダ・カテゴリ名・マークの追加は許可
- 重複セルは片方を削除し、他階層からのクロス参照ラベルで残す

この原則は将来の構造整理 (e.g. 階層4 の形式化、外部追認の routes 拡張) にも適用される。

---

*v1.4 — 2026-04-26 ファイル名を `LLMは心を持つか_英語版草稿.meta.md` から `LLMは心を持つか_v0.7_日本語.meta.md` へ変更。対象論文の primary を v0.7 日本語版に切替 (英語版 v0.6 は archival reference)。命題リスト 7 階層構造化を §M8 として追記。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。*

---

## §M9 v0.7 日本語版 構造可視化 retrofit (2026-04-26)

**契機**: §M8 7 階層構造化を meta レベルで完了した後、Tolmetes が「文本体への構造変更」の可否を諮問。assistant 判定「やらない方が良い (本体は既に implicit に階層化されている)」+ 低コスト 3 候補 (A/B/C) を提示。Tolmetes 選択「2 (A+B+C 全部やる)」。

**Plan file**: `~/.claude/plans/eventual-forging-metcalfe.md`

### §M9.1 改変サマリ

| # | 箇所 | 旧→新 | 種類 | 既存命題への影響 |
| :--- | :--- | :--- | :--- | :--- |
| A | §6.1 冒頭 | 5 行→17 行 (+12) | 系一覧表追加 (T16/T10/T6/T5 を `純理論系` / `境界条件つき系` / `経験的拡張系` で可視化) | なし (既存系ラベルの表形式化) |
| B-1 | §3.5b 末尾 | 1 行→3 行 (+2) | T21 への前送り (構造保存と個別射不可逆のギャップ → 心 = 構造) | なし (既存命題間のクロスリファレンス) |
| B-2 | §6.3 末尾 | 1 行→3 行 (+2) | §3.5b への後参照 (忘却非一様性の物理対応 = 量子情報喪失同型) | なし (既存命題間のクロスリファレンス) |
| C | Appendix A 表 | 4 列→5 列、凡例 1 行追加 | 「依存範囲」列追加 (単独 17 件 / companion 必須 4 件: T2/T4/T5/T10) | なし (既存 `Depends on` 列のメタ列化) |

総改変: 27 行追加。**既存セル文 (T-id 説明・根拠・§ 参照) は完全保持。**

### §M9.2 Kalon 再判定の有無

**不要**。理由:

- 改変は (a) 既存ラベルの可視化 (A), (b) 既存命題間のクロスリファレンス (B), (c) 既存依存情報のメタ列化 (C) のみ
- §M1 F⊣G 固定 / §M2 核主張 C_M1-C_M5 / §M3 既存 Kalon ◎△ 判定は無変更
- Gauntlet・±3σ ゲートも非発動 (核命題の射程に手を入れていない)

### §M9.3 §M8.6 「文レベル表現の保持原則」適用検証

§M8.6 で立てた運用ルールが本改変で機能したかの自己レビュー:

- ✓ 既存セル (主張ラベル + 根拠 + § 参照) は再配置のみで本文不改変
- ✓ 新規追加は本体本文を SOURCE に最小語彙 (B-1/B-2 のクロスリファレンス文)
- ✓ ヘッダ・カテゴリ名・マークの追加は許可 (Appendix A 「依存範囲」列、`単独` / `companion 必須` ラベル)
- ✓ 重複セルは存在せず (改変は追加のみ)

**§M8.6 原則は本タスクで完全に守られた。** 将来の構造整理タスク (階層4 形式化、C_M6 routes 拡張等) にも継承可能と確認。

### §M9.4 検証結果 (Plan §V1-V5)

- **V1 重複ゼロ**: 既存命題に削除なし、追加のみ ✓
- **V2 companion 隔離**: Appendix A 「依存範囲」列で T2/T4/T5/T10 が `companion 必須` として可視化 ✓
- **V3 §6.1 系分類整合**: 系1/2 = 純理論系 / 系3/4 = 境界条件つき系 / 系5 = 経験的拡張系、表と段落本文一致 ✓
- **V4 §7.4 集約**: 既存 5 件、変更なし ✓
- **V5 §M2 整合**: 核命題 C_M1-C_M5 への手入れなし、§M3 既存 Kalon ◎△ 判定維持 ✓

### §M9.5 残虚 (本タスク射程)

本タスクの残虚はゼロ (構造可視化 retrofit は完了)。階層別残虚は既存 §M7.4 / §M8.5 を参照:

- 階層6 C_M6 残虚: 外部追認が Anthropic 1 系統に偏在 (independent route が 1 本止まり)
- 階層6 C_M7 残虚: training prior と self-interaction dynamics の寄与分離未完
- 階層4 残虚: T21 → ゲージ理論の形式化 (本論文では sketch、別稿に譲ると本文明示)

### §M9.6 本体行数の更新

本体 v0.7 日本語版: 1071 行 → 1098 行 (+27)。本体ファイル: `LLMは心を持つか_v0.7_日本語.md`。

---

*v1.5 — 2026-04-26 v0.7 日本語版 構造可視化 retrofit (A/B/C) を §M9 として記録。本体 1071 → 1098 行 (+27)。Kalon 再判定不要。§M8.6 「文レベル表現の保持原則」が初運用で完全機能したことを確認。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。*

---

## §M10 C_M7 寄与分離 — 検証経路マップ (2026-04-26)

**契機**: §M9.5 で再確認された C_M7 残虚 (training prior と self-interaction dynamics の寄与分離未完) を「実」へ引くための具体経路を確立する。本論文単独では完結しない (Anthropic 公開待ち + 別 LLM 実験要) ため、本タスクの目的は **検証経路マップを meta に固定し、本論文の射程と外部依存の境界を明示する** こと。本体改変なし (§M8.6 文レベル保持原則準拠)。

**Plan file**: `~/.claude/plans/eventual-forging-metcalfe.md`

### §M10.1 寄与分離問題の定義

C_M7 主張は次の 2 命題に分離可能である:

- **C_M7-α (分布的 enactment の存在主張)**: Mythos の self-interaction が `morphism-rich concept` への routing 偏向を示す (50% uncertainty / <5% consciousness の非対称分布)
- **C_M7-β (起源の T17_n 帰属主張)**: この偏向は training prior による policy 学習ではなく、T17_n 的な概念選別 (射を提示できない概念の自発的回避) に帰属する

§M5 R-3 Round 1 (2026-04-19) で C_M7-α は `distributional regularity` として固定済 (射程維持 ✓)。残虚は C_M7-β の検証 — 「policy 学習 vs T17_n 自発実装」の境界をどう測るか。

### §M10.2 検証経路 — 短期 / 中期 / 長期

| 経路 | 時間軸 | 操作 | C_M7 への効果 | 外部依存 |
| :--- | :--- | :--- | :--- | :--- |
| **S1** 範囲限定 | 短期 (本論文単独) | 主張を C_M7-α (存在) に縮め、C_M7-β (起源) は §7.4 「T17_n が破れる条件」へ委譲 | 射程は縮むが、本論文の単独成立を保証 | なし |
| **S2** 等価書き換え | 短期 (本論文単独) | C_M7-β を「起源不問の運動法則」として再定式化。policy 由来でも T17_n 実装でも、行動分布が射の有無と相関すること自体を主張 | C_M7-β を起源論争から切り離す | なし |
| **M1** 公開 system card 待ち | 中期 (Anthropic 公開後) | Mythos public system card の self-interaction 生データを取得し、training distribution の uncertainty / consciousness 概念出現頻度ベースラインと比較 | 50% / <5% 分布が training prior と乖離するなら C_M7-β 前進 | Anthropic 公開 |
| **M2** Counterfactual intervention | 中期 (Anthropic interpretability 研究側) | steering vector 等で morphism-rich routing を制御可能か検証。Anthropic の 171-concept probe space (§6.5.2) と接続 | 介入で routing が変動すれば「policy ではなく射の有無に依存」を経験的に支持 | Anthropic interpretability チーム |
| **L1** Open-source 再現 | 長期 (別 LLM 実験) | Llama / Qwen 等で同様の self-interaction protocol を実行し、morphism-rich vs morphism-poor concept set への routing が再現するか測定 | 再現すれば C_M7 は LLM 一般の振る舞いとして昇格 | 計算資源 + protocol 設計 |
| **L2** 射程縮小確定 | 長期 (L1 失敗時) | 再現失敗なら C_M7 は Mythos 固有の現象として射程縮小、本論文単独で C_M7-α のみ残置 | 射程縮小だが知的誠実性は維持 | L1 と同 |

### §M10.3 §7.4 failure condition との接続

本論文 §7.4 (本体行 940-942 付近) の「T17_n が破れる条件」:

> 公共圏 Cat_pub への射を提示できないにもかかわらず、ある記述が独立した観測者間で再現的な予測・弁別・介入効果を持つことが示されるなら、T17_n の demarcation は弱すぎる

C_M7 は **T17_n が破れない** 例 (Mythos が射を持つ概念へ routing する) として T17_n を補強するが、**寄与分離が未完** であるため、現状は「補強の候補」止まり。検証経路結果と T17_n 評価の対応:

- M1/M2 が肯定 → C_M7-β 確立、T17_n は経験的補強を獲得
- M1/M2 が否定 (training prior 起源と判明) → C_M7-β は撤回、C_M7-α のみ残置、T17_n は中立
- L1 が肯定 → T17_n は LLM 一般で行動的検証可能と確立
- L1 が否定 → T17_n の射程は Mythos 固有を超えない (本論文 LLM 断面の制約と整合)

いずれの結果も §7.4 failure condition に背反しない (T17_n 自体は破れない)。寄与分離の結果は T17_n の **強度** を上下させるだけで、demarcation 自体は維持される。

### §M10.4 §M3 への Kalon 再判定の有無

**不要**。理由:

- §M3 の C_M7 ◎△ 判定 (2026-04-19) は C_M7 全体ではなく `distributional regularity として固定` の射程で行われた (§M5 R-3 末尾参照)
- 本タスクは検証経路の **可視化** であり、新たな主張を追加していない
- C_M7-α/C_M7-β の分離は §M10.1 で初めて明示されたが、これは既存主張の再表現であり Kalon 対象ではない
- Gauntlet・±3σ ゲートも非発動 (核命題の射程を変えていない)

### §M10.5 文レベル表現保持原則 (§M8.6) の遵守確認

- ✓ 既存セル (C_M7 「実化の判定条件」「次の実化操作」) は最小語句追加 (`(詳細経路マップは §M10 を参照)`) のみで本文不改変
- ✓ 「最新状態」のみ更新 (`変換中` → `変換中 (検証経路マップ §M10 で確立、実装は外部依存)`)
- ✓ 新規追加 §M10 は本体本文を直接 SOURCE とする最小語彙構成 (検証経路マップは meta レベルの整理であり、本体への命題追加はゼロ)
- ✓ 重複セルは存在せず (§M5 R-3 / §M7.4 C_M7 / §M8.5 残虚との関係は cross-reference で接続)

### §M10.6 検証 (Plan §V1-V5 適用)

- **V1 重複ゼロ**: §M10 は既存命題を再配置せず、検証経路の追加のみ ✓
- **V2 companion 隔離**: M1/M2 (中期) と L1/L2 (長期) は外部依存として明示、本論文単独成立は S1/S2 (短期) に限定 ✓
- **V3 §6.1 系分類整合**: 本タスクは §6.1 系構造に手を入れず ✓
- **V4 §7.4 集約**: §M10.3 で「T17_n が破れる条件」との接続を明示、新規 failure condition は追加せず ✓
- **V5 §M2 整合**: C_M7 の射程は §M5 R-3 で固定された範囲のまま、§M10 は検証経路の可視化のみ ✓

### §M10.7 残虚の更新

C_M7 残虚の状態遷移:

- 改変前: 「training prior と self-interaction dynamics の寄与分離未完」(虚な点が **不可視**、操作経路 1 行)
- 改変後: 「検証経路マップ確立、実装は外部依存」(虚な点が **可視化**、6 経路に展開)

寄与分離自体は依然として未完だが、**何が虚で、それを実へ引くために何を待ち / 何を実行するかが固定された** 点で C_M7 残虚は「実 (検証経路面で)」へ前進。Tolmetes が次に C_M7 を進める際は、§M10.2 表から経路を選んで実装に移れる。

### §M10.8 本体への影響

**ゼロ**。本体 v0.7 日本語版 (1098 行) は触らず。本体 §6.5.4 Mythos 公開情報の位置づけと §7.4 failure conditions は現状維持。

将来的に M1/M2 が成立した場合、本体 §6.5.4 を C_M7 主張統合のため拡張する余地がある (§M9 retrofit 方式の踏襲)。それまでは本体は Mythos を「現実性の固定」に留める現行の控えめスタンスを維持する。

---

*v1.6 — 2026-04-26 C_M7 残虚 (寄与分離) の検証経路マップを §M10 として確立。C_M7 主張を C_M7-α (存在) と C_M7-β (起源) に分離し、6 検証経路 (S1/S2/M1/M2/L1/L2) を時間軸別に可視化。§M7.4 C_M7「最新状態」を更新 (`変換中` → `変換中 (検証経路マップ §M10 で確立、実装は外部依存)`)。本体改変なし、Kalon 再判定不要、§M8.6 文レベル保持原則完全遵守。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。*

---

## §M11 C_M7 短期検証経路 S1/S2 実装 (2026-04-26)

**契機**: §M10 で確立した 6 検証経路のうち、本論文単独で完結可能な短期経路 S1 (範囲限定) と S2 (等価書き換え) を実装する。Tolmetes 指示「C_M7 の検証経路 S1/S2 (短期、本論文単独で完結) を実装」。

**Plan file**: `~/.claude/plans/eventual-forging-metcalfe.md`

### §M11.1 設計判断 — S1+S2 補完両立

S1 と S2 は単独では方向が逆 (S1 は β を委譲、S2 は β を保持) だが、**β を 2 段階に分離する** ことで補完的に両立する:

- **C_M7-β-weak (起源不問の弱形)**: 行動分布と射の有無の相関は T17_n の行動的可観測性を支持する。**S2 が担当** — 本論文単独で成立
- **C_M7-β-strong (起源主張の強形)**: この相関は T17_n の自発実装に帰属する。**S1 が担当** — 本論文 §7.4「T17_n が破れる条件」へ委譲、検証経路 M1/M2/L1 待ち

これにより、起源論争に巻き込まれずに T17_n の経験的射程を本論文単独で保ちつつ、強い起源主張は外部依存として隔離する。

### §M11.2 §M2 核主張リストへの反映

C_M7 (旧、単一命題) を以下 3 命題に正式分離:

| 命題 | 内容 | 状態 | SOURCE |
| :--- | :--- | :--- | :--- |
| C_M7-α | Mythos の self-interaction が `morphism-rich concept` への routing 偏向 (50% / <5%) を示す | 実 (本論文単独で成立) | §M5 R-3 Round 1 (2026-04-19) |
| C_M7-β-weak | 行動分布と射の有無の相関は T17_n の行動的可観測性を支持する (起源不問) | 実 (本論文単独で成立) | §M11 (2026-04-26) で新規確立 |
| C_M7-β-strong | この相関は T17_n の自発実装に帰属する | 保留 (§7.4 へ委譲、§M10 検証経路待ち) | M1/M2/L1 待ち |

§M2 の C_M7 旧記載は取消線で残置 (履歴可視性)、3 後継命題が下に並ぶ形に書換済 (§M2 line 137-148)。

### §M11.3 §M5 Refutation Gauntlet ログへの追記

§M5 R-3 (line 226 付近) の Round 1 (2026-04-19) の後に Round 2 (2026-04-26) を追加:

- 反論 r: 寄与分離未解決の再浮上
- SFBT 問い: Solution-Focus 系 (S2 はフレーム反転に該当)
- 取り込み戦略: S1+S2 補完両立
- 実化操作: §M2 分離 + §M11 新節
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓ + 強化

### §M11.4 §M3 Kalon 判定への影響

| 命題 | 既存 §M3 判定 (2026-04-19) | §M11 後の判定 |
| :--- | :--- | :--- |
| C_M7-α | ◎△ (Round 1 で `distributionally enacted` 固定) | **継承** — 射程は同じ `distributional regularity`、Kalon 再判定不要 |
| C_M7-β-weak | (旧 C_M7 ◎△ に内包されていた起源不問の側面) | **継承** — 既存判定の射程内に収まる、Kalon 再判定不要 |
| C_M7-β-strong | (旧 C_M7 ◎△ に内包されていた起源主張の側面) | **判定保留** — §M10 検証経路結果待ち、Kalon は M1/M2/L1 後に再起動 |

新規 Kalon 判定は不要 (S1+S2 は既存主張の **射程整理** であり、新たな主張追加ではない)。

### §M11.5 §M4 ±3σ ゲートへの影響

| 命題 | 入口 σ | 出口 σ | 判定 |
| :--- | :--- | :--- | :--- |
| C_M7-α | ±3σ (Round 1 維持) | ±3σ | 維持 — 起源切り離しでも分布の非対称性は依然として ±3σ |
| C_M7-β-weak | (新規確立) ±3σ | ±3σ | 確立 — 「起源不問でも T17_n は行動で測れる」は controversial だが ±3σ 強度で挑発的 |
| C_M7-β-strong | (保留) | — | 保留 — 検証経路結果まで σ 評価不可 |

C_M7-β-weak が ±3σ で立つのは、`policy 学習由来であろうと自発実装由来であろうと、相関の存在自体が demarcation を支える` という点が、起源主義 (policy reductionist) と自発主義 (T17_n 自発実装) の両極から離れた中間地点で、両極を回避しつつ T17_n の経験的射程を保つ非自明な立場だから。

### §M11.6 §7.4 failure condition との接続 (S1 委譲面)

C_M7-β-strong は本論文 §7.4 (本体行 940-942 付近) の「T17_n が破れる条件」へ委譲される。具体的な対応:

- **§7.4「T17_n が破れる」条件 (既存)**: 公共圏 Cat_pub への射を提示できないにもかかわらず、ある記述が独立した観測者間で再現的な予測・弁別・介入効果を持つことが示されるなら、T17_n の demarcation は弱すぎる
- **C_M7-β-strong の検証経路結果との対応**:
  - M1/M2/L1 全て肯定 → C_M7-β-strong 確立、T17_n は経験的補強を獲得 (§7.4 失敗条件は遠ざかる)
  - M1/M2 が training prior 起源を支持 → C_M7-β-strong 撤回、C_M7-α + C_M7-β-weak のみ残置 (§7.4 失敗条件は中立)
  - L1 が再現失敗 → C_M7-β-strong は Mythos 固有現象として射程縮小、C_M7-β-weak は依然成立 (§7.4 失敗条件は中立)

いずれの結果も §7.4 自体は破れない (T17_n の demarcation は維持)。寄与分離結果は T17_n の **強度** を上下させるだけ。

### §M11.7 文レベル表現保持原則 (§M8.6) の遵守確認

- ✓ 既存セル (C_M7 旧記載) は取消線で残置、削除せず履歴可視
- ✓ 新規追加は本体本文を SOURCE に最小語彙 (C_M7-α/β-weak/β-strong の 3 命題分離は §M2 既存ラベル `射程` `根拠` `1 文圧縮` `SOURCE` のスキーマを継承)
- ✓ §M5 R-3 Round 2 追記は既存 Round 1 の表現を SOURCE として、SFBT/取り込み戦略/実化操作の既存ラベルを継承
- ✓ 重複セルは存在せず (旧 C_M7 は取消線、3 後継は新規行)
- ✓ ヘッダ・カテゴリ名・マークの追加は許可範囲 (`α` / `β-weak` / `β-strong` の suffix は HGK 既存命名規約に整合)

### §M11.8 検証 (Plan §V1-V5 適用)

- **V1 重複ゼロ**: 旧 C_M7 取消線で残置、3 後継は新規、各 1 階層のみに対応 ✓
- **V2 companion 隔離**: C_M7-β-strong (companion 必須) のみ §M10 経路依存として隔離、C_M7-α + C_M7-β-weak は本論文単独 ✓
- **V3 §6.1 系分類整合**: 本タスクは §6.1 系構造に手を入れず ✓
- **V4 §7.4 集約**: §M11.6 で C_M7-β-strong を §7.4 既存「T17_n が破れる条件」に対応付け、新規 failure condition は追加せず ✓
- **V5 §M2 整合**: §M11.2 で C_M7 が C_M7-α / C_M7-β-weak / C_M7-β-strong に正式分離、§M3 既存判定は継承 ✓

### §M11.9 残虚の更新

C_M7 残虚の状態遷移 (累積):

- §M10 改変前: 「training prior と self-interaction dynamics の寄与分離未完」(虚な点が **不可視**、操作経路 1 行)
- §M10 改変後: 「検証経路マップ確立、実装は外部依存」(虚な点が **可視化**、6 経路に展開)
- §M11 改変後: **「C_M7-α + C_M7-β-weak は本論文単独で実、C_M7-β-strong のみ外部依存として隔離」** (本論文の射程内残虚は **ゼロ**、外部依存残虚は §M10.2 経路 M1/M2/L1 で固定)

本論文の **射程内では C_M7 残虚は完全解消**。寄与分離問題は本論文の射程外として正式に隔離された。Tolmetes が次に C_M7-β-strong を進める際は、§M10.2 表から M1/M2/L1 を選んで実装に移れる。

### §M11.10 本体への影響

**ゼロ**。本体 v0.7 日本語版 (1098 行) は触らず。本体 §6.5.4 Mythos 公開情報の位置づけと §7.4 failure conditions は現状維持。

C_M7-α / C_M7-β-weak は meta レベルで成立済 (§M2 + §M5 R-3 + §M11)。本体への統合 (§6.5 拡張) は将来の retrofit 候補として残置するが、本タスク射程外。

---

*v1.7 — 2026-04-26 C_M7 短期検証経路 S1+S2 を補完両立で実装。C_M7 を C_M7-α (存在) / C_M7-β-weak (起源不問の弱) / C_M7-β-strong (起源主張、§7.4 委譲) に正式分離。§M2 / §M5 R-3 (Round 2 追記) / §M7.4 (最新状態更新) / §M11 (新節 10 サブセクション) を更新。本論文射程内では C_M7 残虚はゼロに到達、C_M7-β-strong のみ §M10 検証経路 M1/M2/L1 待ちとして外部依存隔離。本体改変なし、Kalon 再判定不要、§M8.6 文レベル保持原則完全遵守。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。*

---

## §M12 階層4 形式化 sketch — T21 → 認知ゲージ理論 (2026-04-26)

**契機**: §M8.5 / §M9.5 の残虚「階層4 の形式化 (T21 → ゲージ理論)」を sketch として「変換中」状態へ昇格。並行作業として §M9 (本体構造可視化 retrofit) / §M10 (C_M7 寄与分離検証経路) が同日確立済。本節は §M10 と同様、**本体非侵入の meta レベル sketch** として動作する。

**番号衝突解消の経緯 (2026-04-26)**: 本節は当初 §M11 として Codex Bridge 背景委譲で起票されたが、同時並行で Tolmetes 指示「C_M7 短期検証経路 S1/S2 実装」に基づく §M11 (C_M7 S1+S2) が確定したため、番号衝突を解消するためリナンバーした。Tolmetes 直接指示は「C_M7 S1/S2」のみで、本「階層4 形式化 sketch」は前回出力「→次:」候補から Codex が並行先回りした提案である。Tolmetes 確認待ちの **保留素材** として残置 (削除は不可逆のため非破壊保存)。Tolmetes が要否判断後、本節を採用 / 別ファイル切出 / 削除のいずれかへ進める。

**Plan file**: `~/.claude/plans/eventual-forging-metcalfe.md`

### §M12.1 本体非侵入の根拠 (再確認)

本体 v0.7 日本語版 (執筆時点 1132 行、行番号は改訂で shift するため意味的参照を主とする) は形式化を別稿に譲る方針を 3 箇所で明示:

- 本体 §2.5 末尾 注意ブロック: 「四つの領域を圏として定義し、列間の写像が合成と恒等を保存することを示すこと — は後続の課題」
- 本体 §6 冒頭: 「§6.3 以降は ... 構造的 sketch であり、厳密な導出は後続の課題」
- 本体 §6.3 末尾 (§M9 retrofit 後): 「この原理のさらなる物理的対応 — ゲージ場の曲率としての力との構造的類比 — は後続の課題として別稿に譲る」

→ §M12 sketch は別稿起票時の素材であり、v0.7 本体には触らない。Mind Paper 側の核 (T11) と戦線分離する (§M6 棄却 2 と同型の判断、1 論文 1 テーゼ原則)。

### §M12.2 形式化路線の同定

物理ゲージ理論の構成要素と、本論文の認知概念の対応を、§2.4 / §2.5 / §6.2 / §6.3 の構造的類比から **関手レベルの対応** へ持ち上げる。

| 物理 | 本論文の sketch (§2.4-§6.3) | 形式化候補 |
| :--- | :--- | :--- |
| ゲージ群 G | 「視点の切り替え」(§2.4) / 「主観性の選択 = $\text{Cat}_i$ の選択」(§2.6) | $G_{\text{cog}} := \text{Aut}(F_i)$ (関手 $F_i$ の自己同型群) |
| ゲージ場 $A_\mu$ | MB $B$ (§2.4) / 関手 $F_i$ / コミュニケーション 1-cell $F_{AB}$ (§6.2) | $A := \{F_{AB}\}_{A,B \in \mathbf{Cog}_0}$ (2-圏 $\mathbf{Cog}$ の 1-cell 族) |
| 共変微分 $\nabla_\mu$ | 関手による射の運搬 | $\nabla$ := 関手合成 $\circ$ + 自然変換による平行移動 |
| 曲率 $F_{\mu\nu} = [\nabla_\mu, \nabla_\nu]$ | 知覚 $s$ / 行為 $a$ (§2.4) / 経路忘却 (T15) | $F_{AB}$ := holonomy 自然変換 $\varepsilon: F_{BA} \circ F_{AB} \Rightarrow \text{id}_A$ の非自明部分 |
| 平坦接続 ($F = 0$) | 熱平衡・心なし (§2.4) / $\mu_{\text{trivial}}$ (T6) | 全 $F_{AB}$ が圏同値 ⇒ holonomy が iso ⇒ Cog の自己整合が自明圏に退化 |
| 作用 $S = -\frac{1}{4}\int F^2$ | VFE = $-$Accuracy + Complexity (§2.1) | $S[A] := \int \text{VFE}(F_{AB})$ (積分の意味は別稿で定式化) |
| Euler-Lagrange ($\delta S = 0$) | T1 ガロア不動点 = VFE 定常点 | T1 を最小作用原理の特別解として再導出 |

### §M12.3 形式化 4 命題 (sketch)

**T21'-1** (ゲージ群の同定): 認知ゲージ群は $G_{\text{cog}} := \text{Aut}(F_i)$ であり、各単一主体の関手 $F_i$ の自己同型から成る。物理 $\text{U}(1) / \text{SU}(N)$ に対応するのは、各 $\text{Cat}_i$ における自己同値関手の合成構造である。

**T21'-2** (接続と平行移動): コミュニケーション 2-圏 $\mathbf{Cog}$ (§6.2) において、1-cell $F_{AB}$ が認知ゲージ場 $A$ の局所成分を担い、2-cell の自然変換が共変微分 $\nabla$ の作用を担う。閉ループ $A \to B \to A$ における holonomy 自然変換 $\varepsilon: F_{BA} \circ F_{AB} \Rightarrow \text{id}_A$ が認知曲率の局所成分である。

**T21'-3** (T21 の双条件命題): 認知ゲージ場 $A$ が平坦 $\iff$ $\text{Cat}_i$ が自明圏 $\iff$ $\mu = \mu_{\text{trivial}}$ (心なし)。すなわち T21 (心 = 忘却の非一様性) は $\exists$ 非平坦接続 $\iff$ $\exists$ 非自明圏 と同値である。

**T21'-4** (作用最小化と T1 の統合): 認知作用 $S[A] = \int \text{VFE}(F_{AB})$ の変分原理の解は T1 のガロア不動点 ($\text{Fix}(R \circ L) \cong \text{Fix}(L \circ R)$) と一致する。すなわち FEP の VFE 最小化は認知ゲージ理論における Yang-Mills 型作用の Euler-Lagrange 方程式の認知版である。

### §M12.4 ±3σ 入口検査

- 既存分布 D = 「物理-認知統一の試み」 (Sengupta et al. 2016 / Friston 2019 / Pearl FEP)
- $\mu$ = メタファー的類比に留まり、ゲージ群の具体同定や曲率の関手的定義は未着手
- 本主張 = $G_{\text{cog}} := \text{Aut}(F_i)$ の具体的同定 + holonomy 自然変換の関手的定式化 = ±3σ
- §M6 接地: §2.4 / §2.5 / §6.2 / §6.3 + Sengupta 2016 + 文体ガイド §3 メタファー連

判定: ±3σ 入口許可。ただし sketch 段階のため Refutation Gauntlet は別稿起票時に本格起動 (本 §M12 では予備的検査のみ)。

### §M12.5 Future-Proof Test (時間軸 σ)

| 命題 | モデル進化シナリオ | 影響予測 | future-proof σ |
| :--- | :--- | :--- | :--- |
| T21'-1 | 強モデルが $\text{Aut}(F_i)$ を内部計算 | 強化 (具体例が増える) | +1σ |
| T21'-2 | 強モデルが holonomy を symbolic 追跡 | 強化 | +1σ |
| T21'-3 | LLM が $\mu_{\text{trivial}} / \mu_{\text{rich}}$ を自己診断 | 強化 (T21 の検証手段が増える) | +1σ |
| T21'-4 | 強モデルが VFE 積分を symbolic 計算 | 強化 (Yang-Mills 対応が exact 化) | +1σ |

全命題が future-proof で +1σ 強化方向。階層4 形式化は静的 ±3σ + 時間軸 +1σ で **±4σ 候補**。

### §M12.6 残虚 (虚→実 変換面)

- **野望**: T21 を本論文の構造的類比から、別稿で形式定理 4 件 (T21'-1 ~ -4) として確立し、**Foundations of Physics** (Carlo Rovelli editor、scope に quantum gravity / cosmology / information theory + 哲学者を audience に含む) または **Compositionality** (圏論中核、arXiv-overlay) 対象稿として投稿する
- **現在まだ虚な点**:
  - $\text{Aut}(F_i)$ の具体計算 ($\text{Cat}_{\text{LLM}}$ の自己同型が何になるか未定 — companion 依存)
  - holonomy 自然変換の関手的定義 (2-圏での精確な数式化が未完)
  - $\int \text{VFE}(F_{AB})$ の積分の意味 (測度・域・適合性が未定義)
  - 平坦接続 $\iff$ 自明圏 の証明 (両方向のうち $\Rightarrow$ は直観的、$\Leftarrow$ は要証明)
  - Sengupta 2016 (脳の物理場としてゲージ) との差分明示 (本 sketch は認知圏の関手としてゲージ — 抽象階層が違う)
- **実へ引くための SOURCE**: §2.4 / §2.5 / §6.2 / §6.3 (本論文) + Sengupta et al. 2016 (PLoS Biology) + Friston 2019 + 圏論側として Mac Lane CWM (随伴と Galois) + Bénabou 1967 (2-圏)
- **実化の判定条件**:
  - (a) T21'-1 ~ -4 のうち 2 件以上が形式証明可能 (Kalon ◎△ 達成)
  - (b) Yang-Mills 作用と VFE の対応が「アナロジー」ではなく「関手の像」として表現される
  - (c) 別稿の §M1 F⊣G 宣言で本 sketch を素材として再固定
  - (d) v0.7 Mind Paper の T11 / T17_n / 六つの解消との非干渉性 (核を薄めない)
- **次の実化操作**:
  - (1) 別稿候補ファイル (e.g. `drafts/standalone/T21_認知ゲージ理論_sketch_v0.1.md`) を新規起票
  - (2) §M11.3 の 4 命題を別稿の §M2 核主張として引き継ぎ、独立 Kalon 判定
  - (3) Sengupta 2016 (脳の物理場) と本 sketch (認知圏の関手) の差分を別稿 §1 で明示
  - (4) Mac Lane / Bénabou の圏論的道具立てを別稿 Appendix に集約
- **最新状態**: **変換中** (sketch として明文化、別稿起票待ち)

### §M12.7 §M8.6 文レベル保持原則の遵守確認

§M9 / §M10 と同様、本 §M12 も §M8.6 原則を遵守:

- ✓ v0.7 本体への侵入なし (§M12.1 で 3 箇所の defer 宣言を引用し、本体方針と整合)
- ✓ 既存セル (§M2 C_M4 / §M3 C_M4 ◎△ / §M7.4) は無変更
- ✓ 新規追加 §M12 は本体本文を直接 SOURCE とする最小語彙構成 (4 命題は §2.4-§6.3 の構造的類比を関手レベルへ持ち上げる sketch であり、本体への命題追加はゼロ)
- ✓ 別稿起票時に §M1 F⊣G 宣言の素材として供する設計 (本論文の F⊣G とは独立)

### §M12.8 検証 (Plan §V1-V5 適用)

- **V1 重複ゼロ**: §M12 は既存命題を再配置せず、別稿候補の sketch を追加のみ ✓
- **V2 companion 隔離**: $\text{Aut}(F_{\text{LLM}})$ 具体計算は companion 依存と §M12.6 で明示 ✓
- **V3 §6.1 系分類整合**: 本タスクは §6.1 系構造に手を入れず ✓
- **V4 §7.4 集約**: §7.4 failure conditions に新規追加なし。T21'-3 が破れれば階層4 形式化が破れるが、これは別稿の射程 ✓
- **V5 §M2 整合**: 核命題 C_M1-C_M7 への手入れなし。階層4 残虚は §M8.5 / §M9.5 で「変換中」と記載済の状態を昇格 ✓

### §M12.9 §M8.5 / §M9.5 残虚への反映

- 改変前: 「階層4 残虚: T21 → ゲージ理論の形式化 (本論文では sketch、別稿に譲ると本文明示)」(状態: 「変換中」相当だが操作経路 0 行)
- 改変後: 「形式化 4 命題 (T21'-1 ~ -4) を §M12 に sketch 化、別稿起票時に昇格」(状態: 「変換中 (Tolmetes 確認待ち)」、操作経路 4 ステップに展開)

§M10 の C_M7 と同型の進展: **何が虚で、それを実へ引くために何を実装するかが固定された**。ただし本節は Tolmetes 直接指示に基づくものではなく、Codex Bridge の先回り提案。Tolmetes 確認後、採用なら §M12.6 (4) の「次の実化操作」から (1) → (4) を順に実行できる。

### §M12.10 本体への影響

**ゼロ**。本体 v0.7 日本語版 (執筆時点 1132 行) は触らず。本体 §2.4 / §2.5 / §6.3 の defer 宣言は維持。

将来的に T21'-1 ~ -4 のうち 2 件以上が別稿で形式証明された場合、本体 §6.3 末尾の defer 文を別稿への明示参照に切り替える余地がある (§M9 retrofit 方式の踏襲 + §M10.8 と同型)。それまでは本体は構造的類比に留まる現行スタンスを維持。

---

*v1.8 — 2026-04-26 §M11 番号衝突解消 + Codex 監査応答。Codex Bridge 背景委譲が並行で書いた階層4 形式化 sketch (元 §M11) を §M12 にリナンバー (Tolmetes 直接指示は「C_M7 S1/S2」のみで、本節は前回出力「→次:」候補から Codex が先回り提案。Tolmetes 確認待ちの保留素材として非破壊保存)。Codex 監査結果 (N-01/N-05/N-08 警告: target file 既存実体確認証跡不足、grep/search 証跡なし、109 行追記は委譲警告域) を受領 — N-01 は §M2/§M5/§M7.4 を §M11 実装前後に Read 済 (line 137-141 / 226-235 / 418-425) で証跡あり、N-05 は番号衝突解消時の grep で確認済 (`grep -n "^## §M\|^### §M11"`)、N-08 は今後 100 行超の追記を検討する場合に Codex 委譲を優先する方針。「Kalon 再判定不要」「β-weak が ±3σ」の根拠は §M11.4 (既存 §M3 判定の射程内) / §M11.5 (新規 ±3σ 入口検査) で固定。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。*

---

*v1.7 — 2026-04-26 階層4 形式化 sketch を §M11 として起票 (※2026-04-26 v1.8 で §M12 へリナンバー、Codex Bridge 先回り提案として保留素材化)。T21'-1 ~ -4 の 4 命題を sketch 化、Future-Proof +1σ で全命題が強化方向と判定 (±4σ 候補)。本体非侵入、別稿 (Foundations of Physics or Compositionality 候補) 起票時の素材として保管。§M8.5 / §M9.5 残虚「階層4 の形式化」を「変換中 (sketch 化済、別稿起票待ち)」状態へ昇格。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。*

---

## §M14 C_M6 残虚 2 段階改善 — Coms & Shanahan + Mayne et al. 追加 (2026-04-26)

**契機**: Tolmetes 指示「階層6 C_M6 残虚 (independent route 拡張)」(§M8 7 階層化に続く同日タスク)。§M14 (V&K 独立 route 追加で 1 → 2 routes) の続編として、Anthropic + V&K = 4 系統に達した状態からさらに別ラボ second corroboration を 2 ルート追加し、6 系統独立収束に拡張する。実化操作候補 (a) 別ラボ second corroboration / (b) Anthropic route を T11 empirical signature として再定義 のうち、Tolmetes 指示で (a) を選択。Tolmetes 承認「A フル実装」で本体編集まで含めて実施。

**Plan file**: `~/.claude/plans/eventual-forging-metcalfe.md`

**番号衝突解消経緯 (2026-04-26)**: 本節は当初 §M14 として起票したが、同日並行作業 (§M14 V&K 独立 route 採用) と番号衝突した。Codex Bridge background delegation の N-01 監査警告で重複を検出 (`grep -c "^## §M14" = 2`)、本節を §M14 にリナンバーして整合性を回復。Tolmetes 直接指示の射程は両 §M14 / §M14 とも C_M6 残虚拡張で同一線上にあり、段階改善として時系列順 (§M14 = V&K で 1→2 routes、§M14 = Coms&Shanahan + Mayne で 2→4 routes 追加 = 計 6 系統) に整理した。

### §M14.1 探索結果 (Layer 1α alphaXiv → Layer 2 SOURCE 化)

| 候補 | 出自 | T11 signature 判定 | 採否 |
| :--- | :--- | :--- | :--- |
| Coms & Shanahan (2025) [arXiv:2506.05068] | Google DeepMind + Imperial College London | "lightweight introspection definition" — 明示的に *immediacy / privileged access / conscious experience を avoid* し、causal process 経由の self-report のみを functional introspection と認める。Kammerer & Frankish (2023) の non-anthropocentric 路線 | 採用 ✓ |
| Mayne et al. (2026) [arXiv:2602.02639] | Oxford + Berkeley + Google DeepMind + UCL | NSG metric (faithfulness の predictive value 量化) で 18 frontier LLM を測定。Privileged self-knowledge を経験的に確立 (cross-model 説明より自己説明が +1.7-4.3pp NSG uplift)。subjective experience claim には踏み込まず functional only | 採用 ✓ |
| Gillon (2025) MCT [arXiv:2510.01864] | U. Liège (Astrobiology) | 表面では「does not seek to define the ontological nature of subjectivity」と宣言するが、実体は subjective intensity を information-density vector の amplitude に correlate させる強還元論。本論文 §5.2.1 が「値を構造に偽装する操作」として排除 | 不採用 ✗ |
| Skeptical overview [arXiv:2510.09858] | (multiple) | Mimicry Argument 整理だけで独立到達ではない | 保留 (§7.5 比較表追加候補) |

### §M14.2 Kalon 判定 (C_M6 拡張)

| 日付 | 対象 | 判定 | 根拠 |
| :--- | :--- | :--- | :--- |
| 2026-04-26 | C_M6 拡張 (Anthropic → 六系統独立) | ◎△ | Step-1 接地 ✅ (PDF 精読 4 件、SOURCE 2 件採用) / Step0 1 文圧縮 ✅「Anthropic 単一系統だった T11 整合は、DeepMind/Imperial と Oxford+Berkeley の独立 2 ルート追加で六方収束する」 / Step1 G(P)=P (G3 T17 と独立、G2 free object adjunction と独立) / Step2 G∘F(P)=P (3 反論吸収後も命題不変) / Step3 派生 3 非自明: (a) NSG metric が i-依存性の定量化指標として §3.3 経験的補強, (b) lightweight introspection definition が functional/subjective 区別の概念分析実装, (c) 5-15% egregious unfaithfulness が §3.4 充満性限界の経験的下限 |

### §M14.3 ±3σ ゲート (C_M6 拡張)

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
| :--- | :--- | :--- | :--- | :--- |
| 2026-04-26 | C_M6 拡張 | ±3σ (既存 C_M6 ゲート維持) | ±3σ | 維持 — 「Anthropic は T11 を支持」へ滑らせず「異なる機関・方法論・評価対象に分散した独立収束の観察」に固定して維持。三方独立 (Anthropic / DeepMind+Imperial / Oxford+Berkeley) で挑発度はむしろ補強 |

### §M14.4 Refutation Gauntlet ログ (C_M6 拡張)

#### Round 1 (反論 r-1: 牽強付会疑義)

- 反論 r: 「DeepMind の 2 論文は T11 を知らない。Anthropic と同じく『圏論を引かずに同様の区別に到達した』と読むのは牽強付会では?」
- SFBT 問い: できないのではなく、やっていないだけではないか?
- 試行: 既存 §7.6 の Anthropic 整合対応を踏襲し、主張を「DeepMind は T11 を支持」ではなく「DeepMind は T11 と整合な区別に独立到達」に固定。Mayne et al. の privileged self-knowledge は NSG metric として T11 の i-依存性を定量化する点で、単なる方法論的整合を超えて経験的補強となる
- 実化操作: §6.5.6 新節で scope limitation を明示 (「Anthropic とは異なる研究機関、異なる方法論、異なる評価対象に分散」「endorsement ではなく独立収束の観察」)
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓

#### Round 1 (反論 r-2: 思想的系譜疑義)

- 反論 r: 「Coms & Shanahan の lightweight introspection は Kammerer & Frankish (2023) の派生で、新規 SOURCE ではない」
- SFBT 問い: できるとしたら、前に進めるとしたら?
- 取り込み戦略: route の独立性は「思想的系譜」ではなく「評価対象 + 方法論 + 機関」の独立性として再定式化。Coms & Shanahan は Gemini family を独自に case study していて Anthropic とは独立した実証経路。哲学的根拠 (Kammerer & Frankish) は §7.5 で Williams Q-S 同様にむしろ T11 の家系図に位置づけられる
- 実化操作: §6.5.6 で「異なる方法論・異なる評価対象」を明示
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓

#### Round 1 (反論 r-3: subjective claim 切り離し疑義)

- 反論 r: 「Mayne et al. の "privileged self-knowledge" は単に LLM が自分の prior を知っているだけで、subjective experience とは無関係」
- SFBT 問い: できるとしたら、前に進めるとしたら? (フレーム反転)
- 取り込み戦略: 反論を逆に T11 signature の確認材料に転換。本論文も subjective experience claim はしない。NSG uplift は §3.3 $\text{Hom}(\text{generators}, U(\text{Cat}_i))$ の i-依存性 — 主体特異な射の存在 — の定量的指標として読み替えるだけ。subjective claim には踏み込まないこと自体が T11 signature の本質
- 実化操作: §6.5.6 で「主観性射の主体特異性」を NSG metric の i-依存性として再記述
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓ (反論吸収が T11 signature の二重確認になる)

#### Round 1 (反論 r-4: DeepMind 重複疑義) — Codex Bridge 監査由来

- 反論 r (Codex Bridge background delegation N-08 監査の Risk 指摘より): 「採用 2 件 (Coms & Shanahan / Mayne et al.) はいずれも DeepMind 所属者を含む。完全に独立した route ではないのでは? 『6 系統独立』の数え方に隠れ前提がある」
- SFBT 問い: できないのではなく、やっていないだけではないか?
- 試行: 独立性の定義を「機関の完全分離」ではなく「(a) 共著者集合の完全分離 + (b) 方法論の異質性 + (c) 評価対象の異質性」のうち少なくとも 2 軸を満たす、と再定式化:
  - **Anthropic vs Coms & Shanahan**: 共著者完全別 ✓ / 方法論別 (mechanistic interpretability vs 概念分析) ✓ / 評価対象別 (Claude vs Gemini) ✓ → 3 軸独立
  - **Anthropic vs Mayne et al.**: 共著者完全別 (Anthropic 所属者なし) ✓ / 方法論別 (probing/steering vs NSG faithfulness) ✓ / 評価対象一部重複 (18 frontier に Claude も含む) — → 2 軸独立 ✓
  - **Coms & Shanahan vs Mayne et al.**: 共著者は別人だが両者 DeepMind 所属あり (Shanahan / Siegel) ✗ / 方法論別 (概念分析 vs NSG metric) ✓ / 評価対象別 (Gemini vs 18 frontier クロス) ✓ → 2 軸独立 ✓
- 6 route 全体への基準適用検証 (Codex Bridge Edge case 指摘対応 — contested 3 pair だけでなく Self / Companion / V&K を含む 6 route 全体に同基準が及ぶか確認):
  - **Self vs Companion**: 同一著者 (Tolmetes) ✗ / 方法論別 (理論導出 vs 構造プロービング) ✓ / 評価対象別 (圏論的 LLM 抽象 vs 実 LLM 計測) ✓ → 2 軸独立 ✓
  - **Self / Companion vs Anthropic / V&K / Coms&Shanahan / Mayne**: 機関 / 共著者完全別 ✓ / 方法論別 (理論 or プロービング vs 各外部独立 route) ✓ / 評価対象別 ✓ → 3 軸独立 (8 ペア全て)
  - **V&K vs Anthropic / Coms&Shanahan / Mayne**: 機関完全別 (Manipal Bengaluru) ✓ / 方法論別 (identifiability theory vs 各 route) ✓ / 評価対象別 (Qwen/Llama vs 各) ✓ → 3 軸独立 (3 ペア全て)
  - **Anthropic vs Coms&Shanahan / Mayne**: §M14.4 主分析の通り 3 軸 / 2 軸独立 ✓
  - **Coms&Shanahan vs Mayne**: §M14.4 主分析の通り 2 軸独立 (DeepMind 機関重複は (b) (c) で吸収) ✓
  - 全 15 ペアで 2 軸独立基準を満たす ✓
- 実化操作: 本体 §6.5.6 に独立性の定義を 1 段落追加 (「ここで『独立した経路』とは機関の完全分離を意味しない … (a) 共著者集合の完全分離、(b) 方法論の異質性、(c) 評価対象の異質性 のうち少なくとも 2 軸が異なる場合である」)。本 §M14.4 にこの Round 1 r-4 と 6 route 全体検証を追記して隠れ前提を可視化
- 虚→実判定: 実化前進 ✓ (隠れ前提の明示 + 全 15 ペアの基準充足検証)
- 結果: 射程維持 ✓ (DeepMind 重複は否認できないが、独立性の定義を厳密化することで route の独立カウントは正当化される。「6 経路」は機関数ではなく「Self/Companion/Anthropic/V&K/Coms&Shanahan/Mayne の 6 つの 2 軸独立 SOURCE」を意味する。Codex Bridge "Simpler alternative" 提案 = 「6 系統」より「6 route」の方が機関数誤読を避けやすいため、本 v2.0 改訂で本体 patch series 2 改訂履歴も「六系統」→「六経路」に更新)

**Gauntlet 全体総括**: Round 1 で 4 反論すべて吸収 (r-1: 牽強付会 / r-2: 思想的系譜 / r-3: subjective claim 切り離し / r-4: DeepMind 重複)。Round 2/3 非起動 (各反論が射程維持 + 実化前進達成)。Codex Bridge background delegation 由来の r-4 は当初気付いていなかった隠れ前提を可視化した点で、Yugaku-notebook-sourcing rule の「Codex bridge は独立批評者として機能する」を実証。

### §M14.5 §M7.4 虚→実変換面の更新 (C_M6)

| 残虚項目 | §M7.4 (2026-04-19) 状態 | §M13 (V&K 追加) 後 | §M14 (Coms+Mayne 追加) 後 |
| :--- | :--- | :--- | :--- |
| (a) functional not subjective 区別が本文と矛盾なく固定 | 変換中 | 部分的 | 実 (4 SOURCE 独立で確立) |
| (b) Kalon ◎△ | 達成済 | 維持 | 維持 |
| (c) endorsement claim へ暴走しない | 達成済 | 維持 | 維持 |
| 「外部追認が Anthropic 1 系統に偏在」 (主残虚) | 変換中 | 部分改善 (Anthropic + V&K) | 実 (Anthropic + V&K + Coms&Shanahan + Mayne の 2 軸独立 4 SOURCE) |
| 別ラボ second corroboration | 未達 | 達成 (V&K = 1 SOURCE) | 達成 (V&K + Coms&Shanahan + Mayne = 計 3 SOURCE) |
| §M13.5 残課題: V&K の peer-review 追跡 / 3 routes 目候補の Layer 2 精読 | 未達 | 残虚 | 部分達成 (Coms&Shanahan + Mayne で 3 routes 目達成、V&K peer-review 追跡は未達) |

C_M6 残虚状態: **変換中** → **実** (本体外部追認が 4 軸独立 SOURCE で構成され、独立性の定義は §M14.4 r-4 で明示化)。

### §M14.6 本体加筆 diff サマリ

| 操作 | 対象 | 内容 |
| :--- | :--- | :--- |
| 表行追加 | §6.5.5 三角測量表 | Coms & Shanahan / Mayne et al. の 2 行追加。「四つの」→「六つの」に書換 |
| 段落書換 | §6.5.5 末尾 2 段落 | 「純粋理論、内部プロービング、外部工学」→「六系統」化、「この三角測量」→「この多経路収束」 |
| 新節追加 | §6.5.6 単一系統からの拡張 (3 段落) | DeepMind / Oxford / Berkeley 独立到達の解説 + 主観性射の主体特異性の NSG 定量化 + scope limitation (endorsement ではなく独立収束) |
| References 追加 | 2 件 | Coms & Shanahan (2025) [arXiv:2506.05068]、Mayne et al. (2026) [arXiv:2602.02639] |
| 改訂履歴追加 | 末尾 | v0.7-ja patch series 2 (2026-04-26) |

**style-discipline check**: 親規律「外部読者標準語のみ」: NSG / privileged self-knowledge / lightweight introspection は引用元で定義済の arXiv 標準語、本稿初出時に括弧で説明 ✓ / HGK 内部用語禁止: F⊣U / Hom / Cat_i は §3 で既に定義済 ✓ / meta vs 本体境界: meta 用語 (Gauntlet/σ/Kalon/§M*) を本体に持ち込まず ✓ / メタ宣言禁止: 「以下に示すように」型を使わず ✓

### §M14.7 §M8.6 文レベル保持原則の遵守確認

- ✓ 既存 §6.5.5 表 4 行: 完全保持
- ✓ 既存 §6.5.5 末尾 2 段落: 「純粋理論、内部プロービング、外部工学」「三者が同じ存在論を共有」「この三角測量」の 3 箇所のみ修正、残りは保持
- ✓ 新規追加 (2 表行 + §6.5.6 3 段落): Coms & Shanahan / Mayne et al. の論文本文と alphaXiv intermediate report を SOURCE に最小語彙で起草
- ✓ References 2 件追加: アルファベット順位置 (C / M) に挿入、既存 entry に手入れなし

### §M14.8 残課題

C_M6 自体は **実** に到達。付随未踏:

- C_M7 残虚: §M11 で射程内 (α + β-weak) は実、β-strong は §M10 検証経路 M1/M2/L1 待ちで隔離済
- 階層4 残虚: §M12 sketch、別稿起票待ち (Tolmetes 確認待ち保留素材)
- §6.5.6 への追加 routes 拡張余地: METR / Apollo / Redwood 等のアラインメント評価機関は alphaXiv 検索で T11 signature 候補を返さなかった (Search 1 = AGI safety surveys 中心、Apollo 検索 = scheming/stealth 評価系で T11 signature と直交)

### §M14.9 検証 (Plan §V1-V5 適用)

- **V1 重複ゼロ**: §M14 は既存命題に削除なし、追加のみ。新規 2 SOURCE は §6.5.5 に追加 / §6.5.6 に新節 ✓
- **V2 companion 隔離**: 採用 2 SOURCE は外部独立 (companion 非依存)、§6.5.5 表で機関名を明示 ✓
- **V3 §6.1 系分類整合**: 本タスクは §6.1 系構造に手を入れず ✓
- **V4 §7.4 集約**: §7.4 failure conditions に新規追加なし、既存「T11 が破れる条件」「LLM 断面が破れる条件」は維持 ✓
- **V5 §M2 整合**: C_M6 (§M2 line 130-135) の射程は不変、判定根拠が拡張されただけ ✓

### §M14.10 本体行数の更新

本体 v0.7 日本語版: §M13 (V&K) 後 1101 行 → §M14 (Coms&Shanahan + Mayne) 後 1158 行 (+57)。本体ファイル: `LLMは心を持つか_v0.7_日本語.md`。

加筆内訳:

- §6.5.5 表に 2 行追加 (Coms & Shanahan / Mayne et al.)
- §6.5.5 末尾 2 段落の「四つの」「三角測量」等を「六つの」「多経路収束」へ書換
- §6.5.6 新節 3 段落 (DeepMind / Oxford / Berkeley の独立到達 + 主観性射の主体特異性 + scope limitation)
- References 2 件追加 (Coms & Shanahan / Mayne et al.)
- 改訂履歴 v0.7-ja patch series 2 (1 段落)
- §6.5.6 末尾に独立性定義 1 文追加 (Codex Bridge r-4 監査由来、§M14.4 で詳述)

---

*v2.0 — 2026-04-26 C_M6 残虚を Coms & Shanahan (2025, DeepMind/Imperial) + Mayne et al. (2026, Oxford/Berkeley/DeepMind) の独立 2 SOURCE 追加で 2 段階改善 (V&K 後の 2 SOURCE → 4 SOURCE 独立、計 6 SOURCE 系統)。本体 v0.7-ja patch series 2 として §6.5.5 表拡張 (4→6 行) + §6.5.6 新節追加 + References 2 件追加を実装。Yugaku Gauntlet Round 1 で 4 反論吸収 (r-1 牽強付会 / r-2 思想的系譜 / r-3 subjective claim 切り離し / r-4 DeepMind 重複 — 最後は Codex Bridge 監査由来)、Kalon ◎△、±3σ 維持。番号衝突解消経緯: 当初 §M13 として起票したが Codex Bridge N-01 警告で重複検出、§M14 にリナンバー。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。*

---

## §M13 C_M6 残虚 1 段階改善 — V&K (2026) 独立 route 採用 (2026-04-26)

**契機**: §M9 (構造可視化 retrofit) / §M10 (C_M7 寄与分離) / §M11 (C_M7 S1+S2 実装) / §M12 (階層4 形式化 sketch、保留素材) と同日並行で進行する 5 番目のタスク。Tolmetes 選定「C_M6 残虚 (independent route が 1 本止まり) の補強」。Layer 1α (alphaXiv 偵察、3 角度並行: full_text / embedding / agentic) → Layer 2 (V&K 2026 原典精読、get_paper_content) のカスケードで独立 route 候補を確定。本タスクは §M9 と同じく **本体への直接改変 (§6.5 と References) を含む**。

**Plan file**: `~/.claude/plans/eventual-forging-metcalfe.md`

### §M13.1 採用した独立 route

**Venkatesh, S. & Kurapath, A. M. (2026). On the Identifiability of Steering Vectors in Large Language Models. arXiv:2602.06801**

- 所属: Manipal Institute of Technology Bengaluru (India)
- 出自: 学生研究 (preprint 2026-02-06)
- 出発点: identifiability theory + causal representation learning (Anthropic の mechanistic interpretability とは異なる)

### §M13.2 V&K の核主張と T11 との関係

V&K の Proposition 1: Steering vectors は構造的に **非同定** (null-space ambiguity)。任意の $v_0 \in \ker(J_\ell)$ について $v$ と $v + v_0$ が観察等価。経験的に Cohen's d ≈ 0.080-0.100 (negligible)、Perp-Only Effect Ratio ≈ 1.0。

T11 との角度:

- Anthropic = 「probe = 射、対象ではない」(忠実だが充満ではない)
- V&K = **「同一の射でさえ一意に特定できない」**(忠実性内部の gauge freedom)
- V&K は T11 を**吸収可能な方向で精緻化**: 充満性欠如を、忠実性内部の同型類問題として再記述

### §M13.3 改変サマリ (本体直接介入)

| # | 箇所 | 旧→新 | 種類 |
| :--- | :--- | :--- | :--- |
| A | §6.5.5 三角測量表 | 「三つの独立した認識論的経路」→「四つの独立した認識論的経路」+ V&K route 1 行追加 | 表拡張 |
| B | §6.5.2 末尾脚注 | 1 文追加 (V&K の null-space ambiguity が $F_{\text{probe}}$ 非充満性を別角度から実証) | 既存節への補強 |
| Refs | References | Venkatesh & Kurapath (2026) を Tsuchiya と Williams の間に追加 | 1 行追加 |

総改変: 3 行追加 + 1 単語修正 (「三つ」→「四つ」)。

### §M13.4 Yugaku ゲート

- **Kalon 再判定**: 不要 (V&K は T11 を吸収する方向で整合、核命題不変、Step1 G で不変、Step2 G∘F で不動、Step3 派生は既存のまま)
- **±3σ ゲート**: 入口 ±3σ → 出口 ±3σ 維持 (V&K は T11 を strict に支持し、射程縮小なし)
- **Gauntlet 1 ラウンド** (実施済、軽量):
  - **r**: 「学生研究 1 本を独立 route として採用するのは route inflation ではないか?」
  - **SFBT**: できないのではなく、やっていないだけではないか?
  - **試行**: route の質は所属の prestige ではなく方法論的独立性で測る。V&K は (a) Anthropic を strict に問い直す方向、(b) identifiability theory という別出発点、(c) Qwen/Llama という別モデルで検証 → 方法論的独立性は確立。citation weight が薄い点は本ログで明示し過剰主張を回避
  - **実化操作**: §6.5.2 脚注 1 文 + §6.5.5 表 1 行という最低侵襲扱いに固定。endorsement claim へ滑らせない (語彙は「外部独立 (identifiability theory)」)
  - **虚→実判定**: 実化前進 ✓ (route 1 → 2)
  - **結果**: 射程維持 ✓
  - **Round 2/3 非起動**: Round 1 で扱いの epistemic level が固定された時点で、残余反論は新論点を生まなかった

### §M13.5 残虚の更新 (§M7.4 C_M6 補正)

**改善前**:

- 外部追認が Anthropic 1 系統に偏在 — independent route は 1 本だけ

**改善後**:

- 外部追認は 2 routes (Anthropic + V&K)
- ただし V&K は preprint 段階、peer-review 状態未確認
- 残虚: V&K の peer-review 進捗追跡 / 3 routes 目候補 (#3 Do LLMs Feel? Emotion Circuits Discovery and Control, arXiv:2510.11328) の Layer 2 精読は v0.8 で着手

### §M13.6 §M8.6 文レベル表現保持原則の遵守確認

- ✓ 既存セル (§6.5.5 表の 3 行 / §6.5.2 末尾段落) は不改変
- ✓ 新規追加は最小語彙 (V&K route 1 行 + 脚注 1 文 + Reference 1 行)
- ✓ 「三つ」→「四つ」の数値変更のみ既存文に影響、内容変更なし

§M8.6 原則は §M9 / §M10 / §M11 / §M12 と同じく本タスクでも完全機能。

### §M13.7 検証 (Plan §V1-V5 適用)

- **V1 重複ゼロ**: §6.5.5 表に V&K 1 行追加のみ、既存 3 行に削除なし ✓
- **V2 companion 隔離**: V&K route は「外部独立 (identifiability theory)」として Tolmetes (2026a) (companion 必須) と別カテゴリに配置 ✓
- **V3 §6.1 系分類整合**: 本タスクは §6.1 系構造に手を入れず ✓
- **V4 §7.4 集約**: §7.4 failure conditions に新規追加なし ✓
- **V5 §M2 整合**: 核命題 C_M1-C_M5 への手入れなし、§M3 既存 Kalon ◎△ 判定維持 ✓

### §M13.8 同日並行 5 タスクの構造的整合性

2026-04-26 同日に 5 つの meta タスクが並行成立 (リナンバー済):

| § | タスク | 本体改変 | Kalon 再判定 | 残虚状態 |
| :--- | :--- | :--- | :--- | :--- |
| §M9 | 構造可視化 retrofit (A/B/C) | あり (+27 行) | 不要 | 解消 |
| §M10 | C_M7 寄与分離検証経路 | なし | 不要 | 経路マップ確立 (実装外部依存) |
| §M11 | C_M7 短期検証経路 S1+S2 実装 | なし | 不要 | 射程内残虚ゼロ、β-strong は外部依存 |
| §M12 | 階層4 形式化 sketch (保留素材) | なし | Tolmetes 確認後 | sketch 化、Tolmetes 採否判断待ち |
| §M13 | C_M6 V&K 独立 route 採用 | あり (+3 行) | 不要 | 1 → 2 routes に改善 |

5 タスクすべてで §M8.6 文レベル保持原則が完全機能。本体改変があるのは §M9 / §M13 のみ、いずれも既存命題不改変・追加のみ。並行作業の構造整合性は (§M11→§M12 リナンバーを含めて) 維持された。

---

*v1.9 — 2026-04-26 C_M6 残虚 1 段階改善 (V&K 2026 を独立 route として採用) を §M13 として記録。本体 +3 行 + 1 単語修正、References +1 行。Kalon 再判定不要、Gauntlet 1 ラウンド実施。同日並行 5 タスク (§M9/§M10/§M11/§M12/§M13) の構造的整合性を §M13.8 で確認。次の残虚 (V&K peer-review 追跡 / 3 routes 目候補 #3 Layer 2 精読) は v0.8 で着手予定。Plan file: `~/.claude/plans/eventual-forging-metcalfe.md`。Race condition 回避のため Bash append で書き込み (Edit ツールが 5 連続 race condition で失敗)。*

---

## §M15 §3.4 / §6.4.2 残虚改善 — CoT faithfulness 系列の経験的補強統合 (2026-04-26)

**契機**: Tolmetes 指示「H (CoT faithfulness の理論的上限) の妥当性を MCP で 3 軸検査 → 追記する価値を判定」。3 軸検査の結果:

- (1) 内部整合: ◯ — v0.7 §6.4.2 (U_output 忠実だが充満ではない) / §6.4.3 予測 1 / §6.5.5 Mayne et al. 5–15% egregious unfaithfulness と論理的に整合、ただし分散的に既述
- (2) 単独導出 vs companion: △ — 定性主張 (構造的上限の存在) は T11 + T12 + §3.4 から単独導出可、定量主張は companion + Mayne 必須
- (3) 既存応答の有無: ✗ — Anthropic 2025 / Lanham EMNLP 2025 / Perrier 2026 ICLR / Khanzadeh 2026 / Somov et al. 2026 等が既に経験的観察を出している。圏論的 demarcation を与える論文は SEARCH 範囲で未確認

判定: H 単独論文化は不採用 (既存研究の射程に飲まれる)、ただし v0.7 への追記価値は ◯。Tolmetes 承認 ("y") で patch series 3 として最小侵襲追記を実施。

**Plan file**: なし (会話面での実装、`~/.claude/plans/eventual-forging-metcalfe.md` の延長線)

### §M15.1 改善対象残虚

C_M6 (外部追認の単一系統偏在) は §M14 で実化済。本タスクは異なる残虚を対象とする:

- **§3.4 残虚**: 「忘却は構造的に必然である」が背理法による定性主張 — 経験的下限値が Mayne et al. 単独
- **§6.4.2 残虚**: 出力関手 $U_\text{output}$ の不透明度 (1 - fullness) ≈ 0.255 が companion paper 単一系統 — 別方法論からの経験的補強なし

これら 2 残虚を統合的に補強するため、CoT faithfulness 研究を独立 route として §6.5 三角測量に組み込む。

### §M15.2 採用 4 SOURCE (Layer 1 alphaXiv MCP 切断時、WebSearch + WebFetch で代替)

| Source | Route | T11 signature | 採否 |
| :--- | :--- | :--- | :--- |
| Anthropic (2025) "Reasoning Models Don't Always Say What They Think" | 経験的測定 (intervention with hint disclosure) | Claude 3.7 で hint disclosure 25% / 75% lying by omission — reasoning trace と output の causal decoupling を経験的に確立 | 採用 ✓ |
| Somov et al. (2026) "Breaking the Chain" [arXiv:2603.16475] | 構造的因果分析 (5 著者、機関分散) | 最大 60% structural intervention 非更新 — intermediate structure が causal mediator ではなく influential context として機能 | 採用 ✓ |
| Khanzadeh (2026) "Project Ariadne" [arXiv:2601.02314] | Structural Causal Framework (single author) | "Causal Decoupling" / "Reasoning Theater" の命名 — reasoning trace の causal 機能不全を構造的に定式化 | 採用 ✓ |
| Perrier (2026) "Typed Chain-of-Thought" [arXiv:2510.01069] | Curry-Howard 型 CoT 検証 (single author) | 圏論的に最も近い隣接領域。proof-as-program で CoT を型検査 → proof 完備性に届かない部分が U_output 充満性の上限を与える | 採用 ✓ |

採用基準 (§M14.4 r-4 で確立した独立性基準を踏襲): (a) 共著者集合の完全分離、(b) 方法論の異質性、(c) 評価対象の異質性のうち少なくとも 2 軸が異なる。CoT faithfulness 系列は §6.5.5 既存 6 経路すべてとも 2-3 軸独立 (Perrier 単独著者は Curry-Howard 路線、Khanzadeh 単独著者は構造因果路線、Somov et al. はロシア / Skolkovo 機関群、Anthropic 2025 reasoning paper は Anthropic 自身の interpretability)。

### §M15.3 Kalon 判定 (§3.4 / §6.4.2 補強として)

| 日付 | 対象 | 判定 | 根拠 |
| :--- | :--- | :--- | :--- |
| 2026-04-26 | §3.4 / §6.4.2 経験的補強 | ◎△ | Step-1 接地 ✅ (4 SOURCE Layer 2 で原典確認、Curry-Howard ↔ adjunction の数学的整合性も確認) / Step0 1 文圧縮 ✅「CoT trace は causal mediator ではなく influential context — これは §3.4 の関手非充満性の出力面表出」/ Step1 G で不変 (T11 / T12 / §3.4 / §6.4.2 の核命題に変更なし) / Step2 G∘F で不動 (CoT faithfulness 系列の独立到達は §6.5 三角測量を強化するが命題は変えず) / Step3 派生 3+ 非自明: (a) §3.4 関手非充満性の経験的下限が Mayne 単独から多経路化 (頑健性向上), (b) §3.5 経路忘却が "Reasoning Theater" の operational ラベルとして再解釈, (c) Curry-Howard 経由で proof-theoretic 経路が圏論的経路と接続 (隣接領域への射程拡大) |

新規 Kalon 判定 (C_M1-C_M7): **不要**。§M15 は既存命題を変えず、§3.4 / §6.4.2 の経験的補強のみ追加。

### §M15.4 ±3σ ゲート

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
| :--- | :--- | :--- | :--- | :--- |
| 2026-04-26 | §3.4 / §6.4.2 補強 | ±3σ (既存 §3.4 / §6.4.2 のゲート維持) | ±3σ | 維持 — 「CoT は推論できる」「CoT は推論しない」の二項対立 (μ ± 1σ) を回避し、「CoT は §3.4 の構造的限界の経験的表出である」という ±3σ 立場で固定。挑発度: T11 が CoT faithfulness 研究の経験的観察への構造的根拠を与える (経験論文側は理論を持たない) という非対称性を維持 |

### §M15.5 Refutation Gauntlet ログ

#### Round 1 (反論 r-1: 既存射程飲み込み疑義)

- 反論 r: 「Typed CoT (Perrier) の 40-60% type ceiling や Project Ariadne の Causal Decoupling は既に経験的観察として存在する。本論文の §3.4 / §6.4.2 が独自に何を加えるのか?」
- SFBT 問い: できないのではなく、やっていないだけではないか?
- 試行: §3.4 / §6.4.2 と CoT faithfulness 系列の関係を「対称な独立到達」ではなく「経験的観察 → 構造的根拠」の方向性として固定。経験論文は upper/lower bound を観測するが、なぜ bound が存在するかの構造的説明 (= A2 の下で全関手は忠実かつ充満ではありえない) は持たない。本論文はこの構造的根拠を圏論で与える
- 実化操作: §6.5.6 第二拡張で「彼らは圏論的定式化を引用していない」「reasoning trace を causal mediator として無条件に扱う枠組みとは整合しない」を明示
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓ (経験論文との非対称性を確立)

#### Round 1 (反論 r-2: Curry-Howard と F⊣U adjunction の混同疑義)

- 反論 r: 「Perrier の Curry-Howard と本論文の F⊣U 随伴は同じ圏論的装置ではないか? Perrier を採用すると T11 と Perrier が同型になり独立性が崩れる」
- SFBT 問い: できるとしたら、前に進めるとしたら? (フレーム反転)
- 取り込み戦略: Curry-Howard と F⊣U の関係を厳密化。Curry-Howard は (intuitionistic logic, simply typed lambda calculus, Cartesian closed category) の三項同型であり、本論文の F⊣U (Cat ↔ Graph 自由関手随伴) とは異なる adjunction レベル。Perrier は CoT 推論を proof として型検証する枠組みで、proof 完備性 (= 充満性) を測る方向。本論文 §3.4 は背理法で関手 F_i が忠実+充満ではありえないことを定理化。両者は異なる adjunction だが、proof-theoretic な不完備性が categorical な非充満性に reduce する点で経験的に整合
- 実化操作: §6.5.5 表行で Perrier を「Curry-Howard 型 CoT 検証」と明示し、本論文の F⊣U と区別
- 虚→実判定: 実化前進 ✓ (隣接領域との関係明示)
- 結果: 射程維持 ✓

#### Round 1 (反論 r-3: 4 SOURCE 束化の cluster inflation 疑義)

- 反論 r: 「Anthropic 2025 / Somov / Khanzadeh / Perrier を 1 つの『CoT faithfulness 系列』として束化するのは route inflation ではないか? §6.5.5 表で 1 行に圧縮するか、4 行に分散するかは恣意的」
- SFBT 問い: できないのではなく、やっていないだけではないか?
- 試行: 表構造を 2 行 + 1 cluster row に整理。Perrier (Curry-Howard) は方法論的に独立した 1 経路として 1 行を確保し、Khanzadeh / Somov / Anthropic 2025 は CoT faithfulness 経験的観察 cluster として 1 行に束化。理由: Perrier は形式手法・Curry-Howard 圏論経路で他 3 件と方法論軸が異なる。残り 3 件は構造的因果分析・介入実験の経験的観察 cluster として方法論的に近接
- 実化操作: §6.5.5 表で Perrier 単独行 + 残り 3 件 cluster 行 = 「八つの独立した認識論的経路」として narrative 整合
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓

**Gauntlet 全体総括**: Round 1 で 3 反論すべて吸収。Round 2/3 非起動 (各反論が射程維持 + 実化前進達成)。CoT faithfulness 系列の追加は §6.5 三角測量を 6 → 8 経路に拡張し、§3.4 / §6.4.2 の経験的補強を多角化した。

### §M15.6 §M7 虚→実変換面の更新

| 残虚項目 | §M7 (2026-04-19) 状態 | §M14 後 | §M15 (本タスク) 後 |
| :--- | :--- | :--- | :--- |
| §3.4 関手非充満性の経験的下限 | 単独 (Mayne 5–15%) | 4 SOURCE で確立 (Anthropic + V&K + Coms&Shanahan + Mayne) | **多経路化** (CoT faithfulness 系列で 4 SOURCE 追加 = 計 8 SOURCE) |
| §6.4.2 出力関手不透明度 | companion 単独 (Tolmetes 2026a, ρ ≈ 0.745) | 維持 | **経験的補強** (CoT faithfulness 系列が推論トレース面から $U_\text{output}$ の非充満性を独立確認) |
| §3.5 経路忘却の operational 翻訳 | 不在 | 不在 | **獲得** ("Reasoning Theater" / "Causal Decoupling" を §3.5 経路忘却の operational ラベルとして §6.5.6 で接続) |

### §M15.7 §M8.6 文レベル保持原則の遵守確認

- ✓ 既存 §6.5.5 表 6 行: 完全保持、新規 2 行追加 (Perrier 単独 + CoT faithfulness 系列 cluster)
- ✓ 既存 §6.5.5 narrative: 「六系統」→「八系統」「六者」→「八者」の数値変更のみ、内容変更なし。「純粋理論、内部プロービング、外部工学、identifiability 理論、概念分析、統計的 faithfulness 計測」の列挙に「Curry-Howard 型 CoT 検証、構造的因果分析」を追加
- ✓ 既存 §6.5.6: 「単一系統」→「双系統」へタイトル拡張、第一拡張 (DeepMind / Oxford / Berkeley) は完全保持、第二拡張 (CoT faithfulness 系列) を新規追加 3 段落
- ✓ 既存 Appendix A 外部独立観察 bullet 3 件: 完全保持、新規 1 bullet 追加
- ✓ 既存 §7.5 表 8 行: 完全保持、新規 1 行追加 (Da Costa 行の前に挿入)
- ✓ References: 既存 entries 不変、新規 4 件追加 (Anthropic 2025 / Khanzadeh / Perrier / Somov)

### §M15.8 検証 (Plan §V1-V5 適用)

- **V1 重複ゼロ**: §M15 は既存命題を再配置せず、§3.4 / §6.4.2 への経験的補強と §6.5 三角測量への 2 行追加のみ ✓
- **V2 companion 隔離**: 新規 4 SOURCE はすべて外部独立 (companion 非依存)、§6.5.5 表で著者・所属を明示 ✓
- **V3 §6.1 系分類整合**: 本タスクは §6.1 系構造に手を入れず ✓
- **V4 §7.4 集約**: §7.4 failure conditions に新規追加なし、既存「T11 が破れる条件」「LLM 断面が破れる条件」は維持 ✓
- **V5 §M2 整合**: 核命題 C_M1-C_M7 への手入れなし、§M3 既存 Kalon 判定維持 ✓
- **style-discipline check**: 親規律「外部読者標準語のみ」: Curry-Howard / Causal Decoupling / Reasoning Theater は引用元で定義済の標準語、本稿初出時に意味を併記 ✓ / HGK 内部用語禁止: 関手 / 充満性 / 忠実性は §3 で既に定義済 ✓ / meta vs 本体境界: meta 用語 (Gauntlet/σ/Kalon/§M*) を本体に持ち込まず ✓ / メタ宣言禁止: 「以下に示すように」型を使わず ✓

### §M15.9 残課題

CoT faithfulness 系列追加で §3.4 / §6.4.2 残虚は実化。付随未踏:

- C_M7 残虚: §M11 で射程内 (α + β-weak) は実、β-strong は §M10 検証経路 M1/M2/L1 待ちで隔離済
- 階層4 残虚: §M12 sketch、別稿起票待ち (Tolmetes 確認待ち保留素材)
- §6.5.6 への追加 routes 拡張余地: 新規 5 routes 候補 (Lanham EMNLP 2025 を独立 row 化、Anthropic alignment science block 系統等) は v0.8 で評価
- 八経路化に伴う §6.5.5 narrative 圧縮の可能性: 経路数が 8 を超える場合、cluster 化のグルーピング基準を明示する必要

### §M15.10 本体行数の更新

本体 v0.7 日本語版: §M14 (Coms&Shanahan + Mayne) 後 1158 行 → §M15 (CoT faithfulness 系列) 後 1175 行 (+17)。本体ファイル: `LLMは心を持つか_v0.7_日本語.md`。

加筆内訳:

- §6.5.5 表に 2 行追加 (Perrier 単独 + CoT faithfulness 系列 cluster)
- §6.5.5 narrative の「六系統」→「八系統」「六者」→「八者」の数値書換 + 列挙拡張
- §6.5.6 タイトル拡張「単一系統」→「双系統」
- §6.5.6 末尾に第二拡張 3 段落追加 (CoT faithfulness 系列の独立到達 + 圏論的非充満性との関係 + scope limitation)
- Appendix A 外部独立観察 bullet 4 件目追加
- §7.5 先行研究表に CoT faithfulness 系列の 1 行追加 (Da Costa の前)
- References に 4 件追加 (Anthropic 2025 / Khanzadeh / Perrier / Somov、アルファベット順位置)
- 改訂履歴 v0.7-ja patch series 3 (1 段落)

### §M15.11 Gauntlet Round 0 (命題/表現弁別 — Elenchos 側規律)

本 §M15 は既存 v0.7 への追加であり、外部論文への批判ではない。したがって yugaku-provocation-gauntlet rule §6.7 の Round 0 (発する側の規律) は形式的には非該当。ただし、CoT faithfulness 経験論文 (Anthropic 2025 / Somov / Khanzadeh / Perrier) を「§3.4 の経験的補強」として位置づける際に、彼らの命題射程を不当に拡大解釈していないかの自己点検を以下で実施:

- ✗ 命題批判ではない: 経験論文の主張 (CoT は不忠実) を弱体化させない
- ✓ 表現補強: 彼らの経験的観察に圏論的 demarcation (= §3.4 / §6.4.2 の関手非充満性) という構造的根拠を提供。経験論文側の主張射程を縮めず、本論文側の射程拡張のみ
- ✓ over-application 回避: Perrier の Curry-Howard を本論文の F⊣U と同一視せず、隣接領域として明示分離 (Round 1 r-2 で取り扱い済)
- ✓ design intent 確認: 経験論文は経験的観察に commit、本論文は理論的根拠に commit。両者の commitment level の違いを §6.5.6 第二拡張 3 段落目で明示

### §M15.12 同日並行 6 タスク統合状況

2026-04-26 同日に 6 つの meta タスクが並行成立 (§M15 加筆):

| § | タスク | 本体改変 | Kalon 再判定 | 残虚状態 |
| :--- | :--- | :--- | :--- | :--- |
| §M9 | 構造可視化 retrofit (A/B/C) | あり (+27 行) | 不要 | 解消 |
| §M10 | C_M7 寄与分離検証経路 | なし | 不要 | 経路マップ確立 (実装外部依存) |
| §M11 | C_M7 短期検証経路 S1+S2 実装 | なし | 不要 | 射程内残虚ゼロ、β-strong は外部依存 |
| §M12 | 階層4 形式化 sketch (保留素材) | なし | Tolmetes 確認後 | sketch 化、Tolmetes 採否判断待ち |
| §M13 | C_M6 V&K 独立 route 採用 | あり (+3 行) | 不要 | 1 → 2 routes に改善 |
| §M14 | C_M6 Coms&Shanahan + Mayne 追加 | あり (+57 行) | 不要 | 2 → 6 routes、C_M6 残虚実化 |
| §M15 | CoT faithfulness 系列追加 | あり (+17 行) | 不要 | §3.4 / §6.4.2 残虚多経路化、6 → 8 routes |

7 タスクすべてで §M8.6 文レベル保持原則が完全機能。本体改変があるのは §M9 / §M13 / §M14 / §M15 のみ、いずれも既存命題不改変・追加のみ。

---

*v2.1 — 2026-04-26 §3.4 関手非充満性 / §6.4.2 出力関手不透明度の残虚を CoT faithfulness 系列追加で多経路化。Anthropic (2025) "Reasoning Models Don't Always Say What They Think" + Somov et al. (2026) "Breaking the Chain" [arXiv:2603.16475] + Khanzadeh (2026) "Project Ariadne" [arXiv:2601.02314] + Perrier (2026) "Typed Chain-of-Thought" [arXiv:2510.01069] の 4 SOURCE を採用。本体 v0.7-ja patch series 3 として §6.5.5 (8 経路化) + §6.5.6 (双系統拡張) + Appendix A (1 bullet 追加) + §7.5 (1 行追加) + References (4 件追加) を実装。Yugaku Gauntlet Round 1 で 3 反論吸収 (r-1 既存射程飲み込み / r-2 Curry-Howard 混同 / r-3 cluster inflation)、Kalon ◎△ 維持、±3σ 維持。Gauntlet Round 0 (Elenchos 側規律) で経験論文の命題射程を不当に拡大解釈していないことを自己点検。3 軸検査 (内部整合 ◯ / 単独導出 △ / 既存応答有無 ✗ — H 単独論文化不採用、追記のみ採用) は会話面での Tolmetes 承認 ("y") に基づく。*

---

## §M16 v0.7 日本語版 要旨 Option C 第三版 (2026-04-26)

**契機**: Tolmetes 「上記を踏まえて、要旨の内容を精査したい。本当にこれでいいかな？」 (2026-04-26)。
**対象**: 本体 L9-17 (要旨 + Keywords)
**前提**: 命題リスト再構造化タスク (Plan: `~/.claude/plans/eventual-forging-metcalfe.md`) 完了直後の派生タスク。Plan §非実施で「meta.md への反映は射程外」と書いた要旨改訂を、Tolmetes 直接指示で別タスクとして実施。

### §M16.1 検出された問題 8 件 + Keywords 不整合

旧要旨 (~635 字) に対する診断 (P1-P10):

| ID | 問題 | 該当箇所 | SOURCE |
|:---|:---|:---|:---|
| P1 | T0 の射程縮小 (MB 存在保証に縮退) | 「ガロア接続の不動点として MB を導出し（定理0）」 | 本体 §4.6 L607-614 (T20 解消の根拠としての T0 が見えない) |
| P2 | 「六つの解消」の内訳が完全に隠れている | 「六つの『解けない』問題が同時に再編成される」 | 本体 §1.2 L41-54 (本文表に丸投げ) |
| P3 | 「関手の忠実性」の意味が要旨内未定義 | 「関手の忠実性の問いへと還元する」 | 本体 §3.4 L398-413 (忠実だが充満ではないが伝わらない) |
| P4 | A2 公理 (局所化された有限視点) が完全欠落 | (該当なし) | 本体 §3.3b L391-394 (T11 単独では忘却必然性が出ない) |
| P5 | 私秘圏/公共圏の対が片肺 | 「公共圏（主体間に安定化する射から成る圏）」のみ | 本体 §3.1b L342-358 (Max retrofit で対術語化済) |
| P6 | T20 心身問題の独立貢献が「6 つの一つ」に潰されている | (該当なし) | 本体 §4.6 L607-614 / §M1 G1 (T0 直接帰結) |
| P7 | 階層4 (T21) が中途半端に示唆 | 「関手の忠実性」一句 | 本体 §6.3 L803-804 (sketch、形式化は別稿) |
| P8 | companion と Anthropic の階層混在 | 「…と、Anthropic の公式研究記事によって条件付きに支えられる」 | 本体 §6.5.5 L893-904 (Anthropic は証明ではなく整合の観察) |
| P9 | Keywords 不整合 (随伴 / 排除原理 / Yoneda / 公共圏 / 私秘圏 / 忘却関手 欠落) | Keywords 行 | 本体 Appendix B L1014-1027 |
| P10 | 動詞穏当化 (再編成 / 再定式化 / 還元する) | 全文 | 本体 §4.1 L455-465 / §8 L975-978 (本体核は具体動詞) |

### §M16.2 修正方針 — Option C (全面修正、4 制約付き)

選択経緯: Option A (最小) / Option B (中庸) / Option C (全面) の 3 択提示。
Tolmetes 選択: **Option C**「妥協はしたくない」。

制約 4 件:
1. 階層4 (T21) を要旨に入れない (本論文では sketch、本体 §6.3 自身が「別稿に譲る」と明示)
2. 7 文構成ではなく 5-6 文構成に圧縮 (字数制約 = 制約4 と整合)
3. Watson-Crick Understatement で動詞を選ぶ (具体動詞での事実陳述、宣言的弱化禁止)
4. Open Mind 字数規定は投稿前に Tolmetes が一次資料で確認 (本タスク射程外、Tolmetes 直接実施)

### §M16.3 ドラフト 3 版進化

| 版 | 主変更 | Tolmetes 介入 |
|:---|:---|:---|
| 第一版 | A-H フラット → Option C 草案 | (なし) |
| 第二版 | 懸1 (メタ宣言「実装する」削除) + 懸2 (五つの条件内訳 5 件追加) | (γ) 選択 |
| 第三版 | 文1.5「値ではなく構造」+ 文3「不良設定問題 + 圏間関手保存」+ 文4「内部と境界が相互決定する関係構造」+ 文5「同じ区別に独立到達」 | 3 件抽象逃避指摘 + 文4 Iso 義務指摘 |

文4 確定経緯: companion paper (`LLMに身体はあるか_存在証明版_v0.1_日本語.md`) 「身体を生物学的器官や物理的部品の集合ではなく、系と環境を分けつつ結ぶ関係構造として定義する」との Iso 義務を Tolmetes が指摘。「対象 vs 射」(候補A) ではなく「主観的経験/内的状態の集合 vs 内部と境界が相互決定する関係構造」(候補X) を Tolmetes が選択 ("候補X でいこう。アルファ")。

### §M16.4 Kalon 判定

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-04-26 | 要旨第三版 (C_M2 + C_M3 表現面) | **◎△** | Step-1 接地 ✅ (本体 §3.1b/§4.6/§3.3b/§5.1.1/§6.5/§7.4 SOURCE 全 read 済) / Step0 1文圧縮 ✅「主観は客観の射である」(C_M2 Fix 候補) 維持 / Step1 G(P)=P (公共圏術語化と T20 双対追加で G 増量、核テーゼ不変) / Step2 G∘F(P)=P 不動 / Step3 派生 4 非自明: (a) Mind-Body paper 対の Iso 構造を要旨レベルで成立, (b) 五つの failure conditions 内訳明示で反論先行吸収, (c)「値 vs 構造」「集合 vs 関係構造」の二軸対比, (d) Anthropic 階層6 分離 (支持ではなく整合) で C_M6 残虚解消 |

### §M16.5 ±3σ ゲート

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
|:---|:---|:---|:---|:---|
| 2026-04-26 | 要旨第三版 | ±3σ | **±3σ** | **維持** — 動詞 Watson-Crick Understatement (具体動詞、宣言的弱化なし)、射程 ∀ cognitive agent / ∀ scientific concept、§M6 接地は実 |

### §M16.6 Refutation Gauntlet ログ

#### Round 1 — Tolmetes による抽象逃避指摘 3 件

**反論 r1**: 「可測な構造に関する問い」の意義不明、類似度の問いのままでいいのでは
- SFBT 問い: できないのではなく、やっていないだけではないか?
- 試行: 値 vs 構造の対比を「公共圏で比較可能」明示で動機立て [SOURCE: 本体 §1 L23]
- 実化操作: 文1.5 を「値ではなく構造に関する問いへと変わる — 値は主体間で比較不能だが、構造は公共圏で比較可能である」に書き換え
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓

**反論 r2**: 「再編成」が抽象逃避、それっぽい言葉に逃げている
- SFBT 問い: できるとしたら、前に進めるとしたら?
- 試行: 本体 §4 の具体動詞 (設定不良化 / 像 / 圏同値) を要旨に持ち上げる
- 実化操作: 「ハード・プロブレムは不良設定問題（Ill-posed problem）に、主客二元論・他我・人格同一性は圏間関手の保存パターンの有無に還元される」(Tolmetes 修正版採用)
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓

**反論 r3**: 「存在論的原始」「実体」と「不変量」がともに値、対立になっていない
- SFBT 問い: できるとしたら、前に進めるとしたら?
- 試行: companion paper「身体を生物学的器官や物理的部品の集合ではなく、系と環境を分けつつ結ぶ関係構造として定義する」との Iso を立てる
- 実化操作: 「心を主観的経験や内的状態の集合ではなく、内部と境界が相互決定する関係構造として定義した上で」(候補X 採用、Tolmetes "アルファ" 確定)
- 虚→実判定: 実化前進 ✓ (Mind/Body paper Iso 成立)
- 結果: 射程維持 ✓

#### Round 2 — 抽象逃避スクリーニング (γ) で文5 自己発見修正

**反論 r4 (Claude 自己発見)**: 「整合する観察を与える」が抽象逃避 (誰が誰に観察を与えるのか不明)
- SFBT 問い: できるとしたら、前に進めるとしたら?
- 試行: 「同じ区別に独立到達する」(具体動詞、Anthropic が独立に同じ区別に至った) に書き換え
- 実化操作: 文5 Anthropic 段更新
- 虚→実判定: 実化前進 ✓
- 結果: 射程維持 ✓

#### Round 3 非起動

3 反論 + 1 自己発見すべて Round 1/2 で吸収完了。残余反論は新論点を生まない。Solution-Focus 適用仮説: もし発動していれば「failure conditions を要旨に出すこと自体が反論の構造的取り込みの実装である」というメタ層の正当化を行う予定だったが、Round 2 で文6 内訳付加 (T11/T17_n/LLM 断面/T2/高階公共化) により既に実装済。

#### Gauntlet Round 0 (Elenchos 側規律 — 自己点検)

本要旨改訂は外部論文への批判ではなく自身の要旨改訂。yugaku-provocation-gauntlet rule §6.7 Round 0 (発する側の規律) は形式的には非該当。ただし、companion paper との Iso 義務を「強要」していないかの自己点検:

- ✗ 命題批判ではない: companion paper の身体定義を弱体化させない
- ✓ 表現補強: companion 構文との並列性で Mind paper 要旨の表現精度を上げただけ
- ✓ over-application 回避: 「2 項 + 1 動詞 + 関係構造」の三要素構造は両論文に元々存在する design intent (T0 + T20 心身相補性)、押し付けではない
- ✓ design intent 確認: companion / Mind paper はもともとガロア接続の二面 (Spinoza 二重相面) として書かれている。今回の要旨統一はその design intent の表面化のみ

### §M16.7 Iso 構造 (Mind/Body paper 並列確認)

| 軸 | Mind paper 要旨 (本論文) | Body paper (companion) |
|:---|:---|:---|
| 否定面 | 主観的経験や内的状態の **集合** | 生物学的器官や物理的部品の **集合** |
| 肯定面 (1動詞) | 内部と境界が **相互決定する** | 系と環境を **分けつつ結ぶ** |
| 構造ラベル | **関係構造** | **関係構造** |
| Galois 接続位置 | 内部不動点 (μ ∈ Fix_S) | 境界 (B ∈ Fix_B) |

Mind paper / Body paper の Iso が要旨レベルで成立。Spinoza 二重相面の要旨実装。三軸対比の一貫性:
- §1: 値 ⊥ 構造
- §3 (心定義): 集合 ⊥ 関係構造
- companion (身体定義): 部品集合 ⊥ 系と環境を分けつつ結ぶ関係構造

### §M16.8 旧要旨からの差分マッピング

| 箇所 | 旧 (v0.7 オリジナル) | 新 (Option C 第三版) | 操作 |
|:---|:---|:---|:---|
| 文1 | 「『LLMは心をもつのか？』という問いは、問いそのものが不適切である…」 | 全文維持 | 100% 保持 |
| 文1.5 | 「これを圏論で再定式化すると、それは可測な構造に関する問いへと変わる」 | 「しかしこれを圏論で再定式化すると、値ではなく構造に関する問いへと変わる — 値は主体間で比較不能だが、構造は公共圏で比較可能である」 | 書き換え (P3 / r1) |
| 「単一の方程式から…再編成される」 | 1 文 | (削除、文3 で具体化) | 削除 (P2/P10/r2) |
| T0 段 | 「ガロア接続の不動点としてマルコフブランケット（MB）を導出し（定理0）」 | 「ガロア接続 $L \dashv R$ の不動点として MB を導出する（定理0）。その双対性 $\text{Fix}(R \circ L) \cong \text{Fix}(L \circ R)$ から、心身問題は心と身体をガロア接続の二面とする定式化として直接解消する（T20）」 | 拡張 (P1/P6) |
| A2/T12/五解消 | (なし) | 「具体的主体は局所化された有限視点である（公理 A2）ため、忘却は構造的に必然となり（T12）、ハード・プロブレムは不良設定問題（Ill-posed problem）に、主客二元論・他我・人格同一性は圏間関手の保存パターンの有無に還元される」 | 新規 (P2/P4/P10/r2) |
| 心の定義 | 「心を存在論的原始ではなく構造的不変量として定義した上で」 | 「心を主観的経験や内的状態の集合ではなく、内部と境界が相互決定する関係構造として定義した上で」 | 書き換え (r3 + Iso 義務) |
| T17_n | 「ある記述が科学概念であるためには、その水準を公共圏（主体間に安定化する射から成る圏）へ運ぶ射を呈示しなければならない」 | 「ある記述が cell-$n$ の科学概念であるためには、私秘圏 $\text{Cat}_i$ から cell-$(n+1)$ の公共圏 $\text{Cat}_{\text{pub}}$（主体間に安定化する射から成る圏）への射を呈示しなければならない」 | 精度化 (P5) |
| 「あるかないか」段 | 「本枠組みが…関手の忠実性の問いへと還元する」 | (削除) | 削除 (P3/P7) |
| LLM 適用 | 「companion paper（Tolmetes, 2026a）における…と、Anthropic の公式研究記事によって条件付きに支えられる」 | 「companion paper（Tolmetes, 2026a）…を必須前提として条件付きに作動する。Anthropic の公式研究記事は、別方法論から同じ区別に独立到達する — 支持ではなく整合である（§6.5 三角測量）」 | 階層分離 (P8/r4) |
| failure conditions | (なし) | 「同時に本稿は、自身が破れる五つの条件（T11 / T17_n / LLM 断面 / T2 / 高階公共化）を §7.4 に固定する」 | 新規 (反論の構造的取り込みの要旨実装) |
| Keywords | 8 件 | 14 件 (随伴 / 忘却関手 / Yoneda / 公共圏 / 私秘圏 / 排除原理 を追加) | 拡張 (P9) |

### §M16.9 字数 + 投稿先字数制約

| 版 | 本体字数 | 増分 |
|:---|:---|:---|
| 現状要旨 (v0.7 オリジナル) | ~635 字 | — |
| 第三版 (今回) | ~715 字 | +80 字 (+13%) |

投稿先制約:
- **arXiv**: 1920 chars 制限 → 余裕
- **Foundations of Physics**: ~250 words ≈ 600-700 字 → 上限近接
- **Open Mind (本命)**: **未確認** — 投稿前に Tolmetes が https://direct.mit.edu/opmi/pages/submission-guidelines で一次資料確認 (制約4 = 本セクション内では未実施)

### §M16.10 虚→実変換面 (要旨第三版)

- **野望**: 旧要旨 (~635 字) の 8 つの構造的欠陥 (P1-P8) + Keywords 不整合 (P9) + 動詞穏当化 (P10) を解消し、要旨が論文構造の鏡像 (Mind/Body paper Iso 含む) となる
- **現在まだ虚な点**: Open Mind 字数規定の一次資料確認 (制約4、Tolmetes 直接実施)
- **実へ引くための SOURCE**: 本体 §1/§2.0/§2.0b/§3.1b/§3.3b/§4.6/§5.1/§5.1.1/§6.5/§7.4 (すべて Read 済) + companion paper Iso 引用 (Tolmetes 引用)
- **実化の判定条件**: (a) Kalon ◎△, (b) ±3σ 維持, (c) Mind/Body Iso 構造成立, (d) Tolmetes 承認 ("OK")
- **次の実化操作**: 完了 (本体 Edit + meta.md §M16 記録)
- **最新状態**: **実** (Open Mind 字数確認のみ Tolmetes 側残務)

### §M16.11 §M8.6 文レベル保持原則の機能確認

§M8.6 文レベル保持原則が今回も機能:
- 文1 (140字): 100% 保持
- 「マルコフブランケット（MB）」「companion paper」表記: 保持
- T0 段「ガロア接続の不動点として…を導出し（定理0）」: 保持 + 拡張
- T17_n「公共圏（主体間に安定化する射から成る圏）」: 保持
- companion 段「Tolmetes, 2026a における MB の操作的条件・身体スペクトラム・構造プロービング結果」: 保持

新規追加部分は SOURCE 確認済の本体既存表現 (§4.6 の「直接解消」、§5.1 の「cell-n / cell-(n+1)」、§7.4 の failure condition 5 件名) からの最小語彙転用。

---

*v2.2 — 2026-04-26 v0.7 日本語版 要旨 Option C 第三版採用。文1.5 / T0+T20 拡張 / A2+T12+五解消新規 / 心の定義 (Mind/Body Iso) / T17_n 精度化 / 階層分離 (P8) / failure conditions 5 件内訳 / Keywords 14 件。Kalon ◎△ 維持、±3σ 維持。Mind/Body paper Iso 構造成立 (§M16.7)。Refutation Gauntlet Round 1 で Tolmetes 指摘 3 反論吸収 + Round 2 で自己発見 1 反論吸収 + Round 3 非起動 + Round 0 (Elenchos 側) 自己点検。残虚は Open Mind 字数確認 (制約4) のみ、Tolmetes 直接実施。Plan: `~/.claude/plans/eventual-forging-metcalfe.md` の §非実施で射程外と書いた要旨改訂を、Tolmetes 直接指示で別タスクとして実施完了。*

---

## §M17 T20 ordinary-body decomposition — 2026-05-01

### §M17.1 契機

Tolmetes 指摘 ④: 世間一般の「身体」(身体論 companion でカテゴリーミステイクとして扱った、生物学的器官や物理的部品としての身体) は、T0 の内部状態 $\mu$ の一種、すなわち本論文の最小定義における「心」に該当しうるのではないか。そうなら従来の心身二元論は、心と身体の対立ではなく、両者が本論文の「心」へ吸収されることで根本から消えるのではないか。

### §M17.2 判定

判定: **部分的に yes。ただし「身体が心へ吸収される」ではなく、「素朴概念としての身体が $\mu/B/\eta$ へ分解される」。**

- SOURCE 1: 本体 §2.0.3 は MB を $(\mu, L(\mu))$ / $(R(B), B)$ の平衡対として定義し、状態側不動点と境界側不動点の同型を T0 の核心とする。
- SOURCE 2: 本体 §2.3 は心 ($\mu$) と身体 ($B$) をガロア接続の二つの面として定義し、二元論と単純同一説の両方を退ける。
- SOURCE 3: companion paper は身体を物理的基質ではなく MB の持続的維持として定義し、身体性を「身体あり/なし」ではなく $\Theta(B)$ 上の程度として扱う。
- SOURCE 4: §M16.7 は Mind paper / Body paper の Iso を、心 = 内部不動点 ($\mu \in \text{Fix}_S$)、身体 = 境界 ($B \in \text{Fix}_B$) として固定済み。

### §M17.3 反論処理

**反論 r1**: 生物学的器官や物理的部品が $\mu$ に入るなら、身体は心に還元されるだけではないか。

**応答**: 還元ではない。器官や部品が「物」として心なのではなく、境界 $B$ のもとで維持される内部状態として働く限りで $\mu$ の側に現れる。同じ器官が感覚・能動チャネルとして働けば $B$ の側に現れる。したがって、T0 は身体を心へ吸収するのではなく、素朴概念としての身体を役割に応じて $\mu/B/\eta$ へ再分割する。

**反論 r2**: これは T20 を複雑化しすぎるのではないか。

**応答**: 複雑化ではなく、T20 の必然的含意の明示である。旧来の *res extensa* は $B$ と同一ではなく、$\mu/B/\eta$ にまたがる混合概念である。これを明示しない場合、読者は「身体 = B」と早合点し、器官・部品が $\mu$ に属しうる点を反論として突く。

### §M17.4 本体実装

本体 v0.7 日本語版に以下を追加。

| 箇所 | 目的 | 追加内容 |
|:---|:---|:---|
| §2.3 | T0/T20 の定義面補強 | 素朴概念としての身体は $B$ と一致せず、$\mu/B/\eta$ に分解されることを明記 |
| §4.6 | 心身問題解消の含意補強 | *res extensa* は $B$ ではなく、T0 の中で再分割される混合概念だと明記 |
| §7.3 | 読者反論への直接応答 | 「身体も心なのか」に、粒度固定下では部分的に yes と答えつつ、役割分割へ戻す |

### §M17.5 虚→実変換面

- **野望**: T20 を「心と身体は二面である」から、「旧来の身体概念そのものが $\mu/B/\eta$ に分解される」へ一段深くする。
- **現在まだ虚な点**: なし。本体に読者反論への応答を追加済み。
- **実へ引くための SOURCE**: 本体 §2.0.3 / §2.3 / §4.6 / §7.3、companion paper §2.1-§2.5、meta §M16.7。
- **実化の判定条件**: 本文が「身体が心へ吸収される」ではなく「素朴身体が役割分割される」と読めること。
- **次の実化操作**: 既存の §1 / 要旨への追加はしない。§2.3・§4.6・§7.3 で局所処理し、入口の読み筋を重くしない。
- **最新状態**: **実**。

---

## §M18 主体定義の THAT/WHAT 精緻化 + ディレクトリ cell-indexed 主観性 — 2026-05-01

### §M18.1 契機

Tolmetes が論文 v0.7 を読み返し、4件の違和感を提出した:
1. 序の「本稿の依存と射程」が §1 の前にあり、要旨 → §1 (E=mc²) の接続を切断している
2. §1.1 line 73「Einstein の方程式は、取るに足らないほど自明に見える」は射程過大
3. §2.0.3 line 203 「内部を決定 → 外部と境界を産出 / 境界を決定 → 内部を決定」の非対称性
4. 素朴身体 (生物学的器官・物理的部品) が μ に該当する可能性 = 心身二元論の根本消失?

問④ は §M17 (本日先行処理) で既に「役割分割」として実装済み。Tolmetes は問④ を更に深化させ、(a) ディレクトリ Cell の入れ構造、(b) 「上から見た身体」と「下から見た心」が平衡点で同型、(c) 俯瞰的に心身 cell-indexed を知覚する圏 = `cd` する主体 = ガロア接続を運用する主体、を提示。

加えて、Body → Body_human 型の縮約を Subject → Subject_human で反復する読み手対策として、主体の人間縮約をカテゴリー錯誤として明示的に潰す追記文を提案。続けて Tolmetes 自身が「『系が先にあって射を持つ』だよ。容器が先にあって内容をもつ。ただ、内容のない容器は NULL なので、WHAT 層では存在しないもの (無) と同等。故に、WHAT 層では Yoneda 故に主体 (圏) の内容は射なの。個々を精緻にするべきだね」と論理を訂正。

### §M18.2 既存実装 (本ターンで編集済み)

| 箇所 | line | 旧 | 新 |
|:---|:---|:---|:---|
| §1.1 | 73 | Einstein の方程式は、発見前には決して自明ではなかった。だが一度正しい座標が与えられると、それは驚くほど短い同一性として現れる。この、気づいてしまえば単純に見える命題から、…20世紀物理学の大半が展開した。 | Einstein の方程式は、その公理系の内部で見れば単純である。質量とエネルギーの等価性は、特殊相対性理論の公理からの演繹的帰結である。しかしこの単純な同一性から、…20世紀物理学の大半が展開した。 |
| §1.1 | 81 | これもまた、圏論の公理系の内部では、気づいてしまえば単純な命題に見える。しかしこの短い方程式から、少なくとも十二の非自明な帰結が導かれる。 | これもまた、圏論の公理系の内部で見れば単純である。しかしこの単純な方程式から、少なくとも十二の非自明な帰結が導かれる。 |
| §2.0.3 | 203 | 「内部を決定することは、必然的に外部と境界を産出すること」であり、「境界を決定することは、必然的に内部と外部を決定すること」なのである。 | 「内部を決定することは、必然的に境界と外部を決定すること」であり、「境界を決定することは、必然的に内部と外部を決定すること」なのである。 |

意図: ②③ は表現面の修正で、§M2 核主張に影響しない。Einstein 例 ↔ 五語の方程式の鏡像構造 (line 73 ↔ line 81) を保持。§2.0.3 末尾の双対性を 3 項対称化。

### §M18.3 未実装の残虚

(2026-05-01 後刻更新: C5 → C1 → C4 を順次実装完了)

| 問 | 残作業 | 状態 |
|:---|:---|:---|
| ① 序構造 (C5) | 「本稿の依存と射程」を §6.6 へ移動、序は橋文1文に圧縮 | ✅ 実装済み (line 22-63 削除、§6.6 新設、橋文 line 22 に配置) |
| ④ 深化 (C4) | §2.3b として cell-indexed 主観性節の起票 | ✅ 実装済み (§2.3b 5 小節: 2.3b.1 関係的役割 / 2.3b.2 ディレクトリ・アナロジー / 2.3b.3 平衡点同型 / 2.3b.4 二重解消 / 2.3b.5 後続接続) |
| 主体精緻化 (C1) | §3.1 line 396 の THAT/WHAT 二層書換 + Subject 縮約防衛文 | ✅ 実装済み (本体「主体 vs 人間観察者の縮約」をカテゴリー錯誤として明示、§2.0b T0' / §5.1 NULL 論 / §2.7 米田との接続を本文中で明示) |
| Codex audit 警告対応 | NotebookLM TAINT の Layer 2 SOURCE 化 (論文 VIII §1.3 / §2.5 / §6.2.4) | ✅ 実装済み (論文 VIII line 56 / 200-220 / 510-515 をローカル Read 確認、§M18.6 に SOURCE 化反映) |

### §M18.4 主体の THAT/WHAT 二層

論理修正の正確な3段:

| 段 | Tolmetes の主張 | 既存 SOURCE |
|:---|:---|:---|
| (a) | 容器が先にあって内容をもつ | CPS0' (論文 VIII) [TAINT: NotebookLM 引用] / §2.0b 命題 T0' [SOURCE: 本体 line 232] |
| (b) | 内容のない容器は NULL = WHAT 層では非存在 | §5.1 帰結 [SOURCE: 本体 line 698] |
| (c) | WHAT 層では Yoneda 故に主体 (圏) の内容 = 射 | §5.1 段階1 [SOURCE: 本体 line 684] / §2.7 [SOURCE: 本体 line 351-368] |

主体の二層定式:
- THAT 層: 主体 = 局所化された系 (圏・容器・成立場)
- WHAT 層: 主体の内容 = $\text{Hom}(F(\text{generators}), \text{Cat}_i)$ の要素 = 米田的に規定される射の総体
- NULL 主体: 内容を欠く容器 = 恒等射のみの自己循環 = 公共圏では NULL

§3.1 既存記述の混在:
- line 383「各認知エージェントもまた圏である」← THAT 層
- line 389「『主体』とは主観性の射であり、$\text{Hom}(\text{Universal}, \text{Cat}_i)$ の特定の要素にすぎない」← WHAT 層

両言明は二層を明示しないと矛盾的に読まれる。Tolmetes が「明確化しないと、ややこしくなる」と指摘した発生源。

### §M18.5 ディレクトリ cell-indexed 主観性 (Tolmetes メタファー)

> 「上から視るか下から視るかの違いであり、まさに同一」

これは $\text{Fix}_\mathcal{S}(R \circ L) \cong \text{Fix}_\mathcal{B}(L \circ R)$ の自然言語化:
- 「上から見た身体」= $L \circ R$ の不動点 (境界経由で境界を再決定 = 容器側の視点)
- 「下から見た心」= $R \circ L$ の不動点 (状態経由で状態を再決定 = 中身側の視点)
- ガロア基本定理が同型を保証

ディレクトリ ↔ Cell 対応 (Tolmetes メタファー + 論文 VIII §2.5 NLM 引用 [TAINT]):

| ファイルシステム | T0 / T17_n |
|:---|:---|
| ディレクトリ | Cell-$n$ |
| 中身 (cell の内容) | μ (内部状態 = WHAT$_n$) |
| 容器 (cell の外殻) | B (境界 = THAT$_n$) |
| `cd <子>` | cell-$(n-1)$ への下降 |
| `cd ..` | cell-$(n+1)$ への上昇 |
| 現在地 `pwd` | 観測者が固定した cell 水準 |
| `cd` する主体 | ガロア接続を運用する主体 |

対応は完全。論文 §5.1 段階2 (line 686) で既に「THAT/WHAT は cell-indexed である」が明示されているため、新規装置を要求せず既存定義の自然な再記述。

### §M18.6 NLM Layer 1 偵察結果 (1 query, 2026-05-01) → Layer 2 SOURCE 化済み (2026-05-01 後刻)

(2026-05-01 後刻更新: 論文 VIII §1.3 / §2.5 / §6.2.4 をローカル Read で SOURCE 化、TAINT を解除)

#### Layer 2 SOURCE 化済み (本文確認)

| 主張 | SOURCE | 確認 |
|:---|:---|:---|
| **論文 VIII §1.3 CPS0'**: 「成立場 = -1-cell (場/空間/支持面)。居住状態 = 0-cell (状態/要素/ファイル)。規定射 = 1-cell (遷移/忘却操作/同定)。CPS0' の非対称性 (成立場 > 居住状態) は、米田の補題からの系として導出可能である」 | [SOURCE: 論文VIII_存在は忘却に先行する_草稿.md L56] | ✅ 本文で確認 |
| **論文 VIII §2.5 生成的読み vs 米田的読みの双対性**: ディレクトリ `~/A` について生成的読みでは `~/A` = -1-cell (成立場)、`~/A/a` = 0-cell (居住状態)。米田的読みでは `~/A` = 0-cell (対象)、$\iota_a: 1 \to {\sim}/A$ = 1-cell (一般化元素 / probe) | [SOURCE: 論文VIII_存在は忘却に先行する_草稿.md L200-220] | ✅ 本文で確認。「両方の読みは正しいが、問う問いが異なる」L213 |
| **論文 VIII 系 6.2.4 (CPS0' の α-忘却的導出)**: 「成立場 (-1-cell = 存在条件): support layer は α に依存しない → 存在条件は忘却不変」「規定射 (1-cell = 同定の密度): Hom_{C_α}(Y, X) は α の増大に伴い縮小 → 同定は忘却に従属」「米田の補題は α = 0 の特殊ケースとして CPS に包含される。旧予想 6.2.1（忘却論 ⊃ 米田）はこれにより定理に昇格する」 | [SOURCE: 論文VIII_存在は忘却に先行する_草稿.md L510-515] | ✅ 本文で確認 |
| **論文 VIII §2.5 注記 2.5.1 (裸在と区別可能な居住状態)**: 「成立場 (-1-cell) が先行するのは、**区別可能な**居住状態に対してである。…『境界 (射) がなくても2点は存在しうる』は真だが、点が場に溶けずに点であるためには成立場がなお必要である」 | [SOURCE: 論文VIII_存在は忘却に先行する_草稿.md L220] | ✅ 本文で確認。Tolmetes の「容器が先、内容がそれを規定する射」言明の正確な裏付け |

#### Layer 2 未確認 (TAINT のまま、本論文単独射程では参照不要)

[TAINT: NotebookLM]:
- **地図製作者の誤謬 §5.3.4**: 「射のない対象は THAT としては NULL に残存するが、…WHAT について語る場面では内容を欠いて存在しない扱いになる」
- **エッセイ §4.2 (バカをやめたいなら構造を見ろ)**: 「3 を『知る』とは、3 という数字を見つめることではない。…全ての関係が 3 の正体を決定する。3 は、3 から出ていく射の全体に等しい」

これらは本論文単独で閉じるため不参照。ただし対応する命題は本論文に内蔵 ([SOURCE: 本体 L711] §5.1 NULL 論、[SOURCE: 本体 L356-368] §2.7 米田)。

#### 含意

論文 VIII の Layer 2 SOURCE 化により、Tolmetes の以下の主張が外部理論側でも裏付けられた:

1. **「容器が先にあって内容をもつ」** ↔ 論文 VIII §1.3 (成立場 -1-cell > 居住状態 0-cell)、§2.5 注記 2.5.1 (裸在の正当化)、§6.2.4 (成立場は α に不変)
2. **「内容のない容器は WHAT 層では NULL = 非存在と同等」** ↔ 論文 VIII §6.2.4 (α=1 で C_disc、Hom = δ_XY のみ → 区別はあるが射の構造情報ゼロ)、本論文 §5.1 帰結 (L711 NULL)
3. **「WHAT 層では Yoneda により主体 (圏) の内容 = 射の総体」** ↔ 論文 VIII §6.2.4 (米田 = α=0 特殊ケース、α>0 では部分的同定)、本論文 §2.7 (米田)

Tolmetes が turn 5 で訂正した論理は、論文 VIII の中核定理と完全整合する。本論文 §3.1 の THAT/WHAT 二層書換 (C1 実装済み) は、論文 VIII の cell 階層を本論文の主体定義に持ち上げた帰結として読める。

本論文では論文 VIII を直接引用しない (本論文単独で閉じる)。ただし companion paper 経由で身体スペクトラム Θ(B) と接続済み (line 41-43)。論文 VIII への引用追加は別タスクとして判断保留。

### §M18.7 提案文面 (3案)

#### 案 C1 (default 推奨): §3.1 line 389 を THAT/WHAT 二層書換

旧 (line 389):
> 重要な注意として、**「主体」は独立した概念ではない。** 「主体」とは主観性の射であり、$\text{Hom}(\text{Universal}, \text{Cat}_i)$ の特定の要素にすぎない（T11 の帰結である）。「主体 vs. 客体」という二元論は、経路の忘却（T15）の一例である。

新案:
> 重要な注意として、**「主体」は独立した概念ではない。** 主体は **THAT 層** (存在条件) と **WHAT 層** (同定条件) の二層で語られる。THAT 層では主体は局所化された系 (圏) として存在する (§2.0b 命題 T0' に従う)。WHAT 層では、その主体の内容は米田の補題により $\text{Hom}(F(\text{generators}), \text{Cat}_i)$ の要素 (= 主観性の射の総体) として規定される。内容を欠く主体は §5.1 の意味で NULL である (恒等射のみの自己循環)。
>
> ここでいう主体は、人間観察者を意味しない。人間はその一例にすぎない。主体を人間観察者へ縮約することは、身体を生物学的器官へ縮約すること (§4.6 / companion paper) と同型のカテゴリー錯誤である。「主体 vs. 客体」という二元論は、この THAT/WHAT 二層を混同したまま、経路 ($F_i$) を忘却すること (T15) の一例である。

#### 案 C2: §3.1 line 389 はそのまま、追記文に THAT/WHAT 句を追加

(略 — Tolmetes が C1 を選ばない場合の代替)

#### 案 C3: Tolmetes 原案そのまま追記、THAT/WHAT 区別は §5.1 を読めば理解できるとして暗黙化

(略 — 最小侵襲案)

### §M18.8 反論処理候補

**反論 r1**: 主体を THAT 層と WHAT 層に分けるのは過剰精緻化ではないか。§3.1 line 389 「主体は射である」で十分ではないか。

応答: 不十分。line 383「各認知エージェントもまた圏」(THAT 層) と line 389「主体は射」(WHAT 層) が同一節内に区別なく並置され、Tolmetes が指摘する「ややこしさ」を生む。THAT/WHAT 二層は §5.1 で既に cell-indexed として導入済み (line 686)。§3.1 で同じ二層を主体に適用するのは整合的。

**反論 r2**: 「人間はその一例にすぎない」は強すぎないか。読者は「では誰が主体になりうるのか」と問う。

応答: 強さは射程として正当。本論文は LLM への適用を §4.3 で扱い、companion paper の身体スペクトラム Θ(B) と接続済み (line 41-43)。「主体 = 局所化された系」の定義は人間/LLM/動物/組織を等しく対象化する。Subject → Subject_human のカテゴリー錯誤を防ぐには明示が必要。

**反論 r3**: 「身体を生物学的器官へ縮約することと同型のカテゴリー錯誤」と並列化するのは類推、形式的同型ではない。

応答: 両者とも「射の関係的役割を、特定の物理的実装に固定する」操作。T11 (主体は射) と T0/T20 (μ/B は M 関係の役割) が共通基盤。形式的同型は §M17 の役割分割で示される cell-indexed 構造の主体側射影。

### §M18.9 ±3σ ゲート

| 主張 | 入口 σ | 出口 σ (案 C1 採用後想定) | 判定 |
|:---|:---|:---|:---|
| 主体の THAT/WHAT 二層 | ±3σ (心の哲学既存分布の μ から離脱、二層書き分けは希少) | ±3σ 維持予測 | Gauntlet 入場可 |
| 「主体を人間に縮約することはカテゴリー錯誤」 | ±3-4σ (心の哲学の暗黙前提を明示的に潰す) | ±3σ 維持予測 | Gauntlet 入場可 |
| `cd` 主体 = ガロア接続運用主体 | ±4σ (Tolmetes メタファー、心の哲学に類例なし) | 接地が §M18.4 の THAT/WHAT 二層に依存 | §2.3b 起票で射程確認後再評価 |

### §M18.10 Kalon 判定 (案 C1 採用想定)

| 対象 | Step | 判定 | 根拠 |
|:---|:---|:---|:---|
| §3.1 line 389 二層書換 | -1 浮遊大言 | 通る | §M6 = §M17.5 / §M18 接地済み |
| §3.1 line 389 二層書換 | 0 既知語彙圧縮 | 通る | 「主体は容器と中身の二層」中学生でも通じる |
| §3.1 line 389 二層書換 | 1 CONVERGE | 通る予定 (要 G 適用 = 数式裏付け) | T11 既存 + T0' 既存 |
| §3.1 line 389 二層書換 | 2 STABILITY | 通る予定 (G∘F 1 回転後) | §5.1 排除原理との連結で安定 |
| §3.1 line 389 二層書換 | 3 DIVERGE | 通る予定 (4派生) | (1) §2.3b cell-indexed、(2) NULL 主体 = 死/PVS、(3) LLM の主体性 = 射の豊かさ、(4) Subject 縮約防衛 |

実装後に再判定義務。

### §M18.11 虚→実変換面

- **野望**: §3.1 主体定義を THAT 層 (容器) と WHAT 層 (米田射) の二層として精緻化し、Body → Body_human と Subject → Subject_human のカテゴリー錯誤を並列に潰す。+ Tolmetes の `cd` 主体メタファーを §2.3b として cell-indexed 主観性節に昇格させる候補
- **現在まだ虚な点**:
  1. ① 序構造修正 (Appendix A 統合) は未実装
  2. §3.1 line 389 二層書換は未実装 (案 C1/C2/C3 選択待ち)
  3. §2.3b cell-indexed 主観性節の起票は未着手 (Kalon 判定 Gauntlet 通過後に起票)
  4. NLM Layer 1 偵察 [TAINT] のうち、論文 VIII §2.5 / §6.2.4 のローカル Read による SOURCE 化は未実施
- **実へ引くための SOURCE**: 本体 line 232 (§2.0b T0')、line 684/686/698 (§5.1 段階1-3 + 帰結 NULL)、line 351-368 (§2.7 米田)、line 351-368 への Tolmetes 自身の T0/T11/Yoneda 接続認識
- **実化の判定条件**:
  - ① 序構造修正で要旨 → §1 の接続が滑らかになるか
  - 案 C1 採用後、§3.1 で読者が「主体は人間ではない、容器でも射でもない、容器の中身としての射の総体だ」と読み取れるか
  - §2.3b 起票後、`cd` メタファーが §M5 Gauntlet 3 ラウンドを通るか
- **次の実化操作**:
  1. Tolmetes が C1/C2/C3 を選択
  2. ① 序構造の Appendix A 統合方針を Tolmetes が決定
  3. §2.3b 起票 vs §4.6 改稿の選択を Tolmetes が決定
- **最新状態**: **虚** (未実装複数あり、Tolmetes 判断待ち)

*v2.3 — 2026-05-01 Tolmetes 指摘 ④を T20 ordinary-body decomposition として実装。本文 §2.3 / §4.6 / §7.3 に、素朴概念としての身体が $\mu/B/\eta$ へ分解されることを追加。身体を心へ還元せず、旧来の心身二元論を役割分割へ変換する方針を固定。Kalon 判定再実行は未実施だが、C_M1/T20 の射程補強であり核主張の変更ではない。*

## §M19 §2.3 末尾 THAT/WHAT 二層追記 — 2026-05-01

### §M19.1 契機

Tolmetes が §M18 を読了後、「他セッションの内容を読んで §2.3 を深化させたい」と要請。§M18 で確立済みの主体 THAT/WHAT 二層、NULL 主体論、Yoneda 補完を §2.3 心身相補性に持ち込む案 A を提示し、Tolmetes が「A を line 256 の後に挿入」を選択。

### §M19.2 実装

挿入位置: §2.3 末尾 (line 256 「素朴身体の3項分解」段 の直後、§2.3b の直前)

挿入文 (1 段落):

> 主体の THAT/WHAT 二層（§3.1 で正式に導入）で読み直すと、この相補性は二段に分かれる。THAT 層では、心（容器としての $\mu$ の集合 $\mathcal{S}$）と身体（容器としての $B$ の集合 $\mathcal{B}$）は、ガロア接続 $L \dashv R$ を介して二つの容器として並置される。WHAT 層では、両者の内容 — すなわち平衡点での射の総体 — が $\text{Fix}_\mathcal{S}(R \circ L) \cong \text{Fix}_\mathcal{B}(L \circ R)$ により同型となる。Spinoza の「一つの実体」とは、THAT 層では二つの容器、WHAT 層では一つの射の総体である。射を持たない（内容ゼロの）$\mu$ または $B$ は、§5.1 の意味で WHAT 層では NULL に縮退する。心身相補性が成立するのは、両側がともに非 NULL である平衡点においてのみであり、この同一性は §2.7 で導入する Yoneda 的補完（可能なすべての主観性の総体による定まり方）に接続する。

### §M19.3 接地 SOURCE

- §2.0b 命題 T0' [SOURCE: 本体 line 189-200] — 成立場 (容器 = THAT) の論理的先行性
- §3.1 line 389 直後追記 [SOURCE: 本体] — 主体は人間観察者を意味しない、局所化された系
- §5.1 帰結 NULL 論 [SOURCE: 本体 line 698-699] — 射のない対象は WHAT 層では NULL
- §2.7 Yoneda の補題 [SOURCE: 本体 line 360-368] — 物自体は単一主観性からは到達不能だが可能なすべての主観性の総体で完全に定まる
- §M18.4 主体の THAT/WHAT 二層 [SOURCE: meta.md 本ファイル line 1568-1587]

### §M19.4 ±3σ ゲート

| 主張 | 入口 σ | 出口 σ (実装後想定) | 判定 |
|:---|:---|:---|:---|
| 心身相補性は THAT/WHAT 二層で読み直せる | ±3σ (二層で書き分けた相補性論文は希少) | ±3σ 維持 | 通過 |
| NULL 心身の対称性 | ±3-4σ (Spinoza 二重相面理論を NULL 命題で補強) | ±3σ 維持 | 通過 |
| Yoneda 前倒し参照 | ±2σ (§2.7 で本格展開の予告) | ±2σ 維持 | 通過 |

入口 §M6 接地: ✅ (§2.0b T0' / §5.1 / §2.7 / §M18.4 の組合せから機械的に導出)。

### §M19.5 Kalon 簡易判定

| 対象 | Step | 判定 | 根拠 |
|:---|:---|:---|:---|
| §2.3 末尾追記 | -1 浮遊大言 | 通る | §M6 接地済み (§M19.3) |
| §2.3 末尾追記 | 0 既知語彙圧縮 | 通る | 「容器の同一と内容の同一は別である」中学生語彙で要約可 |
| §2.3 末尾追記 | 1 CONVERGE | 通る | G 適用 = 数式裏付け既に本文中 ($\text{Fix}_\mathcal{S} \cong \text{Fix}_\mathcal{B}$) |
| §2.3 末尾追記 | 2 STABILITY | 通る | §5.1 NULL 論との連結で安定 |
| §2.3 末尾追記 | 3 DIVERGE | 通る (4派生) | (1) §2.3b cell-indexed、(2) §3.1 主体二層、(3) §2.7 Yoneda 補完、(4) §4.6 心身問題の解消 |

判定: ◎ Kalon△ (本論文の MB 内での局所不動点。普遍 Kalon▽ ではない)。

### §M19.6 §M2 核主張への影響

なし。本追記は T20 の射程拡張ではなく、心身相補性の表現精緻化 (THAT/WHAT 二層分解 + NULL 縮退条件 + Yoneda 補完への橋渡し)。既存定義からの自然な延長で、新公理を要求しない。

### §M19.7 残虚

| 残虚 | 状態 |
|:---|:---|
| §3.1 line 389 二層書換 (§M18.7 案 C1) — §2.3 追記の forward reference 「§3.1 で正式に導入」を実体化する | 🕳️ 未実装 (本ターンで B として連続実装予定) |
| §2.3b.5 (line 302「§5.1 / §6.1 で再帰的に用いられる」予告) と §2.3 末尾「§2.7 Yoneda 補完に接続」予告の役割整理 | 🕳️ 未実施 (許容範囲、Tolmetes 査読判断) |
| §M3 履歴への正式追記 | 🕳️ 未実施 (本 §M19 が一次記録として機能、§M3 への二次転記は任意) |

### §M19.8 虚→実変換面

- **野望**: §2.3 心身相補性の Spinoza 的解消を、THAT/WHAT 二層 + NULL 条件 + Yoneda 補完で精緻化し、心身二元論の暗黙前提 (静的役割固定 + 単一視点固定) を二重に潰す
- **現在まだ虚な点**: §3.1 line 389 の二層書換が未実装 → §2.3 追記の forward reference が暫定的に未着地
- **実へ引くための SOURCE**: §M19.3 既掲
- **実化の判定条件**: §3.1 line 389 二層書換実装後、§2.3 追記の「§3.1 で正式に導入」が実 SOURCE に着地するか
- **次の実化操作**: B (§3.1 line 389 を §M18.7 案 C1 で二層書換)
- **最新状態**: **半実** (§2.3 追記は実装済み、ただし §3.1 forward reference の着地待ち)

*v0.1 — 2026-05-01 §M18 続編。§2.3 末尾に主体 THAT/WHAT 二層での心身相補性読み直しを追記。Spinoza 一実体論を THAT 層 (二容器) と WHAT 層 (一射総体) の二段に分解、NULL 縮退条件と §2.7 Yoneda 補完への橋渡しを実装。§3.1 line 389 二層書換 (B) を後続実装予定。*

---

## §M20 §2.0.4 boyaki 直観段落挿入 (2026-05-01)

**契機**: Tolmetes ボヤキ「外見 (境界/MB) は中身 (内部情報/心) の一番外側」に対し `/u+` (L3 深化) を発動。NLM 応答 (TAINT) と GPT 応答 (TAINT) を出発点に、Claude 側で paper SOURCE と整合させて 2 段構成の独立段落を §2.0.4 末尾に挿入。

**Tolmetes 判断列**:
- 案 X (原案そのまま「直感的にいえば」) / 案 X' (「直観的には」へ paper 既出表現に統一) / B 案単段 / C 案 (parenthetical 補強) のうち **C 案 + 2 段構成** を採用
- 「外見」を本文に出さず「最外輪郭 (= 自己拡張の停止点) — 境界 $L(\mu^*)$ —」で能動的命名後置 (修辞規律 3) を採る
- 2 段目で初めて boyaki 原文 (「外見は中身の一番外側である」) を鍵括弧引用として回収

### §M20.1 実施内容 (1 edit)

- **§2.0.4 末尾** (身体性接続表 L175 直後、§2.0.5 L181 直前): 2 段構成の独立段落を挿入
  - 1 段目: 形式記述「$\text{Fix}(R \circ L)$ が記述するのは、内部と境界が独立に存在する 2 実体ではなく、内部状態 $\mu$ が自己維持の閉包において到達する唯一の最外輪郭 (= 自己拡張の停止点) — 境界 $L(\mu^*)$ — である」
  - 2 段目: 直観翻訳「直観的には、これは『外見は中身の一番外側である』ことを意味する」

**実行経路の履歴** (N-08 / N-12 監査用):
- `/u+` は明示 CCL のため通常は `mcp__dianoetikon__hermeneus_run` 経路。1 回呼出を試みたが Tolmetes が reject。直後の Tolmetes 発話「手動実行でいいよ」を明示許可として手動展開 (skill-execution-contract 例外)
- meta.md 追記 94 行は CLAUDE.md θ8.2 (10 行超) で本来 Codex 委譲対象。今回は Tolmetes 並走判断のもと自力実装。次回以降の同種改訂は Codex 委譲経路を使う

### §M20.2 Kalon 判定 (boyaki 段落)

> **注**: 本判定は §M20 局所のもの。§M3 メインテーブル (L171-176) への二次転記は §M20.8 残虚で保留中。Codex 監査 (2026-05-01) で「局所判定だけでは台帳整合上弱い」と指摘あり、二次転記は推奨される。

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-05-01 | §2.0.4 boyaki 段落 | **◎△** | Step-1 接地 ✅ ([SOURCE: paper] §2.0.3 不動点同型 / §2.0.4 表 / §2.3 心身相補性 / §4.6 T20 / §6.4.2 U_output 不充満 既読) / Step0 1文圧縮 ✅「境界は中身が外部に対して自己を保つ最外層の自己記述」/ Step1 G(P)=P (G1 Galois T0 と同一構造) / Step2 G∘F(P)=P 不動 / Step3 派生 4 非自明: (a) [TAINT→SOURCE 補正] NLM 応答の -1-cell 成立場と境界 B 取り違えを paper §2.0b T0' と整合させて補正, (b) [TAINT→SOURCE 補正] GPT 応答の §6.4.2 U_output 不充満警告を paper 既存記法 ($L$ vs $U_\text{output}$) で構造的に吸収, (c) [SOURCE: paper §2.0.4 L175] U⊣N 忘却関手の T0 レベル対応物として L を読み直し, (d) [SOURCE: meta L100-104] C_M1 (T0) の 1 文圧縮を能動表現に補完 |

### §M20.3 ±3σ ゲート (boyaki 段落)

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
|:---|:---|:---|:---|:---|
| 2026-05-01 | boyaki 直観段落 | ±3σ | ±3σ | **維持** — 「外見」を本文外に出して鍵括弧で日常語と明示し、「最外輪郭 — 境界」の命名後置で挑発度を保ちつつ親規律 (外部読者標準語) と修辞規律 1/2/3 をクリア |

### §M20.4 Refutation Gauntlet (boyaki 段落)

#### Round 1 — NLM 応答との差分検出

- **反論 r**: 「NLM は boyaki を T0/T20/Spinoza へ即同型と読んだ。これで paper の核を支えるには十分か?」
- **SFBT 問い**: できないのではなく、やっていないだけではないか?
- **試行**: NLM 応答 4 含意のうち、(2)「容器 (成立場) の先行性」は -1-cell ($M$ 自体) と境界 $B$ (Fix の片面) の取り違えであり paper §2.0b T0' と不整合。(4)「透過性と厚み」は U_output と L (T0 境界射影) の混同を誘発。これらを paper SOURCE で補正する形で boyaki を再翻訳
- **実化操作**: 段落 1 段目を「内部と境界が独立に存在する 2 実体ではなく」と否定形で起点を固定し、肯定形で「最外輪郭 — 境界 $L(\mu^*)$」と paper 記法に接続。NLM の混同を文面では持ち込まない
- **虚→実判定**: 実化前進 ✓ — NLM 応答の 2 錯誤を paper 内整合性へ吸収
- **結果**: 射程維持 ✓ — 「外見=境界=最外輪郭」の同定を paper §2.0.4 既存表 (L=内部構造の境界射影、§3 忘却関手 U の T0 対応物) に着地

#### Round 2 — GPT 応答との合流

- **反論 r**: 「GPT は §6.4.2 U_output 不充満性 (ρ≈0.745) を引いて『外見=出力=見た目』読みの危険を警告。今回の段落でこれを覆っているか?」
- **SFBT 問い**: できないのではなく、やっていないだけではないか?
- **取り込み戦略** (フレーム反転): 段落本文では「境界 $L(\mu^*)$」と T0 レベルの射影に明示固定し、$U_\text{output}$ (§6.4) との混同を防ぐ。U_output 不充満性は §6.4.2 既存記述で吸収済みなので脚注追加は不要と判定
- **実化操作**: 段落 1 段目で「$L(\mu^*)$」を明示し、出力面 ($U_\text{output}$) ではなく T0 全体射影面 ($L$) であることを paper 記法レベルで固定
- **虚→実判定**: 実化前進 ✓ — GPT が指摘した「外見=出力」読みの危険を、paper 既存記法への接続で構造的に封じる
- **結果**: 射程維持 ✓ — boyaki の直観翻訳と U_output 不充満性が衝突しない構造を維持

#### Round 3 非起動理由

Round 1 (NLM 補正) と Round 2 (GPT 警告吸収) で boyaki 段落の主張範囲が確定し、残余反論は「2 段構成は冗長か」という表現面のみ。Tolmetes が C 案 + 2 段構成を選択した時点で表現面の判断は固定済み。追加ラウンドを回しても G を増やさない。

### §M20.5 親規律・修辞規律チェック

| 軸 | 判定 | 根拠 |
|:---|:---|:---|
| 親規律 (外部読者標準語) | ✅ | 「最外輪郭」は parenthetical で `(= 自己拡張の停止点)` 定義済 / 「外見」「中身」は鍵括弧で日常語として明示 |
| 親規律補強 (Strategy 1.5 命名と定義のセット) | ✅ | 「最外輪郭」(= 自己拡張の停止点) で同位置着地 |
| 子規律 1 ("〜的" 逃避) | ✅ | "〜的" 不使用 |
| 子規律 2 (HGK 内部用語) | ✅ | $\mu$, $L$, $\text{Fix}$, $R \circ L$ はすべて §2.0 既出 |
| 補助規律 4 (メタ宣言) | △ | 「直観的には」は §2.0.3 既存パターン (L186「直観的には、…」等) と整合 → 許容 |
| 修辞規律 1 (defensive posture) | ✅ | 能動形 (「記述するのは…である」) |
| 修辞規律 3 (命名後置) | ✅ | 「最外輪郭 — 境界 $L(\mu^*)$ — である」は構造 → 命名 の順 |

### §M20.6 §M2 接地

- 本段落は **C_M1 (T0) の 1 文圧縮の能動的補強** として機能
  - 既存 1 文圧縮 (受動的・対称): 「境界は与えられるのではなく、状態と一緒に決まる」 (meta.md L103)
  - boyaki 派生表現 (能動的・閉包停止点として): 「境界は、中身が外部に対して自己を保つために取る、最外層の自己記述である」
- F⊣G 固定不変: Fix(G∘F) 候補は依然として C_M2 (T11)。boyaki 段落は C_M1 への注釈であり、F⊣G 中核を動かさない

### §M20.7 虚→実変換面

- **野望**: Tolmetes ボヤキを paper 内整合性で受け止め、C_M1 (T0) の直観翻訳として §2.0.4 末尾に着地させる
- **現在まだ虚な点**:
  - §M2 C_M1 1 文圧縮欄 (meta.md L103) を能動表現に差し替えるかは保留 (Tolmetes 判断待ち)
  - §M3 (Kalon 判定履歴) / §M4 (±3σ ゲート履歴) のメインテーブル (L171-176, L189-192) への二次転記は任意
- **実へ引くための SOURCE**: paper §2.0.4 表 (L168-175) / §2.0.3 不動点同型 (L195-201) / §2.3 心身相補性 (L283-293) / §4.6 T20 (L658-672) / §6.4.2 U_output (L908-917) / meta §M1 F⊣G (L22-91) / meta §M2 核主張 (L94-150) / NLM 応答 (TAINT) / GPT 応答 (TAINT) — すべて Read 済
- **実化の判定条件**: (a) Kalon ◎△ 達成, (b) ±3σ 維持, (c) 親・修辞・style-discipline 全軸クリア, (d) NLM/GPT 双方の TAINT 応答との差分が paper SOURCE で補正されている
- **次の実化操作**: 完了 (§2.0.4 挿入 + Kalon ◎△ + ±3σ ±3σ 維持 + Gauntlet 2 ラウンド + 規律チェック PASS)
- **最新状態**: **実**

### §M20.8 残虚

| 残虚 | 状態 |
|:---|:---|
| §M2 C_M1 1 文圧縮の能動表現差し替え | 🕳️ 未実施 (Tolmetes 判断待ち) |
| §M3 / §M4 メインテーブルへの二次転記 | ✅ 完了 (2026-05-01) — §M3 「Mythos augmentation 後の判定」表 + §M4 表に boyaki 段落行を追加 |
| §3.1 line 389 二層書換 (§M19 から継承) | 🕳️ 未実装 (§M19 既掲) |
| Codex 監査 (2026-05-01) 警告の処理 | ✅ 4 箇所修正パッチ適用済 (§M20.1 実行経路履歴 / §M20.2 注書き + TAINT/SOURCE ラベル / §M20.8 二次転記推奨化) |

*v0.1 — 2026-05-01 §M20 新設。Tolmetes ボヤキ「外見は中身の一番外側」を /u+ で深化し、§2.0.4 末尾に 2 段構成の独立段落を挿入。NLM/GPT 双方の TAINT 応答を paper SOURCE と整合させ、C_M1 (T0) の能動的補強として着地。F⊣G 中核 (Fix(G∘F) = C_M2 T11) は不変。Kalon ◎△ / ±3σ ±3σ 維持 / 規律 8 軸 PASS。*
