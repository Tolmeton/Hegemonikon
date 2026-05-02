# HGK ハーネス v2 ロードマップ

※これは `09_能動｜Ergon` プロジェクトの実装計画文書である。

## 1. 現状診断

Theory / Design / Verify の刷新により、現行 HGK の問題はかなり明瞭になった。

- 45K tokens 級 prior を全状態に広く載せている
- Type 2 向け重量ハーネスがデフォルト化している
- `E` 軸の説明量に対して、`C/M` 軸の環境強制が薄い
- skill 候補数が膨らみ、`boot` 時点の選択複雑性が増えている

したがって v2 の目的は「もっと厚いルールを書くこと」ではない。**不均一な忘却場を再設計し、boot/bye の強度を状態依存にすること**である。

## 2. 6 原則に基づく改善計画

| 原則 | 実装方針 | 主要メトリクス |
|:---|:---|:---|
| **P1: 忘却場の不均一性を最大化** | `C` を少数の高強度 kernel に集中し、`E` の長文化を蒸留する | prior token の分散、禁止条件の hit rate |
| **P2: 状態依存ロード** | Type 1/2/3 ごとに `boot` profile を分ける | state 切替精度、task 完遂率 |
| **P3: 逆 U 字の維持** | prior 占有率を 2-5% に保つ | boot token ratio、drift |
| **P4: C を Hook で環境強制** | prose rule を Hook / validator / tool filter へ移植 | human reminder 依存率、hook block 数 |
| **P5: 3 軸安定性** | `C/E/M` を別々に監視し、どの軸が壊れたか可視化する | `$d_C,d_E,d_M$` |
| **P6: RG 蒸留** | Session 終了時に fixed point だけ残す | handoff 再現性、summary 長 |

この 6 原則は slogan ではない。ハーネス設計学では、`P1-P6` はそれぞれ **何を削り、何を残し、何を環境へ移すか**を決める設計レバーである。v2 の刷新は「ルールを増やす計画」ではなく、**過大な `E_H` を削って `C/M` の作用密度を上げる再配線**として読むべきである。

### 2.1 P1-P6 を v2 の作業面へ落とす

| 原則 | 具体タスク | 期待する変化 |
|:---|:---|:---|
| **P1** | core prior と rules を分離し、常駐面を縮める | Type 1 での過負荷低減 |
| **P2** | Type 1/2/3 判定に応じて `boot/bye` 深度を切り替える | 一律重量運用の停止 |
| **P3** | drift と token ratio を同時監視する | 軽すぎ/重すぎの両端回避 |
| **P4** | prose rule を hook / validator / filter へ移植する | human reminder 依存の低下 |
| **P5** | `C/E/M` を別メトリクスとして可視化する | 壊れた面の局所修理が可能 |
| **P6** | `bye` を fixed point だけ残す schema へ寄せる | handoff 再現性の上昇 |

## 3. 実行 Wave

### Wave 1: 計測基盤

- `boot` 時の token 占有率を測る
- Handoff の再現性を測る
- skill 候補数と実使用数の差分を測る

### Wave 2: `boot` 軽量化

- 常時ロードする rule を `C/E/M` に再分類する
- `E` の長文化を縮約し、`C` の kernel だけ常駐化する
- Type 1 用の軽量 profile を先に作る
- `Core prior ~45K tokens` と `Rules 166KB` を分離して扱い、削る対象と残す対象を混同しない

### Wave 3: Hook 化

- `C` 軸に属する規則を Hook / tool filter / validator に移植する
- 「説明して守らせる」から「通さない」に移る
- Hook は増やし続けるのでなく、**最少核を保ったまま密度を上げる**方針を採る

### Wave 4: 状態依存ロード

- Paper X Type 1/2/3 判定器を導入する
- `boot` profile を type ごとに切り替える
- `bye` depth も type ごとに変える

### Wave 5: RG 蒸留

- Session handoff を fixed point 中心に再設計する
- `constraint_delta / encoding_summary / mechanism_receipt` を分離する
- Fractal Summary と Handoff を同一スキーマ系に寄せる

## 4. 実装項目

| 項目 | 内容 | 対応原則 |
|:---|:---|:---|
| `boot profile` 導入 | Type 別ロード設定 | P2, P3 |
| `tool filter` 強化 | capability の環境強制 | P1, P4 |
| `hook inventory` | ルールを Hook 化できる候補の棚卸し | P4 |
| `bye schema` 更新 | C/E/M 3 軸の分離 | P5, P6 |
| `skill surface pruning` | 常時 expose する候補を削減 | P1, P3 |
| `drift dashboard` | Drift と token ratio の同時計測 | P2, P3, P5 |
| `tau quotient` | 類似 skill の `τ-Invariance` 圧縮 | P1, P6 |

## 5. 完了条件

v2 完了の判定は、次の 5 条件で行う。

1. Type 1/2/3 のどれかに応じて `boot` 強度が切り替わる
2. prior 占有率が 2-5% を安定維持する
3. `C` に属する高重要制約が Hook へ移植されている
4. `bye` が `C/E/M` の fixed point を残せる
5. Handoff からの再現性が現行より改善する

## 6. 現在地

- 理論刷新: 完了
- 設計刷新: 完了
- 批評と検証: 完了
- **次の工程**: Wave 1 の計測基盤に着手

---
*Created: 2026-03-09*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
