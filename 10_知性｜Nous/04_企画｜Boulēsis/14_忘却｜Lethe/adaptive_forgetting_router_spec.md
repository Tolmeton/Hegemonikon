# Adaptive Forgetting Router Spec

> 対象: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/`
>
> 役割: `Θ / Ξ / d_α` を入力として、どの距離族・どの feedback 粒度・どの回復手段を使うかを切る **N 側の判断面** を固定する。

## 1. 核

この文書は新しい距離関数を導入しない。
やることは 1 つだけで、**静的 metric 運用をやめ、入力ごとに「どの忘却帯域にいるか」を見て処理を切り替える**ことである。

前提は次の 3 点に固定する。

| 軸 | 固定する意味 |
|:--|:--|
| `Θ` | 忘却の量。どれだけ情報が落ちているか |
| `Ξ` | 忘却の質。不均一に落ちているか、均一に落ちているか |
| `d_α` | 2対象を同型にするために必要な最小忘却量。どの帯域の距離問題か |

この router は、`U` そのものではなく **`N` をどう起動するか** を決める。
したがって位置づけは「検索器」ではなく **回復制御器** である。

## 2. Operative Distinction

本 spec が先に切り分けるべきなのは、次の混同である。

| 層 | 目的 | 主要概念 | 失敗形 |
|:--|:--|:--|:--|
| 安定化層 | collapse 防止 | anti-collapse / isotropic prior / 低 `Θ` | 潰れすぎ |
| 識別層 | 検索力・回復力 | `Ξ > 0` / routing / selective recovery | 使い分け不能 |

規則:

1. **等方忘却は anti-Lēthē ではない。** 基底層での安定化には必要になりうる。
2. **検索力は `Ξ` から生まれる。** したがって上位層では不均一性を消してはいけない。
3. router は「どこまでを安定化層に委ね、どこからを識別層で扱うか」を切る。

## 3. Router Inputs

初版では、観測入力を次の 4 つに固定する。

| 入力 | 意味 | 初期の観測法 |
|:--|:--|:--|
| `theta_band` | 忘却量 | 失敗率、再検索回数、回復不能率から `low / mid / high` に離散化 |
| `xi_band` | 忘却の不均一度 | error 型分散、CV ジニ、帯域別劣化差から `low / mid / high` に離散化 |
| `d_alpha_band` | どの忘却帯域で問題が起きているか | `0.0-0.5 / 0.6-0.8 / 0.81-0.89 / 0.9+` の 4 帯域 |
| `task_shape` | routing 許容度 | `rigid_reasoning / flexible_knowledge / structural_repair / broad_recall` |

`task_shape` を入れる理由は単純で、同じ `Θ/Ξ/d_α` でも、**rigid reasoning では routing が害になりうる**からである。

## 4. Distance Policy

現時点で採る距離族の優先順位は、既存理論に合わせて次で固定する。

| `d_α` 帯域 | 主距離 | 補助距離 | ルータ判断 |
|:--|:--|:--|:--|
| `0.0-0.5` | `fg_jaccard` | なし or 軽い cosine | 順序保持の局所差が効く帯域。最優先で structure-first |
| `0.6-0.8` | `49d cosine` | `fg_jaccard` | 遷移帯域。cosine を主、fg を補助に回す |
| `0.81-0.89` | `49d cosine` | 連続 α 近似 | 偽遠距離の可能性が高い。離散 `d_α` をそのまま信じない |
| `0.9+` | `49d cosine` | なし | 現行距離族だけでは弁別困難。詳細 feedback か追加観測へ送る |

禁止事項:

1. `α>=0.7` で `set_jaccard` を新規主距離として足さない。現状では cosine と冗長。
2. `d_α=0.9` を即「本質的遠距離」と断定しない。偽遠距離の可能性を先に疑う。
3. 単一 metric の改善を router の成功とみなさない。成功は **適切な切替** で測る。

## 5. Feedback Policy

feedback 粒度は次の 3 段に固定する。

| 粒度 | 中身 | 使う条件 |
|:--|:--|:--|
| `none` | feedback なし | `theta_band=low` かつ `xi_band=low` で、既に距離選択が十分なとき |
| `binary` | `keep / drop`, `ok / ng` のみ | `theta_band=mid` だが `xi_band=low` で、局所修正より帯域判定が重要なとき |
| `detailed` | 欠落座標 + `U-pattern` + 修復助言 | `xi_band=high` または `task_shape=structural_repair` のとき |

強い規則:

1. `detailed` は `Ξ` が高い場所に集中する。
2. `Ξ` が低いのに `detailed` を乱発しない。均一忘却には局所助言より再表現が効く。
3. `rigid_reasoning` では `detailed` を入れても、routing 自体は保守的に扱う。

## 6. Recovery Policy

回復手段は N 側の重さで 4 段に分ける。

| 回復手段 | 内容 | 向いている条件 |
|:--|:--|:--|
| `N_light` | chunk / file 候補を再読へ渡す | `broad_recall`, `theta_band=low-mid`, `xi_band=low` |
| `N_symbol` | symbol / reference / declaration 辺を回復 | `structural_repair`, `d_α<=0.5`, `xi_band=high` |
| `N_heavy` | 依存・階層・編集安全面まで回復 | `theta_band=high`, `xi_band=high`, 変更可能性まで見る必要があるとき |
| `N_route_memory` | 類似入力の成功履歴から設定を引く | `flexible_knowledge` かつ task-specific regularity が観測されるとき |

`N_route_memory` は新しい距離ではない。
位置づけは **「似た問いで何が効いたか」を回復する N の補助器** である。

## 7. Decision Table

この表が router の正本である。

| Regime | 入力条件 | 距離族 | Feedback | Recovery | 判定 |
|:--|:--|:--|:--|:--|:--|
| `R1 Stable-Local` | `theta=low`, `xi=low`, `d_α=0.0-0.5` | `fg_jaccard` 主 | `none` | `N_light` | 既存構造近接。router 介入は最小 |
| `R2 Uneven-Local` | `theta=low-mid`, `xi=high`, `d_α=0.0-0.5` | `fg_jaccard` 主, cosine 補助 | `detailed` | `N_symbol` | 近接だが忘却が局所破断。Detailed を使う |
| `R3 Transition` | `theta=mid`, `xi=mid`, `d_α=0.6-0.8` | cosine 主, fg 補助 | `binary` | `N_light` | metric 切替だけで回るかを先に見る |
| `R4 False-Far` | `theta=mid`, `xi=mid-high`, `d_α=0.81-0.89` | cosine 主, 連続 α 近似 | `binary` or `detailed` | `N_route_memory` + `N_symbol` | 離散相転移を疑う。偽遠距離の補正が主眼 |
| `R5 Uniform-Far` | `theta=high`, `xi=low`, `d_α=0.9+` | cosine のみ | `binary` | `N_light` or abort | 均一に忘れている。局所助言より再取得/再表現 |
| `R6 Uneven-Far` | `theta=high`, `xi=high`, `d_α=0.6-0.9` | cosine 主, fg 補助 | `detailed` | `N_heavy` + `N_route_memory` | Phase C 候補。最も介入価値が高い |
| `R7 Rigid-Protect` | `task_shape=rigid_reasoning` | 現行 best static を保持 | `none` or `binary` | `N_light` のみ | routing で劣化しやすいので保護モード |
| `R8 Flex-Route` | `task_shape=flexible_knowledge` かつ `xi=high` | regime 準拠 | `detailed` 許可 | `N_route_memory` 優先 | 類似入力の履歴を積極利用 |

## 8. Minimal Algorithm

router の最小アルゴリズムは次の順序に固定する。

1. `task_shape` を先に切る。
2. `theta_band` と `xi_band` を推定する。
3. `d_alpha_band` を推定する。
4. `Decision Table` から regime を 1 つ選ぶ。
5. regime に応じて `distance / feedback / recovery` を実行する。
6. 出力後、`routing_gain / reasoning_regression / recovery_cost` を記録する。
7. 成功履歴だけでなく **失敗履歴も** `N_route_memory` に残す。

## 9. Output Contract

router が必ず返すべき出力は 6 項目に固定する。

| 出力 | 意味 |
|:--|:--|
| `regime` | 適用した decision row |
| `theta_band` | 忘却量の帯域判定 |
| `xi_band` | 不均一度の帯域判定 |
| `d_alpha_band` | 距離帯域判定 |
| `chosen_stack` | `distance + feedback + recovery` の組 |
| `verification_focus` | 今回どの副作用を最優先監視するか |

`verification_focus` は次の 4 つだけを許可する。

1. `structure_preservation`
2. `routing_gain`
3. `reasoning_regression`
4. `recovery_cost`

## 10. Non-Goals

この spec が **やらない** ことを先に固定する。

| 非目標 | 理由 |
|:--|:--|
| 新しい embedding 学習距離の設計 | それは router ではなく Phase C 実装の責務 |
| `Θ/Ξ/d_α` の精密推定式の完成 | 今は判断面を先に固定する段階 |
| routing memory の永続化実装 | まず何を保存すべきかを決める |
| README / VISION の全面改稿 | scope creep。まず単独 spec を立てる |

## 11. Acceptance Rule

この spec が受け入れ可能なのは、次の条件を満たす場合だけである。

1. `Θ / Ξ / d_α` がそれぞれ別の責務として扱われている。
2. `d_α` 帯域ごとに距離族の選び方が固定されている。
3. `feedback` と `recovery` が同一視されていない。
4. `rigid_reasoning` と `flexible_knowledge` の routing 方針が分離されている。
5. 最終出力が decision table へ可逆に戻せる。

## 12. References

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/README.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/adaptive_forgetting_router_spec.md` Appendix A
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/absorption_map.json`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/VISION.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/intervention_readiness_note.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/paper_diff_2603_19312_2604_11048_forgetting.md`

---


## Appendix A. External Code Search Absorption Map

以下は旧 `ABSORPTION.md` の吸収面である。人間向けの吸収原則はここに統合し、機械可読正本は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/absorption_map.json` に残す。


#### 核

この文書は、`mgrep`、`Serena`、`Semgrep Code Search` を「便利な外部製品」として足すための比較表ではない。
Lēthē の立場では、それらは **忘却と回復の異なる作用素** として読み替えられ、`U / N / Θ / Ξ / d_α` のどこに落ちるかでのみ受け入れられる。

したがって、吸収とは「同じものを再実装する」ことではなく、「外部機構が担っている働きを、Lēthē の正準座標へ書き直してから内在化する」ことである。
人間向け正本はこの文書、機械可読な正本は `absorption_map.json`、実行面の窓口は `graph(action="absorption")` である。

#### 吸収の原則

1. 外部機構は製品名ではなく **作用素** として読む。
2. `U` に落ちないものは「何を捨てているか」が曖昧であり、Lēthē に入らない。
3. `N` に落ちないものは「何を回復しているか」が曖昧であり、探索の終点にならない。
4. `Θ / Ξ` に落ちないものは、忘却量と忘却配分を観測できず、比較できない。
5. `d_α` に落ちないものは、どの帯域の忘却で効くのかが未規定なので、統合設計に使えない。

#### 外部機構の書き換え

| 外部機構 | Lēthē での読み替え | もっとも強い座標 | 現行 HGK の近縁面 |
|---|---|---|---|
| `mgrep` | 自然言語入口と広角近傍探索を担う広角忘却器 | `U + d_α` | `search(scope="code", code_mode="text")`, `both` |
| `Serena (LSP centered)` | symbol / reference を回復する精密回復器 | `N` | `convert(code=...)`, `structure` |
| `Serena (JetBrains/full)` | 依存・階層・編集安全面まで引き戻す重い回復器 | `N + Ξ` | `structure` |
| `Semgrep Code Search` | ルールと制約で候補を刈り込む制約器 | `Θ + Ξ` | `convert(code=...)`, `structure` |

#### 実装上の含意

##### `mgrep`

`mgrep` をそのまま入れると、HGK は「広角入口」と「意味核」を二重に持つことになる。
吸収ではそうしない。`mgrep` が担うのは「自然言語から広く候補を拾う忘却」であり、これは HGK では `code` と `both` に再記述される。

したがって、実装課題は `mgrep` の UI を真似ることではなく、`code` 側の chunk 粒度と二段探索を整えることになる。
未吸収なのは `watch`、multimodal、web 連結であって、意味検索そのものではない。

##### `Serena`

Serena は自然言語意味検索ではなく、記号・参照・依存を正確に引き戻す回復器である。
LSP 中心の最小構成は `N` の精密面、JetBrains まで含む構成は `N` に編集安全面を足した重い面として分かれる。

吸収の核心は、Serena の見かけをなぞることではなく、HGK に **symbol graph / declaration-reference / implementation edge** を立てることにある。
現行 HGK では `search(scope="code", code_mode="symbol")` と `graph(action="code_symbol")` により symbol graph 自体は持った。
まだ未吸収なのは declaration-reference facet、reference/use edge、rename-safe な編集境界である。

##### `Semgrep Code Search`

Semgrep は広角探索ではなく、条件に合うものだけを残す制約器である。
だから吸収先は `Θ / Ξ` であって、`mgrep` の代替にも `Serena` の代替にもならない。

実装課題は、Semgrep の rule 記法を丸ごと移植することではなく、HGK の `code_ccl` 上に **CCL pattern DSL** と negative predicate を立てることである。
今回のセッションではそこまでは進まず、まず「どこへ落ちるか」を manifest と API に固定した。

#### 今回の実装境界

本セッションで実装したのは、外部機構の吸収写像を **正本化し、機械から読める形に固定したこと** である。
まだ実装していないのは、declaration-reference facet、本格的な rule DSL、watch/multimodal など、各 profile の未吸収面そのものだ。

つまり今回は「機能追加」ではなく、「吸収の座標系をコードに埋めた」。
これによって今後の実装は、製品模倣ではなく `U / N / Θ / Ξ / d_α` のどの裂け目を埋めるかとして管理できる。
