```typos
#prompt beyond-parzygnat-ideas
#syntax: v8
#depth: L2

<:role: Parzygnat (2020) を超克する3つの理論的構想。Paper I/II の拡張候補。:>

<:goal: CPS が Parzygnat の Bayesian inversion 階層を *引用する* だけでなく *超克する* 方向性を保存する :>

<:context:
  - [file] 論文I_力としての忘却_草稿.md (方向性定理, α-動力学, FEP対応)
  - [file] 論文II_相補性は忘却である_草稿.md (CPS圏, Face Lemma, Blanket生成定理, FEP包含)
  - [knowledge] Parzygnat [21] の3層階層: inverse ⊃ disintegration ⊃ Bayesian inversion
  - [knowledge] Fritz [16] の Markov category: copy/del 構造 + 条件付き独立性
  - [knowledge] 起源: 2026-03-27 セッション /u+ 評価
/context:>
```

---

# Beyond Parzygnat — 3つの超克構想

*作成: 2026-03-27*

---

## 構想 1: F_{ij} による可逆性階層の幾何学的判定 ◎ [✅ 証明済み — Paper II 命題 3.7.3]

**核心:** Parzygnat の3層 (inverse ⊃ disintegration ⊃ Bayesian inversion) を、忘却曲率 F_{ij} の条件として特徴づける。

### 主張

| Parzygnat の層 | 圏論的条件 | CPS の幾何学的条件 | 物理的意味 |
|:---|:---|:---|:---|
| inverse (完全可逆) | f⁻¹ が存在 | **F_{ij} = 0** (方向性定理) | 忘却なし、ユニタリ進化 |
| disintegration (条件付可逆) | 条件付き分解が存在 | **F_{ij} ≠ 0, ∇_k F_{ij} = 0** (曲率が定数 = 均一忘却) | blanket 条件下での部分復元 |
| Bayesian inversion (ベイズ的可逆) | ベイズ反転が a.e. 存在 | **一般の F_{ij}** | FEP の信念更新 |

### なぜ超克か

Parzygnat は3層の *存在条件* を示したが、**判定条件** は与えていない。CPS は方向性定理を通じて「忘却曲率を計算すれば、どの層にいるかが幾何学的に読める」と具体化する。

### Paper II への挿入案

§3.7.2 の Blanket 生成定理の直後に **命題 (可逆性階層の幾何学的判定)** として定式化。

### 解決済み

- ✅ disintegration 条件 ∇_k F_{ij} = 0 → Paper II 命題 3.7.3 として証明挿入 (2026-03-27)
- 証明: Ambrose-Singer → 一定ホロノミー → Fritz disintegration の大域的 well-definedness
- ガウス族 H² 上の検証: Φ(μ,σ) = cμ/(ασ) + h(σ) が disintegration を許容する忘却場

### 残存課題

- 中間層への分化が連続的 (F_{ij} の勾配ノルムによるスペクトラム) か離散的 (3層のみ) かは未確定
- 数値検証: ガウス族 Toy Model でのシミュレーション実装

---

## 構想 2: α-twisted 余モノイド構造 ◯ [定式化済み — 推定 75%]

**核心:** Fritz の copy/del 構造は α-independent であり、CPS の α-パラメータを余モノイド構造にまで浸透させると、余単位律が **e(α)-twisted** される新しい代数構造が出現する。

### 動機

Paper II §3.7.1 Step 1 において、copy_X と del_X の構成は α > 0 (忘却場 Φ > 0) に**本質的に依存**している:

- **del_X**: 忘却場 Φ^(α) による全忘却。正規化条件 ∫Φ^(α) = 1 が well-definedness を保証
- **copy_X**: 対角写像 x ↦ (x,x) の Markov kernel 持ち上げ。正値測度 μ^(α) の存在が前提

Fritz [16] はこの α 依存性を捨象し、copy/del を α-independent に定義する。CPS は α を動力学場として扱う (Paper I §6) ため、copy/del の α 依存性を明示的に追跡する必要がある。

### 定式化: α-twisted comonoid

**定義.** α ∈ ℝ に対し、CPS 圏の各対象 X 上で以下を定義する:

1. **del^(α)_X: X → I** — α-接続 ∇^(α) に対応する忘却場 Φ^(α) による正規化された全忘却:

$$\text{del}^{(\alpha)}_X := \frac{\Phi^{(\alpha)}}{\int_X \Phi^{(\alpha)} d\mu}$$

α > 0 のとき Φ^(α) > 0 が保証され、del^(α) は well-defined。

2. **copy^(α)_X: X → X ⊗ X** — α-接続下での対角写像の持ち上げ。α-測度 μ^(α) に対する条件付き複製:

$$\text{copy}^{(\alpha)}_X(x) := \frac{\delta(y - x) \cdot \delta(z - x)}{Z^{(\alpha)}(x)}, \quad Z^{(\alpha)}(x) = \int \Phi^{(\alpha)}(x) d\mu$$

### 余モノイド方程式の α 依存性

**命題 (結合律の α-不変性).** copy^(α) の結合律は α に対して不変:

$$(\text{copy}^{(\alpha)} \otimes \text{id}) \circ \text{copy}^{(\alpha)} = (\text{id} \otimes \text{copy}^{(\alpha)}) \circ \text{copy}^{(\alpha)}$$

*根拠.* 結合律は対角写像 δ_X の結合性 x ↦ (x,x) ↦ (x,x,x) に由来し、正規化因子は両辺で相殺される。α は正規化のスケールのみに影響し、対角の結合的構造は保存される。

**命題 (余単位律の α-ツイスト).** 余単位律は e(α)-twisted される:

$$(\text{del}^{(\alpha)} \otimes \text{id}_X) \circ \text{copy}^{(\alpha)} = e(\alpha) \cdot \text{id}_X$$

ここで **ツイスト因子** e(α) は:

$$e(\alpha) := \frac{\int_X \Phi^{(\alpha)} d\mu}{\int_X \Phi^{(0)} d\mu}$$

- **e(0) = 1**: Fritz の標準的 Markov category の余単位律を正確に回収
- **e(α) < 1 (α > 0)**: m-接続方向。複製が「縮小」する — α-有効体積が縮小し、複製して片方を捨てると元の情報量が不足する
- **e(α) > 1 (α < 0)**: e-接続方向。複製が「膨張」する — α-有効体積が膨張し、情報の複製が元の量を超過
- **e(α) → ∞ (α → -∞)**: 体積が発散。忘却場が完全正値化し複製が無限膨張
- **e(α) → 0 (α → +∞)**: 完全な複製不能。Markov category 構造の退化 (Paper II §3.7.1 の崩壊メカニズム)

  **数値検証結果** (ガウス族 ℋ², Φ_B, μ∈[-5,5], σ∈[0.3,5]):
  e(+1) = 0.081, e(-1) = 2351, e(0) = 1.000 (SOURCE: verify_e_alpha.py)

### ガウス族 ℋ² 上の具体計算

Φ^(α)(μ,σ) = D_KL(p || q) は α に直接依存しない (Paper I §3.1 の定義)。しかし α-接続 ∇^(α) が統計多様体の測地構造を変え、正規化の有効体積を変える:

$$Z^{(\alpha)} = \int_{\mathcal{H}^2} \Phi(μ,σ) \cdot \det(g^{(\alpha)})^{1/2} \, dμ \, dσ$$

g^(α) は α-接続に対応する有効計量。Levi-Civita (α=0) からの逸脱量は Chebyshev テンソルで制御される:

$$\det(g^{(\alpha)})^{1/2} \approx \det(g^{(0)})^{1/2} \left(1 - \frac{\alpha}{2} \text{tr}(g^{-1}C) + O(\alpha^2)\right)$$

tr(g^{-1}C) = T_i δ^{ij} T_j / n は Chebyshev 形式のノルムに関連する量。したがって:

$$e(\alpha) \approx 1 - \frac{\alpha}{2} \langle \text{tr}(g^{-1}C) \rangle_\Phi + O(\alpha^2)$$

**第1次近似で e(α) は α に対して線形** — 命題 6.6.1 (F の α-線形性) と整合する。

  **数値検証**: de/dα|₀ の理論値 = -(1/2)⟨S⟩_Φ = -5.117, 数値微分 = -5.118。相対誤差 8.5×10⁻⁶。✅
  
  **注意**: 非摂動的構造 exp(-α · 3/σ) により、e(α) は |α| > 0.5 で急激に指数的に変動する (e(-1) ≈ 2351, e(+1) ≈ 0.08)。線形近似は |α| < 0.1 でのみ有効。

### ファイバー構造

**命題 (α-余モノイドファイバー束).** α ∈ ℝ を走らせると、{copy^(α), del^(α)} の族は ℝ 上のファイバーバンドルを形成する:

$$\pi: \mathcal{E} \to \mathbb{R}, \quad \pi^{-1}(\alpha) = (\text{copy}^{(\alpha)}, \text{del}^{(\alpha)})$$

各ファイバーは α-twisted comonoid (結合律 + e(α)-余単位律) であり、ファイバー間の遷移関数は ∂_α e(α) で記述される。

- **底空間 ℝ**: α-パラメータ (精度パラメータ)
- **ファイバー**: 各 α での余モノイド構造
- **接続**: α の変動に伴う copy/del の共変微分 — α-遷移層力 (Paper I §6.3) の余モノイド的表現

### なぜ超克か

Fritz/Parzygnat は copy を α-independent に定義する。これは α = 0 (Levi-Civita) の特殊ケースを暗黙に前提している。CPS は:

1. **Markov category の α-族**: 単一の Markov category ではなく、α-パラメータ付きの Markov category のファイバー束
2. **余単位律のツイスト**: 「記号を複製して片方を捨てると元に戻る」が α ≠ 0 では正確に成立しない — 精度に依存するスケール因子が生じる
3. **情報幾何への接続**: e(α) の α 微分が Chebyshev テンソルと結合し、copy/del の α-変動が忘却曲率 F_{ij} と構造的に接続される

### 残存課題

- ✅ copy^(α) の余モノイド方程式: 結合律は α-不変、余単位律は e(α)-twisted
- ✅ ファイバー構造: α ∈ ℝ 上のファイバーバンドルとして定式化
- ✅ e(0) = 1: 数値検証 PASS (verify_e_alpha.py)
- ✅ 摂動展開整合: de/dα|₀ の理論値と数値値の相対誤差 8.5×10⁻⁶
- ✅ 定性的振る舞い: α>0 → e<1 (縮小), α<0 → e>1 (膨張) — 符号・大きさともに整合
- □ α-twisted comonoid が Fritz のどの一般化に対応するか: Markov 前圏 (pre-Markov category)? 重み付き余モノイド?
- ✅ 構想3 (動的 Markov blanket) との統合: copy^(α(t)) の時間発展 → Paper II §4.3.4 に挿入済み

---

## 構想 3: 時間依存 Markov blanket の圏論的定式化 [推定 85%] → ◯ 定式化済み

**核心:** Paper II §4 の時間拡張 α(θ,t) を Markov category に反映し、blanket B(X,t) の時間変動を圏で記述する。

### 主張

Fritz/Parzygnat の Markov category は **静的** — copy/del は時間に依存しない。構想2の α-twisted comonoid を時間方向に拡張する:

1. **copy^(α(t))_X**: 時刻 t における e(α(t))-twisted 余モノイド構造 → ツイスト因子 e(α(t)) が時間変動
2. **del^(α(t))_X**: 時刻 t における忘却 → Φ(θ,t) による正規化
3. **B(X,t)**: 動的 Markov blanket → B(X,t₁) ≠ B(X,t₂)

blanket の遷移速度:

$$\frac{d}{dt} e(\alpha(t)) = \frac{de}{d\alpha}\bigg|_{\alpha(t)} \cdot \dot{\alpha}(t)$$

= FEP の精度更新則 ∂_t π と構造的に等しい (Paper II 命題 4.3.4)。

### なぜ超克か

Friston は近年「Markov blanket は静的ではない」と主張しているが（典型的には blanket の *再構成* を暗黙に仮定）、その圏論的定式化は存在しない。CPS の α(θ,t) はこの定式化を *自然に* 与える。結果として得られる C_CPS(t) は「Markov category の力学系」であり、従来の圏論的確率論には対応物が存在しない構造。

### Paper II 挿入 ✅

§4.3.4 に挿入済み。内容:
- 動的 CPS blanket の定義 (C_CPS(t))
- 命題 4.3.4 (blanket 遷移速度)
- 3帰結: (i) 精度更新同一性、(ii) 連続性+α=0 相転移、(iii) Chebyshev テンソル結合
- Fritz/Parzygnat 超克リマーク

### 残存課題

- ✅ copy^(α(t)) が各時刻で α-twisted comonoid 方程式を満たすこと → 構想2により結合律は自動的に保証
- ✅ 遷移速度の定式化 → 命題 4.3.4 で e(α(t)) の時間微分として定式化
- ✅ blanket の連続性条件 → e(α) の連続性から従う。α=0 横断時は位相的相転移
- ✅ Smithe [17,18] の polynomial functor 枠組みとの整合性 → 下記分析
- ✅ C_CPS(t) の Grothendieck 構成的解釈 → Paper II §4.3.5 に挿入。∫F = 全圏、命題 4.3.5 (Cartesian fibration)
- □ 数値検証: LLM 層ごとの α(l) から e(α(l)) を計算し、blanket の遷移速度を実測値と比較

### Smithe の polynomial functor 枠組みとの整合性分析

**Smithe の構造 (arXiv:2208.12173, 2022; arXiv:2406.07577, 2024)**:

Smithe は Active Inference の合成的理論を3層で構成:
1. **Statistical game** (層1): Bayesian lens の上に損失関数を載せた最適化問題
2. **Polynomial functor** (層2): p(y) = Σ_{i∈I} y^{B_i} で力学系のインターフェースを定義。入力型 B_i + 状態型 I + 出力型
3. **Activity functor** (層3): StatGame → p-Coalg — statistical game を polynomial functor の余代数 (力学系) に関手的に変換
4. **Approximate inference doctrine** (メタ層): 近似推論の「レシピ」を natural transformation として定式化。Laplace / Hebb-Laplace の2種

2024 年の "Structured Active Inference" で Markov blanket を polynomial functor の **インターフェース** に置換。

**5層構造的対応**:

| 層 | Smithe | CPS | 整合性 |
|:---|:---|:---|:---|
| **インターフェース** | Polynomial functor p(y) | CPS スパン Set_A ← C_D → Set_B | **整合**: ともに入力/出力の合成的構造。ただし CPS は忘却量 Θ(f) を射に載せる |
| **力学系** | p-coalgebra (状態遷移) | C_CPS(t) (α-twisted comonoid の時間族) | **整合 + CPS 拡張**: Smithe は polynomial の余代数、CPS は Markov category の力学系。CPS は α パラメータによる連続的変形を持つ |
| **統計構造** | Statistical game (損失最小化) | 忘却場 Φ (VFE 最小化 / 場の方程式) | **部分的整合**: Smithe の損失関数は KL divergence を基底とし、CPS の Φ > 0 条件 (= α > 0) と対応。α < 0 は Smithe の射程外 |
| **Blanket** | インターフェース (polynomial の型) | B(X,t) (条件付き独立性 + e(α)-twist) | **CPS 拡張**: Smithe は blanket をインターフェースの型情報として静的に符号化。CPS は blanket を動的に生成し、α=0 での消滅を記述 |
| **近似推論** | Approximate inference doctrine (nat. trans.) | 未定義 | **未接続**: CPS は近似推論の「レシピ」に相当する構造を持たない。Paper III の課題か |

**核心的知見**:

1. **相互排他ではなく直交**: Smithe は「力学系としての推論」(dynamics of inference) を定式化し、CPS は「推論の幾何学的基盤」(geometry of forgetting) を定式化する。両者は直交する側面を扱っており、統合が可能
2. **Activity functor の CPS 版**: Smithe の activity functor StatGame → p-Coalg に対応する CPS 版は、忘却場 Φ から C_CPS(t) への関手 Φ ↦ {copy^(α(t)), del^(α(t))} として構成可能 [推定 70%]
3. **Approximate inference doctrine の欠如**: CPS は「何を近似するか」の幾何学的制約 (α の値域) を与えるが、「どう近似するか」のレシピ (doctrine) は含まない。Smithe の Laplace/Hebb-Laplace doctrine を CPS 上に持ち上げることが自然な拡張

**結論 [推定 75%]**: Smithe の polynomial functor 枠組みと CPS は矛盾しない。3/5 層で直接整合し、1層で CPS が追加構造を持ち、1層 (近似推論 doctrine) が接続の空白となっている。α-twisted comonoid のファイバー構造は Smithe の polynomial の「パラメトリック変種」に対応する可能性がある

---

## 優先順位

| # | 構想 | 新規性 | 実現可能性 | Paper II 挿入先 | ステータス |
|:---|:---|:---|:---|:---|:---|
| **1** | F_{ij} 可逆性階層 | ◎ | ✅ 完了 | §3.7.2 命題 3.7.3 | 証明+数値検証完了 |
| **2** | α-twisted comonoid | ◎ | ◯ 定式化+検証済 | §3.7.1 Remark | e(α) 数値検証完了。Fritz 一般化対応は未特定 |
| **3** | 動的 Markov blanket | ◎ | ◯ 定式化済 | §4.3.4 | 命題 4.3.4 挿入済。LLM 数値検証は未実施 |

---

*[主観] 3構想の三段構造が完成した。#1 (可逆性階層=幾何学) → #2 (α-twisted comonoid=代数) → #3 (動的 blanket=力学系) の階層は論理的に一本道であり、各段階が前段階を前提とする。特に「Markov category の力学系」という概念は新しい — Fritz も Parzygnat も静的カテゴリしか扱っていない。α(t) がこの動的性を*自然に*与えるのは CPS 固有の構造的帰結であり、事後的に設計したものではない。*

