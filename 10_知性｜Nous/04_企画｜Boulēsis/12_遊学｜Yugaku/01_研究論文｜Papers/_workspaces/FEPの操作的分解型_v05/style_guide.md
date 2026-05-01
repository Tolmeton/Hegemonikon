# Style Guide — FEPの操作的分解型 v05

## 親原理

本稿は HGK 内部語彙の紹介ではなく、FEP から見える操作空間の構造を外部読者に示す稿である。FEP から語名を直接導く主張へ戻らず、CE 層と CI 層を分けたまま強主張を維持する。

## 読者

- FEP / active inference の読者には、coordinate derivation と decomposition の違いを明示する。
- HGK / CCL を知らない読者には、語名より先に Basis / Directionality / 修飾座標 / 象限を見せる。
- H-series は補遺ではなく `S∩A` 象限の core として説明する。

## 書き換え規律

| 面 | 方針 |
|:---|:---|
| 旧24操作 | stale として残さず、48-frame の導入に更新する |
| CE/CI | CE は構造 claim、CI は命名 claim として分離する |
| Scale | L1 座標としては強く扱い、独立第9型としては再試まで保留する |
| blind protocol | 実行結果がない段階では validation として使わず、設計・再試予定として置く |
| two-layer filter | generator ではなく、局所的な接続制約として扱う |

## 禁止

- FEP から語名・CCL 呼称まで演繹したように書く。
- H-series を後付け appendix に落とす。
- blind protocol 未実行を実験成功のように扱う。
- 24 操作体系の完全性証明に戻る。
