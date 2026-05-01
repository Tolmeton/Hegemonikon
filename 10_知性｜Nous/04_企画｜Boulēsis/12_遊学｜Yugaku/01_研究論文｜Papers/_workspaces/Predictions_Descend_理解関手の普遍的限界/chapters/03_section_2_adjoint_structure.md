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

