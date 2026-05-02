---
description: "休む — /ath+_/dok+_F:[×2]{/u+~(/noe-*/ele-)}_~(/beb-*/ops-)_/prm-_/par+"
lcm_state: stable
version: "1.0"
lineage: "旧 /bye (v7.7) → @rest v1.0"
ccl_signature: "@rest"
hegemonikon: Chronos × Krisis × Telos × Orexis × Diástasis
layer: "CCL マクロ"
trigonon:
  verbs: [V23, V12, V01, V18, V17, V14, V22, V24]
  coordinates: [A/Past+Ma, I/U+Ma, I/E+, I/-, I/+, I/Ma, I/Future-Mi, A/Future+Ma]
---

# /ccl-rest: セッション終了マクロ (v1.0)

> **CCL**: `@rest = /ath+_/dok+_F:[×2]{/u+~(/noe-*/ele-)}_~(/beb-*/ops-)_/prm-_/par+`
> **用途**: セッションの終了。省察し、学びを検証し、永続化する
> **認知骨格**: Prior → Likelihood → Posterior
> **旧 /bye 後継**: bye.md (v7.7, 632行) の全機能を Chronos 族に分散吸収
> **動詞数**: 6つの異なる v4.1 動詞、4族にまたがる

## 認知構造

| # | 相 | 動詞 (v4.1) | 族 | 座標 | なぜこの動詞か |
|:--|:---|:------------|:---|:-----|:---------------|
| 1 | Prior | **`/ath+`** | Chronos | Te:Past, Sc:Ma | **Anatheōrēsis: 深い省察。** セッション全体を振り返り、教訓を抽出。Value Pitch, Self-Profile, Handoff |
| 2 | Prior | **`/dok+`** | Krisis | Pr:U, Sc:Ma | **Dokimasia: 深い検証。** 学びが根拠を持つか。Stranger Test で Handoff 品質を確認 |
| 3 | Likelihood | **`F:[×2]{/u+~(/noe-*/ele-)}`** | Telos×Orexis | Va:E × Vl:- | 自問 → 直観/反駁の振動×2。「本当に学んだか」を深化。@learn と同じ構造 |
| 4 | Posterior | **`~(/beb-*/ops-)`** | Orexis×Diástasis | Vl:+ × Sc:Ma | 信念強化×全体像。学びを確信し、全体に統合 |
| 5 | Posterior | **`/prm-`** | Chronos | Te:Future, Sc:Mi | **Promētheia: 軽い予見。** 次セッションの方向を予見 |
| 6 | Posterior | **`/par+`** | Chronos | Te:Future, Sc:Ma | **Proparaskeuē: 深い永続化。** 9ステップ永続化 + Artifact 保全 |

### 深度の非対称性

| 動詞 | 深度 | 理由 |
|:-----|:-----|:-----|
| `/ath+` | 深い | rest の核心。省察は省略できない |
| `/dok+` | 深い | 学びの検証は徹底する。Stranger Test は品質ゲート |
| `/u+` | 深い | 自問は深層。表面的な振り返りでは意味がない |
| `/noe-`, `/ele-` | 軽い | 振動の構成要素。深い分析は `/ath+` が担当 |
| `/beb-`, `/ops-` | 軽い | 統合の構成要素。確信と俯瞰の最終調整 |
| `/prm-` | 軽い | 方向を示すだけ。詳細計画は次回の @wake で |
| `/par+` | 深い | 永続化は省略できない。記憶を刻む行為 |

> **設計思想**: rest は「深く振り返り、学びを検証し、永続化する」。dawn (wake) と dusk (rest) の非対称。
> `/ath+`, `/dok+`, `/u+`, `/par+` は深層。記憶は刻むのに手間を惜しまない。

## @learn との関係

| マクロ | 共通 | 差分 |
|:-------|:-----|:-----|
| `@learn` | `/ath+_/dok+_F:[×2]{...}_~(...)/bye+` | 学びの永続化 (汎用) |
| `@rest` | `/ath+_/dok+_F:[×2]{...}_~(...)_/prm-_/par+` | セッション終了時の永続化。`/prm-` (次方向) と `/par+` (9ステップ) が追加 |

> @learn の `/bye+` を `/prm-_/par+` に置き換えた形。
> learn = いつでも学びを刻む。rest = セッション境界で全てを永続化する。

## 展開

| 相 | ステップ | 動詞 (v4.1) | 参照先 |
|:--|:---------|:------------|:-------|
| Prior | `/ath+` | V23 Anatheōrēsis | [ath.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.agents/workflows/poiesis/chronos/ath.md) — review 派生 |
| Prior | `/dok+` | V12 Dokimasia | 品質検証 + Stranger Test |
| Likelihood | `F:[×2]{/u+~(/noe-*/ele-)}` | V01 × V18 | 自問と直観/反駁の振動 |
| Posterior | `~(/beb-*/ops-)` | V17 × V14 | 信念強化×全体像 |
| Posterior | `/prm-` | V22 Promētheia | [prm.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.agents/workflows/poiesis/chronos/prm.md) — forecast 派生 |
| Posterior | `/par+` | V24 Proparaskeuē | [par.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.agents/workflows/poiesis/chronos/par.md) — defend 派生 |

## サブモジュール

> bye から継承。`poiesis/chronos/modules/rest/` に配置:
>
> | ファイル | 機能 |
> |:---------|:-----|
> | `value-pitch.md` | Value Pitch (Benefit 8角度 + Kill Switch) |
> | `pitch_gallery.md` | 正典ギャラリー (熱量の参照) |
> | `handoff-format.md` | Handoff フォーマット定義 |
> | `persistence.md` | 9ステップ永続化手順 |
> | `dispatch-log.md` | WF 使用記録フォーマット |

## 使用例

```ccl
@rest                      # 標準セッション終了
@learn >> @rest             # 学習→完全終了
@rest >> @wake             # 連続セッション
```

## 射の提案

| 条件 | 射 | 意味 |
|:-----|:---|:-----|
| 次セッション | `>> @wake` | 起きる |
| 学びを深める | `>> @learn` | 刻む |
| 緊急終了 | (なし) | `/par-` のみで軽量永続化 |

---
*v1.0 — 旧 /bye (v7.7) の後継。Chronos 族に全機能を分散吸収。6動詞4族 (2026-02-28)*
