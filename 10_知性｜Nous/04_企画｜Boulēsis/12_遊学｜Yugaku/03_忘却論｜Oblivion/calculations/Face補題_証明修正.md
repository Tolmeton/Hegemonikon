# Face Lemma 証明修正 — nerve の 2-coskeletal 性による厳密化
## Paper II §3.4 の差替え案

**作成日**: 2026-03-27
**動機**: 精読レポートで指摘した Face Lemma の証明の3つの欠陥を修正
**方針**: dim Ξ の定義を simplicial chain complex の次元で置き換え、n ≥ 4 の冗長性を Grothendieck の nerve 特性化定理で保証

---

## 0. 現行証明の欠陥（精読レポートより）

1. **循環的定義**: dim Ξ = |独立な生成射| - 1。「独立な生成射」の定義自体が dim Ξ に依存
2. **暗黙の Kan 仮定**: n = 4 の冗長性を「horn-filling 条件により 2-simplex の合成で完全に決定される」と述べるが、一般の圏の nerve は Kan complex ではない
3. **安定性の非数学的定義**: 「概念 x の安定性」に formal な定義がない

---

## 1. 予備知識: nerve と内部 horn 充填

### 1.1 nerve の定義

圏 $\mathcal{C}$ の nerve $N(\mathcal{C})$ は以下の単体的集合:

- $N_0(\mathcal{C})$ = Ob($\mathcal{C}$) (対象)
- $N_1(\mathcal{C})$ = Mor($\mathcal{C}$) (射)
- $N_n(\mathcal{C})$ = $\{(f_1, f_2, \ldots, f_n) \mid f_i \text{ composable}\}$ ($n$ 個の合成可能な射の列)

面作用素 $\partial_i$: $i$ 番目の合成（$i = 0$ は $f_1$ を落とす、$0 < i < n$ は $f_{i+1} \circ f_i$ で合成、$i = n$ は $f_n$ を落とす）。

### 1.2 Grothendieck の nerve 特性化定理

**定理 (Grothendieck [Segal 1968 の再定式化]).** 単体的集合 $X$ が圏の nerve と同型であるための必要十分条件は、全ての内部 horn $\Lambda^n_k$ ($n \geq 2$, $0 < k < n$) が**一意に**充填可能であることである。

すなわち: $n \geq 2$ のとき、$n$-simplex の $n+1$ 個の面のうち両端を除く $n-1$ 個が与えられれば、残りの面（と $n$-simplex 自体）が**一意に**定まる。

**注意 (Kan complex との差異).** Kan complex は**全ての** horn（外部 horn $\Lambda^n_0$, $\Lambda^n_n$ を含む）の充填を要求するが、nerve は**内部** horn のみ。一般の圏の nerve は Kan complex ではない。しかし内部 horn の一意充填は**全ての圏の nerve で成立する**。

### 1.3 核心的帰結: nerve は 2-coskeletal

**系 1.3.1 (2-coskeletal 性).** 圏 $\mathcal{C}$ の nerve $N(\mathcal{C})$ において、$n \geq 3$ の $n$-simplex は、その 2次元面（face）の集合から**一意に**復元される。

*証明.* $n = 3$ の場合: 3-simplex $\sigma = (f, g, h)$ の面は $\partial_0\sigma = (g, h)$, $\partial_1\sigma = (g \circ f, h)$, $\partial_2\sigma = (f, h \circ g)$, $\partial_3\sigma = (f, g)$。内部 horn $\Lambda^3_1$ は $\{\partial_0, \partial_2, \partial_3\}$ から成り、$\partial_1 = (g \circ f, h)$ は合成 $g \circ f$ から一意に定まる。$\Lambda^3_2$ も同様。一般の $n$ に対しては帰納法: $(n-1)$-simplex が 2次元面から一意に復元されれば、$n$-simplex の内部 horn は $(n-1)$次元面から構成され、Grothendieck 定理により一意に充填される。$\square$

**これが現行証明の欠陥2の修正。** 「horn-filling で 2-simplex に帰着」は Kan 条件ではなく、**nerve 固有の内部 horn の一意充填**から従う。この性質は全ての（小さな）圏に対して成立し、追加の仮定を必要としない。

---

## 2. 新定義: 忘却スペクトラムの次元

### 2.1 Star complex の定義

対象 $x \in \text{Ob}(\mathcal{C})$ の **star complex** $\text{St}(x)$ を、$x$ を頂点として含む $N(\mathcal{C})$ の全 simplex の和として定義する:

$$\text{St}(x) = \bigcup_{x \in \sigma} \sigma \subset N(\mathcal{C})$$

### 2.2 新定義: dim Ξ（循環性の除去）

**定義 2.2.1 (忘却スペクトラムの次元).** 対象 $x$ の忘却スペクトラムの次元を以下で定義する:

$$\dim \Xi(x) := \max\{k \mid \text{St}(x) \text{ が非退化 } k\text{-simplex を含む}\}$$

ここで「非退化」は退化作用素 $s_i$ の像でないことを意味する（恒等射のみからなる simplex を除外）。

**旧定義との比較:**
- **旧**: dim Ξ = |独立な生成射| - 1（循環的）
- **新**: dim Ξ = St(x) の最高非退化 simplex の次元（St(x) の構造から直接計算可能、循環なし）

**これが現行証明の欠陥1の修正。** dim Ξ は「独立な生成射」を経由せず、nerve の組合せ構造から直接定義される。

### 2.3 安定性の形式的定義（欠陥3の修正）

**定義 2.3.1 (CPS-安定性).** CPS 圏の対象 $x$ が **CPS-安定** (CPS-stable) であるとは、以下の2条件を満たすことをいう:

(S1) **非自明性**: $\text{St}(x)$ が恒等射 $\text{id}_x$ 以外の射を含む（$x$ は孤立していない）

(S2) **検証可能性**: $\text{St}(x)$ が非退化 2-simplex を含む（合成 $g \circ f = h$ が独立に検証可能）

**旧定義との比較:**
- **旧**: 「概念 x の安定性」（形式的定義なし）
- **新**: (S1) + (S2) の組合せ論的条件

---

## 3. 修正 Face Lemma の主張と証明

### 3.1 修正 Face Lemma

**定理 3.1.1 (Face Lemma, 修正版).** $\mathcal{C}$ を圏、$x \in \text{Ob}(\mathcal{C})$ とする。

**(a) 最小性.** $x$ が CPS-安定であるための最小条件は:

$$\dim \Xi(x) = 2$$

すなわち、$\text{St}(x)$ に含まれる非退化 simplex の最高次元が **exactly 2** である。

**(b) 等価条件.** 以下は同値:

(i) $\dim \Xi(x) \geq 2$

(ii) $x$ を頂点とする composable triple $(f, g, h)$ with $g \circ f = h$ が存在する（ただし $f, g$ は恒等射でない）

(iii) $x$ は CPS-安定である

**(c) 飽和.** $\dim \Xi(x) \geq 2$ ならば、$\dim \Xi(x) = 2$ と見なして差し支えない: $n \geq 3$ の simplex は 2次元面から一意に復元されるため（系 1.3.1）、新しい構造的情報を持たない。

### 3.2 証明

**(a) 最小性の証明.**

dim Ξ の各値について安定性条件 (S1), (S2) を検証する。

**Case dim Ξ = 0.** St(x) は $x$ 自身（0-simplex）のみを含む。$x$ は孤立対象。(S1) 不成立。$\square$

**Case dim Ξ = 1.** St(x) は 1-simplex（射 $f: x \to y$ または $f: y \to x$）を含むが 2-simplex を含まない。

(S1) は成立する（非恒等射 $f$ が存在）。しかし (S2) は不成立:

2-simplex が存在しないということは、St(x) 内に合成関係 $g \circ f = h$ を実現する三角形がないことを意味する。射 $f, g$ が合成可能であっても、合成 $g \circ f$ は $f$ と $g$ から自動的に決定される**派生量**であり、独立な検証径路 $h$ を提供しない。

**精密な議論.** dim Ξ = 1 のとき、St(x) を通る射の集合を $S = \{f_1, \ldots, f_m\}$ とする。これらの射が情報幾何的に担う忘却量を $\Theta(f_i) \in \mathbb{R}$ とする。$S$ の元が pairwise に合成可能であっても、2-simplex がなければ合成制約 $\Theta(g \circ f) = \Theta(g) + \Theta(f)$ が**検証不能**:

- 合成 $g \circ f$ は圏の公理から存在が保証されるが、その忘却量 $\Theta(g \circ f)$ は $\Theta(g) + \Theta(f)$ と一致するかどうかを独立に測定する手段がない
- 2-simplex $(f, g, h = g \circ f)$ において $h$ は $g \circ f$ と同じ射だが、$h$ を**独立な径路として**測定できることが検証可能性の核心

言い換えれば: dim Ξ = 1 では忘却量 $\Theta$ はスカラー（1次元の値）として測定できるが、忘却の**方向** $\partial_i \Theta$ は定義できない。方向の測定には少なくとも2つの独立な軸が必要であり、2-simplex の2つの独立な辺（$f$ と $g$）がこの2軸を提供する。$\square$

**Case dim Ξ = 2.** St(x) は非退化 2-simplex $(f, g, h)$ を含む。$f: a \to b$, $g: b \to c$, $h = g \circ f: a \to c$ で、$f, g$ は恒等射でない。

(S1): $f \neq \text{id}$ より成立。
(S2): 2-simplex $(f, g, h)$ が存在するため成立。

$\text{St}(x)$ において $x$ は $a$, $b$, $c$ のいずれかであり、$x$ を通る composable triple が存在する。

忘却量 $\Theta$ は2つの独立な方向（$f$ 方向と $g$ 方向）に沿って値を持ち、$\partial_i \Theta \neq 0$ が可能。Paper I の方向性定理により、$\partial_i \Theta \neq 0$ は力 $F_{ij} \neq 0$ の必要条件。$\square$

**(b) 等価条件の証明.**

(i) ⟹ (ii): dim Ξ(x) ≥ 2 ならば St(x) に非退化 2-simplex $\sigma$ が存在する。$\sigma$ の3辺 $(f, g, h)$ は composable triple with $g \circ f = h$。非退化条件より $f, g$ は恒等射でない。

(ii) ⟹ (iii): composable triple $(f, g, h)$ with $g \circ f = h$, $f \neq \text{id}$, $g \neq \text{id}$ が存在する。$f \neq \text{id}$ より (S1) 成立。$(f, g, h)$ が非退化 2-simplex を構成するため (S2) 成立。

(iii) ⟹ (i): (S2) より St(x) に非退化 2-simplex が存在する。定義 2.2.1 より dim Ξ(x) ≥ 2。$\square$

**(c) 飽和の証明.**

系 1.3.1（nerve の 2-coskeletal 性）により、$n \geq 3$ の $n$-simplex は 2次元面から一意に復元される。したがって:

1. St(x) に $n$-simplex ($n \geq 3$) が存在しても、その simplex は St(x) の 2-simplex の集合から**一意に再構成可能**
2. 新しい $n$-simplex は新しい合成関係を表現しない——既存の 2-simplex の合成の「記録」にすぎない
3. よって dim Ξ(x) ≥ 3 は dim Ξ(x) = 2 に対して**構造的に新しい情報を持たない**

形式的には: nerve の 2-coskeletal 性により、圏の構造は 2-skeleton $\text{sk}_2 N(\mathcal{C})$ で完全に決定される。St(x) の 2-skeleton $\text{sk}_2 \text{St}(x)$ が St(x) と同じ情報量を持つ。$\square$

**注意.** この飽和は nerve **固有の**性質であり、一般の単体的集合には成立しない。Kan complex（全 horn 充填可能）を仮定する必要もない。Grothendieck 定理の内部 horn の一意充填のみで十分。これが現行証明の欠陥2の決定的修正。

---

## 4. 下流定理への影響

### 4.1 Blanket 生成定理（§3.7.2）への影響

修正 Face Lemma を Blanket 生成定理の証明に組み込む際、追加すべき条件は以下の1点:

**追加条件**: CPS 圏 $\mathcal{C}_{\text{CPS}}$ の nerve において、composable triple $(f, g, h = g \circ f)$ の射が CPS スパンの忘却関手 $U_A$, $U_B$ の方向と整合する割り当てを持つこと。

具体的には (i) ⟹ (ii) の Step 3a で「ext → int の任意の射が B を経由する」と述べていた箇所に、**追加仮定** として以下を明示する:

> **仮定 (CPS 経由条件).** CPS 圏 $\mathcal{C}_{\text{CPS}}$ において、2-simplex $(f, g, h)$ の射の割り当てが以下を満たす: $f$ は $U_A$ 方向の射（外部 → blanket）であり、$g$ は $U_B$ 方向の射（blanket → 内部）である。このとき合成 $h = g \circ f$ は外部 → 内部の径路であり、$h$ の存在が合成の独立検証を提供する。

この追加仮定は Layer 1 条件の第5条件として位置づけられる:

> **(5) CPS 経由**: 全ての非退化 2-simplex $(f, g, h)$ に対し、$f$ と $g$ は CPS スパンの異なる脚に沿う

### 4.2 FEP 包含定理（§3.7.3）への影響

修正は最小限。FEP 包含定理の (c)「blanket の導出」が修正版 Face Lemma を参照するだけ。dim Ξ ≥ 2 ⟺ 2-simplex の存在 ⟺ blanket の構造的出現、の同値性は修正版でも保たれる。

### 4.3 SST（§3.5 Stability Simplex Theorem）への影響

SST の「忘却量は符号付き（R 値）でなければならない」の証明は dim Ξ の定義に依存しない（三角恒等式の代数的構造のみに依存）。修正不要。

ただし SST の「三者の一致」の系——$\min|\text{Hom}|_{\text{verifiable}} = \min \dim(\Xi)_{\text{non-trivial}} = |\text{Fix}(G \circ F) \text{ attributes}| = 3$——は修正版と整合する:

- $\min|\text{Hom}|_{\text{verifiable}}$ = 3: 2-simplex の辺の数 = 3
- $\min \dim(\Xi)_{\text{non-trivial}}$ = 2: 定義 2.2.1 による
- Fix(G∘F) attributes = 3: 不変

数値 3 と 2 の差異は、「辺の数」と「simplex の次元」の差異（2-simplex は3辺だが2次元）に対応する。旧版では両方を 3 と書いていたが、これは辺の数と simplex 次元の混同。修正版ではこの区別が明確化される。

---

## 5. 修正のまとめ

### 5.1 3つの欠陥の修正状況

| 欠陥 | 修正 | 状態 |
|:---|:---|:---|
| 1. dim Ξ の循環的定義 | **定義 2.2.1**: St(x) の最高非退化 simplex の次元 | ✓ 修正済 |
| 2. Kan complex の暗黙仮定 | **系 1.3.1**: nerve の内部 horn 一意充填 (Grothendieck) | ✓ 修正済 |
| 3. 安定性の非形式的定義 | **定義 2.3.1**: (S1) 非自明性 + (S2) 検証可能性 | ✓ 修正済 |

### 5.2 Paper II §3.4 への差替え指示

1. §3.4 冒頭に §1.1–1.3（nerve, Grothendieck 定理, 2-coskeletal 性）を数学的準備として追加
2. 旧 Face Lemma を定理 3.1.1 に差替え
3. 旧証明の「dim Ξ = |独立な生成射| - 1」を定義 2.2.1 に置換
4. 旧証明の「horn-filling」を系 1.3.1 の正確な参照に置換
5. §3.4 末尾の「直感的再述」は維持（2射 = 表と裏、3射 = 三角形の比喩）
6. §3.7.2 Blanket 生成定理に「CPS 経由条件」を Layer 1 第5条件として追加

### 5.3 証明水準の自己評価

| 主張 | 旧水準 | 新水準 |
|:---|:---|:---|
| Face Lemma (3射の最小性) | C (循環的定義 + 暗黙仮定) | **B+ (Grothendieck 定理に依拠)** |
| 飽和 (n ≥ 3 の冗長性) | D (Kan complex 仮定) | **A (nerve の 2-coskeletal 性は定理)** |
| CPS-安定性の定義 | D (非形式的) | **B (形式的だが物理的動機づけが必要)** |

残る弱点: 定義 2.3.1 の (S2)「2-simplex の存在 = 検証可能性」の動機づけが数学的には自明だが、物理的・認知科学的な解釈は依然として「motivated」レベル。これは数学ではなく応用の問題。

### 5.4 精読レポートの残り2件（別途修正）

- **命題 3.3.1 の格下げ**: α と Δd の対応は**定義**として再記述すべき（本ファイルの範囲外）
- **Δd の割り当て基準の統一**: cell 次元とテンソル階数の混同の解消（§2.3 の修正として別途対応）

---

*修正完了: 2026-03-27*
*使用した定理: Grothendieck nerve 特性化 (Segal 1968), 内部 horn の一意充填*
*参照文献追加: Segal, G. (1968). Classifying spaces and spectral sequences. IHES Publ. Math. 34, 105-112. (nerve の 2-coskeletal 性の原典)*
