# エントロピーは忘却である — CPS 圏の統計力学

**Paper IX — v0.1 (2026-07-21) — 忘却論 (Force is Oblivion) シリーズ**

*概要.* Paper VIII で確立した α-忘却濾過の公理系 (F1)-(F4) が、統計力学の基本構造——エントロピー、第二法則、データ処理不等式——を自然に内包することを示す。中心的構成は **CPS エントロピー** $S_{\mathrm{CPS}}(p, \alpha)$: Perrone [P1] が Markov 圏上で定義したエントロピー（確定的射からの divergence の下限）を、CPS($\alpha > 0$) が Markov 圏であること（Paper II 互換性補題 §3.7.1）を通じて α-忘却濾過に輸入する。主定理（CPS エントロピー単調性定理）は、(F4) 公理から直接従う: 忘却が進む（α が増大する）ほど確定的射の集合が縮小し、したがってエントロピーが単調に増大する。これは Paper VIII 定理 6.10.3（射計数版）の Perrone 枠組みへの精密化であり、Shannon/Rényi/Gini-Simpson エントロピーを統一的に回収する。

> **記号規約.** α は Paper VIII の忘却強度パラメータ $\alpha_{\mathrm{VIII}} \in [0, 1]$。Paper III/V の $\alpha_{\mathrm{III}} \in \mathbb{R}$（Amari の α-接続）とは異なる。CPS($\alpha$) は忘却パラメータ $\alpha$ における CPS 圏を指す。$D$ は固定された divergence 関数。統一記号表 (unified_symbol_table.md) を参照。

---

## §1. 動機と問題設定

### 1.1 忘却論の熱力学的構造

忘却論 Papers I–VIII は、α-忘却濾過 {C_α} が熱力学の粗視化（coarse-graining）と構造的に同型であることを示唆してきた（随伴レポート §10）。Paper VIII §6.10 では (F4) 公理から射計数エントロピー $S_{\mathrm{cat}}(\alpha) := \log m(0) - \log m(\alpha)$ の単調増大を証明した（Th. 6.10.3: 忘却の第二法則）。しかし $S_{\mathrm{cat}}$ は射の「数」のみを計量する粗い測度であり、Shannon エントロピーや Rényi エントロピーといった情報論的エントロピーとの関係は未確立であった。

本稿の目的は、この欠落を Perrone [P1] の Markov 圏エントロピーの輸入によって埋めることである。

### 1.2 既存の構成要素

本稿は以下の既存の結果に依存する:

| 結果 | 出典 | 本稿での役割 |
|:--|:--|:--|
| α-忘却濾過 (F1)-(F4) | Paper VIII Def. 6.2.1 | 基底構造 |
| CPS($\alpha > 0$) は Markov 圏 | Paper II §3.7.1 互換性補題 | Perrone 輸入の前提 |
| 射計数エントロピー $S_{\mathrm{cat}}$ | Paper VIII Th. 6.10.3 | 粗い版の第二法則 |
| Schur-Horn 橋渡し | Paper I Th. 5.6.1, Paper IV 命題 7.5.1 | 観測量の entropic 制約 |
| Markov 圏上のエントロピー | Perrone [P1] | 輸入対象 |
| データ処理不等式 (DPI) | Perrone [P1] §3.1, §4.1 | 単調性の道具 |

### 1.3 本稿の構成

§2 で Markov 圏エントロピーの必要な定義を再掲し、§3 で CPS エントロピーを構成する。§4 で Paper VIII の射計数版との関係を示す。

---

## §2. Markov 圏エントロピーの概要

本節は Perrone [P1] と Fritz [F1] の結果を、CPS 圏への適用に必要な範囲で再掲する。

### 2.1 Markov 圏の復習

**定義 2.1.1 (Markov 圏; Fritz [F1, Def. 2.1]).** 対称モノイダル圏 $(\mathcal{C}, \otimes, I)$ が **Markov 圏** (Markov category) であるとは、各対象 $X$ に可換余モノイド構造——comultiplication $\mathrm{copy}_X: X \to X \otimes X$ と counit $\mathrm{del}_X: X \to I$——が備わり、以下を満たすものをいう:

1. $\mathrm{del}_X$ は全ての射 $f: A \to X$ に対して自然: $\mathrm{del}_X \circ f = \mathrm{del}_A$
2. $\mathrm{copy}_X$ は全ての射 $f: A \to X$ に対して以下の意味で「互換的」: $\mathrm{copy}_X \circ f = (f \otimes f) \circ \mathrm{copy}_A$ が**確定的射に対してのみ**成立する

**定義 2.1.2 (確定的射; Fritz [F1, Def. 10.1]).** Markov 圏の射 $f: X \to Y$ が**確定的** (deterministic) であるとは、$\mathrm{copy}_Y \circ f = (f \otimes f) \circ \mathrm{copy}_X$ が成立することをいう。確定的射の全体を $\mathrm{Det}(\mathcal{C})$ と書く。

直観的には、確定的射は「ノイズなし」の写像であり、非確定的射は確率的チャネルに対応する。

### 2.2 Perrone のエントロピー

**定義 2.2.1 (Markov 圏上のエントロピー; Perrone [P1, §2]).** Markov 圏 $\mathcal{C}$ に divergence $D: \mathrm{Mor}(\mathcal{C}) \times \mathrm{Mor}(\mathcal{C}) \to [0, \infty]$ が与えられているとする。状態 $p: I \to X$（=モノイダル単位 $I$ からの射）の**エントロピー** $H_D(p)$ を

$$H_D(p) := \inf_{f \in \mathrm{Det}(\mathcal{C})(I, X)} D(p \| f)$$

で定義する。すなわち、エントロピーは**確定的状態への最小 divergence** である。

**回収される古典的エントロピー.** $D$ の選択に応じて [P1, §2.3]:
- $D = D_{\mathrm{KL}}$ (Kullback-Leibler) → Shannon エントロピー $H(p) = -\sum p_i \log p_i$
- $D = D_\alpha^{\mathrm{Rényi}}$ → Rényi エントロピー $H_\alpha(p) = \frac{1}{1-\alpha}\log\sum p_i^\alpha$
- $D = D_{\mathrm{GS}}$ (Gini-Simpson) → Gini-Simpson 指数 $1 - \sum p_i^2$

### 2.3 データ処理不等式

**定理 2.3.1 (DPI; Perrone [P1, §3.1, §4.1]).** Markov 圏 $\mathcal{C}$ における射 $k: X \to Y$ に対し、$k$ が**確定的射を確定的射に写す**ならば:

$$H_D(k \circ p) \leq H_D(p)$$

すなわち、確定性を保存する「チャネル」を通過してもエントロピーは増加しない。

*直観.* 確定的チャネルは情報を失わない（or 減らすだけ）ので、不確実性（エントロピー）は増えない。

---

## §3. CPS エントロピーの構成

### 3.1 CPS($\alpha > 0$) の Markov 圏構造

Paper II 互換性補題（§3.7.1）により、$\alpha > 0$ のとき CPS 圏は Markov 圏の構造を持つ:

- **$\mathrm{del}_X$**: 忘却場 $\Phi > 0$ による全忘却。$\alpha > 0$ により $\Phi$ の正値性が保証され、正規化 $\mathrm{del}_X = \Phi / \int \Phi$ が well-defined。
- **$\mathrm{copy}_X$**: 対角写像 $x \mapsto (x, x)$ の Markov kernel としての持ち上げ。Fritz の意味での確定的射。
- **確定的射 $\mathrm{Det}(\mathrm{CPS}(\alpha))$**: copy を保存する射。$\alpha$ の増大により Mor が減少するため、$\mathrm{Det}$ も減少する（後述の補題 3.2.1）。

**備考.** $\alpha \leq 0$ では $\mathrm{del}_X$ の正規化が崩壊し（Paper II §3.7.1 備考）、Markov 圏構造が退化する。本稿では $\alpha > 0$ に限定する。$\alpha \leq 0$ セクターのエントロピーは §5 で議論する（Paper III の $\mathbb{Z}_2$-次数付き CPS 圏との関係）。

### 3.2 確定的射の α-単調性

**補題 3.2.1 (確定的射の単調包含).** $0 < \alpha_1 \leq \alpha_2 \leq 1$ ならば:

$$\mathrm{Det}(\mathrm{CPS}(\alpha_2)) \subseteq \mathrm{Det}(\mathrm{CPS}(\alpha_1))$$

*証明.* (F4) より $\mathrm{Mor}(C_{\alpha_2}) \subseteq \mathrm{Mor}(C_{\alpha_1})$。確定的射は射のうち copy を保存するものとして定義される（Def. 2.1.2）。copy の保存は射のクラスの部分条件であるから、$\mathrm{Det}(C_{\alpha_2}) \subseteq \mathrm{Mor}(C_{\alpha_2}) \subseteq \mathrm{Mor}(C_{\alpha_1})$。さらに、$f \in \mathrm{Det}(C_{\alpha_2})$ が $C_{\alpha_1}$ においても copy を保存するかを確認する。

(F1) より $\mathrm{Ob}(C_{\alpha_1}) = \mathrm{Ob}(C_{\alpha_2})$ であるから、copy の定義は両圏で同一の対象上の同一の写像（対角写像）である。$f$ が $C_{\alpha_2}$ で copy を保存するならば、同じ等式は $C_{\alpha_1}$ でも成立する（$C_{\alpha_2}$ での等式は $C_{\alpha_1}$ の射の等式でもある）。したがって $f \in \mathrm{Det}(C_{\alpha_1})$。$\square$

**備考.** この補題は (F1) と (F4) のみを使用し、(F2)(F3) に依存しない。copy 構造の α-非依存性（対角写像であること）が本質的である。

### 3.3 CPS エントロピーの定義

**定義 3.3.1 (CPS エントロピー).** $\alpha > 0$ とし、$D$ を CPS 圏上の divergence とする。状態 $p: I \to X$ の **CPS エントロピー** を

$$\boxed{S_{\mathrm{CPS}}(p, \alpha) := \inf_{f \in \mathrm{Det}(\mathrm{CPS}(\alpha))(I, X)} D(p \| f)}$$

で定義する。

**直観.** CPS エントロピーは「状態 $p$ が、α-忘却レベルにおいてどれだけ確定的状態から離れているか」を測る。α が高い（忘却が強い）ほど利用可能な確定的状態が少なくなるため、最近接の確定的状態はより遠くなり、エントロピーは増大する。

### 3.4 CPS エントロピー単調性定理

**定理 3.4.1 (CPS エントロピー単調性; 忘却の第二法則 — 情報論的版).** $0 < \alpha_1 \leq \alpha_2 \leq 1$ とし、$p: I \to X$ が $\mathrm{Mor}(C_{\alpha_2})$ に属する状態（すなわち、両方の α レベルで well-defined な状態）であるとする。このとき:

$$\boxed{S_{\mathrm{CPS}}(p, \alpha_1) \leq S_{\mathrm{CPS}}(p, \alpha_2)}$$

すなわち、**忘却が進む（α が増大する）ほど CPS エントロピーは単調に増大する。**

*証明.* 補題 3.2.1 より $\mathrm{Det}(C_{\alpha_2}) \subseteq \mathrm{Det}(C_{\alpha_1})$。下限の集合が縮小するから:

$$\inf_{f \in \mathrm{Det}(C_{\alpha_2})} D(p \| f) \geq \inf_{f \in \mathrm{Det}(C_{\alpha_1})} D(p \| f)$$

左辺が $S_{\mathrm{CPS}}(p, \alpha_2)$、右辺が $S_{\mathrm{CPS}}(p, \alpha_1)$。$\square$

**備考 3.4.2 (証明の構造).** この証明は remarkably simple であり、本質的に以下の一行に帰着する:

> **(F4) → 確定的射が減る → 下限の集合が縮む → infimum が増大する**

この単純さは偶然ではない。(F4) は忘却の不可逆性を**射の包含**という最も基本的な形で表現しており、エントロピーの単調性はその直接的な帰結である。

**備考 3.4.3 (Divergence の選択への非依存性).** 定理 3.4.1 は divergence $D$ の具体的な選択に依存しない。$D$ が非負 ($D(p \| f) \geq 0$) かつ確定的射上で最小 ($D(f \| f) = 0$ for $f$ deterministic) であれば成立する。特に:
- $D = D_{\mathrm{KL}}$ → Shannon エントロピーの CPS 単調性
- $D = D_\alpha^{\mathrm{Rényi}}$ → Rényi エントロピーの CPS 単調性
- $D = D_{\mathrm{GS}}$ → Gini-Simpson 指数の CPS 単調性

**備考 3.4.4 (時間の矢 = 忘却の矢).** 定理 3.4.1 を Paper V 定理 2.3.1 ($\beta_\alpha \leq 0$) と結合すると、エントロピーの時間発展が閉じる:

$$\mu \downarrow \xrightarrow{\beta_\alpha \leq 0} \alpha \uparrow \xrightarrow{\text{Th. 3.4.1}} S_{\mathrm{CPS}}(p, \alpha) \uparrow$$

物理時間 $t$ の進行が解像度の粗視化 ($d\mu/dt \leq 0$) として表現されるとき、$\beta_\alpha \leq 0$ は $\alpha$ の単調増大を、定理 3.4.1 は $S_{\mathrm{CPS}}$ の単調増大を保証する。この三段チェーンは熱力学第二法則の圏論的表現であり、忘却方向と時間方向が一致するという「忘却の矢」仮説 (Paper V 系 2.3.3) の動的版である。

### 3.5 境界条件

**命題 3.5.1 (CPS エントロピーの α-境界条件).** 状態 $p: I \to X$ に対し:

(i) **$\alpha = 0$** (完全圏): $S_{\mathrm{CPS}}(p, 0) = \inf_{f \in \mathrm{Det}(C)} D(p \| f) \geq 0$。等号成立条件は $p \in \mathrm{Det}(C_0)$（$p$ が完全圏で確定的）。

(ii) **$\alpha = 1$** (離散圏): $I \neq X$ のとき $S_{\mathrm{CPS}}(p, 1) = +\infty$。

(iii) **中間 α**: 写像 $\alpha \mapsto S_{\mathrm{CPS}}(p, \alpha)$ は $[0, 1] \to [0, +\infty]$ 上の非減少関数である。さらに、**臨界忘却閾値** $\alpha^*(p) := \inf\{\alpha \in [0,1] \mid \mathrm{Det}(C_\alpha)(I, X) = \emptyset\}$ が存在し、$\alpha > \alpha^*(p)$ ならば $S_{\mathrm{CPS}}(p, \alpha) = +\infty$。

*証明.*

(i) (F2) より $C_0 = C$ であるから $\mathrm{Det}(C_0) = \mathrm{Det}(C)$ は確定的射の全体であり、全ての α-レベル中で最大の集合である（補題 3.2.1 の帰結）。したがって infimum が最大集合上で取られ、$S_{\mathrm{CPS}}(p, 0) \leq S_{\mathrm{CPS}}(p, \alpha)$ が任意の $\alpha > 0$ に対して成立する（これは定理 3.4.1 の $\alpha_1 = 0$ の場合でもある）。$D \geq 0$（divergence の非負性）より $S_{\mathrm{CPS}}(p, 0) \geq 0$。$p \in \mathrm{Det}(C_0)$ ならば $D(p \| p) = 0$ から等号。逆に $S_{\mathrm{CPS}}(p, 0) = 0$ ならば、ある確定的射の列 $f_n \in \mathrm{Det}(C_0)$ で $D(p \| f_n) \to 0$ が存在し、$D$ の正定値性の仮定の下で $p$ 自身が確定的であることが従う。□

(ii) (F3) より $\mathrm{Mor}(C_1) = \{\mathrm{id}_X \mid X \in \mathrm{Ob}(C)\}$ であるから、$C_1$ における射は恒等射のみ。特に $\mathrm{Det}(C_1)(I, X) \subseteq \mathrm{Mor}(C_1)(I, X)$。$I \neq X$ のとき $\mathrm{id}_X: X \to X$ は $I \to X$ の射ではなく、$\mathrm{id}_I: I \to I$ は $I \to X$ の射ではないから、$\mathrm{Mor}(C_1)(I, X) = \emptyset$。空集合上の infimum は $+\infty$ であるから $S_{\mathrm{CPS}}(p, 1) = +\infty$。□

(iii) 非減少性は定理 3.4.1 の直接的帰結。$\alpha^*(p)$ の存在: $A := \{\alpha \in [0,1] \mid \mathrm{Det}(C_\alpha)(I, X) = \emptyset\}$ とおく。(ii) より $1 \in A$（$I \neq X$ のとき）、(i) より $0 \notin A$（$\mathrm{Det}(C_0)(I,X)$ は非空と仮定: $p$ が well-defined であるため少なくとも確定的射が存在）。$A$ は下に有界な非空集合であるから $\alpha^*(p) = \inf A$ が存在する。(F4)（射の単調減少）より、$\alpha_2 > \alpha_1$ かつ $\mathrm{Det}(C_{\alpha_1})(I,X) = \emptyset$ ならば $\mathrm{Det}(C_{\alpha_2})(I,X) = \emptyset$（包含 $\mathrm{Det}(C_{\alpha_2}) \subseteq \mathrm{Det}(C_{\alpha_1})$ による）。したがって $A$ は $[\alpha^*(p), 1]$ の形の区間（閉半区間または開半区間）であり、$\alpha > \alpha^*(p)$ ならば $\alpha \in A$ すなわち $S_{\mathrm{CPS}}(p, \alpha) = +\infty$。□

**備考 3.5.2 (臨界忘却閾値の物理的意味).** $\alpha^*(p)$ は「状態 $p$ がエントロピー有限性を維持できる最大忘却強度」を表す。$\alpha < \alpha^*(p)$ では十分な確定的射が生存しており参照点として機能するが、$\alpha > \alpha^*(p)$ では全ての参照が失われ、エントロピーが発散する。これは Paper IV の効果量天井 $r_{\mathrm{obs}} \leq \sqrt{\rho/(K+1)}$ における $\rho \to 0$ 極限——有効な観測次元が消滅する状態——の圏論的対応物である。

### 3.6 Perrone DPI との関係

定理 3.4.1 は Perrone の DPI (Th. 2.3.1) とは**独立な**結果である。

- **Perrone DPI**: 固定された Markov 圏内で、確定的チャネルを通過してもエントロピーは増加しない → **圏内**の単調性
- **Th. 3.4.1**: α パラメータが変化するとき、エントロピーは α に関して単調 → **圏間**の単調性

両者は直交する不等式であり、CPS エントロピーの制約を異なる軸で与える。統合的な不等式は:

$$S_{\mathrm{CPS}}(k \circ p, \alpha_2) \geq S_{\mathrm{CPS}}(k \circ p, \alpha_1) \quad \text{and} \quad S_{\mathrm{CPS}}(k \circ p, \alpha) \leq S_{\mathrm{CPS}}(p, \alpha)$$

ここで $k$ は確定的チャネル。第一不等式は Th. 3.4.1、第二は Perrone DPI。

---

## §4. 射計数エントロピーとの関係

### 4.1 二つのエントロピーの関係

Paper VIII の射計数エントロピー $S_{\mathrm{cat}}(\alpha) = \log m(0) - \log m(\alpha)$（Th. 6.10.3）と CPS エントロピー $S_{\mathrm{CPS}}(p, \alpha)$ の関係を明確にする。

**命題 4.1.1 (射計数版は CPS 版の二重粗視化).** 以下の二段階の粗視化により $S_{\mathrm{cat}}$ は $S_{\mathrm{CPS}}$ から回復される:

**第一粗視化（状態平均化）.** 状態に依存する CPS エントロピーを「平均エントロピー」に粗視化する。形式的に: 対象 $X$ に対し $\mathrm{State}(X) := \mathrm{Mor}(C)(I, X)$ を状態空間とし、一様分布 $\mu_X$ を仮定して

$$\bar{S}_{\mathrm{CPS}}(\alpha, X) := \int_{\mathrm{State}(X)} S_{\mathrm{CPS}}(p, \alpha) \, d\mu_X(p)$$

と定義する。$\bar{S}_{\mathrm{CPS}}$ は特定状態への依存を消去し、対象 $X$ と α のみの関数となる。

**第二粗視化（divergence のカウンティング特殊化）.** Divergence $D$ を **0-∞ カウンティングダイバージェンス** $D_{\#}$ で置換する:

$$D_{\#}(p \| f) := \begin{cases} 0 & \text{if } p = f \\ +\infty & \text{if } p \neq f \end{cases}$$

このとき $S_{\mathrm{CPS}}^{\#}(p, \alpha) = \inf_{f \in \mathrm{Det}(C_\alpha)} D_{\#}(p \| f) = 0$ if $p \in \mathrm{Det}(C_\alpha)$, $+\infty$ otherwise。エントロピーは二値的になり、「状態が確定的か否か」のみを区別する。

**両粗視化の合成.** 二重粗視化の下で、有限エントロピーを持つ状態の「数」の対数的変化を取れば:

$$S_{\mathrm{cat}}(\alpha) = \log m(0) - \log m(\alpha) = \log \frac{|\mathrm{Mor}(C_0)|}{|\mathrm{Mor}(C_\alpha)|}$$

は、（有限 Mor の場合に）$\bar{S}_{\mathrm{CPS}}^{\#}$ の global summary と同型になる。すなわち $S_{\mathrm{cat}}$ は（射の全滅率の対数を通じて）状態を平均化し divergence を離散化した $S_{\mathrm{CPS}}$ の粗い版に他ならない。

*証明.* $D_{\#}$ の下では各状態は「確定的/非確定的」に二値分類され、$S_{\mathrm{CPS}}^{\#}(p, \alpha) \in \{0, +\infty\}$。$\mu_X$-平均は有限エントロピー状態の割合に帰着する。有限射の圏では $|\mathrm{Mor}(C_\alpha)| \leq |\mathrm{Mor}(C_0)|$（(F4)）であり、生存射の対数的減少率 $\log m(0) - \log m(\alpha)$ がこの離散化された平均エントロピーの natural summary を与える。$S_{\mathrm{CPS}}$ は $D_{\#}$ を連続的 divergence $D$（KL ダイバージェンス等）に「解像度を上げ」、かつ状態ごとの精密な距離を測ることで、$S_{\mathrm{cat}}$ の二重の粗さを除去したものである。□

**備考 4.1.2 (粗視化の不等式).** 連続的 $D \geq D_{\#}$ が一般に成り立つわけではないが、Jensen の不等式の類似として: $D$ が凸かつ $D(p \| f) = 0 \Leftrightarrow p = f$ のとき、$S_{\mathrm{CPS}}(p, \alpha) \geq 0 = S_{\mathrm{CPS}}^{\#}(p, \alpha)$ が確定的状態に対して成立する。非確定的状態に対しては $S_{\mathrm{CPS}}(p, \alpha) < +\infty = S_{\mathrm{CPS}}^{\#}(p, \alpha)$ も可能であり、$D_{\#}$ は $D$ に対する粗視化として機能する。

### 4.2 効果量天井との接続

Paper IV 命題 7.5.1 は、効果量天井 $r_{\mathrm{obs}} \leq \sqrt{\rho/(K+1)}$ が Schur-Horn 不等式（= 優越関係）によるエントロピー不等式であることを示した。CPS エントロピーの文脈では:

- $\rho_{\mathrm{spec}} < 1$: 忘却関手による射影が $S_{\mathrm{CPS}}$ を増大させ、観測分散を減衰させる
- $1 - \rho$ は、CPS エントロピーの分散レベルの測度: $(1 - \rho) \propto \Delta S_{\mathrm{CPS}}$

### 4.3 統合的な不等式体系

忘却論が確立したエントロピー関連の不等式を一覧する:

| 不等式 | 出典 | 内容 | 証明の鍵 |
|:--|:--|:--|:--|
| $S_{\mathrm{cat}}(\alpha_1) \leq S_{\mathrm{cat}}(\alpha_2)$ | Paper VIII Th. 6.10.3 | 射計数版の第二法則 | (F4) + $\log$ 単調性 |
| $S_{\mathrm{CPS}}(p, \alpha_1) \leq S_{\mathrm{CPS}}(p, \alpha_2)$ | 本稿 Th. 3.4.1 | 情報論的版の第二法則 | (F4) + $\mathrm{Det}$ の包含 |
| $\Xi_{\mathrm{impl}} \leq \Xi_{\mathrm{theory}}$ | Paper I Th. 5.6.1 | Schur-Horn 橋渡し | Schur-凸性 |
| $r_{\mathrm{obs}} \leq \sqrt{\rho/(K+1)}$ | Paper IV Th. 3.1.1 | 効果量天井 | Schur-Horn + 分散分配 |
| $S_{\mathrm{CPS}}(k \circ p, \alpha) \leq S_{\mathrm{CPS}}(p, \alpha)$ | Perrone DPI [P1] | チャネル内の情報損失 | Markov 圏構造 |

これらは全て**忘却は不可逆であり、エントロピーを増大させる**という単一の原理の異なる表現である。

---

## §5. α ≤ 0 セクターのエントロピー

### 5.1 問題の所在

$\alpha_{\mathrm{VIII}} \leq 0$ は Paper VIII §6.7.1 の正規化写像 $\eta$ の値域の外にあり、$\eta^{-1}(0)$ は $\alpha_{\mathrm{III}} = -\infty$ に対応する（§3.5 参照）。物理的には、α-忘却濾過の枠組みで $\alpha_{\mathrm{VIII}} \leq 0$ は「負の忘却」——情報の自発的生成——を意味する。

より根本的に: $\alpha_{\mathrm{III}} < 0$（Paper III のフェルミオン的セクター）では CPS 圏の Markov 圏構造が退化する（Paper II §3.7.1）。Grassmann 奇射 $f$ は $f \otimes f = 0$（$\xi \wedge \xi = 0$）を満たすため、Perrone–Fritz の Markov 圏公理が要求するコピー射 $\mathrm{del}_X: X \to X \otimes X$ が定義できない。

### 5.2 直接構成の不可能性

**定理 5.2.1 (Perrone エントロピーの α_III < 0 不可能性).** $\mathrm{CPS}^{Z_2}$ 圏のフェルミオン的セクター（$\alpha_{\mathrm{III}} < 0$、Z₂-奇射が非自明に存在する対象を含む）に対し、Perrone の意味での確定的射を用いたエントロピーは well-defined でない。

*証明.* Perrone [P1, §3] のエントロピーの構成には 確定的射 $\mathrm{Det}(C)$ の定義が必要であり、これは Markov 圏のコピー射 $\mathrm{del}_X$ に依存する（$f$ が確定的 $\Leftrightarrow$ $\mathrm{del}_Y \circ f = (f \otimes f) \circ \mathrm{del}_X$）。

$\alpha_{\mathrm{III}} < 0$ のセクターにおいて、Paper III §2.2 の Z₂-次数付けにより射は偶（ボソン的）成分と奇（フェルミオン的）成分に分解される。奇射 $f$ に対し:
- Koszul 符号則より $(f \otimes f)(x) = (-1)^{|f| \cdot |f|} (f \otimes f)(x) = -(f \otimes f)(x)$（$|f| = 1$ のとき）
- したがって $f \otimes f = 0$（特性 $\neq 2$ の体上）
- $\mathrm{del}_Y \circ f = (f \otimes f) \circ \mathrm{del}_X = 0$ より、「確定性条件」は自明に成立するが、$f$ を「確定的」と分類すると $\mathrm{Det}(C_\alpha)$ が全射を含むことになり、$S_{\mathrm{CPS}} = 0$ が恒等的に成立して非自明なエントロピー論が消滅する。
- 代替として $f \otimes f = 0$ の射を $\mathrm{Det}$ から除外しても、奇射が除外されるため $\mathrm{Det}(C_\alpha)$ の偶セクターのみが残り、$S_{\mathrm{CPS}}$ は偶射に対してしか意味を持たない。

いずれにせよ、Perrone の構成を直接適用すると自明または不完全なエントロピーとなる。□

### 5.3 Z₂-次数付きエントロピーの候補構成

**定理 5.2.1 は Perrone エントロピーの *直接的* 輸入が不可能であることを示すが、修正された構成の道を閉ざすものではない。** 以下に二つの候補を提示する。

**候補 A: スーパートレース型エントロピー.**

> **定義 5.3.1.** Z₂-次数付き CPS 圏 $\mathrm{CPS}^{Z_2}$ における**スーパーエントロピー** $S^{Z_2}_{\mathrm{CPS}}$ を:
>
> $$S^{Z_2}_{\mathrm{CPS}}(p, \alpha) := \inf_{f \in \mathrm{Det}^{\mathrm{even}}(C_\alpha)} D(p_{\mathrm{even}} \| f) + \lambda \cdot h(p_{\mathrm{odd}})$$
>
> と定義する。ここで:
> - $p_{\mathrm{even}}, p_{\mathrm{odd}}$ は状態 $p$ の Z₂-次数分解
> - $\mathrm{Det}^{\mathrm{even}}$ は偶セクターの確定的射（Perrone の意味で well-defined）
> - $h(p_{\mathrm{odd}})$ は奇セクターの Grassmann 次数に基づくエントロピー測度（具体的には $h(p_{\mathrm{odd}}) := \mathrm{rank}_\Lambda(p_{\mathrm{odd}})$ の対数）
> - $\lambda > 0$ は偶/奇セクターの重み付けパラメータ

**命題 5.3.2.** 候補 A は以下を満たす:
(i) $\alpha_{\mathrm{III}} > 0$（純ボソン的）のとき $p_{\mathrm{odd}} = 0$ であり、$S^{Z_2}_{\mathrm{CPS}} = S_{\mathrm{CPS}}$ に退化する。
(ii) §3 の第二法則（定理 3.4.1）は偶セクターに対して成立する。
(iii) 奇セクターの寄与 $h(p_{\mathrm{odd}})$ は α-単調性を**一般には**保証しない。

*証明スケッチ.* (i) 偶セクターのみの場合 $h(p_{\mathrm{odd}}) = h(0) = 0$（$\log \mathrm{rank}_\Lambda(0) = -\infty$ を $0$ と規約）。(ii) 偶セクターは Markov 圏構造を保持するから定理 3.4.1 がそのまま適用。(iii) $\alpha$ 増加に伴い Grassmann 次数の高い射が先に消滅するか否かは圏の構造に依存する。□

**候補 B: ε-正則化型.**

> **定義 5.3.3.** $\alpha < 0$ に対し:
>
> $$S^{\epsilon}_{\mathrm{CPS}}(p, \alpha) := \lim_{\epsilon \to 0^+} S_{\mathrm{CPS}}(p, \alpha + \epsilon)$$
>
> ここで $S_{\mathrm{CPS}}(p, \alpha + \epsilon)$ は $\alpha + \epsilon > 0$ の領域での §3 の定義を用いる。

**命題 5.3.4.** $S^{\epsilon}_{\mathrm{CPS}}$ について: 
(i) 極限は $\alpha = 0$ で存在し $S_{\mathrm{CPS}}(p, 0)$ に一致する（命題 3.5.1(i) の連続性）。
(ii) $\alpha < 0$ での極限存在は $\{C_\alpha\}_{\alpha \geq 0}$ の $\alpha < 0$ への延長の滑らかさ条件に依存する。Paper VIII の α-忘却濾過は $[0,1]$ 上で定義されており、負の値への延長は非自明。
(iii) 形式的に $\alpha < 0$ を許す場合、$|\mathrm{Mor}(C_\alpha)| > |\mathrm{Mor}(C_0)| = |\mathrm{Mor}(C)|$ が必要となり、これは**C よりも射が多い圏**の存在を要求する。忘却論の枠組み内では、これは「忘却の逆転 = 情報生成」であり、Paper VI の創発作用 $\Xi$ との接続が示唆される。

### 5.4 α = 0 の特異性と物理的解釈

**定理 5.4.1 (α = 0 相転移).** $\alpha_{\mathrm{III}} = 0$（$\alpha_{\mathrm{VIII}} = 1/2$）において、Paper III の copy/delete 構造はちょうど退化する（Paper III §1.1）。情報幾何的には e-接続と m-接続が一致する自己双対点であり、忘却論的には「忘却と保存がちょうど均衡する」臨界点である。

$S_{\mathrm{CPS}}$ の観点から:
- $\alpha_{\mathrm{VIII}} < 1/2$（$\alpha_{\mathrm{III}} < 0$）: 保存が支配的。確定的射が豊富。$S_{\mathrm{CPS}}$ は小さい。
- $\alpha_{\mathrm{VIII}} > 1/2$（$\alpha_{\mathrm{III}} > 0$）: 忘却が支配的。確定的射が減少。$S_{\mathrm{CPS}}$ は大きい。
- $\alpha_{\mathrm{VIII}} = 1/2$（$\alpha_{\mathrm{III}} = 0$）: 相転移点。ここで $\partial S_{\mathrm{CPS}}/\partial\alpha$ が特異性を持つ可能性がある。

**予想 5.4.2 (臨界指数).** $\alpha_{\mathrm{VIII}} = 1/2$ 近傍で $S_{\mathrm{CPS}}(p, \alpha) \sim |\alpha - 1/2|^{-\gamma}$ の形のスケーリング則が存在し、臨界指数 $\gamma > 0$ は圏 C と状態 p の構造に依存する。これが確認されれば、忘却論は文字通りの「相転移」を含むことになる。

### 5.5 戦略的結論

定理 5.2.1 と候補 A, B の分析から:

1. **Perrone エントロピーの直接輸入は α_III < 0 で不可能** — これは定理であり展望ではない。
2. **候補 A（スーパーエントロピー）が最も有望** — 偶セクターで既存理論を回復し、奇セクターに新たな構造を加える。ただし奇セクターの α-単調性が未確認（OP-IX-1 の核心）。
3. **ε-正則化は α < 0 では「忘却の逆転」を要求**し、Paper VI との統合なしには物理的動機づけが弱い。
4. **α = 0 は真の相転移点**であり、ここでのスケーリング則の確立が次の突破口となりうる。

---

## §6. 分配関数と温度

### 6.1 射のエネルギーの自然な定義

これまで $E(f)$ の定義が未確立であったが、§3.5 の臨界忘却閾値を用いて自然な定義を与える。

> **定義 6.1.1 (忘却エネルギー).** 射 $f \in \mathrm{Mor}(C_0) = \mathrm{Mor}(C)$ に対し、その**忘却エネルギー**を:
>
> $$E(f) := \alpha^*_f := \inf\{\alpha \in [0,1] \mid f \notin \mathrm{Mor}(C_\alpha)\}$$
>
> と定義する。すなわち $E(f)$ は射 $f$ が忘却によって消滅する最小の α 値（生存閾値）である。

**命題 6.1.2 (忘却エネルギーの基本性質).**
(i) $E(\mathrm{id}_X) = 1$ for all $X$（恒等射は完全忘却まで生存）。
(ii) $0 \leq E(f) \leq 1$ for all $f$。
(iii) (F4)（射の単調減少）より: $f \in \mathrm{Mor}(C_\alpha) \Leftrightarrow \alpha < E(f)$（左連続の場合）or $\alpha \leq E(f)$（閉値域の場合）。
(iv) $E(g \circ f) \leq \min(E(f), E(g))$（命題 6.7.4b の系: 合成は構成要素の弱い方で制約される）。

*証明.* (i) 恒等射は全ての $C_\alpha$（$\alpha < 1$）に属し、$C_1 = C_{\mathrm{disc}}$ でも $\mathrm{id}_X$ は生存するから $E(\mathrm{id}_X) = 1$。(ii) (F2) より $f \in \mathrm{Mor}(C_0)$ から $E(f) \geq 0$、(F3) と (F4) から $E(f) \leq 1$。(iii) (F4) の定義から直接。(iv) $f \notin \mathrm{Mor}(C_\alpha)$ ならば $g \circ f$ は $C_\alpha$ で定義できないから $\alpha \geq E(f) \Rightarrow g \circ f \notin \mathrm{Mor}(C_\alpha)$。□

### 6.2 分配関数 $Z_{\mathrm{CPS}}(\beta, \alpha)$

> **定義 6.2.1 (CPS 分配関数).** 逆温度 $\beta > 0$ と忘却強度 $\alpha \in [0,1)$ に対し:
>
> $$Z_{\mathrm{CPS}}(\beta, \alpha) := \sum_{f \in \mathrm{Mor}(C_\alpha)} e^{-\beta E(f)}$$
>
> 有限射の圏（$|\mathrm{Mor}(C_\alpha)| < \infty$）では和は有限であり $Z > 0$。

**命題 6.2.2 (分配関数の α-単調性).** $\alpha_1 < \alpha_2$ ならば $Z_{\mathrm{CPS}}(\beta, \alpha_1) \geq Z_{\mathrm{CPS}}(\beta, \alpha_2)$。

*証明.* (F4) より $\mathrm{Mor}(C_{\alpha_2}) \subseteq \mathrm{Mor}(C_{\alpha_1})$。$e^{-\beta E(f)} > 0$ であるから、和の項数が減少すれば全体も減少する。□

**備考 6.2.3.** 定義 6.1.1 は §3.5 の臨界忘却閾値 $\alpha^*(p)$ と本質的に同じ構造であるが、対象が異なる: $\alpha^*(p)$ は状態 $p$ の生存閾値、$E(f)$ は射 $f$ の生存閾値。$S_{\mathrm{CPS}}$ は状態を固定して確定的射の消滅を測り、$Z_{\mathrm{CPS}}$ は全射の消滅を Boltzmann 重みで統合する。

#### 6.2.4 忘却エネルギーと情報幾何的 α の辞書

架橋関手 B (Paper VIII Def. 6.7.3) は sigmoid 正規化 $\eta(\alpha_{\mathrm{III}}) = 1/(1+e^{-\alpha_{\mathrm{III}}})$ を通じて Paper III の情報幾何的パラメータ $\alpha_{\mathrm{III}} \in \mathbb{R}$ と Paper VIII の忘却強度 $\alpha_{\mathrm{VIII}} \in [0,1]$ を接続する。本項では E(f) がこの接続の射レベルの表現であることを厳密化する。

> **命題 6.2.4 (E(f) ↔ η の辞書).** $\eta: \mathbb{R} \to (0,1)$ を Paper VIII Def. 6.7.1 の sigmoid、$\mathrm{logit}: (0,1) \to \mathbb{R}$ をその逆とする。射 $f \in \mathrm{Mor}(C_0)$ に対し、以下が成立する。
>
> (a) **逆変換**: $\alpha_f^{\mathrm{III}} := \mathrm{logit}(E(f)) = \log\frac{E(f)}{1 - E(f)}$ と定義すれば $E(f) = \eta(\alpha_f^{\mathrm{III}})$。
>
> (b) **辞書の内容**: この等式は tautology **ではなく**、以下の物理的対応を符号化する:
>
> | 圏論的量 (Paper VIII/IX) | 情報幾何的量 (Paper III) | 対応 |
> |:--|:--|:--|
> | $E(f)$ = 射の生存閾値 $\in [0,1]$ | $\alpha_f^{\mathrm{III}}$ = 射が「住む」α-接続レベル $\in \mathbb{R}$ | $E = \eta(\alpha^{\mathrm{III}})$ |
> | $E(f) < 1/2$ (忘却に弱い) | $\alpha_f^{\mathrm{III}} < 0$ (e-接続側 = フェルミオン的) | Th. 5.2.1 により Perrone エントロピー不可能 |
> | $E(f) > 1/2$ (忘却に強い) | $\alpha_f^{\mathrm{III}} > 0$ (m-接続側 = ボソン的) | 標準的 Perrone エントロピーが well-defined |
> | $E(f) = 1/2$ (臨界点) | $\alpha_f^{\mathrm{III}} = 0$ (Fisher 計量 = 自己双対) | 予想 5.4.2 の相転移点 |
>
> (c) **分配関数の情報幾何的表示**: $Z_{\mathrm{CPS}}(\beta, \alpha)$ は情報幾何的座標で
>
> $$Z_{\mathrm{CPS}}(\beta, \eta(\alpha_{\mathrm{III}})) = \sum_{f:\, E(f) > \eta(\alpha_{\mathrm{III}})} e^{-\beta \eta(\alpha_f^{\mathrm{III}})}$$
>
> と書ける。和の条件 $E(f) > \eta(\alpha_{\mathrm{III}})$ は $\alpha_f^{\mathrm{III}} > \alpha_{\mathrm{III}}$（η の単調性）と同値であり、「α-接続レベルが閾値を超える射のみが Boltzmann 重みで寄与する」という明快な幾何的解釈を持つ。
>
> *証明.* (a) は $\eta \circ \mathrm{logit} = \mathrm{id}_{(0,1)}$ から直接。(b) の対応表は、Paper VIII Def. 6.7.3 の射レベル規則——$f \in \mathrm{Mor}(C_{\eta(\alpha_{\mathrm{III}})}) \Leftrightarrow \eta(\alpha_{\mathrm{III}}) \leq E(f)$——と Th. 5.2.1 の不可能性定理を組み合わせたもの。(c) は Def. 6.2.1 に $\alpha = \eta(\alpha_{\mathrm{III}})$ および $E(f) = \eta(\alpha_f^{\mathrm{III}})$ を代入し、$\eta$ の単調性から和の条件を変換する。□

> **備考 6.2.5 (三パラメータ統一への示唆).** 命題 6.2.4(c) は予想 6.3.2（三パラメータ統一）の構造的根拠を強化する。$Z_{\mathrm{CPS}}$ の引数が $(\beta, \eta(\alpha_{\mathrm{III}}))$ であるから、$\beta = \beta_{\mathrm{IB}} = 1/T_{\mathrm{CPS}}$ と同定すれば、**分配関数は情報ボトルネック逆温度と α-接続パラメータの二つの情報幾何的量のみで完全に記述される**。第三のパラメータ $\tau$（創発時間スケール）は $T_{\mathrm{CPS}} \cdot \tau = \text{const}$ を通じて $\beta$ に束縛される。すなわち、三パラメータの独立な自由度は実質 **二つ** ($\alpha_{\mathrm{III}}, \beta$) であり、$\tau$ は従属変数である。

### 6.3 温度と三パラメータの関係

CPS 温度は平衡条件 $\partial S / \partial E = 1/T$ の圏論的対応として定義される:

> **定義 6.3.1 (CPS 温度).** $T_{\mathrm{CPS}} := (\partial S_{\mathrm{cat}} / \partial E_{\mathrm{avg}})^{-1}$ ここで $E_{\mathrm{avg}}(\alpha) := \frac{1}{|\mathrm{Mor}(C_\alpha)|} \sum_{f \in \mathrm{Mor}(C_\alpha)} E(f)$ は生存射の平均エネルギー。

三パラメータ統一の候補:

| パラメータ | 出典 | 役割 | CPS 温度との関係 |
|:--|:--|:--|:--|
| $\alpha$ | Paper VIII §6.2 | 忘却強度 | $T_{\mathrm{CPS}}$ の制御変数 |
| $\tau$ | Paper VI §2 | 創発時間スケール | $T_{\mathrm{CPS}} \propto 1/\tau$（予想: 高温 = 速い忘却 = 短い時間スケール）|
| $\beta_{\mathrm{IB}}$ | Paper III §4 | 情報ボトルネック逆温度 | $\beta_{\mathrm{IB}} = \beta$ として $Z_{\mathrm{CPS}}$ を構成する候補 |

**予想 6.3.2 (三パラメータ統一).** 適切な正規化の下で $\beta_{\mathrm{IB}} = 1/T_{\mathrm{CPS}}$ かつ $T_{\mathrm{CPS}} \cdot \tau = \text{const}$（エネルギー-時間不確定性の類似）。これが成立すれば、Paper III/VI/VIII/IX の温度的パラメータは単一の自由度に帰着する。

### 6.4 自由エネルギーとハミルトニアン

$Z$ と $T$ が確立すれば Legendre 変換により:

$$F_{\mathrm{CPS}}(\beta, \alpha) := -\frac{1}{\beta} \log Z_{\mathrm{CPS}}(\beta, \alpha)$$

**命題 6.4.1.** $F_{\mathrm{CPS}}$ は $\alpha$ に関して非減少かつ $\beta$ に関して非増加。

*証明.* 命題 6.2.2 より $Z$ が $\alpha$-非増加であるから $-\log Z$ は $\alpha$-非減少。$\beta > 0$ の符号から $F$ は $\alpha$-非減少。$\beta$-非増加は $e^{-\beta E} \leq 1$ より $Z \leq |\mathrm{Mor}(C_\alpha)|$ と $\log Z / \beta$ の $\beta$-依存性から。□

CPS ハミルトニアンは $H_{\mathrm{CPS}} := F + T \cdot S_{\mathrm{cat}} = -T \log Z + T S_{\mathrm{cat}}$ として形式的に定義可能。ただし $S_{\mathrm{cat}}$ と $S_{\mathrm{CPS}}$ の二つのエントロピーが存在するため、どちらを用いるかは物理的文脈に依存する（OP-IX-4）。

---

## §7. Open Problems

| ID | 問い | 難易度 | 状態 |
|:--|:--|:--|:--|
| OP-IX-1 | Z₂-次数付きスーパーエントロピー $S^{Z_2}_{\mathrm{CPS}}$ の奇セクターにおける α-単調性 (§5.3 候補A) | 高 | Open |
| OP-IX-2 | 分配関数 Z_CPS(β,α) の連続極限: 有限射圏から無限射圏への拡張 (§6.2) | 中 | Open |
| OP-IX-3 | 三パラメータ統一: α, τ, β_IB の関係の厳密化 (§6.3 予想 6.3.2) | 高 | **方向提示** (Prop. 6.2.4, 備考 6.2.5): 独立自由度は (α_III, β) の2つ、τ は従属変数。予想の核心は β_IB = β の同定に帰着 |
| OP-IX-4 | ハミルトニアン H_CPS の well-definedness: S_cat vs S_CPS の選択 (§6.4) | 中 | Open |
| OP-IX-5 | 忘却関手 $U_{\alpha_1 \to \alpha_2}$ が Markov 関手である条件の精密化 | 中 | Open |
| OP-IX-6 | Perrone DPI と Th. 3.4.1 の統合不等式の最適性 | 中 | Open |
| OP-IX-7 | 時間の矢 = 忘却の矢: 備考 3.4.4 の三段チェーンを独立な定理として形式化 (β_α ≤ 0 + Th. 3.4.1 → dS_CPS/dt ≥ 0)。物理時間と粗視化パラメータの関係の公理化が必要。Paper V Th. 2.3.1, Paper XII §8.3 参照 | 高 | Open |
| OP-IX-8 | 臨界指数 γ (予想 5.4.2): α = 1/2 近傍のスケーリング則の具体的計算 | 高 | Open (§5.4 新設) |

---

## 参考文献

### 忘却論シリーズ（内部）
- [I] Paper I: 力は忘却である (v0.14)
- [II] Paper II: 相補性は忘却である (v1.0)
- [III] Paper III: 暗い側 — Z₂-次数付き CPS 圏 (v1.0)
- [IV] Paper IV: なぜ効果量は小さいか (v1.4)
- [V] Paper V: 繰り込みは忘却である (v0.2)
- [VI] Paper VI: 行為可能性は忘却である (v0.1)
- [VII] Paper VII: 知覚は忘却である (v1.3)
- [VIII] Paper VIII: 圏論的基礎における存在 (v1.5)

### 外部
- [P1] Perrone, P. "Markov Categories and Entropy." *IEEE Trans. Inform. Theory* 70(3), 1677–1719, 2024. arXiv:2212.11719.
- [F1] Fritz, T. "A synthetic approach to Markov kernels, conditional independence and theorems on sufficient statistics." *Advances in Mathematics* 370, 107239, 2020. arXiv:1908.07021.
- [B1] Baez, J.C., Owen, L., Moeller, J. "Compositional Thermostatics." *J. Math. Phys.* 64, 022302, 2023. arXiv:2111.10315.
- [DHKK] Dimitrov, G., Haiden, F., Katzarkov, L., Kontsevich, M. "Dynamical systems and categories." *Contemp. Math.* 621, 133–170, 2014.
- [MO] Marshall, A.W. & Olkin, I. *Inequalities: Theory of Majorization and its Applications*. 2nd ed. Springer, 2011.
- [S1] Sagawa, T. "Entropy, Divergence, and Majorization in Classical and Quantum Thermodynamics." arXiv:2007.09974, 2020.

---

### 変更履歴

| バージョン | 日付 | 内容 |
|:--|:--|:--|
| v0.1 | 2026-07-21 | 初稿: §1-§4 (CPS エントロピー構成 + 単調性定理), §5-§6 展望, §7 Open Problems |
| v0.5 | 2026-07-23 | §3.5: Prop 3.5.1 厳密証明 + 臨界忘却閾値 α* 導入。§4.1: Prop 4.1.1 二重粗視化の厳密化。§5: 展望→定理 (Th. 5.2.1 不可能性 + 候補 A/B + 相転移構造)。§6: 展望→構成 (Def. 6.1.1 忘却エネルギー + Z_CPS + 自由エネルギー) |
| v0.6 | 2026-04-10 | §6.2: Prop. 6.2.4 (E(f)↔η辞書 — 忘却エネルギーと情報幾何的αの厳密対応)。備考 6.2.5 (三パラメータ統一の自由度が実質2であることの構造的根拠)。OP-IX-3 に方向提示を追加 |

---

*Paper IX v0.6 — 2026-04-10*
*MECE 構成: §1 動機, §2 Perrone 枠組みの再掲, §3 CPS エントロピーの構成 (Def. 3.3.1) + 単調性定理 (Th. 3.4.1) + 境界条件 (Prop. 3.5.1), §4 既存結果との統合 (Prop. 4.1.1 二重粗視化), §5 α≤0 (Th. 5.2.1 不可能性 + 候補構成 + 相転移), §6 分配関数 (Def. 6.1.1 + Z_CPS + F_CPS)*
