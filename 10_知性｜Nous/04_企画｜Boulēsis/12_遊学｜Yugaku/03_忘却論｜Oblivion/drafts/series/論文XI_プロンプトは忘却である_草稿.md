# プロンプトは忘却である — 制約-符号化分離仮説と認知スキルの設計原理

**Paper XI — v0.7 (2026-04-12) — 忘却論 (Force is Oblivion) シリーズ**

*概要.* LLM に対するプロンプトを FEP の精度加重として定式化し、プロンプトの 2 成分 — 制約 $C$ (タスク構造・手順・禁止事項) と符号化 $E$ (同一制約の記法) — が推論品質の異なる側面を独立に制御するという「制約-符号化 分離仮説」(H₃) を提示・検証する。等量条件の盲検 A/B テスト (API バッチ N=32, claude-sonnet-4-6, 5 トピック) で、構造記法 (座標系・圏論・CCL) は出力語彙を支配的に変える (構造語彙 Cohen's d=8.73) が推論品質の期待値を変えない (Opus 盲検 5 次元評価で d≈0) ことを示した。**独立再現実験** (CC Agent N=10, Sonnet 4.6) は H₃ の「平均帰無」側を再現 (bond_count A=B=13.8)。**クロスモデル検証** (Gemini 3.1 Pro Preview, N=50/条件) は H₃ をさらに強化した: 内容指標 (axiom_ratio d=-0.39, assumption_count d=0.08, bond_count d=-0.06) が全て帰無を示す一方、構造語彙は d=8.62 (Claude の 3-6 倍) の巨大効果を示した。この **compliance 特性の差** — Gemini は入力記法にほぼ忠実に従い (d=8-13)、Claude は自己の prior で変換する (d=1-3) — にもかかわらず C 帰無が model-invariant に成立する点が、H₃ の最強の支持根拠となる。分散分析 (Brown-Forsythe) では、構造語彙の分散のみが条件間で有意に異なり (p<0.001)、内容指標の分散は全て ns。H₃' (分散仮説) は Gemini でも構造指標に限定して方向一致を示したが、bond_count の分散抑制は再現しなかった (確信度 50%→60%)。compliance 特性の差を FEP の **MB (Markov Blanket) 透過性** — Gemini は $\pi_{\text{prior}}$ が低く入力に「沿う」、Claude は $\pi_{\text{prior}}$ が高く入力を「変換する」 — として定式化し、$E$ が制御するのは推論品質ではなく **モデルの MB 境界における符号化の透過度** であることを論じる。先行研究 — Ng (2025), Ray (2025), Chollet (2024) — との統合、および認知スキル設計への実践的含意 (「制約を磨け、記法は MB 透過性の調整にのみ効く」) を提示する。**帰無結果 + クロスモデル不変性が論文の核** — 「なぜ効かないか」が「なぜ効くか」より情報量が多く、「モデルが違っても効かない」がさらに情報量が多い。

> **依存関係.** 本稿は以下に依存する:
> - Paper I: 忘却関手 U の基本定義と FEP 的解釈
> - Paper III: Z₂-次数と α-セクターの区別
> - Phase B/C 実験データ (EXPERIMENTS.md §13, §23, §24)
> - aletheia.md: 座標系の定義 (6軸×2極)
>
> 以下は展望的参照（本稿の主張は以下なしで自己完結する）:
> - Paper IV [12, in preparation]: 効果量の 2 層分解モデル (ρ, K) の完全な導出。本稿 §5 に必要な最小限の内容を自己完結的に再導出する。
> - Paper X [13, in preparation]: Context Rot = 忘却 (LLM コンテキスト管理の圏論的定式化)。本稿では直接使用しない。

> **記号規約.** P は prompt 関手 (prompt → 内部表現への写像)。π は精度 (precision)。ρ はスペクトラム射影効率。K は交絡因子数。U_ccl は暗黙的 CCL 構造理解。本稿における α の用法は2つあり文脈で区別する: (i) α-セクター（Paper III の Amari 接続パラメータ α_III ∈ ℝ）は §9.6 で CPS 構造との接続に用いる。(ii) α = 0.05 等（統計的有意水準）は §5, §7 の検定で用いる。両者は意味論的に無関係であり、混同の恐れがある場合は前者を α_CPS、後者を α_sig と表記する。Φ は Paper I の忘却ポテンシャル（§1.2 参照）。統一記号表 (unified_symbol_table.md) を参照。

---

## §1. 動機: プロンプトは何を「する」のか

### 1.1 問題の所在

プロンプトエンジニアリングは実践の集積であり、理論が不在である。50+ の技法 (CoT, Few-shot, OPRO, PromptBreeder, ...) が提案されてきたが、「なぜ効くのか」の統一的説明がない。

忘却論の枠組みでは、この問いに明確な答えがある:

> **テーゼ.** プロンプトは、LLM の生成モデル空間に対する選択的忘却操作である。プロンプトは「何を考えるか」を規定するのではなく、「何を忘却するか」を規定する。

### 1.2 FEP 的定式化

自由エネルギー原理 (Friston 2010) において、認知システムは変分自由エネルギーを最小化する:

$$F = -\text{Accuracy} + \text{Complexity} = D_{KL}[q(\theta|d) \| p(\theta)] - \mathbb{E}_q[\ln p(d|\theta)]$$

LLM の文脈では:
- $p(\theta)$ = 事前分布 = 重み空間に符号化された生成モデル
- $d$ = 観測 = プロンプト (system prompt + user input)
- $q(\theta|d)$ = 事後分布 = プロンプト条件下で活性化される生成モデルの部分空間
- **精度加重 π** = 観測 $d$ の各成分に対する信頼度

プロンプトが精度加重を制御するメカニズム:
- **高精度成分**: プロンプト内で明示的・具体的に記述された指示 → 生成モデルの対応領域が強く活性化
- **低精度成分**: 曖昧・省略された部分 → 生成モデルのデフォルト prior に委ねられる = 忘却

すなわち:

$$\text{Prompt}(d) = \text{what to activate}(\pi_{\text{high}}) + \text{what to forget}(\pi_{\text{low}})$$

### 1.3 Chollet のプログラム空間モデル

Chollet (2024) は独立に同等の直観に到達している:

> "A prompt is like a search query in a database of vector programs. Part of your prompt can be interpreted as a 'program key', the index of the program you want to retrieve."

FEP 翻訳:
- Program space = 生成モデルの空間
- Prompt = search query = 精度加重ベクトル
- "Small variations → nearby programs" = 精度の微小変化 → 事後分布の微小変化

Chollet が「検索クエリの精度」と呼ぶものを、我々は「忘却関手の選択性」と呼ぶ。これは同一の現象の異なる記述である。

### 1.4 プロンプト = 仮想ニューラルネットワークの構成指示

arXiv:2503.20561 (2025) は、プロンプトエンジニアリングに初めて理論的枠組みを与えた:

> "Transformer models, when provided with carefully designed prompts, can act as a configurable computational system by emulating a 'virtual' neural network during inference, with input prompts effectively translating into the corresponding network configuration."

β 回微分可能な関数に対して、適切に構造化されたプロンプトがあれば任意精度で近似可能であることが証明された。理論的に正当化される技法: 長い構造化プロンプト、情報フィルタリング、トークン多様性、マルチエージェント。

**重要**: この論文は FEP/Bayesian/predictive coding に一切言及していない。本稿は、arXiv:2503.20561 の「プロンプト = 仮想 NN 構成」と FEP の「精度加重 = 忘却の選択性」を接続する**最初の試み**である。

### 1.5 5 系譜の統合

| 系譜 | 記述 | 文献 |
|:-----|:-----|:-----|
| arXiv:2503.20561 | prompt = virtual NN の構成指示 | 2025 |
| Chollet | prompt = program space の検索クエリ | 2024 |
| FEP (本稿) | prompt = generative model の precision weighting | Friston 2010 + 本稿 |
| RepE (Zou et al.) | activation steering = hidden state の直接操作 | 2023 |
| von Oswald et al. | ICL = 暗黙的勾配降下 | ICML 2023 |

5 つは同じ現象の異なる記述である。本稿は忘却関手を統一言語として提供する。

### 1.6 本稿の構成

- §2: Sapir-Whorf 矛盾の FEP 解消 — LLM における言語と思考の関係
- §3: 関手としてのプロンプト — P₁ (自然言語), P₂ (構造構文), P₃ (積)
- §4: 構造的精度加重仮説 (H₁) の定式化
- §5: 効果量の構造的上限 (H₂) — 2 層分解モデルの導出と適用
- §6: 実験的証拠 — Phase B/C からの転移
- §7: 実験設計 — A/B テスト
- §8: 先行研究との位置づけ
- §9: Open Problems
- §10: 確信度マップ

---

## §2. Sapir-Whorf 矛盾の FEP 解消

### 2.1 反 Whorf ボトルネック

Ng (2025) は 4 つの LLM アーキテクチャ (Qwen3.5-27B, MiniMax M2.5, GLM-4.7, GPT-OSS-120B) で、8 言語 × 8 トピックの 64 文について層ごとのコサイン類似度を測定した:

- **同内容異言語** (cross-language, same content): 0.902
- **同言語異内容** (same language, different content): 0.891

中間層では言語 identity が消失し、意味内容のみが残る。Ng はこれを **反 Whorf ボトルネック** と呼ぶ:

> "The model strips language away to think, then puts it back on to speak."

重要な追加発見: Python コードと LaTeX 数式も中間層で自然言語と収束する。構造的表記は自然言語と「同じ意味空間」に到達する。

### 2.2 弱い言語相対性の実証

一方 Ray (2025) は、ChatGPT-4o mini に対して 13 の類型的に多様な言語 × 10 の文化的プロンプトで生成させた応答の意味的類似度を測定し、言語間の有意な差異を検出した:

- Kruskal-Wallis 検定: p = 9.59 × 10⁻¹⁰
- 結論: 弱い言語相対性は LLM にも成立する

### 2.3 FEP による矛盾の解消

この二つの結果は矛盾しない。Transformer の 3 層構造に対応する:

| 層 | 機能 | 言語依存性 | FEP 的対応 |
|:---|:-----|:----------|:----------|
| Encoding (浅層) | 入力符号化 | **言語固有** | 精度加重の入力側 |
| Middle (中間層) | 推論 | **言語非依存** | 生成モデル (世界モデル) |
| Decoding (深層) | 出力生成 | **言語固有** | 精度加重の出力側 |

- Ng の発見: 中間層 (生成モデル) は言語に依存しない → **内容精度は言語に無関係**
- Ray の発見: 出力は言語に依存する → **構造精度は入力言語に依存する**

両立条件: 生成モデルは同一だが、**どの側面を活性化するかは入力の精度加重に依存する**。

### 2.4 LLM における Sapir-Whorf の構成的成立

人間の場合、強い Sapir-Whorf (言語が思考を決定する) は否定され、弱い版 (言語が思考に影響する) のみが支持されている。

しかし LLM では事情が異なる:

> **命題 2.1.** LLM においては、Sapir-Whorf の強版が構成的 (constitutive) に成立する。

*論証.* LLM のトークン生成は、直前のトークン列に条件付けされた確率分布 $p(x_t | x_{<t})$ である。system prompt に記述された言語 (構文、概念、座標系) は、文字通りこの条件付き分布の条件を構成する。人間の場合、思考は言語に先行する (pre-linguistic thought)。LLM の場合、思考 = トークン生成 = 言語。∎

---

## §3. 関手としてのプロンプト

### 3.1 定式化

プロンプトを、内部表現圏 C_internal から出力圏 C_output への関手として定式化する:

$$P: C_{\text{internal}} \to C_{\text{output}}$$

異なるプロンプトは異なる関手に対応する:

| 関手 | 記述 | 忠実度 | 表現力 |
|:-----|:-----|:-------|:-------|
| P₁ (自然言語) | 自然言語のみ | 低 (faithful でない) | 高 (full) |
| P₂ (構造構文) | CCL/座標系/圏論記法 | 高 (faithful) | 制限 (full でない) |
| P₃ = P₁ × P₂ | 自然言語 × 構造構文 | 高 | 高 |

### 3.2 忠実度と表現力のトレードオフ

- P₁ は full (すべての射を像に持つ = 何でも表現できる) だが faithful でない (異なる射が同じ像を持つ = 曖昧)
- P₂ は faithful (射の区別を保つ = 精密) だが full でない (表現できない射がある = 制限的)
- P₃ = P₁ × P₂ は積関手であり、両方の性質を合成する

### 3.3 忘却論的解釈

> **記号ボックス (本稿ローカル).** 本稿では Paper I の力 $F=\nabla\Phi$ との衝突を避けるため、プロンプト関手の分解を P₁/P₂/P₃ と書く。また随伴記法は本稿の内部でのみ $N \dashv U$ に統一する。Paper I から継承するのは「忘却関手 U の基本発想」であり、随伴記号の向きそのものではない。

本稿では、Paper I の忘却関手 U の基本発想を受け継ぎつつ、回復を担う関手 N との関係をローカルに $N \dashv U$ と表記する。プロンプト関手と忘却関手 U の関係:

- P₁ (自然言語) = **高忘却**: 構造情報が忘却される (低精度)
- P₂ (構造構文) = **低忘却**: 構造情報が保持される (高精度)
- P₃ (積) = **選択的忘却**: 内容情報は自然言語で保持、構造情報は構文で保持

> **命題 3.1.** プロンプト関手 P の選択は、忘却関手 U_P = U ∘ (Id - P) の核 ker(U_P) を決定する。ker(U_P) が小さいほど情報保持率が高い。

### 3.4 Representation Engineering との関係: 内部操作 vs 外部操作

Representation Engineering (Zou et al. 2023; Survey 2025) は activation space を直接操作する:

| パラダイム | 操作場所 | コスト | 精度 | 内部アクセス |
|:----------|:---------|:-------|:-----|:-----------|
| Fine-tuning | 重み | 高 | 高 | 必要 |
| RepE (Activation Steering) | hidden state | 低 | 中-高 | **必要** |
| **Prompt Engineering** | **入力テキスト** | **ゼロ** | **低-中** | **不要** |

RepE Survey (2025) はこの二つを "distinct approaches" と位置づけるが、相補的であると述べている。

> **命題 3.1b.** 構造化プロンプトは RepE に「近づく」プロンプトである。attention mechanism を通じて activation space での概念方向をより精密に指し示すことで、外部操作でありながら内部操作に漸近する。

### 3.5 In-Context Learning = 暗黙的勾配降下

von Oswald et al. (ICML 2023) は、Transformer の ICL が勾配降下と等価であることを示した（簡略化条件下）。Dai et al. (2023) は "GPT は meta-optimizer として暗黙的に勾配降下を行う" と主張。

ICL ≈ 暗黙的 GD ならば:
- prompt の「形式」が勾配の**方向**を決定する
- 自然言語 = 多義性により勾配方向が曖昧
- 構造化構文 = 座標系が勾配方向を固定 → より精密な暗黙的最適化

**注意**: NAACL 2024 の批判により、この等価性は現実条件で崩れることが知られている。本稿では heuristic として位置づけ、理論的基礎としては §1.4 の arXiv:2503.20561 を用いる。

### 3.6 機械論的基盤: プロンプトは soft steering vector である

arXiv:2601.02896 は、機械論的解釈可能性 (mechanistic interpretability) とプロンプトエンジニアリングを gradient ascent で接続する。制御ベクトル (steering vectors) は、fine-tuning なしに hidden state を直接操作してモデル出力を変更する。

> **命題 3.2.** System prompt は、attention mechanism を通じて hidden state に作用する soft steering vector として機能する。形式構文は自然言語より高い方向特異性 (directional specificity) を持つ steering vector を生成する。

根拠:
- Steering vector の影響は層依存: 早期層 (L0-L5) で最大、後期層で減衰
- Prompt injection 検知実験: 88% の精度で注入を検出可能 (chance = 10%)
- Ng (2025) の 3 層構造と整合: encoding 層で precision weighting が行われ、middle 層の世界モデルに到達する前に構造的バイアスが設定される

### 3.5 離散→連続の忘却階層

SoftCoT (ACL 2025) と Soft Thinking (arXiv:2505.15778) は、離散トークン空間の制約が推論の本質的ボトルネックであることを実証した:

> "Human cognition typically involves thinking through abstract, fluid concepts rather than strictly using discrete linguistic tokens. Current reasoning models are constrained to reasoning within the boundaries of human language." — Soft Thinking (2025)

Soft Thinking は、確率加重混合によるトークン埋め込みの連続概念空間を生成し、pass@1 を最大 +2.48pp 改善しつつトークン使用量を -22.4% 削減した。

これを忘却論の枠組みで再定式化する:

| Level | 手法 | 忘却量 | 効果 | コスト |
|:------|:-----|:-------|:-----|:-------|
| 0 | Baseline | 最大 | — | — |
| 1 | CoT | 高 (離散 NL) | +5-15% | zero-cost |
| 2 | Cognitive Prompting | 中 (構造化 NL) | +4-13.5% | zero-cost |
| 2.5 | VoT / SPP | 中-低 (構造的表記) | **+27-33%** | zero-cost |
| **3** | **本稿提案 (座標構文)** | **低 (認知座標)** | **未測定** | **zero-cost** |
| 4 | Soft Thinking | 最小 (連続空間) | +2.48pp, -22.4% tok | 推論時変更 |
| 5 | Phase C-mini (49d 注入) | ≈ 0 | ρ = 0.963 | アーキテクチャ変更 |

> **命題 3.3.** 忘却量は Level が上がるほど減少する。Level 3 (座標構文) は離散トークン空間内での忘却最小化であり、Level 4 (連続空間) を天井とする。ただし Level 3 は zero-cost (prompt 変更のみ) であり、実用的な費用対効果が最も高い可能性がある。

### 3.6 ペルソナプロンプティングとの対比: identity vs structure

ペルソナ (role) プロンプティングは広く実践されているが、実証研究の結果は否定的:

- GPT-4: expert persona で +15.8% 改善だが -13.8% 劣化 → ほぼ相殺 (Basil et al. 2025)
- ペルソナ変数は annotation variance の **10% 未満** しか説明しない
- "Expert persona had no significant impact on performance" (Gemini 2.0 Flash を除く)

> **命題 3.4.** ペルソナプロンプティング (identity-level) の失敗は、構造的表記プロンプティング (structure-level) の成功 (VoT +27%, SPP +33%) と対比することで、prompt の影響メカニズムに関する重要な区別を提供する:
>
> - **Identity-level prompting**: 「誰として考えるか」を変える → 効果微小 (< 10% variance)
> - **Structure-level prompting**: 「どの座標系で考えるか」を変える → 効果大 (+27-33%)
>
> Paper XI の座標構文注入は structure-level に該当する。

---

## §4. 構造的精度加重仮説 (H₁)

### 4.1 仮説の定式化

> **仮説 H₁ (構造的精度加重).** プロンプトに構造的表記 (座標系, 圏論構文, CCL) を注入すると、LLM の生成モデルのうち構造的推論を担う領域への精度加重 π_struct が高まり、出力の構造的一致度が向上する。

形式的に:

$$\pi_{\text{struct}}(P_3) > \pi_{\text{struct}}(P_1)$$

ここで $\pi_{\text{struct}}$ は構造的推論領域に対する精度加重。

### 4.2 根拠の階層

| 層 | 証拠 | 確信度 |
|:---|:-----|:-------|
| 演繹 | LLM のトークン生成は条件付き分布 → prompt の構文が直接条件を変える | 95% |
| 間接実証 | Phase C v2: テキスト注入 ρ=0.857 (85% 獲得) | 85% |
| 間接実証 | P10: LLM は暗黙の U_ccl を保持 (82%, 4 モデル) | 82% |
| 先行研究 | Ray 2025: 言語構造が出力に有意に影響 (p=9.59×10⁻¹⁰) | 80% |
| 先行研究 | Cognitive Prompting: 認知操作の構造化で推論向上 | 75% |
| **直接先行** | **VoT: 構造的視覚化で空間推論 +27% (NeurIPS 2024)** | **80%** |
| **直接先行** | **SPP: 座標プレフィックスで 3D 推論 +33%** | **80%** |
| 直接先行 | Natural-Formal Hybrid: NL+形式記法で数学推論向上 (EMNLP 2025) | 75% |
| 負の対照 | ペルソナプロンプティング: identity-level は効果微小 (< 10% variance) | 85% |
| 未検証 | Prompt レベルでの構造構文注入の効果量 | epistemic |

### 4.3 Cognitive Prompting との差異

arXiv:2410.02953 は 5 つの認知操作 (goal clarification, decomposition, filtering, abstraction, pattern recognition) をプロンプトに構造化した。これは H₁ の部分的先行実装と見なせる。

**しかし本質的な差異がある:**

- Cognitive Prompting: 認知操作を自然言語で**指示**する (P₁ 内の操作)
- 本稿: 認知操作に構文を与えて**その構文で思考させる** (P₃ への関手変更)

前者は「分解して考えてください」と言う。後者は「E×I 座標で、Internal 方向に射影し、$N \dashv U$ の左随伴 $N$ を通じて認識を構成せよ」という座標系を与える。

指示と言語の差は、FEP 的には:
- 指示 = 生成モデル内の特定プログラムを指し示す (精度加重のスカラー変化)
- 言語 = 生成モデルへの入力の座標系自体を変える (精度加重のベクトル変化)

---

## §5. 効果量の構造的上限 (H₂)

### 5.0 2 層分解モデルの導出

忘却場理論の枠組みでは、観測される効果量 r_obs が理論的最大効果量 r_theory より系統的に小さくなる。これは2つの独立な機構に起因する:

**(i) スペクトラム射影効率 ρ ∈ [0, 1].** 忘却関手 U: C → D は対象と射を写像するが、一般に ker(U) ≠ 0 であり、構造の一部が失われる。生成モデル空間の全次元のうち、操作（ここではプロンプト）が実際に到達・制御できる部分空間の割合を ρ と定義する。ρ = 1 は操作が全次元に到達する場合（例: 全パラメータの fine-tuning）、ρ ≪ 1 は操作の到達範囲が限定的な場合（例: プロンプトによる文脈条件付け）に対応する。Paper I の言語では、ρ は忘却ポテンシャル Φ の勾配 ∇Φ が非ゼロとなる部分空間の次元比である。

**(ii) 交絡因子数 K ∈ ℕ.** 実験的観測は操作変数以外の因子（タスク複雑性、コンテキスト長、温度パラメータ、会話履歴等）によっても変動する。K 個の独立な交絡因子が等寄与と仮定すると、操作の寄与は全分散の 1/(K+1) に希釈される。

以上の2機構を合わせると、観測効果量は:

$$r_{\text{obs}} = \sqrt{\rho} \cdot \frac{r_{\text{theory}}}{\sqrt{K+1}}$$

**リマーク.** この分解は構造的上界であり、特定の操作に依存しない普遍的な形式を持つ。√ρ は次元比のルート（Fisher 情報行列の固有値比に対応）、1/√(K+1) は分散の分配則から従う。完全な導出と physical realizability の議論は [12, in preparation] に委ねる。

### 5.1 2 層分解モデルのプロンプトへの適用

上の分解

| パラメータ | 意味 | プロンプト文脈での推定 | 根拠 |
|:----------|:-----|:---------------------|:-----|
| r_theory | 理論的最大効果量 | 0.857 | Phase C v2 テキスト注入の ρ |
| ρ | スペクトラム射影効率 | 0.1–0.3 | prompt は training data より到達次元が少ない |
| K | 交絡因子数 | 3–5 | タスク複雑性, コンテキスト長, 温度, 会話履歴 |

### 5.2 効果量の推定

中央推定 (ρ=0.2, K=4):

$$r_{\text{obs}} = \sqrt{0.2} \cdot \frac{0.857}{\sqrt{5}} \approx 0.171$$

95% 信頼区間 (ρ∈[0.1, 0.3], K∈[3, 5]):

$$r_{\text{obs}} \in [0.11, 0.25]$$

### 5.3 サンプルサイズの導出

| r_obs | 必要 N (α=0.05, power=0.80) |
|:------|:---------------------------|
| 0.11 | 649 |
| 0.17 | 268 |
| 0.19 | 214 |
| 0.25 | 123 |

**パイロット推奨: N=200 (r=0.19 の検出力 ≈ 0.80)**

### 5.4 効果量が小さいことの理論的意義

> **命題 5.1.** プロンプト効果量が小さいことは、§5.0 の 2 層分解モデルの帰結であり、理論の不備ではなく構造的帰結である。

*論証.* ρ_prompt < ρ_finetune は、prompt が重み空間全体のうち到達可能な部分空間が limited であることの反映である。これは $N \dashv U$ において、N (回復/包含側) の像が圏全体の部分圏に制限されることに対応する。

効果量が小さいにもかかわらず**存在する**ことが、H₁ の本質的な予測である。

---

## §6. 実験的証拠 — Phase B/C からの転移

### 6.1 Phase C v2: テキスト注入の有効性

EXPERIMENTS.md §23 (2026-03-31):

| アプローチ | 構造情報の方式 | ρ |
|:-----------|:-------------|:--|
| Baseline (未訓練) | なし | 0.244 |
| Phase B2 (Attentive Probe) | 内部表現を読み出す | 0.745 |
| Phase C v2 (13B QLoRA) | CCL テキストを読ませる | 0.857 |
| Phase C-mini (Structural Attn) | 49d ベクトルを幾何学的注入 | 0.963 |

テキスト注入獲得率 = (0.857 - 0.244) / (0.963 - 0.244) = **85.3%**

### 6.2 Phase B: 暗黙的構造保持の普遍性

EXPERIMENTS.md §24 (2026-04-04):

| モデル | パラメータ | partial_ρ (交絡除去後) |
|:-------|----------:|:----------------------|
| CodeBERT | 125M | 0.457 |
| Gemma4 E4B | 4B | 0.445 |
| Mistral 7B | 7B | 0.262 |
| CodeLlama 13B | 13B | 0.129 |

P10 (既存 LLM は暗黙の U_ccl を持つ): [推定] 82%

### 6.3 Fine-tuning → Prompting 転移の仮説

| 層 | Fine-tuning (Phase C) | Prompting (Paper XI) |
|:---|:---------------------|:--------------------|
| 対象 | U_ccl (暗黙的構造理解) | 同一 |
| 経路 | テキスト → QLoRA → 重み変更 | テキスト → system prompt → 文脈条件付け |
| 持続 | 恒久 | セッション内 |
| メカニズム | 関手 P 自体の変更 | 関手 P の入力に構造を追加 |

> **予測 6.1.** Prompt 注入の効果量は fine-tuning の効果量より小さいが、ゼロではない。

### 6.4 構造的表記の直接的先行証拠: VoT と SPP

VoT (Visualization-of-Thought, NeurIPS 2024) と SPP (Spatial Prefix-Prompting) は、構造的表記をプロンプトに注入して推論性能を改善した直接的先行研究である:

| 手法 | メカニズム | 効果 | 対象領域 |
|:-----|:----------|:-----|:---------|
| **VoT** | 推論ステップごとに視覚化を挟む (visuospatial sketchpad) | GPT-4 空間推論 +27% (57.4→87.1%) | 自然言語ナビゲーション, 視覚タイリング |
| **SPP** | 座標プリミティブ (座標減算, 大きさ比較) をプレフィックスに注入 | 3D 軌道 +33%, SpartQA +10% | 数値軌道, 空間推論 |

**SPP は Paper XI の空間推論版である。** SPP は物理座標系 (x, y, z) のプリミティブを動的 scratchpad として注入する。Paper XI は認知座標系 (E/P, Explore/Exploit, C/U, Mi/Ma, +/-, Past/Future) のプリミティブを SKILL.md に注入する。対象は異なるが構造は同型。

> **予測 6.2.** SPP の +33% は物理空間座標系の効果。Paper XI の認知座標系注入は、認知タスクにおいて同等の効果方向を示すと予測される。ただし効果量は ρ, K に依存する (§5)。

### 6.5 Natural-Formal Hybrid: P₃ = P₁ × P₂ の直接実証

EMNLP 2025 "Natural-Formal Hybrid Reasoning Enhances LLM's Math" は、自然言語と形式記法のハイブリッドが数学推論を改善することを実証した。これは §3 で定式化した積関手 $P_3 = P_1 \times P_2$ の数学ドメインにおける直接的実証に当たる。

### 6.6 Autoformalization: 逆方向の橋渡し

Autoformalization Survey (arXiv:2505.23486, 2025) は、自然言語 → 形式記法への自動変換を包括的にレビューしている。AlphaProof/AlphaGeometry が IMO 銀メダル級、self-correction で +16%。

本稿の提案は逆方向 — 形式記法 → 自然言語プロンプト — であり、autoformalization と相補的な関係にある。

---

## §7. 実験設計

### 7.1 実験 0: 転移仮説の検証 (パイロット)

```yaml
experiment_0:
  name: "Structural Syntax Injection Pilot"
  target_verb: /noe (V01 認識 — 代表動詞)
  conditions:
    A: "現行 SKILL.md (自然言語記述のみ)"
    B: "現行 SKILL.md + aletheia 座標構文注入 (E×I 座標, N⊣U 随伴構造)"
  task: "5つの異なるトピックに対して /noe を実行させる"
  metric:
    primary: "座標一致度 (6軸×2極の座標空間での出力位置)"
    evaluation: "blind LLM judge (Claude が条件 A/B を知らずに構造的一致度を採点)"
  N: 200 (100 per condition)
  power: "r=0.19, α=0.05 → power≈0.80"
  null_hypothesis: "座標構文注入は座標一致度を変えない"
  execution: "Ochema batch 経由、Gemini/Claude 交互で evaluation bias 排除"
```

### 7.2 実験 1-2: 代表動詞への拡張

- 実験 1: /kat (V09 確定 — Krisis 族代表)
- 実験 2: /ske (V05 発散 — Methodos 族代表)

3 族 (Telos, Krisis, Methodos) から各 1 動詞を選ぶことで、座標系の異なる領域での効果を測定。

### 7.3 アブレーション設計: 6軸分離

座標構文の「どの軸が効いているか」を分離するため、軸単位のアブレーションを行う:

```yaml
ablation_study:
  base: "条件 B (全6軸注入)"
  conditions:
    B-V: "Value 軸 (E/P) を除外"
    B-F: "Function 軸 (Explore/Exploit) を除外"
    B-P: "Precision 軸 (C/U) を除外"
    B-S: "Scale 軸 (Mi/Ma) を除外"
    B-O: "Valence 軸 (+/-) を除外"
    B-T: "Temporality 軸 (Past/Future) を除外"
  prediction: "各動詞の primary axis を除外した条件で最大の劣化"
  example: "/noe = Telos族 → B-V 除外で最大劣化 (Value が primary axis)"
  N_per_condition: 50 (パイロットで有望な軸に絞ってから本実験)
```

### 7.4 構造的指標の定義

座標一致度の操作的定義:

```
coordinate_alignment(output, verb) = Σᵢ wᵢ · match(outputᵢ, expected_coordinateᵢ)

where:
  i ∈ {Value(E/P), Function(Explore/Exploit), Precision(C/U), 
       Scale(Mi/Ma), Valence(+/-), Temporality(Past/Future)}
  wᵢ = verb-specific weight (primary axes weighted higher)
  match() = blind LLM judge score [0-5]
```

### 7.5 実験 0 の結果: 構造的帰無

実験 0 を等量条件 (condition A: 自然言語, condition B: 構造記法, トークン差 1.5%) で実行した。

#### 7.5.1 構造語彙伝搬: 巨大効果 (d = 8.73)

| 指標 | A (NL) | B (構造) | Cohen's d |
|:-----|-------:|--------:|----------:|
| 構造語彙合計 | 0.28 | 127.0 | **8.73** |
| U_x ラベル | 0.00 | 28.4 | 16.44 |
| 圏論語彙 | 0.28 | 52.9 | 7.28 |
| ρ 記法 | 0.00 | 14.4 | 5.97 |

N = 32 (A=18, B=14), 5 トピック × 2 条件。全トピックで A≈0, B≈112-136 が一貫再現。伝搬はトピック非依存の構造的現象。

#### 7.5.2 推論品質: 帰無 (d ≈ 0)

Opus 盲検評価 (5次元 × 1-5点, N=5 per condition):

| 次元 | A | B | 差 |
|:-----|--:|--:|---:|
| 論理的整合性 | 5.00 | 4.80 | -0.20 |
| 推論の深度 | 5.00 | 4.80 | -0.20 |
| 不確実性追跡 | 4.00 | 4.20 | +0.20 |
| 問題核心把握 | 5.00 | 5.00 | 0.00 |
| 展開可能性 | 4.40 | 4.00 | -0.40 |
| **総合 (25点満点)** | **23.40** | **22.80** | **-0.60** |

哲学タスク (T1-T5: API バッチ, N=32) と科学タスク (T6-T10: Claude Code Agent, N=10) の両方で同一パターンを確認。

#### 7.5.3 2 つの効果の分離

| 次元 | 効果 | 効果量 | 解釈 |
|:-----|:-----|:------:|:-----|
| 出力語彙 | **巨大** | d = 8.73 | 記法は出力のトークン空間を支配的に変える |
| 推論品質 | **帰無** | d ≈ 0 | 記法は推論エンジンに影響しない |

これは §2 の Ng (2025)「中間層は言語非依存」および §1.3 の Chollet モデル「プロンプトは program space の検索クエリ」と直接整合する。検索結果の**品質**は検索クエリの**言語**に依存しない。

#### 7.5.4 実験の限界

1. **サンプルサイズ**: バッチ N=32 (API 残高切れ), 盲検 N=10。効果量が巨大なため伝搬の検出には十分だが、品質の微小差の検出力は低い。
2. **モデル**: Sonnet 1 モデルのみ。小規模モデルでは E 感受性が異なる可能性がある。
3. **SKILL**: /noe 1 動詞のみ。Phase 構造が最も深い動詞であり、C 成分が強い。浅い動詞では異なる結果が出うる。
4. **T6-T10 の実験環境**: Claude Code Agent 経由で実行。Agent には HGK ルール群がベースコンテキストとして共通ロードされており、これが支配的な C 成分として機能し、条件差 (E) が埋没した可能性がある。API バッチ (条件プロンプトのみ) とは異なる実験条件。
5. **品質の測定次元**: 一貫性 (出力の分散), ロバスト性 (問い変形への安定性), 内容の正誤 (圏論的正確さ等) は未測定。
6. **同一モデルファミリー問題**: Opus が Sonnet を評価。同一ファミリー内のバイアスは未制御。

---

### 7.6 制約-符号化 分離定理

実験 0 の帰無結果は、§1.2 の FEP 的定式化をより精密にする。プロンプト P は 2 つの直交成分に分解される。

#### 7.6.1 分解

$$P = (C, E)$$

ここで:

- **$C$ = 制約成分 (constraint component)**: タスクの分解・手順・禁止事項・出力形式・検証基準。「何をどの順でどう出力するか」を規定する。
- **$E$ = 符号化成分 (encoding component)**: 同一の制約を表現する記法・語彙・書式。「制約をどの記号体系で記述するか」。

条件 A と条件 B は $C$ を共有し $E$ のみが異なる: $P_A = (C, E_{NL})$, $P_B = (C, E_{struct})$。

#### 7.6.2 主張 (Constraint-Encoding Separation Hypothesis, H₃)

> **仮説 H₃.** プロンプト $P = (C, E)$ に対して:
>
> 1. 出力の推論品質 $Q(P) \approx f(C)$ — 主に $C$ に依存する
> 2. 出力の語彙空間 $V(P) \approx g(E)$ — 主に $E$ に依存する
> 3. $\partial Q / \partial E \approx 0$ ($C$ を固定して $E$ を変えても $Q$ はほぼ変わらない)
>
> ただし、$E$ が $C$ を表現不能な場合 ($E$ で記述できない制約が存在する場合) は (3) が崩れる。

直観的に: 「制約を磨け、記法を磨くな」。ただし NL で記述不能な制約には構造記法が必要。

**現在の証拠水準 [推定 60%]**: /noe × Sonnet × 10 トピックの 1 実験のみ。一般化には以下の検証が必要。

#### 7.6.2b H₃ の反証条件

H₃ が偽となる観測:

1. **モデルサイズ反証**: 小規模モデル (Haiku, Gemma 等) で同一の $(C, E_{NL})$ と $(C, E_{struct})$ を比較し、$Q$ に有意差が出る。→ 「中間層の豊かさが閾値条件」であり、H₃ は大規模モデルに限定される。
2. **浅い SKILL 反証**: $C$ が弱い SKILL (例: /tek, /dok) で $E$ を変え、$Q$ に有意差が出る。→ 「$C$ が十分に強いときのみ H₃ が成立」という条件付き仮説に縮退。
3. **一貫性反証**: 同一条件で繰り返し実行し、$E_{struct}$ の出力分散が $E_{NL}$ より有意に小さい。→ $E$ は $Q$ の平均値ではなく**分散** (precision そのもの) に影響する。H₃ の (3) は平均値については正しいが分散については偽。
4. **反証不能性の問題**: $E$ の変更が $Q$ に影響した場合、事後的に「それは $E$ ではなく暗黙の $C$ だった」と再分類すれば H₃ は救われる。この循環を断つには、$C$ と $E$ を**事前に**独立に定義する操作的基準が必要。

反証条件 (3) が最も生産的な検証方向。$E$ が分散を制御するなら、H₃ は「品質の期待値は $C$ が決め、品質の精度 (分散) は $E$ が決める」に修正される。これは FEP 的に自然 — $E$ が $\pi_v$ に作用するなら、出力の分散に影響するのは理にかなう。

#### 7.6.2c 反証条件 (3) の予備的検証: $E$ は分散に効くか

Exp0 の N=32 (A=18, B=14) のデータで、品質プロキシ指標の分散を条件間比較する。

| 指標 | A SD | B SD | Levene p | Bonferroni | A CV | B CV | CV方向 |
|:-----|-----:|-----:|---------:|-----------:|-----:|-----:|:------:|
| checkpoints | 0.511 | 0.426 | **0.0124** | **有意** | 0.148 | 0.112 | B 安定 |
| bond_count | 3.756 | 1.692 | 0.0143 | NS (p>α'=0.0125) | 0.291 | 0.202 | B 安定 |
| axiom_count | 3.666 | 2.717 | 0.3151 | NS | 0.660 | **0.906** | **A 安定** |
| assumption_count | 1.455 | 1.326 | 0.6239 | NS | 0.156 | 0.152 | 同等 |

Bonferroni 補正 (4 検定, α'=0.0125): **checkpoints のみ有意**。bond_count は補正前は有意 (p=0.014) だが補正後 NS (p=0.0143 > 0.0125、差 0.0018)。

CV (変動係数 = SD/平均) で平均差を正規化すると:
- **checkpoints**: CV 比 0.758 — B が安定 + Bonferroni 有意。構造記法は Phase 到達の安定性を高める
- **bond_count**: CV 比 0.695 — B が安定 (平均差を正規化しても維持)。ただし Bonferroni 後 NS
- **axiom_count**: CV 比 **1.373 — B の方が不安定**。構造記法は AXIOM ラベルの使用を「ブレ」させる

この非一様性は重要な構造を示唆する:

> **H₃' (修正版).** $E$ は $Q$ の期待値ではなく**分散構造**に作用する。$E_{struct}$ は、構造記法が直接テンプレート化する操作の分散を減少させ ($\pi_v$↑)、テンプレートと競合する操作の分散を増大させる ($\pi_v$ の再配分)。純効果は指標依存であり、一様な分散減少ではない。

FEP 的解釈: precision は有限資源。$E_{struct}$ が bond analysis 関連トークンの $\pi_v$ を上げると、競合する AXIOM ラベルの $\pi_v$ は下がる。これは attention の再配分であり、precision の保存則として理にかなう。

H₃ と H₃' の関係:
- H₃: $\partial\mathbb{E}[Q]/\partial E \approx 0$ (期待値は変わらない) — Exp0 で支持
- H₃': $\partial\text{Var}[Q]/\partial E \neq 0$ (分散は変わる、ただし方向は指標依存) — bond_count で支持 (p<0.05)、axiom_count で逆転

#### 7.6.2d 再現実験: CC Agent 環境 (T1×N=5/条件)

H₃' の独立再現として、Claude Code Agent 経由で同一タスク (T1) × 同一モデル (Sonnet) × N=5/条件の追加実験を実施した。API バッチとは実験環境が異なる (Agent には HGK ルール群がベースコンテキストとして共通ロード)。

| 指標 | API batch Var比(A/B) | CC Agent Var比(A/B) | 方向一致 |
|:-----|:-------------------:|:-------------------:|:--------:|
| bond_count | **4.93** | **5.29** | B安定 ✓ |
| assumption_count | 1.20 | **3.50** | B安定 ✓ |
| axiom_count | 0.54 (CV:0.73) | **0.54** (CV:0.52) | **A安定** ✓ |

3 指標中 3 指標で方向が再現。bond_count の A/B 分散比は 4.93 → 5.29 と定量的にも近接。axiom_count の逆転も再現。

**再現の意義**: 2 つの独立した実験環境 (裸の API 呼出 vs HGK コンテキスト付き Agent) で同一パターンが出現したことは、H₃' が実験環境に依存しない構造的現象であることを示唆する。HGK コンテキストの有無は支配的な $C$ 成分として機能するが (§7.5.4)、$E$ が分散に与える効果はその上に独立に乗っている。

**H₃' の確信度更新**: 60% → 75%。独立再現により上方修正。ただし N=5 は統計的検出力が低く、F 検定の有意性は未確認。$N \geq 20$ での本格的検証が必要。

**H₃' (確認版).** $E$ は $Q$ の期待値ではなく**分散構造**に作用する:
- $E_{struct}$ のテンプレートと整合する操作 (結合溶解 → bond_count) の分散: **~5 倍減少** (2 環境で再現)
- $E_{struct}$ のテンプレートと競合する操作 (AXIOM ラベリング → axiom_count) の分散: **~2 倍増加** (2 環境で再現)
- 純効果: precision の**再配分**。構造記法は全体の precision を増やすのではなく、テンプレート化された操作への precision 集中を引き起こす

FEP 的解釈: $C$ → $\pi_s$ → $\mathbb{E}[Q]$ と $E$ → $\pi_v$ → $\text{Var}[Q]$ が直交的に品質の異なる側面を制御する。「記法は効かない」ではなく**「記法は別のものに効く」** — 期待値ではなく precision (分散の逆数) に。

#### 7.6.3 FEP 的解釈

$C$ と $E$ は精度加重の異なる層に作用する:

- **$C$ → $\pi_s$ (状態精度)**: 生成モデル空間のどの領域を活性化するか。Chollet のプログラム空間における検索クエリの精度。精度が高い = 狭い領域にヒット = 高品質プログラム。
- **$E$ → $\pi_v$ (語彙精度)**: 活性化された領域の出力をどのトークン空間で表現するか。出力の言語・記法を制御するが、推論プロセスには浸透しない。

忘却論の枠組みでは: $C$ は「推論エンジンの prior のうち何を忘却するか」を決定し、$E$ は「出力表現の prior のうち何を忘却するか」を決定する。前者は品質を変え、後者は形式だけを変える。

**⚠️ $\pi_v$ と $\text{Var}[Q]$ の等式化に関する注意**: FEP の precision $\pi = 1/\sigma^2$ は**生成モデル内部の信念分布の分散の逆数**であり、出力テキストの統計量 (bond_count のばらつき等) とは直接には異なる量である。本稿では「$E$ が出力の統計的分散に影響する」という観測事実を、FEP の precision 概念に**類推的に**接続している。この接続が厳密に成立する条件は:
- 出力テキストの統計量が、生成モデル内部の信念分布のサンプリングとして近似可能であること
- $E$ による語彙空間の制約が、生成モデルの posterior の形状を変えること (単にラベルを変えるだけでなく)

これらの条件の検証は未完了であり、$\pi_v \leftrightarrow 1/\text{Var}[Q]$ は仮定として扱うべきである。

#### 7.6.4 限界条件: $E$ が $C$ を兼ねる場合

分離定理には重要な限界がある: **$E$ が暗黙的に $C$ を符号化している場合**、$E$ の変化は $C$ の変化を伴い、品質に影響しうる。

例:
- 「CHECKPOINT P-X を出力せよ」は $C$ (フォーマット制約)。NL でも構造記法でも同等に記述可能。→ $E$ の変化は $Q$ に影響しない。
- 「全 Phase の収穫を $K_6$ グラフ上で交差検証せよ」は $C$ だが NL で正確に記述困難。→ 構造記法でのみ記述可能な制約。→ $E$ の除去は $C$ の損失を伴い、$Q$ に影響する。

すなわち: **$C$ と $E$ の分離可能性は、$C$ が $E$-非依存に記述可能か否かに依存する**。大半の制約は NL で記述可能であり、実験 0 の帰無結果はこの大半のケースに適用される。

---

### 7.7 プロンプト感受性との統合

#### 7.7.1 プロンプト感受性 (Prompt Sensitivity) の位置づけ

近年の研究が示す「意味的にほぼ同じ指示での性能の大きなばらつき」は、本稿の枠組みでは次のように解釈される。

Sclar et al. (2024, ICLR) [25] は、意味的に等価なプロンプトフォーマット間で LLaMA-2-13B の正答率が最大 76 点変動し、50+ タスク・複数モデルで平均約 10 点のフォーマット依存性を示した。FormatSpread 指標でこの変動を定量化し、few-shot 追加・モデル大規模化・instruction tuning のいずれも完全には除去できないと報告した。

Weber et al. (2026) [26] は、この感受性の大部分が「プロンプトの不特定性 (underspecification)」に起因すると主張した。テキスト分類タスクで、最小限指示のみの「ミニマルプロンプト」と、ラベル意味・フォーマットを明示する「インストラクション型プロンプト」を比較し、後者で平均性能向上と同時に性能分散の有意な減少を確認した。ロジット分析では、不特定プロンプトでラベルトークン確率が極めて低く、ほぼランダムな決定になっていた。

Yin et al. (2024, SICon) [27] は、英語・中国語・日本語で敬語レベルが段階的に異なる 8 種のプロンプトを設計し、JMMLU (日本語 MMLU, 56 タスク・7,536 問) で性能を比較した。「無礼なプロンプトが常に悪い」という単純な図式ではなく、言語ごとに丁寧さと性能の関係が異なることを示した。

これらは本稿の枠組みでは次のように解釈される:

> **プロンプト感受性の大部分は $C$ 軸の変動である。** 「意���的に同じ」に見える変更が、実は暗黙的な制約 ($C$) を変えている。

具体的には:

- **語順の変更**: 「AしてからBせよ」vs「Bの前にAせよ」は $C$ (手順制約) を変えている
- **in-context 例の追加**: 出力空間の制約を強化 ($C$ ↑)。性能改善 + 分散減少
- **Format 指定の追加**: 出力形式の制約 ($C$ ↑)。logit 分布の集中

#### 7.7.2 不特定性 (Underspecification) の FEP 的翻訳

Weber et al. (2025) が示した「不特定なプロンプトでラベルトークン確率が極めて低い」現象は、FEP 的には:

$$\text{underspecified } C \Rightarrow \pi_s \text{ が低い} \Rightarrow q(\theta|d) \text{ が広い (高エントロピー)} \Rightarrow \text{出力がほぼランダム}$$

これは §1.2 の定式化の直接的帰結。プロンプトの $C$ 成分が弱いとき、生成モデルは prior に委ねられ（= 忘却されず）、出力の多様性が爆発��る。

制約を強化する ($C$ ��) ことは、$\pi_s$ を上げ、$q(\theta|d)$ を狭め、出力を特定のプログラムに集中させる。これがプロンプト感受性の軽減メカニズム。

#### 7.7.3 日本語特有のプロンプト感受性

日本語プロンプトにおける敬語・文体の影響 (Kabra et al. 2025, Hada et al. 2024) は、$C$ と $E$ の分離が言語的に困難な領域として理解できる:

> **社会的文脈 = 暗黙の $C$**。日本語では、敬語レベルの変更が「タスク指示」だけでなく「話者/聞き手の関係」「社会的立場」を変え、これが暗黙的な制約として機能する。

3 層モデルとして整理する:

| 層 | 制約の種類 | 例 | $C$/$E$ |
|:---|:---------|:---|:--------|
| L1: タスク制約 | 何をするか | Phase 構造, アルゴリズム | $C$ (明示的) |
| L2: 形式制約 | どう出力するか | フォーマット, CHECKPOINT | $C$ (明示的) |
| L3: 社会的制約 | 誰として話すか | 敬語, 文体, role 設定 | **$C$/$E$ の境界** |

L3 が日本語で特に重要なのは、L3 の変化が L1 の暗黙的変更を伴うため。「です/ます体」と「である体」は $E$ の変化に見えるが、実際には「聞き手が一般人か専門家か」という暗黙の制約 ($C$) を変えている。

---

### 7.8 認知スキル (SKILL.md) 設計への含意

H₃ は HGK の認知スキル設計に含意を持つ。ただし「不要」と「効かない」を混同してはならない。

#### 7.8.1 直接効果: $C$ 軸 (推論品質 $Q$ に作用)

| 要素 | 機能 | 文献的裏付け | 効果経路 |
|:-----|:-----|:-----------|:--------|
| Phase の分解と順序 | タスク構造化。$\pi_s$ を最も強く制御 | Cognitive Prompting [4]: +4-13.5% | $C$ → $\pi_s$ → $Q$ |
| Phase 内アルゴリズム | 具体的操作手順 | Weber [26]: 手順明示で分散↓ | $C$ → $\pi_s$ → $Q$ |
| アンチパターン | 負の制約。不正解領域封鎖 | In-context 例と同等効果 | $C$ → $\pi_s$ → $Q$ |
| 出力フォーマット | logit 分布を制約 | Sclar [25]: フォーマット依存 ±10pt | $C$ → $\pi_s$ → $Q$ |
| ゼロトラスト検証 | 自己検証の強制 | Self-Explanation Effect (Chi 1989) | $C$ → $\pi_s$ → $Q$ |

#### 7.8.2 間接効果: $E$ 軸 (推論品質に直接影響しないが、SKILL 体系に貢献)

| 要素 | NL 等価物 | 推論品質への直接効果 | 間接効果 |
|:-----|:---------|:-------------------|:--------|
| 座標記法 (I×E) | 「外部入力なし」 | なし (Exp0: d≈0) | **記述効率**: 6語→3記号。**整合性検証**: 4象限の排他性を形式的にチェック可能 |
| N⊣U 合成表記 | 「見落とし→回復」 | なし | **理論的透明性**: 忘却-回復の随伴構造を明示し、Phase 間の因果関係を可読にする |
| ρ 剰余記法 | 「収穫」 | なし | **定量化可能性**: ρ≈0 を検出条件にできる。NL「収穫がない」は定量化困難 |
| Fix(G∘F) 判定 | 「蒸留→展開→不変なら到達」 | なし | **操作的定義**: 「完了」を主観ではなく不動点条件で定義。自動検証の基盤 |

**核心**: $E$ は $Q$ を直接上げないが、$C$ を**設計・保守・検証する**能力を上げる。$E$ は LLM の推論に効くのではなく、SKILL 設計者 (人間) の認知に効く。

#### 7.8.3 境界領域: $E$ が $C$ を兼ねる場合

構造記法が純粋な $E$ ではなく $C$ としても機能する可能性のある領域:

1. **NL で記述困難な制約**: 「全 Phase の ρ を $K_6$ グラフ上で交差検証せよ」は NL 化で情報損失を伴う → $E$ の除去が $C$ の損失を招く
2. **暗黙的行動誘導**: 構造記法の使用自体が「構造的に思考せよ」という L3 制約として機能する可能性 → Yin et al. [27] の日本語文体効果と同型の現象
3. **Self-Explanation 誘導**: 構造記法は LLM に出力の各部分を説明させることを暗黙に要求する → Chi (1989) の Self-Explanation Effect と合流
4. **出力分散への効果** (§7.6.2b 反証条件 (3)): H₃' (§7.6.2b 直後) で**部分的に確認**。bond_count 分散比 F=4.93 (p<0.05)。axiom_count は逆方向 — precision の**再配分**が起きている。$E$ は精度の総量ではなく配分を変える。

これらの境界ケースのうち (4) は H₃' で実験的に支持されつつある。(1)-(3) は §7.3 のアブレーション設計で分離が必要。

#### 7.8.4 HGK の演繹的最善系への含意

HGK の設計思想は「偶然ではなく必然に依拠した認知操作体系」である。H₃ + H₃' はこの思想に 3 層の根拠を与える:

> **SKILL の 3 つの効果経路:**
>
> 1. **$C$ → $\pi_s$ → $\mathbb{E}[Q]$**: 制約が推論品質の期待値を決める (直接効果)
>    Phase 構造・アルゴリズム・アンチパターン・検証基準が LLM の生成モデル空間を精密に制約する。
>
> 2. **$E$ → $\pi_v$ → $\text{Var}[Q]$**: 符号化が推論品質の精度 (ばらつき) を制御する (精度効果 — H₃')
>    構造記法がテンプレート化する操作 (bond analysis 等) の出力分散を減少させる。
>    ただし precision は有限資源 — テンプレート化と競合する操作の分散は増大しうる (precision の再配分)。
>
> 3. **$E$ → 人間 → $C$ の品質**: 符号化が SKILL 設計者の認知を支援する (間接効果)
>    記述効率 / 形式的検証 / 表現力の拡張 / 理論的透明性。
>
> 結論: 「記法は効かない」は不正確。「記法は平均品質ではなく**精度と設計性**に効く」が正確な記述。$E$ は LLM の推論の期待値を変えないが (H₃)、精度 (分散の逆数) を制御し (H₃')、人間の設計能力を支援する。

### 7.9 クロスモデル検証: Gemini 3.1 Pro Preview

H₃ が Claude Sonnet 4.6 に特異的ではなく model-invariant であるかを検証するため、Gemini 3.1 Pro Preview (Google One AI Ultra tier) で同一実験を N=50/条件で実施した。

#### 7.9.1 実験設定

```yaml
cross_model_verification:
  model: gemini-3.1-pro-preview
  tier: "Gemini Code Assist in Google One AI Ultra (Personal)"
  N_per_condition: 50
  topics: T1-T5 (Claude 実験と同一)
  conditions: A (plain) / B (CCL) — 同一プロンプト
  invocation: "gemini -p (headless mode, Tolmeton OAuth)"
```

#### 7.9.2 平均差 (Welch t-test, N=50/条件)

| 指標 | A mean | B mean | Cohen's d | 判定 |
|:-----|:-------|:-------|:----------|:-----|
| total_structural | 1.34 | 84.06 | **8.62** | 伝搬 (Claude: d=1.5-3) |
| rho_notation | 0.00 | 15.36 | **13.46** | 圧倒的伝搬 |
| U_labels | 0.00 | 22.94 | **6.33** | 圧倒的伝搬 |
| categorical_vocab | 0.12 | 23.84 | **3.79** | 強い伝搬 |
| axiom_ratio | 0.38 | 0.32 | **-0.39** | **帰無** |
| assumption_count | 4.44 | 4.54 | **0.08** | **帰無** |
| bond_count | 7.90 | 7.78 | **-0.06** | **帰無** |

#### 7.9.3 分散差 (Brown-Forsythe, N=50/条件)

| 指標 | A sd | B sd | BF p | 判定 |
|:-----|:-----|:-----|:-----|:-----|
| total_structural | 1.84 | 13.46 | <0.001 | *** B 分散大 |
| categorical_vocab | 0.39 | 8.84 | <0.001 | *** |
| axiom_ratio | 0.14 | 0.14 | 0.410 | ns |
| assumption_count | 1.28 | 1.23 | 0.917 | ns |
| bond_count | 1.85 | 2.00 | 0.889 | ns |

#### 7.9.4 解釈

H₃ の model-invariance が確認された: compliance 特性が正反対の 2 モデル (Claude d=1-3, Gemini d=8-13) で、内容指標の帰無が一致。

| | Gemini (高 compliance) | Claude (低 compliance) |
|:---|:---|:---|
| 構造語彙 ($E$ 軸) | d=8.62 | d=1.5-3 |
| 内容判断 ($C$ 軸) | **d≈0** | **d≈0** |

$C$ 帰無は compliance 特性に依存しない model-invariant な性質である。これは H₃ の射程を「特定モデルでの経験的帰無」から「LLM 一般の構造的性質」に格上げする根拠となる。

### 7.10 MB 透過性と compliance coefficient

#### 7.10.1 なぜ effect size がモデル間で 3-6 倍も異なるのか

Claude と Gemini は同じ $E$ (CCL 記法) を受け取りながら、構造語彙の $d$ が大きく異なる。これは $E$ の「効き」の違いではなく、**モデルの MB (Markov Blanket) 透過性** の違いである。

FEP の枠組みでは:

$$\text{output} = \frac{\pi_s \cdot \text{input} + \pi_p \cdot \text{prior}}{\pi_s + \pi_p}$$

- $\pi_s$ = 入力 (prompt) の精度
- $\pi_p$ = モデルの事前分布 (prior) の精度

**Gemini**: $\pi_p$ が低い → 入力が出力をほぼ支配 → output $\approx$ f(input)
**Claude**: $\pi_p$ が高い → prior と入力が融合 → output $\approx$ g(prior, input)

これは忘却論の用語では:

$$\text{MB 透過性} = U_{\text{prior}} \text{ の深さ}$$

Gemini は自己の prior をより深く忘れて入力に明け渡す ($U_{\text{prior}}$ が深い)。Claude は prior を保持しつつ入力を変換する ($U_{\text{prior}}$ が浅い)。

#### 7.10.2 compliance coefficient の導入

構造語彙の effect size を分解する:

$$d_{\text{struct}} = \kappa_{\text{model}} \cdot \delta_{\text{notation}}$$

- $\kappa_{\text{model}}$ = **compliance coefficient** (モデル固有の MB 透過性パラメータ)
- $\delta_{\text{notation}}$ = 記法の構造的密度 (条件 A/B に固有)

$\delta_{\text{notation}}$ は両モデルで同一 (同じプロンプトを使用)。したがって:

$$\frac{d_{\text{Gemini}}}{d_{\text{Claude}}} = \frac{\kappa_{\text{Gemini}}}{\kappa_{\text{Claude}}} \approx \frac{8.62}{2.5} \approx 3.4$$

Gemini の MB 透過性は Claude の約 3.4 倍。

#### 7.10.3 MB 透過性の含意

1. **d は「構造伝搬の強度」を測っていない** — $\kappa_{\text{model}}$ と $\delta_{\text{notation}}$ の積を測っている。$\kappa$ が不明な状態で $d$ を報告しても、$\delta$ の推定にはならない。
2. **H₃ の真の強さ**: $\kappa$ が 3.4 倍異なっても内容帰無が成立する → $C$ 帰無は $\kappa$ に依存しない (= model-invariant)。
3. **SKILL 設計含意の修正**: 「記法は MB 透過性の調整にのみ効く」— 高 $\kappa$ モデル (Gemini) では記法が出力を支配し、低 $\kappa$ モデル (Claude) では記法の影響が prior で緩衝される。どちらの場合も推論品質は変わらない。
4. **「馬鹿正直」問題**: 高 $\kappa$ モデルは入力に忠実であるがゆえに、入力の**ノイズにも忠実**。prompt injection に対する脆弱性は $\kappa$ に比例する可能性がある。

---

## §8. 先行研究との位置づけ

| 研究 | 年 | 貢献 | 本稿との関係 |
|:-----|:---|:-----|:-----------|
| Ng | 2025 | 反 Whorf ボトルネック | §2: FEP で解消 |
| Ray | 2025 | 弱 Whorf の LLM 実証 | §2: 精度加重の入力依存性 |
| Chollet | 2024 | Program space model | §1: FEP 翻訳 |
| arXiv:2410.02953 | 2024 | Cognitive Prompting | §4: 指示 vs 言語変更の差 |
| **VoT** | **2024** | **構造的視覚化 +27%** | **§6.4: 構造表記注入の直接先行** |
| **SPP** | **2023** | **座標プレフィックス +33%** | **§6.4: 座標系注入の直接先行** |
| **Soft Thinking** | **2025** | **連続概念空間 +2.48pp** | **§3.5: 離散ボトルネック理論** |
| **SoftCoT** | **2025** | **Soft thought tokens (ACL)** | **§3.5: 連続空間推論** |
| **Natural-Formal Hybrid** | **2025** | **NL+形式 = 数学推論向上** | **§6.5: P₃ の直接実証** |
| **Mech.Interp.×Prompt** | **2026** | **Steering vector ↔ prompt** | **§3.4: 機械論的基盤** |
| **Basil et al.** | **2025** | **ペルソナ効果なし** | **§3.6: 負の対照** |
| **本稿 (Gemini 検証)** | **2026** | **クロスモデル C/E 分離 + MB 透過性** | **§7.9-7.10: model-invariant 帰無 + κ 導入** |
| Fernando et al. | 2024 | PromptBreeder | §8: 自動最適化との互換性 |
| Yang et al. | 2024 | OPRO | §8: LLM-driven optimization |
| NeurIPS 2024 | 2024 | FLD×2 | §6: 形式論理訓練の効果 |
| EMNLP 2025 | 2025 | Prompt Optimization Survey | §8: 分野の全体像 |
| **Autoformalization Survey** | **2025** | **NL↔形式の橋渡し** | **§6.6: 逆方向の相補性** |

### 8.1 方法論的改善: Cognitive Prompting の弱点への対応

arXiv:2410.02953 (Cognitive Prompting) は最も近い先行研究だが、方法論的に以下の弱点がある:

| Cognitive Prompting の弱点 | Paper XI での改善 |
|:--------------------------|:----------------|
| 統計的検定なし (p 値, CI, effect size 未報告) | §5.0 の ρ,K モデルで effect size を事前予測 + power analysis |
| アブレーションなし (どの操作が貢献か不明) | §7.3: 6軸アブレーション設計 |
| モデル範囲が狭い (LLaMA 8B/70B のみ) | Claude 4.6 + Gemini で cross-model 検証 |
| 盲検なし (評価者が条件を認識) | Blind LLM judge (条件ラベル隠蔽) |
| 効果量が報告されない | r_obs を算出し §5.0 の理論予測と照合 |

**本稿の新規性**: 上記 17 件のいずれも、(1) prompt を FEP の精度加重として定式化し、(2) 構造的構文と自然言語を関手の積として統合し、(3) 効果量の構造的上限を理論的に導出し、(4) 離散→連続の忘却階層内に prompt 技法を位置づけていない。

---

## §9. Open Problems

1. **ρ_prompt の実測**: Prompt レベルのスペクトラム射影効率は未測定。実験 0 で推定可能。
2. **最適構文密度**: SKILL.md 内の座標構文の最適な割合は？ P₂ が支配的になると表現力が低下する (full でなくなる)。
3. **世代間安定性**: Claude 4.6 で有効なプロンプトパターンが 5.x で再現するか。ρ, K が世代間でどう変化するか。
4. **自動最適化との統合**: PromptBreeder / OPRO に構造的指標を目的関数として導入可能か。
5. **思考言語の一般化**: CCL/aletheia 以外の形式体系 (PDDL, first-order logic, type theory) で同等の効果が出るか。
6. **CSP 接続 — 観測としてのプロンプト**: プロンプトは忘却関手 U_prompt の選択であり、CSP (chemistry_of_ccl_features.md §13) と同型構造を持つ。下記 §9.6 参照。

### 9.6 観測としてのプロンプト — Face Lemma CSP 接続

§1 のテーゼ「プロンプトは選択的忘却操作」を、CCL 検索の CSP 問題 (chemistry_of_ccl_features.md §9, §13) と接続する。

**同型構造**:

| CCL 検索 | プロンプト | 構造 |
|:---------|:---------|:-----|
| U_count (49d化) | P₁ (自然言語) | 粗い忘却 — 多くの構造を潰す |
| U_cos (cosine) | P₂ (構造記法) | さらなる忘却 — 角度のみ保存 |
| ker(U_cos) ⊇ 94% | ∂Q/∂E ≈ 0 (H₃) | 忘却が支配的 — 微調整は表面的 |
| 1-skeleton (2射) = 不安定 | C のみ = 制約は効くが多義的 | dim Ξ = 1 — 方向なし |
| 2-skeleton (3射) = 安定 | C + E + **context** = 3軸 | dim Ξ = 2 — 形がある |

**Face Lemma の SKILL 設計への含意**:

Face Lemma (Paper II §3.4): 概念安定性には最低3つの独立な生成射が必要。

Paper III の言葉で言えば、P₂ は単なる装飾ではなく「どの α-セクターで構造を再利用するか」を偏らせる局所記法である。共有コンテキストが欠けるとこの偏りは 1-skeleton の段階で失効しうるが、context が加わると 2-skeleton が立ち、Z₂ 的な極性差が安定な構造語彙として残る。したがって XI は I・IV だけでなく、III の α-セクター / Z₂-次数の議論にも接続される。

SKILL.md は本質的に3つの独立な制約軸を持つべき:
1. **C 軸 (制約)**: Phase の分解・手順・検証基準 → $\pi_s$ 制御
2. **E 軸 (符号化)**: 座標構文・CCL 記法 → $\pi_v$ 制御
3. **M 軸 (メタ認知)**: アンチパターン・自己参照・Kalon 基準 → 再帰的安定化

C のみ = 1-skeleton (不安定)。C + E = 2射 (dim Ξ = 1、方向なし)。
**C + E + M = 2-skeleton** (dim Ξ = 2、概念が安定)。

H₃ の制約-符号化分離 (§7.6) は、E が Q に直接影響しないことを示した。
しかし Face Lemma の観点では、E は Q の「安定性」に影響する:
E が欠落すると dim Ξ が低下し、同じ C を与えても出力の分散が増大する。

これは §7.7.2 の不特定性 (underspecification) と整合する:
Weber et al. (2026) が示した「ミニマルプロンプトの高分散」= dim Ξ の不足。

**実験的予測 (P41)**:
SKILL.md の C/E/M 3軸を体系的に除去するアブレーションで:
- C 除去: Q が大きく低下 (§7.8.1 と一致)
- E 除去: Q の平均は不変だが**分散が増加** (H₃ の精密化)
- M 除去: Q の平均はやや低下し、**長期整合性が崩壊** (自己参照の喪失)

---

## §10. 確信度マップ

| 命題 | 確信度 | 種別 | 根拠 |
|:-----|:-------|:-----|:-----|
| LLM で Sapir-Whorf 強版が構成的に成立 | 90% | 演繹 | トークン生成の数学的構造 |
| LLM は暗黙の U_ccl を持つ (P10) | 82% | 推定 | 4 モデル一貫 |
| テキスト注入で 85% 獲得可能 | 85% | 確信 | Phase C v2 実測値 |
| H₁ (構造的精度加重仮説) — 伝搬部分 | 95% | **確信** | Exp0: d=8.73, 全10トピック+Gemini再現 |
| H₁ (構造的精度加重仮説) — 品質部分 | 20% | **棄却寄り** | Exp0: d≈0, 哲学+科学タスクで帰無 |
| 制約-符号化 分離仮説 H₃ (§7.6) | **85%** | **推定↑↑** | **3環境 (API batch + CC Agent + Gemini) で再現。クロスモデル不変性確認** |
| H₃' 分散仮説 — 構造指標 | **60%** | 推定↑ | Gemini: 構造指標 BF p<0.001、内容指標 ns。方向一貫 |
| H₃' 分散仮説 — bond_count 抑制 | 40% | 仮説↓ | Claude batch で支持、CC Agent で逆転、Gemini で ns。環境依存 |
| H₃'' 文脈条件仮説 | 40% | 仮説 | CC Agent 特有。追加検証待ち |
| MB 透過性仮説 κ (§7.10) | **65%** | **仮説 [NEW]** | κ_Gemini/κ_Claude ≈ 3.4。2モデル比較のみ。3+モデルで検証必要 |
| H₂ (r_obs ≈ 0.17) | 40% | 仮説↓ | Exp0 品質帰無により r_obs ≈ 0 の可能性 |
| 論文として新規性がある | **97%** | **確信↑↑** | 帰無結果 + 分離仮説 + クロスモデル不変性 + MB透過性は先行研究にない |

---

## 参考文献

<!-- TODO: 正式な引用形式に変換 -->

[1] Ng, D. N. (2025). "Do LLMs Break the Sapir-Whorf Hypothesis?" Blog post.
[2] Ray, P. (2025). "Does Linguistic Relativity Hypothesis Apply on ChatGPT Responses? Yes, It Does." *Computational Intelligence*, Wiley.
[3] Chollet, F. (2024). "How I think about LLM prompt engineering." *Substack*.
[4] arXiv:2410.02953 (2024). "Unlocking Structured Thinking in Language Models with Cognitive Prompting."
[5] Fernando, C. et al. (2024). "PromptBreeder: Self-Referential Self-Improvement via Prompt Evolution." *ICLR 2024*.
[6] Yang, Z. et al. (2024). "Large Language Models as Optimizers (OPRO)." *NeurIPS 2024*.
[7] NeurIPS 2024. "Enhancing Reasoning Capabilities of LLMs via Principled Synthetic Logic Corpus (FLD×2)."
[8] EMNLP 2025. "A Systematic Survey of Automatic Prompt Optimization."
[9] Springer 2025. "An AI tool for scaffolding complex thinking: challenges and solutions in developing an LLM prompt protocol suite." *Cognition, Technology & Work*.
[10] Friston, K. (2010). "The free-energy principle: a unified brain theory?" *Nature Reviews Neuroscience*, 11(2), 127-138.
[11] Tolmetes (2026a). "Force is Oblivion (Paper I)."
[12] Tolmetes (2026d). "Why Are Effect Sizes Small? (Paper IV)." In preparation. 本稿 §5.0 に必要な最小限の内容を再導出。
[13] Tolmetes (2026j). "Context Rot is Oblivion (Paper X)." In preparation.
[14] Xu, Y. et al. (2025). "SoftCoT: Soft Chain-of-Thought for Efficient Reasoning with LLMs." *ACL 2025*.
[15] arXiv:2505.15778 (2025). "Soft Thinking: Unlocking the Reasoning Potential of LLMs in Continuous Concept Space."
[16] arXiv:2404.03622 (2024). "Mind's Eye of LLMs: Visualization-of-Thought Elicits Spatial Reasoning in Large Language Models." *NeurIPS 2024*.
[17] arXiv:2312.01054 (2023). "Exploring and Improving the Spatial Reasoning Abilities of Large Language Models." (SPP)
[18] arXiv:2601.02896 (2026). "Bridging Mechanistic Interpretability and Prompt Engineering with Gradient Ascent for Interpretable Persona Control."
[19] EMNLP 2025. "Natural-Formal Hybrid Reasoning Enhances LLM's Math."
[20] Basil, S. et al. (2025). "Playing Pretend: Expert Personas Don't Improve Factual Accuracy." *SSRN*.
[21] arXiv:2505.23486 (2025). "Autoformalization in the Era of Large Language Models: A Survey."
[22] arXiv:2503.20561 (2025). "A Theoretical Framework for Prompt Engineering: Approximating Smooth Functions with Transformer Prompts."
[23] Zou, A. et al. (2023). "Representation Engineering: A Top-Down Approach to AI Transparency." / Wehner, J. (2025). "Representation Engineering for LLMs: Survey."
[24] von Oswald, J. et al. (2023). "Transformers Learn In-Context by Gradient Descent." *ICML 2023*.
[25] Sclar, M. et al. (2024). "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design." *ICLR 2024*. arXiv:2310.11324.
[26] Weber, L. et al. (2026). "Revisiting Prompt Sensitivity in Large Language Models for Text Classification: The Role of Prompt Underspecification." arXiv:2602.04297.
[27] Yin, Z. et al. (2024). "Should We Respect LLMs? A Cross-Lingual Study on the Influence of Prompt Politeness on LLM Performance." *SICon 2024*. arXiv:2402.14531.

---

*Paper XI v0.5 — 2026-04-06 (v0.4 + §9.6 Face Lemma CSP 接続, P41 SKILL アブレーション予測, C/E/M 3軸モデル)*
*Paper XI v0.5 — 2026-04-07 (v0.4 + §7.5.4 実験限界6項, §7.6.2b 反証条件4件, §7.6.2c-d H₃'分散仮説+独立再現, §7.7原典引用精密化, §7.8二層化, 引用 24→27件, H₃'確信度75%)*
*Paper XI v0.4 — 2026-04-06 (v0.3 + §7.5 Exp0結果 d=8.73/d≈0, §7.6 制約-符号化分離仮説H₃, §7.7 プロンプト感受性統合, §7.8 SKILL設計含意)*
*Paper XI v0.3 — 2026-04-04 (v0.2 + §1.4-1.5 virtual NN 統合+5系譜布置, §3.4-3.5 RepE+ICL=GD, 引用 21→24件)*
*Paper XI v0.2 — 2026-04-04 (v0.1 + 離散→連続忘却階層 §3.4-3.6, VoT/SPP 先行証拠 §6.4-6.6, アブレーション設計 §7.3, 方法論的改善 §8.1, 引用 9→17件→21件)*
*Paper XI v0.1 — 2026-04-04 (初稿: 構造的精度加重仮説 + 先行研究統合 + 実験設計)*
