# 差分メモ: `2603.19312` × `2604.11048` を忘却論へ接続する

## 核

[確信 0.88] 二論文の共通核は、「性能は情報量の多さそのものから出るのではなく、**何を残し何を捨てるかの制御**から立ち上がる」という点にある。
[確信 0.82] ただし制御している層は異なる。`2603.19312` は**潜在表現の安定化**、`2604.11048` は**推論時の能力配分の切替**であり、Lēthē に引くなら前者は主に `U/Θ` 側、後者は主に `N/Ξ/d_α` 側の示唆を与える。
[推定 0.74] したがってこれは「同一問題に対する優劣比較」ではなく、「忘却論の上位座標から見た相補的外部証拠の比較」で読むのが正しい。

## 1. 二論文で共通する主張

1. **無制約の表現は能力の源ではなく、むしろ破綻源である。**
`2603.19312` では、予測損失だけでは collapse に落ちるため、ガウス分布を課す anti-collapse 正則化が必要だと主張する。`2604.11048` では、persona は単なる文体ではなく能力配分を変え、しかも良い方向にも悪い方向にも効くので、素のままの一様運用を前提にできないと示す。

2. **万能の固定設定は存在しない。**
`2603.19312` は stable だが、短ホライズン、低多様性データ、高次元等方 prior の適合困難といった限界を明示する。`2604.11048` はさらに露骨で、instruction-following では広く改善が出る一方、reasoning では一貫して悪化する条件がある。忘却論の言い方では、「正しい忘却」は常に**帯域依存**である。

3. **妥当性は downstream 成績だけでなく、内部構造の可観測性で測るべきである。**
`2603.19312` は physical probing と surprise/VoE で latent の中身を見に行く。`2604.11048` は cross-architecture consistency、trait-process mapping、DPR の差分で、steering がノイズではなく再現可能な内部再配分であることを見に行く。どちらも「当たった/外れた」だけでは足りないという立場で一致する。

## 2. 互いに補完する点

1. **`2603.19312` は「忘却の安定化」を与え、`2604.11048` は「忘却の配分切替」を与える。**
前者は collapse を避けるために latent 幾何を整え、後者は query ごとに persona を切り替えて能力配分を動かす。Lēthē に引くと、前者は「忘却をどう安定に起こすか」、後者は「起こした忘却をどう状況依存で使い分けるか」を埋める。

2. **前者は `Θ` の制御、後者は `Ξ` の利用として読むと噛み合う。**
LeWM の anti-collapse は「潰れすぎ」を防ぐための量制御に近い。persona 論文の task-specific gain/degrade と DPR は、「忘却の不均一さを query ごとに使い分ける」と読むと、Lēthē の `Ξ` と自然に接続する。

3. **Lēthē の既存二本柱を別方向から補強する。**
Lēthē は既に `README.md` で「距離層別化を本論、Detailed Feedback 介入を補強線」に固定している。`2603.19312` は距離以前の latent 安定化の必要性を、`2604.11048` は介入が常に一様利得ではなく routing を要することを与えるので、この二本柱の弱点を別々に埋める。

## 3. 競合または緊張する点

1. **等方化 vs 非等方性。**
`2603.19312` は isotropic Gaussian prior で collapse を防ぐ。だが Lēthē は `Ξ > 0`、つまり**忘却の不均一**から力が生まれると置いている。ここを混同すると破綻する。
[推定 0.79] 解像度は「基底層では等方化が安定性を担い、上位の検索/回復層では非等方性が識別力を担う」という**層分離**である。

2. **統一モデル志向 vs 動的ルーティング志向。**
`2603.19312` は単一の stable world model を押す。`2604.11048` は単一の static persona を捨て、query-adaptive routing を押す。
[推定 0.76] Lēthē はこれを「単一 metric を磨く」方向だけでなく、「入力ごとにどの距離・どの介入を使うかを決める」方向へ分岐させる必要がある。

3. **“意味がある latent” と “有益な steering” は同義ではない。**
LeWM では physically implausible event への surprise 上昇が成功指標になる。persona 論文では、instruction-following 改善と reasoning 低下が同時に起こる。
[確信 0.83] つまり Lēthē 側でも、介入の良し悪しを単一スカラーで潰してはいけない。**構造保存、探索利得、推論劣化、回復可能性**を分けて持つ必要がある。

## 4. Lēthē 側で今すぐ更新すべき判断面

| 判断面 | 今の固定 | 今すぐ更新すべきこと | 更新理由 |
|:--|:--|:--|:--|
| 忘却の層位 | `Ξ` を力の源泉として強く押している | **「anti-collapse のための等方忘却」と「検索力を生む非等方忘却」を分ける** | LeWM を入れると、等方化が即 anti-Lēthē ではなく、層を分ければ整合する |
| Phase C の介入仮説 | Detailed Feedback は効く、特に `Ξ` 高域で効くという仮説が主 | **「介入は帯域依存で、全タスク一様利得ではない」を明文化する** | persona 論文では改善と悪化が明確に分かれる。介入の普遍利得仮説は危険 |
| `N` 側の設計 | 回復は主に CCL 注入や検索で考えている | **query-conditioned routing memory を `N` の一部として昇格させる** | DPR は「似た問いの成功履歴」から低コストに改善しており、Lēthē の回復側に新しい設計面を開く |
| 評価面 | 距離・検索・Detailed Feedback の主張が中心 | **評価軸を `構造保存 / routing 利得 / reasoning 劣化 / 回復コスト` に分解する** | persona 側の結果は「改善したが別能力を壊す」を示すため、単一指標では判断を誤る |

## 結論

[確信 0.86] `2603.19312` は「忘却を安定に起こす条件」を、`2604.11048` は「忘却を状況依存で配分する条件」を与える。
[推定 0.78] Lēthē はこの二つを受けて、**単一の忘却論**から**二層の忘却論**へ進むべきである。
第1層は anti-collapse のための安定化、第2層は task/query ごとの routing である。

## 次に起こすべき artifact

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/adaptive_forgetting_router_spec.md`

中身は 1 枚でよい。
要件は「入力から `Θ/Ξ/d_α` をどう見積もり、どの距離族・どの feedback 粒度・どの回復手段を選ぶか」を decision table に落とすこと。
理由は単純で、いま必要なのは新しい大理論ではなく、`static metric` から `adaptive routing` へ移るための最小の判断面だからである。

## SOURCE

- `2603.19312`: <https://arxiv.org/pdf/2603.19312>
  参照点: abstract, anti-collapse regularization, physical probing, VoE, conclusion.
- `2604.11048`: <https://arxiv.org/abs/2604.11048> / <https://arxiv.org/pdf/2604.11048>
  参照点: abstract, RQ1-RQ4 results, DPR, conclusion.
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/README.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/adaptive_forgetting_router_spec.md Appendix A`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/VISION.md`
