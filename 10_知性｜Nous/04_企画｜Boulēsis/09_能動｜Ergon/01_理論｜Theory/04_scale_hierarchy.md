# ハーネスの RG フローとスケール階層

Ergon プロジェクト 理論文書 04

## 1. Scale 座標空間における階層構造

HGK 系には 6 つの修飾座標が存在する。そのうち **Scale (粒度) 座標**は、忘却場 $\Phi_H$ をどの解像度で観測するかを決める軸である。旧文書の `Milestone / Slice / Task` は、新体系では **RG フロー上の観測レベル**として読み替えられる。

- **Task (Micro)**: 単一の自律ステップ。単一または少数の関数・ファイル・ツール呼出の変更。
  - $L \dashv R$ が最も高解像度で見える層。
- **Slice (Meso)**: 複数 Task を束ねた垂直能力。Boundary Maps と契約が最も効く層。
  - `C/E/M` の型整合が観測可能な層。
- **Session / Milestone (Macro)**: boot で開始し bye で閉じる粗視化単位。
  - 外部公開可能な `Milestone` は、この Session が外界に接続された固定点として見えたもの。

$$
\text{Task} \hookrightarrow \text{Slice} \hookrightarrow \text{Session}
$$

重要なのは、これは単なる入れ子ではないという点である。**各層は同じハーネスを異なる解像度で見た像**である。

## 2. 随伴対 $L \dashv R$ のフラクタルな適用

随伴対 $L$ (boot / 展開) と $R$ (bye / 蒸留) は、このスケール階層の全てで自己相似的に実行される。

1. **Micro サイクル (Task)**
   - $L_{\text{Task}}$: 仕様・制約・局所コンテキストを Task に boot する
   - $R_{\text{Task}}$: 実行結果を Belief Update へ bye する
2. **Meso サイクル (Slice)**
   - $L_{\text{Slice}}$: 複数 Task を束ね、Produce / Consume / Contract を一貫した能力へ展開する
   - $R_{\text{Slice}}$: UAT や統合テストの結果を、次の Slice に渡せる summary へ蒸留する
3. **Macro サイクル (Session)**
   - $L_{\text{Session}} = \text{boot}$: Rules / ROM / Handoff をそのセッションの作業面へロードする
   - $R_{\text{Session}} = \text{bye}$: セッション全体の差分を Handoff / ROM / Rule Delta へ圧縮する

ここでのフラクタル性とは、「形が似ている」ことではない。**同じ随伴が Scale 変換の下で保たれる**という意味である。

## 3. Paper V の β 関数と蒸留

Paper V の繰り込み (RG) をハーネスへ適用すると、各スケールで保持される情報量には流れがある。

可視情報量を $I_H(\mu)$ とおくと、

$$
\beta_H(\mu) := - \frac{d I_H(\mu)}{d \log \mu} \ge 0
$$

と書ける。意味は単純である。

- $\mu \to \infty$: 高解像度。個別コマンド、ファイル名、局所ログまで保持される
- $\mu \downarrow$: 粗視化。局所ディテールが削れ、契約・差分・要約だけが残る
- $\mu \to 0$: **不動点構造（本質的制約）**だけが残る。これが蒸留である

したがって蒸留とは「情報を雑に捨てること」ではない。**RG フローを Macro 側へ進め、不動点だけを残す操作**である。

## 4. Paper V §3.4 次元的頑健性定理

Paper V §3.4 の次元的頑健性定理を、Paper XI の `C/E/M` 分解に接続すると次が得られる。

> `C + E + M` の 3 軸が独立に保存される限り、粗視化してもハーネスの効果は頑健である。

| 軸 | 何を保存するか | 蒸留後にも残るべき核 |
|:---|:---|:---|
| **C** (Constraint) | 行為を曲げる方向 | Nomoi、Hook、禁止条件 |
| **E** (Encoding) | 人間が再読可能な記述 | Handoff、ROM、summary の意味核 |
| **M** (Mechanism) | 実際に力を発生させる接続 | Hook、tool contract、boundary enforcement |

この 3 軸のうち 1 つでも潰すと、蒸留は単なる情報欠損になる。逆に 3 軸が残っていれば、詳細を大幅に削ってもハーネスの「効き」は保たれる。

## 5. Paper VI τ-Invariance 定理

Paper VI の `τ-Invariance` 定理をハーネス設計へ移すと、次の主張になる。

> `G∘F` の不動点の品質は `τ` に依存しない。したがって、適切な `τ` 帯の中で行う蒸留は品質を落とさない。

ここで `τ` は「どこで区切るか」を決める閾値であり、ハーネス言語では summary の粒度、chunk の切り方、handoff の圧縮深度に対応する。`τ` を変えると見かけの分割は変わるが、`G∘F` が収束して残す品質核は変わらない。

$$
Q\!\left(\operatorname{Fix}(G \circ F; \tau)\right) \approx Q_*
\qquad (\tau \in \text{admissible band})
$$

直観的には、良い蒸留とは「文章の切り方を変えても意味の骨格が崩れない」状態である。Paper V の `C/E/M` 保存則と合わせると、次が言える。

- `C` が残る限り、制約の向きは変わらない
- `E` が残る限り、人間が再展開できる意味核は壊れない
- `M` が残る限り、実際に力を発生させる接続は失われない
- したがって `τ` を粗くしても、`G∘F` の不動点品質は保存される

蒸留はここで初めて「短縮」ではなく**品質不変な粗視化**になる。

## 6. Boundary Maps と Fractal Summaries の Scale 依存性

- **Boundary Maps** は主に **Meso (Slice)** スケールで決定的な役割を果たす。Task では細かすぎ、Session では粗すぎる。Slice 間の `Produce / Consume / Contract` がハーネスの骨格になる。
- **Fractal Summaries** は `R (bye)` のスケール依存的適用である。Task 終了時の短い Belief Update から、Session 終了時の Handoff まで、すべては `bye` の粗視化の深さが違うだけである。
- したがって GSD の **Fractal Summaries = Reduce パターン** であり、`R` の適用深度を Scale ごとに変えたものと解釈できる。

## 7. timakin (2026) の 3 原則と Scale の対応

timakin (2026) のコンテキスト管理 3 原則 `Reduce / Offload / Isolate` は、Paper X の CM 戦略を実務語彙に翻訳したものと読める。

| 原則 | 忘却論的解釈 | 主な Scale | 典型操作 |
|:---|:---|:---|:---|
| **Reduce** | 同一 blanket 内の粗視化。`R` による蒸留 | Micro → Meso | summary、fractal summary、log 圧縮 |
| **Offload** | 状態を作業面の外へ逃がす。`bye` の外部化 | Meso ↔ Macro | ROM、Handoff、外部ファイル、Git |
| **Isolate** | blanket の外に別の blanket を作る | Meso ↔ Meso' | サブエージェント委譲、分離実行 |

ここから分かるのは、3 原則が並列の小技ではないという点である。**Scale をまたぐときにどの種の忘却を使うか**を選ぶ設計言語である。

## 8. 設計上の帰結

1. Task を直接積み上げても Session は設計できない。Scale が変わるたびに `R` の粗視化深度を変える必要がある。
2. `boot⊣bye` は Macro でしか働かない別機構ではない。Task の `L⊣R` を $\mu \to 0$ まで流した極限像である。
3. HGK v2 の改善とは、コンテキストを増やすことではなく、**どの Scale で何を残すかを RG 設計すること**である。
4. 蒸留の成否は「どれだけ短くしたか」ではなく、`C/E/M` を保ったまま `τ` を動かしても品質が崩れないかで判定すべきである。

---
*Created: 2026-03-09*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
