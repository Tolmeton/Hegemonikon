# T-100 Bundle 1 Source Audit — P-VII x E-03/E-05/E-08/E-10

作成日: 2026-05-01

## Audit Question

T-100 Bundle 1 の短文稿は、独立 artifact として新規に書くべきか。それとも既存の遊学エッセイ本文、特に `E-03 センスがないと生きるのは大変` を母体にすべきか。

## SOURCE

注意: 2026-05-01 確認時点で、main branch `b2c9211a9` と `claude/serene-clarke` branch `d1b3e6de` は merge-base を持たない別履歴だった。E-03/E-05/E-10 を含む Essay 一式は `claude/serene-clarke` / `master` 側にあり、main 側には未統合。削除ではなく branch divergence / unmerged source surface と判断する。

| essay | path | observed role |
|:--|:--|:--|
| `E-03` センスがないと生きるのは大変 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/04_遊学エッセイ｜Essays/センスがないと生きるのは大変_たたき台.md` | Bundle 1 の本文母体。センス = 入力から引き出せる射の数、見えるもの/見えないもの、precision、米田、射の保持まで既にある |
| `E-05` バカの一つ覚え | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/04_遊学エッセイ｜Essays/バカの一つ覚え_たたき台.md` | E-03 の「深さ」に対する「幅」。複数の圏/世界を持つか、自然変換できるかの補助線 |
| `E-08` バカをやめたいなら構造を見ろ | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/04_遊学エッセイ｜Essays/バカをやめたいなら構造を見ろ_v2.md` | 既に独立完成度が高い基礎稿。構造を見る = 射を見る / 良い出発点を見つける、という理論基盤 |
| `E-10` 愚か者ほど不確定を嫌う | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/04_遊学エッセイ｜Essays/愚か者ほど不確定を嫌う_たたき台.md` | 肉付け未定の補助稿。不確定受容/prior precision/逃避コストの情動側 |

## Observations

`E-03` だけで、T-100 Bundle 1 の短文稿に必要な主成分はほぼ足りている。既存稿は、センスを「一つの入力から主体が引き出す射の数」と定義し、映画例、FEP の sensory precision、米田の補題、観測関手の忠実度、射の保持まで含む。

`E-05` は `E-03` の代替本文ではなく、深さ/幅の直交性を与える補助線である。`E-03` が一つの圏の中でどれだけ射を見えるかを扱うのに対し、`E-05` は複数の圏の間を渡れるかを扱う。

`E-08` は Bundle 1 の本文候補というより、シリーズ内の基礎稿である。ここから直接短文を再生成すると、`E-03` の主体側知覚論ではなく、構造を見る一般論へ戻りすぎる。

`E-10` は不確実性への情動的逃避を扱うが、現時点の status は「たたき台のたたき台」であり、Bundle 1 の本文母体にするには弱い。E-03 の末尾に「不確定を保持できるか」という補助段落として使うのが妥当。

## Judgment

T-100 Bundle 1 の公開用 L0 article は、独立新規 draft としてではなく、`E-03 センスがないと生きるのは大変` の public-facing polish として進めるのが正しい。

`E-05/E-08/E-10` は同じ構造の 4 本を均等に束ねる素材ではなく、E-03 を支える三つの補助軸として扱う。

| support axis | source | use in E-03 polish |
|:--|:--|:--|
| 幅 | `E-05` | センスの「深さ」と、一つ覚え脱出の「幅」を混同しないための注 |
| 基礎 | `E-08` | 構造を見る = 射を見る、という reader-facing 定義の背骨 |
| 情動 | `E-10` | 不確定を嫌うほど粗い近似を現実と取り違える、という末尾補助 |

## Rejection Ledger

| rejected move | reason |
|:--|:--|
| `T-100_bundle1_pvii_l0_article_draft_2026-05-01.md` を正本 draft にする | 4 essay 本文を直接読まずに作ったため、SOURCE-grounded な接続稿ではない |
| 4 essay を同じ比重で一つの短文に束ねる | 既存 SOURCE 上、E-03 が明確な母体で、他 3 本は補助軸 |
| E-08 を主本文に戻す | 既に完成度の高い基礎稿であり、Bundle 1 の「センス」入口から逸れる |

## Next

次に進むなら、`センスがないと生きるのは大変_たたき台.md` を母体に、冒頭 800-1200 字を public-facing に磨く。新規 draft は橋メモとして残し、必要な表現だけ E-03 polish へ吸収する。
