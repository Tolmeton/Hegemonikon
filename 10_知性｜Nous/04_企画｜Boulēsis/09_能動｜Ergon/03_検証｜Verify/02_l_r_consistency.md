# boot/bye 整合性検証

※これは `09_能動｜Ergon` プロジェクトの検証文書である。

## 1. 検証対象

本稿で検証するのは、旧来の「Plan/Task 型の整合性」だけではない。**Session スケールの `boot⊣bye` が、Task/Meso スケールの `L⊣R` と同じ不動点構造を保てているか**を確認する。

検証項目は 3 つある。

1. `boot` が必要な `C/E/M` を正しくロードしているか
2. `bye` が `C/E/M` の核を正しく残しているか
3. 連続セッションで Drift と Context Rot を抑えられているか

## 2. `boot` 側の型対応

`L (boot)` が担うべき kernel は次の 3 軸である。

| boot 入力 | 役割 | `L` スキーマとの対応 |
|:---|:---|:---|
| Rules / Nomoi | Constraint kernel | `constraint_kernel` |
| Output style / schema / handoff format | Encoding kernel | `encoding_kernel` |
| Hook / tool policy / validator | Mechanism kernel | `mechanism_kernel` |

この対応が崩れると、`boot` は「何でも読む巨大 prompt」になり、Task/Meso の `L` と同型でなくなる。

## 3. `bye` 側の型対応

`R (bye)` が Session 終了時に残すべき核も同様に 3 軸へ分かれる。

| bye 出力 | 役割 | `R` スキーマとの対応 |
|:---|:---|:---|
| Rule Delta / 禁止条件の更新 | Constraint delta | `constraint_delta` |
| Handoff / ROM / summary | Encoding summary | `encoding_summary` |
| 何が効いたかの記録 | Mechanism receipt | `mechanism_receipt` |

`bye` が prose の総括だけになり、`constraint_delta` や `mechanism_receipt` を落とすと、次の `boot` で同じ場が再構成できない。

## 4. Drift 測定

Session 間 Drift は、`bye_t` で残した kernel と `boot_{t+1}` で再ロードされた kernel のズレとして測る。

$$
\text{Drift}_{t \to t+1}
= d_C + d_E + d_M
$$

ここで:

- $d_C$: 禁止条件・許可条件のズレ
- $d_E$: schema / handoff / summary 形式のズレ
- $d_M$: Hook / tool / validator のズレ

Paper X の参照点では、**Drift ≈ 0.2** は「一致しすぎても、ずれすぎてもいない」中域として読むのが自然である。完全一致 `0` はハーネスが次回の状況差を吸収できていない恐れがあり、逆に大きすぎる Drift は Context Rot そのものになる。

ここでの `0.2` は prior 占有率の話ではない。`boot⊣bye` が残した kernel と再構成された kernel の**正規化差分**であり、Session 持続性の健全域を示す参照値である。

### 実務上の観測指標

| 指標 | 意味 | Drift の主因 |
|:---|:---|:---|
| 同じ禁止条件が次セッションで失われる | C 崩れ | `$d_C$` |
| Handoff を読んでも再開位置が曖昧 | E 崩れ | `$d_E$` |
| 前回効いた Hook が今回効かない | M 崩れ | `$d_M$` |

## 5. Context Rot 対策の検証

Paper X の観点から見ると、Context Rot 対策は `boot⊣bye` の品質検証である。

### Reduce

- 何を検証するか: `bye` が冗長ログを削り、固定点構造だけを残せているか
- 失敗症状: summary が長いのに次行動が決まらない

### Offload

- 何を検証するか: 必要な状態が作業面の外へ保存され、次回 `boot` で再ロードできるか
- 失敗症状: session 内では分かるが、再開時に全部読み直しになる

### Isolate

- 何を検証するか: 子 blanket の raw transcript を親へ混入させず、distilled result のみ返せているか
- 失敗症状: サブエージェントを使うほど親セッションが肥大化する

### boot/bye 観点での解釈

- `boot` が重すぎると Reduce が失敗し、開始時点で Rot を内包する
- `bye` が長すぎると Offload が失敗し、保存したつもりのものが再利用不能になる
- 子系の結果を summary でなく transcript ごと返すと Isolate が失敗し、Drift が次セッションへ連鎖する

## 6. 三角恒等式の Session スケール検証

### 恒等式 1: $(\varepsilon L) \circ (L\eta) = \text{id}_L$

Session スケールでは次のように読む。

> `boot → execute → bye → re-boot` しても、同じ session family が再生されるか

検証ポイント:

- 初期ロードされる `C/E/M` が同等か
- 同じ task routing が再現されるか

### 恒等式 2: $(R\varepsilon) \circ (\eta R) = \text{id}_R$

Session スケールでは次のように読む。

> `bye → re-boot → re-execute → re-bye` しても、同じ Handoff kernel に戻るか

検証ポイント:

- `constraint_delta` が保たれるか
- `encoding_summary` が再読可能か
- `mechanism_receipt` が次回の行動を拘束できるか

## 7. 判定

| 項目 | 判定 | コメント |
|:---|:---|:---|
| `boot` の型対応 | PASS | `C/E/M` で再記述可能 |
| `bye` の型対応 | PASS | Handoff を 3 軸に分解できる |
| Drift 測定可能性 | PASS | `$d_C + d_E + d_M$` で定義できる |
| Drift 参照帯 | PASS | Paper X 参照値 `≈ 0.2` を健全域の目安に置ける |
| Context Rot 対策との接続 | PASS | Reduce/Offload/Isolate に落ちる |
| 現行実装の安定性 | 要改善 | Type 依存ロードが未実装 |

**結論**:

`boot⊣bye` は理論的には `L⊣R` と整合する。問題は整合性そのものではなく、**現行 HGK が全状態へ同じ強度の boot をかけていること**である。

---
*Created: 2026-03-10*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
