# Detailed Feedback 介入準備ノート

> 対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/`
>
> この文書の役割は、**Detailed Feedback を本論から切り離し、介入実験ラインとして次段へ送ること**である。

## 1. 位置づけ

今回の距離論文では、Detailed Feedback を結論に混ぜない。理由は単純で、現時点の PDDL-INSTRUCT 由来の強い主張は **外部テンプレートとしては有用だが、Code ドメインでは未検証** だからである。

本稿で残すのは次の 2 命題だけ。

| 命題 | 今回の扱い |
|:--|:--|
| `P33`: Detailed Feedback が Θ を大幅に下げるか | 未検証の推定。次稿入口 |
| `P34`: Ξ が高いほど Detailed Feedback が効くか | 未検証の推定。次稿入口 |

したがって、本稿の結論は「Detailed Feedback は効くはずだ」では終わらない。終わり方は「中間帯を診断したので、次はその帯域に介入する因果実験が必要である」である。

## 2. Detailed Feedback の定義

Binary と Detailed の差を曖昧にしないため、Detailed Feedback は以下の 3 成分を**同時に**含むものとして固定する。

| 成分 | 役割 | Binary との差 |
|:--|:--|:--|
| 欠落座標 | 何を忘れたか | Binary は欠落の有無しか言わない |
| U-pattern | どの忘却型か | Binary は忘却の型を区別しない |
| 修復助言 | 次に何を補えばよいか | Binary は回復方向を持たない |

Operational には次の形式:

```text
Missing coordinates: ...
U-pattern: ...
Repair hint: ...
```

この 3 成分が揃わない限り、名称が feedback でも Detailed とは呼ばない。

## 3. 介入実験ライン

介入の基底は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/intervention_experiment.py` と `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/intervention_ochema.py` にある `U / G / S` 比較である。

| 戦略 | 固定されるもの | 変わるもの |
|:--|:--|:--|
| `U` | 総情報予算 | turn ごとの保持率は一様 |
| `G` | 総情報予算 | 新しい turn に重みを寄せる |
| `S` | 総情報予算 | 一部 turn を全保持し、それ以外を除去する |

この 3 戦略でまず守るべき条件:

1. 総予算は固定
2. 比較対象は配分だけ
3. Detailed Feedback を入れるまでは、追加変数を増やさない

## 4. 何を足すと Detailed になるか

`U / G / S` の上に次の 1 層を追加したとき、初めて「Binary ではなく Detailed」と言える。

| 層 | 内容 | 必須か |
|:--|:--|:--|
| Binary 層 | OK / NG, keep / drop のみ | 単独では不十分 |
| Detailed 層 | 欠落座標 + U-pattern + 修復助言 | **必須** |

つまり介入比較は次の 4 条件が最小になる。

| 条件 | 中身 |
|:--|:--|
| `baseline` | 配分のみ。feedback なし |
| `binary` | 配分 + Binary feedback |
| `detailed` | 配分 + Detailed feedback |
| `detailed_high_xi` | Ξ が高い帯域に限定して Detailed |

ここで初めて `P33` と `P34` を別々に測れる。

## 5. 最小因果系

次段で必要な最小因果系はこれで足りる。

1. 同一タスク集合
2. 同一総予算
3. 同一モデル
4. `U / G / S` の配分差
5. `none / binary / detailed` の feedback 差
6. `Ξ` の高低による層別

観測値は少なくとも 3 つ必要。

| 観測値 | 意味 |
|:--|:--|
| `P` | パッチ一致度または成功率 |
| `Θ` | 失敗率由来の忘却パラメータ |
| `ΔP_high_xi - ΔP_low_xi` | `P34` の因果差 |

## 6. なぜ本論に入れないか

Detailed Feedback を今回の本論から外す理由は 3 つある。

| 理由 | 内容 |
|:--|:--|
| 焦点保持 | 距離論文の核は中間帯崩れの診断であり、介入ではない |
| 検証不足 | Code ドメインでの `P33/P34` は未実測 |
| 読者負荷 | Structural Attention / Phase C / PDDL 参照を一度に入れると論点が拡散する |

したがって、このノートの役割は「まだやっていない」を言い訳することではない。**次に何をやれば因果が立つかを、先に決めておくこと**である。

## 7. 受け入れ条件

この準備ノートが満たすべき条件は次の通り。

1. Detailed Feedback の定義が Binary と混ざらない
2. `U / G / S` が総予算固定の比較であると明記される
3. `P33/P34` が本論の結論ではなく、次稿入口だと明記される
4. 次に必要な最小実験条件が、そのまま実装指示に落ちる

## 8. 結論

Detailed Feedback は Lēthē にとって重要だが、**今回の距離論文の主役ではない**。今回やるべきことは、距離診断で見えた盲点に対して、次にどんな介入を設計すれば因果が立つかを固定しておくことである。
