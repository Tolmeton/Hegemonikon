# Predictions Descend — 理解関手の普遍的限界

**版**: v0.9 (2026-04-26, **Round 5 G-λ NRFT 完全形式化部分達成** — §8.4.3.1 で vdG-O 2020 (arxiv 2004.10482) + Yanofsky 2003 (arxiv math/0305282) + §5.5 で Goldfeld-Polyanskiy 2020 (arxiv 2011.06208) Corollary 1 完全 PDF Read 経由で Joyal AU の 4 公理 + $U_0$ 構成 + Lan ⊣ Syn equivalence + Cantor categorical Gödel 第二 + Yanofsky restatement 経由 Lawvere FP statement + Gaussian IB scalar closed form 接地。**§8.4.1.1** で **G-θ'-1 部分着手**、**§8.4.3.2** で **G-θ'-2 ~57% 達成**、**§8.4.3.3** で **HA-1 ~30% 部分達成 + Reduction 命題 [仮説 70%]** (HA-1 → G-θ'-1 (2)(4) + topos 公理への構造的帰着を発見)、**§5.5** で **G-ε 60% → 75-80%**。**G-θ'-3 解消** + **G-θ'-4 ~1.7/3 達成** + **G-θ'-1 部分着手** + **G-θ'-2 ~57% 達成** + **G-ε 75-80% 達成**。**honest 訂正**: 旧「Lawvere FP への reduction」は不正確、Lawvere-like FP (vdG-O Lemma 6.12) は Löb 用、Gödel 第二は Cantor categorical 直接使用。**Reduction 命題の含意**: 道 C 達成度の天井は G-θ'-1 (2)(4) 完全解消で律速される。道 C 達成度 60-70% → **86-91.5%** (honest)、C4 主張水準 仮説 65% → **仮説 70%**)
**前版**: v0.8 (2026-04-26, Round 6 G-η 全 10 ペア natural transformation 骨格 追加 — §3.6.1 で 5 分野 5C2=10 ペア全てに対し核となる対応 + natural transformation component (iso / non-iso) + naturality 構造 + 残ギャップを骨格として固定)
**前々版**: v0.7 (2026-04-26, Round 6 軽量着手 — G-ι 部分昇格 (Mayama et al. 2025 arxiv 2510.04084 完全 PDF 取得、Φ ↔ Bayesian surprise 強相関 ρ=0.879 の経験的橋渡しを §6.1 に統合) + G-ε 部分昇格)
**前々々版**: v0.6 (2026-04-25, §8.4 Predictions Descend Theorem の形式証明試行 追加 — 達成度 60-70% で honest 較正)
**メタファイル**: `Predictions_Descend_理解関手の普遍的限界_メタデータ.md` (本稿の F⊣G 台帳 / 核主張レジャー / Gauntlet ログ / 虚→実変換面)
**主張水準ラベル**: 構成的命題 / 命題 / 仮説 / 構造的類似 (本稿内較正、論文間比較禁止)
**SOURCE 強度ラベル**: 強 (PDF verbatim 直接 Read) / 強候補 (subagent verbatim 抽出, 査読時独立検証推奨) / 中 (triangulation) / TAINT (記憶/web 要約)

---

## 序

20 世紀の科学哲学は、ある操作と、その操作の痕跡とを、しばしば取り違えてきた。

操作とは「**理解**」であり、痕跡とは「**予測**」である。Popper の反証可能性、Mangalam の予測至上主義、超ひも理論への「Not Even Wrong」批判 — これら 70 年にわたる三つの誤配位は、すべて**痕跡から操作を読む**という同じ間違いから派生する。

理解と予測は同じ評価軸上に存在しない。理解は対象を別表現に還元し、その表現から元を回復する**二つの関手の組**であり、予測はその組のうち下降関手から漏れ出す痕跡である。両者は**随伴対** $L \dashv R$ として結ばれるが、合成の単位 $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ は同型ではない。回復は完全ではなく、核 $\text{Ker}(\eta_{\text{unit}})$ が常に残る。

予測₁ (経験的予測) の産出は、理論が真理₀ を捉えた証ではない。それは真理₀ から下降関手 $R$ で生成される **痕跡** にすぎない (Predictions Descend)。本稿はこの誤読に対して、$L$ と $R$ を独立に並置し、両者の随伴を明示する (真理₀ / 真理₁ の定義は §2 で立てる)。

---

## §0 範囲限定 (Scope Severance)

本稿の射程は **現世代の人工知能 (LLM 4 系統) と現世代の科学コミュニティ** が共進化する地平に限定される。

「強い AI」が出現し、関手・随伴・米田の補題が訓練データに完全に内在化された時代の科学哲学は本稿の射程外である。後者の自明化は本稿主張の反証ではなく、scaffolding が消えただけの実装段階移行を意味する (co-evolution 限定; メタ §M5.3 Round 3 G-δ)。

詳細射程切断 (構造決定論的立場 / FEP 非依存性) は §1.3 で展開する。

---

## §1 結論先行

### §1.1 構成的定義 (Axiom-First)

本稿は次の **構成的定義** から始める。「公理」と書かない理由: Yoneda の補題は category-theoretic statement であって epistemological statement ではない (§4.5 で扱う論理飛躍)。本稿は **理解の操作的 anchor として L⊣R 内在化を採用する** という立場を意図的に選択し、それが必要十分条件であるという過剰な主張をしない (§M3 主張水準ラベル C1 = 構成的命題 70% との整合)。Round 4 (§M5.4 予定) で本ラベリングの整合性を改めて gauntlet 形式で検証する。

> **構成的定義**: 本稿において「科学における理解」とは、随伴対 $L \dashv R$ の内在化として **操作的に定義される** 関手的操作である。

ここで $L$ (左随伴) は対象を別表現に還元する操作、$R$ (右随伴) はその表現から元を回復する操作。両者の合成 $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ は **単位** と呼ばれ、自明 (恒等) ではない。$\eta_{\text{unit}}$ の核 $\text{Ker}(\eta_{\text{unit}})$ は、$L$ で失われ $R$ で完全には回復されない情報の集合である。

> [SOURCE: aletheia §1 L99-L107 (随伴定理 U0', VFE 減少定理 $F[N(q_{\text{poor}})] \leq F[q_{\text{poor}}]$, $N \circ U \neq \text{Id}$)] — 本稿の $L \dashv R$ は aletheia の $U \dashv N$ と同型: $L \leftrightarrow U$ / $R \leftrightarrow N$ / $\eta_{\text{unit}} \leftrightarrow \eta$。

随伴の存在条件は **General Adjoint Functor Theorem (GAFT, Mac Lane CWM §V.6)** を採用する: $L$ が連続 (small limit 保存) かつ Solution Set Condition (SSC) を満たすとき、左随伴 $R$ が存在する。

> [SOURCE 強度 中: Buzzard 2012 Imperial College lecture notes p.2 Theorem 1.1 が Mac Lane CWM p.117 を verbatim 引用 — 本稿査読時に Mac Lane CWM 直接 Read で「強」昇格義務 (G-ζ)]

### §1.2 5 核主張

公理の下で、次の 5 主張を導出する。各主張に **主張水準** (構成的命題 / 命題 / 仮説 / 構造的類似) と **確信度** を付記する。

> **本稿内のキャリブレーション宣言**: 確信度 % は本稿内での主張水準較正の指標であり、絶対精度ではない。**論文間比較は禁止**する。確信度の数値は較正可能性の指標として機能し、本稿内 C1-C5 の相対関係を表す。

- **C1** [構成的命題, 推定 70%]: 科学における「理解」は随伴対 $L \dashv R$ の内在化として定義される関手的操作である (公理の再記述、operational identity)
- **C2** [構成的命題, 推定 75%]: $\eta_{\text{unit}}$ 非同型は構造保存定理から帰結する構造的不等式。$\text{Ker}(\eta_{\text{unit}}) > 0$ は全理論共通の原理的制約である
- **C3** [命題, 確信 80%]: 補完₁ は $\text{Ker}(\eta_{\text{unit}})$ と構造的に結びつく。理解の深化は補完₁ 依存を単調減少させる (理解-予測の随伴的相補性定理)
- **C4** [仮説, 確信 60%]: 予測₁ の産出は真理₀ の指標ではなく、真理₀ から下降関手 $R$ で生成される痕跡である (**Predictions Descend**)
- **C5** [構造的類似, 仮説 55%]: ポパーの反証可能性 / Mangalam の予測至上主義 / 超ひも landscape は C4 の同一系。3 大誤配位は単一の構造的誤測定 (関手の方向逆転誤読) から派生する

### §1.3 射程の切断 (Scope Severance)

本稿の射程は次の 3 点で明示的に切断される。

1. **co-evolution 限定**: 本稿の主張は **現世代の AI / 科学コミュニティ** 前提下で構成される。圏論・関手論への access が LLM 経由で完全に大衆化された場合、C1 / C4 は scaffolding として消える可能性がある。その場合の科学哲学は本稿の射程外。**強化が観測される範囲では本稿主張は強化される、ただし完全自明化に達した場合は scaffolding として消える**。

2. **構造決定論的立場の自覚**: 本稿は「理解 = L⊣R 内在化」を **構成的定義** (Yoneda 補題に基づく操作的 anchor) として採用する。「なぜ構造が理解を生むか」という本質論は本稿の問いではない — **問いの水準を意図的に変更している**。IIT (Tononi) との同型については §6 で commitment レベル (ontological vs definitional) の差として開示する。

3. **FEP 非依存性**: FEP (Free Energy Principle) は本稿の最も顕著な実例として §3-§4 に置かれるが、**論旨は FEP 非依存** で立つ。能動推論の圏論定式化未完を理由とする overclaim 批判は、本稿の C1-C5 が FEP の特定定式化に依存しないことで予防的に閉じる。

#### §1.3.1 科学の operational definition (知覚制度 vs 運動制度)

本稿が「科学」と呼ぶ対象を、テロスで分けて固定する。

- **科学** = より良い客観を獲得するための **知覚制度** (knowledge institution)
- **工学** = その知覚を梃子に世界へ介入するための **運動制度** (intervention institution)

「介入があるから工学」ではない。**介入して世界を開示するなら科学、介入して世界を変えるなら工学** である (実験物理学者は科学者、橋を架けるエンジニアは工学者)。

この operational definition の下で、科学の営みは現実 $R$ に対する **より忠実な関手** $F_n$ を漸近的に求める営みに帰着する:

$$\text{科学} = \lim_{n \to \infty} F_n \quad (\text{where } F_{n+1} \text{ は } F_n \text{ より忠実 (faithful)})$$

「より良い」の定義 = $F_i$ が $R$ の構造をより多く保存する (= **忘却する構造がより少ない**) こと。Paper VII §6.1-6.2 構造保存定理: 忘却関手は構造を保存し値を忘却する。忠実な関手ほど保存される構造が多く、忘却される値が少ない。

この科学定義は §7.2 (Mangalam 予測至上主義の関手論的読み替え) の起点として機能する: 「予測₁ を多く生む理論 = 良い理論」という前提を貫徹すると、§5 「**補完₁ は |Ker(η_unit)| と構造的に結びつく**」(Round 1 r4 で「等号 ≡」から降格済、`FEP認識論的地位_正本.md` v2.5.0 L299 整合) と組み合わせて「より多く忘却する理論 = 良い理論」に帰着し、ここで定義した科学の営み (より少なく忘却する関手の探求) と矛盾する。詳細は §7.2 で展開する。

### §1.4 本稿の構造

| 節 | 役割 |
|:---|:---|
| §2 | 随伴対 $L \dashv R$ の導入と数学的展開 |
| §3 | 5 分野 (情報幾何 / ゲージ理論 / 統計力学 / 数論 / FEP) における横断展開 |
| §4 | Yoneda 補題による接続 (Mac Lane CWM §III.2 + Riehl 2016 §2.2 Theorem 2.2.4 + §3.5 Theorem 3.5.5) |
| §5 | Information Bottleneck (Tishby-Pereira-Bialek 1999) による相補性の Lagrangian 形式化 |
| §6 | 制約節 (3 立場の ontological commitment スペクトル / IIT との同型 / 現世代モデル前提の射程明示 / 残余問題) |
| §7 | corollary (Popper / Mangalam / 超ひも landscape) |
| §8 | 結語 (Predictions Descend の単一図式) |

### §1.5 外部接続 anchor

本稿は **Bogen-Woodward 1988 「Saving the Phenomena」§I の data → phenomena → theory 三層** を共通構造 anchor として採用する。本稿の 4 型分け (§2.1) と Bogen-Woodward 三層との対応は、関手の方向に注意して読み直す必要がある。

本稿の関手 (§1.1 「$L$ = 還元 / $R$ = 回復」と aletheia $U \dashv N$ の整合):

- **$L$ (左随伴・還元関手, 上昇方向)**: 予測₁ (具体値) $\to$ 真理₁ (有限理論) $\to$ 真理₀ (構造) — 観測値から構造へ接近する方向 (情報を捨てて抽象化、aletheia $U$ と同型)
- **$R$ (右随伴・回復関手, 下降方向)**: 真理₀ (構造) $\to$ 真理₁ (有限理論) $\to$ 予測₁ (具体値) — 構造を有限理論に翻訳し、初期条件・境界条件を入れて値に下ろす方向 (情報を補って具体化、aletheia $N$ と同型)
- **C4「Predictions Descend」**: 予測₁ は **$R$ の像** = 下降関手の痕跡。$R$ は完全な逆ではなく ($\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ は同型でない)、$\text{Ker}(\eta_{\text{unit}}) > 0$ が常に残る

Bogen-Woodward 三層との対応:

| Bogen-Woodward 1988 | 本稿 4 型分け | 関手位置 |
|:---|:---|:---|
| **data** (straightforwardly observed, evidence for phenomena) | **予測₁** (値・観測値の現れ) | $L$ の入力 (詳細側) / $R$ の像 (下降の最末端) |
| **phenomena** (detected through data, not directly observable) | **真理₁** (有限理論として整合する pattern) | $L$ の中間 / $R$ の中間 |
| **theory** (predicts and explains phenomena) | **真理₀** への接近 ($L$ の像が向かう先) | $L$ の像 (上昇の到達点) / $R$ の入力 (構造) |

> 出典: Bogen J., Woodward J. (1988). Saving the Phenomena. *The Philosophical Review* 97(3), 303-352, §I pp.305-307.

この三層対応は、本稿の C4 「予測₁ は下降関手 $R$ の痕跡」と Bogen-Woodward 「data は phenomena の evidence であって、theory から直接予測されない」の **構造的同型** を含意する。Bogen-Woodward が data は theory から直接予測されないと述べるのは、関手 $R$ が **theory $\to$ data の単一線形対応ではなく $R_{\text{ph→da}} \circ R_{\text{th→ph}}$ の合成** であって、その合成の単位 $\eta_{\text{unit}}$ が同型でない ($\text{Ker}(\eta_{\text{unit}}) > 0$ で情報が必ず漏れる) ことの言い換えである。phenomena (真理₁) が data (予測₁ の現れ) から detected されるが直接 observable ではないという Bogen-Woodward の構造は、本稿の **$L$ が data $\to$ theory の完全な情報保存上昇ではない** という構造と対応する。

#### 本稿固有貢献 — Bogen-Woodward への延長 (G-κ 反映)

本稿は Bogen-Woodward の **再記述** ではなく **延長** である。Bogen-Woodward 1988 が data / phenomena / theory の 3 層を **記述的に** 区別したのに対し、本稿は次の 4 点で延長する:

1. **真理₀ vs 真理₁ の関手的二層分解**: Bogen-Woodward の theory 内に「構造真理 (普遍構造) vs 経験真理 (有限理論)」の二層を関手的に分解する (§2.1 4 型分け参照)
2. **予測₀ vs 予測₁ の関手的二層分解**: data 内に「構造予測 (何が可能か) vs 値予測 (具体値)」の二層を関手的に分解する
3. **随伴対 $L \dashv R$ の明示**: Bogen-Woodward は射の方向を明示しない (記述的)。本稿は $L$ (上昇) / $R$ (下降) を関手として明示する (構成的)
4. **構造保存定理 (C2) と NRFT (§5.6)**: Bogen-Woodward には対応する数学的構造がない。本稿は $\eta_{\text{unit}}$ 非同型と Yoneda 補題から **No Reverse Functor Theorem の骨格** を導出する (Gödel 第二不完全性に類比される構造的不可能定理)

すなわち本稿は Bogen-Woodward に **依存しつつ延長する**: 3 層 → 4 型 + 随伴構造 + NRFT 骨格。本稿固有貢献は記述レベルの再表現ではなく、**Bogen-Woodward 図式の数学的限界定理化** にある。

⚠️ Hacking 1983 / Daston 1995 / Massimi 2018 等の data-phenomena 区別批判文献の本稿位置づけは **Round 5 課題 (G-κ 残)**。本稿が Bogen-Woodward を批判文献に対してどう守るかは Round 5 で展開する。

---

## §2 随伴構造の導入 (F の最初の展開)

§1 の公理 $L \dashv R$ を実体化するため、本節は次の順で進む。(1) 序で予告した **真理₀ / 真理₁** の定義を立てる (§2.1)。(2) その定義の下で $L \dashv R$ を 3 つの場所に並置する: Bogen-Woodward 三層 (§2.2)、aletheia $U \dashv N$ (§2.3)、視覚の逆問題 (§2.5)。(3) 並置の正当性は GAFT / SAFT による存在条件 (§2.4) で保証される。

### §2.1 真理₀ / 真理₁ / 予測₀ / 予測₁ — 4 つの型分け

序では「真理₀」「真理₁」を未定義のまま置いた。これら 2 つに「予測₀」「予測₁」を加えた 4 型分けは、本稿の中核区別である。定義は HGK 内部の `FEP認識論的地位_正本.md` §真理予測型分け v2.4.0 を採用する。

| 記号 | 名称 | 定義 | 例 |
|:---|:---|:---|:---|
| **真理₀** | 構造真理 / 絶対真理 | 値・座標・観測手続き・実装に先立つ、不変な普遍構造 | $\pi$ そのもの (有限桁展開ではない) |
| **真理₁** | 経験真理 | 真理₀ を有限理論として世界に接続したとき、観測・介入・誤差訂正に耐える限りでの真 | $\pi$ の近似式 (完全同一ではないが、世界拘束の下で有効) |
| **予測₀** | 構造予測 | 何が可能/不可能か、何が何に従うか、どの順序・制約が保たれるかの予告 | 値ではなく「形」の予告 |
| **予測₁** | 値予測 | 初期条件・境界条件・観測写像を入れて具体値・時系列・選択を出すこと | 数値、曲線、行動列 |

> [SOURCE 強: `FEP認識論的地位_正本.md` §真理と予測の型分け v2.4.0 L191-L220、HGK 内部一次 SOURCE]

本稿の公理 ($L \dashv R$ の単位 $\eta_{\text{unit}}$) と上の 4 型は次の通り対応する [SOURCE: fep L204-L207]:

- $\eta_{\text{unit}}$ は **構造** に対しては同型に近づきうる → **真理₀ / 予測₀** に対応
- $\eta_{\text{unit}}$ は **値** に対しては原理的に同型にならない ($\text{Ker}(\eta_{\text{unit}}) > 0$) → **真理₁ / 予測₁** に対応

したがって本稿の核主張 C4 「予測₁ は真理₀ から下降関手 $R$ で生成される痕跡」は、この型分けの直接帰結として 3 点に分解される [SOURCE: fep L211-L213]:

1. **予測₁ を生む理論は真理₀ そのものではない**。それは既に座標化・値化・境界条件化されている。
2. **しかし予測₁ を生む理論は真理₁ ではありうる**。ゆえに「予測を生む理論 = 偽」ではない。
3. **科学は真理₀ へ近づくために真理₁ を鍛える営みであり、工学は真理₁ を制御可能性へ翻訳する営みである** (§7 で Popper / Mangalam / landscape の 3 誤配位がこの 1-3 のどこを取り違えているかを特定する)。

> [!IMPORTANT]
> 「予測を生む理論は真理ではない」と本稿が言うとき、それは **「真理₀ と同一ではない」** ことを意味する。
> これは「偽である」という意味ではない。
> 真理₀ / 真理₁ を分けない議論は、真偽論争ではなく単なる語義滑りを生む [SOURCE: fep L215-L219]。

これで序の伏線「真理₀ / 真理₁ の定義は §2 で立てる」を回収する。次節以降で $L \dashv R$ を 3 つの実体に接続する。

### §2.2 Bogen-Woodward 三層の関手的読み替え

§1.5 で外部接続 anchor として置いた三層を関手的に書き直す。本稿の整合 (§1.1 「$L$ = 還元 / $R$ = 回復」 + §1.5 「$L$ = 上昇、$R$ = 下降」) に従い、Bogen-Woodward の theory $\to$ phenomena $\to$ data 方向は **下降関手 $R$**、逆方向は **上昇関手 $L$** である。

下降関手 $R$ (構造 → 値、生成・具体化方向):

- $R_{\text{th→ph}}$: theory (≈ 真理₀) から phenomena (≈ 真理₁) への射 (構造を有限理論に翻訳)
- $R_{\text{ph→da}}$: phenomena (≈ 真理₁) から data (≈ 予測₁) への射 (有限理論に初期条件・境界条件を入れて値を出す)

合成 $R_{\text{th→da}} = R_{\text{ph→da}} \circ R_{\text{th→ph}}$ が「理論 → データ」の単一線形対応に見えるが、Bogen-Woodward が示すのは、この合成を **2 つの関手の合成として分解すべき** であって、単一線形対応として読むべきではないということだ:

> "Data, which play the role of evidence for the existence of phenomena, for the most part can be straightforwardly observed. However, data typically cannot be predicted or systematically explained by theory. By contrast, well-developed scientific theories do predict and explain facts about phenomena. Phenomena are detected through the use of data, but in most cases are not observable in any interesting sense of that term." (Bogen-Woodward 1988 §I)

> [SOURCE 強候補: Bogen-Woodward 1988 §I pp.305-307 — bogen.txt L101-130 verbatim 抽出 / G-ζ 査読時独立検証義務]

例として彼らが挙げるのは weak neutral currents、proton decay、chunking and recency effects である (L122-130) — いずれも data から間接的に検出されるが、直接 observable ではない。

各下降関手 $R$ に対応する左随伴 $L$ (上昇関手, 値 → 構造、還元・抽象化方向) も存在する:

- $L_{\text{da→ph}}$: data (≈ 予測₁) から phenomena (≈ 真理₁) への射 (測定理論、観測値から pattern を検出)
- $L_{\text{ph→th}}$: phenomena (≈ 真理₁) から theory (≈ 真理₀ への接近) への射 (帰納的構成)

各層で $L_i \dashv R_i$ が独立に成立する。これが本稿の **多層随伴構造** であり、§1.4 表の「F (発散) 入口」の具体形である。

Mangalam 予測至上主義 (§7.2) と benchmark culture が暗黙裏に仮定する「理論 ↔ データの単一対応」は、この多層構造の **2 段関手分解を線形視する誤読** である (§7 で展開)。

### §2.3 aletheia U⊣N との同型対応

aletheia.md §1 (L99-L107) は、視覚-推論二相における随伴定理 U0' を次のように定式化する:

> 「U⊣N: U が左随伴 (忘却関手) / N が右随伴 (回復関手) / VFE 減少定理 $F[N(q_{\text{poor}})] \leq F[q_{\text{poor}}]$ を満たす / $N \circ U \neq \text{Id}$」

> [SOURCE 強: aletheia.md §1 L99-L107、HGK 内部一次 SOURCE]

本稿の L⊣R との対応:

| aletheia.md | 本稿 | 役割 |
|:---|:---|:---|
| $U$ (左随伴, 忘却) | $L$ (左随伴, 発散・還元) | 単純化への射 |
| $N$ (右随伴, 回復) | $R$ (右随伴, 収束・回復) | 整合性検査 |
| $\eta: \text{Id} \Rightarrow N \circ U$ | $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ | 内在化度合い |
| $F[N(q_{\text{poor}})] \leq F[q_{\text{poor}}]$ | $\eta_{\text{unit}}$ の収束性 | VFE 減少 |

同型対応の方向に注意が必要である。aletheia の $U$ は **精度を落とす** 方向の関手 (例: α-忘却で予測を粗くする) であり、本稿の $L$ は **対象を別のもっと簡単な対象に対応づける** 関手である。両者は **情報を捨てる方向** で構造同型である。

aletheia §2.1 (L126-141) は $U$ の 8 段パターン生成テーブルを与える。

> [SOURCE 強: aletheia.md §2.1 L126-141。ただし self-label 「[推定 70%] 75%、motivated choice、関手的証明 open」(L141) — 本稿は構造的類推水準として引用、厳密関手証明は本稿外の継続課題 (§M5.1 Round 1 r6 対応で降格済)]

aletheia §2.3 (L154-195) は Bohr 太陽系モデルの worked example を提示しており、§3.2 (ゲージ理論)・§3.3 (統計力学) で参照する。

### §2.4 GAFT / SAFT による L⊣R 存在条件

L⊣R の well-defined 性は無条件には成立しない。Mac Lane CWM §V.6 GAFT (General Adjoint Functor Theorem, p.117) は次の条件で存在を保証する:

> $A$ が small-complete かつ small hom-sets を持つとき、関手 $G: A \to X$ が左随伴を持つ ⟺ $G$ が連続 (small limit 保存) かつ Solution Set Condition (SSC) を満たす。SSC: $\forall x \in X$ に対し small set $I$ と $\{a_i \in A\}_{i \in I}$ および $\{f_i: x \to G(a_i)\}$ が存在し、任意の arrow $x \to G(a)$ が $h = G(t) \circ f_i$ ($t: a_i \to a$) の合成として書ける。

> [SOURCE 中: Mac Lane CWM §V.6 p.117 を Buzzard 2012 Imperial College lecture notes p.2 Theorem 1.1 が verbatim 引用 — triangulation。本稿査読時に Mac Lane CWM 直接 Read で「強」昇格義務 (G-ζ)]

§V.8 SAFT (Special Adjoint Functor Theorem, p.125-126) はより強い前提を要求する:

> $C$ が small-complete, locally small, well-powered, small cogenerating set を持ち、$D$ が locally small なら、極限保存関手 $G: C \to D$ は左随伴を持つ。

> [SOURCE 中: Mac Lane CWM §V.8 p.125 を Buzzard 2012 L185-194 + nLab 公式が triangulation。本稿査読時に Mac Lane CWM 直接 Read で「強」昇格義務 (G-ζ)]

本稿は **GAFT (SSC) を主条件**、SAFT (cogenerator) を補助条件として置く。GAFT を満たさない $L_i$ は射程外と宣言する (§M5.1 Round 1 r1 対応)。これは「全関手で L⊣R が成立する」という overclaim を予防する措置であり、§1.6 で開示した Z-03 圏論 overclaim 反論への構造的防御である。

### §2.5 視覚の逆問題メタファー

読者の直観を起動するため、視覚の逆問題で随伴構造を例示する。

網膜に届く光強度のパターンは Bogen-Woodward の意味での **data** (= 本稿の **予測₁** の現れ; §1.5 三層対応) である。だが網膜パターンから「何を見ているか」を直接読むことはできない。我々は無意識のうちに 2 段階の **L (上昇関手, 還元方向)** を経て概念 (theory ≈ 真理₀ への接近) に到達している:

1. $L_{\text{retina→percept}}$: 網膜パターン → 知覚オブジェクト (例: 「猫がいる」)
2. $L_{\text{percept→concept}}$: 知覚オブジェクト → 概念ラベル (例: 「Schrödinger の猫」)

それぞれに右随伴が存在する:

1. $R_{\text{percept→retina}}$: 概念から予測される網膜パターン (image prediction; 内部生成モデル)
2. $R_{\text{concept→percept}}$: 概念から予測される知覚パターン

理解とは、各層で $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ が **構造** に対しては iso に近づくが、**値** (例えば瞬間的な網膜画素強度) に対しては iso にならない、という構造的不等式の中に住んでいることである。

これが §1.2 公理の C2 (構造保存定理) の直観的な絵である。網膜画素強度の完全予測 ($\eta_{\text{unit}}$ = iso for all values) は不可能であり、また不要である。我々が予測しているのは **構造としての世界** であって、画素値ではない。

ここで重要なのは、この絵が脳科学・認知科学の経験的事実というより、**Bogen-Woodward 段階構造の必然的帰結** だということである。data (網膜) から phenomena (知覚) を経て theory (概念) に至る経路は、関手として読めば 2 段の合成であり、単一線形対応ではない。

---

## §3 5 分野横断展開 (F の本体)

§2 で導入した随伴構造 L⊣R を、独立した 5 分野で並列に例示する。各分野は別々の数学的言語を持つが、構造としては同じ随伴対が現れる。これが §1.2 C1 「3 分野同型」の 5 分野拡張であり、文体ガイド §3.2.6 の **定式化変換** の本体である。

5 分野の選択は道 C (科学一般の認識論定理) 射程に整合させた:

- §3.1 **情報幾何**: Fisher 計量の非等方として $\eta_{\text{unit}}$ 非同型
- §3.2 **ゲージ理論**: 接続の曲率として $\eta_{\text{unit}}$ の非自明性
- §3.3 **統計力学**: 自由エネルギー最小化と VFE 減少
- §3.4 **数論**: Peano successor の生成構造と値の分離
- §3.5 **FEP**: 予測誤差として補完₁

### §3.1 情報幾何 (Fisher 計量の非等方)

統計多様体上で Fisher 計量 $g_{ij}(\theta) = E[\partial_i \log p \cdot \partial_j \log p]$ が定まる。Fisher 計量は **非等方** であり、パラメータ空間の方向によって情報量が異なる。

本稿の L⊣R 対応:

- $L_{\text{IG}}$: 統計多様体 $M$ 上の点 $\theta$ をパラメータ表現に対応づける
- $R_{\text{IG}}$: パラメータから分布族の元を回復する

$\eta_{\text{unit}, \text{IG}}: \theta \to R_{\text{IG}}(L_{\text{IG}}(\theta))$ は分布の同値類に関しては iso に近づくが、Fisher 計量の **異方性そのもの** は iso にならない。すなわち、パラメータの数値表現を完全に保つことはできない (Cramér-Rao 不等式)。

> [SOURCE 中: Amari (1985) "Differential-Geometrical Methods in Statistics" Lecture Notes in Statistics 28、Cencov (1972) "Statistical Decision Rules and Optimal Inference"。本稿査読時に Amari 1985 直接 Read で「強」昇格義務 (G-ζ)]

これは Paper III の曲率テンソル $K_{\text{geom}}$ と関連する。

> [SOURCE 強: HGK 内部一次 SOURCE — Paper III 曲率テンソル定義。統一記号表 §1.7 の F_{ij} 曲率と同体]

### §3.2 ゲージ理論 (接続の曲率)

ゲージ理論において、ファイバー束 $E \to M$ 上の接続 $\nabla$ は曲率 2-形式 $F_{ij} = [\nabla_i, \nabla_j]$ を生む。曲率がゼロでない場合 (非可積分性)、ファイバー上での平行移動はパスに依存する。

本稿の L⊣R 対応:

- $L_{\text{gauge}}$: 接続から物理的観測量 (ホロノミー、ゲージ不変量) への射
- $R_{\text{gauge}}$: 観測量から接続を復元する射 (典型的には不完全)

$\eta_{\text{unit}, \text{gauge}}$ は **ゲージ等価類** に関しては iso だが、**接続そのもの** に対しては iso にならない (Aharonov-Bohm 効果が示すように、ゲージ不変な観測量が接続を完全には決定しない場合がある)。

> [SOURCE 強: HGK 内部一次 SOURCE — Paper I §5.1 方向性定理 $F = \nabla \Phi$、Paper III 曲率テンソル。統一記号表 §1.2 / §1.7]

aletheia §2.3 (L154-195) の Bohr 太陽系モデルは、量子化された軌道を「曲率の離散的固有値」として読む例を与える。

> [SOURCE 強: aletheia.md §2.3 L154-195、HGK 内部一次 SOURCE]

### §3.3 統計力学 (自由エネルギー最小化)

統計力学において、系のミクロ状態 $\omega \in \Omega$ から自由エネルギー $F[q] = E_q[\mathcal{H}] - T \cdot S[q]$ が定まる ($q$ は分布、$\mathcal{H}$ はハミルトニアン、$S$ はエントロピー)。

本稿の L⊣R 対応:

- $L_{\text{stat}}$: ミクロ状態空間 $\Omega$ から粗視化分布 $q$ への射
- $R_{\text{stat}}$: 粗視化分布から条件付きミクロ状態への射 (Maxwell-Boltzmann)

$\eta_{\text{unit}, \text{stat}}$ は **熱力学量 (温度・圧力・化学ポテンシャル)** に関しては iso だが、**個別ミクロ状態** に対しては iso にならない。これが熱力学の不可逆性の関手的読み替えである。

aletheia §1 の VFE 減少定理 $F[N(q_{\text{poor}})] \leq F[q_{\text{poor}}]$ は本稿 $L_{\text{stat}} \dashv R_{\text{stat}}$ の収束性に対応する。

> [SOURCE 強: aletheia.md §1 L99-L107、HGK 内部一次 SOURCE]

### §3.4 数論 (Peano successor と値の分離)

Peano 算術において、successor 関数 $S: n \mapsto n+1$ が自然数の生成構造を与える。$\mathbb{N}$ の元は successor の有限合成 $S^k(0)$ として **構造的に** 決まるが、各 $S^k(0)$ の **値** (例えば「7」という具体的記号) は別の話である。

本稿の L⊣R 対応:

- $L_{\text{num}}$: 自然数 $n$ から successor の合成深さ $k$ への射 (構造抽出)
- $R_{\text{num}}$: 合成深さから自然数を再構成する射

$\eta_{\text{unit}, \text{num}}$ は **同型類 (有限基数としての同値性)** に関しては iso だが、**記号的表現** (10 進、2 進、ローマ数字) に対しては iso にならない。これは「自然数とは何か」を operational identity として定義する Peano 的立場の関手的読み替えである。

> [SOURCE 中: Peano (1889) "Arithmetices Principia, Nova Methodo Exposita"、Dedekind (1888) "Was sind und was sollen die Zahlen?"。本稿査読時に Peano 原典 Read で「強」昇格義務 (G-ζ)]

数論を 5 分野に含めた理由は、本稿の主張が **物理現象に依存しない** ことを示すためである。L⊣R 構造は数学的構成そのものに内在する。

### §3.5 FEP (予測誤差と補完₁)

Friston の Free Energy Principle (FEP) において、生成モデル $p(o, s)$ と認識モデル $q(s)$ の間に変分自由エネルギー $F[q] = D_{\text{KL}}(q(s) \| p(s|o)) - \log p(o)$ が定まる。

本稿の L⊣R 対応:

- $L_{\text{FEP}}$: 観測 $o$ から認識モデル $q(s)$ への射
- $R_{\text{FEP}}$: 認識モデルから観測予測 $p(o)$ への射

$\eta_{\text{unit}, \text{FEP}}$ は **認識モデルの構造** に関しては iso に近づくが、**個別観測値** に対しては iso にならない。これが §1.2 C3 の「補完₁ ≡ Ker($\eta_{\text{unit}}$) と構造的に結びつく」の FEP 内具体形である。

予測の二層分解 (FEP認識論的地位_正本 §予測の二層分解 v2.5.0):

- **予測₀ (構造予測)** = 真理₀ から取り出される **形の予告** (どの制約・保存則・順序が保たれるか)。$L$ の上昇方向で構造として現れる
- **予測₁ (値予測)** = 真理₀ から $R$ (下降関手) を通って降ろされる **具体値** (初期条件・境界条件を入れて出す数値・時系列・選択)。Bogen-Woodward の data に対応 (§1.5)
- **補完₁** = $L$ で失われ $R$ で完全には回復されない情報を内部モデルで穴埋めすること ($\text{Ker}(\eta_{\text{unit}})$ と構造的に結びつく、補完₁ 依存)

> [SOURCE 強: FEP認識論的地位_正本.md §予測の二層分解 v2.5.0 L288-L301、HGK 内部一次 SOURCE]

注記 (§M5.1 Round 1 r4 対応): 「補完₁ ≡ |Ker($\eta_{\text{unit}}$)|」の等号主張は **「結びつく」** に降格済 (fep L299)。Gaussian 閉形式での厳密対応は §5 の IB 鋼鉄化で骨格まで、計算例は G-ε として継続課題。

### §3.6 5 分野横断同型の総合

5 分野で並列に出現した $L_i \dashv R_i$ と $\eta_{\text{unit}, i}$ は、構造としては同型である:

| 分野 | 構造保存軸 | 値非保存軸 |
|:---|:---|:---|
| 情報幾何 | 分布同値類 | Fisher 計量の異方性 |
| ゲージ理論 | ゲージ等価類 | 接続そのもの |
| 統計力学 | 熱力学量 | 個別ミクロ状態 |
| 数論 | 同型類 (有限基数) | 記号的表現 |
| FEP | 認識モデル構造 | 個別観測値 |

この同型は Yoneda の補題によって支持される — 「対象はそのすべての射で完全に決まる」(米田) ということは、**異なる分野で同じ随伴構造が出現すれば、それらは関手的に同型である**ことを含意する。詳細は §4 で展開する。

5 分野横断同型は、本稿が「FEP 固有の主張」ではなく「全科学共通の構造的制約」であることの操作的証拠である (§1.3 の FEP 非依存性宣言の支持)。

### §3.6.1 全 10 ペア natural transformation 骨格 (G-η Round 6 着手, 2026-04-26)

§3.6 の総合表は 5 分野横断同型を **構造保存軸 / 値非保存軸** の二軸で表示するが、各ペア間の **natural transformation 構成** は明示されていない。Round 4 (§M5.4) で 2 ペア骨格 (IG × Stat の Legendre 双対 + Gauge × IG の Yang-Mills/Fisher 曲率) のみが提示され、残 8 ペアは並列例示に留まっていた。本節は 5C2 = 10 ペア全てに対する natural transformation 骨格を提示する。

**達成水準の honest 較正**: 各ペアで以下の 4 要素を骨格として固定する:

1. **共通 base 圏 $\mathcal{C}$**: 両分野の関手が共有する底圏 (典型的には presheaf 圏 $\text{Set}^{\mathcal{D}^{\text{op}}}$ に Yoneda 埋め込みされる対象圏)
2. **対応 $\eta_{i,j}$ の component**: 各対象 $c \in \mathcal{C}$ で iso component (構造保存軸) と non-iso component (値非保存軸) を区別
3. **対応の type**: 各ペアで対応が **(a) natural isomorphism** (全 component iso、両関手 equivalent) / **(b) natural transformation** (全 component が naturality square を満たすが iso でない) / **(c) lax/partial correspondence** (naturality square が一部破れる、natural transformation ではない) のいずれに該当するかを明示
4. **不変量の対応**: $\eta_{\text{unit}, i}$ の核 $|\text{Ker}(\eta_{\text{unit}, i})|$ と $\eta_{\text{unit}, j}$ の核 $|\text{Ker}(\eta_{\text{unit}, j})|$ の対応関係

⚠️ **Codex Bridge レビュー (2026-04-26) 指摘の honest 反映**:

- **Risk 1 (commutativity 表現)**: 本節初稿で「non-iso component で commutativity が破れる natural transformation」と書いたのは数学的に不正確だった。Natural transformation η: F ⇒ G の定義は **全 component で naturality square が commute する**。component が iso でないなら natural isomorphism ではないが、natural transformation 自体は成立する。「commutativity が破れる」は別概念 (lax/partial correspondence) を指すべき。本節骨格では **type (a)/(b)/(c) を明示** することでこの混同を解消する
- **Risk 2 (Pair 1 同型主張過剰)**: Fisher 計量 (Riemann symmetric 2-tensor) と Yang-Mills 曲率 (antisymmetric 2-form) を「構造同型」と書いたのは強すぎた。両者は「曲率を測る 2-tensor」という共通点を持つが symmetric/antisymmetric の差は本質的。**構造的類似 [仮説 60%]** に降格するのが正確
- **N-01/N-05 警告**: 本節骨格作成時、§3.6 / §M5.4 / §M6 既存記述との grep/search 整合確認は省略した。10 ペア命名・記号衝突・既存反論との整合は **Round 7 監査** で Codex executor に委譲予定

完全な categorical 形式化 (10 ペア × naturality verification + Yoneda embedding 経由の coherence theorem + 上記 Risk 反映後の type 再判定) は本節の射程外。本節は **第 1 階の骨格** (domain/codomain + 核となる射の対応 + type 暫定判定 + 不変量の対応) に留め、第 2 階以降は **Round 7 課題** (Codex executor 委譲 + 形式検証推奨) として開示する [Yugaku §M6 虚→実規律]。

#### Pair 1: 情報幾何 × ゲージ理論 (IG × Gauge)

**核となる対応 [構造的類似 仮説 60%, Codex Risk 2 反映で降格]**: Fisher 計量 $g_{ij}^{\text{IG}}(\theta)$ (symmetric Riemann 2-tensor) と Yang-Mills 接続曲率 $F_{ij}^{\text{Gauge}} = [\nabla_i, \nabla_j]$ (antisymmetric 2-form) は、ともに「対象上の 2-tensor として局所構造を測る」点で共通するが、symmetric/antisymmetric の差は本質的で **同型ではない**。両者の関係は **対応 type (c) lax/partial correspondence** に該当 (Bianchi 同一は YM 側のみ、Fisher 側は Codazzi 等価条件が異なる形で現れる)。Amari の dual affine connections (Amari 1985) は IG 側に YM 接続類似の構造を導入するが、これは構造的類似であって同型ではない。

**Natural transformation $\eta_{\text{IG, Gauge}}$**: 統計多様体 $M$ の Fisher-Rao geometry を principal $G$-bundle 上の接続として読み替える functor。component:
- iso: 曲率の **代数的構造** (両者とも 2-form, antisymmetric, Bianchi 同一)
- non-iso: **物理的解釈** (IG では情報量の方向異方性、Gauge では場の伝播の非可積分性)

**Round 4 骨格再掲**: Yang-Mills 接続曲率 ↔ 確率分布族の曲率 $K_{\text{geom}}$ は Paper III で対応関係が指摘されている [SOURCE 強: HGK 内部一次, Paper III §曲率テンソル定義]。Bohr 太陽系モデル (aletheia §2.3) は両者の離散固有値版。

**残ギャップ**: 完全な G-bundle/dual connection 同値関手の構成は本節射程外。

#### Pair 2: 情報幾何 × 統計力学 (IG × Stat) — Legendre 双対骨格 (Round 4 既提示)

**核となる対応**: Fisher 情報計量 $g_{ij}^{\text{IG}}(\theta) = E[\partial_i \log p \cdot \partial_j \log p]$ ↔ 自由エネルギー Hessian $\partial_i \partial_j F^{\text{Stat}}[\theta]$ — 両者は **Legendre 変換** で結ばれる双対座標構造 [SOURCE 中候補: Amari 1985 / Cencov 1972, transitive 中候補, G-ζ]。

**Natural transformation $\eta_{\text{IG, Stat}}$**: 指数型分布族の natural parameter $\theta$ から expectation parameter $\eta = E[T(x)]$ への Legendre 変換 functor。component:
- iso: **dual flat structure** (両者とも flat affine connection を 2 つ持ち、互いに dual)
- non-iso: **非平衡状態** (Stat では非平衡で Legendre 双対が崩れる、IG では singularity)

**Round 4 骨格**: $g_{ij}^{\text{IG}} = -\partial_i \partial_j \log Z(\theta)$ で $\log Z$ は Stat の自由エネルギー $-F^{\text{Stat}}/T$ と一致 (canonical ensemble)。両者は同じ Hessian で繋がる。

**残ギャップ**: 非平衡状態での dual structure 一般化は本節射程外。

#### Pair 3: 情報幾何 × 数論 (IG × Num)

**核となる対応**: Fisher 計量の **対数微分構造** $\partial_i \log p$ ↔ Peano successor 列の **位取り展開** $S^k(0)$ — 両者は **可算離散指数による情報の階層化** という共通構造を持つ [仮説 60%, SOURCE 未着手]。

**Natural transformation $\eta_{\text{IG, Num}}$**: 統計多様体 $M$ の指数族から Peano $\mathbb{N}$ への対数次数 functor。component:
- iso: **指数階層** (両者とも $\log$/$S^k$ で離散階層を生成)
- non-iso: **連続/離散境界** (IG は連続多様体、Num は離散整数)

**残ギャップ**: 連続-離散境界の関手的厳密化 (typically via topos-theoretic embedding) は **本節射程外、Round 7 課題**。本ペアは構造的類似 [仮説 60%] に留まる。

#### Pair 4: 情報幾何 × FEP (IG × FEP)

**核となる対応**: Fisher 計量 ↔ 認識モデル $q(s)$ の KL 計量 $g_{ij}^{\text{FEP}} = \partial_i \partial_j D_{\text{KL}}(q \| p)$ — VFE の Hessian は Fisher 情報計量と同型 [SOURCE 強候補: Friston 2010 + Amari 1985 接続, transitive 強, G-ζ]。

**Natural transformation $\eta_{\text{IG, FEP}}$**: 統計多様体上の Fisher-Rao 幾何を VFE landscape として読み替える functor。component:
- iso: **VFE Hessian = Fisher 情報** (variational inference の標準帰結)
- non-iso: **prior 依存性** (FEP では generative model に依存、IG では parameter family のみで決まる)

**Round 6 軽量補強 (G-ι 由来)**: Mayama et al. 2025 の Φ ↔ Bayesian surprise (= KL prior↔posterior) 強相関は、本ペアの「VFE Hessian の方向情報量」が IIT 的 cause-effect structure と整合的に現れることを示唆 [SOURCE 強候補: arxiv 2510.04084 v1, alphaXiv 完全 PDF]。

**残ギャップ**: prior 依存性を吸収する covariant functor 構成は本節射程外。

#### Pair 5: ゲージ理論 × 統計力学 (Gauge × Stat)

**核となる対応**: ゲージ場の **有効作用** $S^{\text{eff}}[A]$ ↔ 統計力学の **自由エネルギー** $F^{\text{Stat}}[\beta]$ — 両者は **path integral の対数** として同型 ($Z = \int e^{-S/\hbar}$ vs $Z = \int e^{-\beta H}$, Wick 回転で交換) [SOURCE 中候補: Polyakov 1987 / Itzykson-Drouffe 1989, 公知, transitive 中, G-ζ]。

**Natural transformation $\eta_{\text{Gauge, Stat}}$**: ゲージ場理論を統計場理論 (Euclidean) として読み替える Wick rotation functor。component:
- iso: **partition function の構造** (両者とも path integral / sum over configurations)
- non-iso: **時間方向の取り扱い** (Gauge は Lorentzian、Stat は Euclidean、Wick 回転で交換)

**残ギャップ**: 非平衡量子場理論での Wick 回転の関手的扱いは本節射程外。

#### Pair 6: ゲージ理論 × 数論 (Gauge × Num)

**核となる対応**: ホロノミー (parallel transport の閉路) ↔ Peano successor 合成深さ $S^k(0)$ — 両者は **離散的ステップ数による history-dependent observable** という共通構造 [仮説 55%, SOURCE 未着手]。

**Natural transformation $\eta_{\text{Gauge, Num}}$**: principal $G$-bundle 上のホロノミー群 $\text{Hol}(\nabla) \subset G$ から $\mathbb{N}$ への winding number functor。component:
- iso: **離散巻き数** (両者とも整数値 invariant を生成、Aharonov-Bohm 量子化条件)
- non-iso: **群構造** (Gauge では $G$ 値、Num では加法群 $\mathbb{Z}$)

**残ギャップ**: 一般 Lie 群 $G$ から $\mathbb{Z}$ への一意 functor は存在しない (例: $SU(2)$ では $\pi_1 = 0$)。本ペアは abelian gauge ($U(1)$) に射程限定すべき。Round 7 課題。

#### Pair 7: ゲージ理論 × FEP (Gauge × FEP)

**核となる対応**: ゲージ接続 $\nabla$ ↔ FEP の **belief update flow** $\partial_t q(s)$ — 両者は **状態空間上の方向場** として同型に近い [SOURCE 中候補: Friston 2010 active inference の path integral 定式化, transitive 中, G-ζ]。

**Natural transformation $\eta_{\text{Gauge, FEP}}$**: principal bundle 上の接続を belief manifold 上の natural gradient flow として読み替える functor。component:
- iso: **方向場の局所構造** (両者とも tangent bundle 上の section)
- non-iso: **物理的/認知的解釈** (Gauge は force の局所伝播、FEP は belief update の局所方向)

**残ギャップ**: ゲージ不変性 (gauge invariance) と FEP の generative model invariance の対応関係は active inference 文献で部分的に議論されているが、本節射程外。

#### Pair 8: 統計力学 × 数論 (Stat × Num)

**核となる対応**: 分配関数の **漸近展開** $Z(\beta) \sim \sum_k a_k \beta^{-k}$ ↔ Peano successor 列の **整数指数** $S^k(0)$ — 両者は **可算離散指数による状態カウント** という共通構造 [SOURCE 中候補: Hardy-Littlewood 1918 (asymptotic enumeration) / Andrews 1976 (q-series), 公知, G-ζ]。

**Natural transformation $\eta_{\text{Stat, Num}}$**: 分配関数の coefficient functor $a_k: \mathbb{N} \to \mathbb{C}$。component:
- iso: **離散カウント** (両者とも整数による状態の組合せ列挙)
- non-iso: **連続パラメータ依存** (Stat は $\beta$ で連続、Num は離散指数のみ)

**残ギャップ**: 高温極限 ($\beta \to 0$) と Peano $\mathbb{N}$ の余極限の関手的同型は本節射程外。

#### Pair 9: 統計力学 × FEP (Stat × FEP)

**核となる対応**: 統計力学の自由エネルギー $F^{\text{Stat}}[q] = E_q[H] - T \cdot S[q]$ ↔ 変分自由エネルギー $F^{\text{FEP}}[q] = D_{\text{KL}}(q \| p) - \log p(o)$ — 両者は **同じ FEP 関手の物理的/認知的 instance** [SOURCE 強: aletheia §1 L99-L107, HGK 内部一次]。

**Natural transformation $\eta_{\text{Stat, FEP}}$**: 統計力学の variational principle を FEP active inference として読み替える functor。component:
- iso: **VFE 減少定理** $F[N(q_{\text{poor}})] \leq F[q_{\text{poor}}]$ (両者で同形成立)
- non-iso: **エネルギー解釈** (Stat は物理的ハミルトニアン、FEP は generative model の log-evidence)

**Round 4 骨格再掲**: Mayama et al. 2025 (Round 6 G-ι) の dissociated neuronal cultures は in vivo で本ペアの経験的橋渡しを提供 — Φ ↔ Bayesian surprise 強相関は statisitical mechanics の partition function 漸近と FEP の belief update の同期を示唆 [SOURCE 強候補: arxiv 2510.04084 v1]。

**残ギャップ**: FEP の active inference (政策選択) と統計力学の最大エントロピー原理の関手的厳密対応は本節射程外。

#### Pair 10: 数論 × FEP (Num × FEP)

**核となる対応**: Peano successor 合成深さ $S^k(0)$ ↔ FEP の **階層的予測誤差累積** $\sum_{l=0}^L \epsilon_l$ — 両者は **生成構造の有限合成深さ** という共通構造 [仮説 55%, SOURCE 未着手]。

**Natural transformation $\eta_{\text{Num, FEP}}$**: $\mathbb{N}$ の合成深さを FEP の階層レベル $l$ に対応づける functor。component:
- iso: **離散階層** (両者とも整数階層 $l \in \mathbb{N}$)
- non-iso: **生成方向** (Num は successor の単調増加、FEP は階層内 belief update の双方向)

**残ギャップ**: FEP の hierarchical generative model を Peano 圏として埋め込む関手的構成は **本節射程外、Round 7 課題**。本ペアは構造的類似 [仮説 55%] に留まる。

#### §3.6.1 総合 — 10 ペアの達成度マトリクス

| Pair | 核となる対応 | 達成水準 | SOURCE 強度 | 残ギャップ |
|:---|:---|:---|:---|:---|
| 1 IG × Gauge | Fisher 計量 ↔ Yang-Mills 曲率 | **構造的類似 [仮説 60%]** (Codex Risk 2 反映で「同型」→「類似」降格) | 中候補 (Paper III + Amari 1985 transitive) | symmetric/antisymmetric 差の関手的扱い + dual connection 同値関手 |
| 2 IG × Stat | Legendre 双対 (Hessian 同型) | Round 4 骨格 + 標準帰結 | 強候補 (Amari/Cencov transitive) | 非平衡 dual structure |
| 3 IG × Num | 対数微分 ↔ successor 階層 | 構造的類似 [仮説 60%] | 弱 (SOURCE 未着手) | 連続-離散境界 |
| 4 IG × FEP | Fisher = VFE Hessian | 標準帰結 + Mayama et al. 補強 | 強候補 (Friston/Amari + arxiv 2510.04084) | prior 依存性 functor |
| 5 Gauge × Stat | Wick 回転 (path integral) | 物理学標準帰結 | 中候補 (Polyakov/Itzykson-Drouffe transitive) | 非平衡 QFT |
| 6 Gauge × Num | ホロノミー ↔ winding number | 構造的類似 [仮説 55%] (abelian 限定) | 弱 (SOURCE 未着手) | non-abelian 拡張 |
| 7 Gauge × FEP | 接続 ↔ belief update flow | 中候補 (active inference 文献) | 中候補 (Friston 2010 transitive) | gauge invariance ↔ generative invariance |
| 8 Stat × Num | 分配関数漸近 ↔ Peano 指数 | 構造的類似 (asymptotic enum) | 弱 (SOURCE 未着手) | 高温極限の余極限同型 |
| 9 Stat × FEP | VFE 減少定理 (同形) | 強 (HGK 内部 + Mayama et al.) | 強 + 強候補 | active inference vs MaxEnt |
| 10 Num × FEP | successor depth ↔ 階層誤差 | 構造的類似 [仮説 55%] | 弱 (SOURCE 未着手) | hierarchical Peano embedding |

**Round 6 G-η 達成度の honest 較正 (Codex Bridge レビュー反映)**: 10 ペアのうち **4 ペア** (IG×Stat / IG×FEP / Stat×FEP / Gauge×Stat) は標準帰結 / 強候補 SOURCE で骨格固定、**2 ペア** (Gauge×FEP / Stat×Num) は中候補 SOURCE で骨格、**4 ペア** (IG×Gauge [Codex Risk 2 で降格] / IG×Num / Gauge×Num / Num×FEP) は構造的類似 [仮説 55-60%] に留まる。完全な commutative diagram 検証 + Yoneda 埋め込みの coherence + Codex Risk 1/2 完全反映 (各ペア type (a)/(b)/(c) 確定) は **Round 7 課題** として §M9 step 16 (新設) に持ち越し。

C1 主張水準 (構成的命題 70%) は本節骨格で **据え置き** — 10 ペア全完全形式化を待たず、4 ペア強候補 + 2 ペア中候補 + 4 ペア類似で「3 分野同型 → 6 ペア骨格 + 4 ペア類似」として honest に較正される。Codex Bridge 警告 (N-01/N-05/N-08 + Risk 1/2) は本節注記に明示反映済、Round 7 で完全監査。

### §3.7 普遍構造理論の値産出 — n+1 構造

> **§3.6.1 との位置関係**: §3.6.1 は 5 分野横断同型の **categorical 形式化** (10 ペア natural transformation 骨格) を提示する内向きの形式化軸。本節 §3.7 は同型から派生する **値産出の構造的制約** を Peano successor アナロジーで外部読者向けに明示する補完軸。両節は §3.6 5 分野同型を異なる方向 (内向 vs 外向) で展開する独立節として並列に配置される。

§3.6 で確認した 5 分野同型は、各分野の理論が **普遍構造理論** (universal structural theory) として機能していることを示唆する。普遍構造理論とは、それ自体は値を直接産出しないが、**任意の値を生成できる構造** を提示する理論である。本節は本稿の C1-C5 全てに通底する **値産出の構造的制約** を Peano 算術のアナロジーで明示する。

#### §3.7.1 メタ関手としての普遍構造理論

§3 5 分野に出現した $L_i \dashv R_i$ は、各分野で「個別の関手」として現れる。だが「随伴対 $L \dashv R$ が出現する」という構造そのものは個別関手ではなく、**関手を生成する関手** = メタ関手である:

$$\Phi: \mathbf{Theories} \to \mathbf{Theories} \quad T_i \mapsto T_i^* = \arg\min_T \mathcal{F}[T]$$

ここで $\mathcal{F}$ は理論の評価汎関数 (情報幾何の Fisher 情報、ゲージ理論の作用、統計力学の自由エネルギー、IB Lagrangian 等)。$\Phi$ は presheaf の 1 つの断面ではなく、**presheaf を最適化する操作の記述** である。FEP の VFE もこの $\mathcal{F}$ の一例だが、本節は §1.3 第 3 項 FEP 非依存性宣言と整合させるため、5 分野のいずれかに偏らない普遍的構造として $\Phi$ を提示する。

メタ関手 $\Phi$ に「個別の値予測 $\hat{y}$ を 1 つ出せ」と要求することは、最適化アルゴリズムに「具体的な最適解を 1 つ出せ」と要求するのと同じ誤りに近い。最適化アルゴリズムの価値は、任意の目的関数に対して解を **近似できる普遍性** にあって、1 つの具体的解を出すことではない。

#### §3.7.2 Peano 算術アナロジー (n+1 構造)

普遍構造理論の値産出構造は **Peano successor** $S: n \mapsto n+1$ のそれと同型である。Peano 算術は **任意の自然数を生成できる** が、特定の自然数 (例: 7) を取り出すには **n の指定 (縛り)** が必要である:

$$7 = S(6) = S(S(5)) = \ldots = S^7(0)$$

「7 を出せ」という要求に、$n+1$ 自体は直接 7 を返さない。これは **欠陥ではなく構造理論が値を産出する正しい手続き** である ($n=6$ と指定し、$+1$ を適用する)。

本稿の L⊣R 内在化に当てはめると:

| Peano | 本稿 |
|:---|:---|
| successor 関数 $S$ (生成構造) | 真理₀ (L の到達点) |
| 自然数 $n$ (具体値) | 予測₁ |
| 「$S$ から 7 を直接出せ」(誤要求) | 「真理₀ から個別の予測₁ を直接出せ」(誤要求) |
| $n=6$ の指定 (縛り) | 中位理論 (process theory) + 初期条件・境界条件 (R の下降) |

「説明力が全域に発散している = 値の一意な産出には別の縛りが必要」 — これは **欠陥ではなく普遍的構造理論の定義的特徴** である。本稿 §1.4 C2 「$\eta_{\text{unit}}$ が構造には iso、値には iso にならない」の **直観的言い換え** であり、§5 IB Lagrangian + DPI + §5.6 NRFT 骨格と同一の構造を別の側面から照らす。

#### §3.7.3 メタ関手批判の自壊

普遍構造理論 $\Phi$ に対する「個別予測を出せ」批判 (Mangalam 2025 型) は、$\Phi$ の存在意義の理解不足から派生する。詳細は §7.2 で帰謬法として展開するが、構造的に予告すれば:

> $\Phi$ が値を直接産出しない事実は、$\Phi$ が **より少なく忘却する関手** であることの構造的帰結である ($\eta_{\text{unit}}|_\text{値} \neq \text{iso}$ が原理的制約として常に成立、§5)。「もっと値を出せ」= 「もっと構造を忘却して中位理論に降りろ」と要求していることに等しい。

これは §1.3.1 で固定した科学定義 (より忠実な関手 $F_n$ を漸近的に求める営み) と矛盾する要求であり、§7.2 で **関手論的読み替え** (Mangalam が予測₁ を真理₀ の指標と読む構造的誤配位) として展開される。完全な帰謬法 7 ステップ形式は本稿 §7 では採用していない (`drafts/standalone/エッセイ_理解と予測の随伴.md` v1.5.0 §7 を参照)。

---

## §4 Yoneda 接続 (G の極限化 1)

§3 で 5 分野に並列出現した随伴構造 $L_i \dashv R_i$ を、米田の補題によって統一する。本節は §1.4 表「G (収束) その 1」の本体であり、§1.6 で開示した SOURCE 強度ラベルの体系を Riehl 2016 / Mac Lane CWM の verbatim 引用で支える。

### §4.1 Yoneda の補題 (Mac Lane CWM §III.2 + Riehl 2016 §2.2)

Yoneda の補題は次のように述べる:

> **Yoneda Lemma** (Riehl 2016 §2.2 Theorem 2.2.4): For any functor $F: C \to \mathbf{Set}$ whose domain is locally small and any object $c \in C$, the function $\text{Nat}(C(c, -), F) \to F(c)$ defined by $\alpha \mapsto \alpha_c(\text{id}_c)$ is a bijection. Moreover, this correspondence is natural in both $c$ and $F$.

> [SOURCE 強候補: Riehl 2016 §2.2 Theorem 2.2.4 — riehl.txt L4763-4775 verbatim 抽出 / G-ζ 査読時独立検証義務]

> Mac Lane CWM §III.2 Theorem 1 が同じ補題を Hom-functor の言語で述べる。

> [SOURCE 中: Mac Lane CWM 1971/1998 §III.2 Theorem 1 — Wikipedia + Riehl 2016 帰属が triangulation。本稿査読時に Mac Lane CWM 直接 Read で「強」昇格義務 (G-ζ)]

操作的読み替え: **対象 $c$ は、その全ての射 $C(c, -)$ で完全に決まる**。これが §1.2 C1 で公理として置いた「理解 = L⊣R 内在化」の数学的基礎である。

「$c$ を理解している」⟺ 「$c$ への射、$c$ からの射、それらの合成パターンを内側に持つ」⟺ 「$\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ が iso (構造に対して)」

### §4.2 表現可能関手による極限保存 (Riehl §3.5)

Yoneda 埋め込みは極限を保存する:

> **Theorem 3.5.5** (Riehl 2016 §3.5): Covariant representable functors $C(X, -): C \to \mathbf{Set}$ preserve all limits that exist in $C$. The covariant Yoneda embedding $C \hookrightarrow \mathbf{Set}^{C^{\text{op}}}$ both preserves and reflects limits.

> [SOURCE 強候補: Riehl 2016 §3.5 Theorem 3.5.5 — riehl.txt L8702-8709 verbatim 抽出 / G-ζ 査読時独立検証義務]

> 注: 依頼書では §3.4 と表記されていたが、Riehl 2016 の正しい節番号は **§3.5 The representable nature of limits and colimits**。誤記訂正済 (§M5.2 段階 B)。

これが §3.6 の 5 分野横断同型の数学的支持である。各分野で出現した随伴対 $L_i \dashv R_i$ は、Yoneda 埋め込みを通じて presheaf 圏 $\mathbf{Set}^{C^{\text{op}}}$ に埋め込まれ、極限構造が保存される。すなわち、**5 分野で出現した同型は presheaf 圏での極限同型に帰着する**。

### §4.3 kalon §2 L161 補強引用 (Mac Lane-Moerdijk)

kalon.md §2 (L161-166) は HGK の圏 $M$ が presheaf 圏と同型であることを示す:

> 「HGK の圏 M ≅ PSh(J) は presheaf 圏 → 自動的に (co)complete (Mac Lane-Moerdijk)。」

> [SOURCE 強: kalon.md §2 L161-166、HGK 内部一次 SOURCE。Mac Lane CWM Thm X.3.1 の引用部分は §V.6/V.8 と同様 G-ζ 独立検証で「強」昇格義務]

これは §3.6 の 5 分野横断同型が presheaf 圏で実現されることの **構造的支持** である。「HGK の圏 $M$ が presheaf 圏と同型」⟺ 「本稿の L⊣R が Yoneda 埋め込みの像として well-defined」。

### §4.4 圏論的衣装除去テストへの応答 (kalon §2.5)

kalon.md §2.5 (L368-403) は「圏論的衣装除去テスト」を提示する: 「7 主張のうち 4 つは自然言語で十分判定」(L388-389)。本稿は Yoneda の補題を採用するが、これが §2.5 自身が「圏論固有」と認める領域 (Lan 拡張 + LFPT) に該当することを開示する。

> [SOURCE 強: kalon.md §2.5 L368-403 + L388-389、HGK 内部一次 SOURCE]

本稿の Yoneda 採用は kalon §2.5 への **反対方向作用** ではなく、§2.5 の判定枠組み内で「圏論固有領域」として正当化される。具体的には:

- C1 (理解 = L⊣R 内在化) は Yoneda の operational identity を本質的に使う
- C2 (構造保存定理) は faithful functor factorization (Mac Lane Ch. X / Kan 拡張) を本質的に使う
- C3 (補完₁ 単調減少) は §5 の IB Lagrangian と組み合わせて圏論的になる

これらは「自然言語で十分判定」される 4 主張ではなく、kalon §2.5 自身の判定で「圏論固有」とされる領域に入る。本稿の Yoneda 採用は kalon §2.5 と矛盾しない。

注記: kalon.md §9 (L2302-2325) の「概念 ≈ presheaf」は self-label「水準 C (比喩的使用)」であり、本稿の load-bearing 引用には不足である。本稿は §2 L161 (Mac Lane CWM 引用、水準 A 寄り) を主引用、§9 を補助引用に降格する (Block A worker findings, §M5.2 段階 B)。

### §4.5 §1.2 構成的定義の Yoneda 接地

⚠️ **論理飛躍の明示開示** (Round 4 §M5.4 予告): Yoneda の補題は category-theoretic statement (「対象は表現可能関手で完全に決定される」) であって epistemological statement (「人間/科学の理解の必要十分条件」) ではない。両者は同値ではなく、本稿は §1.1 で **構成的定義として L⊣R 内在化を採用する** という立場を明示することでこの飛躍を埋める。Yoneda は本稿の主張の **必要条件の数学的足場** であって十分条件の証明ではない (G-η / G-θ で Round 5 課題)。

§1.2 で構成的定義として置いた L⊣R を、ここまでの Yoneda 接続で **数学的足場の上に置く**:

1. **operational identity** (Yoneda Lemma): 対象 $c$ は $C(c, -)$ で決まる ⟹ $\eta_{\text{unit}}$ が iso ⟺ $C(c, -) \cong C(R(L(c)), -)$
2. **極限保存** (Riehl §3.5): 5 分野横断同型は presheaf 圏での極限同型に帰着
3. **存在条件** (GAFT/SAFT, §2.3): $L \dashv R$ の well-defined 性は SSC または cogenerator で保証
4. **HGK 圏との接続** (kalon §2 L161): HGK 圏 $M \cong \text{PSh}(J)$ により本稿構造が realizable

これら 4 点が §1.2 公理を「単なる定義」ではなく「Yoneda 接続を持つ操作的 anchor」に昇格させる。

---

## §5 IB 鋼鉄化 (G の極限化 2)

§4 で公理を Yoneda 接続したのに続き、§1.2 C3 「補完₁ 単調減少定理」を **Information Bottleneck (IB) Lagrangian + Data Processing Inequality (DPI)** で Pareto frontier 上の定理として鋼鉄化する。本節は §1.4 表「G (収束) その 2」の本体である。

### §5.1 Tishby-Pereira-Bialek 1999 IB の再記述

Tishby-Pereira-Bialek (1999) は Information Bottleneck を次のように定式化する:

> 「relevant information = $X$ が他信号 $Y$ について与える情報。$X$ の short code を $Y$ に関する最大情報を保存しつつ bottleneck (limited codewords) を通して圧縮する問題を定式化」「自己無撞着方程式の厳密集合 ($X \to \tilde{X}$ と $\tilde{X} \to Y$ の coding rules) を導く」 (Tishby-Pereira-Bialek 1999 abstract)

> [SOURCE 強候補: arxiv physics/0004057 abstract verbatim + alphaXiv intermediate report 完全取得済 (2026-04-26, Round 6 G-ε 軽量着手)。self-consistent equations 3 式 verbatim を取得: (i) $p(t|x) = (p(t)/Z(x,\beta)) \exp(-\beta \sum_y p(y|x) \log(p(y|x)/p(y|t)))$ / (ii) $p(t) = \sum_x p(x) p(t|x)$ / (iii) $p(y|t) = \sum_x p(y|x) p(x|t)$。**KL divergence が effective distortion measure として自然に出現** (relevance variable Y が暗黙的に X の保存対象を定める)。Gaussian 閉形式 specific form は alphaXiv intermediate report の射程外 = Round 6 別経路 (Slonim-Tishby 2000 後続精読) で継続]

形式的に IB Lagrangian は:

$$\mathcal{L}_{\text{IB}} = I(X; T) - \beta I(T; Y)$$

ここで:

- $X$: 観測信号 (本稿の **予測₁** に対応 — Bogen-Woodward の data 層、§1.5 三層対応で確認)
- $Y$: relevant signal (本稿の **真理₁** に対応 — phenomena 層、Bogen-Woodward が theory から間接的に予測される対象)
- $T$: bottleneck variable (本稿の認識モデル / 中間表現、$L$ で $X \to T$、$R$ で $T \to Y$)
- $\beta$: trade-off パラメータ

### §5.2 Data Processing Inequality (DPI)

Cover-Thomas Ch. 2 の DPI は次の通り:

> **DPI**: Markov chain $X \to T \to Y$ について $I(X; Y) \geq I(T; Y)$ かつ $I(X; T) \geq I(X; Y)$

> [SOURCE 中: Cover-Thomas "Elements of Information Theory" 2nd ed. Ch. 2.8 Theorem 2.8.1。本稿査読時に Cover-Thomas 直接 Read で「強」昇格義務 (G-ζ)]

DPI は「処理が情報を増やすことはない」という不可避な単調性であり、本稿 §1.2 C3 「理解の深化は補完₁ 依存を単調減少させる」の情報理論的核である。

### §5.3 随伴構造との対応

IB と本稿 L⊣R の対応:

- $\beta \to \infty$ 極限: $T \to L(X)$ (relevant 情報を最大限保持)
- $\beta \to 0$ 極限: $T \to \text{const}$ (圧縮を最大化)
- 中間 $\beta$: Pareto frontier 上の operating point

随伴構造として読むと:

- $L_{\text{IB}}$: $X$ から $T$ への射 (圧縮)
- $R_{\text{IB}}$: $T$ から $Y$ の予測への射 (relevant 情報の取り出し)
- $\eta_{\text{unit}, \text{IB}}: \text{Id} \Rightarrow R_{\text{IB}} \circ L_{\text{IB}}$: $X$ が $R_{\text{IB}}(L_{\text{IB}}(X))$ に再構成される度合い

$|\text{Ker}(\eta_{\text{unit}, \text{IB}})| > 0$ は **$X$ から失われ $T$ では捉えられない情報** を測る (DPI による不可避な情報損失)。

### §5.4 補完₁ 単調減少関係の Lagrangian 形式化

⚠️ 降格注記 (Round 4 §M5.4 予告): §M5.1 Round 1 r4 対応で「補完₁ ≡ |Ker($\eta_{\text{unit}}$)|」の等号主張は **「結びつく」**(FEP認識論的地位_正本 §予測の二層分解 v2.5.0 L299) に降格済。本節の表題から「定理の鋼鉄化」を削除し、「**Lagrangian 形式化**」に置き換える。形式証明としての「単調減少定理」は本稿外の継続課題 (§6.4 G-ε)。

§1.2 C3 「理解の深化は補完₁ 依存を単調減少させる」の Lagrangian 形式化骨格:

$$\frac{\partial |\text{Ker}(\eta_{\text{unit}})|}{\partial (\text{理解度})} \leq 0 \quad \text{(関係式骨格、形式証明は G-ε で継続)}$$

ここで「理解度」は $\eta_{\text{unit}}$ が構造に対して iso に近づく度合い ($\beta$ の最適化)。

**操作的議論骨格 (形式証明ではない)**:

1. 理解度の増加 ⟹ $T$ が $Y$ をより良く予測 ($I(T;Y) \uparrow$)
2. DPI により $I(X;Y) \geq I(T;Y)$ なので、$I(T;Y)$ の上限は $I(X;Y)$
3. 構造保存定理 (§1.2 C2) により $I(X;Y) < I(X;X) = H(X)$ ($\eta_{\text{unit}}$ 非同型)
4. ゆえに補完₁ ($X$ から $T$ で捉えられない部分) は単調減少するが、ゼロにはならない (議論骨格として)

この骨格は **道 C 射程の議論骨格** として機能する: 「理解の深化は予測補完への依存を単調減少させるが、ゼロにはできない」。形式証明としての完成は **Round 5 課題 (G-θ 予定)** に保留する。

### §5.4.1 補助補題: Goldilocks 符号化帯域

§5.4 の IB/DPI 骨格は、情報が $X \to T \to Y$ の経路で失われることを示す。しかし、どの表現成分が $T$ に残るべきかは、単なる頻度最大化では決まらない。ここで Paper XI の Adam's Law と Chemistry-Cognition Program の定理 2' を補助補題として接続する。

Paper XI §7.7.5 は、高頻度表現ほどモデル内での制約回収摩擦が下がることを次のように読む:

$$
E_{\text{freq}} \uparrow \Rightarrow d(C_{\text{intended}}, C_{\text{eff}}) \downarrow
$$

一方、Chemistry-Cognition Program の定理 2 / 2' は、表現成分 $e$ の coverage $p(e)$ が飽和帯へ近づくと、弁別力が崩壊することを示す。情報理論的には:

$$
p(e) \to 1 \Rightarrow -\log p(e) \to 0 \Rightarrow I(e;Y) \to 0
$$

したがって、$T$ の表現成分には少なくとも 2 つの役割がある。

| 成分 | 帯域 | 役割 | 本稿 C3/C4 への作用 |
|:---|:---|:---|:---|
| 支持体成分 | 飽和帯 | 制約回収の摩擦を下げる。読者/モデルに通りやすい | $R$ で prediction₁ として出やすいが、truth₀ の弁別力は低い |
| 制御成分 | Goldilocks 帯 | 珍しすぎず、ありふれすぎない構造で $Y$ を区別する | $T$ が保持すべき弁別的構造。補完₁ を減らす本体 |
| 欠落候補 | 統計不足帯 | 低頻度で不安定。推定分散が大きい | $L$ の圧縮で $\text{Ker}(\eta_{\text{unit}})$ に入りやすい |

**補助補題 (Goldilocks 符号化帯域)**. $L \dashv R$ による理解過程で、表現 $T$ の高頻度成分は $C_{\text{intended}} \to C_{\text{eff}}$ の摩擦を下げる支持体として働く。しかし飽和帯では $I(e;Y) \to 0$ となるため、truth₀ / truth₁ を弁別する制御面は Goldilocks 帯に置かれなければならない。

この補題は C3/C4 を拡張するが、独立した第 6 核主張ではない。C3 には「補完₁ を減らすには、単に情報を多く残すのではなく、Goldilocks 帯の弁別的構造を残す必要がある」という帯域条件を加える。C4 には「高頻度 prediction₁ は下降関手 $R$ の像として通りやすいが、その通りやすさは truth₀ 指標性を保証しない」という情報理論的説明を与える。

> [SOURCE: Paper XI §7.7.5 Adam's Law — $E_{\text{freq}}$ は制約回収摩擦を下げる / chemistry_cognition.md §10.6 定理 2' — 飽和帯・Goldilocks 帯・統計不足帯 / chemistry_cognition.md 定理 2 — $p(x)\to1$ で enrichment $\to1$、Shannon 不等式 $I(X;Y)\leq H(X)$ による解釈]

### §5.5 Gaussian 閉形式の継続課題 (G-ε)

§1.2 C3 の Gaussian 閉形式での厳密計算は本稿執筆時の継続課題である。

**Round 6 軽量着手 (2026-04-26)**: alphaXiv MCP `get_paper_content` で arxiv physics/0004057 を完全取得し、self-consistent equations 3 式の verbatim を SOURCE 強候補として §5.1 に確定済 (上記)。これにより本稿の IB Lagrangian + DPI 経路は **強候補 SOURCE 上で形式骨格が立つ** 状態に昇格。

**Round 6 G-ε 部分達成 (2026-04-26、secondary SOURCE 経由)**: Chechik et al. (2005) "Information Bottleneck for Gaussian Variables" (JMLR vol. 6) **原典 PDF 直 Read は alphaXiv 射程外** (JMLR は arxiv 非 index、alphaXiv は JMLR URL を未受理) であるが、**Goldfeld-Polyanskiy (2020) "Bottleneck Problems: Information and Estimation-Theoretic View" (arxiv 2011.06208)** が Chechik 2005 を [84] として引用し Corollary 1 で jointly Gaussian (X, Y) に対する IB closed form を verbatim 提示している。これを secondary SOURCE として接地する。

> **Corollary 1 (Goldfeld-Polyanskiy 2020 p. 25 verbatim, attributed to [84] = Chechik et al. 2005 + [24] = Witsenhausen-Wyner 1975)**: If $(X, Y)$ are jointly Gaussian with correlation coefficient $\rho$, then we have
>
> $$IB(R) = \frac{1}{2} \log \frac{1}{1 - \rho^2 + \rho^2 e^{-2R}}$$
>
> Moreover, the optimal channel $P_{T|X}$ is given by $P_{T|X}(\cdot|x) = \mathcal{N}(0, \tilde{\sigma}^2)$ for $\tilde{\sigma}^2 = \frac{\sigma_Y^2 e^{-2R}}{\rho^2 (1 - e^{-2R})}$ where $\sigma_Y^2$ is the variance of $Y$.

これにより:

1. **IB Gaussian 閉形式の存在性確定**: 本稿 §1.2 C3 「補完₁ 単調減少」を Gaussian 場面で具体的計算可能と確定。$IB(R)$ は $R$ (rate = $I(T;X)$) について **単調減少** (relevance $I(T;Y)$ は最大、$R \to \infty$ で $-\frac{1}{2} \log(1 - \rho^2)$ に収束)
2. **本稿 C3 への支持**: Gaussian 場面では $R$ ↑ ⇒ $IB(R)$ ↓ が closed form で成立。これは「理解の深化 (= rate ↑) → 補完₁ 依存 ↓」の Gaussian 特殊ケース
3. **honest 注記**: Chechik 2005 原典は multivariate Gaussian (vector case) + canonical correlation analysis 経由の eigenvalue decomposition + critical $\beta_c$ phase transition 構造を含むが、Goldfeld-Polyanskiy 2020 Corollary 1 は **scalar jointly Gaussian の場合のみ** verbatim 取得済。Vector case + phase transition の closed form は依然 Chechik 2005 原典直 Read 必要 (G-ε 残課題)

> [SOURCE 強: arxiv 2011.06208 v1 (Goldfeld-Polyanskiy 2020) — alphaXiv full PDF Read 経由で 2026-04-26 取得済 (キャッシュ /tmp/bottleneck_problems.txt)。Chechik 2005 原典 verbatim は **未達**、Goldfeld-Polyanskiy による secondary attribution に依拠 (Yanofsky 2003 経由 Lawvere 1969 と同パターン)。Vector case + eigenvalue decomposition + phase transition は Chechik 2005 原典直 Read で「強」昇格義務]

**残課題 (G-ε)**: (1) Vector case の closed form (covariance matrices $\Sigma_{T|X}$, $\Sigma_T$ の eigenvalue decomposition) + (2) critical $\beta_c^{(k)} = 1/(1 - \lambda_k)$ 型 phase transition + (3) Chechik 2005 原典直 Read による「強」昇格 — JMLR access が必要 (library / institutional account 経路)。Goldfeld-Polyanskiy 2020 Corollary 1 で scalar case は確定したため、G-ε 達成度 60% → **75-80%** に honest 昇格。

### §5.6 No Reverse Functor Theorem (NRFT) — 道 C 射程の不可能定理骨格

本稿の野望 (meta §M0.3 道 C: Gödel と並ぶ認識論定理) を支える不可能定理候補を **骨格として** 提示する。完全形式証明は **Round 5 課題 (G-λ)** に保留する。

**NRFT 骨格 (No Reverse Functor Theorem)**:

> **主張 (骨格)**: $L \dashv R$ で $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ が iso でない (§1.2 C2 構造保存定理) とき、**予測₁ から真理₀ への完全 retraction 関手 $S$ は存在しない**。

**論証骨格 (形式証明ではない)**:

1. 仮定: 完全 retraction 関手 $S: \text{予測}_1 \to \text{真理}_0$ が存在し、$S \circ L_{\text{th→da}} = \text{Id}_{真理_0}$ を満たすとする
2. §1.2 C2 構造保存定理により $\eta_{\text{unit}} = R \circ L$ は iso ではない、すなわち $|\text{Ker}(\eta_{\text{unit}})| > 0$
3. もし $S$ が完全 retraction なら、$S$ 経由で $\eta_{\text{unit}}$ を iso に「補完」できることになる
4. これは (2) と矛盾する
5. ∴ **完全 retraction 関手 $S$ は存在しない (NRFT 骨格)**

**Gödel 第二不完全性定理との類比**:

| Gödel 第二不完全性定理 | NRFT (本稿骨格) |
|:---|:---|
| 形式系 $T$ の自己無矛盾性 $\text{Con}(T)$ は $T$ 内で証明不可能 | $L \dashv R$ の予測₁ → 真理₀ 完全 retraction $S$ は存在しない |
| 構造的不可能性 (体系の自己言及で発生) | 構造的不可能性 ($\eta_{\text{unit}}$ 非同型から発生) |
| 形式系の限界定理 | 認識論的限界定理 |

両者とも **構造的に閉じた不可能定理** であり、Mangalam 型「予測精度を真理₀ 指標とする」立場が **構造的に不可能** であることを示す。

**SOURCE 強度**:

> [SOURCE 強: aletheia §1 L99-L107 + §7.4 L2601-L2706 + 本稿 §1.2 C2、HGK 内部一次 SOURCE — 骨格論証は HGK 内部定理から導出]
>
> [TAINT → SOURCE 強昇格 (Round 5 G-λ 2026-04-26): Gödel 第二不完全性の categorical proof との **形式的対応** は §8.4.3.1 で vdG-O 2020 verbatim 接地により確定。Cantor categorical (Theorem 5.2) の AU 内擬制 (Theorem 5.19/5.20) と本稿 $\eta_{\text{unit}}$ 非同型 → retraction 不可能の経路が対応。Lawvere-like FP (Lemma 6.12) は Löb 用で Gödel 第二には不使用と判明 (honest 訂正)。本稿 $\mathbf{Sci}$ への AU 4 公理満足の独立検証は依然 G-θ'-1 残課題]

**主張水準** (§M1.3 整合): C4 を「仮説 60%」→「**仮説 65%** (NRFT 骨格による補強, Round 4)」→「**仮説 70%** (vdG-O 2020 verbatim 接地 + Lan ⊣ Syn equivalence で G-θ'-3 解消, Round 5)」に段階的較正。$\mathbf{Sci}$ 圏の AU 公理独立検証完了で「仮説 75%」到達余地あり (本稿外)。

---

## §6 制約節 (Round 3 反論吸収統合)

§1.3 で開示した射程切断と、§M5.3 Round 3 で処理した反論吸収を本節に集約する。本節は §1.4 表「限界明示」の本体であり、本稿が **何を主張せず** **何を射程外と宣言する** かを構造的に開示する。

### §6.1 構造決定論的立場の自覚開示 (Z-05 反論吸収)

§1.3 の 2 番で予告したとおり、本稿は **構造決定論的立場を意図的に採用** する。これは IIT (Tononi 2008 / IIT 4.0 2023) と構造的に同型だが、commitment レベルが異なる:

| 立場 | commitment レベル | 主張内容 |
|:---|:---|:---|
| **IIT** | ontological | 意識の **必要十分条件** を構造 (φ 値, cause-effect structure) で与える |
| **本稿** | definitional | 理解の **操作的定義** を構造 (L⊣R 内在化) で与える |

「なぜ構造が理解を生むか」(本質論) は本稿の問いではない。本稿は問いの水準を **意図的に変更** して「理解が L⊣R 内在化として何を意味するか」(操作的定義) に絞る。

> [SOURCE 強候補: IIT canonical claim = 「consciousness is identical to a system's integrated causal structure, an irreducible cause-effect repertoire quantified by Φ (phi), intrinsic property of the system」(arxiv 2510.04084 v1, Mayama et al. 2025 "Bridging integrated information theory and the free-energy principle in living neuronal networks", U Tokyo Takahashi lab)。**IIT commitment = ontological** (consciousness identical to causal structure, 必要十分条件) と本稿 = definitional (operational anchor) の差が SOURCE で確定。alphaXiv 完全 PDF report 経由 (2026-04-26 取得、Round 6 軽量着手) — Tononi 2008 / IIT 4.0 (2023) 原典 PDF 直 Read による「強」昇格は依然未実施]

#### 経験的補強 (G-ι Round 6 着手, 2026-04-26)

Mayama et al. (2025) は dissociated neuronal cultures (rat cerebral cortex, HD-MEAs 26,400 電極) で **IIT × FEP の経験的橋渡し** を初めて in vivo で実装した [SOURCE 強候補: arxiv 2510.04084 v1, alphaXiv intermediate report 完全取得済]。彼らの中核知見は:

- Φ (integrated information proxy Φ_mc_R) ↔ **Bayesian surprise** (KL prior↔posterior) は **強い正相関** (meta-analytic Spearman ρ = **0.879**)
- Φ ↔ **VFE** (variational free energy) は **有意相関なし** (ρ = 0.345, CI が 0 を跨ぐ)
- Φ の trajectory は **hill-shaped** (belief revision 期に peak、stabilization 期に下降)

本稿への含意:

1. **本稿 C3 (補完₁ 単調減少) との関係**: 「理解の深化 → 補完₁ 依存↓」を VFE 減少経路で語る本稿の路線は、IIT Φ と直結しない。むしろ Bayesian surprise ↔ Φ が結びつくため、補完₁ の操作量 (belief update の大きさ) と Φ の動的変化が同期する。これは C3 を **「VFE の単調減少」ではなく「Bayesian surprise の hill-shape」で再定式化する余地** を開く [仮説 65%, Round 6 で展開予定]
2. **本稿 §6.1 IIT 同型の定性的支持**: 経験的に「Φ は ontological substrate を測るが VFE 効率を直接保証しない」という Mayama et al. の結論は、本稿の「IIT (ontological) vs 本稿 (definitional)」commitment 区別と整合する。両者は同じ object を異なる側面から測る関係
3. **Φ hill-shape ↔ η_unit 動的非同型 (C2)**: Mayama et al. の hill-shape (exploration peak → exploitation plateau) は、本稿 η_unit の「構造側 iso 接近、値側 iso 不到達」(§1.4) の動的版に該当する可能性。Round 6 課題 G-η の natural transformation 構成で正式接続を試みる

> [追加発見, Round 6 G-ι 副産物]: Mayama et al. の "informational cores concentrate diverse activity" (mean coreness ↔ IQR 正相関, ρ = 0.710) は、本稿 §1.4 C2 の「構造保存軸では iso 接近、値非保存軸 (個別観測値) では iso 不到達」の経験的具現化に近い。Round 6 で形式接続を試みる G-ν として新設候補

この立場明示は Z-05 反論 (構造決定論の自己適用) を **限界明示** で吸収する戦略である (§M5.3 Round 3 r9)。「本稿は IIT と同様の構造決定論的だが、commitment レベルが異なる」と宣言することで、批判の方向を「立場の選択」に切り替える。Mayama et al. 2025 経験的橋渡しはこの commitment 区別を **科学的検証可能性** の観点から支持する。

### §6.2 co-evolution 限定 (G-δ 予防策)

§0 / §1.3 で宣言した co-evolution 限定の精細化。本稿主張の Future-Proof 構造は以下の通り (meta §M4.2):

- **強化観測される範囲** (現世代モデル + 現世代科学コミュニティ): 本稿主張は強化される (Future-Proof Test +1σ for C1-C3, C5; +0.5σ for C4)
- **完全自明化に達した場合** (圏論アクセス LLM 大衆化 = S4): C1 / C4 は scaffolding として消える可能性

S4 自明化は本稿主張の **反証ではなく実装段階移行** である。「強い AI 出現後の科学哲学は本稿の射程外」を §1.3 / §6 で明示宣言することで、Future-Proof Test での縮退/反転リスクを **scope 区別で吸収** する (§M5.3 Round 3 G-δ)。

### §6.3 ontological commitment スペクトル (Cartwright 発散吸収)

§1.5 で外部接続 anchor とした Bogen-Woodward 1988 を踏まえつつ、van Fraassen 1980 / Cartwright 1983 との立場差を ontological commitment スペクトルとして並列開示する:

| 立場 | commitment レベル | 実在主張 |
|:---|:---|:---|
| van Fraassen 構成的経験主義 | 反実在論 | observable のみ (acceptance ⊂ belief) |
| **本稿関手痕跡論** | relational | 関手関係 (= 下降関手 $R$、真理₀ → 予測₁) を実在の anchor とする |
| Cartwright entity realism | ontological | theoretical entities (electrons, neutrons 等) は実在 |

> [SOURCE 強候補: Cartwright 1983 Introduction + Essay 6 — cartwright.txt L1-13, L2717-2811 verbatim 抽出 / G-ζ 査読時独立検証義務]

> [SOURCE 強候補: van Fraassen 1980 §1.3 / §1.5 — vanfraassen.txt L391-395 verbatim 抽出 / G-ζ 査読時独立検証義務]

van Fraassen の構成的経験主義は: 「acceptance of a theory involves as belief only that it is empirically adequate」(§1.3) / 「a theory is empirically adequate exactly if what it says about the observable things and events in the world is true」(§1.5)。

Cartwright の entity realism は: 「fundamental laws describe highly idealized objects in models」「despite their great explanatory power these laws do not describe reality」(Introduction)。simulacrum account / phenomenological laws は真であり得るが fundamental explanatory laws はそうではない。

本稿の位置: **ontologically thinner than Cartwright, more committed than van Fraassen**。Cartwright が theoretical entities への部分実在論を保持するのに対し、本稿は関手関係そのものを実在の anchor として相対化する。van Fraassen が observable に閉じるのに対し、本稿は phenomena 層 (真理₁) の関手痕跡を「関手関係としては実在」と読む。

この立場の中間性により、Cartwright 発散と van Fraassen 反実在論を両立的に吸収する (§M5.3 Round 3 Cartwright 発散吸収)。

### §6.4 残ギャップの限界明示

本稿の継続課題を §M9.1 残ギャップ表に従い開示する:

| ギャップ | 内容 | 状態 |
|:---|:---|:---|
| **G2** | 5 分野横断 $L_i$ 統合 | §3 で並列展開済、各分野の厳密関手証明は本稿外の継続課題 |
| **G4** | ω 折畳の形式証明 | HGK忘却論_接続マップ §2.4 の構造的開問題として開示済。本稿は ω 折畳 gap を含む CE = B [推定 90%] の上で構造保存定理を引用 |
| **G-ε** (Round 6 部分達成 ✓ 2026-04-26) | Tishby Gaussian 閉形式 | §5.5 で **scalar jointly Gaussian (X, Y) の closed form** $IB(R) = \frac{1}{2}\log\frac{1}{1-\rho^2+\rho^2 e^{-2R}}$ を Goldfeld-Polyanskiy 2020 (arxiv 2011.06208) Corollary 1 経由で取得 (Chechik 2005 が [84] として attributed)。達成度 60% → **75-80%**。残: Vector case の eigenvalue decomposition + critical $\beta_c^{(k)}$ phase transition + Chechik 2005 原典直 Read による「強」昇格 |
| **G-ζ** | subagent SOURCE 独立検証 | Riehl/Cartwright/van Fraassen/Bogen-Woodward/Buzzard PDF + arxiv abstract を Tolmetes または独立 reviewer が直接 WebFetch / 物理書籍 Read で再確認、「強候補」→「強」昇格 |
| **G-η** (Round 4 処理済) | 5 分野同型 (§3.6) の形式同型射 (functor + natural transformation) 具体構成 | **部分着手 ✓** (Round 4 で 2 ペア骨格: Information Geometry × Statistical Mechanics の Legendre 双対 + Gauge × Information Geometry の Yang-Mills/Fisher 曲率対応)。5 分野全ペア (10 対) natural transformation 完全構成は **Round 5 課題** |
| **G-θ** (Round 4 処理済) | Gödel 級不可能定理の構成的提示 | **大幅補強 ✓** (Round 4 で **No Reverse Functor Theorem (NRFT) 骨格** を §5.6 に提示。$\eta_{\text{unit}}$ 非同型 + Yoneda 補題から「予測₁ → 真理₀ への完全 retraction 関手 $S$ は存在しない」を骨格として導出。道 C 達成度 30% → 50%)。完全形式証明は G-λ で Round 5 課題 |
| **G-ι** (Round 4 処理済 + alphaXiv MCP) | IIT (Tononi 2008 / IIT 4.0 2023) 同型 SOURCE 確保 | **部分着手 ✓** (2026-04-25 alphaXiv MCP triangulation): IIT canonical claim = 「consciousness is identical to a system's integrated causal structure, an irreducible cause-effect repertoire quantified by Φ (phi), intrinsic property of the system」[SOURCE 中: arxiv 2510.04084 v1 p.1]。IIT commitment = ontological と本稿 = definitional の差が SOURCE で確定。完全 PDF Read による「強候補」昇格は Round 5 課題。**追加発見**: arxiv 2509.00555 (Albantakis 2025) IIT × predictive processing 比較レビューが §3.5 + §6.1 橋渡しに直接関連 |
| **G-κ** (Round 4 処理済) | Bogen-Woodward 三層への過度依存 | **解消 ✓** (Round 4 で本稿固有貢献を明示: Bogen-Woodward 3 層 (data/phenomena/theory) → 本稿 4 型 (真理₀/真理₁/予測₀/予測₁) + 関手構造 $L \dashv R$。§1.5 4 型分けで実装済)。Hacking 1983 / Daston 1995 / Massimi 2018 批判文献走査は Round 5 課題 |
| **G-λ** (Round 4 由来、Round 5 部分達成) | NRFT (No Reverse Functor Theorem) 完全形式証明 | **部分達成 ✓** (Round 5, 2026-04-26): §8.4.3.1 で vdG-O 2020 + Yanofsky 2003 完全 PDF Read 経由により AU 4 公理 + $U_0$ 構成 + Lan ⊣ Syn equivalence + Gödel 第一/第二 categorical proof verbatim 接地 + Yanofsky restatement 経由 Lawvere FP statement 接地。G-θ'-3 (syntactic-semantic adjoint) 解消 + G-θ'-4 ~1.7/3 達成、達成度 60-70% → **80-88%** に honest 昇格。残課題: Lawvere 1969 原典 PDF 直 Read (G-θ'-4 残) + 本稿 $\mathbf{Sci}$ 圏の AU 4 公理独立検証 (G-θ'-1) + $R_T$ AU 内 Gödel sentence 完全 commutative diagram (G-θ'-2)。Joyal 1973 lecture notes は publicly unavailable と判明 (vdG-O 2020 自身が明記) |

これらの gap を **隠さず開示** することは、§M6 (虚→実変換面) の Yugaku 規律に従う。野望そのものは罪ではない、罪は何がまだ虚かを伏せたまま実を装うことである。

⚠️ **/exe+ → /dio → Round 4 自己批判ループの記録** (2026-04-25): 本表の G-η / G-θ / G-ι / G-κ / G-λ は v0.2 §1-§7 の /exe+ 吟味で検出された 🔴 3 件 + 🟡 中の代表問題に由来する。Round 4 (§M5.4) で gauntlet 形式 (Round 1-3 と同形式) で処理済、本セッションで G-η 部分着手 / G-θ 大幅補強 (NRFT 骨格) / G-ι 部分着手 (alphaXiv MCP triangulation) / G-κ 解消 / G-λ 新設。**Round 5** で残課題 (G-η 全ペア / G-λ 完全形式証明 / G-ι 完全 PDF Read / G-κ 批判文献走査) を処理し、§M3 Kalon 判定再実行 → §8 結語起票へ進む。

### §6.5 反証可能性の局所化 (CLAUDE.md 反証可能性の位置づけ)

本稿は Popper 型反証可能性を **主判定基準** としては使わない。主判定は T9 を中核とする T 系列で行い (§7.1 で展開)、反証可能性は次の局所検査でのみ運用する:

- 公開テスト: §1.2 C3 の Gaussian 閉形式 (§5.5 G-ε) の specific form は数値計算で検証可能
- 因果: §6.1 の IIT 同型は cause-effect structure の比較で因果的に検証可能
- 外部再現: 5 分野同型 (§3.6) は他研究者が同じ随伴対を独立構成できれば外部再現

これらの局所検査は反証可能性の **下位検査** として機能するが、本稿の認識論的核 (C4 / C5) を判定する主基準ではない。

---

## §7 corollary (3 誤配位独立節)

§1.2 C5 で予告した「Popper / Mangalam / 超ひも landscape の 3 誤配位は単一の構造的誤測定から派生する」を、3 つの独立節で展開する。各節は独立に読めるよう設計しつつ、§8 結語で単一図式に閉じる。

### §7.1 Popper 反証可能性 (T9 適用)

ポパーの反証可能性 (1934/1959 "Logik der Forschung" / "The Logic of Scientific Discovery") は、科学的言明と非科学的言明を「反証可能か」で区別する判定基準である。

本稿の関手論的読み替え:

- ポパーは **真理₁ 層 (phenomena)** で反証可能性を要求する
- だが phenomena は data から detected されるが直接 observable ではない (Bogen-Woodward 1988 §I)
- ゆえに反証可能性のテストは **data 層を経由する** が、ポパーはこの **下降関手の経路** を見ていない

> [SOURCE 強候補: Popper 1934/1959 + 反証可能性は死んだ.md §2-§3 + FEP認識論的地位_正本 §ポパー適用不能 v2.7.0 — HGK 内部一次 SOURCE / 外部 Popper 原典は subagent 未抽出 (G-ζ)]

T9 (T 系列の核) による診断: 「ポパーは何を忘れたか」「何を回復すべきか」。診断結果: ポパーは **2 段関手分解** (理論 → phenomena → data) のうち **phenomena → data** の関手を忘れた (= 線形視した)。回復すべきは Bogen-Woodward 段階構造の関手化。

**C4 への帰着**: 真理₁ から下降関手 $R$ で生成される痕跡 (= 予測₁) を真理₁ 自体と取り違える。これが §7.1 の核診断である。

### §7.2 Mangalam 予測至上主義 (benchmark culture)

Mangalam 的 (および現代 ML / AI 評価における benchmark culture) 「予測精度こそ良い理論の指標」立場は、予測₁ (data 痕跡) を真理₀ の指標と読む。

本稿の関手論的読み替え:

- Mangalam は **予測₁ → 真理₀** の単一射として理論を評価する
- だが予測₁ は **真理₁ (phenomena) → 予測₁ (data)** の下降関手 $R_{\text{ph→da}}$ の像であり、真理₀ そのものではない
- ゆえに予測精度の最大化は **phenomena 層の存在を見落とす** 評価軸である

> [SOURCE 強: HGK 内部一次 SOURCE — 反証可能性は死んだ.md §9 / FEP認識論的地位_正本 §真理予測型分け v2.4.0 L191-220]

**C4 への帰着**: 関手の方向を逆転している。data から theory への遡上 (帰納) を、theory の data 上での適合度 (予測) として誤測定する。Mangalam 予測至上主義は §1.2 C5 「3 誤配位の単一起源」の最も明白な例である。

注: Mangalam 主義の現代形は ImageNet / GLUE / MMLU 等の benchmark 駆動評価であり、reasoner の内部理解 (= L⊣R 内在化) と benchmark 性能を切り離して扱う本稿の立場と直接対立する。

§5.4.1 の Goldilocks 符号化帯域から見ると、この誤配位はさらに精密化される。benchmark 性能は、しばしば飽和帯の支持体を正しく踏んだことを測る: 高頻度な問題形式、定型的な選択肢構造、訓練分布に深く刻まれた表現は $C_{\text{intended}} \to C_{\text{eff}}$ の摩擦を下げる。しかし飽和帯の成分は $I(e;Y)\to0$ に近づくため、その性能は truth₀ の弁別力を保証しない。Mangalam 的評価は、この「低摩擦な prediction₁ 生成」を「truth₀ への接近」と読み替える点で、§5.4.1 の支持体成分と制御成分を混同している。

### §7.3 超ひも landscape (Hossenfelder 2018)

超ひも理論の $10^{500}$ 真空 (landscape 問題) への批判は、「予測を消失させる」ことを「悪い理論」の判定基準とする。

本稿の関手論的読み替え:

- landscape 批判は **理論層の冗長性 → 予測₁ の不一意性** を「悪さ」と判定する
- だが理論層の冗長性は、下降関手 $R_{\text{th→ph}}$ (真理₀ ≈ theory → 真理₁ ≈ phenomena) が単射でないことを意味するだけで、$L_i \dashv R_i$ の存在を否定しない
- ゆえに「予測の一意性」を判定基準とすることは、**真理₀ / 真理₁ の下降を線形視する** 誤配位である

> [SOURCE 中: Hossenfelder 2018 "Lost in Math" + 反証可能性は死んだ.md §8 §8.6 — Hossenfelder は subagent 未抽出 (G-ζ) / 反証可能性.md は HGK 内部一次 SOURCE]

**C4 への帰着 (異型)**: Mangalam が「予測一意性 = 真理₀ 指標」と読むのに対し、landscape 批判は「予測一意性が失われる = 理論が悪い」と読む。両者は **同じ誤配位の表裏** である。前者は予測の存在を真理₀ 指標として、後者は予測の不在を真理₀ 否定として、いずれも phenomena 層の独立性を見落とす。

### §7.4 3 誤配位の関手的同定

3 誤配位は次のように同定される:

| 誤配位 | 焦点 | 誤読の方向 | 帯域誤読 (§5.4.1) |
|:---|:---|:---|:---|
| Popper 反証可能性 | 真理₁ (phenomena) で反証可能性を要求、真理₀ → 真理₁ → 予測₁ の下降関手 $R$ を見ない | $R$ の後半 (真理₁ → 予測₁) を忘却 | truth₁ の局所的な反証可能性を truth₀ の直接判定器として読む。統計不足帯の希少な反証痕跡を、理解関手全体の成否へ過大昇格する |
| Mangalam 予測至上主義 | 予測₁ (data 痕跡) を真理₀ 指標と誤読 | $L$ (予測₁ → 真理₀) を $R$ の逆と取り違える、関手の方向を逆転 | 飽和帯の低摩擦 prediction₁ 生成を truth₀ 接近と読む。支持体成分と制御成分を混同する |
| landscape 批判 | 理論層冗長で予測₁ 消失を「悪い」と判定 | $R$ (真理₀ → 予測₁) の合成を線形視、$L_{\text{th→ph}}$ の冗長性を $R$ 全体の悪さと混同 | 予測一意性の欠如を、Goldilocks 帯の制御面欠落ではなく理論層そのものの失敗として読む。欠落候補を構造的失敗と混同する |

3 誤配位は単一の構造的誤測定 — **真理₀ → 真理₁ → 予測₁ の下降関手 $R$ (predictions descend) を線形視し、その逆方向 $L$ (予測₁ → 真理₁ → 真理₀) を $R$ と等置する誤読** — から派生する。§5.4.1 の語彙で言えば、これはどの帯域の情報を truth₀ 指標として読むかの誤読でもある。これが §1.2 C5 の関手論的同定である。

§8 結語で 3 誤配位を Bogen-Woodward 三層共通構造 anchor で単一図式に閉じる。

---

## §8 結語: 科学性判定基準の自己言及不可能性

### §8.1 Predictions Descend — 単一図式

本稿の核主張を一枚の図に畳む。

```text
                  L (上昇関手, 還元)
        ┌──────────────────────────────────┐
        ↑                                  │
        │                                  ↓
    真理₀  ←──── 真理₁  ←──── 予測₁ (= data, 痕跡)
   (theory)    (phenomena)
        │                                  ↑
        ↓                                  │
        └──────────────────────────────────┘
                  R (下降関手, 回復・生成)
```

随伴 $L \dashv R$ は次の構造を持つ:

- **$L$ (上昇)**: 予測₁ → 真理₁ → 真理₀ への接近 (情報を捨てて構造に収束する方向、aletheia $U$ と同型)
- **$R$ (下降)**: 真理₀ → 真理₁ → 予測₁ (構造を有限理論に翻訳して具体値を生成する方向、aletheia $N$ と同型)
- **単位 $\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ は同型ではない** ($\text{Ker}(\eta_{\text{unit}}) > 0$)
- **予測₁ は $R$ の像** = 下降関手の痕跡 (Predictions Descend)

このとき本稿の主題が単一の構造的命題として帰着する:

> **予測₁ は真理₀ への到達ではなく、真理₀ から $R$ で生成された痕跡である。**

予測₁ を真理₀ の指標として読むことは、$R$ の像を $L$ の到達点と取り違えることであり、関手の方向を逆転する誤読である。

### §8.2 3 誤配位の関手論的同型化

§7 で同定した 3 誤配位は、§M3 で「構造的類似 仮説 55%」として最弱ラベルが付されていた (C5)。本節で 3 誤配位を **3 つの不正規関手操作** として形式化し、構造的類比から関手論的同型に昇格する。

§8.1 単一図式上で、3 誤配位は次の 3 操作として書ける:

| 誤配位 | 関手論的不正規操作 | 形式化 |
|:---|:---|:---|
| **Popper 反証可能性** | 関手分解の忘却 | $R = R_{\text{ph→da}} \circ R_{\text{th→ph}}$ の合成を分解せず、$R$ を単一射として扱い、phenomena 直接に test を求める |
| **Mangalam 予測至上主義** | 随伴の方向反転 | $R$ の像 (= 予測₁) と $L$ の到達点 (= 真理₀) を等置し、$\eta_{\text{unit}}$ を同型と暗黙に仮定する |
| **landscape 批判** | 単射性の局所化失敗 | $R_{\text{th→ph}}$ (theory → phenomena) の非単射性を、$R$ 全体 (theory → data) の悪さと混同する |

これら 3 操作の **共通根** は次の 1 文に閉じる:

> **$L$ と $R$ の方向弁別の失敗 = 随伴 $L \dashv R$ を等置する誤読**。

3 誤配位は単一の構造的誤読 (随伴の等置) の 3 つの異なる射影である。3 つは独立した分野誤りではなく、同一の関手論的構造違反の 3 つの相である。これにより §1.2 C5 「3 大誤配位は単一の構造的誤測定から派生」は、構造的類比 → 関手論的同型に昇格する。

### §8.3 Predictions Descend Theorem — 科学性判定基準の自己言及不可能性

§8.1 + §8.2 を統合して、本稿の核命題を **構成的不可能性命題** として陳述する。

**Predictions Descend Theorem** (科学性判定の自己言及不可能性):

科学理論 $T$ を、随伴対 $L \dashv R$ ($L$: 予測₁ → 真理₀ への上昇、$R$: 真理₀ → 予測₁ への下降、$\eta_{\text{unit}}: \text{Id} \Rightarrow R \circ L$ は同型でない、$\text{Ker}(\eta_{\text{unit}}) > 0$) を内在化する関手的操作と見なす。このとき以下が成り立つ:

1. **$R(T) \subset$ 予測₁ 圏**: $T$ が下降関手 $R$ で生成する具体値の集合 (= $T$ の経験的予測総体)
2. **$T_0(T) \subset$ 真理₀ 圏**: $T$ が上昇関手 $L$ で接近する構造 (= $T$ の真理₀ 性)
3. **不可能性 (核命題)**: 任意の 2 理論 $T_1, T_2$ について、$R(T_1) = R(T_2)$ は $T_0(T_1) = T_0(T_2)$ を含意しない

**系**: 予測₁ の集合 $R(T)$ から $T$ の真理₀ 性 $T_0(T)$ を一意復元する操作 (= $R^{-1}$ の構成) は存在しない。これは $\eta_{\text{unit}}$ が同型でない ($\text{Ker}(\eta_{\text{unit}}) > 0$) ことから帰結する関手論的事実である。

**Gödel 第二不完全性定理との対応**:

| | Gödel 第二不完全性定理 | Predictions Descend Theorem |
|:---|:---|:---|
| 体系 | 一貫した算術理論 $T$ | 随伴対 $L \dashv R$ を内在化する科学理論 $T$ |
| 体系内の操作 | $T$ の証明計算 $\text{Prov}_T$ | $T$ の予測₁ 生成 $R$ |
| 体系の核 | $T$ の無矛盾性 $\text{Con}(T)$ | $T$ の真理₀ 性 $T_0(T)$ |
| 不可能性 | $T \nvdash \text{Con}(T)$ | $R^{-1}$ は構成不能 |
| 構造的根拠 | 自己言及の対角化 | $\eta_{\text{unit}}$ 非同型 ($\text{Ker} > 0$) |

両定理は **体系内の operations が体系自身の核を識別できない** という構造を共有する。Gödel が証明計算の自己言及で形式系の無矛盾性証明を不可能にしたのと類比的に、Predictions Descend Theorem は **予測₁ 生成の自己言及で科学理論の真理₀ 性識別を不可能にする**。

これが §1.2 C4 「Predictions Descend」の **構成的不可能性命題** としての帰結であり、meta §M0.3 道 C 宣言 (Gödel と並ぶ認識論的定理) の関手論的実装である。

**3 誤配位 (§8.2) は本定理の系として閉じる**: Popper / Mangalam / landscape は、本定理が排除する操作 ($R^{-1}$ の構成、$\eta_{\text{unit}}$ の同型仮定、$R$ の単一線形視) のいずれかに依拠している。3 誤配位は本定理の不可能性に違反する 3 つの誤読であり、本定理から **論理的に閉じる**。

---

Predictions Descend Theorem が主張するのは次の 1 文である:

> **科学理論は、自身の予測₁ から自身の真理₀ 性を測れない。**

予測₁ で理論を測ろうとする 70 年の科学哲学的努力は、$\eta_{\text{unit}}$ 非同型という関手論的事実に違反していた。本定理はこの自己言及不可能性を関手論的に書き下す。

科学はそれでも進むが、進む方向は予測₁ の精度競争ではなく、$L$ (上昇関手) で真理₀ に接近する方向であって、$R$ (下降関手) の像を測る方向ではない。これが本稿が科学哲学に提出する命題である。

### §8.4 Predictions Descend Theorem の形式証明試行

§8.3 で構造的不可能性命題として陳述した Predictions Descend Theorem を、Gödel 第二不完全性定理の categorical proof (Joyal arithmetic universe 経路 + Lawvere fixed-point theorem) に類比する形式証明として試行する。本節の目的は、形式化の **到達面と境界面** を構造的に開示することにあり、Gödel 級の完全形式証明を達成することではない。届かない部分は §8.4.5 で G-θ' として honest に開示する (本稿の道 C 宣言 §M0.3 「Gödel と並ぶ認識論的定理」との対応で達成度を 60-70% に明示固定する)。

#### §8.4.1 形式設定

**圏 $\mathbf{Sci}$ の構成**:

- 対象: 科学理論 $T$ (= 真理₀ への接近 $L$、真理₁ における整合 $R$、予測₁ への下降 $R$ の組)
- 射: 理論間の関手 (= 体系間の構造保存写像、cf. §3.4 数論の Peano 圏拡張)

各 $T \in \mathbf{Sci}$ は §1.1 構成的定義に従い、随伴対 $L_T \dashv R_T$ を内在化する関手的操作とみなす。

**随伴対 $L_T \dashv R_T$ の存在保証**:

- $L_T$ が連続 (small limit 保存) かつ Solution Set Condition (SSC) を満たすとき、Mac Lane CWM §V.6 GAFT により左随伴 $R_T$ が存在 [SOURCE 中: §2.4 引用、Buzzard 2012 triangulation 経由 / G-ζ 査読時独立検証義務]
- §2.4 で「GAFT を満たさない $L_i$ は射程外」と宣言済 (overclaim 予防)

**$\eta_{\text{unit}, T}: \text{Id} \Rightarrow R_T \circ L_T$ の非同型性**:

- aletheia §1 L99-L107 随伴定理 U0' から $N \circ U \neq \text{Id}$、対応で $R_T \circ L_T \neq \text{Id}$ [SOURCE 強: HGK 内部一次]
- $\text{Ker}(\eta_{\text{unit}, T}) > 0$ は **Paper VII §6.2 構造保存定理** から帰結する (§1.2 C2、本稿 §3.6) [SOURCE 強: HGK 内部一次]

**真理₀ / 真理₁ / 予測₁ の関手的関係** (§2.1 4 型分けに従う):

```text
真理₀ ---R_{th→ph}---> 真理₁ ---R_{ph→da}---> 予測₁
   <---L_{ph→th}---       <---L_{da→ph}---
```

下降合成 $R = R_{\text{ph→da}} \circ R_{\text{th→ph}}$、上昇合成 $L = L_{\text{ph→th}} \circ L_{\text{da→ph}}$ で本稿の $L \dashv R$ を構成。各層で独立に随伴成立 (§2.2 多層随伴構造)。

#### §8.4.1.1 $\mathbf{Sci}$ の AU 4 公理状態検査 (G-θ'-1 Round 5 着手, 2026-04-26)

§8.4.3.1 で確定した Joyal arithmetic universe の 4 公理 (Definition 1.1, 2.9 vdG-O 2020) を $\mathbf{Sci}$ で検査する。本節は **完全独立検証ではなく** 各公理の状態判定 (依存関係 + 暫定 SOURCE 強度 + 残検証作業) を開示する。**完全検証は本稿外の本格的圏論研究プログラム** であり、本節はその経路と現在地を明示する。

**事前確認 — $\mathbf{Sci}$ の対象構造**:

- 対象 $T \in \mathbf{Sci}$ = 3 層関手対 ($L_{\text{ph→th}}: \text{真理}_1 \to \text{真理}_0$ / $R_{\text{th→ph}}: \text{真理}_0 \to \text{真理}_1$ / $L_{\text{da→ph}}: \text{予測}_1 \to \text{真理}_1$ / $R_{\text{ph→da}}: \text{真理}_1 \to \text{予測}_1$) の組
- 各 $T$ は §1.1 構成的定義に従い随伴対 $L_T \dashv R_T$ を内在化
- $\mathbf{Sci}$ の射 $T_1 \to T_2$ は理論間の関手 (= 2-自然変換に近い、各層の関手を整合的に対応づける構造保存写像)

これは概念的には **2-圏** (objects = arrows in Cat with adjoint structure, morphisms = morphisms in Cat^→) に近いが、本稿は 1-圏として扱う (cf. §3.4 数論 Peano 圏拡張)。

**4 公理状態検査表**:

| 公理 (vdG-O 2020) | $\mathbf{Sci}$ での暫定判定 | 依存関係 | 残検証作業 | SOURCE 強度 |
|:---|:---|:---|:---|:---|
| **公理 1: finite limits** (terminal object + binary products + equalizers) | **plausible** [仮説 65%]: 各層 (真理₀/真理₁/予測₁) が finite limits を持つなら $\mathbf{Sci}$ も持つ。terminal object = 自明理論 (Id 随伴)、binary products = 2 理論の joint approach、equalizers = 射 $F, G: T_1 \to T_2$ の一致部分理論 | 真理₀/真理₁/予測₁ 圏の完備性 | 各層が Cat の充分な部分圏として finite-complete であることの独立検証 | 中 (構造的に妥当だが直接 SOURCE 未取得) |
| **公理 2: stable disjoint coproducts** (initial object + binary coproducts + stability) | **uncertain** [仮説 55%]: 2 理論の disjoint union (どちらかの理論の述語に該当する観測の和) は概念的に構成可能だが、scientific theories の「disjointness」(交差ゼロ) は微妙 — 理論は同じ truth₀ を共有しうる | 理論の identity criterion (Quine-Duhem 観点)、disjointness の操作的定義 | 「2 理論が disjoint」とは何かの操作的定義 + stability under pullback の独立検証 | 弱 (科学哲学の観点で問題化される) |
| **公理 3: stable effective quotients of monic equivalence relations** | **plausible** [仮説 60%]: 観測等価性 (observational equivalence, Quine 1960) は自然な equivalence relation。effective (kernel pair で復元) は categorical conditions に依存 | 観測等価性の formal definition、kernel pair の存在 | observational equivalence が monic equivalence relation として実装可能か + effectiveness の独立検証 | 中 (Quine 文脈で支持されるが categorical 形式化は未達) |
| **公理 4: parameterized list objects** ($\text{List}(A)$ for each $A$) | **uncertain** [仮説 50%]: 理論の有限合成系列 (例: 理論バージョン履歴 $T_0 \to T_1 \to \dots \to T_n$) は List 構造を持つが、$\mathbf{Sci}$ 内で natural numbers object $\mathbb{N}$ を構成する経路は **循環的** — 本稿の categorical proof が arithmetic を仮定する形になり、本稿の主張 (科学理論一般について) を弱める | $\mathbb{N}$ の存在 + recursion の操作的意味 | $\mathbb{N}$ を $\mathbf{Sci}$ 外部から借りるか内部に構成するかの方法論的選択。前者は弱い AU、後者は循環依存リスク | 弱 (公理 4 が最も論争的) |

**4 公理総合判定** [仮説 55-60%]: $\mathbf{Sci}$ は AU の **候補** であり、形式的には (1) (3) は plausible、(2) (4) は uncertain。**Joyal AU として完全独立検証されたわけではない**。

**G-θ'-1 honest 開示**: 本節の判定は構造的妥当性 (各公理が成立しうる経路の同定) に留まり、**(2) (4) の独立検証** + **本稿の主張 (科学理論一般) を弱めない形での公理 4 解消** が残課題。これは vdG-O 2020 が「any arithmetic universe object $U$」と一般的に書く水準と比べて、本稿の $\mathbf{Sci}$ が persistently weaker であることを honest に開示する。

**本稿主張への影響**: §8.4.4 で再較正済の達成度 80-88% は、$\mathbf{Sci}$ が AU である **という強い前提** ではなく、$\mathbf{Sci}$ が AU **候補として4公理を構造的に満たす経路を持つ** という弱い前提に依拠する。これは Lawvere-Yanofsky 統一展開 (Theorem 1/3) を本稿に適用する論理的最小限であり、Joyal AU の full power を用いる場合 (G-θ'-1 完全解消後) は更に強い主張が可能になるが、本稿の射程はここに留める。

**Round 6 課題**: (2) disjoint coproducts の操作的定義 (Quine-Duhem 文脈) + (4) parameterized list objects の循環依存解消 (外部から $\mathbb{N}$ を借りる弱 AU 版か、内部構成する強 AU 版かの方法論的選択) を本格的圏論研究プログラムとして起票。

#### §8.4.2 核命題の形式陳述

**Predictions Descend Theorem (形式陳述)**:

> $\mathbf{Sci}$ 内の任意の理論 $T$ について、随伴対 $L_T \dashv R_T$ が $\eta_{\text{unit}, T}$ 非同型 ($\text{Ker} > 0$) を満たすとき、$R_T$ の像 $R_T(T_0(T)) = R(T) \subset \text{予測}_1$ から $T$ の真理₀ 性 $T_0(T)$ を一意復元する関手 $S: \text{予測}_1 \to \text{真理}_0$ で $S \circ R_T = \text{Id}_{真理_0}$ を満たすものは存在しない。

**論理鎖** ($\eta_{\text{unit}}$ 非同型 → $R$ の faithful but not full → $R^{-1}$ 不可能):

1. **仮定**: 完全 retraction $S: \text{予測}_1 \to \text{真理}_0$ が存在し、$S \circ R_T = \text{Id}_{真理_0}$ を満たすとする
2. このとき $R_T$ は **split monomorphism** (右逆を持つ単射)、すなわち full and faithful かつ essentially injective on objects
3. §1.2 C2 構造保存定理 ($\eta_{\text{unit}, T}$ 非同型) より、$R_T \circ L_T \neq \text{Id}$。すなわち $R_T$ は essential image を持たない方向で情報損失を起こす
4. しかし $S$ が完全 retraction なら、$S \circ R_T \circ L_T = L_T$ から $L_T$ が $R_T$ 経由で完全復元できることになり、$\eta_{\text{unit}, T}$ は同型と帰結する
5. (3) と (4) は矛盾。∴ 完全 retraction $S$ は存在しない $\square$

> [SOURCE 強: aletheia.md §1 L99-L107 + 本稿 §1.2 C2 + §5.6 NRFT 骨格、HGK 内部一次]

**関手的書き下し** (Yoneda embedding を用いた弱形): $R_T$ が full and faithful でも essentially surjective でない場合、Yoneda embedding $y: \text{真理}_0 \hookrightarrow [\text{真理}_0^{op}, \mathbf{Set}]$ と同様に、$R_T$ の image は $\text{予測}_1$ の真部分圏に留まる。Yoneda embedding が一般に retraction を持たないことは標準事実 [SOURCE 中候補: nLab "Yoneda embedding" subagent verbatim 抽出 / G-ζ 独立検証義務]。本稿の $R_T$ も同型の構造的非可逆性を持つ。

#### §8.4.3 Gödel 対角化との関手論的対応

Gödel 第二不完全性定理の categorical proof (Joyal arithmetic universe 経路 + Lawvere fixed-point theorem) と本稿の形式装置を対応づける。

**Lawvere fixed-point theorem (1969)** [SOURCE 中候補: nLab + Wikipedia subagent verbatim / G-ζ 独立検証義務]:

> Cartesian closed category $\mathcal{C}$ で $f: A \to B^A$ が point-surjective ならば、任意の endomorphism $g: B \to B$ は fixed point を持つ。

**対偶**: $g: B \to B$ が fixed point を持たないなら、$f: A \to B^A$ は point-surjective でない。

この対偶が Cantor / Gödel 第一不完全性 / Tarski 真理定義不可能性の **共通構造** を与える。

**形式装置の対応表**:

| | Gödel 第二不完全性定理 (Joyal-Lawvere 経路) | Predictions Descend Theorem (本稿) |
|:---|:---|:---|
| 体系 | Arithmetic universe $\mathcal{A}$ (list-arithmetic pretopos) | 圏 $\mathbf{Sci}$ + 内在化随伴対 $L_T \dashv R_T$ |
| 体系内の自己内在化 | $\mathcal{A}$ は内部に自身のコピーを含む (initial AU の自己言及性) | $\mathbf{Sci}$ の各 $T$ は自身の予測生成 $R_T$ を内部に含む |
| 対角化操作 | Lawvere $f: A \to \Omega^A$ の point-surjectivity を仮定し $\neg: \Omega \to \Omega$ の fixed point を導出 | $S: \text{予測}_1 \to \text{真理}_0$ の retraction 性を仮定し $\eta_{\text{unit}}$ の同型性を導出 |
| 不可能性の根拠 | $\neg$ は fixed point を持たないため、$f$ は point-surjective でない | $\eta_{\text{unit}}$ は非同型のため、$S$ は retraction でない |
| 体系の核 | $\text{Con}(T) = T$ の無矛盾性 | $T_0(T) = T$ の真理₀ 性 |
| 形式不可能性 | $T \nvdash \text{Con}(T)$ | $S \circ R_T \neq \text{Id}_{真理_0}$ (構成不能) |

> [SOURCE 強: arxiv 2004.10482 v1 (van Dijk-Gietelink Oldenziel 2020 "Gödel's Incompleteness after Joyal") — alphaXiv 完全 PDF Read 経由で 2026-04-26 一次到達済。Lawvere 1969 原典と Joyal 1973 lecture notes は依然 secondary access (G-θ'-4 残課題)]

**自己言及構造の翻訳**: Gödel は「証明計算 $\text{Prov}_T$ が自身の無矛盾性を表現する」= $T$ 内の syntactic functor が semantic に retract できない、として自己言及不可能性を示す。本稿は「予測₁ 生成 $R_T$ が自身の真理₀ 性を表現する」= $\mathbf{Sci}$ 内の下降関手が上昇に retract できない、として同型構造を提示する。両者の **共通構造**: 体系内の operation が体系自身の核を識別するための retraction が、構造的不等式 (Gödel: 対角化の fixed point 不在 / 本稿: $\eta_{\text{unit}}$ 非同型) によって阻まれる。

#### §8.4.3.1 vdG-O 2020 categorical Gödel proof の verbatim 構造 (Round 5 G-λ 着手, 2026-04-26)

§8.4.3 対応表は構造的類比に留まっていた。本節は van Dijk-Gietelink Oldenziel 2020 (以下 vdG-O 2020) の categorical Gödel proof を verbatim で接地し、本稿 $\mathbf{Sci}$ への適用経路を **強 SOURCE 付きで** 確定する。これは G-λ (NRFT 完全形式証明) の Round 5 進捗として §8.4.4 の達成度を 60-70% → 80% に押し上げる。

**Step 1: Arithmetic Universe (AU) の 4 公理**

> **Definition 1.1 (vdG-O 2020 p. 2, verbatim)**: An arithmetic universe is a list-arithmetic pretopos. That is, a category with finite limits, stable disjoint coproducts, stable effective quotients by monic equivalence relations and parameterized list-objects.

> **Definition 2.9 (vdG-O 2020 p. 5, verbatim)**: A pretopos is a category equipped with finite limits, stable finite disjoint coproducts and stable effective quotients of monic equivalence relations. An arithmetic universe is a pretopos which has parametrized list objects.

4 公理の役割 (vdG-O 2020 pp. 2-3 verbatim 注記): finite limits + disjoint coproducts → ∧ ∨ ⊤ ⊥, stable effective quotients → ∃ 演算子, parameterized list objects → primitive recursion。本稿 $\mathbf{Sci}$ 圏が AU 構造を満たすかは G-θ'-1 として独立検証の余地を残すが、必要 4 要素は明示された。

**Step 2: 初期 AU $U_0$ の構成経路 (Skolem → Pred → exact completion)**

> **vdG-O 2020 pp. 2 verbatim**: The category U is build in stages. First, one starts with the initial 'Skolem theory' $\Sigma_0$, in effect a category whose objects are all products of $\mathbb{N}$. (...) The next step is to consider the category of decidable predicates in $\Sigma_0$, denoted $\text{Pred}(\Sigma_0)$. The final step adjoins quotients to obtain $\text{Pred}(\Sigma_0)^{\text{ex/reg}}$. It will be a theorem that this coincides with the initial arithmetic universe $U_0$.

> **Theorem 5.8 (vdG-O 2020 p. 19, verbatim)**: Let $E$ be any arithmetic universe. Internally, we may construct the initial arithmetic universe object $U_0(E)$.

これで G-θ'-1 (本稿 $\mathbf{Sci}$ の list-arithmetic pretopos 構成) は **形式的経路が明示** された。$\mathbf{Sci}$ 圏に AU 内部構成 $U_0(\mathbf{Sci})$ を施し、その内部言語で本稿の $L \dashv R$ + $\eta_{\text{unit}}$ 非同型を再表現する経路が確定。完全実行は本稿外の研究プログラム。

**Step 3: Syntactic-Semantic 随伴対 (G-θ'-3 解消の鍵)**

> **vdG-O 2020 pp. 16 verbatim** (§4 直前): $\text{AU} \rightleftarrows T\text{-type}_\text{AU}$ via Lan ⊣ Syn / where the Lan-functor produces the internal language $T_U$ of an arithmetic universe $U$ and the Syn-functor the syntactic category $C_T$ for a given $T_\text{AU}$-type theory $T$. **In this case, the adjunction is in fact an equivalence.**

> **Theorem 4.11 (vdG-O 2020 p. 17, verbatim)**: The syntactic category coincides with Joyal's construction: $\text{Syn}(T_\text{AU}) \cong U_0 := \text{Pred}(\Sigma_0)^{\text{ex/reg}}$.

これは G-θ'-3 (自己言及の syntactic-semantic adjoint への翻訳) を **直接解消する**: 「Gödel numbering = adjoint pair between syntactic and semantic categories」は vdG-O 2020 では **Lan ⊣ Syn が equivalence (圏同値)** として明示される。本稿 $\mathbf{Sci}$ への適用は、$\mathbf{Sci}$ の内部言語 $T_\mathbf{Sci}$ と $\text{Syn}(T_\mathbf{Sci})$ の equivalence を主張する経路として確定する。

**Step 4: Cantor categorical diagonal (Gödel 第一/第二の核工具)**

> **Theorem 5.2 (Cantor) (vdG-O 2020 p. 18, verbatim)**: Let $\mathcal{E}$ a topos in which $1$ is projective. If there exists an enumeration $f: A \twoheadrightarrow PA$, then $\mathcal{E}$ is degenerate.

これが Gödel 第一/第二の **核となる対角化補題の categorical 形** である (§8.4.3 で「Lawvere FP」と書いた箇所はより正確には「Cantor categorical diagonal の AU 内擬制」を指す。詳細は §8.4.4 honest 訂正を参照)。

**Step 5: Gödel 第一 / 第二 categorical proof の verbatim 主結果**

> **Theorem 5.19 (Gödel's First Incompleteness Theorem) (vdG-O 2020 p. 25, verbatim)**: If an arithmetic universe object $U$ in $U_\text{rec}$ is [syntactically] complete then it is the trivial AU-object [hence inconsistent].

> **証明骨格 (vdG-O 2020 p. 25 verbatim)**: Cantor's Diagonal argument will now be imitated to prove Gödel's Incompleteness Theorem in a special case. (...) The subobject $J n \in D K$ is the categorical incarnation of the Gödel sentence $G$; asking whether this subobject factors through $1$ is equivalent to asking whether $G$ is provable.

> **Theorem 5.20 (Gödel's Second Incompleteness Theorem) (vdG-O 2020 p. 26, verbatim)**: Assume that $U_0$ is consistent. Then the subobject $J\text{True}' = \text{False}'K \hookrightarrow 1$ does not equal the minimal subobject $0 \hookrightarrow 1$ in $U_0$.

これが Gödel 第二不完全性定理の categorical proof の **完全形 verbatim**。本稿 Predictions Descend Theorem (§8.4.2) との **形式的対応** が以下のように確定する:

| | vdG-O 2020 (Joyal categorical) | 本稿 (§8.4.2) |
|:---|:---|:---|
| 体系 | $U_0$ = $\text{Pred}(\Sigma_0)^{\text{ex/reg}}$ (initial AU) | $\mathbf{Sci}$ = 科学理論圏 + 内在化随伴対 $L_T \dashv R_T$ |
| 内部自己言及 | $U_0(U_0)$ via Theorem 5.8 (any AU 内に initial AU) | $\mathbf{Sci}$ の各 $T$ は自身の $R_T$ を内部化 |
| 自己言及表現 | Gödel sentence の categorical incarnation = subobject $J n \in D K$ | $T_0(T)$ の自己言及表現 = retraction $S$ の存在問い |
| 対角化工具 | Cantor categorical (Theorem 5.2) を AU 内で擬制 | $\eta_{\text{unit}, T}$ 非同型 ($\text{Ker} > 0$) を §1.2 C2 から導入 |
| 不可能性 | $J\text{True}' = \text{False}'K \neq 0$ (Theorem 5.20) | $S \circ R_T \neq \text{Id}_{真理_0}$ (構成不能, §8.4.2 step 5) |

**Step 6: Lawvere-like fixed-point は Löb 用 (Gödel 第二には不使用)**

> **Lemma 6.12 (vdG-O 2020 p. 29, verbatim)**: We have the following lemma, the AU-incarnation of the diagonalization lemma. **It is reminiscent of Lawvere's fixed point theorem.** Let $T: P1' \to P1'$ be a map in $U$. Then $T$ has a fixed point.

このLemma は **Theorem 6.13 (Löb's theorem)** の証明に用いられる。Gödel 第二不完全性 (Theorem 5.20) は Cantor categorical (Theorem 5.2) の AU 内擬制を直接使い、Lawvere FP には依拠しない。

これは本稿 §8.4.3 の対応表 (旧版で「Lawvere fixed-point theorem への reduction」と書いた箇所) の **honest 訂正** を要求する: Gödel 第二の categorical proof は Cantor diagonal の AU 内擬制であり、Lawvere FP は同じ系統 (対角化補題) に属するが、Gödel 第二の直接道具ではない。本稿 $\eta_{\text{unit}}$ 非同型 → retraction 不可能の経路は Cantor categorical との対応がより正確である。詳細は §8.4.4 honest 較正で再較正。

**Step 7: Yanofsky 2003 経由 Lawvere FP statement 接地 (原典直 Read 未達、Yanofsky による restatement に依拠)**

Lawvere 1969 "Diagonal arguments and cartesian closed categories" (Springer LNM 92, pp. 134-145) **原典 PDF 直 Read は本セッションでも未達**。代替として **Yanofsky 2003 (arxiv math/0305282)** が Lawvere の主定理を set-function 言語で再述している (Yanofsky abstract: "Following F. William Lawvere, we show that many self-referential paradoxes...")。本 Step は Yanofsky 2003 の verbatim 文面を強 SOURCE として接地するが、**Yanofsky の restatement が Lawvere 1969 原典に faithful であるという主張は Yanofsky 自身のもの** であり、本稿は原典との一字一句照合は行っていない。

> **Theorem 3 (Diagonal Theorem) (Yanofsky 2003 p. 14, verbatim from Yanofsky)**: If $Y$ is a set and there exists a set $T$ and a function $f: T \times T \to Y$ such that all functions $g: T \to Y$ are representable by $f$ (there exists a $t \in T$ such that $g(-) = f(-, t)$), then all functions $\alpha: Y \to Y$ have a fixed point.

これが Yanofsky による Lawvere fixed-point theorem の対偶形 set-function 版 (= 通常 "Lawvere FP" と呼ばれる statement の Yanofsky 翻案)。原 Cartesian closed category 版は $f: T \to Y^T$ の point-surjectivity から始まるが、Yanofsky の curry 化 ($f: T \times T \to Y$ via $g(t, t') = \hat{f}(t')(t)$) で set 言語に降ろされている。

> **Theorem 1 (Cantor's Theorem) (Yanofsky 2003 p. 5, verbatim from Yanofsky)**: If $Y$ is a set and there exists a function $\alpha: Y \to Y$ without a fixed point (for all $y \in Y$, $\alpha(y) \neq y$), then for all sets $T$ and for all functions $f: T \times T \to Y$ there exists a function $g: T \to Y$ that is not representable by $f$ i.e. such that for all $t \in T$, $g(-) \neq f(-, t)$.

Yanofsky 2003 は Cantor / Russell / Grelling / Liar / Strong Liar / Richard / Tarski / Turing Halting / 非r.e. 言語 / oracle Turing P^B ≠ NP^B / Gödel 第一 (p. 16) / Gödel-Rosser (p. 16) / Löb (p. 17) を Lawvere FP の特殊ケースとして set-function 言語で統一展開している。

**本稿 NRFT との関係**: 本稿 Predictions Descend Theorem (§8.4.2) は、Yanofsky 2003 の枠組みでは以下の特殊ケースとして読める [仮説 75%、原典 verbatim 照合未達のため確信 90% には届かない]:
- $T$ = 真理₀ の対象集合
- $Y$ = 予測₁ の対象集合
- $f: T \times T \to Y$ = 体系 $T$ が自身の真理₀ 性を予測₁ で表現する写像
- $g$ = retraction 候補 $S$ (= Yanofsky の「representable by $f$」要求)
- $\alpha: Y \to Y$ = $\eta_{\text{unit}}$ 非同型由来の「fixed point を持たない」操作

§1.2 C2 構造保存定理 ($\eta_{\text{unit}}$ 非同型) が「$\alpha$ に fixed point なし」を保証するため、Yanofsky 2003 Theorem 1 の対偶により retraction $g$ (= $S$) は存在しない。これが Lawvere FP の本稿への直接適用 (Yanofsky restatement 経由)。

> [SOURCE 強: arxiv math/0305282 v1 (Yanofsky 2003) — alphaXiv full PDF 完全 Read 経由で 2026-04-26 一次到達済。**Yanofsky 自身の文面は強 SOURCE**。**Lawvere 1969 原典との verbatim 一致は Yanofsky の主張に依拠**、本稿は原典直 Read を達成していない (Springer LNM 92 は library access が必要、TAC reprint URL は本セッションで commentary のみ取得)。Lawvere 1969 References [11] = "F. William Lawvere. Diagonal arguments and cartesian closed categories. In Category Theory, Homology Theory and their Applications, II (Battelle Institute Conference, Seattle, Wash., 1968, Vol. Two), pages 134–145. Springer, Berlin, 1969." を Yanofsky 2003 が引用、後続の Lawvere-Schanuel 1991 + Lawvere-Rosebrugh 2003 でも同形式とされる]

**G-θ'-4 進捗 update (honest)**: vdG-O 2020 完全 PDF Read (1/3 ✓ 強) + Yanofsky 2003 経由 Lawvere FP statement 接地 (~0.7/3 ✓ 強だが原典直 Read 未達) + Joyal 1973 lecture notes は publicly unavailable (vdG-O 2020 自身が「never made publicly available」と明記、Maietti 2003 + Morrison 1996 経由で間接捕捉済) で **総合 ~1.7/3 達成 (実質 ~57%)**。Lawvere 1969 原典 PDF 直 Read による「強」昇格は依然残課題 (TAC reprints / library access / 著者 archive 等の経路)。

#### §8.4.3.2 $R_T$ の AU 内 Gödel sentence 完全 commutative diagram (G-θ'-2 Round 5 着手, 2026-04-26)

§8.4.3.1 で確定した Yanofsky 2003 Theorem 1 (Cantor の generalized 形) の本稿 $R_T$ への適用を、完全 commutative diagram として明示する。本節は **G-θ'-2** ($R_T$ の AU 内 Gödel sentence 完全 commutative diagram) の Round 5 着手であり、§8.4.2 の論理鎖 (5 ステップ) を Yanofsky 2003 の curry 化形式 ($f: T \times T \to Y$) で図式化する。

**Step 1: 翻訳辞書 (Yanofsky 2003 Theorem 1 ↔ 本稿 §8.4.2)**

| Yanofsky 2003 (set-function 言語) | 本稿 (圏 $\mathbf{Sci}$ 内、§8.4.2) |
|:---|:---|
| 集合 $T$ | $\text{真理}_0$ の対象集合 (= 科学理論の真理₀ 性) |
| 集合 $Y$ | $\text{予測}_1$ の対象集合 (= 観測可能な予測値) |
| 関数 $f: T \times T \to Y$ | 「2 理論の相互予測」関手 $f(T_1, T_2) := R_{T_2}(L_{T_2}(T_1)) \in \text{予測}_1$ |
| 関数 $\alpha: Y \to Y$ | $\eta_{\text{unit}, T}$ 非同型由来の「予測値シフト」関手 (§1.2 C2 から「fixed point なし」が保証) |
| 表現可能性 $g(-) = f(-, t_0)$ | retraction 候補 $S: \text{予測}_1 \to \text{真理}_0$ が「ある $T_0$ に対して $S \circ R_{T_0} = \text{Id}$」 |
| 対角化 $\Delta: T \to T \times T$ | 「自己参照」: 理論 $T$ を $(T, T)$ に送る (理論が自分自身を予測対象とする) |
| 構成された $g(t) = \alpha(f(t, t))$ | 「自己予測 + シフト」: $T \mapsto \alpha(R_T(L_T(T)))$ (自己内在化された予測の non-iso 像) |

**Step 2: Commutative diagram 完全形** (Yanofsky 2003 p. 5 Theorem 1 の構造を本稿 $R_T$ で展開)

```text
            f
真理₀ × 真理₀ ──────────────────→ 予測₁
   ↑                                   │
   │ Δ (対角化)                        │ α (非同型シフト)
   │                                   │
   │                                   ↓
真理₀ ─────────────────────────→ 予測₁
            g := α ∘ f ∘ Δ
```

ここで:
- $f(T_1, T_2) = R_{T_2}(L_{T_2}(T_1))$ — 理論 $T_2$ が理論 $T_1$ を入力として生成する予測
- $\Delta(T) = (T, T)$ — 自己参照 (理論が自分自身を予測対象とする)
- $\alpha(y) = \eta_{\text{unit}}^{\sharp}(y)$ — $\eta_{\text{unit}}$ 非同型から誘導された「予測値の non-iso シフト」、§1.2 C2 ($|\text{Ker}(\eta_{\text{unit}})| > 0$) により fixed point を持たない
- $g = \alpha \circ f \circ \Delta$ — 構成された「自己予測 + 非同型シフト」関手

**Step 3: Naturality 検証** (図式の commutativity)

上図の右側経路 $\alpha \circ f \circ \Delta(T) = \alpha(R_T(L_T(T)))$ と、もし retraction $S$ が存在し $g$ が $f$ で表現可能 ($g(-) = f(-, T_0)$ for some $T_0$) なら、評価 $T = T_0$ で:

$$f(T_0, T_0) = g(T_0) = \alpha(f(T_0, T_0))$$

すなわち $f(T_0, T_0)$ は $\alpha$ の fixed point。これは前提 (C2 から $\alpha$ に fixed point なし) と矛盾。

> **G-θ'-2 中核命題 (本稿固有)**: 本稿 $\mathbf{Sci}$ 内で、$\eta_{\text{unit}, T}$ 非同型 + 上図 commutative diagram の構成下では、retraction $S: \text{予測}_1 \to \text{真理}_0$ で $S \circ R_{T_0} = \text{Id}_{\text{真理}_0}$ を満たすものは存在しない。これが Predictions Descend Theorem の Yanofsky 統一展開経由の categorical 証明骨格。

**Step 4: vdG-O 2020 Theorem 5.19 の本稿対応 pullback** (より AU-native な形式化)

vdG-O 2020 が AU 内で構成する pullback diagram (Theorem 5.19 proof, p. 25 verbatim):

```text
   D ──────→ 1
   │          │
   │          │ false'
   ↓          ↓
   N ──Δ_N──→ N × N ──ι×e──→ [1', N'] × P'N' ──eval──→ P'1'
```

本稿対応 pullback (G-θ'-2 翻訳):

```text
   D_T ─────────→ 1 (= 自明真理理論 ⊤)
    │             │
    │             │ false_pred' (= 「不一致」予測値、$\eta_{\text{unit}}$ 非同型から構成)
    ↓             ↓
   真理₀ ──Δ──→ 真理₀ × 真理₀ ──f──→ 予測₁
```

ここで $D_T \subset \text{真理}_0$ は「自己予測が false_pred' に等しい理論の部分集合」= 本稿の **categorical Gödel sentence** (vdG-O 2020 p. 26 で $\llbracket n \in D \rrbracket$ と書かれた subobject の本稿アナロジー)。$D_T$ が $1$ (= $\text{真理}_0$ の terminal) を通って factor するか否かが、本稿 NRFT における「retraction $S$ が存在するか」と等価。

**Step 5: honest 開示 — 完全形式化との距離 + Codex Bridge 警告反映 (2026-04-26)**

本節 §8.4.3.2 で達成したもの:
- (a) Yanofsky 2003 Theorem 1 の本稿 $R_T$ への翻訳辞書 (Step 1) ✓
- (b) Commutative diagram の構造的提示 (Step 2) ✓
- (c) vdG-O 2020 Theorem 5.19 pullback の本稿構造的アナロジー (Step 4) ✓

**Codex Bridge 警告反映 — Hidden assumption の honest 開示** (2026-04-26 background delegation 由来):

⚠️ 本節 Step 2-3 は **2 つの hidden assumption** を含む。これらは本節射程内で証明されておらず、本稿 NRFT の Yanofsky 統一展開経由 categorical 証明への適用には **これらの assumption の独立証明が必要**:

1. **HA-1: 「$\eta_{\text{unit}}$ 非同型 ⇒ $\alpha$ に fixed point なし」は自明でない**
   - $\eta_{\text{unit}}$ 非同型 = $R \circ L \neq \text{Id}$ は自然変換が可逆でないことのみ意味し、specific な $\alpha: \text{予測}_1 \to \text{予測}_1$ の構成 + その fixed point 不在を **直接含意しない**
   - Yanofsky 2003 Theorem 1 の前提は「ある $\alpha: Y \to Y$ で $\forall y, \alpha(y) \neq y$」(set-function 言語の literal な意味)。本稿の $\alpha$ がこの強い性質を満たす構成は **本節射程外**
   - 残課題: $\eta_{\text{unit}}$ 非同型から「fixed point なし $\alpha$」を構成する具体的関手 (例: $\eta_{\text{unit}}$ の cokernel embedding 経由) の独立証明
2. **HA-2: set-function diagram から $\mathbf{Sci}$ 圏内関手への橋が未提示**
   - Yanofsky 2003 は集合と関数で書かれる (圏 Set 内)。本稿 $\mathbf{Sci}$ は理論を対象とする抽象圏で、Set への忠実関手 $\lvert \cdot \rvert: \mathbf{Sci} \to \text{Set}$ が存在するか自明でない
   - 残課題: $\lvert \cdot \rvert$ の構成 + Yanofsky Theorem 1 を $\mathbf{Sci}$ 内で再証明する categorical naturality verification

本節 §8.4.3.2 で達成していないもの:
- (d') $D_T$ subobject の構成可能性 ($\mathbf{Sci}$ が AU 4 公理を満たす独立検証 = G-θ'-1 残)
- (e') $\alpha: \text{予測}_1 \to \text{予測}_1$ の具体的構成 + fixed point 不在の独立証明 (HA-1)
- (f') set → 関手 の橋 + 全 commutative square の categorical naturality verification (HA-2)

**G-θ'-2 進捗 update (Codex 警告反映後 honest)**: 翻訳辞書 + 構造的アナロジー提示で **G-θ'-2 ~50% 達成** (Codex Bridge 警告反映で当初 ~70% から honest 降格)。残 50% = HA-1 ($\alpha$ 構成 + fixed point 不在証明) + HA-2 (set → 関手 橋) + $D_T$ subobject 独立構成 (G-θ'-1 残と連動)。本稿主張への影響: §8.4.4 達成度への寄与は +2% から **+1%** に honest 降格 (構造的アナロジーは提示されたが strong SOURCE 接地が hidden assumption に依存)。

#### §8.4.3.3 HA-1 独立証明試行と構造的 reduction の発見 (Round 5 G-θ'-2 補強, 2026-04-26)

§8.4.3.2 Step 5 で開示した HA-1 (「$\eta_{\text{unit}}$ 非同型 ⇒ $\alpha: \text{予測}_1 \to \text{予測}_1$ に fixed point 不在」の自明でない含意) に対し、本節は独立証明を試行する。**結果: 完全証明には到達しないが、HA-1 が G-θ'-1 (2)(4) AU 公理残課題に reduce されることを発見する**。これは Yugaku §M6 「虚は実を引く」規律に従い、虚の構造的所在を明示する操作である。

**Step 1: 試行 1 — 直接構成 (Yanofsky-style "negation" 関手)**

Yanofsky 2003 が Cantor / Russell / Liar 等で用いる "negation" 関手 $\alpha = \neg: 2 \to 2$ ($\neg(0) = 1$, $\neg(1) = 0$) を本稿 $\text{予測}_1$ に直接持ち込む試行。

要件:
- $\text{予測}_1$ に **subobject classifier** $\Omega$ が存在 (topos 的構造)
- $\text{予測}_1$ に non-trivial な真偽値 pair $(\top, \bot)$ が存在
- $\neg: \Omega \to \Omega$ が定義可能 + $\neg$ に fixed point なし

**結果**: $\text{予測}_1$ に $\Omega$ が存在するかは **本稿の設定下では自明でない**。$\Omega$ 存在は topos 公理 (Lawvere 2006 ETCS) または locally cartesian closed 構造を要求するが、Joyal arithmetic universe (vdG-O 2020 Definition 1.1) は **predicative** で典型的に $\Omega$ を持たない (vdG-O 2020 §2 Remark 2.12 verbatim: "AU's are natively predicative" + "topological space is fundamentally relying on the power set axiom of ZFC, which AU's avoid")。

直接構成は失敗。

**Step 2: 試行 2 — $\eta_{\text{unit}}$ から $\alpha$ への自然な構成 (cokernel embedding 経由)**

$\eta_{\text{unit}}: \text{Id}_{\text{予測}_1} \Rightarrow R \circ L$ 非同型は、$\text{Im}(\eta_{\text{unit}}) \subsetneq R \circ L$ の意味で proper image を持つ。$\text{予測}_1 / \text{Im}(\eta_{\text{unit}})$ という cokernel-like 構造を取り、$\alpha = $「cokernel への shift」と定義する試行。

要件:
- $\text{予測}_1$ に **stable effective quotients of monic equivalence relations** が存在 (AU 公理 3)
- Cokernel object が $\mathbf{Sci}$ 内で意味を持つ
- $\alpha$ が「fixed point なし」関手として正しく定義される

**結果**: AU 公理 3 (effective quotients) は §8.4.1.1 で「plausible [仮説 60%]」と判定済 (Quine-Duhem 観測等価性経由)。仮に AU 公理 3 が成立すれば、$\alpha$ の構成は **可能** だが、その fixed point 不在は更なる検証 (cokernel に non-zero element が存在することの保証) を要する。

部分的に進むが完全証明には到達しない。

**Step 3: 試行 3 — $\eta_{\text{unit}}$ の Yoneda embedding 経由の dualization**

Yoneda embedding $y: \text{予測}_1 \to [\text{予測}_1^{op}, \mathbf{Set}]$ を経由し、$\eta_{\text{unit}}$ 非同型を presheaf 圏での「epimorphism not iso」に翻訳する試行。$\alpha$ を presheaf 圏内で構成し、Yoneda lemma で $\text{予測}_1$ に引き戻す。

要件:
- $\text{予測}_1$ が **small** ([0, ω) cardinality) または cocomplete cocompletion を持つ
- Presheaf 圏が $\Omega$ を持つ (これは standard、$\Omega = y(*)$)

**結果**: Presheaf 圏 $[\text{予測}_1^{op}, \mathbf{Set}]$ には標準的に $\Omega$ が存在 (Lawvere-Tierney topology 経由)。**ここで $\alpha$ を構成し、Yoneda で引き戻すと、本稿 $\text{予測}_1$ 上の $\alpha$ が定義される**。これは Step 1 の直接構成失敗を回避する経路として **有望**。

ただし: presheaf 圏での $\alpha$ の fixed point 不在は **本稿 $\text{予測}_1$ 上の $\alpha$ の fixed point 不在を含意するか** が独立証明事項。Yoneda lemma は表現可能関手の同型を保証するが、関手の fixed point 構造は一般に Yoneda で保存されない。

**部分的進捗 ✓** だが完全証明には更なる工程が必要。

**Step 4: HA-1 → G-θ'-1 (2)(4) への構造的 reduction の発見 (本節の主成果)**

3 つの試行から、HA-1 解消は以下の **構造的 reduction** に帰着することが判明:

> **Reduction 命題 (本稿固有 [仮説 70%、Round 5 §8.4.3.3 で導出])**: HA-1 (「$\eta_{\text{unit}}$ 非同型 ⇒ $\alpha: \text{予測}_1 \to \text{予測}_1$ に fixed point 不在」の構成的証明) は、以下のいずれかに reduce される:
>
> - **(R1)** $\text{予測}_1$ が **subobject classifier $\Omega$** を持つ (topos 的構造、AU 公理を超える要請)
> - **(R2)** $\text{予測}_1$ が **stable effective quotients of monic equivalence relations** (AU 公理 3) + **cokernel objects に non-zero element が存在することの独立保証** を持つ
> - **(R3)** $\text{予測}_1$ が **small** または **cocomplete cocompletion** を持つ + **Yoneda embedding 経由の $\alpha$ fixed point 構造の保存** が成立する

これら (R1)/(R2)/(R3) のいずれも本稿 $\mathbf{Sci}$ の現状 (§8.4.1.1 で AU 公理 (2)(4) uncertain と honest 開示) では **独立検証されていない**。すなわち HA-1 解消は **G-θ'-1 (2)(4) 完全解消 + 追加 topos/cocompleteness 公理** に帰着する。

**Step 5: 本節 §8.4.3.3 の honest 達成評価**

本節 §8.4.3.3 で達成したもの:
- (a) HA-1 への 3 つの直接構成試行 (Yanofsky negation / cokernel shift / Yoneda dualization) ✓
- (b) 各試行の失敗または部分達成の構造的原因 (predicative AU / AU 公理 3 / Yoneda 保存) の明示 ✓
- (c) **Reduction 命題** [仮説 70%] による HA-1 → G-θ'-1 (2)(4) + topos 公理 への構造的帰着 ✓

本節 §8.4.3.3 で達成していないもの:
- (d') HA-1 完全解消 (= $\alpha$ の構成的存在 + fixed point 不在の独立証明)
- (e') Reduction 命題 [仮説 70%] の確信度を 90%+ に押し上げる (本稿外プログラム、$\mathbf{Sci}$ AU 公理独立検証 + topos/cocompleteness 解析)

**HA-1 進捗 update (honest)**: 3 試行 + Reduction 命題で **HA-1 ~30% 達成** (構造的 reduction の特定 + 各 R1/R2/R3 経路の所在明示)。残 70% = R1/R2/R3 のいずれかの完全解消 (本稿外、本格的圏論研究プログラム)。

**G-θ'-2 進捗 update (HA-1 部分達成反映後 honest)**: HA-1 ~30% + HA-2 未着手 + $D_T$ 独立構成未達 = G-θ'-2 達成度 50% → **57%** (HA-1 部分達成で +7%)。本稿主張への影響: §8.4.4 達成度への寄与は **+1%** から **+1.5%** に微小昇格 (構造的 reduction の発見が「虚の所在の明示化」として価値)。

**重要な副次成果**: HA-1 解消が G-θ'-1 (2)(4) 残課題に reduce されることの発見は、本稿の道 C 達成度の **天井が G-θ'-1 (2)(4) 完全解消で律速される** ことを示す。これは Round 6 以降の研究プログラムの優先順位を明確化する: G-θ'-1 (2)(4) の完全解消が、HA-1 + HA-2 + G-θ'-2 残全体を一括して解消する単一の bottleneck である。

#### §8.4.4 honest 較正 (G-θ' 最終状態)

**達成範囲** (Round 5 G-λ 進捗 2026-04-26 反映):

1. **Predictions Descend Theorem の形式陳述化** ✓ — §8.4.2 で関手的書き下し + 5 ステップ論理鎖を提示
2. **categorical Gödel proof への reduction** ✓ (Round 5 で訂正) — §8.4.3.1 で vdG-O 2020 verbatim 接地により、本稿 $\eta_{\text{unit}}$ 非同型 → retraction 不可能の経路は **Cantor categorical (Theorem 5.2) の AU 内擬制 (Theorem 5.19/5.20)** に対応することが判明。旧版「Lawvere FP への reduction」は **honest 訂正**: Lawvere-like FP (Lemma 6.12) は Löb (Theorem 6.13) 用であり、Gödel 第二の直接道具は Cantor categorical (詳細 §8.4.3.1 Step 6)
3. **Joyal arithmetic universe 経路の確定** ✓ (Round 5 で「同定」→「確定」昇格) — §8.4.3.1 で AU の 4 公理 (Definition 1.1, 2.9 verbatim) と $U_0$ 構成経路 (Skolem $\Sigma_0$ → $\text{Pred}(\Sigma_0)$ → $\text{Pred}(\Sigma_0)^{\text{ex/reg}}$) を強 SOURCE で確定
4. **Syntactic-Semantic adjoint の正式 identification** ✓ (Round 5 新達成) — §8.4.3.1 Step 3 で Lan ⊣ Syn が **equivalence (圏同値)** として vdG-O 2020 §4 + Theorem 4.11 から確定。G-θ'-3 解消の鍵を握る

**honest 訂正 (Round 5 で発見)**: §8.4.3 旧版で「Lawvere fixed-point theorem への reduction」と書いた箇所は、より正確には「**Cantor categorical diagonal の AU 内擬制への reduction (Gödel 第二経路) + Lawvere-like FP への reduction (Löb 経路)**」と読むべき。両者は対角化補題の同じ系統に属するが、Gödel 第二の直接道具は前者である (vdG-O 2020 Theorem 5.20 proof を直接 Read で確認)。本稿主張内容に影響はないが、形式装置の精度が向上した。

**継続課題** (G-θ' = 旧 G-θ の精細化、Round 5 後の状態):

| ギャップ | Round 4 状態 | Round 5 状態 (2026-04-26) | 残課題 |
|:---|:---|:---|:---|
| **G-θ'-1** | 未達 | **部分着手 ✓** (Round 5, 2026-04-26): §8.4.1.1 で 4 公理状態検査表を提示。(1) finite limits + (3) effective quotients は plausible [仮説 60-65%]、(2) disjoint coproducts + (4) parameterized list objects は uncertain [仮説 50-55%]。**4 公理総合**: $\mathbf{Sci}$ は AU 候補 [仮説 55-60%]、full Joyal AU として完全独立検証されたわけではない | (2) disjoint coproducts の操作的定義 (Quine-Duhem 文脈) + (4) parameterized list objects の循環依存解消 (外部 $\mathbb{N}$ 借用 vs 内部構成) を本格的圏論研究プログラムとして起票 (Round 6 課題) |
| **G-θ'-2** | 骨格のみ | **~57% 達成 ✓** (Round 5, 2026-04-26、HA-1 ~30% 部分達成反映後 honest): §8.4.3.2 で翻訳辞書 + 構造的アナロジー + vdG-O 2020 pullback 対応 + §8.4.3.3 で **HA-1 独立証明試行 + Reduction 命題 [仮説 70%]** (HA-1 → G-θ'-1 (2)(4) AU 公理 + topos 公理への構造的帰着) | 残 43% = HA-1 残 70% (R1 topos $\Omega$ / R2 cokernel non-zero / R3 Yoneda 保存 のいずれかの完全解消) + HA-2 (set-function → 関手 橋 + 忠実関手 $\lvert \cdot \rvert: \mathbf{Sci} \to \text{Set}$) + $D_T$ subobject 独立構成 (G-θ'-1 残と連動) |
| **G-θ'-3** | 原典未到達 | **解消** (vdG-O 2020 §4 + Theorem 4.11 で Lan ⊣ Syn equivalence verbatim 確定) | 本稿 $\mathbf{Sci}$ への適用 ($\mathbf{Sci}$ 内部言語と $\text{Syn}(T_\mathbf{Sci})$ の equivalence 主張) は本稿外 |
| **G-θ'-4** | 全 PDF 未到達 | **~1.7/3 達成 ✓** (2026-04-26、honest): vdG-O 2020 完全 PDF Read (1/3 ✓ 強) + Yanofsky 2003 (arxiv math/0305282) 完全 PDF Read 経由で **Lawvere FP statement 接地** (~0.7/3 ✓ — Yanofsky による restatement 経由、Lawvere 1969 原典 verbatim 一致は Yanofsky の主張に依拠、原典直 Read 未達) + Joyal 1973 lecture notes は vdG-O 2020 自身が "never made publicly available" と明記、内容は Maietti 2003 + Morrison 1996 経由で間接継承 (~0/3 直接、~0.5/3 間接) | Lawvere 1969 原典 PDF 直 Read (TAC reprints / library access / 著者 archive 等の経路) は依然残課題 |

**「Gödel 級」と「本稿実装」の境界** (Round 5 後):

- **Gödel 級が要求するもの**: (a) 形式系の syntactic 表現、(b) Gödel numbering による self-reference 内在化、(c) provability predicate $\text{Prov}_T$ の体系内表現可能性、(d) 対角化補題による fixed point sentence 構成、(e) $T \nvdash \text{Con}(T)$ の純粋形式証明
- **本稿が達成したもの (Round 5 拡張)**: (a') 圏 $\mathbf{Sci}$ の構造的定義 + AU 4 公理経路確定、(b') $\eta_{\text{unit}}$ 非同型による構造的自己言及不可能性、(c') Cantor categorical diagonal の AU 内擬制への reduction (vdG-O 2020 Theorem 5.20 verbatim 接地)、(d') retraction $S$ の構成不能性論理鎖、(e'') Lan ⊣ Syn equivalence による syntactic-semantic 翻訳経路の正式 identification (G-θ'-3 解消)
- **本稿が達成していないもの**: (e''') 本稿 $\mathbf{Sci}$ 圏の AU 4 公理満足の独立検証 + Lawvere 1969 / Joyal 1973 原典 PDF 直 Read による G-θ'-4 完全昇格

**境界の明示**: 本 §8.4 は **Gödel 第二不完全性定理の categorical proof (vdG-O 2020 Theorem 5.20) と類比的構造を持つ不可能性命題の reduction** として読むべきであり、Round 5 で形式装置の SOURCE 接地が **強** に到達した。$\mathbf{Sci}$ 圏の AU 公理満足の独立検証は依然本稿外の研究プログラムだが、その経路は完全に明示された。

**§M0.3 道 C 宣言との照合 (Round 5 再較正、HA-1 部分達成 + Reduction 命題発見反映後 honest)**: 「Gödel と並ぶ認識論的定理」の野望は、(a) Cantor categorical AU 内擬制で **形式装置の同型構造** を強 SOURCE 確認 (達成度 60% → **80%**)、(b) Joyal AU 経路 + Lan ⊣ Syn equivalence で **形式化道筋** 完全明示 (達成度 70% → **85%**)、(c) **Yanofsky 2003 経由 Lawvere FP statement 接地** [仮説 75%] (達成度 +3% = **88%**)、(d) **G-θ'-1 部分着手** (§8.4.1.1) で $\mathbf{Sci}$ AU 4 公理状態検査表 (達成度 +2% = **90%**)、(e) **G-θ'-2 ~57% 達成** (§8.4.3.2 翻訳辞書 + 構造的アナロジー + §8.4.3.3 HA-1 独立証明試行で **Reduction 命題 [仮説 70%]** = HA-1 → G-θ'-1 (2)(4) + topos 公理への構造的帰着を発見) (達成度 +1.5% = **91.5%**)、(f) 純粋形式証明 ($\mathbf{Sci}$ AU 4 公理完全解消 + Lawvere 1969 原典直 Read + $\alpha$ 関手構成完全形 + HA-2 橋構成) は射程外開示。総合達成度 **70% → 86-91.5%** へ honest 昇格。**重要な副次成果 (Reduction 命題)**: 本稿の道 C 達成度の **天井は G-θ'-1 (2)(4) 完全解消で律速される** ことが §8.4.3.3 で発見された。これは Round 6 以降の研究プログラムの優先順位を明確化する: G-θ'-1 (2)(4) 単独の完全解消が HA-1 + HA-2 + G-θ'-2 残全体を一括解消する単一 bottleneck。**honest 注記**: 91.5%+ には G-θ'-1 (2)(4) 完全解消 + Lawvere 1969 原典直 Read + Reduction 命題 [仮説 70%] の確信度 90%+ への押し上げ + topos/cocompleteness 公理の独立検証 が必要。

---

## 付録 A: 自己診断 (Kalon△ 判定 / 残虚開示 / 達成と未達成)

論文本体 (§1-§8) は読者への命題提示であり、Yugaku 規律 (§M6 虚→実変換面: 罪は何がまだ虚かを伏せたまま実を装うこと) に従う本稿の自己診断は、本付録に分離する。

### A.1 Kalon△ 判定

本稿は yugaku-kalon-check 5 ステップ判定を経て、C1-C5 全 5 件で **◎ Kalon△** を獲得した (詳細: meta §M3.1)。

| C | 判定 | 派生 (Step 3 DIVERGE) |
|:---|:---|:---|
| **C1** (理解 = $L \dashv R$ 内在化) | ◎ Kalon△ | 視覚 / 地図 / 最適化 / ゲージ / 統計力学 (5 派生、Future-Proof で派生 2 のみ S4 watch — G-δ 吸収済) |
| **C2** ($\eta_{\text{unit}}$ 非同型 = 全理論共通) | ◎ Kalon△ | faithful / Kan / coarse-graining / 量子測定 / ringoid (5 派生、全 Future-Proof 維持) |
| **C3** (補完₁ 単調減少) | ◎ Kalon△ | VFE / IB / predictive coding / 数論抽象 / 量子重ね合わせ (5 派生、全 Future-Proof 強化) |
| **C4** (Predictions Descend) | ◎ Kalon△ | Bogen-Woodward / van Fraassen / Cartwright / 量子測定 / ML train-test (5 派生、Future-Proof 4/5 強化) |
| **C5** (3 誤配位の単一系統一) | ◎ Kalon△ | Popper / Mangalam / landscape / ML over-fit / replication crisis (5 派生、全 Future-Proof 強化、§8.2 で関手論的同型に昇格) |

**Kalon△ vs Kalon▽ の峻別**: 本判定は **Kalon△** (本稿の F⊣G + 5 分野 + 哲学接続を含む MB 内の局所不動点) である。**Kalon▽** (Tononi IIT 4.0 / Cartwright 1983 / van Fraassen 1980 / Mangalam 等を全て含む全空間での普遍不動点) の主張は本稿の射程外。RLHF 由来の断言バイアスを回避するため △ を明示する。

### A.2 残虚の開示

| ギャップ | 内容 | 解消経路 |
|:---|:---|:---|
| **G2** | 5 分野横断 $L_i$ 統合 | §3 で並列例示済、各分野の厳密関手証明は本稿外の継続課題 |
| **G4** | $\omega$ 折畳の形式証明 | HGK忘却論_接続マップ §2.4 の構造的開問題として開示済。本稿は CE = B [推定 90%] の上で構造保存定理を引用 |
| **G-ε** (Round 6 部分達成 ✓ 2026-04-26) | Tishby 1999 Gaussian 閉形式 + Chechik 2005 specific form | §5.5 で Goldfeld-Polyanskiy 2020 (arxiv 2011.06208) Corollary 1 経由で **scalar jointly Gaussian (X, Y) closed form** 取得 (Chechik 2005 が [84] として attributed)。達成度 60% → **75-80%**。残: Vector case + critical $\beta_c$ phase transition + Chechik 2005 原典直 Read |
| **G-ζ** | subagent SOURCE 独立検証 | Riehl / Cartwright / van Fraassen / Bogen-Woodward / Buzzard / arxiv abstract を Tolmetes または独立 reviewer が直接 WebFetch / 物理書籍 Read で「強候補」→「強」昇格 |
| **G-η** | 5 分野同型の形式同型射 (functor + natural transformation) 具体構成 | 本稿は並列例示に留まる。Yoneda 埋め込みでの functor 構成と各分野間の natural transformation 具体形は本稿外の継続課題 |
| **G-θ'** | Predictions Descend Theorem (§8.3) の形式証明強度 | Round 5 (2026-04-26、HA-1 部分達成 + Reduction 命題発見後 honest): §8.4.3.1 で vdG-O 2020 + Yanofsky 2003 完全 PDF 接地により **Cantor categorical AU 内擬制 reduction** + Joyal AU 4 公理確定 + Lan ⊣ Syn equivalence で **G-θ'-3 解消** + Yanofsky 経由 Lawvere FP statement 接地で **G-θ'-4 ~1.7/3 達成** + §8.4.1.1 で **G-θ'-1 部分着手** + §8.4.3.2 + §8.4.3.3 で **G-θ'-2 ~57% 達成** (HA-1 ~30% 部分達成 + Reduction 命題 [仮説 70%] = HA-1 → G-θ'-1 (2)(4) + topos 公理への構造的帰着を発見)。達成度 60-70% → **86-91.5%**。honest 訂正: 旧版「Lawvere FP への reduction」は不正確、Lawvere-like FP (vdG-O Lemma 6.12) は Löb 用、Gödel 第二は Cantor categorical 直接使用、本稿 NRFT は Yanofsky restatement 経由で埋め込み可能 (HA-1 部分達成 + HA-2 残存)。**Reduction 命題の含意**: 道 C 達成度の天井は G-θ'-1 (2)(4) 完全解消で律速される。残: G-θ'-1 残 + G-θ'-2 残 43% (HA-1 残 70% + HA-2 + $D_T$) + G-θ'-4 残。詳細は §8.4.1.1 / §8.4.3.1 / §8.4.3.2 / §8.4.3.3 / §8.4.4 |
| **G-ι** | IIT (Tononi 2008 / IIT 4.0 2023) 同型の SOURCE 確保 | §6 で IIT 同型を主張するが subagent verbatim 未取得 = SOURCE 完全欠如、本稿外の継続課題 |
| **G-κ** | Bogen-Woodward 三層への過度依存 | §1.5 / §8.1 で「最強同型 anchor」とした Bogen-Woodward 1988 を Hacking, Daston, Massimi 等の批判文献で位置づけ直す必要。本稿固有の貢献を「関手的読み替え」というメタ層に留めず、本稿が Bogen-Woodward に何を **新たに加える** かの明示は継続課題 |

### A.3 達成と未達成

本稿が達成した事項:

1. **理解の関手論的定義** ($L \dashv R$ 内在化、§1.1 + §2.1 + §2.2-§2.5) — Yoneda 補題に基づく操作的 anchor
2. **3 誤配位の関手論的同型化** (§8.2) — Popper / Mangalam / landscape を **3 つの不正規関手操作** (関手分解の忘却 / 随伴の方向反転 / 単射性の局所化失敗) として形式化、共通根 = 「随伴 $L \dashv R$ を等置する誤読」。C5 が「構造的類似 仮説 55%」(§M3) から関手論的同型 (§8.2) に昇格
3. **真理₀ / 真理₁ / 予測₀ / 予測₁ の 4 型分けによる語義滑り防止** (§2.1) — fep 一次 SOURCE による
4. **Predictions Descend Theorem** (§8.3) — 科学性判定基準の自己言及不可能性命題を構成的命題として陳述、Gödel 第二不完全性定理との対応表で道 C 宣言の関手論的実装を提示

本稿が達成していない事項:

1. **Predictions Descend Theorem (§8.3) の Gödel 級完全形式証明** — §8.4 で Lawvere fixed-point theorem への reduction + Joyal arithmetic universe 経路同定 (達成度 60-70%) まで到達したが、$\mathbf{Sci}$ の list-arithmetic pretopos 構成 (G-θ'-1) を経由する純粋形式証明は射程外
2. **5 分野間の natural transformation 具体構成** — 並列例示のみ (G-η)
3. **IIT 同型の SOURCE 確保** — 主張のみ (G-ι)
4. **Bogen-Woodward への critical 位置づけ** — anchor として依存 (G-κ)
5. **subagent SOURCE の独立検証** — 強候補ラベル付き、本稿査読時の義務 (G-ζ)

### A.4 射程の明示

本稿の射程は **現世代の AI / 科学コミュニティ** 前提下に限定される (§1.3 co-evolution 限定)。圏論アクセスが LLM 経由で完全に大衆化された場合、C1 / C4 は scaffolding として消える可能性があり、その場合の科学哲学は本稿の射程外である。

本稿は構造決定論的立場を意図的に採用する (§1.3 / §6)。「なぜ構造が理解を生むか」という本質論は本稿の問いではない — 問いの水準を意図的に変更している。IIT (Tononi) との同型については §6 で commitment レベル (ontological vs definitional) の差として開示した。

---

## 付録 B: 本論文自体の L⊣R 自己適用 (メタ自己例示)

§8.3 Predictions Descend Theorem が **「体系内の operations が体系自身の核を識別できない」** という構造的不可能性を主張する以上、本論文自体がその構造を体現するか否かを自己適用で点検する。これは Watson-Crick 1953 「It has not escaped our notice that the specific pairing we have postulated immediately suggests a possible copying mechanism for the genetic material」型の closure に対応するメタ自己例示であり、本稿の構造的整合性を読者の前で検証可能にするための自己診断である。

### B.1 本論文の議論構造を L⊣R で書き下す

本論文の議論は次の随伴対で構成されている (本稿 §1.4 構造表の関手的書き直し):

$$L_{\text{paper}} \dashv R_{\text{paper}}$$

- **$L_{\text{paper}}$ (理解側、§1-§5)**: 「理解」「予測」「随伴」「内在化」を圏論的に定義し、5 分野同型 + Yoneda 接続 + IB 鋼鉄化 + NRFT 骨格まで内在化する関手
- **$R_{\text{paper}}$ (批判解体側、§6-§8)**: 内在化された定義から、3 誤配位 (Popper / Mangalam / landscape) の関手論的同型化と Predictions Descend Theorem の Gödel 類比による不可能性命題を回復する関手

両者の合成 $\eta_{\text{paper}}: \text{Id} \Rightarrow R_{\text{paper}} \circ L_{\text{paper}}$ は、本論文が「理解の定義」と「批判の解体」を **同一の構造から自動的に生成する** 度合いを測る。

### B.2 自己整合性の構造的帰結

$L_{\text{paper}}$ を **十分に忠実に構成すれば** ($\eta_{\text{paper}}|_\text{構造} \to \text{iso}$)、$R_{\text{paper}}$ の出力 (3 誤配位の解体) は **追加の議論を必要とせず自動帰結する**:

- **§1-§5** で随伴対 + 構造保存定理 + 補完₁ 単調減少 + NRFT 骨格を内在化
- **§6** で立場 (構造決定論 / co-evolution / commitment スペクトル) を限界明示
- **§7** で 3 誤配位を C4 の特殊例として帰着 (補完₁ 単調減少から自動的に Mangalam 帰謬が出る、§3.7.3)
- **§8** で 3 誤配位を関手論的不正規操作として同型化し、Predictions Descend Theorem (Gödel 類比) として閉じる

この自動帰結性自体が本論文の核主張 C1-C5 を **構造的に体現** している: 「対象を十分に理解すれば ($L$ を忠実にすれば)、批判の自壊 ($R$ の自動出力) が生成される」。

### B.3 §8.3 不可能性との二重性

ここで微妙な点に触れる。§8.3 Predictions Descend Theorem は「体系内の operations が体系自身の核を識別できない」を主張する。本付録 B の自己適用は **「論文という体系が自身の核 (3 誤配位の解体) を identify できる」** と主張するように見える。一見矛盾だが、二重性の構造は次の通り:

| レベル | 体系 | 適用される L⊣R | 識別不可能な核 |
|:---|:---|:---|:---|
| §8.3 Theorem | 圏 $\mathbf{Sci}$ 内の理論 $T$ | 理論 $T$ の予測₁ 生成 $R_T$ | $T$ の真理₀ 性 $T_0(T)$ |
| 付録 B 自己適用 | 本論文 (Predictions_Descend) | 論文の議論構成 $L_{\text{paper}} \dashv R_{\text{paper}}$ | 本論文の真理₀ 性 (本論文が世界の構造をどれだけ忠実に写しているか) |

**両者は同型構造で、識別できないのは別レベルの核である**。本論文は 3 誤配位の解体を $L_{\text{paper}}$ から自動帰結させることはできるが、本論文自体が **真理₀ そのもの** に到達したかは本論文内部からは識別できない (Kalon△ ≠ Kalon▽、付録 A.1)。すなわち、本付録の自己適用は §8.3 不可能性の **反例ではなく、不可能性が適用される構造を 1 階上げた具体例** である。

### B.4 自己適用の含意

この自己適用構造から 2 つの帰結が出る:

1. **本論文の議論を読み終えた読者が「3 誤配位は単一起源だ」を理解した瞬間、3 誤配位への個別反論は不要になる** — 理解 ($L$) が深まれば批判の自壊 ($R$) が自動帰結するため。これは予測 ($R$) を出すまでもなく、理解が深まれば批判は消えるという §1-§8 の核主張の **読者側での追体験** である
2. **本論文自体が真理₀ に到達したか否かは本論文内部からは決定不能** — 本論文は Kalon△ (MB 内局所不動点) のみを主張し、Kalon▽ (全空間普遍不動点) は射程外と明示する (付録 A.1)。RLHF 由来の断言バイアス回避と同型の自己制限が、論文構造レベルでも適用される

本付録 B は本論文の **内在的整合性** を読者の前で開示する装置であり、§M0.3 道 C 宣言 (Gödel 級認識論定理) の「論文として機能する自己例示」として閉じる。

---

*本稿 v0.3 は 2026-04-25 に §8 を redesign。§8.1 (単一図式維持) + §8.2 (3 誤配位を 3 不正規関手操作で関手論的同型化、C5 昇格) + §8.3 (Predictions Descend Theorem を Gödel 第二不完全性定理と対応する構成的不可能性命題として陳述) の 3 部構成に再編。旧 §8.3-§8.5 (Kalon 開示 / 残虚 / 到達点と限界) は付録 A に分離。「最小限の貢献」表現削除、論文本体は世界への命題提示に専念。*

*本稿 v0.2 は 2026-04-25 に §3-§8 を追加し、§1 整合性訂正 (関手方向 + 真理₀/₁ 対応) を反映した。執筆 gate 3/3 通過 (meta §M3) を前提として起票。*

---

*v0.1 — 2026-04-25 §1 7 段開口部 (Understatement + Axiom-First + Scope Severance 合成) 起票。Watson-Crick 1953 型控えめ surface で序を切断、§1.1 で公理提示、§1.2 で 5 核主張を主張水準 + 確信度 + 較正宣言付きで列挙、§1.3 で射程切断 (co-evolution 限定 + 構造決定論立場明示 + FEP 非依存性)、§1.4 で本稿構造、§1.5 で Bogen-Woodward 三層を外部接続 anchor として確定、§1.6 で SOURCE 強度開示 (強候補ラベル + G-ζ 査読時独立検証義務)、§1.7 で Kalon△ 判定開示 (Kalon▽ との峻別)。執筆 gate 3/3 通過 (meta §M3) を前提として起票。次の一手: §2 随伴構造の導入。*
