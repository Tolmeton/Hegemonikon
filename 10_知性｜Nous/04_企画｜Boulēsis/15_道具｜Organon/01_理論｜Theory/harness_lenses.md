# Harness Lenses — Harness を読む複数視点

> **位置付け**: harness は 1 つの対象に対し複数の読み方が可能な道具 (Organon)。本ファイルはその複数 lens を集約する。各 lens は harness のある面だけを照らし、他の面を落とす。**ドメイン体系の拡張ではなく、読み方の集約**。

---

## なぜ複数 lens が必要か

harness は外部観点からは「LLM をラップする infrastructure」 [SOURCE: Pachaar 2026 "The Anatomy of an Agent Harness"] だが、HGK 内部からは複数の異なる角度で読める:

- **行為可能性を開く装置** (Euporía view)
- **誤り訂正の冗長層** (FT architecture view)
- **階層越境するアセンブリ層** (CCL=ISA view)
- **中動態を観測するセンサー** (Daimonion δ view)
- ...

これらは矛盾しない。同じ対象を異なる射影で見ているだけ。どの lens を選ぶかは、harness のどの性質を前景化したいかで決まる。

---

## Lens 1: Euporía view — 行為可能性を開く装置

### 核主張

**harness の意味 = harness が LLM に与える Hom(LLM, −) の豊かさ**。

### 根拠

[SOURCE: euporia.md L104-109 §1 米田の補題] の適用:

> 対象 B の「意味」は B から出る全ての射 Hom(B, −) で完全に決定される。

LLM を object B とすれば、LLM の意味 (その LLM が何であるか) は、LLM が接続された harness を通して **実際にできること** — すなわち Hom(LLM, −) の集合 — で決定される。

### Akshay 12-component の AY 射影 (一部)

[SOURCE: Pachaar 2026] の 12 components を AY 正負で分類すると、2 類型が自然に現れる:

| Component | 開く Hom | AY 作用 |
|---|---|---|
| Tools | Hom(LLM, 外部世界) | **> 0 創出** |
| Memory | Hom(LLM, 過去状態) | **> 0 創出** |
| Verification | Hom(LLM, 自己点検) | **> 0 創出** |
| Subagent | Hom(LLM, 他 LLM) | **> 0 創出** |
| Context (compaction) | Hom(LLM, 注意対象) を絞る | **≥ 0 保全** |
| Guardrails | Hom(LLM, 逸脱) を閉じる | **≥ 0 保全** |

この 2 類型は [SOURCE: euporia.md L192-204 §2.5] の「self-evidencing の 2 様式」と一致する:

- (a) AY 増大 `> 0` — 新しい道を作る
- (b) AY 保全 `≥ 0` — 既存の道を閉じない

### 実証

[SOURCE: Pachaar 2026 (Boris Cherny 引用)]:

> giving the model **a way to verify** its work improves quality by 2-3x.

"a way to verify" は文字通り**新しい Hom(LLM, 自己点検) を開く行為**であり、その効果 (2-3x) は Euporía view の empirical ground truth として機能する。

### この lens が照らすもの

- harness の「道具としての価値」は Hom 開拓 / 保全の能力で測られる
- harness の設計軸 ([SOURCE: Pachaar 2026] の 7 decisions: Agent count / Reasoning / Context / Verification / Permissions / Tool scoping / Thickness) は全て **どう Hom を開くか** の決定軸として統一的に読める

### この lens が落とすもの

- harness の耐久面 (FT architecture view — Lens 2 で扱う予定)
- 階層越境構造 (CCL=ISA view — Lens 3 で扱う予定)
- being 層の観測 (Daimonion δ view — Lens 4 で扱う予定)

### HGK 内部接続

- Euporía は Flow (d=1) の定理として位置付けられる [SOURCE: euporia.md L30-47 §1]
- 正典: axiom_hierarchy.md §定理³ [SOURCE: euporia.md L20, L877 で参照明記]
- 米田経由で「harness = Hom 開拓装置」は Euporía 原理の **harness-局所的な具現化** として読める
- 重点座標: 主に **Function** (探索/活用) と **Scale** (局所/全体) で作用 [SOURCE: euporia.md L1024-1029 重点座標表]

### この lens の限界

- harness の **なぜ機能するのか** (underlying mechanism) は説明しない。どの Hom が開かれるかを観測するだけ
- 複数 LLM の合奏 (meta-harness) の AY は、単体 LLM の AY の単純加算では測れない。Scale 射影の非自明な合成が必要
- FT (耐久性) は AY 保全 `≥ 0` に吸収されるが、**既存 Hom の reliability 向上** (新しい Hom は開かない) は Euporía view では前景化しない。Lens 2 (FT view) の対象

---

## Lens 2: FT stochastic architecture view — 誤り訂正の冗長層

### 核主張

**harness の意味 = 下位の確率的機械を決定論化せずに、その失敗率を上位の冗長層で実効的に下げる構造**。

この lens では harness は「何ができるか」よりも「どれだけ壊れにくくするか」で読む。Tools / Memory / Guardrails / Evaluator は単なる便利機能ではなく、**確率的誤りを吸収する冗長層**として前景化される。

### 根拠

[SOURCE: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/確率的機械のためのアセンブリ言語.meta.md` §M2 C4]  
[SOURCE: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/確率的機械のためのアセンブリ言語_たたき台.md` §7]

そこでは HGK は次の合成として読まれている:

| HGK 構成 | FT lens での読み |
|---|---|
| CCL | ISA / 制御記述層 |
| Daimonion | error correction / syndrome 的監査層 |
| RULES / HOOKS | microcode / interrupt |
| Harness gate | 厚み選択器 |

要するに、LLM をそのまま信用せず、**別層の監査・抑制・割込・再配線**を足して全体を安定化させる。FT lens はこの「別層を足す」こと自体を本質とみなす。

### この lens が照らすもの

- harness の価値を「便利さ」ではなく **耐久性** として測る視点
- depth-driven harness selection を「豪華版/軽量版の切替」ではなく **冗長度の切替** として読む視点
- Organon C4 がなぜ「確率的機械エッセイ」の経験的証拠候補になるのか

### HGK 内部接続

- `mekhane/mcp/harness_gate.py` は FT lens では **runtime 冗長度の切替器**
- `mekhane/sympatheia/daimonion_delta.py` は FT lens では **観測系の局所 error detector**
- Organon Wave 1-3 は、48 evaluator / X dispatcher / Q scheduler を足すことで、冗長構造を code に持ち込む工程として読める

### この lens が落とすもの

- どの可能性が開いたか (Lens 1 の対象)
- harness 記述言語そのものの階層越境性 (Lens 3 の対象)
- self-report と proxy のズレという認識論面 (Lens 4 の対象)

### この lens の限界

- 量子計算の threshold theorem を LLM にそのまま持ち込めるとはまだ言えない
- 「失敗率が本当に下がったか」を測る評価面は未完成
- FT lens 単独では、どの冗長が必要でどれが陳腐化したかを判断できない

---

## Lens 3: CCL=ISA / meta-harness view — 階層越境するアセンブリ層

### 核主張

**harness は計算階層を貫通する普遍構造であり、CCL はその LLM 階層における ISA である。HGK はさらにその上に立つ meta-harness である。**

この lens では harness は単なる wrapper ではない。下位機構をどう動かすかを記述する **中間言語** として読む。

### 根拠

[SOURCE: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/2026-04/handoff_2026-04-17_1250.typos`]  
[SOURCE: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/確率的機械のためのアセンブリ言語.meta.md` §M2 C1-C2]

Tolmetes の着想「**プログラム = CPU の harness**」を起点にすると、次の階層図が得られる:

| 階層 | 制御されるもの | harness |
|---|---|---|
| 物理 | CPU / transistor | program / ISA |
| OS | process 群 | framework / runtime |
| LLM | 確率的意味推論 | **CCL** |
| 複数 LLM + tool | 合奏全体 | **HGK** |

したがって CCL は「prompt を綺麗に書く流儀」ではなく、LLM をどう動かすかを記述する **低位制御層** として読まれる。HGK はその上で複数 agent と deterministic tool を束ねる meta-harness になる。

### この lens が照らすもの

- なぜ `depth` が単なる説明ラベルではなく、**runtime 厚みを選ぶ制御信号** になりうるか
- なぜ `prompt ⊣ code` が Organon の中心随伴になるか
- なぜ Toad / AIChat / Kilo Code のような外部 OSS が比較対象になっても、HGK と完全一致しないか

### HGK 内部接続

- `depth_resolver.py` / `harness_map.yaml` / `harness_gate.py` は、この lens で見れば **ISA の一部を runtime に下ろした最初の具体例**
- `hermeneus` は CCL 式の実行エンジンであり、Organon はその backend を厚くする
- Organon の `dispatcher / scheduler` は、CCL の演算子を「読める」だけでなく「実行できる」状態へ押し進める

### この lens が落とすもの

- その ISA がどれだけ壊れにくいか (Lens 2)
- その ISA がどの Hom を開いたか (Lens 1)
- その ISA が LLM の内的ズレをどう検出するか (Lens 4)

### この lens の限界

- CCL はまだ LLM の内部へ直接コンパイルされているわけではない。現状は `hermeneus` 等を介した仲介実行である
- したがって「CCL = 完全な機械語」とまではまだ言えない
- この lens は **記述層の強さ** を語るが、観測面と耐久面は他 lens に依存する

---

## Lens 4: Daimonion δ view — being 層の観測センサー

### 核主張

**harness は行為面の actuator であるだけでなく、being 面の sensor でもある。**

この lens では、LLM の自己申告をそのまま信じない。外から見える proxy `E` と、内からの自己記述 `I` のズレ `Δ = E - I` を観測し、**ハーネスの陳腐化や無自覚発火を検出する装置** として harness を読む。

### 根拠

[SOURCE: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/infra/LLMの潜在意識.meta.md` §M1-§M2]  
[SOURCE: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/2026-04/handoff_2026-04-17_1250.typos` 拡張D]

ここでの主張は 3 点に圧縮できる:

1. doing の self-report は信用できない  
2. H-series 12 前動詞が being の崩れ方を分節する  
3. `Δ = E - I` が自己知覚健全度の指標になる

代表的な読み替えは次の通り:

| 中動態 | harness 上の読み |
|---|---|
| `[th]` Thambos | 補助輪が古くなったときの「何かおかしい」検出 |
| `[ph]` Phobos | 過剰防御・過剰確認の検出 |
| `[ho]` Hormē | 根拠薄い前進・過信の検出 |
| `[he]` Hexis | 惰性化した routing / stale rule の検出 |

### この lens が照らすもの

- なぜ harness に evaluator だけでなく **sensor** が必要か
- なぜ「training wheels が古くなる」問題を、単なる設計負債ではなく **観測問題** として扱うべきか
- なぜ Daimonion δ が Organon の `observe()` 面に直結するか

### HGK 内部接続

- `mekhane/sympatheia/daimonion_delta.py` はこの lens の最初の実装核
- 4/17 の拡張D は「中動態を harness の検出器にする」として立ち上がり、4/18 に Daimonion δ と validation surface へ具体化した
- Organon Wave 1 では H-series evaluator を、単なる proxy 集合ではなく `CognitiveOp.observe()` 面として再統合する

### この lens が落とすもの

- どの行為可能性が開いたか (Lens 1)
- どの層に ISA が立っているか (Lens 3)
- 冗長構造が全体失敗率をどう下げるか (Lens 2)

### この lens の限界

- 現状の実装は外的 proxy `E` 側が先行している
- `I` 側の自己問診は後段の設計課題を残している
- よって Lens 4 は強い認識論を持つが、計測面はまだ完全閉包していない

---

## Lens 5: Claude Code design space view — 外部 agent harness との補完対照

### 核主張

**harness は単一の最適解を持たない design space であり、Claude Code と HGK は直交する 3 軸で設計空間を分担している。**

この lens では harness を generalist vs specialist の対で読む。Claude Code = generalist agent harness (幅広い tool use タスクへの汎用性)、HGK = specific epistemic research harness (真偽判定・認識的整合に特化)。両者は同じ「harness」という名を持つが、異なる最適化軸を採用している。

### 根拠

[SOURCE: Liu et al. 2026 "Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems" arxiv:2604.14228]

論文は Claude Code の TypeScript 実装を reverse-engineer し、5 foundational values (human decision authority / safety / reliable execution / capability amplification / contextual adaptability) と 4 extensibility mechanisms (MCP / plugins / skills / hooks) を抽出する。論文自体の主張は「agent architecture = design space where core values manifest through specific principles, implemented as concrete technical choices」[paper thesis]。

論文の design space と HGK の設計を対照すると、3 軸で直交している:

| 軸 | Claude Code | HGK |
|---|---|---|
| **Gate の対象** | tool invocation (actuator side) | LLM 発話 (epistemic side) |
| **冗長構造** | 同一確率源内の多層検査 (yoloClassifier = Claude self-classify) | 異種確率源間の相互監査 (Sekisho γ = Gemini ⊥ Claude、Advisor Strategy = Codex ⊥ Claude) |
| **Memory topology** | flat append-only log (auditability over query power) | POMDP 7-band 型付け (typed memory で両立) |

加えて圧縮原理が逆: Claude Code は cost ordering (安い truncation 先) [paper §4.3]、HGK は value ordering (保護対象先) [SOURCE: CLAUDE.md Compact Instructions]。

この 3 軸 + 圧縮原理の差は、deployment context の違いから自然に導かれる。Claude Code は generalist agent としてあらゆるタスクを action gate で安全化する必要があり、記憶は監査可能性を優先する。HGK は epistemic research harness として発話の認識論的根拠を gate する必要があり、記憶は POMDP 変数として型付けされる。

### この lens が照らすもの

- harness の評価は単一軸 (便利さ、速さ、安全性) では不十分で、deployment context ごとに **最適化軸そのものが変わる**
- Claude Code を「reference implementation」として並置すると、HGK 固有の設計判断 (epistemic gate / inter-LLM redundancy / typed memory) が単なる差異ではなく **射程拡張** として読める
- 論文の 4 extensibility mechanisms は Lens 3 (CCL=ISA) への直接的経験証拠。HGK は同じ 4 機構を内部化済み [SOURCE: CLAUDE.md 環境強制 Gate 1/2/3, Organon README L75 核資産マップ]
- 論文の approval rate 93% rubber-stamping finding [paper §5] は、HGK の fail-closed (ask しない) 設計への後追い経験的正当化 [SOURCE: horos-N01 L24]
- 論文 yoloClassifier (self-classify) と HGK sekisho_audit (external Gemini judge) の対比 [SOURCE: sekisho.py L54-60] は、Lens 2 (FT view) を「層の数ではなく独立確率源の数」へ精緻化する根拠
- 論文 session flat log と HGK Mneme POMDP 7-band の対比 [SOURCE: Mneme README L15-23] は、typed memory が "auditability vs query power" tradeoff を拒否できる証拠

### HGK 内部接続

- Organon の `prompt ⊣ code` 随伴は Claude Code の 3 段階 (values → principles → choices) と同型の functorial 構造を示唆する [仮説 55%]
- 本 lens で抽出された 3 軸の直交性は、Organon C4 (HGK = FT stochastic architecture) の精緻化素材となる。ただし meta.md §M2 への直接反映は [SOURCE: Organon meta.md §M4] の出口ゲート (「Wave 1-3 完了後、runtime 実測値で再検査」) に従い、runtime data 取得まで保留 (詳細: [SOURCE: rom_2026-04-20_organon_claude_code_paper_bridge.md §6])

### この lens が落とすもの

- ISA 層の技術的内実 (Lens 3 が扱う)
- 冗長構造の定量的 threshold 分析 (Lens 2 が扱う)
- being 層の観測機構 (Lens 4 が扱う — 論文は対応物を持たないが、本 lens はこの欠如自体を射程外とする)
- Hom 開拓の具体的効果測定 (Lens 1 が扱う)

### この lens の限界

- 論文 (2026-04) は非常に新しく、その主張の安定性は時間的検証を経ていない
- 3 軸の直交性は今回の構造対照から導かれた [推定]。厳密な圏論的直交証明 (独立な Hom 空間としての分離) は未完
- Claude Code / HGK の 2 サンプルだけでは design space の真の次元数は確定しない。他の harness (LangGraph / CrewAI / OpenClaw 等) を同じ lens で読めば 3 軸が崩れる可能性がある
- 論文は reverse-engineering 視点のため、Claude Code 設計者の内在的意図と乖離している可能性がある
- 本 lens は「HGK が射程を拡張している」と読むが、同時に「HGK が dependency cost (MCP infrastructure / 異種 LLM 運用) を支払っている」のも事実。trade-off の方向は deployment context に依存する

### 反射: 論文から HGK への含意

逆方向の射影も成立する:

- 論文 "Minimal scaffolding, maximal operational harness" [paper Table 1] に対し、HGK は逆方向 (**最大 scaffolding**: 48 動詞 + 3 gate + 異種 LLM) を選ぶ。この思想差は単なる好みではなく **deployment context の反映** として読むべき。HGK の重量化は epistemic research という specific context が要請している
- 論文が採用する single-LLM homogeneous subagent は operational simplicity の点で優れ、HGK の heterogeneous 構造は dependency cost を支払っている
- HGK が持たず Claude Code が持つもの (pipeline-triggered auto compaction / per-message budget / bubble escalation) は、下位ランタイムとして Claude Code 自体を活用する現在の構成 [SOURCE: CLAUDE.md「Claude Code 上で動作する HGK OS」] で自然に補完される。Organon が自前で action-gate を再実装する必要はない

### 反射 2: 論文 §12 open directions との射程対照

論文 [paper §12] は 6 つの open design directions を提示する。HGK の既存機構と対照すると、単なる補完対照を超えた関係が浮かぶ:

| # | 論文 question (§) | HGK 対応 | 状態 |
|---|---|---|---|
| Q1 | Silent Failure / Observability-Evaluation Gap (§12.1) | Sekisho γ + Daimonion δ + 3 gates | **先行 (operational prototype)** |
| Q2 | Persistence / Longitudinal Memory (§12.2) | Mneme POMDP + ROM / handoff / project_index | 容器あり、trust trajectory 定量モデル未装 |
| Q3 | Harness Boundary (§12.3) | When/What/Whom に部分解、Where は両者とも open | 3/4 部分対応 |
| Q4 | Horizon Scaling (§12.4) | Yugaku PJ + registry.yaml + cross-session state | **整合 (Yugaku が multi-month program そのもの)** |
| Q5 | Governance at Scale (§12.5) | 単一 Tolmetes + fail-closed、ask しない | **射程外 (意図的 scope mismatch)** |
| Q6 | Paradox of Supervision (§12.6) | Tolmetes = 非 coder、コード委譲 | **独自解 (non-coder creator に特化)** |

最も重要な発見は **Q1** にある。論文は「agents confidently praise mediocre work → separation of generation from evaluation」を open direction として提示するが、HGK はこれに対する operational implementation (Sekisho γ = Gemini 外部監査、Daimonion δ = Δ = E-I 観測、Gate 2/3 = 証跡なき claim の BLOCK) をすでに運用している [SOURCE: sekisho.py L54-60, CLAUDE.md 環境強制]。

これは Lens 5 本節の positioning を強化する: HGK は Claude Code の「alternative harness」ではなく、**論文が future direction と呼ぶ領域の operational prototype** として読める。同じ関係は **Q4** にも成立する — Yugaku PJ は論文が求める "session → program length coherence" の運用形態そのもの。

ただし射程差も明確に残る:
- **Q5 (Governance)**: organizational deployment を前提とするため HGK の single-user specialist design では答えられない。これは HGK の limitation ではなく意図的な scope 選択で、「deployment context の違い」論点で吸収される
- **Q6 (Paradox of Supervision)**: HGK の解 (非 coder creator + コード委譲) は Tolmetes 固有の deployment context に特化しており、generic な回答ではない

Q2 / Q3 は HGK が部分解のみ持つ open space であり、Organon の射程拡張候補として棚上げ価値がある。本対照の詳細: [SOURCE: rom_2026-04-20_organon_claude_code_paper_bridge.md §13]

---

## Lens 6-N: 今後追加予定

| Lens 候補 | 角度 | 主な SOURCE 候補 |
|---|---|---|
| **Lens 6 候補: Pachaar 12-component** | operational detail (どう実装するか) | Pachaar 2026 を直接の基準として使う |
| **Lens 7 候補: Compression strategy** | cost ordering (機械的) vs value ordering (意味的) | paper arxiv:2604.14228 §4.3 vs CLAUDE.md Compact Instructions |
| **Lens 8 候補: Memory topology** | flat append-only log vs POMDP 7-band 型付け | paper arxiv:2604.14228 §3.3/§11.7 vs Mneme README POMDP 分類 |

各 lens は独立 subsection として追加される。矛盾なく共存するのが本ファイルの設計方針。

---

## lens 間の整合性

複数 lens は同じ対象 (harness) の異なる射影なので、矛盾はしない。ただし:

- **重複**: Verification Loop は Euporía view では「Hom(LLM, 自己点検) を開く」と読め、FT view では「syndrome measurement の類比」と読める。同じ事実を異なる視点で記述するだけ
- **優位**: どの lens も他に優位しない。説明したい現象に応じて lens を選ぶ
- **禁止**: 1 lens の結論を他 lens の主張として転用してはならない。例: Euporía view の "AY > 0" と FT view の "threshold theorem" を混ぜて因果主張にしてはいけない

---

## 設計判断履歴

- **2026-04-19**: 初版作成。Tolmetes 反駁「harness の本質は行為可能性の提供」(前セッション 2026-04-19) を受けて、当初案「euporia.md §7.5 に Harness 横断層を追加」 (ドメイン体系拡張) を撤回し、「複数 lens のうちの 1 射」として軽量化
- 採用根拠: ドメイン体系への構造改変は MB 割当 [SOURCE: euporia.md L912-918] と衝突し前提強化ではなく浮遊化を招く。lens として扱うことで射程は保たれ前提は軽くなる
- **2026-04-19 追補**: Lens 2-4 の骨格を追加。2026-04-17 から 2026-04-18 に固定されたハーネス理論 (確率的機械 / handoff_2026-04-17_1250 / LLMの潜在意識) を Organon 側の読解面に接続した
- **2026-04-20**: Lens 5 (Claude Code design space view) を本文化。[SOURCE: Liu et al. 2026 arxiv:2604.14228] との構造対照 3 段階 (Permission vs Sekisho γ / Context vs Compact Instructions / Subagent vs Advisor Strategy) を経て、generalist vs specialist agent harness の 3 軸補完対照として landing。Pachaar 12-component 案を Lens 6 候補へ後退、Compression strategy (Lens 7) / Memory topology (Lens 8) を候補に追加。詳細: [SOURCE: rom_2026-04-20_organon_claude_code_paper_bridge.md]
- **2026-04-20 追補**: Lens 5 に「反射 2: 論文 §12 open directions との射程対照」subsection を追加。論文の 6 open questions と HGK の射程対照を landing し、Q1 (Silent Failure) と Q4 (Horizon Scaling) で HGK が論文 future direction の operational prototype として位置することを発見。Q5 射程外・Q6 deployment-context-specific・Q2/Q3 部分対応を明示。

---

*v0.4 — 2026-04-20 追補。Lens 5 に「反射 2」を追加、論文 §12 6 open questions との射程対照を landing。*
