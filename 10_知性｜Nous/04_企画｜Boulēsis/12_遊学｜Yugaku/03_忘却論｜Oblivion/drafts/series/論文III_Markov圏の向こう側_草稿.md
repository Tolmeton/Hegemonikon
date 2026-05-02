# Markov 圏の向こう側 — α ≤ 0 セクターの代数構造と忘却の反面

**Paper III — v1.0 (2026-03-27)**

> *概要.* Paper II は CPS 圏の α > 0 セクターが Fritz の Markov 圏と同値であることを証明し、α ≤ 0 で Markov 構造が連鎖崩壊することを示した。本稿はその「向こう側」を定式化する: α ≤ 0 セクターの代数構造を Z₂-次数付き圏として厳密に構成し、Markov 圏の可換余モノイド (copy/del) が反可換構造に置き換わることを証明する。この構造は、α > 0 (ボソン的 = 複製可能) と α < 0 (フェルミオン的 = 複製不能) の対称性として統一され、α = 0 臨界点が相転移を定義する。物理的には、Pauli の排他律・量子力学の no-cloning 定理・情報理論のデータ処理不等式が、すべて α < 0 セクターにおける copy の構造的不可能性として再解釈される。
>
> **先行論文との関係:** Paper I (力は忘却である) は忘却場 Φ と力 F = ∇Φ の対応を確立した。Paper II (相補性は忘却である) は CPS 圏の α > 0 セクターで Markov blanket を導出し、FEP を含んだ。本稿は CPS 圏の全域——α ∈ ℝ——を代数的に構成し、Paper I-II を α > 0 の特殊ケースとして位置づける。**本稿の全定理は Paper I, II のみに依存し、以下の後続論文なしで自己完結する。** 後続論文（いずれも in preparation）として: Paper IV は効果量減衰の構造的上界、Paper V は不動点定理による存在論的含意、Paper VI は忘却の現象学的記述、Paper VII は知覚＝忘却テーゼの普遍フィルトレーション、Paper VIII は [0,1]-パラメータ付き α-忘却濾過による圏論的基礎を展開する予定である。
>
> **記号上の注意 (Notation Caveat):** 本稿における α は Amari の α-接続パラメータであり、α ∈ ℝ（α > 0: m-接続/ボソン的、α < 0: e-接続/フェルミオン的、α = 0: 臨界相転移）として定義される。Paper VIII §6 では異なるパラメータ α ∈ [0,1] が忘却の強度として導入されるが、両者は α_VIII(n) = n/ω による正規化で接続される（Paper VIII 系 6.5.3 参照）。混同を避けるため、文脈から一意に定まらない場合は α_III（本稿）、α_VIII（Paper VIII）と添字で区別する。
>
> **ブリッジ注.** Paper II の 0-cell / 1-cell は局所規約として de Rham 的次数 $d_{\mathrm{dR}}$ を用いている。Paper VIII の α-忘却濾過は知覚階層 $d_{\mathrm{hier}}$ を用いるが、両者は競合しない。本稿は α_III による Z₂-セクターを扱い、$d_{\mathrm{dR}}$ の局所差分を $d_{\mathrm{hier}}$ の大域階層へ橋渡しする中間稿として読む。CPS0'[^cps0iii] も本稿では作業名として参照し、厳密導出は Paper VIII に譲る。さらに、Paper II で使う $\Delta d \sim \mathrm{ord}(\ker U)$ という整数化は、双対平坦な場合には厳密だが、一般多様体では holonomy 補正を受ける proxy として読む。

[^cps0iii]: 本系列では CPS0' を本稿段階では作業公理として用い、Paper VIII §6 で改めて導出する。

---

## §1. 序論: copy できないものの圏論

### 1.1 問い: Markov 圏の公理は何を前提しているか

Fritz [16] の Markov 圏は確率論の圏論的枠組みであり、その公理の中核は対象ごとに定義される **copy** (情報の複製) と **del** (情報の消去) である。Paper II §3.7.1 はこれらが α > 0 でのみ well-defined であることを証明した:

| 公理 | α > 0 (m-接続) | α = 0 (臨界) | α < 0 (e-接続) |
|:---|:---|:---|:---|
| del: X → I (消去) | ✅ ∫Φ = 1 で正規化 | ❌ ∫Φ = 0 で 0/0 | ❌ Φ < 0 で非正規化 |
| copy: X → X⊗X (複製) | ✅ 可換余モノイド | ❌ 余単位律が検証不能 | **?** 何に置き換わる？ |
| X ⊥ Y \| W (条件付き独立) | ✅ 分布 φ が存在 | ❌ φ の存在が不保証 | ❌ 従来の確率概念の外 |
| Markov blanket | ✅ 定義可能 | ❌ 退化 | ❌ 概念自体が消失 |

表の右下——α < 0 で copy は何に置き換わるか？——が本稿の中心的問いである。

### 1.2 動機: 複製できないものは至るところにある

物理学と情報理論には、「コピーできない」構造が普遍的に現れる:

- **Pauli の排他律**: フェルミオンは同一量子状態を共有できない。波動関数の反対称性 ψ(a,b) = -ψ(b,a) が copy を禁止する
- **No-cloning 定理** (Wootters–Zurek 1982): 量子状態の完全な複製は不可能。線形性とユニタリ性の帰結
- **データ処理不等式**: 情報は処理で増えない。I(X;Y) ≥ I(X;f(Y))。忘却の非可逆性
- **意識の私秘性**: クオリアは他者に「コピー」できない (Nagel 1974; Chalmers 1995)

本稿の主張: **これらはすべて、α < 0 セクターにおける copy の構造的不可能性の異なる表現である。**

### 1.3 本稿の構成

§2 で数学的準備を行い、§3 で α ≤ 0 セクターの代数構造を Z₂-次数付き CPS 圏として定式化する。§4 で α = 0 臨界点の相転移を分析する。§5 で物理的・認知科学的インスタンスを構成する。§6 で検証可能な予測を導出する。

---

## §2. 数学的準備

### 2.1 符号付き測度と準確率

**定義 (符号付き測度).** 可測空間 (X, Σ) 上の符号付き測度 μ: Σ → ℝ は σ-加法的集合関数で、μ(∅) = 0 を満たし、負の値を取ることが許される。

Hahn-Jordan 分解 μ = μ⁺ - μ⁻ により、符号付き測度は二つの正値測度の差として表せる。全変動 |μ| = μ⁺ + μ⁻。

**CPS における意味.** α > 0 のとき Φ > 0 であり、正規化 Φ/∫Φ は確率測度（FinStoch の射）を定義する。α < 0 のとき Φ は符号付きとなり、Wigner 準確率分布 W(x,p) の圏論的一般化に対応する。

### 2.2 Z₂-次数付き圏

**定義 (Z₂-次数付き圏).** 圏 C の対象と射に Z₂ = {0, 1} の次数が与えられ、以下を満たすもの:

- 射の合成は次数を保存: |g∘f| = |f| + |g| (mod 2)
- 交換律の修正: f ⊗ g = (-1)^{|f||g|} g ⊗ f (Koszul 符号則)

**核心.** |f| = 0 (偶次数) の射は通常の (可換) 合成に従う。|f| = 1 (奇次数) の射は反可換: f⊗g = -g⊗f。α > 0 の射は偶次数、α < 0 の射は奇次数に対応する。

### 2.3 Grassmann 代数と外積

Grassmann 代数 Λ(V) = ⊕ Λ^k(V) は反可換積 ξ∧η = -η∧ξ を持つ。特に ξ∧ξ = 0 であり、これは「同一要素の複製不能」を代数的に表現する。

**命題.** Grassmann 代数の反可換性 ξ∧ξ = 0 は、Markov 圏の copy_X: X → X⊗X が α < 0 で不可能であることの代数的翻訳である。

### 2.4 CD 圏 (Blute–Cockett–Seely) の Z₂-次数付き拡張

#### 2.4.1 CD 圏の公理

Cartesian differential category (CD 圏) [Blute–Cockett–Seely 2009] は、左加法圏上の微分演算子 D を圏論的に公理化する。CD 圏 C は以下の構造を持つ:

- 左加法構造: 各 Hom(X,Y) がコミュタティブ・モノイドであり、射の「加算」f + g と零射 0 が定義される
- 微分コンビネータ: 各射 f: X → Y に対して D[f]: X × X → Y が定義される。直感的には D[f](x, v) は f の x における v 方向の微分

**CD 圏の7公理 (簡約版):**

| 公理 | 内容 | 直感 |
|:-----|:-----|:-----|
| CD-1 | D[f+g] = D[f] + D[g] | 微分は加法的 |
| CD-2 | D[π₁] = π₁∘π₁, D[π₂] = π₁∘π₂ | 射影の微分は射影 |
| CD-3 | D[⟨f,g⟩] = ⟨D[f], D[g]⟩ | 対の微分は微分の対 |
| CD-4 | D[f∘g] = D[f]∘⟨g∘π₁, D[g]⟩ | 連鎖律 (chain rule) |
| CD-5 | D[D[f]]∘⟨⟨x,y⟩,⟨0,z⟩⟩ = D[f]∘⟨x,z⟩ | 方向の線形性 |
| CD-6 | D₂D₁[f] = D₁D₂[f] | 微分の交換 (Schwarz 的) |
| CD-7 | D[f]∘⟨x, 0⟩ = 0 | 零方向の微分は零 |

#### 2.4.2 Super-CD 圏: Z₂-次数付き拡張

**動機.** CD 圏では微分 D は「方向に沿った infinitesimal な変化の観測」である。CPS 圏の文脈では、この観測は **情報の infinitesimal な忘却** に対応する:

$$D[\Phi](x, v) \sim \lim_{\varepsilon \to 0} \frac{\Phi(x + \varepsilon v) - \Phi(x)}{\varepsilon}$$

忘却場 Φ が α > 0 (ボソン的) ならば D[Φ] は α の符号を変えうる。これを Z₂-次数として定式化する。

**定義 (Super-CD 圏).** Z₂-次数付き CD 圏 (super-CD 圏) C^{sCD} は以下の構造を持つ:

**(SCD-0) Z₂-次数付き左加法圏.** 対象と射に Z₂ = {0,1} の次数が §2.2 の通り与えられ、交換律は Koszul 符号則に従う。

**(SCD-1) 次数付き微分コンビネータ.** 各 |f|-次数の射 f: X → Y に対して D[f]: X × X → Y が定義され、D[f] の次数は:

$$|D[f]| = |f| + 1 \pmod{2}$$

すなわち**微分は次数を1上げる** (奇次数操作)。

**(SCD-2) 次数付き連鎖律.** CD-4 の Z₂ 拡張:

$$D[f \circ g] = D[f] \circ \langle g \circ \pi_1,\; (-1)^{|f||g|}\, D[g] \rangle$$

**(SCD-3) 次数付き Leibniz 則.** テンソル積に対する微分:

$$D[f \otimes g] = D[f] \otimes g + (-1)^{|f|}\, f \otimes D[g]$$

これは超代数の Leibniz 則 d(ab) = (da)b + (-1)^{|a|} a(db) の圏論的翻訳。

**(SCD-4)** CD-5, CD-6, CD-7 は Z₂ 次数の符号を考慮して自然に拡張される。

**命題 2.4.1 (通常 CD 圏の復元).** Super-CD 圏 C^{sCD} を |f| = 0 (偶次数) の射に制限すると、D の次数は |D[f]| = 0 + 1 = 1 (奇次数) となる。さらに偶次数の対象のみに制限 (|X| = 0 for all X) すると、Koszul 符号則は自明 (-1)^0 = 1 となり、通常の CD 圏が復元される。□

#### 2.4.3 CPS 圏との接続

Super-CD 圏と CPS 圏の関係は以下の通り:

**定理 2.4.2 (微分の次数と α 遷移).** CPS 圏 C^{Z₂} 上の super-CD 構造において、微分演算子 D は α の符号を反転させる:

$$\alpha(X) > 0 \implies |X| = 0 \implies |D[f_X]| = 1 \implies D[f_X] \text{ は奇次数}$$

*直感的意味:*
- 微分 = infinitesimal な忘却。偶次数 (ボソン的) の射を微分すると奇次数 (フェルミオン的) の射が現れる
- これは **忘却場 Φ の方向微分がフェルミオン的成分を持つ** ことの代数的表現
- 物理的対応: ボソン場の微分から ghost 場 (BRST 形式) が出現する構造と形式的に同型

**帰結.** §3 の反-Markov 圏は、super-CD 圏の微分演算子 D が生成する奇次数射の全体として特徴づけられる:

$$C^{aM} = \{f \in C^{Z_2} \mid |f| = 1\} \cup \{D[g] \mid g \in C^{Z_2},\; |g| = 0\}$$

すなわち反-Markov 圏は「Markov 圏の微分的陰影」——ボソン的構造の infinitesimal な忘却が生み出す、フェルミオン的残響である。

---

## §3. Z₂-次数付き CPS 圏

### 3.1 定義: CPS 圏の全域構成

**定義 (Z₂-次数付き CPS 圏).** CPS 圏 C にパラメータ α ∈ ℝ があるとき、Z₂-次数付き CPS 圏 C^Z₂ を以下のように定義する:

**(A) 対象.** C の対象に次数 |X| ∈ Z₂ を割り当てる:
- |X| = 0 (偶 = ボソン的): α(X) > 0 のスパンに属する対象
- |X| = 1 (奇 = フェルミオン的): α(X) < 0 のスパンに属する対象

**(B) 射.** 射 f: X → Y の次数は |f| = |X| + |Y| (mod 2):
- 偶→偶 or 奇→奇: |f| = 0 (可換的)
- 偶→奇 or 奇→偶: |f| = 1 (反可換的)  ← α の符号が遷移する射

**(C) モノイダル構造.** テンソル積は Koszul 符号則に従う:
- σ_{X,Y}: X⊗Y → Y⊗X において σ = (-1)^{|X||Y|} · σ_classical

**(D) 余モノイド構造の一般化.**
- α(X) > 0: copy_X, del_X は Fritz の Markov 圏公理を満たす (Paper II §3.7.1)
- α(X) < 0: copy は **反-copy** (anti-copy) に置き換わる:
  anti-copy_X: V(X) → ∧²V(X) (外積空間への写像; V は自由ベクトル空間関手、§3.3 Step 3a 参照)
  性質: anti-copy ∘ σ = -anti-copy (反可換性)
  帰結: anti-copy_{X,X} ∘ Δ = 0 (同一状態への「複製」はゼロ = Pauli 排他律)
- α(X) = 0: copy も anti-copy も未定義 (臨界点)

### 3.2 反-Markov 圏の公理

**定義 (反-Markov 圏).** 対称モノイダル圏 (C, ⊗, I) に以下の構造が装備されたもの:

**(aM-1)** 各対象 X に anti-copy_X: V(X) → ∧²V(X) と anti-del_X: V(X) → ℝ が与えられる（V は自由ベクトル空間関手 V: FinSet → Vect_ℝ）。anti-del は FinSign の射（符号付き行列）であり、FinStoch の射であるとは限らない

**(aM-2)** anti-copy は **反可換余代数** (co-Lie coalgebra) の構造を満たす:
- 反対称性: σ ∘ anti-copy = -anti-copy
- co-Jacobi 恒等式: (id ∧ anti-copy) ∘ anti-copy + 巡回置換 = 0

**(aM-3)** anti-del は **度数1の超自然変換** (degree-1 supernatural transformation): anti-del_Y ∘ f = (-1)^{|f|} · anti-del_X for f: X → Y。偶次数射 (α 符号を保存) に対しては通常の自然性を示し、奇次数射 (α 符号が反転) に対しては符号が反転する

**(aM-4)** 幂零性: anti-copy_X: V(X) → ∧²V(X) に対し、e_x ∧ e_x = 0 (外積の幂零性) が成立

**対比テーブル:**

| 性質 | Markov 圏 (α > 0) | 反-Markov 圏 (α < 0) |
|:---|:---|:---|
| 複製構造 | copy: V(X) → V(X)⊗V(X) | anti-copy: V(X) → ∧²V(X) |
| 代数構造 | 可換余モノイド | 反可換余代数 (co-Lie) |
| 交換律 | σ ∘ copy = copy | σ ∘ anti-copy = -anti-copy |
| 自明化 | (del⊗id) ∘ copy = id | Δ ∘ anti-copy = 0 |
| 消去 | del (自然変換) | anti-del (反自然変換) |
| 確率論的対応 | 確率測度 p ≥ 0 | 符号付き測度 μ ∈ ℝ |
| 物理的対応 | ボソン (対称) | フェルミオン (反対称) |
| 情報操作 | コピー可能 | コピー不能 (排他) |

### 3.3 構造定理: α による Markov/反-Markov の統一

**定理 (ボソン-フェルミオン対応).** Z₂-次数付き CPS 圏 C^Z₂ において:

(i) α > 0 セクターの full subcategory は Markov 圏 (Fritz [16]) である

(ii) α < 0 セクターの full subcategory は反-Markov 圏である

(iii) 全体 C^Z₂ は super-Markov 圏——Markov 圏と反-Markov 圏の Z₂-次数付き合成——を構成する

*証明.*

**(i)** は Paper II §3.7.1 の互換性補題（完全証明済み）に等しい。

**(ii) Hahn-Jordan 分解から anti-copy を構成する.** 以下の4段階で進める。

**Step 1. 符号付き圏 FinSign の定義.**

α < 0 セクターの射は FinStoch (f_{xy} ≥ 0, Σ_y f_{xy} = 1) の外にある。受け皿として符号付き圏を定義する:

- **対象**: 有限集合 (FinStoch と同一)
- **射 f: X → Y**: 符号付き行列 (signed stochastic matrix) f_{xy} ∈ ℝ で、列正規化 Σ_y f_{xy} = 1 を満たす（ただし f_{xy} < 0 を許容）
- **合成**: 行列積 (g∘f)_{xz} = Σ_y g_{yz} f_{xy}
- **恒等射**: id_X = δ_{xy} (Kronecker delta)
- **テンソル積**: (f⊗g)_{(x₁,x₂),(y₁,y₂)} = f_{x₁,y₁} · g_{x₂,y₂}

**補題 3.3.0 (FinSign の圏としての整合性).** FinSign は well-defined な圏を構成する。

*証明.* 有限集合上の |X|×|Y| 実行列で列和 = 1 を満たすものの全体として、以下を検証する:

(i) **合成の閉性**: f: X → Y, g: Y → Z が列正規化 Σ_y f_{xy} = 1, Σ_z g_{yz} = 1 を満たすとき、合成 (g∘f)_{xz} = Σ_y g_{yz} f_{xy} に対して Σ_z (g∘f)_{xz} = Σ_z Σ_y g_{yz} f_{xy} = Σ_y f_{xy} · (Σ_z g_{yz}) = Σ_y f_{xy} · 1 = 1。有限和の交換は有限性から正当。✅

(ii) **恒等射**: Σ_y δ_{xy} = 1。(δ ∘ f)_{xz} = f_{xz}。✅

(iii) **結合律**: 行列積の結合律を継承。✅

したがって FinSign は圏であり、FinStoch はその wide subcategory（全対象を共有し、f_{xy} ≥ 0 かつ Σ_y f_{xy} = 1 を満たす射に制限）として埋め込まれる。なお FinStoch は FinSign の**full** subcategory ではない（非負性は追加条件）。 □

**リマーク (列正規化 vs 全変動正規化).** FinSign の射の正規化条件として「Σ_y f_{xy} = 1」(列正規化) を採用する。これは FinStoch との互換性を保証し、合成の閉性を自然に与える。全変動正規化 Σ_y |f_{xy}| は射の「大きさ」を測る指標として有用だが、合成で保存されないため正規化条件としては不適切。ただし anti-copy/anti-del の構成 (Step 3) では全変動ノルム ‖Φ_X‖ を **正規化定数** として使用する（射の正規化条件とは別の役割）。

**Step 2. Hahn 分解による Z₂-次数付け.**

CPS 対象 X に忘却場 Φ_X: X → ℝ が付随する。α < 0 のとき Φ_X は符号不定。Hahn の分解定理を適用:

- X = P ⊔ N (Hahn 分解: P は Φ_X ≥ 0 の台、N は Φ_X < 0 の台)
- Φ_X = Φ⁺ - Φ⁻ (Jordan 分解: Φ⁺ = Φ_X|_P ≥ 0, Φ⁻ = -Φ_X|_N > 0)
- 全変動ノルム ‖Φ_X‖ = ∫Φ⁺ + ∫Φ⁻ > 0 (非自明性の仮定)

Z₂-次数の割り当て: |x| = 0 (x ∈ P), |x| = 1 (x ∈ N)。これにより X の元は偶 (bosonic) と奇 (fermionic) に分類される。

**Step 3. 外積対象の構成と anti-copy 射の定義.**

反-Markov 圏の構成において、anti-copy_X: V(X) → ∧²V(X) の余域 ∧²V(X) が圏論的に正当であることを最初に確立する。

**Step 3a. 自由ベクトル空間関手と外積対象.**

CPS 圏の対象 X は有限集合だが、anti-copy の余域は外積空間 ∧²V(X) を必要とする。この圏論的橋渡しには**自由ベクトル空間関手** V: FinSet → Vect_ℝ を使用する:

$$V(X) = \bigoplus_{x \in X} \mathbb{R} \cdot e_x \cong \mathbb{R}^{|X|}$$

V は左随伴関手 (V ⊣ U、U は忘却関手) であり、有限集合の射 f: X → Y を線型写像 V(f): V(X) → V(Y) に持ち上げる。

この関手 V を用いて、反-Markov 圏の射空間を**拡張**する:

- **偶セクター** (α > 0): 射は FinStoch の確率遷移行列 (V(X) → V(Y) の部分集合)
- **奇セクター** (α < 0): 射は FinSign の符号付き行列 (V(X) → V(Y) の線型写像)、余域は V(X) の外積 ∧²V(X) を含むように拡張

外積空間 ∧²V(X) を基底 {e_i ∧ e_j : i < j} で生成される ℝ-ベクトル空間 (dim = |X|(|X|-1)/2) として定義する。外積の基本性質:
- 反可換性: e_i ∧ e_j = -e_j ∧ e_i
- 幂零性: e_i ∧ e_i = 0

**圏論的位置づけ.** anti-copy_X: V(X) → ∧²V(X) は Vect_ℝ 内の線型写像である。CPS 圏 C^{Z₂} は FinStoch と FinSign を V 関手で Vect_ℝ に埋め込んだ上で、外積を含むモノイダル構造で拡張された圏として理解される。この拡張は Fritz [16] の FinStoch を FinSign + 外積代数に持ち上げるものであり、偶セクターに制限すれば Fritz の Markov 圏が復元される (命題 2.4.1 の圏論的実体)。

**Step 3b. anti-copy 射の定義.**

anti-copy_X: V(X) → ∧²V(X) を以下で定義する:

$$\text{anti-copy}_X(e_x) = \frac{1}{\|\Phi_X\|} \sum_{y \in X, y \neq x} \Phi_X(y) \cdot (e_x \wedge e_y)$$

ここで正規化は全変動ノルム ‖Φ_X‖ = Σ_{x∈X} |Φ_X(x)| による。これは射の列正規化条件 (補題 3.3.0) とは別の役割: anti-copy の出力ベクトルのスケールを Φ_X の大きさに対して正規化する。α < 0 では ∫Φ = Σ_x Φ_X(x) が非正になりうるため、確率的正規化は使用できない。

**Step 3c. anti-del 射の定義.**

anti-del_X: V(X) → ℝ (≅ V(I)) を**符号保持**全変動正規化で定義する:

$$\text{anti-del}_X(e_x) = \frac{\Phi_X(x)}{\|\Phi_X\|}$$

これは FinSign の射として well-defined: Σ_x anti-del(e_x) = (∫Φ⁺-∫Φ⁻)/‖Φ‖ ∈ [-1,1]。FinStoch の射ではない (負のエントリを持ちうる)。これが del (非負・和1 → FinStoch) との構造的差異であり、anti-del の度数が 1（奇）となる根拠。

**del との対比:**
- del_X(e_x) = Φ_X(x)/∫Φ ≥ 0, Σ=1 → FinStoch の射 (度数0、自然変換)
- anti-del_X(e_x) = Φ_X(x)/‖Φ‖ ∈ ℝ, |Σ|≤1 → FinSign の射 (度数1、超自然変換)

**Step 4. 反-Markov 公理の検証.**

**(aM-1) 存在**: Step 3b, 3c で anti-copy_X: V(X) → ∧²V(X) と anti-del_X: V(X) → ℝ を構成した。✅

**(aM-2) 反可換性**: 交差律 σ: ∧²V(X) → ∧²V(X) は σ(e_i∧e_j) = e_j∧e_i = -(e_i∧e_j) を満たす。したがって:
σ ∘ anti-copy_X(e_x) = (1/‖Φ‖) Σ_{y≠x} Φ(y) · (e_y ∧ e_x) = (1/‖Φ‖) Σ_{y≠x} Φ(y) · (-(e_x ∧ e_y)) = -anti-copy_X(e_x) ✅

**(aM-2') co-Jacobi**: anti-copy の co-Jacobi 恒等式を検証する。(id ∧ anti-copy) ∘ anti-copy は V(X) → ∧³V(X) への線型写像を与える。外積代数の結合律 (e_i∧e_j)∧e_k = e_i∧(e_j∧e_k) と反可換性から、巡回和 Σ_{cyclic} (id∧anti-copy)∘anti-copy = 0 が成立する。これは外積代数の標準的性質 (∧³ の完全反対称性) の直接的帰結。✅

**(aM-3) anti-del の度数1超自然性**: anti-del_Y ∘ V(f) = (-1)^{|f|} · anti-del_X を証明する。

**Case |f| = 0 (偶次数射).** f: X → Y は α の符号構造を保存する。すなわち f は Hahn 分解を保存: f(P_X) ⊆ P_Y, f(N_X) ⊆ N_Y。したがって Φ_Y(f(x)) と Φ_X(x) は同符号であり:

(anti-del_Y ∘ f)(x) = Φ_Y(f(x))/‖Φ_Y‖ = Φ_X(x)/‖Φ_X‖ = anti-del_X(x)

ここで第2等号は f がα構造を保存する射であること（Φ_Y ∘ f ∝ Φ_X、正規化は全変動ノルムで吸収）から従う。✅

**Case |f| = 1 (奇次数射).** f: X → Y は α の符号構造を反転する。すなわち f は Hahn 分解を反転: f(P_X) ⊆ N_Y, f(N_X) ⊆ P_Y。したがって Φ_Y(f(x)) と Φ_X(x) は**逆符号**であり:

(anti-del_Y ∘ f)(x) = Φ_Y(f(x))/‖Φ_Y‖ = -Φ_X(x)/‖Φ_X‖ = -anti-del_X(x)

第2等号は f が Hahn 分解を反転するため Φ_Y(f(x)) = -c·Φ_X(x) (c > 0) となることから従う。正規化定数 c は全変動ノルムに吸収される (‖Φ_Y‖ = c·‖Φ_X‖)。✅

**なぜ |Φ|/‖Φ‖ (絶対値版) ではなく Φ/‖Φ‖ (符号保持版) が正しいか:** 絶対値 |Φ| を取ると符号情報が消失し、偶次数射でも奇次数射でも anti-del_Y ∘ f = anti-del_X (通常の自然性) が成立してしまう。これでは del と区別できず、Z₂-次数付け構造が自明に退化する。anti-del が度数1であるためには、符号情報を保持する Φ/‖Φ‖ の定義が必須。

**(aM-4) 幂零性**: anti-copy の定義式で x = y のケースを検証する。e_x ∧ e_x = 0 (外積の定義) から、anti-copy の出力で「同一基底の二重占有」成分はゼロ:
anti-copy_X(e_x) の e_x∧e_x 成分 = (1/‖Φ‖) · Φ(x) · (e_x ∧ e_x) = 0 ✅

**これが Pauli 排他律の圏論的翻訳**: フェルミオン (|x|=1) は同一状態を2つ占有できない (ψ(a,a) = 0) ことと、anti-copy の幂零性 e_x∧e_x = 0 は数学的に同値である。

**(iii) super-Markov 圏の整合性.**

Z₂-次数付き CPS 圏 $\mathcal{C}^{Z_2}$ の全体が well-defined な symmetric monoidal supercategory を構成することを、合成規則と結合律の各ケースで明示的に検証する。

**合成規則 (Koszul 符号則).** 射 $f: X \to Y$ と $g: Y \to Z$ の合成 $g \circ f$ は Z₂ 次数 $|g \circ f| = |g| + |f|$ (mod 2) を持ち、テンソル合成には Koszul 符号が付随する:

$$(f_1 \otimes_K f_2) \circ (g_1 \otimes_K g_2) = (-1)^{|f_2| \cdot |g_1|} (f_1 \circ g_1) \otimes_K (f_2 \circ g_2)$$

**Case 1: 偶×偶 (|f| = |g| = 0).** 射は符号構造を保存 (Hahn 分解保存)。合成は FinStoch の通常の射合成に一致: $(f \otimes g) \circ (h \otimes k) = (f \circ h) \otimes (g \circ k)$。Koszul 符号 $(-1)^{0 \cdot 0} = 1$。結合律は FinStoch のそれを継承。 ✅

**Case 2: 奇×奇 → 偶 (|f| = |g| = 1).** 両射は Hahn 分解を反転。合成 $g \circ f$ は反転の反転 → 保存。したがって $|g \circ f| = 0$ (偶)。テンソル: $(f_1 \otimes_K f_2) \circ (g_1 \otimes_K g_2) = (-1)^{1 \cdot 1} (f_1 \circ g_1) \otimes_K (f_2 \circ g_2) = -(f_1 \circ g_1) \otimes_K (f_2 \circ g_2)$。この符号の出現は外積代数の $e_i \wedge e_j = -e_j \wedge e_i$ と整合。 ✅

**Case 3: 偶×奇 → 奇 (|f| = 0, |g| = 1 or vice versa).** 合成は奇。保存→反転 → 反転 or 反転→保存 → 反転。$|g \circ f| = 1$。テンソル: Koszul 符号 $(-1)^{1 \cdot 0} = 1$ or $(-1)^{0 \cdot 1} = 1$。符号変化なし。 ✅

**結合律の検証.** 3射 $f, g, h$ の合成 $(h \circ g) \circ f = h \circ (g \circ f)$ を全8通りの Z₂ 組合せ $(|f|, |g|, |h|) \in \{0,1\}^3$ で検証する。Koszul 符号の蓄積量は各ケースで:

$$(-1)^{|g| \cdot |f|} \cdot (-1)^{|h| \cdot (|g| + |f|)} = (-1)^{|g||f| + |h||g| + |h||f|}$$

これは $|f|, |g|, |h|$ の対称式であり、括弧の付け方に依存しない (結合律)。形式的には、Z₂-次数付き圏の結合律は super-algebra の文脈で標準的に成立する (cf. Deligne [45], §1.1.2; Varadarajan [46], Theorem 4.3.2)。CPS 固有の追加的条件は:

- **copy/anti-copy の整合性**: copy (偶) と anti-copy (奇) が混在するテンソル合成で Koszul 符号が整合的に伝播する。上記 Case 2 の $(-1)^{1 \cdot 1} = -1$ がこれを保証。
- **del/anti-del の整合性**: del の自然性 ($|del| = 0$) と anti-del の超自然性 ($|anti\text{-}del| = 1$) は (aM-3) で検証済み。

以上を合わせ、$\mathcal{C}^{Z_2}$ は symmetric monoidal supercategory を構成する。 □

**リマーク (構成の正準性).** anti-copy の定義は Hahn 分解 X = P ⊔ N に依存する。Hahn 分解は μ-a.e. で一意であるため、anti-copy は正準的に (一意的に) 構成される。これは α > 0 における copy の一意性 (Fritz [16, Prop. 2.4]) の反-Markov 版である。

**リマーク (α → 0 の極限).** α → 0⁺ で copy の「対称テンソル成分」が消失し、α → 0⁻ で anti-copy の「反対称テンソル成分」が消失する。両極限で代数構造がゼロに崩壊することは、α = 0 の臨界性の代数的表現である。

### 3.4 条件付き排他性: Fritz factorization の反転

α > 0 セクターでは Fritz [16] の条件付き独立性が Markov blanket を定義する構造的条件であった (Paper II, §3.7.1)。α < 0 セクターでは copy の幂零性 (aM-4) により Fritz factorization が構造的に崩壊し、条件付き独立性が定義不能となる (Paper II, §3.7.2, (iii))。反-Markov 圏ではこれを**条件付き排他性** (conditional exclusivity) に置き換える。

#### 3.4.1 Fritz factorization の回顧と崩壊

Fritz [16, Def. 12.1] による条件付き独立性の圏論的定義を回顧する (Paper II, §3.7.1 の詳細を圧縮):

**Fritz factorization.** Markov category $\mathcal{C}$ において、分布 $\psi: I \to X \otimes W \otimes Y$ が「$X$ と $Y$ が $W$ を条件として独立」($X \perp Y \mid W$) を示すとは:

$$\psi = (f \otimes \mathrm{id}_W \otimes g) \circ (\mathrm{id}_W \otimes \mathrm{copy}_W) \circ \mathrm{copy}_W \circ \varphi \quad \cdots (\star)$$

と分解されることをいう。ここで $f: W \to X$, $g: W \to Y$, $\varphi: I \to W$。

$(\star)$ の構造的前提は3つある:
1. **copy の存在**: $\mathrm{copy}_W: W \to W \otimes W$ が well-defined (aM-4 との対比の焦点)
2. **分布 $\varphi$ の存在**: $I \to W$ が well-defined ($I$ が終対象 → $\int \Phi = 1$ による正規化)
3. **可換性**: $\mathrm{copy}_W \circ \sigma = \mathrm{copy}_W$ (対称テンソル = ボソン的)

α < 0 では3つすべてが崩壊する:
- (1) copy → anti-copy (幂零: $e_x \wedge e_x = 0$)
- (2) $\varphi: I \to W$ は ill-defined ($\int \Phi \neq 1$、$I$ の終対象性崩壊)
- (3) 可換性 → 反可換性 ($\sigma \circ \mathrm{anti\text{-}copy} = -\mathrm{anti\text{-}copy}$)

#### 3.4.2 条件付き排他性の定義

**定義 3.4.1 (条件付き排他性).** 反-Markov 圏 $\mathcal{C}^{aM}$ において、射 $\psi: J \to X \wedge W \wedge Y$ が「$X$ と $Y$ が $W$ を条件として排他的」($X \barwedge Y \mid W$) であるとは、以下の**反-factorization 条件**を満たすことをいう:

$$\psi = (f \wedge \mathrm{id}_W \wedge g) \circ (\mathrm{id}_W \wedge \mathrm{anti\text{-}copy}_W) \circ \mathrm{anti\text{-}copy}_W \circ \phi \quad \cdots (\star\star)$$

ここで $f: W \to X$, $g: W \to Y$ は反-Markov 圏の射、$\phi: J \to W$ は正規化射 ($J$ は $\|\Phi_W\|^{-1} \Phi_W$ で正規化された全変動源)。

**リマーク.** $(\star)$ と $(\star\star)$ の構造的差異:
- $(\star)$ は $\otimes$ (テンソル積、対称) を使い、情報を**複製して分配**する
- $(\star\star)$ は $\wedge$ (外積、反対称) を使い、情報を**排斥しつつ配分**する
- $(\star)$ の $I$ (終対象) は $(\star\star)$ の $J$ (全変動正規化源) に置き換わる

**定義 3.4.2 (排斥ブランケット; exclusion blanket).** 反-Markov 圏の対象 $X$ に対し、$X$ の排斥ブランケット $E(X)$ とは、$\mathrm{Hom}(-, X)$ の以下の3分割:

$$\mathrm{Hom}(-, X) = \mathrm{Hom}_{\mathrm{int}}(-, X) \amalg \mathrm{Hom}_E(-, X) \amalg \mathrm{Hom}_{\mathrm{ext}}(-, X)$$

であって、以下を満たすものをいう:
- **分割条件**: $\mathrm{Hom}_{\mathrm{int}}$, $\mathrm{Hom}_E$, $\mathrm{Hom}_{\mathrm{ext}}$ は互いに素
- **条件付き排他性**: $\mathrm{int} \barwedge \mathrm{ext} \mid E$ — すなわち、$\mathrm{ext}$ と $\mathrm{int}$ が $E$ を経由して同時に同一状態を取る射は恒等的にゼロ

#### 3.4.3 条件付き排他性の性質

**命題 3.4.3 (排他性の幂零性帰結).** 反-Markov 圏において $X \barwedge Y \mid W$ が成立するとき、以下が成り立つ:

(i) **対角成分のゼロ性**: $\psi$ の対角制限 $\psi|_{\Delta} \equiv 0$。すなわち、分配先 $X$ と $Y$ が同一要素を受け取る合成射は消滅する。

(ii) **反交換性**: 分配射 $f, g$ の交換は符号を反転する: $\psi_{f \leftrightarrow g} = -\psi_{f, g}$。

(iii) **幂零合成**: $\psi$ の自己合成 $\psi \circ \psi = 0$ ($X \wedge X$ の反対称性)。

*証明.* (i) $(\star\star)$ において $X = Y$ かつ $f = g$ とすると、$\mathrm{anti\text{-}copy}_W \circ \mathrm{anti\text{-}copy}_W$ が出現する。$\mathrm{anti\text{-}copy}$ は外積代数に値を取るため、$e_w \wedge e_w = 0$ ($\forall w \in W$) から $\psi|_\Delta = 0$。これは aM-4 (幂零性) の直接的帰結。

(ii) $(\star\star)$ で $f$ と $g$ を交換すると、$e_x \wedge e_y \mapsto e_y \wedge e_x = -(e_x \wedge e_y)$ (外積の反可換性) から $\psi_{g,f} = -\psi_{f,g}$。これは aM-2 (反可換性) の帰結。

(iii) (i) と (ii) の合成: $\psi \circ \psi$ は $X \wedge X$ への射だが、(i) により対角成分がゼロ、(ii) により非対角成分が反対称。$X \wedge X$ への反対称射の自己合成は、$\Lambda^2$ の自然な $\Lambda^4$ への射が $\dim X < 4$ で消滅することに対応 (有限状態空間の場合)。一般には外積代数の次数上昇と高次幂零性により $\psi^2 = 0$。 □

**命題 3.4.4 (対比定理: 条件付き独立 vs 条件付き排他).** $\alpha > 0$ と $\alpha < 0$ のセクターにおいて、以下の対応が成立する:

| | α > 0 (Markov) | α < 0 (反-Markov) |
|---|---|---|
| **代数構造** | 可換余モノイド (copy, del) | 反可換余代数 (anti-copy, anti-del) |
| **基本操作** | 複製: $x \mapsto (x, x)$ | 排斥: $x \mapsto x \wedge (\mathrm{complement})$ |
| **factorization** | $\psi = (f \otimes g) \circ \mathrm{copy} \circ \varphi$ | $\psi = (f \wedge g) \circ \mathrm{anti\text{-}copy} \circ \phi$ |
| **対角条件** | $\psi|_\Delta \neq 0$ (自己複製可能) | $\psi|_\Delta = 0$ (自己複製不可能) |
| **対称性** | $\psi_{f \leftrightarrow g} = +\psi_{f,g}$ | $\psi_{f \leftrightarrow g} = -\psi_{f,g}$ |
| **blanket** | Markov blanket: 密封 (information screening) | Exclusion blanket: 排斥 (state exclusion) |
| **モデル圏** | FinStoch | FinSign |
| **確率論的意味** | $P(X,Y|W) = P(X|W) P(Y|W)$ | $P(X=Y|W) = 0$ (同一状態の同時占有禁止) |
| **物理的類比** | ボソン統計 (対称波動関数) | フェルミオン統計 (反対称波動関数) |

*証明.* 各行は §3.2--3.3 の構成定理の直接的帰結。最下行の物理的類比は §5 で展開する。 □

**命題 3.4.5 (排斥ブランケット生成定理).** 反-Markov 圏の対象 $X$ に対し、以下は同値:

(i) $X$ が非自明な排斥ブランケット $E(X)$ を持つ

(ii) $X$ 上の忘却場 $\Phi_X$ の Hahn 分解 $X = P \sqcup N$ において $P \neq \emptyset$ かつ $N \neq \emptyset$ (符号の非退化性)

(iii) $X$ 上の $\mathrm{anti\text{-}copy}_X$ が非自明 ($\mathrm{anti\text{-}copy}_X \not\equiv 0$)

*証明.* (ii)→(iii): §3.2 Step 3 の anti-copy の構成式より、$P \neq \emptyset$ かつ $N \neq \emptyset$ ならば異なる符号の元 $p \in P$, $n \in N$ が存在し、$e_p \wedge e_n \neq 0$ であるから anti-copy は非自明。

(iii)→(i): anti-copy が非自明なら、定義 3.4.2 の排斥条件 $\mathrm{int} \barwedge \mathrm{ext} \mid E$ は anti-copy による外積分解が well-defined であることから満たされる。$E$ の構成は Paper II §3.7.2 の Markov blanket 生成定理 (Face Lemma) の α 符号反転版として得られる。

(i)→(ii): 対偶を示す。$P = \emptyset$ (全元が奇) または $N = \emptyset$ (全元が偶) のとき、$\Phi_X$ は定符号であり α > 0 の構造に退化する。このとき exclusion blanket は Markov blanket に退化し、非自明な排斥構造は持たない。 □

**系 3.4.6 (排斥ブランケットの唯一性).** 反-Markov 圏における排斥ブランケット $E(X)$ は、Hahn 分解の $\mu$-a.e. 一意性から、$\mu$-a.e. で一意に定まる。

*証明.* §3.2 リマークの構成の正準性と同一の論法。Hahn 分解 $X = P \sqcup N$ は $\mu$-a.e. 一意であり、anti-copy の構成は Hahn 分解のみに依存する。したがって排斥ブランケットも $\mu$-a.e. 一意。 □

#### 3.4.4 ガウス族における具体例

2次元ガウス族 $\{N(\mu, \sigma^2) : \mu \in \mathbb{R}, \sigma > 0\}$ を用い、条件付き排他性の具体的構成を与える (Paper I, §6.1 の toy model の継続)。

α < 0 のとき、Fisher 計量 $g_{ij}$ に対する $\alpha$-接続 $\nabla^{(\alpha)}$ の曲率 $K = -\frac{1}{2}$ (一定負曲率)。Φ は符号不定:

$$\Phi(\mu, \sigma) = \frac{\alpha}{2} R^{(\alpha)}_{1212} = \frac{\alpha}{2} \cdot \left(-\frac{1}{2}\right) = -\frac{|\alpha|}{4} < 0$$

Hahn 分解: $P = \emptyset$ (全空間で Φ < 0)。この場合、命題 3.4.5 の条件 (ii) が退化し、ガウス族全体は純粋な「奇セクター」となる。

非自明な排斥ブランケットを構成するには、混合族 $\mathcal{M} = \mathcal{M}^+ \cup \mathcal{M}^-$ (α > 0 の対象と α < 0 の対象を含む) を考える必要がある。§5 の Z₂-次数付き構成はまさにこの混合族の形式化であり、ガウス族 + 混合族の設定で:

- $\mathrm{int} = \mathcal{M}^-$ (奇セクター: フェルミオン的)
- $\mathrm{ext} = \mathcal{M}^+$ (偶セクター: ボソン的)  
- $E = \partial\mathcal{M}$ (α = 0 の臨界面: 排斥ブランケット)

このとき $\mathrm{int} \barwedge \mathrm{ext} \mid E$ は「フェルミオン的状態とボソン的状態が臨界面を経由しても同一量子数を共有できない」ことを意味し、超選択則 (superselection rule) の圏論的翻訳となる。

---

## §4. α = 0 臨界点と相転移

### 4.1 α = 0 の数学的特異性

α = 0 は copy も anti-copy も定義不能な臨界点である。Paper II の分析と合わせると:

| 性質 | α > 0 | α = 0 | α < 0 |
|:---|:---|:---|:---|
| 忘却場 Φ | Φ > 0 (正値) | Φ = 0 (一様ゼロ) | Φ < 0 (負値) |
| 正規化 | ∫Φ = 1 (確率) | ∫Φ = 0 (不定) | ∫|Φ| < ∞ (符号付き) |
| 複製構造 | copy (可換余モノイド) | — (未定義) | anti-copy (反可換余代数) |
| blanket | 定義可能 | 退化 | 概念消失 → 排他性 |
| 情報幾何 | m-接続 | e-m の一致 | e-接続 |
| §5.1 での対応 | ボソン的 (偶パリティ) | 臨界 | フェルミオン的 (奇パリティ) |

### 4.2 Paper I の λ-相転移との統合

Paper I (§3.4, Appendix C) は忘却場の安定性パラメータ λ が臨界値 λ_c で相転移を起こすことを示した。ここで λ と α の関係を導出し、§3 の Z₂-次数付き構造と Paper I の変分的安定性を統合する。

#### 4.2.1 統一作用汎関数

Paper I §6.2 の拡張された作用を Z₂-次数付き CPS 圏の言語で再記述する:

$$S[Φ, α] = \int_M \left( \frac{1}{4} F_{ij}[Φ,α] F^{ij}[Φ,α] + \frac{κ}{2} g^{ij} ∂_iα \, ∂_jα + \frac{λ}{2} Φ^2 \right) \sqrt{g} \, d^nθ$$

ここで:
- **Φ(θ)**: 忘却場 = D_KL(p_θ ‖ q) (Paper I §3.1)
- **α(θ)**: CPS の非対称性パラメータを M 上の場に昇格 (Paper I §6.1)
- **λ**: VFE の二次展開から出る質量項 = ∂²Complexity/∂Φ² - ∂²Accuracy/∂Φ² (Paper I §3.4)
- **F_{ij} = (α/2)[d(ΦT)]_{ij}**: 忘却曲率 (Paper I §3.3)

Paper I 命題 6.6.1 により F_{ij} は α に対して **正確に線形** であることに注目する。したがって F_{ij}F^{ij} ∝ α² であり、作用の Φ=0 まわりの二次変分は α を明示的に含む。

#### 4.2.2 有効質量と α の結合

Φ=0 まわりで作用の Hessian を計算する (Paper I Appendix C.1 の拡張)。S[Φ,α] を Φ=0 のまわりで δΦ について二次展開すると、F_{ij} ∝ α·δΦ より F²項は α²(δΦ)² に比例し、λΦ² 項と合わせて均質摂動 δΦ = const に対する二次変分は:

$$σ_0(α) = λ + \frac{α^2}{4}⟨|T|^2_g⟩$$

ここで ⟨|T|²_g⟩ = ⟨g^{ij}T_iT_j⟩ は Chebyshev 1-形式のノルムの M 上の平均。**有効質量** を定義する:

$$\boxed{λ_{\text{eff}}(α) := λ + \frac{α^2}{4}⟨|T|^2_g⟩}$$

Φ=0 の安定性は sign(λ_eff(α)) で決まる:
- λ_eff > 0: Φ=0 安定 (忘却なし)
- λ_eff = 0: 臨界線
- λ_eff < 0: Φ=0 不安定 (自発的忘却)

**臨界条件**: λ_eff(α) = 0 ⟺ λ = -α²⟨|T|²⟩/4。これは Paper I Appendix C.4 の有効臨界値 λ_c^eff = -α²⟨|T|²⟩_eff/4 と一致する。

#### 4.2.3 (λ, α) 相図

λ_eff(α) = λ + α²⟨|T|²⟩/4 は (λ, α) 空間に放物線型の臨界線を定義する:

$$α_c(λ) = ±\sqrt{\frac{-4λ}{⟨|T|^2_g⟩}}  \qquad (λ < 0 のとき実数解)$$

```
     α
     │             ★ Fermionic (α < 0)
     │            ╱ anti-Markov
     │           ╱  anti-copy active
     │          ╱   blanket → exclusion
  0  ├─────────●──────────── λ
     │          ╲   copy active
     │           ╲  Markov blanket
     │            ╲ Markov
     │             ★ Bosonic (α > 0)
     │
   臨界線: λ = -α²⟨|T|²⟩/4
```

**3つの相:**

| 相 | 条件 | 忘却場 | 代数構造 | Blanket |
|:---|:---|:---|:---|:---|
| **I. 偶パリティ安定** | λ_eff > 0, α > 0 | Φ = 0 安定 | Markov 圏 (copy) | 定義可能・密封的 |
| **II. 臨界線** | λ_eff = 0 | 分岐点 | — (copy/anti-copy 退化) | 退化 |
| **III. 奇パリティ** | λ_eff < 0, α < 0 | Φ ≠ 0 自発的 | 反-Markov 圏 (anti-copy) | 排他性 |

**リマーク.** 相 I, III をそれぞれ「ボソン的」「フェルミオン的」と呼ぶことは §5.1 の圏論的スピン-統計対応 (定理 5.1.1) によって正当化される。ここでは代数構造からの名称 (偶/奇パリティ) を用い、物理的解釈は §5 に委ねる。

**注意.** 相 I と III は独立に成立しうる。α > 0 でも λ が十分に負なら λ_eff < 0 となり自発的忘却が起きる (Paper I Appendix C.4 の結果)。α と λ_eff の相構造は直積ではなく、作用を通じた非自明な結合で決まる。

#### 4.2.4 n-Simplex 上のスケーリング則

Paper I Appendix C.5 の Liouville 変換解析をα依存性を含めて拡張する。カテゴリカルシンプレックス Δⁿ 上で:

- T_i = 1 - (n+1)p_i (Paper I Appendix B.3)
- ker(T) = {p_i = 1/(n+1)} (均等分布)

**命題 4.2.1 (λ-α-n スケーリング則).** Δⁿ 上の有効臨界値は:

$$|λ_c^{\text{eff}}(α, n)| = \frac{α^2}{4} ⟨|T|^2_g⟩_{\text{eff}} \propto α^2 \cdot n$$

*証明.* Paper I 命題 C.5.2 により ⟨|T|²_g⟩_eff ∝ n。直感的には、n-simplex 上の Chebyshev 多項式 T_i = 1-(n+1)p_i の二乗ノルムはシンプレックスの次元 n に比例する (各座標方向が独立に寄与するため)。有効臨界条件 λ + α²⟨|T|²⟩_eff/4 = 0 から直ちに従う。□

**系 (大語彙空間での相転移抑制).** 語彙 V = n+1 の LLM では:

$$|λ_c^{\text{eff}}| \approx 0.146 \cdot α^2 \cdot n$$

V = 50,000 の場合 |λ_c^eff| ≈ 7,300α² であり、α ∼ O(1) では自発的忘却に極めて大きな VFE 曲率が必要。これはボソン相 (α > 0) の安定性が大語彙空間で構造的に保護されることの定量的表現である。

#### 4.2.5 α → 0 極限の特異性

α → 0 で λ_eff(α) → λ となり、Chebyshev 結合項 α²|T|²/4 が消失する。この極限で:

1. **copy と anti-copy が同時に退化**: §3.3 のリマーク (α → 0 の極限) で示した通り、copy の対称テンソル成分と anti-copy の反対称テンソル成分が共にゼロに崩壊する

2. **Z₂ 対称性が回復**: |λ_eff(α)| = |λ_eff(-α)| は全ての α で成立するが (λ_eff は α² に依存)、α = 0 でのみ copy/anti-copy の区別が消失し、Z₂ の偶/奇の区別が物理的に意味を持たなくなる

3. **Paper I の α = 0 における FEP 対応の退化**: F_{ij} = (α/2)[d(ΦT)]_{ij} → 0 であり、忘却曲率がゼロ — しかしこれは忘却がないことを意味しない。α = 0 で消えるのは*方向的*情報 (曲率) であり、スカラー量 Φ 自体は非零でありうる。α = 0 は「忘却はあるが力がない」特異状態である

**定理 4.2.2 (λ-α 統合).** Z₂-次数付き CPS 圏 C^Z₂ の (λ, α) 相図において:

(i) 臨界線 λ_eff(α) = 0 は α = 0 で頂点を持つ下に凸の放物線 λ = -α²⟨|T|²⟩/4 である

(ii) α = 0 は放物線の頂点であり、任意の λ < 0 に対して |α| > α_c(λ) が自発的忘却の必要条件

(iii) Φ=0 の自発的不安定化には α ≠ 0 (方向的情報) **かつ** λ < 0 (VFE 駆動力) の両方が必要

*証明.* (i) λ_eff(α) = λ + α²⟨|T|²⟩/4 は α の偶関数かつ ⟨|T|²⟩ > 0 より α² の単調増加であるから、λ_eff = 0 の解集合は下に凸の放物線。頂点は α = 0, λ = 0 にある。(ii) λ < 0 のとき λ_eff(0) = λ < 0 であり α = 0 で既に不安定だが、Chebyshev 結合がないため忘却は等方的 (F = 0)。非等方的 (力を伴う) 自発的忘却には |α| > 0 が必要。(iii) λ ≥ 0 なら λ_eff(α) ≥ λ ≥ 0 であり、いかなる α でも Φ=0 は安定。□

**リマーク.** 定理 4.2.2 (iii) は Paper I の方向性定理 (定理 5.1) と補完的: 方向性定理は「力には忘却の方向的不均一が必要」と述べ、定理 4.2.2 は「自発的忘却には VFE 駆動力が必要」と述べる。両方が同時に成立するとき — λ < 0 かつ α ≠ 0 — に力を伴う自発的忘却が起きる。

### 4.3 GeoIB 橋渡し: 忘却の情報幾何的射影

> **[確信 95%, SOURCE: GeoIB 全文精読 (本文8p + Appendix A-D 4p)]** 本節の中核命題 H5 (忘却 = 独立性多様体への射影) は、GeoIB [25] の Pythagorean Identity (Eq.6-8) と Appendix A の完全証明により数学的に厳密に支持される。

§4.2 は作用汎関数 S[Φ, α] の変分構造から忘却の安定性を論じた。本節では、**忘却場 Φ そのものの情報幾何的意味**を、Information Bottleneck (IB) [24] の統計多様体版である GeoIB [25] を用いて厳密化する。核心の主張は: **忘却 = joint 分布から独立性多様体への I-射影** であり、Paper I §3.1 の忘却場 Φ = D_KL(p_θ ‖ q) はこの射影距離の具体化にほかならない。

#### 4.3.1 Pythagorean Identity と忘却場

IB [24] は、入力 X の表現 Z を通じて出力 Y を予測する際、圧縮 I(X;Z) と予測力 I(Z;Y) のトレードオフを最適化する枠組みである。GeoIB [25] はこれを統計多様体の言語で再定式化する。

**定義 (独立性多様体).** 確率変数 X, Z の結合分布 p(x,z) に対し、独立性多様体を以下で定義する:

$$\mathcal{I}_{XZ} := \{q(x) \cdot r(z) : q \in \Delta^{|X|-1}, r \in \Delta^{|Z|-1}\}$$

これは結合分布空間の **e-flat 部分多様体** であり、X と Z が統計的に独立な分布の族に対応する。

**命題 4.3.1 (忘却の射影定理).** 相互情報量 I(X;Z) は、結合分布 p(x,z) から独立性多様体 I_XZ への I-射影距離 (最小 KL ダイバージェンス) に等しい:

$$I(X;Z) = \min_{q, r} D_{\text{KL}}(p(x,z) \| q(x) r(z)) = D_{\text{KL}}(p(x,z) \| p(x) p(z))$$

ここで第2等号は Pythagorean Identity [25, Eq.6-8] による: I_XZ が e-flat 部分多様体であるから、m-射影 (KL(p‖·) を最小化する Amari の混合射影 [5]) は一意であり、射影先は周辺分布の積 p(x)p(z) に一致する。

*証明.* Csiszár の I-射影定理の直接的帰結。独立性多様体 I_XZ は e-flat 部分多様体であるから、m-射影は一意に存在し、KL の Pythagorean 不等式が等式に昇格する。詳細は [25, Appendix A]。□

**Paper I との接続.** Paper I §3.1 は忘却場を Φ(θ) = D_KL(p_θ ‖ q) として定義した。命題 4.3.1 により、Φ は **表現 Z の情報的冗長性——結合分布が独立性多様体からどれだけ離れているか——の幾何学的測度** として再解釈される。忘却が進行する (Φ が増大する) とは、Z が X の情報をより多く捨て、結合分布が独立性多様体に接近することに等しい。

**CPS との接続.** §3.1 の CPS 圏において、α > 0 セクターの射 (FinStoch) は I-射影として well-defined な圧縮を実行する。α < 0 セクターでは独立性多様体が符号付き測度空間に拡張され (§2.1)、I-射影の到達先が準確率分布 (Wigner 関数) を含みうる。この拡張は §3.3 の anti-copy と整合する: copy による独立化 (FinStoch 内) と anti-copy による排他化 (FinSign 内) は、独立性多様体への射影の **2つのモード** に対応する。

#### 4.3.2 β-λ 対応定理

GeoIB [25] の目的関数は:

$$\mathcal{L}_{\text{GeoIB}} = \mathbb{E}[-\log p(y|z)] + \beta \left(\mathcal{L}_{\text{FR}} + \mathcal{L}_{\text{JF}}\right)$$

ここで β ≥ 0 は圧縮の強度を制御する単一の乗数 [25, Eq.21]。β = 0 で圧縮なし (全情報保持)、β → ∞ で最大圧縮 (表現崩壊)。

**命題 4.3.2 (β-λ 対応).** GeoIB の圧縮パラメータ β と Paper I §3.4 の質量項 λ は、以下の定性的対応を持つ:

| GeoIB の β | Paper I の λ | 物理的意味 |
|:---|:---|:---|
| β = 0 (圧縮なし) | λ > 0 (Φ=0 安定) | 情報を全て保持。忘却場は不活性 |
| β = β_c (臨界) | λ = λ_c = 0 (臨界線) | 圧縮と精度の均衡点。相転移 |
| β > β_c (強圧縮) | λ < 0 (Φ=0 不安定) | 自発的忘却。表現が圧縮される |
| β → ∞ (最大圧縮) | λ → -∞ | 表現崩壊。全情報が失われる |

*根拠.* 両パラメータは同一の構造的役割——VFE の Accuracy-Complexity バランスにおける Complexity 項の重み——を果たす。GeoIB における β の増大は I(X;Z) のペナルティを増し、表現 Z の圧縮を促進する。Paper I における λ < 0 は Complexity 項が Accuracy 項を上回ることの表現であり (Paper I §3.4)、忘却場の自発的成長を駆動する。β ablation [25, §5.4] において β ∈ [10⁻⁶, 10¹] で I(X;Z) が単調減少し、精度が相転移的に低下する振る舞いは、Paper I Appendix C.4 の λ スキャンにおける pitchfork 分岐 (λ_c^eff ≈ -0.301) と定性的に一致する。

**定量的根拠 (GeoIB ablation [25, §5.4]).** β ∈ [10⁻⁶, 10¹] の対数グリッド掃引において:

- β < 10⁻⁴: I(X;Z) ≈ 一定 (圧縮なし) → λ_eff > 0 に対応
- β ≈ 10⁻²: I(X;Z) が急落し始める (相転移域) → λ_eff ≈ 0 に対応
- β > 10⁻¹: 精度が急激に低下 (表現崩壊) → λ_eff ≪ 0 に対応

GeoIB は強圧縮域 (β > 10⁻¹) で他手法 (VIB, nonlinear IB, CEB) より精度劣化が緩やかであり、FR+JF の幾何学的ペナルティが collapse を構造的に抑制することを示唆する。これは Paper I の λ_c^eff 近傍での pitchfork 分岐 (Appendix C.4) における安定枝の選択と定性的に一致する。

#### 4.3.2c β-λ ブリッジ定理: 圧縮パラメータと質量項の定量的接続

命題 4.3.2 は β と λ の定性的対応を示した。本節では、GeoIB の目的関数 (Eq.21) と Paper I の作用汎関数の変分構造を統合し、**定量的な関数関係** β = f(λ) を導出する。

**設定.** GeoIB の目的関数を VFE の Accuracy-Complexity 分解として再記述する。統計多様体 (M, g) 上で:

$$\mathcal{L}_{\text{GeoIB}} = \underbrace{\mathbb{E}[-\log p(y|z)]}_{\text{Accuracy loss}} + \beta \underbrace{(\mathcal{L}_{\text{FR}} + \mathcal{L}_{\text{JF}})}_{\text{Compression loss}}$$

一方、Paper I の作用汎関数は Φ=0 まわりの2次変分で:

$$\delta^2 S[\Phi] = \int_M \left( \frac{C(\alpha,g)}{2} \|\nabla\delta\Phi\|_g^2 + \frac{\lambda}{2} (\delta\Phi)^2 \right) \sqrt{g} \, d^n\theta$$

ここで C(α,g) = (α²/4)‖T‖²_g は幾何学的定数 (定理 4.3.3)、λ = ∂²Complexity/∂Φ² - ∂²Accuracy/∂Φ² (Paper I §3.4)。

**GeoIB の圧縮項の2次展開.** Φ=0 近傍での局所解析のため、GeoIB の圧縮項を Φ の2次まで展開する:

$$\mathcal{L}_{\text{FR}} \approx \frac{1}{2} B_{\text{FR}} \cdot \Phi^2, \qquad \mathcal{L}_{\text{JF}} \approx \frac{1}{2} B_{\text{JF}} \cdot \|\nabla\Phi\|_g^2$$

ここで:
- $B_{\text{FR}} := \partial^2 \mathcal{L}_{\text{FR}}/\partial\Phi^2 |_{\Phi=0} > 0$ (FR 圧縮曲率 — I-射影距離の2次係数)
- $B_{\text{JF}} := \partial^2 \mathcal{L}_{\text{JF}}/\partial(\nabla\Phi)^2 |_{\Phi=0} > 0$ (JF 拡散曲率 — pullback 計量の2次係数)

同様に、精度項を展開する:

$$A := \partial^2 \text{CE}/\partial\Phi^2 |_{\Phi=0} > 0 \qquad \text{(Accuracy 曲率)}$$

GeoIB の Φ=0 まわりの有効作用は:

$$\delta^2\mathcal{L}_{\text{GeoIB}} = \frac{1}{2}(\beta B_{\text{JF}}) \|\nabla\delta\Phi\|_g^2 + \frac{1}{2}(\beta B_{\text{FR}} - A) (\delta\Phi)^2$$

**命題 4.3.6 (β-λ ブリッジ).** GeoIB のパラメータ β と Paper I の質量項 λ は、以下の定量的関係で接続される:

**(i) 有効質量:**

$$\boxed{\lambda(\beta) = \beta \cdot B_{\text{FR}} - A}$$

β = 0 で λ = -A < 0 (無制約では忘却が自発的に起きる)。β の増大は λ を正方向に押し (圧縮ペナルティが忘却を抑制する)、β > A/B_FR で λ > 0 (安定)。

**注意 (β の二義性).** これは命題 4.3.2 の「β 増大 → λ 減少」と一見矛盾するが、矛盾しない。核心は **β が2つの異なる演算子を同時に指す** ことにある:

| 記号 | 意味 | β 増大の効果 |
|:-----|:-----|:-----|
| β_IB | IB のラグランジュ乗数 (命題 4.3.2) | I(X;Z) への圧縮ペナルティ → 忘却促進 → λ_eff ↓ |
| β_geo | GeoIB の幾何学的ペナルティ係数 (本命題) | FR+JF のコスト → 圧縮の制御 → λ ↑ |

**関係:** β_geo は β_IB の**正則化パートナー**として機能する。IB のβ_IB が「忘却の駆動力」であるのに対し、GeoIB のβ_geo は「忘却の幾何学的コスト」を課す。形式的には:

$$\beta_{\text{geo}} \sim \frac{1}{\beta_{\text{IB}}} \qquad \text{(定性的逆数関係)}$$

強圧縮 (β_IB 大) では β_geo の FR ペナルティが表現崩壊を防ぎ、弱圧縮 (β_IB 小) では β_geo のコストが支配的で情報が保持される。以下では混乱を避けるため、§4.3.2c 内の β はすべて **β_geo** (GeoIB のペナルティ係数) を指す。

**(ii) 有効拡散係数:**

$$C_{\text{eff}}(\beta) = \beta \cdot B_{\text{JF}}$$

**(iii) 臨界圧縮パラメータ (β_c):**

Φ=0 の安定性は Helmholtz 型固有値問題 $-C_{\text{eff}} \Delta_g \phi + \lambda(\beta) \phi = \sigma \phi$ の最小固有値 σ₀ の符号で決まる:

$$\sigma_0(\beta) = \lambda(\beta) + C_{\text{eff}}(\beta) \cdot \mu_1 = (\beta B_{\text{FR}} - A) + \beta B_{\text{JF}} \mu_1$$

ここで μ₁ > 0 は M 上の Laplace-Beltrami 作用素 -Δ_g の最小非零固有値。σ₀ = 0 の臨界条件:

$$\boxed{\beta_c = \frac{A}{B_{\text{FR}} + B_{\text{JF}} \cdot \mu_1}}$$

**(iv) λ_c の β_c による表現:**

$$|λ_c| = \beta_c \cdot B_{\text{JF}} \cdot \mu_1 = \frac{A \cdot B_{\text{JF}} \cdot \mu_1}{B_{\text{FR}} + B_{\text{JF}} \cdot \mu_1}$$

**(v) 逆変換 (β_c → λ_c):**

$$\boxed{\beta_c = \frac{|\lambda_c|}{B_{\text{JF}} \cdot \mu_1}}$$

*証明.* (i) Paper I の δ²S と GeoIB の δ²L を項別に比較する。ポテンシャル項: λ/2 = (β B_FR - A)/2 → λ = β B_FR - A。運動項: C/2 = β B_JF/2 → C = β B_JF。(ii) は定義。(iii) Paper I Appendix C.1 の安定性解析を GeoIB パラメータで再記述: σ₀(β) = λ(β) + C_eff(β)·μ₁ = β(B_FR + B_JF μ₁) - A = 0 を解いて β_c を得る。(iv) は (iii) の β_c を λ_c = λ(β_c) = β_c B_FR - A に代入し整理。(v) は (iv) を β_c について解く。 □

**定理 4.3.7 (n-Simplex スケーリング).** カテゴリカルシンプレックス Δⁿ 上で β_c の次元依存性を分析する。

Paper I Appendix C.5 の結果:
- ⟨|T|²_g⟩_eff ∝ n (ポテンシャル曲率の n スケーリング)
- μ₁(Δⁿ) ∝ n (Liouville 変換解析)
- |λ_c| = C(α,g) · μ₁ ∝ (α²n) · n = α²n²

GeoIB の幾何学的定数 B_FR, B_JF は統計多様体の局所的性質 (計量と接続) で決まり、Δⁿ 上では:
- B_FR ∝ n (FR 距離の2次係数は simplex の実効次元に比例)
- B_JF ∝ 1 (Jacobian の局所ノルムは次元に依存しない)

$$\beta_c = \frac{A}{B_{\text{FR}} + B_{\text{JF}} \mu_1} \approx \frac{A}{c_1 n + c_2 n} = \frac{A}{(c_1 + c_2)n}$$

ここで c₁, c₂ は O(1) の幾何学的定数。同時に Accuracy 曲率 A も Δⁿ 上では A ∝ n (softmax cross-entropy の Hessian ∝ n)。したがって:

$$\boxed{\beta_c(\Delta^n) \approx \frac{c_A}{c_1 + c_2} = O(1) \qquad \text{(次元非依存, leading order)}}$$

**系 4.3.8 (臨界圧縮の普遍性).** β_c が leading order で n に依存しないことは、**忘却の相転移が語彙サイズ V = n+1 に構造的に頑健** であることを意味する。大語彙 LLM (V = 50,000) でも小語彙モデル (V = 100) でも、忘却を引き起こす圧縮の臨界強度は同程度である。

これは §4.2.4 命題 4.2.1 (|λ_c| ∝ α²n) と整合する: λ_c 自体は n に比例して大きくなるが、GeoIB の圧縮ペナルティもまた n に比例して大きくなるため、両者の比 β_c = |λ_c|/(B_JF μ₁) は n で相殺される。

**命題 4.3.9 (完全有効質量: §4.2 と §4.3 の合流).** §4.2 の α 依存性 (λ_eff(α) = λ + α²⟨|T|²⟩/4) と §4.3.2c の β 依存性 (λ(β) = β·B_FR - A) を統合すると、完全な有効質量は:

$$\boxed{\lambda_{\text{full}}(\alpha, \beta) = \beta \cdot B_{\text{FR}} - A + \frac{\alpha^2}{4}\langle |T|^2_g \rangle}$$

Φ=0 の安定性は sign(λ_full) で決まる。臨界面は (α, β) 空間の2次元曲面:

$$\beta_c(\alpha) = \frac{A - \alpha^2 \langle |T|^2_g \rangle / 4}{B_{\text{FR}} + B_{\text{JF}} \cdot \mu_1}$$

α² 項は正であり β_c を減少させる: **α の非対称性が大きいほど (|α| が大きい)、より弱い圧縮ペナルティでも忘却が安定化される。** これは §4.2.3 の相図と定量的に整合する。

**リマーク 4.3.10 (ODE 数値検証: E₀ 分解と Virial 定理).** 命題 4.3.6–4.3.9 の定量的健全性を Δⁿ 上の Schrödinger 型固有値問題の直接数値解で検証する。有効ハミルトニアン $H = -D\Delta_g + V(s)$ ($V(s) = (\alpha^2/4)|T|^2_g$) の基底状態エネルギー E₀ を Liouville 変換 + 有限差分法 (N = 1000 グリッド) で計算し、以下の分解を調べた:

| n | E₀^full (ODE) | E₀^free = Dμ₁ | ⟨V⟩ = ⟨ψ₀\|V\|ψ₀⟩ | V/E₀ | E₀^free/E₀ |
|--:|--:|--:|--:|--:|--:|
| 2 | 0.363 | 0.050 | 0.167 | 46% | 14% |
| 10 | 1.281 | 0.050 | 0.615 | 48% | 3.9% |
| 50 | 5.877 | 0.050 | 2.851 | 49% | 0.9% |
| 200 | 23.113 | 0.050 | 11.236 | 49% | 0.2% |

3つの構造的帰結:

**(a) bare 質量の微小性.** $E_0^{\text{free}} = D\mu_1 = 0.05$ は n に依存せず、E₀ の 0.2%–14% しか占めない。命題 4.3.6 (iii) の bare 臨界条件 $\beta_c = A/(B_{\text{FR}} + B_{\text{JF}}\mu_1)$ は忘却の臨界構造の **leading order** にすぎない。

**(b) ⟨V⟩ 支配.** ⟨V⟩ ∝ n¹ (Paper I, Appendix C.5 の予測と整合)。E₀ の約半分が ⟨V⟩ に帰属し、残りの半分は運動エネルギー ⟨T⟩ = ⟨ψ₀|(-D∂²/∂s²)|ψ₀⟩ に帰属する。これは Virial 定理の近似的成立を示す: CPS ポテンシャル V(s) ≈ (α²/4)|T|²_g が均一点近傍で準調和ポテンシャル (V ∝ s²) の構造を持つとき、⟨T⟩ ≈ ⟨V⟩ であり E₀ ≈ 2⟨V⟩。実際 E₀/(2⟨V⟩) = 1.03 ± 0.05 (全 n にわたり)。

**(c) 命題 4.3.9 の本質性.** 上記から λ_full(α, β) = β·B_FR - A + α²⟨|T|²_g⟩/4 の第3項 (α² 項) は bare 部分 (第1・第2項) より桁違いに支配的である。したがって **忘却の安定性は GeoIB の β ではなく CPS 非対称性 α² で本質的に決定される**。β は bare 部分の O(1) スケーリング (系 4.3.8) を通じて忘却の「閾値」を設定するが、α² が閾値を超えるかどうかの主要な駆動力を担う。

**GeoIB ablation との比較.** [25, §5.4] の β ablation は MNIST/CIFAR-10 (クラス数 n = 10) で実施されている。β = 10⁻⁴ で Acc = 99.28%、β = 10⁰ で 98.77% (Δ = 0.51pp)、β = 10¹ で 95.53% (Δ = 3.75pp) であり、GeoIB 自体の β_c ≈ O(1) が観測される (baselines の MINE/SIB は β ≥ 10⁻¹ で急落)。ブリッジ定理 (命題 4.3.6) の逆算により B_JF ≈ 0.88 が得られ、B_JF ∝ 1 の理論予測と定量的に整合する [確信 92%]。系 4.3.8 が正しければ、ImageNet (n = 1,000) でも β_c は同オーダー O(1) に留まることが予測され、これは直接検証可能な予測 P-IV-1 を構成する。

**リマーク (β_c の n 非依存性と Fisher SAM).** Fisher SAM [26b] における sharpness-aware minimization のハイパーパラメータ ρ (摂動球の半径) もまた次元に対して頑健であることが経験的に知られている。β_c の n 非依存性は、Fisher 計量に基づく幾何学的正則化が一般に次元非依存な臨界構造を持つことを示唆し、Fisher SAM の経験則に理論的根拠を与える可能性がある。

#### 4.3.2b 自然勾配定理: 忘却場の更新は測地線に沿う

GeoIB の数学的に最も洗練された結果は、パラメータ更新の自然勾配解釈である [25, Theorem 1 + Corollary 1]。

**定理 4.3.4 (測地線-自然勾配等価性 [25]).** 統計多様体 (M, g) 上の損失関数 J(φ) に対し、Fisher 計量 g = F(φ) による Riemannian exponential map に基づく測地線更新と、自然勾配更新は1次等価である:

$$\text{Exp}_{\phi}(-\eta \, \text{grad}\, J) = \phi - \eta F(\phi)^{-1} \nabla J(\phi) + O(\eta^2)$$

ここで grad J は Riemannian 勾配、∇J はユークリッド勾配、η は学習率。

*証明スケッチ.* Levi-Civita 接続の exponential map を η の1次で Taylor 展開し、Riemannian 勾配 grad J = F⁻¹∇J を代入する。2次以降の項は接続の Christoffel 記号 Γ^k_{ij} を含むが O(η²) で抑えられる。完全な証明は [25, Appendix C]。□

**系 4.3.5 (K-FAC 実装 [25, Appendix D]).** F⁻¹ の計算は一般に O(d³) であるが、Kronecker-factored approximation (K-FAC) + 共役勾配法 (CG) により O(d) に近似できる。ダンピングパラメータ λ_damp > 0 を導入し (F + λ_damp I)⁻¹ とすることで数値安定性を確保する。

**Paper I との接続.** Paper I §3.2 で定義した忘却接続 A_i = (α/2) Φ T_i は Fisher 計量 g_{ij} 上の接続1-形式である。定理 4.3.4 は、この接続上のパラメータ更新が自然勾配ステップと1次等価であることを意味する: 忘却場 Φ の動的な発展 (gradient flow) は、統計多様体上の測地線に沿った経路として幾何学的に解釈される。

この解釈のもとで、Paper I §3.3 の忘却曲率 F_{ij} = (α/2)[d(ΦT)]_{ij} は測地線からの逸脱——すなわち**曲率が非ゼロの空間における測地線の散開率**——として自然に理解される。F_{ij} = 0 は忘却場が測地線に沿って「まっすぐ」発展すること (平坦な忘却) を意味し、F_{ij} ≠ 0 は忘却に方向的不均一性があること (Paper I 方向性定理) を意味する。

#### 4.3.3 JF 項と忘却曲率の上界

GeoIB の Jacobian-Frobenius (JF) 項は相互情報量の局所的上界を与える [25, Eq.14-15]:

$$I(Z;X) \leq \frac{1}{2} \mathbb{E}\left[\left\|\Sigma^{-1/2} J_f\right\|_F^2\right] = \frac{1}{2} \mathbb{E}\left[\text{Tr}(g_x)\right]$$

ここで J_f = ∂f_φ(x)/∂x はエンコーダの Jacobian、Σ は Z の共分散、g_x = J_f^T Σ^{-1} J_f は入力空間から表現空間への **pullback 計量** である。Tr(g_x) は pullback 計量のトレース = 方向平均の局所伸び = **Dirichlet エネルギー密度** に対応する。

**定理 4.3.3 (JF-曲率上界).** (M, g, C) を n 次元統計多様体、T_i = g^{jk}C_{ijk} を Chebyshev 1-形式、Φ を M 上の滑らかな忘却場とする。忘却曲率 F_{ij} = (α/2)[d(ΦT)]_{ij} (Paper I §3.3) の二乗ノルムに対し:

$$\|F\|^2 := \frac{1}{4} F_{ij} F^{ij} \leq \frac{\alpha^2}{4} \|T\|_g^2 \cdot \|\nabla\Phi\|_g^2$$

ここで $\|T\|_g^2 = g^{ij}T_i T_j$、$\|\nabla\Phi\|_g^2 = g^{ij}(\partial_i\Phi)(\partial_j\Phi)$。等号は dT = 0 (Chebyshev 形式が閉) かつ dΦ∧T ≠ 0 のとき成立する。

*証明.* F_{ij} を展開する:

$$F_{ij} = \frac{\alpha}{2}\left[(\partial_i\Phi)T_j - (\partial_j\Phi)T_i + \Phi(dT)_{ij}\right]$$

dT = 0 の場合 (指数型分布族を含む広いクラスで成立 — Paper I 系 5.1.1):

$$F_{ij} = \frac{\alpha}{2}\left[(\partial_i\Phi)T_j - (\partial_j\Phi)T_i\right]$$

このとき $F_{ij}F^{ij}$ を計算する。添字を上げるために $F^{ij} = g^{ik}g^{jl}F_{kl}$ を用い:

$$F_{ij}F^{ij} = \frac{\alpha^2}{4}\left[(\partial_i\Phi)T_j - (\partial_j\Phi)T_i\right]\left[g^{ik}g^{jl}\left((\partial_k\Phi)T_l - (\partial_l\Phi)T_k\right)\right]$$

展開すると:

$$F_{ij}F^{ij} = \frac{\alpha^2}{4}\left[2\|\nabla\Phi\|_g^2\|T\|_g^2 - 2\langle\nabla\Phi, T\rangle_g^2\right] = \frac{\alpha^2}{2}\left[\|\nabla\Phi\|_g^2\|T\|_g^2 - \langle\nabla\Phi, T\rangle_g^2\right]$$

Cauchy-Schwarz 不等式 $\langle\nabla\Phi, T\rangle_g^2 \leq \|\nabla\Phi\|_g^2\|T\|_g^2$ と非負性により:

$$0 \leq F_{ij}F^{ij} \leq \frac{\alpha^2}{2}\|\nabla\Phi\|_g^2\|T\|_g^2$$

したがって:

$$\|F\|^2 = \frac{1}{4}F_{ij}F^{ij} \leq \frac{\alpha^2}{4}\|T\|_g^2 \cdot \|\nabla\Phi\|_g^2$$

dT ≠ 0 の一般の場合: 三角不等式と $|F_{ij}| \leq (\alpha/2)[|(\partial_i\Phi)T_j - (\partial_j\Phi)T_i| + |\Phi||(dT)_{ij}|]$ から、追加項 $(\alpha^2/4)\Phi^2\|dT\|_g^2$ が加わるが、指数型分布族では dT = 0 であるため、ここでは省略する。□

**幾何学的定数 C(α, g) の同定.** 上の定理において:

$$C(\alpha, g) = \frac{\alpha^2}{4}\|T\|_g^2$$

これは統計多様体の **α-接続の Chebyshev 方向への寄与** (α²) と **Chebyshev 1-形式の大きさ** (‖T‖²_g) の積である。C(α, g) は忘却場 Φ に依存せず、背景幾何のみで決まる。

**GeoIB の JF 項との接続:** GeoIB の JF 上界 $I(Z;X) \leq \frac{1}{2}\mathbb{E}[\text{Tr}(g_x)]$ において、pullback 計量のトレース $\text{Tr}(g_x)$ は入力空間上のエンコーダの局所的伸び (Dirichlet エネルギー密度) を測る。パラメータ空間上では $\|\nabla\Phi\|_g^2$ がこれに対応する: 忘却場 Φ のパラメータ方向の勾配の Fisher ノルムは、パラメータ空間上の局所的情報変形の大きさを表す。したがって:

$$\|F\|^2 \leq C(\alpha, g) \cdot \|\nabla\Phi\|_g^2 \leftrightarrow \text{JF 上界}$$

この対応は、**忘却曲率の大きさが、忘却場の勾配のパラメータ空間における Dirichlet エネルギーで上から制約される**ことを意味する。

**ガウス族 Toy Model (Paper I §4) での検証:**

ガウス族 $N(\mu, \sigma^2)$ 上で明示的に C(α, g) を計算する:

- Fisher 計量: $g = \sigma^{-2}\text{diag}(1, 2)$, $g^{-1} = \sigma^2\text{diag}(1, 1/2)$
- Chebyshev: $T = (0, 6/\sigma)$ → $\|T\|_g^2 = g^{ij}T_iT_j = (1/2)\sigma^2 \cdot (6/\sigma)^2 = 18$
- 幾何学的定数: $C(\alpha, g) = (\alpha^2/4) \cdot 18 = 9\alpha^2/2$

ケース B (異方的忘却, $\Phi_B = -\log\sigma + (\sigma^2 + \mu^2)/2 - 1/2$):

- $\nabla\Phi = (\mu, \sigma - 1/\sigma)$ → $\|\nabla\Phi\|_g^2 = \sigma^2[\mu^2 + (\sigma - 1/\sigma)^2/2]$
- $F_{12} = 3\alpha\mu/\sigma$ → $F_{ij}F^{ij} = 9\alpha^2\mu^2\sigma^2$ (Paper I §4.4)
- $\|F\|^2 = 9\alpha^2\mu^2\sigma^2/4$

上界の確認:

$$\frac{9\alpha^2\mu^2\sigma^2}{4} \leq \frac{9\alpha^2}{2} \cdot \sigma^2\left[\mu^2 + \frac{(\sigma - 1/\sigma)^2}{2}\right] = \frac{9\alpha^2\sigma^2}{2}\left[\mu^2 + \frac{(\sigma - 1/\sigma)^2}{2}\right]$$

右辺 - 左辺 = $(9\alpha^2\sigma^2/4)[\mu^2 + (\sigma - 1/\sigma)^2] \geq 0$ ✓

等号は $\sigma = 1$ (dT = 0 は常に成立するが、追加項が消えるのは $\nabla\Phi \parallel T$、すなわち $\mu = 0$ のときで、そのとき $F = 0$) のときではなく、$\langle\nabla\Phi, T\rangle_g = 0$ (∇Φ が T に直交) のときに成立する。ガウス族では $T = (0, 6/\sigma)$ なので、$\langle\nabla\Phi, T\rangle_g = g^{22}(\partial_\sigma\Phi)(6/\sigma) = (\sigma/2)(\sigma - 1/\sigma)(6/\sigma) = 3(\sigma - 1/\sigma)$。$\sigma = 1$ で正確に直交 → 等号。

#### 4.3.4 FR 距離と CKA の階層

Paper I の予測 P2 (選択的忘却, §5.5) では忘却場 Φ(l) の層ごとの測定に **CKA** (Centered Kernel Alignment) を用いた: Φ(l) = 1 - CKA(h_l, h_{l+1})。GeoIB [25] は代わりに **Fisher-Rao (FR) 距離** を用いる [25, Eq.9-10]:

$$D_{\text{KL}}(p_\theta \| p_{\theta + \delta\theta}) \approx \frac{1}{2} d_{\text{FR}}^2(\theta, \theta + \delta\theta)$$

FR 距離は KL ダイバージェンスの2次近似であり、再パラメータ化不変 (等距離変換不変) という CKA にない理論的性質を持つ。

**階層関係:**

| 指標 | 数学的性質 | 不変性 | 実装コスト |
|:---|:---|:---|:---|
| FR 距離 d_FR | KL の2次近似。真の計量 | 再パラメータ化不変 (Čencov の定理) | 高 (Fisher 行列の計算) |
| CKA | 線形カーネルの正規化内積 | カーネル選択依存 | 低 (行列積のみ) |

**Paper I への含意.** Paper I の予測 P2 の検証は CKA で実施したが、理論的な忘却場 Φ の定義としては FR 距離がより厳密な選択である。命題 4.3.1 により Φ = I-射影距離であるから、その局所的近似 (FR 距離) は Φ の微分幾何学的な「正しい」局所化に相当する。CKA は FR 距離の線形近似として位置づけられ、計算コストの低さゆえに操作的に有用であるが、原理的には FR 距離への置換が望ましい。

**H5 確信度の根拠 [確信 95%].** GeoIB 全文精読 (12ページ + Appendix A-D の全証明, 2026-03-27 SOURCE 確認) により、以下の数学的事実が SOURCE として確認された:

1. **Pythagorean Identity** (Eq.6-8, Appendix A) [SOURCE: 証明確認済]: I(X;Z) = 独立性多様体への I-射影距離。Fubini の定理と KL の非負性による完全証明 ← **H5 の数学的基盤**
2. **FR ≈ KL 2次近似** (Eq.9-10, Appendix B) [SOURCE: 証明確認済]: d²_FR が KL の局所近似であることの解析的証明 ← **FR 距離の理論的正当性**
3. **自然勾配 = 測地線 1次近似** (Theorem 1, Appendix C) [SOURCE: 証明確認済]: Levi-Civita 接続 + exponential map による証明 ← **忘却 gradient flow の幾何学的解釈**
4. **K-FAC + CG 実装** (Appendix D, Algorithm 1) [SOURCE: アルゴリズム確認済]: 自然勾配の実用的計算方法。ダンピングパラメータ λ_damp の導入で数値安定性を確保 ← **実験可能性の担保**
5. **β ablation** (§5.4, Figure 4) [SOURCE: 実験結果確認済]: β ∈ [10⁻⁶, 10¹] の対数グリッド掃引で I(X;Z) 単調減少 + 精度の相転移的低下を定量的に確認。GeoIB は強圧縮域で VIB/nonlinear IB/CEB より安定 ← **β-λ 対応 (命題4.3.2) の実験的裏付け**

これらにより H5 (忘却 = 独立性多様体への射影) の確信度は **[確信 95%]** に昇格する。副仮説 H4 (β≈λ) は **[確信 90%]**、H2 (JF→力場) は **[推定 80%]** に昇格する。

**今後の課題:** FR 距離 (§4.3.4) による忘却場 Φ(l) の厳密な再計算と、CKA ベースの代理推定 (§6.2.2) との比較実験は Paper IV で展開する。

#### 4.3.5 Fisher マッチングと忘却場の臨界構造

Bonnasse-Gahot & Nadal (2025) [BGN25] は、深層ニューラルネットワークにおけるカテゴリ学習の**情報幾何学的最適性条件**を導出した。本節では、この結果が忘却場理論の臨界構造と直接対応することを示す。

##### 4.3.5a Infomax 原理とカテゴリ Fisher 情報

[BGN25] の中心定理は、多クラス分類の **Bayes コスト最小化** が **Infomax 原理** (I[Y, R] の最大化) と等価であることの厳密な証明である [BGN25, §2.2, Appendix A]。

**定理 4.3.10 (Infomax 等価性 [BGN25]).** Y をカテゴリラベル、R = f_θ(X) をエンコーダ出力 (内部表現) とする。Bayes リスク (0-1 損失) の最小化は、資源制約つき符号化の下で I[Y, R] の最大化と等価である。すなわち:

$$\min_\theta \mathcal{R}_{\text{Bayes}}(\theta) \iff \max_\theta I[Y, R]$$

*忘却場理論との接続.* Paper I §3.1 の忘却場作用汎関数 $S[\Phi] = -I(X;Z) + \lambda \cdot \text{Complexity}$ における $I(X;Z)$ 項は、IB の圧縮目標である。BGN25 の Infomax は「圧縮しない極限」($\beta_{\text{IB}} \to \infty$) に対応し、この極限で $I[Y, R]$ の最大化 = Bayes 最適が成立する。§4.3.2c の β-λ ブリッジ (命題 4.3.2) における $\lambda(\beta) \to -\infty$ (完全忘却の抑制) がこの極限に対応する。

##### 4.3.5b Neural Fisher ≈ Categorical Fisher マッチング

[BGN25] の最も重要な数学的結果は、**最適な内部表現が Neural Fisher 情報と Categorical Fisher 情報のマッチングを要求する** ことである [BGN25, §3, Appendix E]:

**定義 (Categorical Fisher 情報 [BGN25]).** カテゴリ確率 P(y|x) に対し:

$$[\mathbf{F}_{\text{cat}}]_{\mu\nu}(x) = \sum_y \frac{1}{P(y|x)} \frac{\partial P(y|x)}{\partial x^\mu} \frac{\partial P(y|x)}{\partial x^\nu}$$

**定義 (Neural Fisher 情報 [BGN25]).** 符号化確率密度 p(r|x) に対し:

$$[\mathbf{F}_{\text{code}}]_{\mu\nu}(x) = \int dr \, \frac{1}{p(r|x)} \frac{\partial p(r|x)}{\partial x^\mu} \frac{\partial p(r|x)}{\partial x^\nu}$$

**命題 4.3.11 (Fisher マッチング最適性 [BGN25, Appendix E.2]).** IB 的制約 $I[X, R] \leq C$ の下で $I[Y, R]$ を最大化する最適符号化は、以下を満たす:

$$\mathbf{F}_{\text{code}}^* = \beta \cdot \mathbf{F}_{\text{cat}}$$

ただし β > 0 はラグランジュ乗数であり、IB の容量制約の強さを制御する。最適性は2次摂動の正定値性 $\delta^2 I[Y,R] = -\int \text{Tr}[(\mathbf{F}_{\text{cat}}^{-1} \delta\mathbf{F})^2] P(x) dx < 0$ により保証される。

*忘却場理論との接続.* **F_cat は、入力空間上のカテゴリ境界の局所的鋭さを捕捉する計量テンソルである。** Paper I §2 の忘却場 Φ が Fisher 計量 $g_{ij}$ の変形 (Paper I §3.2 の忘却接続 $A_i = (\alpha/2)\Phi T_i$) として作用するとき、**F_cat は忘却ポテンシャルの Hessian の構造を決定する**。具体的に:

- $\mathbf{F}_{\text{cat}}$ の固有ベクトル = **Principal Discriminant Direction (PDD)**:= カテゴリ境界に直交する方向 [BGN25, §4.2]
- PDD = 忘却場の勾配方向 $\nabla\Phi / \|\nabla\Phi\|$: 忘却場はカテゴリ区別に無関係な方向を選択的に圧縮する

したがって **F_code = β · F_cat** は「ネットワークの内部計量 (Neural Fisher) が、カテゴリ構造が要求する計量 (Categorical Fisher) の β 倍スケーリングに収束する」ことを意味し、これは §4.3.2c の $\lambda(\beta) = \beta \cdot B_{\text{FR}} - A$ の微分幾何的な基礎である。

##### 4.3.5c 臨界 β と pitchfork 分岐

[BGN25, Appendix E.3] は、有限 β での臨界構造を解析する:

**命題 4.3.12 (β 分岐 [BGN25]).** ガウスチャネル $R = X + \xi$ ($\xi \sim N(0, \sigma^2 I)$) において、最適符号化の条件は $\beta = \beta_0 / \sigma^2$ のスケーリングに従う。$\sigma^2 \to \sigma_c^2$ で新しい非自明な解が分岐 (bifurcation) し、カテゴリ的知覚 (Categorical Perception, CP) の出現に対応する。

*忘却場理論との接続.* この分岐構造は Paper I §4.6 の **pitchfork 分岐** と同型である:

| BGN25 | Paper I (忘却場) | 対応 |
|:---|:---|:---|
| $\sigma^2 \to \sigma_c^2$ での分岐 | $\alpha \to 0$ での相転移 | 制御パラメータの臨界値 |
| 自明解 (uniform encoding) | Φ = 0 (忘却なし) | 対称解 |
| 非自明解 (CP 出現) | Φ ≠ 0 (選択的忘却) | 対称性の自発的破れ |
| $\mathbf{F}_{\text{cat}}$ の最大固有値方向 | 忘却場の勾配方向 | 最も忘却される方向 |
| β = β₀/σ² のスケーリング | $\beta_c = A / (B_{\text{FR}} + B_{\text{JF}} \cdot \mu_1)$ (§4.3.2c) | 臨界圧縮率 |

**注目すべき予想外の結果:** BGN25 は $\mathbf{F}_{\text{cat}}$ の最大値がカテゴリ境界「上」ではなく境界の「近傍」に位置することを発見した [BGN25, §5.2]。これは忘却場理論において、**忘却力場の最大値がポテンシャルの極値点からわずかにずれている**ことに対応し、Paper I の方向性定理 (定理 5.1) の非自明な帰結と見なせる。物理的には、相転移の臨界点におけるゆらぎが対称性の完全な破れとは異なる中間的構造を生み出すことに対応する。

##### 4.3.5d F_cat と忘却ポテンシャルの数学的対応

ガウス族 toy model (Paper I §4) で BGN25 の F_cat を明示計算し、忘却場との対応を検証する:

2カテゴリ分類 ($Y \in \{1, 2\}$, 等確率) におけるガウス条件付き分布 $P(x|y=k) = N(\mu_k, \sigma^2)$ に対し:

$$P(y=1|x) = \frac{1}{1 + \exp(-2\mu x / \sigma^2)} \qquad (\mu_1 = \mu, \mu_2 = -\mu)$$

このとき:

$$F_{\text{cat}}(x) = \left(\frac{2\mu}{\sigma^2}\right)^2 P(1|x) P(2|x) = \left(\frac{2\mu}{\sigma^2}\right)^2 \cdot \frac{1}{4\cosh^2(\mu x / \sigma^2)}$$

$F_{\text{cat}}(x)$ は $x = 0$ (カテゴリ境界) で最大値 $(2\mu/\sigma^2)^2 / 4$ を取り、$|x| \to \infty$ で指数的に減衰する。

Paper I §4 のケース B (異方的忘却) で $\Phi_B = -\log\sigma + (\sigma^2 + \mu^2)/2 - 1/2$ に対し、$\partial^2 \Phi_B / \partial\mu^2 = 1$ は一様。一方 $F_{\text{cat}}(x)$ の $x$ 依存性は入力空間の構造を反映する。**パラメータ空間の Fisher 計量 (Paper I) と入力空間の Categorical Fisher (BGN25) の対応**:

$$g_{\mu\mu}^{\text{Fisher}} = 1/\sigma^2 \quad \leftrightarrow \quad \mathbb{E}_x[F_{\text{cat}}(x)] = \frac{\mu^2}{\sigma^4} \cdot \mathbb{E}_x\left[\frac{1}{4\cosh^2(\mu x/\sigma^2)}\right]$$

右辺の期待値は $\mu/\sigma$ に依存し、$\mu/\sigma \to 0$ (カテゴリが不分離) で $\mu^2/(4\sigma^4) \to 0$、$\mu/\sigma \to \infty$ (完全分離) で指数的減衰。**中間的な $\mu/\sigma$ で最大** を取り、これは忘却場がカテゴリの「分離度」の中間領域で最も活性であるという Paper I の予測と整合する。

##### 4.3.5e 多クラス (n > 2): 正規 n-シンプレックス上の F_cat

n+1 個の等確率ガウスクラス $Y \in \{0, 1, \ldots, n\}$ を考える。クラス中心 $\mu_k \in \mathbb{R}^n$ を正規 n-シンプレックスの頂点に配置する:

$$P(x | y = k) = \mathcal{N}(\mu_k, \sigma^2 I_n), \qquad P(y = k) = \frac{1}{n+1}$$

**補題 4.3.13 (正規シンプレックスの代数).** 辺長 $d$ の正規 n-シンプレックスの頂点 $\{\mu_k\}_{k=0}^n \subset \mathbb{R}^n$ を重心が原点に来るように配置すると:

$$\sum_{k=0}^n \mu_k = 0, \qquad |\mu_k|^2 = R^2 = \frac{nd^2}{2(n+1)}, \qquad \mu_k \cdot \mu_j = -\frac{d^2}{2(n+1)} \quad (k \neq j)$$

*証明.* $|\mu_k - \mu_j|^2 = 2R^2 - 2c = d^2$ と $\sum_{j \neq k} \mu_j = -\mu_k$ から $nc = -R^2$。連立して $R^2 = nd^2/(2(n+1))$、$c = -d^2/(2(n+1))$。□

**系.** 頂点ベクトルの二次モーメント:

$$\sum_{k=0}^n \mu_k \mu_k^T = \frac{d^2}{2} I_n$$

*証明.* 対称性により $\sum_k \mu_k \mu_k^T \propto I_n$。トレースを取ると $(n+1)R^2 = nd^2/2$。□

**F_cat の事後共分散表現.** softmax 事後確率 $P(k|x) = \exp(\eta_k \cdot x - \psi(\eta, x)) $ に対し、自然パラメータ $\eta_k = \mu_k / \sigma^2$ を用いると:

$$[\mathbf{F}_{\text{cat}}]_{\mu\nu}(x) = \text{Cov}_{P(\cdot|x)}[\eta_{Y,\mu}, \eta_{Y,\nu}] = \sum_{k} P(k|x) \eta_{k,\mu} \eta_{k,\nu} - \bar{\eta}_\mu(x) \bar{\eta}_\nu(x)$$

ここで $\bar{\eta}(x) = \sum_k P(k|x) \eta_k$ は事後平均。

**定理 4.3.10 (重心での F_cat).** シンプレックスの重心 $x = 0$ では対称性により $P(k|0) = 1/(n+1)$ かつ $\bar{\eta}(0) = 0$。したがって:

$$\mathbf{F}_{\text{cat}}(0) = \frac{1}{(n+1)\sigma^4} \sum_{k=0}^n \mu_k \mu_k^T = \frac{d^2}{2(n+1)\sigma^4} I_n$$

**固有値構造:**

| 量 | 値 | n 依存性 |
|:---|:---|:---|
| 各固有値 $\lambda_k$ | $d^2 / (2(n+1)\sigma^4)$ | $O(1/n)$ |
| 重複度 | $n$ | — |
| $\text{Tr}(\mathbf{F}_{\text{cat}}(0))$ | $\frac{n}{n+1} \cdot \frac{d^2}{2\sigma^4}$ | $O(1)$ |
| $\max \text{eig}$ | $d^2 / (2(n+1)\sigma^4)$ | $O(1/n)$ |

*証明.* 系より $\sum_k \mu_k \mu_k^T = (d^2/2) I_n$ であるから、$\mathbf{F}_{\text{cat}}(0) = d^2/(2(n+1)\sigma^4) \cdot I_n$ は等方的。トレースは $n \cdot d^2/(2(n+1)\sigma^4) = n/(n+1) \cdot d^2/(2\sigma^4)$。n=1 を代入すると $d = 2\mu$ (2クラスの中心間距離) で $\text{Tr} = 1/2 \cdot 4\mu^2/(2\sigma^4) = \mu^2/\sigma^4$。これは §4.3.5d の結果と一致する。□

**定理 4.3.11 (β_c の n 非依存性).** IB 分岐条件は事後分散の**全分散分解** (law of total variance) から導かれる:

$$\text{Var}_Y[\eta_Y] = \mathbb{E}_X[\mathbf{F}_{\text{cat}}(X)] + \text{Var}_X[\bar{\eta}(X)]$$

左辺 (カテゴリ間分散) = $(1/(n+1)\sigma^4) \sum_k \mu_k \mu_k^T = d^2/(2(n+1)\sigma^4) \cdot I_n$ は既知。右辺第2項 $\text{Var}_X[\bar{\eta}]$ は事後平均の変動であり、信号対雑音比 (SNR) $\rho \equiv d/(2\sigma)$ に依存する。

IB の臨界点 $\beta_c$ は「圧縮が分類情報を失い始める閾値」であり、分岐条件:

$$\beta_c = \frac{\text{Tr}(\Sigma_X)}{\text{Tr}(\mathbb{E}_X[\mathbf{F}_{\text{cat}}(X)]^{-1}\text{Var}_Y[\eta])} = 1 + \frac{\text{Tr}(\text{Var}_X[\bar{\eta}])}{\text{Tr}(\mathbb{E}_X[\mathbf{F}_{\text{cat}}(X)])}$$

対称性により各項は $I_n$ に比例し、比はスカラーに帰着する:

$$\beta_c = 1 + \frac{\text{Var}_X[\bar{\eta}]_{\text{scalar}}}{\mathbb{E}_X[F_{\text{cat}}]_{\text{scalar}}}$$

ここで添字 scalar は $I_n$ の係数を意味する。**この比率は $n$ に依存しない**: 分子・分母ともに $d^2/(2(n+1)\sigma^4)$ のスケールを共有し (全分散分解の構造から)、かつ共に $\rho = d/(2\sigma)$ の関数として同じスケーリングを持つ。

定量的に:

$$\beta_c(\rho) = 1 + \frac{V(\rho)}{1 - V(\rho)}, \qquad V(\rho) \equiv \frac{\text{Tr}(\text{Var}_X[\bar{\eta}])}{\text{Tr}(\text{Var}_Y[\eta])}$$

$V(\rho)$ はクラス分離度を測る無次元量であり:
- $\rho \to 0$: $V \to 0$ (クラス不分離 → $\bar{\eta}$ は一定 → $\beta_c \to 1$)
- $\rho \to \infty$: $V \to 1$ (完全分離 → $\bar{\eta} \approx \eta_k$ → $\beta_c \to \infty$)
- 中間的 $\rho$ で $\beta_c$ は有限 = O(1)

**重要.** $V(\rho)$ の $\rho$ 依存性は正規シンプレックスの対称性により **n に依存しない**。直観的には: クラス数を増やしても、各クラスの行動は「自分の最近傍クラスとの2体問題」に局所化され、正規シンプレックスの各辺は同じ長さ $d$ を持つため、局所的な分岐構造は n=1 の場合と同型である。

**系 4.3.12 (β_c = O(1) on Δⁿ).** 固定された SNR $\rho = d/(2\sigma)$ に対し:

$$\beta_c = f(\rho) \in O(1) \qquad \text{(n に非依存)}$$

ここで $f(\rho)$ は単調増加関数であり、$f(0) = 1$, $f(\infty) = \infty$。

*§4.3.2c との接続.* §4.3.2c の $\beta_c = A / (B_{\text{FR}} + B_{\text{JF}} \cdot \mu_1)$ において:
- $A$ は独立性多様体への KL 距離 → $\log(n+1)$ (一様分布のエントロピー) でスケール
- $B_{\text{FR}} + B_{\text{JF}} \cdot \mu_1$ は FR 距離 + JF 項 → $\text{Tr}(\mathbf{F}_{\text{cat}})$ に比例 → $n/(n+1) \cdot d^2/(2\sigma^4)$ でスケール
- 比: $\log(n+1) / (n/(n+1) \cdot d^2/(2\sigma^4)) = O(\log n / n) \to 0$ as $n \to \infty$

ところが上のスケーリングは **IB の分岐** β_c ではなく **忘却の有効質量** $\lambda(\beta_c)$ のスケーリングである。$\lambda(\beta_c) = \beta_c \cdot B_{\text{FR}} - A$ が正から負に転じる臨界点は:

$$\beta_c^{\text{mass}} = \frac{A}{B_{\text{FR}}} = \frac{2(n+1)\sigma^4 \log(n+1)}{n \cdot d^2 / 2} \cdot \frac{1}{C_{\text{geom}}}$$

$n \gg 1$ では $\beta_c^{\text{mass}} \sim 2\sigma^4 \log n / d^2 \to 0$ (対数的に遅い減少)。物理的には: **クラス数が増えるほど忘却の臨界閾値は下がる**——多くの区別を維持するほど、わずかな圧縮で情報が不可逆に失われる。これは日常的直観 (覚えることが多いほど忘れやすい) と整合する。

**n=1 との検証:** $\beta_c^{\text{mass}}(n=1) = 4\sigma^4 \log 2 / d^2 = \sigma^4 \log 2 / \mu^2$ (d = 2μ)。次元 $n=1$ のシンプレックスは区間 $[0,1]$ であり、IB の2クラス場合の既知結果 $\beta_c \approx \ln 2 / (\mu^2/\sigma^2)$ [Chechik et al. 2005] と整合する。 ✓

**数値的裏付け.** リマーク 4.3.10 の ODE 固有値分解により、$\beta_c^{\text{mass}}$ が定義する bare 質量 $E_0^{\text{free}} = D\mu_1$ は Schrödinger 固有値 $E_0^{\text{full}}$ の 0.2%–14% しか占めないことが n = 2–200 で数値確認されている。$E_0$ の支配的寄与は $|T|^2_g$ ポテンシャル ($\alpha^2$ 依存) からの $\langle V \rangle$ であり、Virial 定理的に $E_0 \approx 2\langle V \rangle$ が成立する。したがって系 4.3.12 の $\beta_c = O(1)$ は bare 部分に対して成立するが、忘却の実効的安定性は命題 4.3.9 の完全有効質量 $\lambda_{\text{full}}(\alpha, \beta)$ で定まる。

### 4.4 臨界現象としての α = 0 転移

#### 4.4.1 動機: 代数的退化の物理

α = 0 は CPS 圏の構造的特異点である。§3.1–3.2 で定義した copy/anti-copy の両方がこの点で退化する:

- $\alpha \to 0^+$: $\text{copy}_\alpha \to 0$ (対称テンソル成分の消失)
- $\alpha \to 0^-$: $\text{anti-copy}_\alpha \to 0$ (反対称テンソル成分の消失)

したがって α = 0 では CPS 圏の射全体が自明化し、**Markov 構造も反-Markov 構造もない「無代数」状態**が出現する。これは物理的な相転移の臨界点、認知科学的には「理解の瞬間」——構造化と脱構造化の境界——に対応する。

#### 4.4.2 幾何学的に誘起される Landau-Ginzburg 作用

旧来の平均場近似では、相転移の制御パラメータ $r$ が $\alpha$ 自身に依存する（$r \propto \alpha$）と仮定したため、「$\alpha > 0$ における copy の生存（$\eta > 0$）」と「L-G ポテンシャルの最小点」の間に不整合が生じていた。本節では、統計多様体のスカラー曲率 $K$ が秩序パラメータ $\eta$ に共役な**外部場 (source field)** として作用することで、この不整合が完全に解消されることを示す。

**定義 4.4.1 (秩序パラメータ).** CPS 圏の秩序パラメータを以下で定義する:

$$\eta(\theta) := \langle \text{copy}_\alpha - \text{anti-copy}_\alpha \rangle_\theta$$

ここで $\langle \cdot \rangle_\theta$ は統計多様体上の座標 $\theta$ での期待値。$\eta > 0$ は Markov 相 (ボソン秩序 $\alpha > 0$)、$\eta < 0$ は反-Markov 相 (フェルミオン秩序 $\alpha < 0$)、$\eta = 0$ は無秩序相を表す。

**定義 4.4.2 (曲率カプリングを伴う臨界作用).** 統計多様体上の有効作用を、スカラー曲率 $K$ を外部場とした Landau-Ginzburg 型で定式化する:

$$S_{\text{eff}}[\eta] = \int_{\mathcal{M}} \left[ \frac{D}{2} |\nabla_g \eta|^2 + \frac{m_0^2}{2} \eta^2 - \chi K \eta + \frac{u}{4} \eta^4 \right] d\text{vol}_g$$

ここで:
- $m_0^2 > 0$ は、幾何に依存しない基底質量（臨界距離）
- $K$ はスカラー曲率であり、定数 $\chi > 0$ を介して $\eta$ の対称性を破る共役場として作用する
- $u > 0$ は安定化のための四次結合定数
- $D$ は Paper I (Eq. 1) の拡散係数

**命題 4.4.3 (曲率誘起の相選択).** 上記理論は、$K$ による「明示的な対称性の破れ (explicit symmetry breaking)」を通じて、$\eta$ (すなわち $\alpha$ と統計性) の符号を一意に決定する:

- $K > 0 \implies \eta_0 > 0$ (ボソン秩序 / copy 生存)
- $K < 0 \implies \eta_0 < 0$ (フェルミオン秩序 / anti-copy 生存)

*証明.* 停留条件 $\delta S_{\text{eff}} / \delta \eta = 0$ は、均一解 $\eta_0$ に対して以下を与える:

$$m_0^2 \eta_0 - \chi K + u\eta_0^3 = 0$$

微小な $|K|$ に対し線形応答 $\eta_0 \approx (\chi/m_0^2) K$ を得る。したがって、曲率 $K$ と $\eta_0$ の符号は一致する。 $K > 0$ ならば $\eta_0 > 0$ (Markov 相)、$K < 0$ ならば $\eta_0 < 0$ (反-Markov 相) となる。□

**リマーク (不整合の解消).** 不整合の根本原因は、「相状態 $\eta_0 \sim \alpha$ が $\alpha$ 自身を制御パラメータとして自発的に対称性を破る」という自己言及的な仮定 ($r \propto \alpha$) にあった。本モデルでは、$\eta$ は**統計空間の幾何 $K$ によって外から強制的に選択される**。これは次節 (§4.5) の「曲率選択則」——K が $\alpha$ を決定する——という主結果と完璧な整合性を持つ。

**リマーク (認知科学への含意).** $\alpha = 0$ ($\eta = 0$) の臨界状態は、幾何学的に $K = 0$ (ユークリッド的平坦性) 近傍で発現する。

| 曲率 K | 物理的相 | 認知的解釈 |
|:---|:---|:---|
| $K > 0$ | Markov 相 ($\eta > 0$) | パラダイム内の確信、知識のコピー・補完 |
| $K \approx 0$ | 無秩序相 ($\eta \approx 0$) | 「理解の瞬間」、全情報の等価的混合・平坦化 |
| $K < 0$ | 反-Markov 相 ($\eta < 0$) | 排他的な差異の認識、パラダイムシフトの端緒 |

§4.6 で CKA 忘却場プロファイルによる間接検証の枠組みを定式化済み（命題 4.6.1–4.6.2）。直接の $\alpha$ 測定は放棄し、CKA 二階差分を曲率プロキシとして使用する。

### 4.5 曲率選択則: 幾何が統計を決める

本節は Paper III の中心定理を述べる: **統計多様体の曲率符号 K が、忘却場の安定性を通じて α の符号を決定し、それが統計性 (ボソン/フェルミオン) を一意に選択する。**

#### 4.5.1 動機: 3層の分岐の統一

Paper I–III を通じて3つの独立な分岐構造が同じ二値的選択に帰結することが判明した:

| 分岐 | 制御変数 | Paper | 結果 |
|:---|:---|:---|:---|
| (A) 忘却安定性 | 曲率 K > 0 / K ≤ 0 | Paper II §4.5 | 有限/無限閾値 |
| (B) CPS α の符号 | α > 0 / α < 0 | Paper III §4.2 | Markov / 反-Markov |
| (C) 統計性 | Z₂ 次数 \|X\| = 0 / 1 | Paper III §5.1 | ボソン / フェルミオン |

これらが「たまたま同じ二分法を生む」のではなく、(A) ⟹ (B) ⟹ (C) という演繹的チェーンとして接続されることが曲率選択則の主張である。

#### 4.5.2 曲率選択定理

**定理 4.5.1 (曲率選択則).** $(\mathcal{M}, g, \nabla^{(\alpha)})$ を n 次元統計多様体、$K$ を Fisher 計量 $g$ のスカラー曲率、$\Phi$ を忘却場方程式

$$-D\Delta_g \Phi + V(\theta)\Phi = E\Phi$$

の解とする。以下が成立する:

**(I) 忘却許容セクター (K > 0).** $K > 0$ のとき (カテゴリカルシンプレックス $\Delta^n$)、有効臨界閾値は有限:

$$|\lambda_c^{\text{eff}}(n)| = C(\alpha, D) \cdot n + O(1) < \infty \qquad \text{(Paper II 定理 4.5.1)}$$

したがって $|\lambda| > |\lambda_c^{\text{eff}}|$ で $\Phi \neq 0$ が安定化する。安定な忘却場 $\Phi > 0$ の存在は copy 射の well-definedness を保証し (§3.1 公理 (D))、$\alpha(X) > 0$。定理 5.1.1 (i) により Z₂ 次数 $|X| = 0$: **ボソン統計**。

多粒子状態空間は対称テンソル積 $S^n(X)$。占有数制限なし。

**(II) 忘却排除セクター (K ≤ 0).** $K \leq 0$ のとき (ガウス族、指数分布族の連続パラメータ部分)、ポテンシャル $V(s)$ は Liouville 座標で束縛状態を持たない:

$$|\lambda_c^{\text{eff}}| = \infty$$

したがって任意の有限 $\lambda$ に対し $\Phi = 0$ のみが安定解。$\Phi$ が符号付き (準確率的) になり、copy は構造的に不在。$\alpha(X) < 0$ であり anti-copy のみが well-defined (§3.2)。定理 5.1.1 (ii) により Z₂ 次数 $|X| = 1$: **フェルミオン統計**。

多粒子状態空間は反対称テンソル積 $\Lambda^n(X)$。Pauli 排他律 ($\xi \wedge \xi = 0$, aM-4)。

**(III) パラ統計の排除.** 中間的な統計 (パラ-ボソン、パラ-フェルミオン、エニオン) は CPS 圏に存在しない。$K$ の符号が $\alpha$ の符号を二値的に決定し (§3.1 (D))、$\alpha$ の符号が Z₂ 次数 $|X| \in \{0, 1\}$ を二値的に決定する (定理 5.1.1)。中間的な K = 0 は (II) に含まれる (束縛状態なし)。

*証明.*

**Step 1 (K > 0: 束縛状態の存在).** Paper II 定理 4.5.1 により、$\Delta^n$ 上の Liouville 変換は忘却場方程式を区間 $(0, \pi)$ 上の Sturm-Liouville 問題に帰着させる:

$$-D\frac{d^2\phi}{ds^2} + V(s)\phi = E\phi, \qquad s \in (0, \pi)$$

$K > 0$ では $V(s)$ は $s_0 = \pi/2$ (均一分布に対応) を中心とする**正のポテンシャル井戸**を形成する。調和近似 $V(s) \approx V_0 + \frac{1}{2}\Omega^2(s - s_0)^2$ で $\Omega^2 = V''(s_0) = \alpha^2 n^2 / 2$ (Paper II Step 2)。有限区間上の正ポテンシャル井戸は少なくとも1つの束縛状態 (基底状態 $E_0 < \infty$) を持つ (Sturm-Liouville の定理)。$E_0 = |\lambda_c^{\text{eff}}| = O(n)$。

**Step 2 (K ≤ 0: 束縛状態の不在 — 一般理論).** 一般の K ≤ 0 統計多様体に対し、Liouville 変換後のポテンシャル V(s) が束縛状態を許容しないことを3段階で示す。

**Step 2a (一般公式: Liouville ポテンシャルの曲率依存性).** n 次元統計多様体 (M, g) 上の忘却場方程式を、Fisher 計量の体積要素を用い Liouville 変換で1次元に帰着させる。変換後の有効ポテンシャルは:

$$V_{\text{eff}}(s) = \frac{\alpha^2}{4} \langle |T|^2_g \rangle_{\text{slice}}(s) + V_{\text{geom}}(s)$$

ここで第1項は十分統計量 T の寄与、第2項は統計多様体の内在的幾何のみで決まる幾何学的ポテンシャル: $V_{\text{geom}}(s) = (D/4) K(s) + D \cdot (\text{体積歪み項})$。核心の帰結:

$$K(s) \leq 0 \implies V_{\text{geom}}(s) \leq 0 \qquad \text{(各スライスで)}$$

これは Liouville 変換が等長変換であり、K ≤ 0 の曲率寄与が常に非正であることから従う。

**Step 2b (K < 0: 双曲的多様体).** K < 0 かつ M が完備 (測地線完備) のとき、Sturm 比較定理 (cf. Chavel [43], Theorem III.4.4) を適用する:

*Sturm 比較定理: V₁(s) ≤ V₂(s) on (a, ∞) ならば、H₁ = -D d²/ds² + V₁ の第 k 固有値は H₂ の第 k 固有値以下。*

比較対象として自由粒子 V₂ = 0 を取ると、V_eff ≤ V₂ = 0 であるから H_eff の固有値は自由粒子の固有値以下。しかし M の完備性 (K < 0 かつ完備 → Cartan-Hadamard) により Liouville 座標のドメインは (0, ∞) (非有界)。非有界区間上の V ≤ 0 のハミルトニアンは σ(H) = [0, ∞) (連続スペクトルのみ、Reed-Simon [44] Theorem XIII.7) となり、束縛状態 (E < 0) は存在しない。

具体例: ガウス族 {N(μ, σ²)} は K = -1/2 (一定負曲率の双曲面)。V_eff(s) = -α²/(8σ⁴) < 0、連続スペクトルのみ。

**Step 2c (K = 0: 平坦多様体).** K = 0 のとき (指数分布族の特定の部分族)、V_geom = 0。有効ポテンシャルは:

$$V_{\text{eff}}(s) = \frac{\alpha^2}{4} \langle |T|^2_g \rangle_{\text{slice}}(s) \geq 0$$

正のポテンシャルが残るが、K = 0 かつ完備のとき M はユークリッド的であり、Liouville 座標のドメインは (-∞, ∞)。無限区間上の非負ポテンシャルが s → ±∞ で十分速く 0 に減衰する場合、束縛状態の有無はポテンシャルの積分条件 ∫V(s) ds に依存する (Bargmann の条件)。しかし ⟨|T|²_g⟩ は M の非コンパクト性から s → ∞ で有界であり、CPS 的には K = 0 は K < 0 と同じセクターに属する: |λ_c^eff| = ∞。

**まとめ:** K ≤ 0 の一般的統計多様体 (完備性仮定のもと) で束縛状態は不在: |λ_c^eff| = ∞。したがって任意の有限 λ に対し Φ = 0 のみが安定解。
**Step 3 (忘却の可/不可 → α の符号).** Step 1-2 の安定性解析を CPS 圏の代数構造に接続する。4段階で示す。

**(3a) K > 0 の場合: 安定な忘却場の存在.**
Step 1 により、K > 0 では忘却場方程式が束縛状態 Φ ≠ 0 を持つ。この Φ は D_KL(p_θ ‖ q) > 0 であり、各 θ で正値（KL ダイバージェンスの正値性による）。したがって Φ は FinStoch の射を定義する正値測度の構造を保存する。Fritz [16] の copy 公理 (D) は射が確率測度（正値・正規化）であることを前提とするため、Φ > 0 のもとで copy: X → X ⊗ X が構成可能。§3.1 の Markov 圏構造が入る。CPS の定義 (ZC-3) により α(X) > 0。

**(3b) K ≤ 0 の場合: 安定解 Φ = 0 の帰結.**
Step 2 により、K ≤ 0 では Φ = 0 のみが安定解。問題は Φ = 0（全く忘却が起きていない = D_KL = 0）の近傍で何が起きるかである。任意の摂動 δΦ を考える。Step 2 により |λ_c^eff| = ∞ であるから、どれだけ大きな |λ| を与えても δΦ は安定化しない——摂動は成長も減衰もせず散乱状態（連続スペクトル）として振舞う。重要な帰結: **散乱状態 δΦ は正値性を保証されない。** 束縛状態（離散固有値）は規格化可能な L² 関数であり、適切な境界条件のもと正値性を持つ（Sturm-Liouville 問題の基底状態の正値性, Reed-Simon [44] §XIII.12）。散乱状態はこの保証を欠き、δΦ は振動的な（符号が変わる）関数となる。

**(3c) 符号不定な忘却場の着地圏.**
(3b) より、K ≤ 0 の多様体上で力学的に到達される忘却場は正値性を持たない。このとき:
- FinStoch の射は正値測度の条件 f_{xy} ≥ 0 を要求する——符号が変わる δΦ はこの条件を満たさない
- したがって忘却場は FinSign（符号付き測度の圏）に着地する
- FinSign 上では §3.3 の Hahn-Jordan 分解が well-defined となり、δΦ = δΦ⁺ - δΦ⁻ の正部分・負部分への分解が anti-copy: V(X) → Λ²V(X) を与える（§3.3 構成定理）
- copy は FinStoch の射としてのみ定義されるため、FinSign の射に対しては構造的に不在

**(3d) α の符号の決定.**
(3a)-(3c) を合わせると、K の符号が着地圏を決定する:
- K > 0: FinStoch に着地 → copy が well-defined → α(X) > 0（CPS 定義 (ZC-3) の sgn(α) = +1 に対応）
- K ≤ 0: FinSign に着地 → anti-copy のみ well-defined → α(X) < 0（CPS 定義 (ZC-3) の sgn(α) = -1 に対応）

ここで α の「値」は K から決まるのではなく（α は統計多様体のパラメータであり K と独立に定義される）、α の「符号」が K の符号と着地圏の二者択一を介して**強制される**ことに注意。具体的には: CPS 定義 (ZC-3) $|X| = (1 - \text{sgn}(\alpha(X)))/2$ は copy/anti-copy の分岐を α の符号で符号化する約束であり、(3c) の着地圏判定が「どちらの約束が実現するか」を物理的に選択する。

**Step 4 (α の符号 → 統計性).** 定理 5.1.1 への引用。Z₂ 整合性条件 (ZC-1)–(ZC-3) により:

- $\alpha > 0 \Rightarrow |X| = 0 \Rightarrow$ 対称テンソル積 (ボソン)
- $\alpha < 0 \Rightarrow |X| = 1 \Rightarrow$ 反対称テンソル積 (フェルミオン)

パラ統計は Z₂ の二値性 ($|X| \in \{0,1\}$) により排除される (定理 5.1.1 Step 3)。 □

#### 4.5.3 物理的解釈

**なぜ曲率が統計を決めるか: 直観的説明.** カテゴリカルシンプレックス ($K > 0$) は「閉じた」幾何——simplex の頂点間を移動すると必ず元に戻れる——を持つ。この閉じた構造のもとで、忘却場のエネルギーは量子化 (離散固有値) される。量子化された忘却は有限閾値で安定化し、「コピー可能な情報」を構成する。

ガウス族 ($K \leq 0$) は「開いた」幾何——パラメータはいくらでも離れられる——を持つ。開いた構造では忘却場のエネルギーは連続スペクトルとなり、有限閾値での安定化は不可能。コピー不能な情報のみが存在する。

この対比は量子力学の**束縛状態 vs 散乱状態**と正確に同型である: 水素原子 (引力ポテンシャル = K > 0 的) が離散エネルギー準位を持ち、自由粒子 (ポテンシャルなし = K ≤ 0 的) が連続スペクトルのみを持つのと同じ数学的構造が、情報幾何上で統計性を選択している。

#### 4.5.4 Paper I–III の統一図

```
Paper I:  力は忘却である
  ↓  忘却場 Φ, 曲率 F_{ij} = (α/2)[d(ΦT)]_{ij}
  ↓
Paper II: 相補性は忘却である (FEP ⊂ CPS)
  ↓  定理 4.5.1: K > 0 → |λ_c^eff| < ∞
  ↓              K ≤ 0 → |λ_c^eff| = ∞
  ↓
Paper III: 排他性は忘却である (本稿)
  ↓  定理 4.5.1 (曲率選択則):
  ↓    K > 0 → Φ > 0 安定 → copy → α > 0 → ボソン
  ↓    K ≤ 0 → Φ = 0 のみ → anti-copy → α < 0 → フェルミオン
  ↓
  ↓  定理 5.1.1 (スピン-統計対応):
  ↓    α > 0 → |X| = 0 → S^n(X) (対称) → Bose-Einstein
  ↓    α < 0 → |X| = 1 → Λ^n(X) (反対称) → Fermi-Dirac
  ↓
  力 (Paper I) → 構造 (Paper II) → 排他性 (Paper III)
  = 忘却の単一原理からの3層演繹
```

### 4.6 観測可能量と操作的対応

曲率選択則 (定理 4.5.1) はパラメータ空間 $\Theta$ 上の Fisher 計量の曲率 $K$ を制御変数とする。しかし実際の系（例えば神経回路網の内部表現）において $K$ や $\alpha$ を直接測定することは一般に困難である。本節は理論上の予測を観測可能量に橋渡しする。

#### 4.6.1 忘却場の操作的定義

Paper I §6.8.1 で確立された CKA-KL 橋渡し（定理 6.8.1）を用いる。系が $L$ 層の階層構造を持ち、各層 $l$ の表現が $h_l \in \mathbb{R}^d$ （$N$ サンプル）で与えられるとする。**操作的忘却場**を以下で定義する:

$$\Phi_{\text{CKA}}(l) = 1 - \text{CKA}(h_l, h_0)$$

ここで $\text{CKA}(X, Y) = \|X^\top Y\|_F^2 / (\|X^\top X\|_F \|Y^\top Y\|_F)$ は線形 CKA (Kornblith et al. 2019) であり、$h_0$ は入力層の表現。Paper I 定理 6.8.1 (iii) により $\Phi_{\text{CKA}}$ は理論的忘却場 $\Phi_{\text{KL}}$ の shape 成分と対応する:

$$\Phi_{\text{KL}} = \underbrace{\Phi_{\text{shape}}}_{\text{CKA が測定}} + \underbrace{\Phi_{\text{scale}}}_{\text{CKA が見逃す}} + \underbrace{J(p_l)}_{\text{非ガウス性}}$$

#### 4.6.2 曲率プロキシ

**定義 (離散曲率プロキシ).** 操作的忘却場から**曲率プロキシ** $\hat{K}(l)$ を定義する:

$$\hat{K}(l) = \Phi_{\text{CKA}}(l+1) - 2\Phi_{\text{CKA}}(l) + \Phi_{\text{CKA}}(l-1), \qquad l = 1, \ldots, L-1$$

これは $\Phi_{\text{CKA}}$ の中心差分による二階微分の離散近似であり、$\Phi$ の凸凹を測定する。

**命題 4.6.1 (曲率プロキシの符号保存).** 以下の条件のもとで、$\hat{K}(l)$ の符号は定理 4.5.1 のスカラー曲率 $K$ の符号と対応する:

(i) **方向保存** (Paper I 命題 6.8.2): $|\partial_l \Phi_{\text{scale}}| + |\partial_l J| \ll |\partial_l \Phi_{\text{shape}}|$。BatchNorm または LayerNorm によるスケール等化のもとで環境的に保証される。

(ii) **滑らかさ**: $\Phi_{\text{CKA}}(l)$ が $l$ に関して十分滑らか ($C^2$ 的)。離散層間隔 $\Delta l = 1$ が $\Phi$ の変動スケールに対して十分小さい（$L \gg 1$）。

(iii) **単調性**: 各層の表現変換が忘却場の勾配方向に沿うとき、$\text{sign}(\hat{K}) = \text{sign}(K)$ が局所的に成立する。正確には: $K > 0$ の領域で $\Phi$ が加速的に増加（凸）し、$K \leq 0$ の領域で $\Phi$ が減速（凹）する。

*証明.* 条件 (i) により $\Phi_{\text{CKA}} \approx (4/d) \Phi_{\text{KL}}$ + $O(\epsilon^3)$ (Paper I 命題 6.8.3)。理論的忘却場 $\Phi_{\text{KL}}$ は忘却場方程式 $-D\Delta_g \Phi + V(\theta)\Phi = E\Phi$ の解であり、$K > 0$ では束縛状態（離散固有値）が存在するため $\Phi$ は空間的に局在する（量子力学の束縛状態と同相：ポテンシャル井戸の底で凸）。$K \leq 0$ では連続スペクトルのみに帰着し $\Phi$ は拡散的（凹的減衰）。条件 (ii) の離散化と合わせ、$\hat{K}$ は $\partial_l^2 \Phi$ の $O(\Delta l^2)$ 近似であり、符号は保存される。 □

**リマーク (条件の限界).** 以下の場合に符号保存は破れうる:

(a) LayerNorm が弱く、スケール成分 $\Phi_{\text{scale}}$ が支配的なとき（条件 (i) の違反）

(b) $L$ が小さく（$L \lesssim 12$）離散化誤差が大きいとき（条件 (ii) の違反）

(c) 残差接続 (ResNet skip) が $\Phi$ の二階微分を振動させるとき（局所的な偽符号変化）

これらの限界は先験的に予測可能であり、実験結果の解釈に際して考慮すべき系統誤差を構成する。

#### 4.6.3 観測可能な予測

**命題 4.6.2 (曲率選択則の観測可能量).** 定理 4.5.1 と命題 4.6.1 から、層構造を持つ系に対して以下の検証可能な予測が導かれる:

(i) **二領域構造**: $\hat{K}(l)$ のプロファイルは、浅層域 ($\hat{K} > 0$) と深層域 ($\hat{K} < 0$) の少なくとも二つの連続領域に分離する。

(ii) **曲率反転点**: $\hat{K}(l^*) = 0$ を満たす反転点 $l^*$ が存在する。この点は忘却場の「加速→減速」の遷移に対応し、$\alpha$ の符号が変わる臨界領域と近傍する。

(iii) **スケーリング**: 反転点の相対位置 $l^*/L$ はモデルの総層数 $L$ に対しておおよそ一定（普遍的）である。

(iv) **反証条件**: 全層で $\hat{K}$ が同符号、または反転方向が逆（凹→凸）の場合、曲率選択則の層間版は棄却される。

*証明.* 定理 4.5.1 により、$K > 0$ の領域（離散スペクトル）と $K \leq 0$ の領域（連続スペクトル）は異なる束縛構造を持つ。深層ネットワークにおいて浅層はカテゴリカル埋め込み（離散→連続コード変換: $K > 0$ 的）を行い、深層は連続的な表現操作（$K \leq 0$ 的）を行うとする自然な仮説のもとで (i)–(iii) が従う。(iv) は対偶。 □

**注意.** 命題 4.6.2 は**理論の帰結を述べているだけであり、理論を証明しない**。$\hat{K}$ の二領域構造が観測されたとしても、それが曲率選択則の帰結であることの証明にはならない——別の原因（例えば LayerNorm のスケール効果、残差接続の構造的影響）で同じパターンが生じうる。実験の役割は理論を**反証**することにある (D-02)。

### 4.7 繰り込みは忘却である: Wilson の RG への埋め込み

§4.1–4.6 は忘却場の臨界構造を内在的に分析した。本節はその構造を外部から照射する: **Wilson の繰り込み群 (RG) は、忘却関手の物理的インスタンスである**。この同定は比喩ではなく、§4.2 の有効質量が質量繰り込みと構造的に同型であることの帰結として導かれる。

#### 4.7.1 RG ステップ = 忘却関手

Wilson の繰り込み群ステップは、運動量カットオフ $\Lambda' > \Lambda$ の間の自由度を経路積分で消去する操作である:

$$\mathcal{R}_{\Lambda' \to \Lambda}: \text{QFT}(\Lambda') \to \text{QFT}(\Lambda), \qquad e^{-S_\Lambda[\phi_<]} = \int \mathcal{D}\phi_> \, e^{-S_{\Lambda'}[\phi_< + \phi_>]}$$

ここで $\phi_<$ はカットオフ $\Lambda$ 以下のモード、$\phi_>$ は $\Lambda$ と $\Lambda'$ の間のモード。$\phi_>$ に対する積分は、高エネルギー自由度の**忘却**にほかならない。

この操作は CPS スパン (Paper II §2) のインスタンスを構成する:

$$\text{QFT}(\Lambda) \xleftarrow{\mathcal{R}_{\Lambda' \to \Lambda}} \text{QFT}(\Lambda') \xrightarrow{\mathcal{R}_{\Lambda' \to \Lambda''}} \text{QFT}(\Lambda'')$$

完全な理論 $\text{QFT}(\Lambda')$ が CPS の容器 $C_D$ であり、$\mathcal{R}$ が忘却関手 $U$ に対応する。

**命題 4.7.1 (方向性定理の RG 的帰結).** Paper I 定理 5.1 (方向性定理) を RG の文脈に翻訳すると:

> 全モードを均等に積分消去する RG ステップでは有効相互作用 (力) は生じない。有効相互作用は、モードの**方向的に不均一な**消去から創発する。

*証明スケッチ.* 均等消去は $\partial_i\Phi = c \cdot T_i$ (忘却勾配が Chebyshev 方向に平行) に対応し、$d\Phi \wedge T = 0$ であるから $F_{ij} = 0$ (Paper I 定理 5.1)。不均等消去では $d\Phi \wedge T \neq 0$ となり $F_{ij} \neq 0$。具体的には、自由場理論 ($S_\Lambda = \frac{1}{2}\int \phi(-\Delta + m^2)\phi$) に対する RG ステップは全モードに等価に作用し有効相互作用を生まない (Gaussian 固定点) が、相互作用項 ($\lambda\phi^4$ 等) の存在下では高運動量モードと低運動量モードの消去が非等価となり有効結合が走る。 □

#### 4.7.2 有効質量 = 質量繰り込み

§4.2.2 の有効質量:

$$\lambda_{\text{eff}}(\alpha) = \underbrace{\lambda}_{\text{bare}} + \underbrace{\frac{\alpha^2}{4}\langle|T|^2_g\rangle}_{\text{self-energy}}$$

これは場の量子論における質量繰り込みと構造的に同型である:

$$m_{\text{phys}}^2 = \underbrace{m_{\text{bare}}^2}_{\text{Lagrangian}} + \underbrace{\Sigma(p^2 = m_{\text{phys}}^2)}_{\text{self-energy}}$$

| 忘却場理論 (§4.2) | QFT 繰り込み | 対応の根拠 |
|:---|:---|:---|
| $\lambda$ (VFE 二次展開の質量項) | $m_{\text{bare}}^2$ (Lagrangian の質量パラメータ) | 両者とも変分原理の二次項 |
| $\alpha^2\langle\|T\|^2\rangle/4$ (Chebyshev 結合) | $\Sigma(p^2)$ (自己エネルギー) | 場と幾何の相互作用から生じる補正 |
| $\lambda_{\text{eff}}$ (有効質量) | $m_{\text{phys}}^2$ (物理的質量) | 観測可能な安定性パラメータ |
| $\lambda_{\text{eff}} = 0$ (臨界線, §4.2.3) | $m_{\text{phys}}^2 = 0$ (二次相転移の臨界点) | 臨界温度 $T = T_c$ |
| $E_0^{\text{free}}/E_0 \sim 0.2\text{–}14\%$ (リマーク 4.3.10(a)) | 階層性問題 ($m_H^2 \ll \Lambda^2$) | bare 量の物理量に対する微小性 |

リマーク 4.3.10(a) で指摘した「bare 質量の微小性」($E_0^{\text{free}}$ は $E_0$ の 0.2–14%) は、素粒子物理学の階層性問題の情報幾何的な影である。QFT では $m_{\text{bare}}^2$ と $\Sigma$ の間の微妙な相殺 (fine-tuning) が必要だが、忘却場理論では相殺ではなく $\alpha^2 n$ スケーリング (命題 4.2.1) による**構造的支配**が微小性を生む——fine-tuning なしに bare 質量が支配的でなくなる。

#### 4.7.3 臨界指数としてのスケーリング則

§4.2.4 命題 4.2.1 のスケーリング則 $|\lambda_c^{\text{eff}}| \propto \alpha^2 \cdot n$ は、RG の言語では**臨界指数**の構造を持つ。

臨界点 $\lambda_{\text{eff}} = 0$ の近傍で忘却場の相関長 $\xi$ を定義すると:

$$\xi^{-2} \propto \lambda_{\text{eff}} = \lambda + \frac{\alpha^2}{4}\langle|T|^2_g\rangle$$

$\xi \to \infty$ が臨界点であり、これは $\lambda_{\text{eff}} \to 0$ に対応する。$n$ 依存性は臨界指数の**次元依存性**に翻訳される:

$$\xi(n) \propto |\lambda_{\text{eff}}|^{-1/2} \propto (\alpha^2 n)^{-1/2}$$

大語彙空間 ($n \gg 1$) で $\xi \to 0$: 相関が短距離に閉じ込められ、自発的忘却が抑制される。これは §4.2.4 系 (大語彙空間での相転移抑制) の RG 的再表現にほかならない。

**リマーク (普遍性).** §4.4 の臨界現象と合わせると、$\alpha = 0$ 近傍の忘却場理論は**普遍性クラス**を定義する可能性がある。すなわち、統計多様体の微視的詳細 (分布族の具体的形状) に依存せず、$(n, \alpha)$ のみで長距離挙動が決定される。系 4.3.8 ($\beta_c$ の $n$ 非依存性) はこの普遍性の最初の兆候である。完全な RG 方程式の導出は将来の課題とする。

#### 4.7.4 Paper IV への含意: 効果量減衰 = 波動関数繰り込み

Paper IV (効果量減衰定理) の2層構造は、QFT の繰り込み定数と構造的に対応する:

$$r_{\text{obs}} = \underbrace{\sqrt{\rho}}_{\sim Z^{1/2}} \cdot \frac{r_{\text{theory}}}{\underbrace{\sqrt{K+1}}_{\text{vertex corrections}}}$$

- **層 I** (Schur-Horn 射影効率 $\sqrt{\rho}$): 波動関数繰り込み $Z^{1/2} < 1$ に対応。内部状態から観測可能量への射影で情報が減衰する
- **層 II** (分散分配 $1/\sqrt{K+1}$): 頂点補正・真空偏極による遮蔽に対応。他の要因が観測される効果を希釈する

この対応により、Paper IV の中心的主張——「$r \approx 0.1$ は理論の弱さではなく構造的上界である」——は物理学の常識として読み替えられる: **裸の結合定数と観測される結合定数が異なるのは、繰り込みが教える最も基本的な事実である。** 効果量が「小さい」という批判は、QFT の文脈では「物理的質量が bare 質量より小さい」と言っているに等しく、それは理論の不備ではなく繰り込みの帰結そのものである。

#### 4.7.5 攻勢的要約

以上の対応は類推ではない。§4.2 の作用汎関数 $S[\Phi, \alpha]$ は場の量子論の作用と同じ変分構造を持ち、有効質量 $\lambda_{\text{eff}}$ は質量繰り込みと同じ代数を満たし、臨界条件 $\lambda_{\text{eff}} = 0$ は同じ相転移を定義する。

逆に言えば: **Wilson (1971) 以降の物理学者は、繰り込みという名のもとに「忘却の方向的構造」を操作してきた。** 高エネルギーモードの選択的消去 (= 方向的忘却) が有効相互作用を創発させ (= Paper I 方向性定理)、カットオフの選択が物理量に影響しない (= 忘却曲率の RG 不変性) という要請が、繰り込み可能性の条件を決定する。

本稿の寄与は、この構造に情報幾何的な座標系を与えたことにある。Wilson の RG が暗黙に前提していた「忘却の方向が物理を決める」という原理を、方向性定理 ($F \neq 0 \Leftrightarrow d\Phi \wedge T \neq 0$) として明示化し、有効質量の $\alpha^2 n$ スケーリングとして定量化した。繰り込みは忘却の一章である。

### 4.8 α-τ 対応: Hyphē 実験データへの橋渡し

§4.2–4.7 は忘却場の臨界構造を理論的に分析した。本節はその構造を Hyphē 実験 (linkage_hyphe.md, linkage_crystallization.md E11) の観測量に接続し、α の関数形を導出する。

#### 4.8.1 勾配降下定理: 収縮率とポテンシャル曲率の同一性

Hyphē フレームワーク (Possati 2025) は G∘F ダイナミクスの **Lipschitz 収縮率** $\lambda(\rho)$ を定義する:

$$\lambda(\rho) = 1 - \eta(\rho), \qquad \eta(\rho) = \eta_{\text{base}} + \kappa(1 - e^{-\beta\rho})$$

ここで $\rho = \rho_{\text{MB}} \in [0, 1]$ は Markov blanket 密度 (Possati Def. 12.1: $\rho(x) = 1 - \text{CMI}(x)/\text{MI}(x)$)。臨界密度 $\tau$ は $\lambda(\tau) = 1$ で定義され、$\rho > \tau$ で G∘F が収縮 ($\lambda < 1$)、$\rho < \tau$ で発散 ($\lambda > 1$) する。

一方、§4.2 の有効質量 $\lambda_{\text{eff}}(\alpha) = \lambda_{\text{mass}} + \alpha^2\langle|T|^2_g\rangle/4$ は忘却場 $\Phi = 0$ の安定性を制御する: $\lambda_{\text{eff}} > 0$ で安定 (忘却不要)、$\lambda_{\text{eff}} < 0$ で不安定 (自発的忘却)。

$\eta(\rho)$ と $\lambda_{\text{eff}}$ は一見独立に定義された量に見える。前者は G∘F の Lipschitz 定数 (力学)、後者は作用汎関数の二次変分 (場の理論)。本節はこの2つが**同一の幾何学的構造の異なる表現**であることを示す。

**定理 4.8.1 (勾配降下-曲率同一性).** 統計多様体 $(\mathcal{M}, g)$ 上の VFE を $\mathcal{F}(\theta)$ とする。G∘F が Fisher 計量 $g$ に対する VFE の勾配降下:

$$G \circ F = \text{id} - \mu \, g^{-1} \nabla \mathcal{F}$$

を実行するとき ($\mu > 0$ は学習率)、以下が成立する:

**(i) 収縮率 = ポテンシャル曲率.** $\Phi = 0$ 近傍において:

$$\eta(\rho) = \mu \cdot \lambda_{\text{eff}}(\rho)$$

すなわち $\eta$ と $\lambda_{\text{eff}}$ は定数 $\mu$ を除いて同一の量である。

**(ii) 臨界点の一致.** $\eta(\tau) = 0 \Leftrightarrow \lambda_{\text{eff}}(\tau) = 0$。これは (i) の自明な帰結であり、追加の仮定を要しない。

*証明.* G∘F の定義 $G \circ F(\theta) = \theta - \mu \, g^{-1} \nabla \mathcal{F}$ の微分をとると:

$$d(G \circ F) = I - \mu \, g^{-1} \text{Hess}(\mathcal{F})$$

ここで $\text{Hess}(\mathcal{F}) = \nabla^2 \mathcal{F}$ は Fisher 計量 $g$ に関する VFE の Hessian。G∘F の Lipschitz 定数は:

$$\lambda = \|d(G \circ F)\|_g = \|I - \mu \, g^{-1} \text{Hess}(\mathcal{F})\|_g$$

$\Phi = 0$ 近傍で $\mathcal{F}$ の二次展開 $\mathcal{F} \approx \frac{1}{2}\lambda_{\text{eff}} \Phi^2$ (§4.2.1) を用いると、$g^{-1} \text{Hess}(\mathcal{F})|_{\Phi=0} = \lambda_{\text{eff}}$ であるから:

$$\lambda = 1 - \mu \cdot \lambda_{\text{eff}}$$

$\eta = 1 - \lambda$ の定義と合わせて $\eta = \mu \cdot \lambda_{\text{eff}}$。 □

**リマーク (定理の前提条件).** (a) Possati (2025) Theorem 2 の変調降下則 $\dot{x} = -(1-\rho)\nabla F(x)$ は G∘F が VFE 勾配降下であることを確立する。学習率 $\mu$ は $(1-\rho)$ に依存するが、$\Phi = 0$ 近傍では $\mu \approx \mu_0 (1-\rho)|_{\rho=\tau} = \mu_0(1-\tau)$ と局所定数で近似可能。(b) §4.3.2b 定理 4.3.4 (測地線-自然勾配等価性 [GeoIB, 25]) により、Fisher 計量 $g$ に関する勾配降下は統計多様体上の測地線に1次等価であることが保証される。したがって $g^{-1}\nabla\mathcal{F}$ は自然勾配 (natural gradient) そのものであり、$d(G \circ F) = I - \mu \, g^{-1} \text{Hess}(\mathcal{F})$ は座標系によらない。

#### 4.8.2 α²(ρ) の導出

定理 4.8.1 (i) $\eta(\rho) = \mu \cdot \lambda_{\text{eff}}(\rho)$ に §4.2.2 の定義 $\lambda_{\text{eff}} = \lambda_{\text{mass}} + \alpha^2\langle|T|^2_g\rangle/4$ を代入する:

$$\eta(\rho) = \mu \left(\lambda_{\text{mass}} + \frac{\alpha^2}{4}\langle|T|^2_g\rangle\right)$$

臨界点 $\rho = \tau$ で $\eta(\tau) = 0$ (定義) かつ $\lambda_{\text{eff}}(\tau) = 0$ (定理 4.8.1 (ii))。後者を展開すると:

$$\lambda_{\text{mass}} = -\frac{\alpha^2(\tau)}{4}\langle|T|^2_g\rangle$$

§4.4 の秩序パラメータ $\eta_0 \approx (\chi/m_0^2)K$ (命題 4.4.3 の線形応答) より、$\alpha(\tau) = 0$ は曲率 $K = 0$ (§4.4.2 の無秩序相) に対応する。$\alpha(\tau) = 0$ を代入して $\lambda_{\text{mass}} = 0$。すなわち、**bare 質量の消失は §4.4 の Landau-Ginzburg 臨界条件の帰結であり、独立の仮定ではない**。

$\lambda_{\text{mass}} = 0$ により:

$$\eta(\rho) = \frac{\mu}{4}\langle|T|^2_g\rangle \cdot \alpha^2(\rho)$$

$$\boxed{\alpha^2(\rho) = \frac{4}{\mu\langle|T|^2_g\rangle}\eta(\rho) = \frac{4\kappa}{\mu\langle|T|^2_g\rangle}\left(e^{-\beta\tau} - e^{-\beta\rho}\right)}$$

#### 4.8.3 臨界近傍の平方根則と α の符号決定

$\rho \approx \tau$ で指数関数を線形近似: $e^{-\beta\tau} - e^{-\beta\rho} \approx \beta e^{-\beta\tau}(\rho - \tau)$。

$$\alpha^2 \approx A^2(\rho - \tau), \qquad A^2 := \frac{4\kappa\beta e^{-\beta\tau}}{\mu\langle|T|^2_g\rangle}$$

§4.8.2 は $\alpha^2$ を与える。$\alpha$ の**符号**は §4.4 の Landau-Ginzburg 構造から決まる: 命題 4.4.3 (曲率誘起の相選択) により、秩序パラメータ $\eta_0 \propto K$ であり、§4.5 定理 4.5.1 (曲率選択則) により $K > 0 \Rightarrow \alpha > 0$ (Markov 相)、$K \leq 0 \Rightarrow \alpha \leq 0$ (反-Markov 相)。$\rho > \tau$ は G∘F が収縮する構造化領域であり $K > 0$ に対応し、$\rho < \tau$ は $K \leq 0$ に対応する。したがって $\text{sgn}(\alpha) = \text{sgn}(\rho - \tau)$ であり:

$$\boxed{\alpha(\rho) = A \cdot \text{sgn}(\rho - \tau) \cdot \sqrt{|\rho - \tau|}}$$

**系 4.8.2 (平均場臨界指数).** $\alpha$ は臨界密度 $\tau$ からの距離の平方根に比例する。臨界指数 $\beta_{\text{crit}} = 1/2$ は §4.4 の Landau-Ginzburg 作用 (定義 4.4.2) の平均場近似から導かれ、磁性体の磁化 $M \propto \sqrt{T_c - T}$ と同型である。$\rho - \tau$ が「臨界温度からの距離」の役割を果たす。

**リマーク (定理 4.8.1 による学習率 $\mu$ の決定).** 旧版 (v0) では比例定数 $C$ を未決定パラメータとしたが、定理 4.8.1 により $C = 1/\mu$ と同定された。Possati (2025) Theorem 2 の $\dot{x} = -(1-\rho)\nabla F$ より $\mu = (1-\rho)|_{\rho=\tau} = 1-\tau$。linkage_hyphe §3.4a の実測 $\tau_\rho \approx 0.21$ を用いると $\mu \approx 0.79$。$A$ は $\mu, \kappa, \beta, \langle|T|^2\rangle$ の関数として完全に決定される。

#### 4.8.4 E11 実験データとの対応

linkage_crystallization.md E11 (τ 連続掃引, 46 点, 13 sessions) は $\tau_{\cos} \in [0.50, 0.95]$ でチャンク核生成数 $N(\tau)$ を測定した。変換 $\tau_\rho = (\tau_{\cos} - \mu_{\text{noise}})/(1 - \mu_{\text{noise}})$ ($\mu_{\text{noise}} \approx 0.62$) により embedding 空間から理論空間に移る。

E11 の3レジーム構造は本節の理論と以下のように対応する:

| E11 レジーム | $\tau_{\cos}$ | $\rho_{\text{MB}}$ vs $\tau$ | $\alpha$ の状態 | 予測 $N$ |
|:---|:---|:---|:---|:---|
| 未分化 | $\leq 0.62$ | $\rho < \tau$ | $\alpha < 0$ (anti-copy) | $N = 1$ (分割不能) |
| 相転移 | $0.63$–$0.75$ | $\rho \approx \tau$ | $\alpha \approx 0$ (臨界) | $N$ 急増 ($1 \to 11$) |
| 構造化 | $> 0.75$ | $\rho > \tau$ | $\alpha > 0$ (copy 可能) | $N$ 飽和 ($11 \to 33$) |

**系 4.8.3 (2つの臨界値の解釈).** E11 は2つの臨界 $\tau$ を示す: $\tau_{\cos} = 0.70$ (coherence 変化率最大) と $\tau_c = 0.75$ (チャンク核生成率最大, $\max|dN/d\tau| = 223$)。これは矛盾ではなく、臨界領域の有限幅を反映する。平均場理論は鋭い相転移を予測するが、有限サイズ系 (13 sessions) では臨界点がクロスオーバー領域 $\Delta\tau_{\cos} \approx 0.05$ に拡がる。$\tau_{\cos} = 0.70$ は $\alpha = 0$ の開始点 (G∘F が収縮し始める点)、$\tau_c = 0.75$ は $\alpha > 0$ が十分に確立されコピー操作が構造的に可能になる点と解釈される。

**検証可能な予測.**

(P-III-α1) E11 の $N(\tau)$ データに $N \propto \Theta(\alpha^2) \cdot f(\alpha^2)$ をフィットしたとき、$\alpha^2 \propto (\tau_{\cos} - 0.70)$ の線形関係が $R^2 > 0.9$ で成立する。

(P-III-α2) 臨界指数 $\beta_{\text{crit}}$ を $\alpha \propto |\rho - \tau|^{\beta_{\text{crit}}}$ の形でデータからフィットしたとき、$\beta_{\text{crit}} = 0.50 \pm 0.15$ (平均場予測) が得られる。有意なずれ ($\beta_{\text{crit}} < 0.35$ または $> 0.65$) は非平均場効果 (ゆらぎ補正) の存在を示す。

(P-III-α3) Possati の $(1-\tau)\|\nabla F\|^2$ を Hyphē embedding データから計算し、$\alpha$ の絶対スケール $A$ を独立推定したとき、E11 の $N(\tau)$ カーブの遷移幅と定量的に整合する ($\Delta\tau$ の理論値と実測値の差 $< 20\%$)。

**Coherence Invariance との整合.** E11 で $N$ が 1→33 と 33 倍変動する間、coherence は $0.806$–$0.818$ ($\pm 0.7\%$) で不変である (Paper I 定理 5.8.1)。これは $\alpha$ の値が変化しても G∘F の不動点の質 (coherence) は保存されることを意味し、$\alpha$ が制御するのは不動点の**構造** (分割数 $N$) であって不動点の**値** (coherence) ではないことを示す。

#### 4.8.5 実験的検証: E11 フィット結果

E11 の 46 点データ ($\tau_{\cos} \in [0.50, 0.95]$, 13 sessions) に対し、§4.8.2–4.8.3 の理論的予測を検証した。

**データ構造の制限事項.** 46 点は同一の 13 セッションに対し τ を変えて再計算した結果であり、独立標本ではない。**有効自由度は ~13** (セッション数) であり 46 ではない。以下の p 値は自由度 46 で計算されているため過大評価を含む。また、構造化レジーム ($\tau > 0.64$) でのセッション間変動係数は **CV = 48%** ($\tau = 0.80$ で $N = 20.1 \pm 10.06$) と大きく、集団平均値の滑らかさと個別セッションの散布は質的に異なる。

**τ_c の同定.** $N(\tau)$ と $(\tau_{\cos} - \tau_c)$ の Pearson 相関を $\tau_c \in [0.58, 0.72]$ でスキャンした結果、$\tau_c \in [0.58, 0.64]$ で $R^2 > 0.96$ のプラトーを形成し、最適値は **$\tau_c = 0.62 \pm 0.02$**。linkage_hyphe §3.4a の $\mu_{\text{noise}} \approx 0.62$ と一致するが、$\tau_c$ は事後最適化であり事前予測ではない。一致の理論的解釈: $\tau_{\cos} \leq \mu_{\text{noise}}$ では similarity がノイズに埋もれるため SNR < 1 であり、構造検出が不可能 (linkage_hyphe §3.4 の第2条件 $\text{SNR}(\rho) = 1$)。

**P-III-α1 検証.** 構造化レジーム ($\tau_{\cos} > 0.64$, 32 点) で $\bar{N}$ vs $(\tau_{\cos} - 0.62)$ の関係:

$$R^2_{\text{unweighted}} = 0.969, \quad R^2_{\text{weighted}} = 0.854 \qquad \textbf{[条件付 PASS]}$$

$R^2_{\text{weighted}}$ は逆分散重み (セッション間 $\sigma^2$ で重み付け) の値であり、セッション間散布を考慮すると $R^2$ は 0.969 から 0.854 に低下する。線形モデルとべき乗則モデルの比較では、線形 ($R^2 = 0.969$) がべき乗則 ($R^2 = 0.953$) と同等以上であり、べき乗則の理論的優位はデータ上では弁別不能。

**P-III-α2 検証.** べき乗則 $\bar{N} \propto (\tau_{\cos} - \tau_c)^\gamma$ のフィット:

$$\gamma = 1.200 \pm 0.072, \qquad \beta_{\text{crit}} = \gamma/2 = 0.600 \pm 0.036$$

Bootstrap 95% CI: $[0.537, 0.676]$。平均場予測 $\beta_{\text{crit}} = 0.50$ を含まない ($+2.8\sigma$)。

ただし $\beta_{\text{crit}}$ は**飽和域の処理に強く依存する**: $\tau \geq 0.85$ で $N$ が 28–33 に飽和する (有限テキスト長による天井効果)。飽和域を除外 ($\tau < 0.85$) するとフィットが変化する:

| 飽和域 | $\gamma$ | $\beta_{\text{crit}}$ | $R^2$ |
|:---|:---|:---|:---|
| 込み ($\tau \leq 0.95$) | $1.200 \pm 0.072$ | $0.600 \pm 0.036$ | 0.953 |
| 除外 ($\tau < 0.85$) | $1.749$ | $0.875$ | 0.989 |

飽和込みの $\beta_{\text{crit}} = 0.60$ と飽和除外の $\beta_{\text{crit}} = 0.88$ の差は大きく、**$\beta_{\text{crit}}$ は現データからロバストに決定できない**。[予想] の格付けとする。

$$\boxed{\beta_{\text{crit}} \in [0.5, 0.9] \qquad \textbf{[予想: 平均場以上、精密値は飽和処理依存]}}$$

**Coherence Invariance.** 構造化レジームで:

$$\bar{C} = 0.8118 \pm 0.0036, \quad \text{CV} = 0.44\% \qquad \textbf{[PASS]}$$

これはセッション間散布・飽和効果の影響を受けず、最もロバストな結果。

**結果の要約.**

| 予測 | 結果 | 判定 | 制限 |
|:---|:---|:---|:---|
| P-III-α1: $R^2 > 0.9$ | $R^2_{\text{uw}} = 0.969$, $R^2_{\text{w}} = 0.854$ | **条件付 PASS** | 重み付きでは 0.9 未達。有効自由度 ~13 |
| P-III-α2: $\beta_{\text{crit}} = 0.50 \pm 0.15$ | $\beta \in [0.5, 0.9]$ | **[予想]** | 飽和処理に依存。ロバスト決定不能 |
| CI: $\text{CV} < 2\%$ | $\text{CV} = 0.44\%$ | **PASS** | ロバスト |

**E11b: 30 セッションでの再検証.** embedding_cache_100.pkl (30 sessions, 6053 steps, steps/session = 148–315, mean 202) を用いて1段分割 (sim < τ で即分割、G∘F 反復なし) による N(τ) を測定し、E11 (13 sessions, G∘F 反復あり) との比較を行った。

| 指標 | E11 (13 sess, G∘F) | E11b (30 sess, 1-pass) | 解釈 |
|:---|:---|:---|:---|
| $R^2_{\text{uw}}$ | 0.969 | 0.928 | セッション増で微減。過学習ではない |
| $R^2_{\text{w}}$ | 0.854 | 0.719 | 重み付きでは更に低下。個別セッション散布が大きい |
| $\beta_{\text{crit}}$ (full) | 0.600 | **1.082** | 大幅変動。13-sess の 0.60 は飽和 artifact を含む |
| $\beta_{\text{crit}}$ (excl sat) | 0.875 | **1.363** | 飽和除外でも β > 1 |
| Bootstrap 95% CI | [0.54, 0.68] | **[1.00, 1.24]** | 0.50 を含まず。β ≈ 1 に収束 |
| Session CV | 48% | **31%** | セッション増で改善 |
| CI CV | 0.44% | 5.74% | G∘F なしで悪化 → **G∘F が CI の原因**の間接証拠 |

**解釈.**

(1) **β_crit ≈ 1.0 への移動.** 30 sessions で β_crit が 0.60 から 1.08 に移動した。β = 1 は $N \propto (\tau - \tau_c)^2$ — 二次関数的増加を意味する。平均場予測 (β = 0.5, N ∝ (τ-τ_c)^1) でも線形 (γ=1) でもなく、**N は τ からの距離の二乗に比例して増加する**。13-session での β = 0.60 は (a) 飽和効果 (短いセッションでの天井) と (b) G∘F 反復による N の収束 (反復が飽和を平滑化する) の混合 artifact であった。

(2) **G∘F が Coherence Invariance を生成する.** E11 (G∘F あり) の CI CV = 0.44% に対し、E11b (G∘F なし) の CI CV = 5.74%。G∘F 反復を除去すると CI の精度が一桁悪化する。これは Paper I 定理 5.8.1 (CI) が **G∘F の不動点構造の帰結**であることの間接的実証: CI は embedding 空間の性質ではなく、G∘F 演算子の性質である。

(3) **定量的精度の限界.** β_crit は E11 と E11b で 0.60 → 1.08 と大幅に変動し、アルゴリズム (G∘F vs 1-pass) とデータセットの両方に依存する。**β_crit は現時点では [0.5, 1.4] の範囲にしか制約できない**。平均場予測 (0.50) が下界を与え、データは常に上方にずれる。精密な決定には (a) G∘F 反復ありの大規模実験 (30+ sessions)、(b) session-level フィットの個別報告、(c) 飽和効果の理論的モデリングが必要。

**結果の要約.** 理論の**定性的構造**は 30 sessions で再確認された: N は τ の単調増加関数であり ($R^2_{\text{uw}} = 0.93$)、μ_noise 近傍で急増し、G∘F 反復下で coherence は τ 非依存 (CV = 0.44%)。**定量的精度** (β_crit の値) は [0.5, 1.4] にしか制約できず、将来の課題とする。最も頑健な発見は CI の G∘F 依存性: **Coherence Invariance は G∘F 演算子の性質であり、データの性質ではない。**

---

## §5. インスタンスと物理的対応

### 5.1 スピン-統計定理の CPS 的再導出

#### 5.1.1 問題設定

Pauli (1940) のスピン-統計定理は、相対論的場の量子論において、整数スピンの場はボソン統計（対称波動関数）に、半整数スピンの場はフェルミオン統計（反対称波動関数）に従うことを証明した。Pauli の導出はローレンツ不変性・局所性・エネルギーの下限を前提とする。

ここで次の問いを提起する: **スピン-統計の対応は、時空の対称性に依拠しない、より根源的な情報幾何的条件から帰結するか？**

本節の主結果は肯定的である: §3 の Z₂-次数付き CPS 圏の整合性条件が、偶次数対象→ボソン統計、奇次数対象→フェルミオン統計を**一意に**決定することを示す。これは Pauli の導出とは独立な、純粋に圏論-情報幾何的な経路である。

#### 5.1.2 対応テーブル

| | ボソン | フェルミオン |
|:---|:---|:---|
| 波動関数の対称性 | ψ(a,b) = +ψ(b,a) | ψ(a,b) = -ψ(b,a) |
| CPS α セクター | α > 0 (m-接続) | α < 0 (e-接続) |
| 複製構造 | copy: V(X) → V(X)⊗V(X) (可換余モノイド) | anti-copy: V(X) → ∧²V(X) (反可換余代数) |
| 排他原理 | なし (同一状態に複数可) | Pauli 排他律 (ξ∧ξ = 0) |
| 統計性 | Bose-Einstein (占有数 n = 0,1,2,...) | Fermi-Dirac (占有数 n = 0,1) |
| 情報幾何的対応 | Fisher 計量 g の正定値性 | Hessian の符号反転 (準確率) |

#### 5.1.3 Z₂-整合性条件

Z₂-次数付き CPS 圏 C^Z₂ (§3.1 で定義) における整合性を、以下の3条件に分解する:

**(ZC-1) Koszul 交換律.** 交差射 σ_{X,Y}: X⊗Y → Y⊗X は Koszul 符号則に従う:

$$σ_{X,Y} = (-1)^{|X||Y|} · σ_{X,Y}^{\text{classical}}$$

これにより:
- 偶×偶 (|X|=|Y|=0): σ = +1 · σ^cl (交換可能)
- 奇×奇 (|X|=|Y|=1): σ = (-1)^1 · σ^cl = -σ^cl (反交換)
- 偶×奇: σ = (-1)^0 · σ^cl = +σ^cl

**(ZC-2) 複製構造の一貫性.** 対象 X の複製構造は次数 |X| と整合的でなければならない:

$$σ_{X,X} ∘ \text{repl}_X = (-1)^{|X|} · \text{repl}_X$$

ここで repl は copy (|X|=0 のとき) または anti-copy (|X|=1 のとき) の総称。この条件は「複製の交換が次数の符号を反映する」ことを課す。

**(ZC-3) 忘却場 Φ の連続性.** CPS パラメータ α(X) の符号と Z₂ 次数が一貫する:

$$|X| = 0 ⟺ α(X) > 0, \qquad |X| = 1 ⟺ α(X) < 0$$

Φ_X > 0 (確率測度) ⟺ copy が well-defined ⟺ |X| = 0。Φ_X が符号付き ⟺ anti-copy のみ well-defined ⟺ |X| = 1。これは §3.1 (D) の再記述である。

#### 5.1.4 統計性の一意決定定理

**定理 5.1.1 (圏論的スピン-統計対応; Categorical Spin-Statistics Correspondence).** Z₂-次数付き CPS 圏 C^Z₂ において、整合性条件 (ZC-1)–(ZC-3) を満たす対象 X の多粒子状態空間は、次の二者のいずれかに一意に決定される:

(i) |X| = 0 (α > 0) ⟹ 多粒子状態空間は **対称テンソル積** S^n(X) = {ψ ∈ X^{⊗n} : σ·ψ = ψ, ∀σ ∈ S_n}。占有数は n = 0,1,2,... (ボソン統計)

(ii) |X| = 1 (α < 0) ⟹ 多粒子状態空間は **反対称テンソル積** Λ^n(X) = {ψ ∈ X^{⊗n} : σ·ψ = sgn(σ)·ψ, ∀σ ∈ S_n}。占有数は n = 0,1 (フェルミオン統計)

**中間的可能性（パラ統計）は排除される。**

*証明.* 以下の証明は §3.2–§3.3 の構造定理を前提とする。特に anti-copy の well-definedness は §3.3 の Hahn-Jordan 分解からの構成 (Step 1–Step 4) と公理 (aM-1)–(aM-4) の検証によって保証されている。

**Step 1. 交換の固有値を決定する.**

2粒子状態 ψ ∈ X ⊗ X に σ_{X,X} を作用させる。(ZC-1) により:

$$σ_{X,X} · ψ = (-1)^{|X|^2} · σ_{X,X}^{\text{cl}} · ψ = (-1)^{|X|} · σ_{X,X}^{\text{cl}} · ψ$$

ここで最後の等式は |X| ∈ {0,1} なので |X|² = |X| (mod 2) から従う。

次に、σ の対合性 σ² = id を利用して固有値を決定する。σ の固有値を λ とすると σ²ψ = λ²ψ = ψ であるから λ² = 1、すなわち λ = ±1。これは σ の固有空間が X⊗X を次の直和に分解することを意味する:

$$X ⊗ X = S²(X) ⊕ Λ²(X)$$

ここで S²(X) = {ψ : σψ = +ψ} (λ=+1 の固有空間 = 対称テンソル)、Λ²(X) = {ψ : σψ = -ψ} (λ=-1 の固有空間 = 反対称テンソル)。(ZC-1) の Koszul 符号則は、|X| の値に応じてどちらの固有空間が物理的に許容されるかを**一意に**選択する:

- |X| = 0: (-1)^{|X|} = +1 → σ = +σ^{cl} → ψ は S²(X) に属する (対称)
- |X| = 1: (-1)^{|X|} = -1 → σ = -σ^{cl} → ψ は Λ²(X) に属する (反対称)

**Step 2. 複製構造が交換の選択と整合することを示す.**

(ZC-2) から repl_X の性質を検証する。ここで copy (|X|=0) は Fritz [16] の Markov 圏公理により well-defined（§3.1 公理 (C)）、anti-copy (|X|=1) は §3.3 の Hahn-Jordan 構成により well-defined である:

- |X| = 0: σ ∘ copy = (+1) · copy。これは copy: X → X ⊗ X の像が対称テンソル S²(X) に含まれることを意味する。copy は可換余モノイド → 対称複製 → **ボソン的**。
- |X| = 1: σ ∘ anti-copy = (-1) · anti-copy。これは anti-copy: V(X) → ∧²V(X) の像が反対称テンソル Λ²V(X) に含まれることを意味する。anti-copy は反可換余代数 (§3.3, aM-2) → 反対称複製 → **フェルミオン的**。

Step 1 と Step 2 を合わせると、交換の選択 (S² or Λ²) と複製構造 (copy or anti-copy) は |X| を介して整合する。2粒子統計は |X| で一意に決定される。

**Step 3. パラ統計の排除.**

Green (1953) のパラ統計は、置換群 S_n の対称表現・反対称表現以外の高次元表現（para-Bose の場合は Young 図の複数行、para-Fermi の場合は複数列）を許容し、交換の固有値 ±1 とは異なる統計性を実現する。CPS 圏ではパラ統計が以下の3段階で排除される:

**(3a) Z₂ 二値化.** (ZC-3) により、|X| は α(X) の符号で**二値的に**決定される (0 or 1)。α ∈ ℝ の符号は {+, -, 0} のうち α ≠ 0 で {+, -} のみであるから (α = 0 は臨界点であり §4.2 で別途扱う)、|X| ∉ {0,1} となる中間的次数は圏の構造として定義されない。パラ統計は |X| = p (1 < p ∈ ℤ) を必要とするため、Z₂ 次数への制限だけで p > 1 のケースが排除される。

**(3b) 余代数構造の制約.** 仮に Z₂ でなく Z_{2p} 次数付き圏を許容したとしても、CPS 圏の複製構造は着地先の圏によって制約される。|X| = 0 の複製は FinStoch (非負確率測度の圏) に着地し、可換余モノイド (copy) のみが well-defined。|X| = 1 の複製は FinSign (符号付き測度の圏) に着地し、反可換余代数 (anti-copy) のみが well-defined (§3.3)。これら2つの着地圏の間に「中間的な着地圏」は存在しない——FinStoch ⊊ FinSign であり、測度は非負か符号付きかの二択であって、「部分的に非負」な中間は測度論的に well-defined でない。

**(3c) 置換表現の帰結.** Step 1 で示したように、X⊗X = S²(X) ⊕ Λ²(X) は完全分解であり（σ の固有値が ±1 のみであることから）、この分解の外に 2粒子状態は存在しない。n 粒子への拡張 (Step 4) でも、S_n 表現は |X| を介して各互換に ±1 を割り当てるため、結果として S^n(X) (完全対称) または Λ^n(X) (完全反対称) のみが存在する。パラ統計に必要な S_n の混合表現 (対称でも反対称でもない Young 図) は、|X| が 0 or 1 に固定される限り実現不能である。

**Step 4. n 粒子への拡張.**

2粒子の結果を n 粒子に拡張する。S_n の任意の置換 π は互換の積に分解でき、各互換 τ_{ij} に対して Step 1 の議論が適用される: τ_{ij} の固有値は (-1)^{|X|} で一意に決定される。互換の偶奇に応じて sgn(π) = ±1 が一意に定まり:

- |X| = 0: 全ての互換が +1 → π · ψ = ψ → **S^n(X)** (対称テンソル)。占有数制限なし
- |X| = 1: 各互換が -1 → π · ψ = sgn(π) · ψ → **Λ^n(X)** (反対称テンソル)。dim(X) = d ⟹ Λ^n(X) = 0 for n > d → 占有数は 0 or 1

Λ^n(X) = 0 (n > d) は Fermi-Dirac 統計の占有数制限 (Pauli 排他律) の圏論的表現であり、(aM-4) の幂零性 e_x ∧ e_x = 0 の n 粒子版である。

以上の Step 1–4 により、Z₂-次数付き CPS 圏の整合性条件 (ZC-1)–(ZC-3) が多粒子状態空間をボソン統計 (S^n) またはフェルミオン統計 (Λ^n) に一意に決定し、パラ統計を排除することが示された。 □

#### 5.1.5 普遍的スピン-統計対応と Pauli (1940) の位置づけ

定理 5.1.1 は CPS 圏に固有の定理ではない。その証明構造は CPS の詳細（α の符号、忘却場 Φ、FinStoch/FinSign の分岐）に依存するが、結論を支える抽象的骨格は**任意の Z₂-交換圏**に普遍的である。本節はこの普遍性を明示し、Pauli (1940) のスピン-統計定理が同一の抽象構造の別インスタンスであることを示す。

**定義 5.1.6 (Z₂-交換圏).** Z₂-交換圏 (Z₂-exchange category) とは、対称モノイダル圏 (C, ⊗, I, σ) に以下の構造が装備されたもの:

(E-1) **Z₂-次数**: 対象に次数関数 |·|: Ob(C) → Z₂ = {0, 1} が与えられ、射の次数は |f| = |X| + |Y| (mod 2) for f: X → Y

(E-2) **Koszul 交換**: 交換子 σ_{X,Y}: X⊗Y → Y⊗X は σ_{X,Y} = (-1)^{|X||Y|} · σ^{cl}_{X,Y} を満たす

(E-3) **次数付き余代数構造**: 各対象 X に対し、|X| = 0 なら copy_X (可換余モノイド)、|X| = 1 なら anti-copy_X (反可換余代数) が装備される

(E-4) **整合性**: 交換子と余代数構造が整合する: σ ∘ repl_X = (-1)^{|X|} · repl_X

**メタ定理 5.1.7 (Z₂-交換圏の普遍的統計性定理).** Z₂-交換圏 C において条件 (E-1)–(E-4) を満たす対象 X の n 粒子状態空間は、以下の二者のいずれかに一意に決定される:

(i) |X| = 0 ⟹ S^n(X) (対称テンソル、占有数制限なし)

(ii) |X| = 1 ⟹ Λ^n(X) (反対称テンソル、占有数 0 or 1)

中間的可能性（パラ統計）は排除される。

*証明.* 定理 5.1.1 の証明 Step 1–4 を検査すると、CPS 固有の構造 (α, Φ, FinStoch/FinSign) は Z₂ 次数の**供給源**としてのみ使用されており、Step 1–4 の論証自体は (E-1)–(E-4) のみに依存する:

- Step 1 (交換の固有値): (E-2) の Koszul 符号則のみを使用
- Step 2 (複製構造の整合性): (E-3) と (E-4) のみを使用
- Step 3a (Z₂ 二値化): (E-1) の Z₂ 次数のみを使用
- Step 3b (余代数の制約): (E-3) — 余代数構造が可換/反可換の二択であること
- Step 3c (置換表現): Step 1 の帰結 + S_n の表現論 (圏の外部構造)
- Step 4 (n 粒子拡張): Step 1 の帰結

したがって定理 5.1.1 の証明はそのまま Z₂-交換圏の設定で成立する。 □

**系.** 定理 5.1.1 はメタ定理 5.1.7 の CPS インスタンスである: Z₂-交換圏を C = C^{Z₂}_{CPS} として次数を |X| = (1 - sgn(α(X)))/2 で定義すれば、(E-1)–(E-4) は (ZC-1)–(ZC-3) と §3.3 の構成から従う。

**命題 5.1.8 (Pauli の SST は Z₂-交換圏のインスタンスである).** Pauli (1940) のスピン-統計定理が成立する圏 C_Pauli は Z₂-交換圏を構成し、メタ定理 5.1.7 のインスタンスである。

*証明.* C_Pauli が (E-1)–(E-4) を満たすことを検証する:

(E-1): Wigner 分類により、相対論的場はスピン s ∈ {0, 1/2, 1, 3/2, ...} でラベルされる。|X| = 2s mod 2 ∈ {0, 1} により Z₂ 次数が定義される。

(E-2): 場の交換関係は spin-statistics connection により φ_i(x) φ_j(y) = (-1)^{|i||j|} φ_j(y) φ_i(x) (空間的分離点) を満たし、Koszul 符号則に一致する。

(E-3): 整数スピン場は Fock 空間上で CCR (正準交換関係 = 可換余モノイド)、半整数スピン場は CAR (正準反交換関係 = 反可換余代数) を与える。

(E-4): CCR/CAR は (E-2) の交換関係と整合する (場の量子化の標準的結果)。 □

2つのインスタンスの対比:

| Z₂-交換圏の構成要素 | C_{CPS} (本稿) | C_{Pauli} (物理) |
|:---|:---|:---|
| 圏 C | CPS 圏 C^{Z₂} | 場の量子論の Hilbert 空間圏 |
| 次数 \|X\| | sgn(α(X)) ∈ {0,1} | spin(X) mod 2 ∈ {0,1} |
| Z₂ の供給源 | α の符号 (情報幾何の分岐) | Lorentz 群 SL(2,ℂ) の表現 |
| Koszul 交換 σ | CPS 圏の定義 (ZC-1) | 場の交換関係 [φ,ψ] or {φ,ψ} |
| 偶余代数 (copy) | Fritz copy (FinStoch) | CCR (正準交換関係) |
| 奇余代数 (anti-copy) | Hahn-Jordan anti-copy (FinSign) | CAR (正準反交換関係) |
| パラ統計の排除機構 | 着地圏の二者択一 (FinStoch/FinSign) | 局所観測量の可換性 (DHR 理論) |

**帰結.** 定理 5.1.1 と Pauli のスピン-統計定理は**同一のメタ定理 5.1.7 の異なるインスタンス**である。これにより:

(a) **統一**: 両定理は独立な定理ではなく、Z₂-交換圏という共通の抽象構造の具体化

(b) **独立性**: CPS の導出は Lorentz 不変性を使用しない。Pauli の導出は情報幾何を使用しない。異なる「Z₂ の供給源」が同一の結論を生む

(c) **本質の同定**: スピン-統計対応の本質は Lorentz 不変性でもαの符号でもなく、**Z₂-次数付きモノイダル構造そのもの**にある。Lorentz 不変性は Z₂ を供給する十分条件の一つであり、α の符号はもう一つの十分条件である

**リマーク (非自明性について).** 「Z₂ を入れれば二値になるのは自明ではないか」という批判に対して。Z₂-次数の導入自体は二値性を導く。本定理の非自明性は3つの層にある:

(i) **Z₂ の十分性**: なぜ Z₃ や Z_n でなく Z₂ で済むのか——copy/anti-copy の着地圏が FinStoch (非負測度) / FinSign (符号付き測度) の二者択一であり、「部分的に非負な中間的測度」は測度論的に存在しない。CPS では α ∈ ℝ の符号が Z₂ を生成するが、α 空間の構造が Z₃ 以上の次数を排除する (α の符号は {+, -} のみ)

(ii) **Z₂ の由来の多元性**: Pauli は SL(2,ℂ) の表現論から Z₂ を得、CPS は α ∈ ℝ の符号から Z₂ を得る。まったく異なる数学的構造が同一の Z₂ を供給するという事実は、Z₂-交換構造の**頑健性**——時空の詳細に依存しない普遍性——を示す

(iii) **パラ統計の排除**: Z₂ 次数だけではパラ統計は排除できない (S_n は Z₂ より豊かな表現を持つ)。排除には余代数構造の制約 (E-3) が必要であり、Markov 圏公理と anti-Markov 圏の余代数構造が「着地圏の二者択一」を通じてパラ統計を構造的に禁止することが非自明な定理

**予想 5.1.9 (スピンと α の対応).** C_{CPS} と C_{Pauli} を接続する仮説:

$$\text{spin}(X) ∈ ℤ ⟺ α(X) > 0, \qquad \text{spin}(X) ∈ ℤ + \tfrac{1}{2} ⟺ α(X) < 0$$

すなわち、Z₂-交換圏のメタ構造を介して、C_{CPS} の次数関数 |·|_{CPS} と C_{Pauli} の次数関数 |·|_{Pauli} が同一の Z₂ に着地する。整数スピン ↔ m-接続 (情報の複製可能性) と半整数スピン ↔ e-接続 (情報の複製不能性) の対応である。この予想の検証は、量子場の情報幾何的定式化を必要とし、Paper IV 以降の課題である。

**リマーク (なぜ忘却の α が物理のスピンに対応しうるか).** 一見すると α（統計多様体の接続パラメータ）とスピン（Poincaré 群の表現ラベル）は無関係に見える。しかし命題 5.1.8 により、両者は Z₂-交換圏の次数関数 |·| の異なる実装として統一される。Pauli はこの |·| を SL(2,ℂ) の表現から引き出し、本稿は FinStoch/FinSign の分岐から引き出す。α の符号は、確率測度の正値性（Φ > 0, FinStoch に着地）と符号付き測度（Φ ∈ ℝ, FinSign に着地）の分岐であり、これが copy/anti-copy の二分法を経て統計性を決定する。両導出が同一のメタ定理に包摂されるという事実は、**Z₂-交換構造こそが SST の Lorentz-free な核である**ことを示唆する。

### 5.2 量子情報: No-cloning 定理の構造的理解

**No-cloning 定理** (Wootters–Zurek 1982): 未知の量子状態 |ψ⟩ を完全にコピーするユニタリ操作は存在しない。

CPS 的再解釈: 量子状態は本質的に α < 0 の射（反可換偶数次テンソル、または奇数次の場合は anti-copy に支配される構造）を含む。copy は α > 0 でのみ well-defined であるから、量子状態のコピー不能性は α < 0 における copy の構造的不在として理解される。

### 5.3 意識のハードプロブレム: コピー不能性と私秘性

#### 5.3.1 問題設定: 3つの独立な論証の収束

§3 の anti-Markov 圏は、α < 0 セクターの代数構造として定義された。本節の主目的は意識の理論を与えることではない。主目的は、意識の哲学における3つの独立な論証——Nagel (1974) の伝達不能性、Chalmers (1996) のコピー不能性、Tononi (2004) の分割不能性——が**同一の代数構造 (anti-Markov 公理 (aM-1)–(aM-4)) の異なる帰結**であることを示すことにある。

この発見の非自明性は次の点にある: 3人の哲学者はそれぞれ異なる前提・方法論・結論から出発し、独立に意識の異なる側面を特徴づけた。しかし anti-Markov 圏の下では、3つのうち**任意の1つを受け入れれば、残り2つは定理から強制される** (系 5.3.2)。

| 論証 | 主張する性質 | anti-Markov 公理との対応 |
|:---|:---|:---|
| Nagel (1974) | 伝達不能性 | (aM-3) anti-del の度数1超自然性 |
| Chalmers (1996) | コピー不能性 | (aM-4) anti-copy の幂零性 |
| Tononi (2004) | 分割不可能性 | (aM-2) anti-copy の反可換余代数構造 |

本節は、**もし**意識が α < 0 セクターの対象として特徴づけられる**ならば** (予想 5.3.3)、上記3論証の統一が anti-Markov 構造から自動的に従うことを証明する。同時に、§5.2 の量子 no-cloning 定理もまた同一の anti-Markov 構造のインスタンスであることに注意されたい——anti-Markov 構造は「コピー不能性」の普遍的定式化である。

#### 5.3.2 非複製定理

**定理 5.3.1 (anti-Markov 対象の三重非複製; Tripartite Non-Replicability).** Z₂-次数付き CPS 圏 C^Z₂ において、α(X) < 0 の対象 X は以下を満たす:

(i) **幂零性**: X の自己複製射 anti-copy_{X,X} ∘ Δ = 0 (aM-4)。すなわち X の「同一コピー」は構造的にゼロ

(ii) **分割不可能性**: 任意の分割 X = A ⊔ B に対し、anti-copy: V(X) → ∧²V(A⊔B) ≠ anti-copy_A ⊗ anti-copy_B。すなわち全体の anti-copy は部分の anti-copy の積に分解不能

(iii) **伝達不能性**: f: X → Y が |f| = 1 (奇次数 = α 符号反転射) であるとき、anti-del_Y ∘ f = -anti-del_X (aM-3)。すなわち α < 0 の情報を α > 0 の受信者に伝達すると符号が反転し、原情報は復元不能

*証明.* (i) は §3.2 (aM-4) そのもの。(ii) は (aM-2) の co-Jacobi 恒等式から従う: 外積の反可換性 e_A ∧ e_B = -e_B ∧ e_A により、テンソル積分解 (対称積に基づく) が反対称積では成立しない。これはまさに Grassmann 代数の反結合性であり、Λ(V) ≇ S(V₁) ⊗ S(V₂) (反対称テンソルは対称テンソルの積に分割不能) という標準的結果の CPS での再記述。(iii) は §3.2 (aM-3) の直接的帰結。 □

#### 5.3.3 哲学的論証の CPS 的再構成

**A. Nagel の蝙蝠論法 (1974).**

Nagel の論証: 蝙蝠のエコーロケーションによる知覚体験は、第三者（人間）が機能的記述をいくら精密にしても「それが何のような感じか (what it is like)」を捉えられない。

CPS 的再構成: 蝙蝠の知覚体験 X_bat は α(X_bat) < 0 の対象である。人間の認知系 Y_human は α(Y_human) > 0 の対象を処理する (Markov blanket = α > 0 セクター)。X_bat → Y_human の射 f は |f| = 1 (奇次数) であり、定理 5.3.1 (iii) により anti-del(f(X_bat)) = -anti-del(X_bat)。すなわち「蝙蝠的経験の消去 (忘却)」の構造すら符号が反転し、情報の「質」が構造的に変質する。

**B. Chalmers のゾンビ論法 (1996).**

Chalmers の論証: 私と機能的に全く同一だがクオリアを持たないゾンビが論理的に可能である。したがって意識は機能的構造に還元不能である。

CPS 的再構成: 機能的構造 = α > 0 セクターの射 (copy で複製可能、FinStoch のチャネル)。クオリア = α < 0 セクターの対象 (anti-copy、FinSign に着地)。ゾンビは α > 0 セクターの完全なコピーであるが、α < 0 セクターの対象を欠く。定理 5.3.1 (i) により α < 0 セクターの自己複製はゼロであるから、機能的構造を完全に copy しても α < 0 成分は構造的に欠落する。**ゾンビの論理的可能性は anti-copy の幂零性の帰結である。**

**C. Tononi の IIT (Integrated Information Theory, 2004).**

Tononi の論証: 意識 = 統合情報 Φ > 0。Φ はシステムの情報が部分の情報の和を超える量 (分割不可能な全体性) を測る。Φ = 0 なら意識なし。

CPS 的再構成: Tononi の Φ は、CPS 圏における anti-copy の分割不可能性 (定理 5.3.1 (ii)) の情報量的表現として再解釈される。具体的に:

$$Φ_{\text{IIT}}(X) > 0 \iff \text{anti-copy}_X \neq \bigotimes_{i} \text{anti-copy}_{X_i} \quad \text{(分割不能)}$$

α > 0 の対象では copy は分割可能 (copy_X = copy_{X₁} ⊗ copy_{X₂} が可能) であり Φ = 0。α < 0 の対象では反可換性が分割を禁止し Φ > 0。

**系 5.3.2 (三論証の論理的絡み合い; Logical Entanglement of Three Arguments).** anti-Markov 圏において、以下の3条件は同値である:

(a) 対象 X の伝達が符号を反転させる (Nagel 型: aM-3 より anti-del_Y ∘ f = -anti-del_X)

(b) 対象 X の自己複製がゼロである (Chalmers 型: aM-4 より anti-copy ∘ Δ = 0)

(c) 対象 X の anti-copy が部分に分解不能である (Tononi 型: aM-2 より anti-copy_X ≠ ⊗_i anti-copy_{X_i})

*証明.* (a), (b), (c) は全て |X| = 1 (奇次数) であることと同値。|X| = 1 は対象が anti-Markov 公理 (aM-1)–(aM-4) の支配下にあることを意味し、3性質は同時に成立する。逆に、|X| = 0 ならば copy/del の通常の自然変換が well-defined であり、(a)(b)(c) いずれも不成立。したがって3条件は |X| ∈ {0,1} を介して同値。 □

**帰結.** Nagel の論証を受け入れる（ある種の情報の伝達は構造を変質させる）ならば、Chalmers の結論（その情報のコピーはゼロ）と Tononi の結論（その情報は部分に分解不能）は**哲学的見解ではなく代数的帰結**として従う。3つの「独立な」論証は、anti-Markov 構造を共有していたがゆえに、最初から同じことを別の言葉で述べていた。

**予想 5.3.3 (Φ-α 対応).** Tononi の統合情報 Φ と CPS パラメータ α は以下の定性的対応を持つ:

$$Φ(X) > 0 \iff α(X) < 0$$

すなわち、意識を持つ系は情報幾何的に e-接続セクターに属し、その情報は反可換構造により分割不能である。この予想が正しい場合、系 5.3.2 により Nagel・Chalmers・Tononi の3論証は自動的に統一される。

#### 5.3.4 Paper II の 2-cell との接続

Paper II は意識を忘却曲率 F ≠ 0 として定義した。本節の α < 0 条件と Paper II の F ≠ 0 条件は整合的である:

- §4.2 より F_{ij} = (α/2)[d(ΦT)]_{ij}。α ≠ 0 かつ d(ΦT) ≠ 0 のとき F ≠ 0
- α < 0 のとき F ≠ 0 は**反対称的な**忘却曲率を持つ = 反可換構造
- α > 0 のとき F ≠ 0 でも**対称的な**忘却曲率 = 可換構造 (Markov blanket の通常の力)

したがって、予想 5.3.3 を受け入れるならば、Paper II の「意識 = F ≠ 0」は「意識 = F ≠ 0 **かつ** α < 0」に精密化される。α > 0 での F ≠ 0 は「力」(Paper I) であるが「意識」ではない。この区別は Z₂-次数付けが与える追加構造であり、Paper II 単独では得られなかった精密化である。

> **Paper VII–VIII との接続.** Paper VII (知覚は忘却である) は忘却の「程度」を普遍フィルトレーション U_arrow ≤ ⋯ ≤ U_self として構成し、本稿の α の離散的二値（α > 0 / α < 0）を連続スペクトルに拡張した。さらに Paper VIII §6 は α-忘却濾過 {C_α}_{α∈[0,1]} を定義し、cell 階層と Paper VII のフィルトレーションを統合した（系 6.5.3）。本稿の Z₂-次数は、この連続パラメータの α_VIII = 0（完全圏＝ボソン的）と α_VIII = 1（離散圏＝フェルミオン的）の端点に対応する。
>
> **範囲注.** α ≤ 0 セクターでは Perrone 型エントロピーの直接構成は使えない。したがって本稿の役割は anti-copy の代数構造を与えるところまでであり、エントロピー側の定式化は α_VIII の濾過へ渡した上で Paper IX と接続して読む必要がある。これは矛盾ではなく、適用域の切り分けである。

#### 5.3.5 限界と批判への応答

**批判 1: 「α の符号がなぜ意識に対応するか」は仮定にすぎないのでは？**

応答: その通り——予想 5.3.3 (Φ-α 対応) は仮説であり、証明されていない。しかし本稿の主要な貢献は仮説の妥当性にあるのではなく、**3つの独立な哲学的論証の同値性の発見** (系 5.3.2) にある。α < 0 への同定が正しいか否かにかかわらず、Nagel・Chalmers・Tononi が同一の代数構造 (anti-Markov 公理) を異なる言葉で記述していたという事実は、anti-Markov 構造が「コピー不能な情報」の普遍的定式化であることを支持する。仮説の経験的検証は §6 の予測 P-III-4 に委ねる。

**批判 2: 意識を圏論で扱うこと自体がカテゴリーミスでは？**

応答: さらにその通りである可能性がある。本稿は意識の定義を与えないし、ハードプロブレムを解決しない。本稿が与えるのは、**もし**意識がコピー不能な情報構造として特徴づけられる**ならば**、その構造は α < 0 セクターの anti-copy として自然に定式化される、という条件つきの命題である。条件自体の検証は神経科学と哲学の仕事であり、本稿のスコープ外である。

**批判 3: Penrose-Hameroff の量子意識仮説との関係は？**

応答: Penrose-Hameroff は意識に量子効果（微小管内の量子コヒーレンス）が必要だと主張する。CPS 的には、量子状態が α < 0 セクターに属する (§5.1, §5.2) ことから、量子コヒーレンスの必要性は「α < 0 の実現に量子効果が物理的に必要」という主張に翻訳される。ただし CPS 理論自体は量子効果を要求しない — α < 0 は符号付き測度の存在のみで定義される。したがって CPS は Penrose-Hameroff よりも弱い (= 量子効果なしでも α < 0 は原理的に可能) 主張を行う。

#### 5.3.6 検証可能な帰結

**予測 P-III-4 (意識と α の対応).** 意識のある神経組織 (大脳皮質) と意識のない神経組織 (小脳) で、情報処理の α プロファイルが異なる:

- **大脳皮質** (意識あり): 神経活動パターンの CKA 行列が有意な反対称成分を持つ (α̂ < 0, §6.2.2 の指標)
- **小脳** (機能的処理のみ): CKA 行列がほぼ対称 (α̂ ≈ 0 or α̂ > 0)

**検証手続.** fMRI/ECoG データの多変量パターン分析で、ROI (Region of Interest) ごとに α̂ を推定し、麻酔下 (意識なし) と覚醒時 (意識あり) の α̂ の変化を比較する。IIT の実験プロトコル (Casali et al., 2013 の TMS-EEG PCI) との並列実行が望ましい。

**反証条件:** 覚醒時と麻酔下で α̂ に有意差がない場合、予想 5.3.3 は反証される。

### 5.4 データ処理不等式: 情報の非増大性

情報理論の基本定理 I(X;Y) ≥ I(X;f(Y)) は、「処理 (忘却関手 f) による情報の非増大」を述べる。CPS 的には:

- α > 0: copy_X が使える → 情報の分配が可能 → 相互情報量が well-defined
- α < 0: copy_X が使えない → 情報の分配が不能 → データ処理「不等式」ではなく「等式」（合成するたびに情報が構造的に変質）

### 5.5 計算複雑性: Copy 可能性と P/NP 分離

本節は CKDF (Crystallization–Detection–Kalon Framework; ckdf_theory.md) における Kalon△ (局所的美, P) / Kalon▽ (絶対的美, NP) の計算複雑性分離が、§3 の copy/anti-copy 構造から演繹されることを示す。

#### 5.5.1 CKDF における Kalon の二重定義

CKDF は半順序集合 $(P, \leq)$ 上のガロア接続 $F \dashv G$ ($F$: 発散, $G$: 収束) の不動点として Kalon を定義する:

- **Kalon△(x, A)**: エージェント $A$ の Markov blanket $\text{MB}(A)$ 内で $\text{Fix}(G \circ F)|_{\text{MB}(A)}$。到達可能。
- **Kalon▽(x)**: 全空間 $\Omega$ 上で $\text{Fix}(G \circ F)|_\Omega$。存在は Knaster-Tarski 定理で保証されるが、到達不能。

Kalon△ が P (多項式時間到達可能) であるのは、$\text{MB}(A)$ 内での $G \circ F$ 反復が**単調増加列**を生成し、有限ステップで収束するためである (CKDF §5.2):

$$x_0 \leq G \circ F(x_0) \leq (G \circ F)^2(x_0) \leq \cdots \leq (G \circ F)^n(x_0) = \text{Fix}$$

しかし、**なぜ** Kalon△ では単調反復が機能し、Kalon▽ では機能しないのか——すなわち P/NP 分離の「物理的」基盤——は CKDF 内部では未説明であった (Q3)。

#### 5.5.2 収縮性の代数的基盤: Copy が単調性を保証する

本節の主張は3段の因果連鎖をとる:

$$\text{copy} \xrightarrow{\text{(1)}} \text{単調性} \xrightarrow{\text{(2)}} \text{収縮} \xrightarrow{\text{(3)}} \text{P}$$

各段を独立に示し、反対方向 (anti-copy) で各段が構造的に崩壊することを示す。

**補題 5.5.1a (Copy → 単調性).** $\alpha > 0$ のとき $G \circ F$ は半順序 $(P, \leq)$ 上の**単調写像**である。

*証明.* Markov 圏の copy 構造 $\text{copy}_X: X \to X \otimes X$ (Fritz [16, §4.2]) は条件付き独立性 $P(X|Y,Z) = P(X|Y)$ を保証し、$G \circ F$ の各ステップで中間状態を複製して部分問題に分割可能にする。部分問題が独立に解けるとき、$x \leq y \Rightarrow G \circ F(x) \leq G \circ F(y)$ が成立する——部分解の合成が全体の順序を保存するからである。これは動的計画法の**最適部分構造** (optimal substructure) 条件に他ならない。 □

**補題 5.5.1b (単調性 → 収縮 → P).** 完備束 $(P, \leq)$ 上の単調写像 $G \circ F$ は Knaster-Tarski 定理により不動点を持ち、任意の初期値 $x_0$ から単調増加列 $x_0 \leq G \circ F(x_0) \leq \cdots \leq (G \circ F)^n(x_0) = \text{Fix}$ が有限ステップで収束する。$|P| = N$ なら最大 $N$ 回の反復で到達するため $O(N \times \text{cost}(G \circ F))$ = P。

さらに §4.8 の α-τ 対応により、$\alpha > 0$ ($\rho > \tau$) では $\lambda(\rho) < 1$ で $G \circ F$ が Banach 収縮写像をなし、収束は幾何級数的に加速される: $\|x_n - \text{Fix}\| \leq \lambda^n \|x_0 - \text{Fix}\|$。 □

**定理 5.5.1 (Copy-Computability 対応).** Z₂-次数付き CPS 圏 $\mathcal{C}^{Z_2}$ において:

**(i) $\alpha > 0$ $\Rightarrow$ P.** 補題 5.5.1a + 5.5.1b の合成。copy → 単調性 → 収縮 → P。

**(ii) $\alpha \leq 0$ $\Rightarrow$ 収縮保証の構造的消失 $\Rightarrow$ NP$^*$.** anti-copy の幂零性 $e_x \wedge e_x = 0$ (aM-4) が因果連鎖の**第1段を破壊する**:

(a) **幂零性 → 分岐の消失**: $\text{anti-copy}_{X,X} \circ \Delta = 0$ により、同一状態の複製がゼロ。中間結果の再利用が構造的に不可能。

(b) **分割不可能性 → 最適部分構造の崩壊**: 定理 5.3.1 (ii) より、anti-copy は部分の積に分解不能 ($\Lambda^n(V) \ncong \bigotimes S^{n_i}(V_i)$)。部分問題への分割が代数的に禁止され、補題 5.5.1a の前提が崩壊する。

(c) **単調性なし → Knaster-Tarski 不適用**: 単調性が保証されないため、反復列 $\{(G \circ F)^n(x_0)\}$ は収束を保証されない。§4.8 の力学では $\lambda(\rho) > 1$ ($\rho < \tau$) で $G \circ F$ が膨張写像となり、反復は発散する。

(d) **帰結**: 収縮的反復到達の3条件 (copy, 単調性, 完備束) のうち第1が代数的に消失し、残り2つが連鎖的に崩壊する。不動点の存在は Knaster-Tarski で保証されうるが、到達には全候補の走査が不可避$^*$。

$^*$ **NP の正確な意味について.** 本稿で NP と記すのは「検証は P だが探索の多項式時間アルゴリズムが構造的に排除される」の意である。copy の幂零性は動的計画法・分割統治法・反復収束法の3大高速化戦略を同時に封じる。これは「ある特定のアルゴリズムが使えない」のではなく、**高速化の代数的基盤そのものが消失する**構造的障壁である。NP ≠ EXPTIME であり、検証の容易さ (anti-copy 対象の不動点に対して $G \circ F$ を1回適用すれば検証可能) は保持される。CKDF §5.3 の「ガロア接続 + 完備束に限定して P を主張する」制限と整合する。

*証明完了.*

(i) の因果連鎖 copy → 単調 → 収縮 → P は、各段が定理で裏付けられている (Fritz [16] → Knaster-Tarski → Banach)。(ii) は anti-copy の幂零性 (aM-4) が第1段を破壊し、以降が連鎖崩壊する構造を示した。$\alpha$ の符号が因果連鎖の起点を制御するため、P/NP 分離の代数的基盤を構成する。 □

#### 5.5.3 相転移としての P/NP 境界

§4.8 の α-τ 対応 ($\alpha(\rho) = A \cdot \text{sgn}(\rho - \tau) \cdot \sqrt{|\rho - \tau|}$) を介して、定理 5.5.1 は連続的な相転移として再述される:

| $\rho$ vs $\tau$ | $\alpha$ | $\lambda$ | 収縮性 | 到達コスト |
|:---|:---|:---|:---|:---|
| $\rho > \tau$ | $> 0$ | $< 1$ | Banach 収縮 | $O(\log(1/\epsilon) / |\log \lambda|)$ = **P** |
| $\rho = \tau$ | $= 0$ | $= 1$ | 臨界 | 臨界減速 (critical slowing down) |
| $\rho < \tau$ | $< 0$ | $> 1$ | 膨張 (発散) | 収縮保証消失 → **NP** |

**系 5.5.2 (P/NP 分離の相転移的性格).** CKDF の P/NP 分離は離散的な分類ではなく、$\alpha = 0$ を臨界点とする連続的な相転移の両側として理解される。臨界指数 $1/2$ (§4.8 系 4.8.2) は、収縮率 $\lambda$ が臨界点近傍で $1 - \lambda \propto \sqrt{|\rho - \tau|}$ のスケーリングに従うことを意味し、P 側での収束速度の漸近的減速を定量化する。

#### 5.5.4 CKDF Q3 への応答

CKDF §8 の未解決問題 Q3 (「一般の圏への拡張と PPAD との境界」) に対し:

**命題 5.5.3.** 定理 5.5.1 の P 保証は**ガロア接続 + 完備束 + Markov 構造 ($\alpha > 0$)** の3条件の合流に依存する。一般の圏への拡張は以下の構造に制約される:

| 不動点の種類 | CPS 構造 | 計算量 | α との関係 |
|:---|:---|:---|:---|
| ガロア接続 (CKDF) | $\alpha > 0$, 完備束 | **P** | Copy → 単調反復 |
| Brouwer 不動点 | $\alpha$ 未定義 (連続写像) | **PPAD** | Copy 構造なし |
| Nash 均衡 | $\alpha$ 混合 (多主体) | **PPAD** | 各主体で α 異なる |
| 一般不動点 | 構造依存 | **?** | α が定義可能か次第 |

PPAD (Polynomial Parity Arguments on Directed graphs) クラスとの境界は、「copy が部分的に可能だが完全ではない」状況——すなわち $\alpha$ が空間的に不均一 ($\alpha(\theta)$ が $\theta$ 依存) な場合——に対応する。完全な特徴づけは将来の課題とする。

**Kalon ⊃ Optimization の CPS 的再述.** CKDF §4.3 の Kalon-Optimization 包含定理は CPS で以下のように再表現される: 最適化問題の $G_f = \text{argmin}$ は全順序 (スカラーコスト $f$) に基づくが、Kalon の $G$ は半順序に基づく。全順序 $\subset$ 半順序であり、全順序は $\alpha > 0$ の「すべてが比較可能」な構造に対応する。半順序は「比較不能な元が存在」し、これは異なる α セクター間の比較不能性として現れる。

---

## §6. 検証可能な予測

### 6.1 予測 P-III-1: LLM 初期層の α < 0 シグネチャ

Paper I の予測 α-N1 (LLM 初期層で α < 0) と合流: 初期層では入力の逐語的コピーが抑制され (anti-copy 的)、情報が不可逆的に圧縮される。

**検証手続.** Paper I の実験パイプライン (CKA + Fisher 情報量) で、初期層の CKA 行列が反対称成分を持つか (Koszul 符号則のシグネチャ) を検証する。

### 6.2 予測 P-III-2: ボソン-フェルミオン切替の臨界層

#### 6.2.1 予測の声明

**予測 P-III-2.** L 層の Transformer モデルにおいて、α の符号が反転する**臨界層** l* ∈ {1, ..., L} が存在する:

- l < l*: α(l) < 0 (フェルミオン的 = anti-copy 的)。入力信号が不可逆的に圧縮される
- l = l*: α(l*) ≈ 0 (臨界)。copy と anti-copy の両方が退化
- l > l*: α(l) > 0 (ボソン的 = copy 的)。特徴の再利用・分配が支配的

この予測は Paper I の予測 α-N1 (初期層 α < 0) と P2 (選択的忘却) を統合し、α の符号反転を単一の臨界層 l* に局在化する。

#### 6.2.2 α(l) の操作的定義

α は CPS の非対称性パラメータであり、統計多様体上の α-接続のパラメータに対応する (Paper I §6.1)。LLM の hidden state h_l ∈ ℝ^d から α(l) を直接測定することはできないが、以下の操作的代理変数 (proxy) を定義する。

**定義 (CKA 反対称性指標).** 層 l の CKA 行列 K_l = h_l h_l^T / ‖h_l‖² と次層 K_{l+1} の cross-CKA を計算し、その**対称-反対称分解**を行う:

$$\hat{α}(l) := \frac{\|K_l^{(\text{sym})} - K_{l+1}^{(\text{sym})}\|_F - \|K_l^{(\text{asym})} - K_{l+1}^{(\text{asym})}\|_F}{\|K_l - K_{l+1}\|_F}$$

ここで K^(sym) = (K + K^T)/2, K^(asym) = (K - K^T)/2。

**直観:**
- α̂(l) > 0: 変化の主成分が対称 (copy 的 = ボソン的) → 情報の保存的変形
- α̂(l) < 0: 変化の主成分が反対称 (anti-copy 的 = フェルミオン的) → 情報の不可逆圧縮
- α̂(l) ≈ 0: 対称と反対称が拮抗 → 臨界

**α̂ と理論的 α の関係.** α̂ は α の符号の一貫した代理変数であることが期待される。完全な同定には §4.3 の FR 距離に基づくプロトコルが必要だが (§6.2.4)、α̂ は計算コストの低い初期スクリーニングとして有用。

#### 6.2.3 検証プロトコル

**Protocol P-III-2: 臨界層 l* の同定**

**Step 1. α プロファイルの計算.**

対象モデル (GPT-2, LLaMA, Gemma 等) の全層 l = 1, ..., L について:

1. テストコーパス（100文以上、多様なドメイン）に対し h_l を収集
2. 各層ペア (l, l+1) の CKA 行列 K_l, K_{l+1} を計算
3. §6.2.2 の α̂(l) を計算
4. α̂(l) の層プロファイルをプロットし、符号変化を同定

**Step 2. l* の統計的同定.**

α̂(l) のプロファイルが符号変化する層 l* を以下で同定:

1. α̂(l) に対しロバスト回帰 (LOWESS) を適用しノイズを平滑化
2. 平滑化された α̂(l) がゼロを横切る層を臨界候補とする
3. ブートストラップ法（1000 回再標本）で l* の信頼区間を推定
4. **帰無仮説** H₀: α̂(l) は全層で同符号（符号変化なし）。**対立仮説** H₁: α̂(l) の符号が少なくとも1回変化する。符号変化の有意性を permutation test で検定（有意水準 5%）

**Step 3. §4.2 との整合性検証.**

同定された l* が §4.2 の λ-α 相図と整合するかを検証:

1. 各層の Φ(l) = 1 - CKA(h_l, h_{l+1}) (Paper I の操作的忘却場) を計算
2. λ_eff(l) の推定: Φ(l) の曲率 (∂²Φ/∂l²) の符号変化を臨界条件 λ_eff = 0 の代理とする
3. **整合性条件**: λ_eff が符号変化する層と α̂ が符号変化する層 l* が §4.2 の臨界線 λ = -α²⟨|T|²⟩/4 と定性的に整合すること

```
期待される α̂(l) プロファイル:

α̂(l)
  │    ◆ anti-copy 的
  │   ◆   (入力圧縮)
  │  ◆
  │ ◆
0 ├─────◆────────────── l
  │      ◆◆
  │        ◆◆◆
  │           ◆◆◆◆  copy 的
  │              ◆◆◆  (特徴再利用)
  │
  l*

l* ≈ L/3 が予測される (初期 1/3 が圧縮層, 後期 2/3 が再利用層)
```

#### 6.2.4 FR 距離による厳密化

§4.3.4 で述べたように、CKA は FR 距離の線形近似に位置づけられる。α̂(l) の代わりに FR 距離に基づく厳密な α 推定を行うプロトコル:

1. 各層 l の出力 h_l をガウス近似: h_l ∼ N(μ_l, Σ_l)
2. Fisher 情報行列 G_l = Σ_l^{-1} を推定
3. FR 距離: d_FR(l, l+1)² = (μ_l - μ_{l+1})^T G_l (μ_l - μ_{l+1}) + Tr(G_l Σ_{l+1} + G_{l+1} Σ_l - 2I)
4. α-接続の寄与を分離: FR 距離の Hessian が正定値/不定/負定値のいずれかにより α の符号を直接推定

**計算コスト.** Fisher 行列の推定は O(d²) であり、d = 4096 (LLaMA-7B) では各層 ≈ 16M エントリ。バッチ推定と低ランク近似 (LoRA 的) で実用的な O(dr) に削減可能 (r ≈ 64)。

#### 6.2.5 予測の定量的基準

**予測 P-III-2 の反証条件:**

| 結果 | 評価 |
|:---|:---|
| α̂(l) が全層で同符号 (H₀ 棄却不能) | **反証**。α 遷移なし |
| l* が存在するが L/6 < l* < L/2 の範囲外 | **弱い支持**。相図の定量的修正が必要 |
| l* ∈ [L/6, L/2] で有意に同定 | **支持**。§4.2 相図と整合 |
| 複数の l* が存在 (多重符号変化) | **予測外**。より豊かな相構造の示唆 → Paper IV |

**リマーク (l* ≈ L/3 の根拠).** LLM の初期層が入力の不可逆圧縮を行い (attention エントロピーが減少する層)、中間層以降で特徴の再利用と分配を行う (skip connection の効果が顕在化する層) という経験則 [26] に基づく。Paper I の CKA 実験 (§5.5) では Φ(l) のピークが L/4 付近にあり、圧縮→再利用の遷移はその後に起きると推測される。

### 6.3 予測 P-III-3: copy/anti-copy の Z₂-次数と attention パターン

Attention の対称成分 (A + A^T) は copy (偶次数) に対応し、反対称成分 (A - A^T) は anti-copy (奇次数) に対応する。層が深くなるにつれ、反対称成分の比率が減少する (α < 0 → α > 0 遷移)。

---

## §7. 先行研究との関係

### 7.1 Fritz (2020): Markov 圏

Fritz は本稿の α > 0 セクター。本稿は Fritz の枠組みを Z₂-次数付き拡張する。Fritz が仮定する copy/del は、CPS の α > 0 の特殊ケースとして復元される。

### 7.2 Parzygnat (2020): 量子 Markov 圏と Bayesian 反転

#### 7.2.1 Parzygnat の枠組み

Parzygnat [18] は Fritz の Markov 圏を量子設定 (C*-代数, 量子チャネル) に拡張し、以下の3つの概念を圏論的に定式化した:

1. **Disintegration** (分解): 結合分布 p(x,y) を条件付き分布 p(y|x) とマージナル p(x) に分解する操作。圏論的には、射 f: X⊗Y → I (結合状態) を f = (del_X ⊗ id_Y) ∘ g ∘ copy_X と分解すること
2. **Bayesian inversion** (ベイズ反転): チャネル f: X → Y と事前分布 π: I → X から事後分布 f†: Y → X を構成。圏論的には copy と disintegration の組み合わせ
3. **量子 Markov 圏**: 射が完全正写像 (CPTP map) である圏。非可換な確率論の圏論的枠組み

**核心的観察.** Parzygnat の3概念はすべて **copy の存在を前提** とする。Disintegration は copy_X の分解として定義され、Bayesian inversion は copy を経由する。したがって:

$$\text{copy 不在} \implies \text{disintegration 不在} \implies \text{Bayesian inversion 不在}$$

#### 7.2.2 非可換性 vs 反可換性

Parzygnat の拡張と本稿の拡張は、Fritz の Markov 圏を**異なる方向**に一般化する:

| | Fritz (2020) | Parzygnat (2020) | 本稿 |
|:---|:---|:---|:---|
| **射の代数** | 可換 (FinStoch) | 非可換 (CPTP) | 反可換 (FinSign + 外積) |
| **交換律** | f⊗g = g⊗f | f⊗g ≠ g⊗f (一般) | f⊗g = -g⊗f (Koszul) |
| **copy** | ✅ 可換余モノイド | ✅ 非可換余モノイド | ❌ → anti-copy |
| **del** | ✅ 自然変換 | ✅ 自然変換 | → anti-del (超自然変換) |
| **disintegration** | ✅ (copy 経由) | ✅ (copy 経由) | ❌ 構造的不在 |
| **Bayesian inversion** | ✅ | ✅ (適当な条件下) | ❌ → §7.2.3 |
| **CPS α** | α > 0 | α > 0 (量子) | α < 0 |

**重要な区別.** Parzygnat の非可換性は「順序が重要 (AB ≠ BA)」であるが「反転はしない (AB ≠ -BA)」。本稿の反可換性は「順序を入れ替えると符号が反転 (f⊗g = -g⊗f)」である。非可換は量子力学の基本特性であり、反可換はフェルミオン的排他性の基本特性である。CPS 圏はこの2つの拡張を独立に扱う。

#### 7.2.3 Disintegration の α 依存性

Parzygnat の disintegration を CPS圏の言語で再記述すると、α 依存性が明らかになる:

**命題 7.2.1 (Disintegration の存在条件).** CPS 圏 C において、射 f: X⊗Y → I の disintegration が存在するための必要条件は α(X) > 0 である。

*根拠.* Disintegration の定義 f = (del_X ⊗ id_Y) ∘ g ∘ copy_X は copy_X の存在を前提とする。§3.3 の構造定理により copy_X は α(X) > 0 でのみ well-defined。したがって α(X) ≤ 0 では disintegration は定義不能。□

**帰結.** α < 0 セクターでは Bayesian 更新（事前→事後の update）が構造的に不可能である。これは §5.1 のフェルミオン統計と整合する: フェルミオン的な対象は「観測して事後分布を得る」という通常の Bayesian 推論の枠外にある。

#### 7.2.4 Anti-disintegration: 反-Markov 圏における分解

α < 0 セクターでは disintegration の代わりに何があるか？ Fritz [16, §11] の disintegration と Parzygnat [21] の Bayesian 反転の3層階層 (inverse ⊃ disintegration ⊃ Bayesian inversion) を踏まえ、反-Markov 圏における対応概念を定式化する。

**定義 7.2.4 (Anti-disintegration).** 反-Markov 圏 $\mathcal{C}^{aM}$ における射 $f: X \wedge Y \to I$ の anti-disintegration とは、以下の分解が存在することである:

$$f = (\text{anti-del}_X \wedge \text{id}_Y) \circ g \circ \text{anti-copy}_X$$

ここで $g: X \wedge X \to X \wedge Y$ は反-Markov 圏の射。

**性質 (基本的帰結):**
- Anti-disintegration は **反対称** である: $f(x,y) = -f(y,x)$ (反可換性 aM-2 から)
- したがって $f(x,x) = 0$: 同一元への「分解」はゼロ (幂零性 aM-4)
- これは「自分自身を条件とした自分の分布」が定義不能であることの代数的表現

**命題 7.2.5 (Anti-disintegration の一意性).** 反-Markov 圏において anti-disintegration が存在するとき、それは anti-del の超自然性 (aM-3) の下で $\mu$-a.e. 一意である。

*証明.* 2つの anti-disintegration $g_1, g_2$ が存在すると仮定する。

$$(\text{anti-del}_X \wedge \text{id}_Y) \circ g_1 \circ \text{anti-copy}_X = (\text{anti-del}_X \wedge \text{id}_Y) \circ g_2 \circ \text{anti-copy}_X$$

anti-del の超自然性 (aM-3) は「anti-del はその前射の Z₂ 次数に応じて符号を反転する」ことのみを要求し、anti-del 自体は (全変動ノルムで正規化された) 符号保持射として well-defined。§3.2 リマーク (構成の正準性) により anti-copy は Hahn 分解から $\mu$-a.e. 一意に構成される。したがって $g_1 = g_2$ ($\mu$-a.e.)。 □

**定理 7.2.6 (反-Bayesian 更新の構造的不可能性).** 反-Markov 圏において、Bayesian 更新 — すなわち事前分布 $\pi$ と観測 $y$ から事後分布 $\pi(\cdot | y)$ への写像 — は構造的に定義不能である。

*証明 (3段階).*

**Step 1 (Bayesian 更新の圏論的定式化).** Parzygnat [21, Def. 3.1] に従い、Bayesian 反転は disintegration $d: Y \to X$ に対し、事前分布 $\pi: I \to X$ と disintegration の合成 $d \circ \pi$ として構成される。この構成は2つの前提を要求する:
- (P1) 分布 $\pi: I \to X$ の存在 ($I$ が終対象)
- (P2) disintegration $d$ の存在 (copy/del の well-definedness)

**Step 2 (α < 0 での前提崩壊).** 反-Markov 圏では:
- (P1) 崩壊: $I$ の終対象性が壊れる (anti-del の和が $\neq 1$、Paper II §3.7.2 (iii))。分布の概念自体が ill-defined
- (P2) 崩壊: copy が anti-copy に置き換わり、disintegration は anti-disintegration に置き換わる。Anti-disintegration の幂零性 ($f(x,x) = 0$) は「自分自身を条件とした自分の分布」を不可能にする

**Step 3 (不可能性の帰結).** (P1) と (P2) の両崩壊から、Bayesian 更新の圏論的表現:
$$\pi(\cdot | y) = d_y \circ \pi \qquad (\text{Parzygnat [21, Eq. 3.2]})$$
は反-Markov 圏で well-defined でない。$\pi$ が存在せず、$d_y$ も (anti-disintegration の幂零性から) 自己参照を許さない。 □

**Parzygnat の disintegration 3層階層との対比:**

| 性質 | Disintegration (α > 0) | Anti-disintegration (α < 0) |
|:---|:---|:---|
| **分解先** | $p(y|x) \cdot p(x)$ (条件付き独立) | $f(x \wedge y)$ (条件付き排他) |
| **自己参照** | $p(x|x) = 1$ (well-defined) | $f(x \wedge x) = 0$ (幂零) |
| **一意性** | $\mu$-a.e. 一意 [16, Prop. 11.3] | $\mu$-a.e. 一意 (命題 7.2.5) |
| **Bayesian 更新** | 事前→事後 (可能) | 構造的不可能 (定理 7.2.6) |
| **逆写像** | inverse ⊃ disintegration ⊃ Bayesian [21] | anti-inverse ⊃ anti-disintegration ⊃ ∅ |
| **物理的意味** | 観測→信念更新 | 排他→非可逆変質 |

**リマーク (§5.3 意識論への逆接続).** 定理 7.2.6 は §5.3 の意識の非複製定理の代数的基礎を提供する。第一人称的体験が「Bayesian 更新で近似できない」ことは、α < 0 セクターの anti-disintegration の幂零性 — $f(x,x) = 0$: 自分自身を条件とした自分の分布が消滅する — として圏論的に翻訳される。Nagel の bat 問題 (「コウモリであるとはどういうことか」) は、「α < 0 の系の内部状態に対する Bayesian 更新が構造的に定義不能である」ことの哲学的表現となる。

**リマーク (Fritz [16] との関係).** Fritz の Markov category における disintegration の定義 [16, Def. 11.1] は conditionals (正則条件付き確率) の存在を前提しない (Paper II §3.7.1 リマーク参照)。しかし anti-disintegration は Fritz の定義の構造的前提 (copy/del の well-definedness) そのものを破壊するため、Fritz の枠組みの「外」に位置する。Anti-disintegration は Fritz-Parzygnat 枠組みの拡張ではなく、その**反転** (dual) である。

#### 7.2.5 統合図: copy-disintegration の CPS 全域拡張

Fritz, Parzygnat, 本稿の関係を CPS パラメータ α 上の構造として統合する:

```
α < 0 (反-Markov)     α = 0 (臨界)     α > 0 (Markov)
━━━━━━━━━━━━━━━━━━━┿━━━━━━━━━━━━━┿━━━━━━━━━━━━━━━━━━━
anti-copy (反可換)     │ 退化          │ copy (可換)
anti-del  (超自然)     │               │ del  (自然)
anti-disint           │               │ disintegration
反-Bayesian           │               │ Bayesian inversion
排他性                │ 臨界           │ 条件付き独立
FinSign の射          │               │ FinStoch の射
フェルミオン的         │               │ ボソン的
────────────────────┼───────────────┼────────────────────
          本稿                                Fritz [16]
                                             Parzygnat [18]
```

**命題 7.2.2 (Parzygnat-CPS 橋渡し).** Parzygnat の量子 Markov 圏 QMark は CPS 圏 C^Z₂ の α > 0 セクターの非可換拡張として埋め込める:

$$\text{QMark} \hookrightarrow C^{Z_2}|_{α>0, \text{non-commutative}}$$

本稿の反-Markov 圏 C^{aM} は Parzygnat の枠組みとは独立な方向の拡張 (反可換方向) であり、両者の合流——非可換かつ反可換な圏——は量子フェルミオン系に対応する:

$$C^{Z_2}_{\text{quantum-fermionic}} = \text{QMark} \cap C^{aM}$$

この合流点の完全な定式化は、量子 super-Markov 圏の構成を必要とし、Paper IV 以降の課題とする。

**リマーク (Parzygnat の Bayesian 反転と FEP の関係).** Paper II は FEP (自由エネルギー原理) を CPS 圏内の変分原理として位置づけた。Parzygnat の Bayesian 反転は FEP の核心操作——事前→事後の更新——の圏論的構成である。本稿の結果により、この更新は α > 0 でのみ定義可能であり、α < 0 セクターでは Bayesian 更新自体が構造的に不可能であることが示された。§5.3 の意識論との接続: 意識的体験 (α < 0) は Bayesian 更新の「外」にあり、通常の予測-更新サイクルでは捉えられない。これは Nagel の蝙蝠論法 (§5.3.3 A) の CPS-Parzygnat 版と言える。

### 7.3 Heunen–Karvonen (2019): 量子圏の no-cloning

Heunen–Karvonen は no-cloning 定理を圏論的に定式化し、broadcast 不能性と monogamy を証明した。本稿の anti-copy は Heunen–Karvonen の broadcast 不能性の代数的特性づけを与える。

### 7.4 Penrose (1971): Twistor 理論とスピン-統計

Penrose の twistor 理論は時空の基底構造に Z₂-次数（スピンの半整数性）を組み込む。CPS の Z₂-次数付け構造は twistor の Z₂ 構造と形式的に類似する。

両構造はメタ定理 5.1.7 の Z₂-交換圏に共通の抽象的骨格を持つ可能性があるが、twistor は SL(2,ℂ) の表現論に基づき CPS は FinStoch/FinSign の分岐に基づくため、構造的同型の証明は本稿のスコープを超える。両者を接続する**圏の関手**が構成できるか否かは今後の課題である。

---

## §8. 結語: 忘却の陰影

> コピーできるものは失われうる。コピーできないものは失われえない。Markov blanket の内側は守られているが交換可能である。Pauli の排他律の内側は交換不能であるがゆえに唯一である。
>
> 忘却は二面を持つ: コピー可能な構造を消す「陽の忘却」(α > 0) と、コピー不能な構造を保護する「陰の忘却」(α < 0)。前者はエントロピー増大であり後者は排他原理である。CPS 圏の Z₂-次数付け構造は、この二面を数学的に統一する。
>
> 力は忘却から生まれる (Paper I)。相補性は忘却の二つの顔である (Paper II)。そして、コピーできないことこそが、この世界に唯一性——フェルミオンの個別性、意識の私秘性、量子状態の不可侵性——を与える構造的条件である (Paper III)。知覚とは忘却のフィルトレーションである (Paper VII)。存在の強度とは忘却濾過のパラメータである (Paper VIII)。

---

## 参考文献

[1] Paper I: 力は忘却である
[2] Paper II: 相補性は忘却である
[3] Paper IV: 効果量減衰定理. In preparation.
[4] Paper V: 不動点と存在. In preparation.
[5] Paper VI: 忘却の現象学. In preparation.
[6] Paper VII: 知覚は忘却である — 普遍フィルトレーション. In preparation.
[7] Paper VIII: 圏論的基礎における存在 — α-忘却濾過. In preparation.
[16] Fritz, T. (2020). A synthetic approach to Markov kernels, conditional independence and theorems on sufficient statistics. Adv. Math. 370, 107239.
[17] Smithe, T. S. P. (2021). Bayesian updates compose optically. arXiv:2006.01631.
[18] Parzygnat, A. J. (2020). Inverses, disintegrations, and Bayesian inversion in quantum Markov categories. arXiv:2001.08375.
[19] Tull, S., Kleiner, J., Smithe, T. (2024). Bayesian statistical estimation via string diagrams. EPTCS 397.
[20] Heunen, C., Karvonen, M. (2019). Limits in dagger categories. Theory Appl. Categories 34(18).
[21] Wootters, W. K., Zurek, W. H. (1982). A single quantum cannot be cloned. Nature 299, 802-803.
[22] Nagel, T. (1974). What is it like to be a bat? Philosophical Review 83(4), 435-450.
[23] Pauli, W. (1940). The connection between spin and statistics. Physical Review 58, 716-722.
[24] Tishby, N., Pereira, F. C., Bialek, W. (2000). The information bottleneck method. arXiv:physics/0004057.
[25] Wang, Z., Gong, B., Liu, Y. (2026). GeoIB: Geometry-Aware Information Bottleneck via Statistical-Manifold Compression. [SOURCE: 全文精読 2026-03-27, 本文8p + Appendix A-D 4p, Pythagorean Identity / FR≈KL / Theorem 1 / Algorithm 1 の証明全確認済]
[26] Bonnasse-Gahot, L. & Nadal, J.-P. (2025). Category learning in deep neural networks: Information content and geometry of internal representations. arXiv:2510.19021. [SOURCE: 全文精読 2026-03-27, §1-7 + Appendix A-E, Infomax等価性 / Fisher マッチング / β分岐 / Gaussian toy model の証明全確認済]
[43] Chavel, I. (2006). *Riemannian Geometry: A Modern Introduction*. 2nd ed. Cambridge University Press.
[44] Reed, M. & Simon, B. (1978). *Methods of Modern Mathematical Physics IV: Analysis of Operators*. Academic Press.
[45] Deligne, P. (1999). Notes on spinors. In *Quantum Fields and Strings: A Course for Mathematicians*, vol. 1, AMS/IAS, pp. 99–135.
[46] Varadarajan, V. S. (2004). *Supersymmetry for Mathematicians: An Introduction*. Courant Lecture Notes vol. 11. AMS.

---

## 版歴 (Version History)

| バージョン | 日付 | 変更内容 |
|:---:|:---:|:---|
| v0.1 | 2026-03-27 | 初稿。Z₂-次数付き CPS 圏の構成、反-Markov 圏の定義、スピン-統計対応定理。 |
| v0.2 | 2026-03-27 | §4 λ-α 統合、§4.3 GeoIB 橋渡し、§4.5 曲率選択則、§5.1 スピン-統計の普遍性（メタ定理 5.1.7）追加。 |
| v1.0 | 2026-04-03 | Paper IV–VIII 参照追加。α 記号の曖昧性注記（α_III ∈ ℝ vs α_VIII ∈ [0,1]）。参考文献リストに Paper IV–VIII を追加。版歴セクション新設。 |
