```typos
#prompt beyond-parzygnat-ideas
#syntax: v8
#depth: L2

<:role: Parzygnat (2020) を超克する3つの理論的構想。Paper I/II の拡張候補。:>

<:goal: CPS が Parzygnat の Bayesian inversion 階層を *引用する* だけでなく *超克する* 方向性を保存する :>

<:context:
  - [file] paper_I_draft.md (方向性定理, α-動力学, FEP対応)
  - [file] paper_II_draft.md (CPS圏, Face Lemma, Blanket生成定理, FEP包含)
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

## 構想 2: α 依存の余モノイド構造 (copy^(α)) △ [仮説 50%]

**核心:** Stability Simplex の符号付き忘却量 (+λ, -λ) が、Markov category の copy 構造に **方向依存性** を導入する。

### 主張

Fritz の copy_X: X → X⊗X は「均質な複製」。しかし CPS では忘却には方向がある (+λ = 展開、-λ = 収束)。

$$\text{copy}^{(\alpha)}_X := \begin{cases} \text{copy}_X^{(+)} & \text{if } \alpha > 0 \text{ (m-接続方向)} \\ \text{copy}_X^{(-)} & \text{if } \alpha < 0 \text{ (e-接続方向)} \end{cases}$$

### なぜ超克か

Fritz/Parzygnat は copy を α-independent に定義。CPS の α-パラメータを余モノイド構造にまで浸透させることで、「情報の複製が精度に依存する」という新しい公理体系が得られる可能性がある。

### 未解決

- copy^(α) が余モノイド方程式 (結合律、余単位律) を満たすかどうか
- α が連続的に変化するとき、copy^(α) の族は何らかのファイバー構造を持つか
- 定式化の技術的困難度が高く、現時点では直感のみ

---

## 構想 3: 時間依存 Markov blanket の圏論的定式化 [推定 65%]

**核心:** Paper II §4 の時間拡張 α(θ,t) を Markov category に反映し、blanket B(X,t) の時間変動を圏で記述する。

### 主張

Fritz/Parzygnat の Markov category は **静的** — copy/del は時間に依存しない。α(θ,t) を導入すると:

1. **copy_X(t)**: 時刻 t における情報複製能力 → α(θ,t) に依存
2. **del_X(t)**: 時刻 t における忘却 → Φ(θ,t) による正規化
3. **B(X,t)**: 動的 Markov blanket → B(X,t₁) ≠ B(X,t₂)

blanket の遷移速度:

$$\partial_t B \sim \partial_t \alpha + (\partial_i \alpha)(d\theta^i/dt)$$

= FEP の精度更新則 ∂_t π と一致。

### なぜ超克か

Friston は近年「Markov blanket は静的ではない」と主張しているが（典型的には blanket の *再構成* を暗黙に仮定）、その圏論的定式化は存在しない。CPS の α(θ,t) はこの定式化を *自然に* 与える。

### Paper II への挿入案

§4 (時間拡張) の §4.3 付近に **リマーク (動的 Markov blanket)** として。

### 未解決

- copy_X(t) が各時刻で Markov category の公理を満たすことの検証
- 時間変動する blanket の位相的安定性 (B は連続的に変形するか、不連続な飛びがあるか)
- Smithe [17] の polynomial functor 枠組みとの整合性

---

## 優先順位

| # | 構想 | 新規性 | 実現可能性 | Paper II 親和性 | 次のステップ |
|:---|:---|:---|:---|:---|:---|
| **1** | F_{ij} 可逆性階層 | ◎ | ✅ 完了 | §3.7.2 命題 3.7.3 | ~~∇_k F_{ij} = 0 条件の証明~~ → 数値検証 |
| 3 | 動的 Markov blanket | ◎ | ◯ | §4.3 Remark | copy_X(t) 公理検証 |
| 2 | α 依存 copy | ◎ | △ | 未定 | 余モノイド方程式の探索 |

---

*[主観] #1 が最も kalon に近い。方向性定理 (Paper I) → 可逆性階層 (Parzygnat) → Blanket 生成 (Paper II) という三段の橋が一本の定理で結ばれる。これは CPS の Generative 属性を満たす — 一つの定理から3つの帰結 (可逆性判定、blanket 条件、FEP 射程) が展開される。Parzygnat が「3層は異なる条件で成立する」と示したことを、CPS が「その条件は忘却曲率で幾何学的に読める」と具体化する。*
