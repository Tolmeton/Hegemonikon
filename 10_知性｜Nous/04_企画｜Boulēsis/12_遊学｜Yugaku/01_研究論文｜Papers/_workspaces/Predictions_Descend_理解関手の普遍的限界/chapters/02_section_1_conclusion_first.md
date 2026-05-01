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

