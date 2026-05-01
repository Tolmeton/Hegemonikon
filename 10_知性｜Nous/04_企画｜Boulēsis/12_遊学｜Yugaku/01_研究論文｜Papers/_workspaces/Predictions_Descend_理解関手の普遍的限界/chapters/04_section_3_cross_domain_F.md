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

