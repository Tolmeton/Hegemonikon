# g^(α) 計量族の文献調査報告

## 0. 判定

**NOT FOUND:** Amari-Čencov 以外で coherent な `g^(α)` 計量族は、この調査範囲では確認できなかった。

[確信: 高] 古典的な情報幾何の核では、`α` は **接続の 1 パラメータ族**に掛かっており、計量には掛かっていない。公開アクセスできた一次・準一次ソースを突き合わせると、見つかるのは一貫して「固定計量 + α-接続族」か、あるいは `q` / `κ` / `ϕ` など **別の変形パラメータ**で定まる一般化計量である。したがって、Paper I §6.7 の `g^(α)` をそのまま文献定義として採るのは危うい。現時点では **`g^(α) := g^(0)`（Fisher 計量固定）で進める**のが最も defensible である。

## 1. 核心証拠

| 文献 | 確認箇所 | SOURCE で確認できたこと | 含意 |
|---|---|---|---|
| Ay, Jost, Lê, Schwachhöfer, *Information geometry and sufficient statistics* (arXiv:1207.6736; 2017 本の基礎稿) | Thm. 2.10(2), Thm. 3.5 | Thm. 2.10(2) は「十分統計で不変な weakly continuous quadratic form は Fisher quadratic form の定数倍に限る」と述べる。Thm. 3.5 は Fisher metric と Amari-Chentsov tensor の不変性を確認する。 | 不変性公理を保つ限り、古典的統計多様体で `g^(α)` なる別個の計量族を立てる余地はない。`α` で動くのは connection 側である。 |
| Shima, *The Geometry of Hessian Structures* (2007) | Def. 2.1, Prop. 2.2, pp. 14-15（公開スキャン） | Hessian structure は局所ポテンシャル `φ` を持ち、計量は `g_{ij} = ∂_i∂_j φ` で与えられる。アクセス可能スキャン全体に対するテキスト検索では `alpha` / `α` 相当の記述は見当たらなかった。 | Hessian 幾何では「ポテンシャルの Hessian としての計量」はあるが、Amari の `α` と連動する `g^(α)` は見つからない。 |
| Calin, Udrişte, *Geometric Modeling in Probability and Statistics* (2014) | Ch. 8 “Dualistic Structure”, Abstract, pp. 223-255（Springer preview） | 抽象は「Fisher information matrix は任意の Riemannian metric `g` に置き換えられ、`∇^{(-1)}`, `∇^{(1)}` は dual pair `∇, ∇*` に置き換わる」と述べる。 | ここでも構図は「1つの metric + dual connection pair」であり、`α` に応じて metric を動かす話ではない。 |
| Vigelis, de Souza, Cavalcante, *New Metric and Connections in Statistical Manifolds* (arXiv:1511.01176) | Eq. (1), Eq. (13), Eq. (16), Sec. 3 | `ϕ`-family から新しい metric を定義し、その divergence から dual connection `D^{(1)}, D^{(-1)}` を得て、Eq. (16) で `α`-connections を定義している。`α=0` は Levi-Civita connection。 | 一般化された setting でも、`α` は **既に選ばれた metric の上の connection family** に掛かっている。`g^(α)` ではない。 |

## 2. 近傍発見（ただし Paper I の `g^(α)` にはならない）

### 2.1 Naudts 系の ϕ / q 変形

| 文献 | 定義の核心 | 枠組み | Amari との関係 | Paper I での使用可能性 |
|---|---|---|---|---|
| Naudts, *Generalised Exponential Families and Associated Entropy Functions* (Entropy 2008) | Sec. 10 Eq. (48) で metric tensor を導入。Sec. 12 Eq. (60) で generalized Fisher information、Eq. (63) で `I_{ij}(θ) = z(θ) g_{ij}(θ) = z(θ)^2 σ_{ij}(θ)` を示す。 | 一般化 entropy・escort probability・Massieu 関数を備えた generalized exponential family。 | Fisher の一般化ではあるが、`α`-connection に対応する metric family ではない。パラメータは entropy / escort 構造から来る。 | **修正が必要。** Paper I の `α` をそのまま移植できない。 |
| Amari, Ohara, Matsuzoe, *Geometry of deformed exponential families* (Physica A 2012) | p. 4308-4309, Introduction. 「invariant geometry では Fisher information が唯一の Riemannian metric」であり、`α`-connections が付随する一方、`q`-family では conformal に関連した別幾何が現れる。 | deformed exponential family / q-family。 | `α`-geometry を参照しつつも、metric の変形は `q`-family や conformal 変換により現れる。 | **適用外。** `α`-metric ではなく、`q`-deformation の話。 |

### 2.2 κ 変形

| 文献 | 定義の核心 | 枠組み | Amari との関係 | Paper I での使用可能性 |
|---|---|---|---|---|
| Wada, Scarfone, *Information Geometry on the κ-Thermostatistics* (Entropy 2015) | Sec. 3, Eq. (78) で `κ`-generalized metric を `κ`-deformed θ-potential の Hessian として定義。Eq. (81), (88) で `κ`-deformed e/m connection、Eq. (100) で grand-canonical ensemble 上の具体形。 | `κ`-exponential family, `κ`-escort distribution, `κ`-entropy。 | Amari の dual flatness を `κ` setting に移した一般化。`α` ではなく `κ` が metric を動かす。 | **適用外。** 追加構造が重く、Paper I の統計多様体 + Fisher 計量とは別世界。 |

### 2.3 最近の非パラメトリック変形多様体

| 文献 | 定義の核心 | 枠組み | Amari との関係 | Paper I での使用可能性 |
|---|---|---|---|---|
| Newton, *A two-parameter family of non-parametric, deformed exponential manifolds* (Information Geometry 2024) | Abstract と Sec. 1, Sec. 3-4。Amari の `α`-divergences を滑らかに扱える 2-parameter deformed manifold を作るが、Cor. 1 では tensor field として **Fisher-Rao metric** が主役。 | non-parametric deformed manifolds, Sobolev model spaces, `η`-deformed log/exp。 | `α`-divergence の smoothness を広げる一般化だが、metric 自体は `α` family ではない。 | **適用外。** `α` を divergence/embedding 側に使っており、`g^(α)` の直接根拠にはならない。 |

## 3. 候補ごとの確認メモ

| 候補 | 実際に確認した箇所 | 結果 |
|---|---|---|
| Shima (2007) | Def. 2.1, Prop. 2.2, pp. 14-15; スキャン全文検索 | Hessian potential 由来の metric は確認。`α` 依存 metric family は未確認。 |
| Ay et al. (2017) | 2012 基礎稿の Thm. 2.10, Thm. 3.5 | Fisher quadratic form の一意性を確認。`α`-metric なし。 |
| Calin–Udrişte (2014) | Ch. 8 Abstract, pp. 223-255; book overview | `g` と dual connections の抽象化は確認。`g^(α)` 記述は未確認。 |
| Naudts (2011) | Springer book preview; Naudts 2008; Naudts 系を継承した 2012, 2015 論文 | generalized Fisher / escort / deformed metrics は確認。だが `α`-family ではない。 |
| Recent 2020-2026 | Web 検索 + Newton 2024 を精読 | `α`-divergence を扱う recent manifolds はあるが、metric は Fisher-Rao のまま。 |

## 4. 検索したキーワード

`"alpha metric" "information geometry"`, `"alpha-connection metric"`, `"generalized Fisher metric" statistical manifold`, `"metric family" "statistical manifold"`, `"Hessian information geometry alpha"`, `"q-deformed Fisher metric"`, `"phi-deformed metric"`, `"two-parameter deformed exponential manifolds"`, `"κ-generalized metric information geometry"`.

## 5. 結論

[確信: 高] 調査範囲では、**Amari の `α`-connection parameter と同じ `α` で classical statistical manifold 上の Riemannian metric を動かす先行定義**は見つからなかった。見つかった一般化はすべて、

1. **Fisher / generalized Fisher を固定し、その上で `α`-connections を動かす型**  
2. **`q` / `κ` / `ϕ` / `η` など別パラメータで metric を変形する型**

のどちらかである。

したがって、論文 I §6.7 の改訂方針としては、現段階では

> `g^(α) := g^(0)` として Fisher 計量を固定し、`α` は connection / divergence 側だけに残す

が最も安全である。

## 6. 主要 SOURCE

1. Ay, N., Jost, J., Lê, H.V., Schwachhöfer, L., *Information geometry and sufficient statistics*, arXiv:1207.6736.  
   URL: https://ar5iv.labs.arxiv.org/html/1207.6736

2. Shima, H., *The Geometry of Hessian Structures* (2007), accessible scan.  
   URL: https://epdf.pub/the-geometry-of-hessian-structures.html

3. Calin, O., Udrişte, C., *Geometric Modeling in Probability and Statistics* (2014), book + chapter preview.  
   URLs:  
   https://link.springer.com/book/10.1007/978-3-319-07779-6  
   https://link.springer.com/chapter/10.1007/978-3-319-07779-6_8

4. Vigelis, R.F., de Souza, D.C., Cavalcante, C.C., *New Metric and Connections in Statistical Manifolds*, arXiv:1511.01176.  
   URL: https://ar5iv.org/pdf/1511.01176

5. Naudts, J., *Generalised Exponential Families and Associated Entropy Functions*, *Entropy* 10(3), 131-149 (2008).  
   URL: https://www.mdpi.com/1099-4300/10/3/131

6. Amari, S.-I., Ohara, A., Matsuzoe, H., *Geometry of deformed exponential families: Invariant, dually-flat and conformal geometries*, *Physica A* 391(18), 4308-4319 (2012).  
   URL: https://bsi-ni.brain.riken.jp/database/file/316/321.pdf

7. Wada, T., Scarfone, A.M., *Information Geometry on the κ-Thermostatistics*, *Entropy* 17(3), 1204-1228 (2015).  
   URL: https://www.mdpi.com/1099-4300/17/3/1204

8. Newton, N.J., *A two-parameter family of non-parametric, deformed exponential manifolds*, *Information Geometry* 7, 171-186 (2024).  
   URL: https://link.springer.com/article/10.1007/s41884-022-00079-5
