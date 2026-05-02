# Codex 委託 brief: g^(α) 計量族の文献調査

## 目的

論文I「力としての忘却」で仮置きされている記号 `g^(α)` — α ∈ ℝ でパラメータ化された統計多様体上のリーマン計量族 — に、情報幾何学または関連分野の文献的裏付けがあるかを確認する。

## 背景

論文I §6.7 は α-SAM という最適化手法を提案しており、α-接続近傍を次で定義している:

```
B_ρ^(α)(θ) = {θ + ε : ε^T g^(α)(θ) ε ≤ ρ}
```

ここで g^(α) は「α-接続に対応するリーマン計量」と書かれているが、これは Amari の標準的情報幾何学と整合しない可能性がある:

- Amari (2016) の枠組みでは **α-接続 ∇^(α) は接続の 1 パラメータ族**であって、計量の族ではない
- **Čencov の定理 (1982)** により統計多様体上の不変計量は Fisher 計量が (スケール倍を除き) 一意
- α ≠ 0 の α-接続は一般に**計量接続ですらない** (∇^(α) g ≠ 0)

つまり「g^(α)」という記号は Amari の標準枠組みでは未定義である可能性が高い。

## 調査してほしいこと

**主問**: Amari-Čencov 以外の枠組みで、統計多様体 (あるいはその一般化) 上に α ∈ ℝ でパラメータ化された**計量族** g^(α) が定義される文献があるか?

### 具体的に当たってほしい候補

1. **Shima, H. (2007)** "The Geometry of Hessian Structures", World Scientific.
   - Hessian 多様体上の計量。Hessian potential ψ によって g_ij = ∂²ψ/∂θ^i∂θ^j と定義される
   - 問い: 異なる α-divergence の Hessian (D^(α) のような) を取ると α 依存の計量族が得られるか? それが Shima の枠組みで coherent か?

2. **Ay, N., Jost, J., Lê, H. V., Schwachhöfer, L. (2017)** "Information Geometry", Springer.
   - 非パラメトリック情報幾何の現代的定式化
   - 問い: この本の中で α-metric、generalized Fisher metric、α-dependent metric family 等の記述があるか?

3. **Calin, O., Udrişte, C. (2014)** "Geometric Modeling in Probability and Statistics", Springer.
   - 情報幾何の応用的文献
   - 問い: α-接続に付随する計量の独立構成の記述があるか?

4. **Naudts, J. (2011)** "Generalised Thermostatistics", Springer.
   - Tsallis / q-deformed 統計力学
   - 問い: q-deformed Fisher metric, φ-deformed metric が存在するか? これらは α-family と対応するか?

5. **最近の arXiv 論文 (2020-2026)**
   - 検索キーワード: "α-metric information geometry", "alpha-connection metric", "generalized Fisher metric", "Hessian information geometry alpha", "metric family statistical manifold"
   - 問い: 近年 (特に深層学習文脈) で統計多様体上の α-parameterized metric family を定義する論文があるか?

### 除外条件

以下は「g^(α) の発見」とみなさない:
- Fisher 計量の**異なる座標表現** (e-座標, m-座標) — これは同じ Fisher 計量なので除外
- α-divergence D^(α) そのもの — これは計量ではなく発散 (擬距離) なので除外
- Fisher-Rao 計量の一般化 (Wasserstein 計量等) で α 依存しないもの — 除外
- Tsallis q-metric のうち、**不変性公理を緩めたもの** — Paper I の設定 (統計多様体 + Fisher 計量) と整合しないので除外、ただし注記

## 出力形式

### もし発見した場合

```
FOUND: <文献の書誌情報>
定義の核心: <数式を含めて 5-10 行で定義を要約>
枠組み: <どの追加構造の上で成立するか>
Amari との関係: <等価 / 一般化 / 異なる枠組み のいずれか>
Paper I での使用可能性: <そのまま使える / 修正が必要 / 適用外>
引用カウント (可能なら): <Google Scholar 等で確認できれば>
```

### もし発見しなかった場合

```
NOT FOUND: Amari-Čencov 以外で coherent な g^(α) 計量族は文献調査の範囲で見つからなかった
検索した文献リスト:
  - <文献1>: <何を確認したか、何がなかったか>
  - <文献2>: ...
検索したキーワード:
  - <kw1>
  - <kw2>
結論: Paper I は g^(α) := g^(0) (Fisher 計量固定) で進めるべき
```

## 制約

- **時間**: 30-60 分で切る。深追いしすぎない
- **優先度**: 上記の 5 候補を順に当たり、見つかり次第報告
- **言語**: 出力は日本語
- **SOURCE 厳格**: 各文献の対応箇所 (ページ / 定理番号 / 式番号) を必ず明示
- **推測禁止**: 「こうだろう」「たぶん」は書かない。実際に読んだ箇所のみ報告

## 報告先

このファイルと同じディレクトリの `codex_report_g_alpha_literature.md` に書き出す。

## 補足

このタスクは論文I §6.7 の改訂に使う。発見の有無で改訂の方向が決まる:
- 発見 → その定義を採用し α-SAM を本来の形で構築
- 不発見 → g^(α) := g^(0) の Option C 簡約で α-SAM を再定式化
