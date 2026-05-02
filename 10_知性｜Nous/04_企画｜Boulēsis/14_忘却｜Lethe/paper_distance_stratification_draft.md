# 忘却の質を測るための距離の層別化 — 論文草稿

> 正本対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/`
>
> この草稿は、Lēthē の本論を **「距離の層別化」** に固定するための paper-facing draft である。Detailed Feedback と Structural Attention はここでは主結果に昇格させない。

## 要旨

本稿は、Lēthē を「検索改善案」ではなく、「忘却の質をどう測るか」という問題として組み直す。中心命題は、`49d + cosine` が近接と遠隔の大局は捉えても、中間帯域を潰すため、単一距離では忘却の質を記述できないという点にある。したがって必要なのは、万能な 1 本の尺度ではなく、どの帯域で何を見失うかを切り分ける **距離の層別化** である。本稿は新しい最終距離の勝利宣言ではなく、介入以前の診断面を固定するための論文ドラフトである。

## 0. 命題面

本稿の中心命題は次の一文に固定する。

> **49d + cosine は近接構造と遠隔構造の大局は捉えるが、中間帯域を潰す。ゆえに忘却の質を測るには、単一距離ではなく距離の層別化が必要である。**

本稿で扱う命題の階層:

| status | 命題 |
|:--|:--|
| `確立済み` | 5-bin で `B2-B4` の崩れが見え、単一距離に盲点がある |
| `補強` | `CCL string distance` と `d_lēthē candidate` は、どこで何を見失うかの比較軸になる |
| `未検証` | `P33`: Detailed Feedback が Θ を下げる |
| `未検証` | `P34`: Ξ が高いほど Detailed Feedback が効く |

## 1. 問題設定

化学でいえば、分子式だけを見て分子の近さを決めるのに似ている。`C2H6O` という表記だけでは、エタノールとジメチルエーテルは同じものとして見えてしまう。組成は同じでも、結合のされ方が違えば性質は変わる。必要なのは「何が何個あるか」だけでなく、「どう結ばれているか」である。

Lēthē の `49d + cosine` も、ちょうどこの分子式読みに近い。大きさや組成の近さ、つまり「だいたい近い」「だいたい遠い」という大局は掴める。しかし構造の差が効き始める中間帯域では、同じ部品を持つ別配置や、似た流れを持つ別配線を潰しやすい。

コード検索や構造検索の評価では、しばしば「近いか遠いか」の単一 score が使われる。しかし Lēthē が見ている対象は、単なる近傍検索ではない。名前を忘れて構造だけを残したとき、**どの差が残り、どの差が潰れるか** が本体である。

この観点では、最も重要なのは近傍精度だけではない。遠隔構造だけでもない。問題はそのあいだの **中間帯域** にある。ここで距離が鈍ると、検索・監査・回復のすべてが「何となく似ている/違う」の曖昧な面に落ちる。

## 2. 既存結果の再配置

P3/P3b の既存実験は、従来は「CCL が text より強いか」という勝敗線で読まれてきた。本稿ではその読みを変える。重要なのは総合勝敗ではなく、**5-bin に切ったときにどこで視力が落ちるか** である。

この再配置により、P3/P3b は単なる性能比較ではなく、距離診断の入口になる。近似ペア相関、hard negative 分離、Energy 系の証拠も同様である。これらは「構造が存在する」ことを支える補強であり、本論の中心命題そのものではない。

## 3. 距離層別化

本稿のコアは、本ファイル Appendix D と `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_stratification.json` にある。

ここで固定する事実は 3 つだけでよい。

| observation | 意味 |
|:--|:--|
| `B2-B4` で視力が落ちる | 中域が単一距離の盲点である |
| `49d cosine` は `B5` 側も圧縮しやすい | 中域 blur だけでなく遠隔側の false positive もある |
| `CCL string distance` と `d_lēthē candidate` は近接側で過敏化する | 別の距離族を足せば自動的に解決するわけではない |

したがって、本稿の寄与は「新しい最終距離の提案」ではなく、**距離族ごとの歪みを帯域ごとに見える形へ出したこと** にある。

## 4. `d_lēthē` の位置づけ

`d_lēthē` は本稿では勝利宣言の対象ではない。役割はもっと限定的で、**単一 cosine が押しつぶした差を、忘却の複数面から照らし直す診断距離族** として置く。

現時点の暫定形は単純でよい。

```text
0.5 * ccl_normalized_distance + 0.5 * control_flow_distance
```

この式の価値は、最終形であることではない。中域で何が潰れ、近接で何が過敏化し、遠隔で何が圧縮されるかを、単一軸よりも分解して観察できることにある。

## 5. 限界

本稿で切り捨てるものを明示する。

| out_of_scope | 理由 |
|:--|:--|
| Structural Attention 全面 | 距離論文の命題を太らせる |
| Phase C 大規模学習 | 必要性の議論と実装野心が混ざる |
| QLoRA / Gemma4 probing 断片 | 本稿の核である距離層別化から焦点を外す |
| Detailed Feedback の強い効果主張 | まだ介入実験線として閉じていない |

本稿は「何が効くか」より前に、「どこで見失っているか」を定義する論文である。この順序を崩さない。

## 6. 次段

次稿に送るのは、Detailed Feedback の介入実験である。その入口は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/intervention_readiness_note.md` に固定した。

ここで残す問いは 2 つだけでよい。

1. `P33`: Detailed Feedback は Θ を大幅に下げるか
2. `P34`: Ξ が高い帯域ほど Detailed Feedback が効くか

この 2 命題は本稿の結論ではない。本稿で確立するのは、**介入が必要になる前段として、距離の盲点がどこにあるかを見えるようにした** という一点である。

## 7. 結語

Lēthē を「検索改善案」として読むと、議論はすぐ最終距離や最終アーキテクチャの勝負に流れる。本稿はそこに乗らない。ここで確立するのは、忘却の質を測るとき、最初に必要なのは万能距離ではなく **距離の層別化** だということである。

この整理は cosine を捨てることを意味しない。cosine は粗い第一段のふるいとしては残るが、構造の最終判定を単独で担わせない、という役割の再配置こそが本稿の含意である。

---

## Appendix A. Submission Surface

以下は旧 `paper_distance_stratification_abstract.md` の吸収面である。本文の命題を増やさず、投稿用 title / abstract / 禁止主張だけを保持する。


> 対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/`
>
> これは距離層別化論文の abstract 面であり、Detailed Feedback や Structural Attention の主張を混ぜない。

### Title Candidate

**Seeing the Middle Collapse: Distance Stratification for Structural Retrieval under Forgetful Representations**

### Abstract v1

Code retrieval systems often compress structural difference into a single similarity score. This is sufficient for near duplicates and clearly unrelated code, but it obscures the intermediate regime where retrieval, auditing, and reconstruction become epistemically fragile. We study this regime in Lēthē, a framework that forgets names and preserves structure through a categorical intermediate representation, CCL. Our claim is not that one new metric universally wins. Instead, we show that structural retrieval must be read through distance stratification. Using a fixed five-band partition over AST distance and a shared evaluation surface derived from `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_stratification.json`, we compare three distance families: `49d cosine`, `CCL string distance`, and a provisional `d_lēthē` diagnostic distance. The resulting picture is asymmetric: `49d cosine` preserves global near/far order but compresses the middle and produces far-band false positives, whereas structure-sensitive distances recover separation at the cost of near-band over-sensitivity. The contribution of this paper is therefore diagnostic rather than triumphalist: we make visible where each distance family loses sight of structure, and argue that the quality of forgetting should be evaluated bandwise rather than by a single score.

### Short Abstract v2

Single-score similarity hides the regime where structural retrieval actually fails. In Lēthē, we show that `49d cosine` captures near/far structure but collapses the middle band. Using a fixed five-band partition over AST distance, we compare `49d cosine`, `CCL string distance`, and a provisional `d_lēthē` distance on a shared evaluation surface. The result is not a universal winner but a diagnostic map: `49d cosine` compresses middle and far distinctions, while structure-sensitive distances reopen those bands at the cost of near-band over-separation. Our contribution is to recast retrieval evaluation as distance stratification and to treat the quality of forgetting as a bandwise observable rather than a single metric.

### Constraint

この abstract で言ってよいこと:

| label | 許可 |
|:--|:--|
| `確立済み` | `49d cosine` が中域を潰す / bandwise 診断が必要 |
| `補強` | `CCL string distance` と `d_lēthē candidate` の歪み比較 |
| `禁止` | Detailed Feedback が効く / Structural Attention が必要 / 最終距離が確定した |


## Appendix B. Introduction Surface

以下は旧 `paper_distance_stratification_introduction.md` の吸収面である。本文 §1 へ展開する前の英語 introduction draft として保持する。


> 対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/`
>
> これは paper-facing introduction 面である。目的は「何を証明する論文か」を最初の 2 ページで固定すること。

### Opening

Code similarity is usually narrated as a search problem: given one function, retrieve another function that is structurally close. But this framing hides a prior question. Before we ask whether a system can retrieve structure, we should ask how structure disappears when names are forgotten and only relations remain. Lēthē begins from this earlier problem. It studies code under a forgetful representation, where lexical identity is stripped away and structural form is preserved through CCL, a categorical intermediate representation.

This shift changes what should count as success. If retrieval is evaluated only by a single similarity score, then two distinct failures are collapsed into one number: the inability to separate nearby but non-identical structures, and the inability to keep genuinely distant structures apart. In practice, however, these failures do not occur uniformly. Some distance families preserve the global near/far picture while losing the middle. Others recover middle-band distinctions but overshoot and fragment near neighbors. The question is therefore not which distance wins in the abstract, but where each distance family loses sight of structure.

### Problem

Our empirical starting point is a recurrent pattern in P3/P3b: the representation appears adequate when examples are either clearly near or clearly far, yet becomes unstable in the intermediate regime. This instability is not noise around an otherwise healthy score. It is the signal. The middle band is where retrieval, auditing, and reconstruction become ambiguous, because the representation can no longer say whether two programs are variants of one structural strategy or merely adjacent in surface form.

For that reason, this paper does not present `d_lēthē` as a final winning metric. Nor does it move immediately to intervention claims such as Detailed Feedback or larger architectural proposals such as Structural Attention. Those questions may matter later, but they become meaningful only after the diagnostic problem is made explicit. The present paper isolates that problem.

### Thesis

We argue that structural retrieval under forgetful representations must be evaluated through distance stratification rather than by a single similarity score. Concretely, we fix a five-band partition over AST distance and compare three distance families on the same pair set: `49d cosine`, `CCL string distance`, and a provisional `d_lēthē candidate`. This shared surface lets us ask a sharper question: which families collapse the middle, which over-separate the near band, and which create false positives in the far band?

The answer is asymmetric. `49d cosine` preserves broad order but compresses the middle and leaks into far-band false positives. `CCL string distance` and `d_lēthē candidate` reopen some of that separation, but they do so by becoming more aggressive in the near band. The contribution of the paper is not to eliminate this tradeoff. It is to make the tradeoff visible and measurable.

### Contributions

1. We recast structural retrieval evaluation as a bandwise diagnostic problem, not a single-score ranking problem.
2. We introduce a fixed five-band evaluation surface over AST distance and expose where middle-band collapse occurs.
3. We compare three distance families on the same pair set and show that each has a distinct failure geometry.
4. We reposition `d_lēthē` as a diagnostic distance family rather than a final universal metric.

### Scope Boundary

This paper does not claim that Detailed Feedback already improves recovery, that Structural Attention is necessary, or that a final distance function has been found. Those belong to a subsequent intervention paper. Here the task is prior: define the blind spot before proposing the cure.

### Section Map

1. Problem setting: why the middle band matters
2. Re-reading P3/P3b: from benchmark win/loss to diagnostic surface
3. Distance stratification: fixed-band empirical analysis
4. Positioning `d_lēthē`: a diagnostic family, not a final metric
5. Limits: what is intentionally excluded
6. Next step: why intervention experiments become necessary only after diagnosis


## Appendix C. Figure Plan

以下は旧 `paper_distance_stratification_figures.md` の吸収面である。図版生成 script / 出力 / caption policy を本文から分離して保持する。


> データ正本:
> `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_stratification.json`
>
> figure 集約:
> `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_figure_data.json`
>
> 生成 script:
> `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/plot_p3b_figures.py`
>
> 出力先:
> `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/paper_figures/`

### Generated Outputs

| figure | path |
|:--|:--|
| `Figure 1` | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/paper_figures/figure1_middle_band_collapse.png` |
| `Figure 2` | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/paper_figures/figure2_failure_geometry.png` |
| `Figure 3` | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/paper_figures/figure3_distance_family_tradeoff.png` |
| `Figure 4` | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/paper_figures/figure4_representative_pairs.png` |

### Figure 1

**Title**
Middle-band collapse under `49d cosine`

**Question**
単一 `49d cosine` は、どの帯域で視力を落とすか。

**Data**
`band_mean_distances.cosine_49d`

**Expected visual**
折れ線。`B1` から `B5` へ単調に上がるが、傾きが浅く、`B2-B5` が広く圧縮されて見える。

**Caption draft**
`49d cosine` preserves the global near-to-far ordering, but its spread across `B2-B5` remains compressed. The middle regime is not cleanly resolved into distinct structural bands.

### Figure 2

**Title**
Failure geometry differs by distance family

**Question**
どの距離族が、どの失敗様式を多く出すか。

**Data**
`failure_counts`

**Expected visual**
積み上げ棒または grouped bar。`49d cosine` は `mid_band_blur` と `far_band_false_positive`、`CCL string distance` は `near_band_false_negative`、`d_lēthē candidate` は中間形。

**Caption draft**
The failure profile is not uniform across distance families. `49d cosine` collapses the middle and leaks false positives into the far band, while structure-sensitive distances reduce far-band collapse at the cost of stronger near-band separation.

### Figure 3

**Title**
Distance-family tradeoff across the five canonical bands

**Question**
`49d cosine`、`CCL string distance`、`d_lēthē candidate` は、帯域ごとにどう異なるか。

**Data**
`band_mean_distances`

**Expected visual**
3 本線の比較。`49d cosine` は低く圧縮、`CCL string distance` は全域で高め、`d_lēthē candidate` はその中間。

**Caption draft**
No distance family dominates globally. Instead, each induces a characteristic distortion profile over the same five-band surface.

### Figure 4

**Title**
Representative failure pairs

**Question**
失敗様式は、具体的にどの pair に現れるか。

**Data**
`representative_examples`

**Expected visual**
表。各距離族ごとに 1 つずつ代表例を見せる。本文では `pair_id`, `func_a`, `func_b`, `band_id`, `distance_value` を載せれば十分。

**Caption draft**
Representative pairs make the diagnostic categories concrete: `49d cosine` under-separates some far-band pairs, while structure-sensitive distances can over-separate near-band neighbors.

### Use Policy

この paper で figure に使ってよい主張:

| figure | allowed claim | disallowed claim |
|:--|:--|:--|
| `Figure 1` | 中域圧縮が見える | `49d` が無価値 |
| `Figure 2` | 失敗様式が距離族ごとに違う | `d_lēthē` が最終勝者 |
| `Figure 3` | 歪みの幾何が違う | 全帯域で最良距離が決まった |
| `Figure 4` | failure_mode が具体 pair に落ちる | Detailed Feedback の必要性が実証済み |


## Appendix D. Diagnostic Report Source

以下は旧 `distance_stratification_report.md` の吸収面である。本文 §3 の empirical surface と、`experiments/p3b_stratification.json` の読み方を固定する。


> 正本対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/`
>
> この文書の役割は、**Lēthē の本論を「距離の層別化」に固定すること**である。主張は 1 つだけ。
>
> **49d + cosine は遠近の大局は捉えるが、中間帯域を潰す。したがって距離は単一値ではなく、帯域ごとに読む必要がある。**

### 1. カーネル

P3b の 5-bin 分析では、近い構造と遠い構造では相関が戻る一方、**中間帯 (Bin 2-4)** で相関が急落した。これは「検索が失敗した」のではなく、**単一距離が構造差を丸めてしまった**ことを示す。ゆえに本論の寄与は、新しい距離が絶対的に勝つことではない。**どの帯域で何を見失うかを診断可能にすること**にある。

### 2. 帯域定義

本レポートと `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_benchmark.py` は、以下の AST 距離境界を canonical として共有する。

| band_id | AST 距離帯 | 初期件数 (P3b) | 読み |
|:--|:--|--:|:--|
| `B1` | `0.000 - 0.448` | 60 | 近接構造。近いものを近いと見られるか |
| `B2` | `0.448 - 0.542` | 60 | 遷移帯前半。崩れ始める場所 |
| `B3` | `0.542 - 0.614` | 60 | 中域核。最も鈍る場所 |
| `B4` | `0.614 - 0.694` | 60 | 遷移帯後半。回復境界 |
| `B5` | `0.694 - 1.000` | 60 | 遠隔構造。遠いものを遠いと見られるか |

P3b の公開値:

| Bin | ρ(Spearman) | 含意 |
|:--|--:|:--|
| `B1` | `0.622` | 近傍では相関が立つ |
| `B2` | `0.281` | ここから視力が落ちる |
| `B3` | `0.180` | 中域核の崩れ |
| `B4` | `0.074` | 単一距離の盲点が最大化 |
| `B5` | `0.429` | 遠隔では再び相関が戻る |

再現 artifact の現状態:

| run_date | functions | pairs | pair_sampling | 49d source |
|:--|--:|--:|:--|:--|
| `2026-04-17` | 191 | 500 | canonical 5-band 層化 | `sample_reconstructed` |

注: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/02_索引｜Index/code_ccl_features.pkl` は現環境に存在しなかったため、`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/code_ingest.py` の `ccl_feature_vector()` から sample 内 49d を再構成し、z-score + L2 正規化した。

現 run の帯域件数:

| band_id | 件数 |
|:--|--:|
| `B1` | 32 |
| `B2` | 103 |
| `B3` | 117 |
| `B4` | 133 |
| `B5` | 115 |

### 3. 失敗様式

距離層別化で見たい失敗は、単純な「誤答」ではない。帯域ごとに意味が違う。

| failure_mode | 意味 | 典型帯域 |
|:--|:--|:--|
| `mid_band_blur` | 中域差異が 1 本の距離に圧縮され、差が立たない | `B2-B4` |
| `near_band_false_negative` | 近い構造が不当に遠く見える | `B1` |
| `far_band_false_positive` | 遠い構造が不当に近く見える | `B5` |
| `aligned` | 帯域期待と距離の読みが一致 | 全帯域 |

本論で主に扱うのは `mid_band_blur` である。`B1/B5` の誤差は周辺症状であり、芯は **「中域で差が立たない」** ことにある。

ただし現 run では、`49d cosine` に `far_band_false_positive` が 90 件出ている。これは「遠隔構造を近く見すぎる」失敗が中域 blur と並ぶ副症状である。したがって本論は `mid_band_blur` を中心に据えつつも、`B5` 側の圧縮も盲点として明示する。

### 4. 比較する距離族

このレポートで比較するのは「勝者決定戦」ではなく、**何を見ているかの比較**である。

| 距離族 | 役割 | この論文での位置づけ |
|:--|:--|:--|
| `49d cosine` | 高速で大局を取る基準線 | 主診断対象 |
| `CCL string distance` | CCL 文字列上の差異を直接測る | 49d が潰した差の参照軸 |
| `d_lēthē candidate` | 複数の忘却像を束ねた暫定距離族 | 最終勝者ではなく診断補助 |

暫定 `d_lēthē candidate` の現時点の定義:

```text
0.5 * ccl_normalized_distance + 0.5 * control_flow_distance
```

これは最終定義ではない。意味はただ一つで、**単一 cosine が見落とす帯域を、複数の構造差で照らし直す**ことにある。

現 run の帯域平均距離:

| 距離族 | `B1` | `B2` | `B3` | `B4` | `B5` |
|:--|--:|--:|--:|--:|--:|
| `49d cosine` | 0.2010 | 0.3501 | 0.4272 | 0.4755 | 0.5671 |
| `CCL string distance` | 0.5928 | 0.6641 | 0.6656 | 0.7147 | 0.8170 |
| `d_lēthē candidate` | 0.4703 | 0.6322 | 0.6530 | 0.7047 | 0.7823 |

この面から読めることは明確である。`49d cosine` は単調性自体は保つが、`B2-B5` を広く圧縮する。対して `CCL string distance` と `d_lēthē candidate` は高めに張ることで中域と遠隔を分け直す。ただしその代償として、`B1` で「近いものを遠く見すぎる」誤差が生まれる。

現 run の failure 件数:

| 距離族 | `aligned` | `mid_band_blur` | `near_band_false_negative` | `far_band_false_positive` |
|:--|--:|--:|--:|--:|
| `49d cosine` | 158 | 252 | 0 | 90 |
| `CCL string distance` | 282 | 187 | 27 | 4 |
| `d_lēthē candidate` | 272 | 203 | 17 | 8 |

この比較が示すのは勝敗ではない。`49d cosine` は遠隔側で圧縮し、`CCL string distance` は近接側で過敏になり、`d_lēthē candidate` はその中間に位置する。つまり Lēthē の論文で必要なのは「最終距離の宣言」ではなく、**どの距離族がどの帯域でどの歪みを持つかの診断表**である。

代表例:

| 距離族 | failure_mode | pair | 読み |
|:--|:--|:--|:--|
| `49d cosine` | `far_band_false_positive` | `export_chat_metadata.parse_all_conversations` ↔ `ls_daemon.stop` (`B5`, `0.6049`) | 遠い構造が十分に開かず、遠隔帯が圧縮される |
| `CCL string distance` | `near_band_false_negative` | `wf_evolver.evaluate_mutation` ↔ `service._ask_cortex_chat` (`B1`, `0.5714`) | 近接構造でも文字列差が強く出て、近傍を遠く見すぎる |
| `d_lēthē candidate` | `mid_band_blur` | `wf_evolver.evaluate_mutation` ↔ `proof_skeleton.generate_proof` (`B2`, `0.6124`) | 補助距離を足しても、なお中域の境界は不安定に残る |

### 5. 共通 JSON

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_benchmark.py` は、距離層別化用に `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3b_stratification.json` を出力する。

各 record の最小面:

| key | 意味 |
|:--|:--|
| `pair_id` | 関数ペア ID |
| `func_a` / `func_b` | 代表例を人間が読めるようにするための関数名 |
| `band_id` | 上記 5 帯域のどこか |
| `ast_distance` | canonical 帯域を決める基準距離 |
| `ccl_distance` | 折り畳み後 CCL 文字列距離 |
| `cosine_49d` | 49d cosine。現 run では `sample_reconstructed` から計算 |
| `distance_family` | `cosine_49d` / `ccl_string` / `d_lethe_candidate` |
| `pair_type` | `near_structure` / `mid_structure` / `far_structure` |
| `failure_mode` | 上表の失敗様式 |
| `example_status` | `report_candidate` / `background` / `needs_measurement` |

この JSON の目的は、論文本文より前に「同じペア集合・同じ帯域境界」で距離族比較を固定することにある。

### 6. 本論への写像

本稿の 6 章への割当は次の通り。

1. 問題設定
   中間帯は検索の残差ではなく、単一距離の盲点である
2. 既存結果の再配置
   P3/P3b と 5-bin を「距離の勝敗」ではなく「帯域診断」へ読み替える
3. 距離層別化
   `B2-B4` の崩れを中心に据える
4. `d_lēthē` の位置づけ
   新距離の勝利ではなく、診断距離族の必然
5. 限界
   Structural Attention と Detailed Feedback は本稿の射程外
6. 次段
   介入実験が必要になる理由だけを残す

### 7. 結論

距離論文の結論は次の一文に閉じる。

> **Lēthē の独立寄与は、49d + cosine が潰す中間帯域を発見し、その盲点を距離層別化で可視化したことにある。**
