# T-097 Connection Map Legend

作成日: 2026-04-27  
対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku`

## 決定核

この legend は、`T-098` の 7x17 一次マトリクスで各セルを最低限
`射影層 / 向き / 強度 / 状態`
の 4 軸で埋められるようにするための正本である。

判断の原則は次の 3 点:

1. ノード集合は `T-096` の canonical inventory だけを使う。
2. 1 セル 1 主記録を原則とし、複数の橋がありうる場合は最も強いものを主記録にし、残りは `note` に退避する。
3. `強度` は「どれだけ深くつながるか」、`状態` は「それが現物 corpus に既に書かれているか」を分離して扱う。

SOURCE:
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/PINAKAS_TASK.yaml` の `T-095`-`T-100`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/ビジョン.md` §3-§4
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/T-096_canonical_inventory_2026-04-23.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/PINAKAS_SEED.yaml` の `S-017`

## A. ノード ID

### A1. Paper 側 (`P-*`)

| ID | タイトル |
|:--|:--|
| `P-I` | 力としての忘却 |
| `P-II` | 相補性は忘却である |
| `P-III` | Markov圏の向こう側 |
| `P-IV` | なぜ効果量は小さいか |
| `P-V` | 繰り込みは忘却である |
| `P-VI` | 行為可能性は忘却である |
| `P-VII` | 知覚は忘却である |

### A2. Essay 側 (`E-*`)

| ID | タイトル |
|:--|:--|
| `E-01` | Mythos分析エッセイ |
| `E-02` | なぜバカほどビジネス書を好むのか |
| `E-03` | センスがないと生きるのは大変 |
| `E-04` | バカであるほど他人のあり方にこだわる |
| `E-05` | バカの一つ覚え |
| `E-06` | バカは伝染する |
| `E-07` | バカは右を見たら左を忘れる |
| `E-08` | バカをやめたいなら構造を見ろ |
| `E-09` | 博学野郎はおバカさん |
| `E-10` | 愚か者ほど不確定を嫌う |
| `E-11` | 狂っているは褒め言葉 |
| `E-12` | 疑えさすれば救われる |
| `E-13` | 美しさは真理の証か |
| `E-14` | 言葉遊びはやめましょう |
| `E-15` | 近道を求めるほどバカになる |
| `E-16` | 馬鹿であるほど自信をもつ |
| `E-17` | 馬鹿な奴ほど世界を否定する |

## B. セル記法

`T-098` の 7x17 マトリクスでは、各セルを次の 1 行で記述する。

```text
paper_id | essay_id | proj | dir | str | st | phase | l2_hook | note
```

必須列は `paper_id | essay_id | proj | dir | str | st`。  
`phase | l2_hook | note` は補助列で、わからなければ空欄でよい。

## C. 射影層 (`proj`)

`proj` は「この接続をどの層で回収すると最も強いか」を表す。

| 値 | 意味 | 用途 |
|:--|:--|:--|
| `L0` | 一般読者向け概念射影が主 | note / エッセイ / X thread で先に効く |
| `L1` | 論文 spine / 命題 / 節構成で回収するのが主 | 7 本の Paper 側へ直結する |
| `L2` | 実験 / OSS / 実装面で回収するのが主 | 実装・計測・公開 repo で効く |

運用規則:
- 迷ったら `L1` を優先する。今回の母地図は `Paper × Essay` だからである。
- `L2` を主に置くのは、Paper/Essay の対応そのものよりも実装・実験への落ちが主価値である場合だけ。

## D. 向き (`dir`)

`dir` は「どちらがどちらへ donor になるか」を表す。

| 値 | 意味 |
|:--|:--|
| `E→P` | Essay 側の直観・語り・例が Paper 側へ吸収される |
| `P→E` | Paper 側の定理・構造が Essay 側へ射影される |
| `E↔P` | 双方向。片側だけでは接続を言い尽くせない |
| `—` | 現時点では接続なし |

## E. 強度 (`str`)

`str` は「どれだけ深くつながるか」の強さで、証拠状態とは別である。

| 値 | 意味 | 判断基準 |
|:--|:--|:--|
| `3` | 強結合 | 同じ spine / 定理核 / 章核に直接回収できる |
| `2` | 中結合 | 明確な橋はあるが、補題・橋渡し文・再配線が必要 |
| `1` | 弱結合 | モチーフ共有や stressor としては有効だが主射ではない |
| `0` | 無結合 | 現時点ではつながりを置かない |

## F. 状態 (`st`)

`st` は「その接続が corpus にどう存在しているか」を表す。

| 値 | 意味 |
|:--|:--|
| `anchored` | 現物の本文・構成・meta から既に回収できる |
| `candidate` | 接続は濃厚だが、まだ本文や台帳へは未実装 |
| `blank` | いまは空欄として扱う |

運用規則:
- `str=0` のときは `st=blank` を使う。
- `anchored` は「書いてあること」の判定であり、「正しいこと」の判定ではない。

## G. 補助列

### G1. `phase`

`phase` は `Papers/ビジョン.md` の Phase 0-4 のどこで使うと効くかを付す。

| 値 | 意味 |
|:--|:--|
| `0` | Mythos 波乗り |
| `1` | 忘却論基礎の浸透 |
| `2` | LLM 身体性の展開 |
| `3` | 力としての忘却 |
| `4` | OSS / 書籍化 |

### G2. `l2_hook`

`l2_hook` は L2 へ伸びる足場があるときだけ使う。

| 値 | 意味 |
|:--|:--|
| `none` | 今は L2 足場なし |
| `exp` | 実験・計測へ伸びる |
| `impl` | 実装・コードへ伸びる |
| `oss` | OSS / 公開 artifact へ伸びる |

## H. 記入テンプレート

`T-098` ではまず次の形式で 119 セルを埋める。

```text
P-I | E-15 | L1 | E→P | 2 | candidate | 3 | none | Tier 1 candidate from S-017
P-II | E-07 | L1 | E→P | 2 | candidate | 3 | none | Tier 1 candidate from S-017
P-III | E-06 | L1 | E→P | 2 | candidate | 3 | none | Tier 1 candidate from S-017
P-IV | E-01 | —  | —   | 0 | blank     |   |      |
```

## I. Sanity Check

`T-098` 開始前の sanity check として、少なくとも次の 6 件を先に固定する。

| paper_id | essay_id | proj | dir | str | st | phase | l2_hook | note |
|:--|:--|:--|:--|:--:|:--|:--:|:--|:--|
| `P-VII` | `E-07` | `L1` | `E→P` | `3` | `anchored` | `1` | `none` | `S-017` / `T-095` の既知 3 本の 1 つ |
| `P-VII` | `E-10` | `L1` | `E→P` | `3` | `anchored` | `1` | `none` | 「不確定」ライン |
| `P-VII` | `E-05` | `L1` | `E→P` | `3` | `anchored` | `1` | `none` | 「一つ覚え」ライン |
| `P-I` | `E-15` | `L1` | `E→P` | `2` | `candidate` | `3` | `none` | `S-017` Tier 1 候補 |
| `P-II` | `E-07` | `L1` | `E→P` | `2` | `candidate` | `3` | `none` | `S-017` Tier 1 候補 |
| `P-III` | `E-06` | `L1` | `E→P` | `2` | `candidate` | `3` | `none` | `S-017` Tier 1 候補 |

## J. 次段への手渡し

`T-098` はこの legend をそのまま schema として使い、全 119 セルを
`anchored / candidate / blank`
のいずれかへ最低限分類する。

`T-099` ではこの一次マトリクスを逆向きに読み替え、
「各 Essay がどの Paper を主射として要求するか」
へ圧縮する。
