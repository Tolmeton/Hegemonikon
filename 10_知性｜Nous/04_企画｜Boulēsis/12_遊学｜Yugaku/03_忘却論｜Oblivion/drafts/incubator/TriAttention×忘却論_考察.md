# TriAttention × 忘却論ローカルLLM研究 — 裏付け・批評・深化版

## 0. 先に結論

TriAttention は、**長文脈推論の KV 圧縮法としてはかなり強い**。pre-RoPE 空間での Q/K 集中、ドメイン横断の安定性、matched-accuracy 条件での 2.5x throughput / 10.7x memory reduction は、論文本文・README・results・calibration guide でかなり素直に裏付けられる。

一方で、元文書の後半には、**工学的事実**・**理論的に整合する読み替え**・**まだ比喩段階の接続**が混ざっていた。特に次の 3 点は修正が必要だった。

1. `U_TriAtt` を単一の固定関手として置くより、**状態・budget・window・calibration stats に依存する作用素族**として扱う方が正確  
2. MRL `R` を「忘却強度 α」と同一視するのは強すぎる。`R` はむしろ **圧縮可能性 / 幾何学的可読性** の指標  
3. `2048/32768` をそのまま Paper IV の有効次元比 `ρ` と読むのは無理がある。これは **token budget 比** であって **有効次元比** ではない

この改稿では、TriAttention を **「学習済み距離選好に基づく、状態依存の粗視化作用素」** として再定式化し、その上で忘却論との接続を一段深くした。

## 1. まず事実として言えること

### 1.1 裏付け済みの技術事実

**一次ソース**

- 論文: [TriAttention: Efficient Long Reasoning with Trigonometric KV Compression](https://arxiv.org/abs/2604.04921)
- GitHub: [WeianMao/triattention](https://github.com/WeianMao/triattention)
- 結果表: `docs/results.md`
- 校正法: `docs/calibration.md`
- Gemma 4: [vLLM Gemma 4 recipe](https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html), [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4)

| 論点 | 何が裏付けられるか | 修正メモ |
|:---|:---|:---|
| Q/K 集中 | pre-RoPE 空間で Q/K が固定された非ゼロ中心の周りに集中する | これは論文の中核主張で、そのまま採用してよい |
| 安定性 | 位置・入力・ドメインに対して安定。Qwen3-8B では Math / Coding / Chat で MRL が 0.977–0.980、約 90% の head で `R > 0.95` | 元文書の数値は概ね正確 |
| 再構成 | 三角関数級数による attention 再構成は、Qwen3 / Qwen2.5 / Llama3 で per-head 分布が右裾重、平均 0.5 超、ピークは 0.6–0.9 付近。例示 head では `r = 0.72` | 「大多数で 0.6-0.9」より「分布のピークが 0.6-0.9」の方が正確 |
| 効率改善 | AIME25 で Full Attention と **同精度 40.8%** を保ったまま **2.5x throughput** または **10.7x KV memory reduction** | これは **matched-accuracy 条件** での主張 |
| 固定 budget 性能 | Qwen3-8B, KV budget=2048 では AIME25 は Full 40.8 に対し TriAttention 32.9。AIME24 42.1、MATH-500 は budget=1024 で 68.4 vs Full 69.6 | 元文書の「AIME25=40.8%」は条件が抜けていた |
| Memory retention | DFS 系 benchmark で depth 16 までは Full Attention とほぼ同等 | これは「圧縮耐性」の証拠であって、まだ RG 不変性の証明ではない |
| 校正ロバスト性 | 50k–960k token の校正量で性能が安定し、低品質 HTML でも大崩れしない | 「モデル固有性」を強く示唆するが、厳密には「完全入力独立」より控えめに読むべき |
| 対応モデル | README の verified/supported は Qwen3-8B / DS-Llama-8B / DS-Qwen-7B。results には GPT-OSS-20B も出る | 「正式対応」と「結果表掲載」は分けて書くべき |
| Gemma 4 基盤 | vLLM 側は Gemma 4 を公式サポート。31B dense は BF16 で 1x80GB 級、dual attention・256K context・global layer の unified K/V + p-RoPE が公式記述にある | **Gemma 4 が vLLM で動く**ことと、**TriAttention が Gemma 4 にそのまま適用できる**ことは別問題 |

### 1.2 ここを明確に直すべきだった

- **「AIME25 で 40.8% = Full と同等」**  
  → 固定 budget=2048 の結果ではない。**matched-accuracy 条件での throughput 比較**でそうなる。

- **「GPU 要件 = A100 80GB / RTX 4090 24GB」**  
  → 正確には、A100 80GB は論文の主要実験環境、24GB 級 GPU は OpenClaw ローカルデプロイの実証的モチーフ。**一般的最小要件として一行で並べると誤解を招く。**

- **「Gemma 4 未サポートだが vLLM 依存は問題なし」**  
  → vLLM 基盤は問題ないが、TriAttention 側の **attention module 追従・p-RoPE 対応・layer type 分離**が未解決なので、実際には「インフラは前進、実装は未確定」と書くべき。

## 2. 批評修正: どこが飛躍していたか

### 2.1 Paper X との接続: `U_TriAtt` は「一個の関手」ではなく「作用素族」

元文書の一番良い着眼点は、TriAttention を **選択的忘却** と見たことだ。ただし、そのまま単一の `U_TriAtt` を置くのは少し雑だ。

TriAttention の実体は、少なくとも次に依存する。

- 時刻 `t`
- 現在の cache 状態 `C_t`
- budget `B`
- pruning interval `β`（論文既定では 128）
- calibration stats `θ`
- head / layer ごとの score 関数

したがって、より正確には

```text
U^Tri_{t;B,β,θ}: C_t -> C'_t
```

のような **状態依存作用素族**として扱うべきだ。

この修正は重要で、元文書の

```text
ker(U_TriAtt) = {k | S̃(k) < B-th quantile}
```

も、そのままでは静的すぎる。正しくは

```text
E_{t;B,β,θ} = { k in C_t | rank_t(S_{B,β,θ}(k)) > B }
```

のような **その時刻の eviction set** として記述する方がよい。  
つまり TriAttention が忘れるのは「普遍的に同じ対象」ではなく、**その瞬間の幾何と budget が規定する可観測性の外側**である。

### 2.2 `U_KLN` と `U_Sum` の「間にある」は言い過ぎ

元文書では `U_TriAtt` を `U_KLN` と `U_Sum` の間に置いていたが、これは見た目ほど自明ではない。

- `U_KLN`: recency による hard selection
- `U_Sum`: aggregation による representation change
- `U_TriAtt`: score による sparse selection

`U_TriAtt` は **選択系**では `U_KLN` に近いが、**表現圧縮系**の `U_Sum` とは型が違う。  
したがって、現時点での最も安全な言い方は:

> TriAttention は、KLN 型の recency forgetful operator と Sum 型の summarization operator の「あいだ」にあるというより、**importance-weighted sparse forgetting** という第三の枝を作る。

この方が理論的にきれいだし、将来の比較もやりやすい。

### 2.3 MRL `R` を忘却強度 `α` と読むのは危うい

これは元文書で最も修正したい点の一つ。

`R` が高いことは、

- Q/K がよく集中している
- 距離選好が幾何学的に読みやすい
- trigonometric score が効きやすい

ことを意味する。つまり `R` はまず **圧縮則の可読性 / 幾何学的一貫性** であって、直接には **忘却の強さ** ではない。

高 `R` の head でも、budget が極端に小さければ大量に忘れる。逆に低 `R` でも、budget が十分大きければほとんど忘れない。  
だから

```text
R -> 1 だから α -> 0
```

は一般命題としては成立しない。

よりよい分解は次の 2 軸だ。

| 量 | 意味 |
|:---|:---|
| `κ_h := R_h` | その head の **圧縮可能性 / 幾何学的一貫性** |
| `γ_{t}(B)` | その budget 下での **実際の忘却圧** |

TriAttention の本質は「忘却が弱い」ことではなく、**忘却を幾何学的に制御できる**ことにある。

### 2.4 Paper IV との接続: budget 比と有効次元比は別物

元文書の

```text
2048 / 32768 ~ 0.06 だから ρ_spec ~ 0.06
```

は、直観としてはわかるが、そのままでは飛躍がある。

- `2048 / 32768` は **token budget ratio**
- Paper IV の `ρ` は **有効次元 / 有効自由度 / 実際に使われる表現空間の厚み**

であって、同じではない。

ここは次のように言い換えると強くなる。

> TriAttention の結果は、「タスクに効いている KV 幾何は、見かけの token 数よりずっと低い有効自由度で記述できる」ことを示唆する。ただし、その `ρ_eff` は budget 比ではなく、別途測る必要がある。

測るべきは例えば:

```text
srank(K) = ||K||_F^2 / ||K||_2^2
ρ_eff = srank(K_retained) / srank(K_full)
```

あるいは attention logit / hidden state の有効 rank でもよい。  
**Paper IV との本当の接続点は `B/L` ではなく `ρ_eff`** である。

### 2.5 Paper V との接続: 「RG 不変性の工学的実証」はまだ早い

window-based pruning を粗視化になぞらえるのは良い。ただし、

- pruning が 128 token ごとに起きる
- depth 16 まで memory retention が維持される

ことから、すぐに

- RG 不変性
- 固定点
- c 定理の上界到達

まで言い切るのは強すぎる。

ここで本当に必要なのは、少なくとも次の 3 つだ。

1. **半群性**  
   `R_{β2} ∘ R_{β1} ≈ R_{β1+β2}` がどれくらい成り立つか
2. **観測量不変性**  
   accuracy, logit correlation, hidden-state overlap などが coarse-graining 後も安定か
3. **flow の安定性**  
   budget や scale を変えたとき、head ごとの retention law が連続的に変形するか

したがって、ここは

> TriAttention は RG 的な離散粗視化作用素の**候補**である

と止めるのが適切で、`depth 16` は **圧縮耐性の経験的証拠**として使うべきだ。

## 3. 深化: より強い理論ブリッジ

ここからが元文書を一段進める部分。

### 3.1 「Q/K 中心 = 忘却場の臨界点」より、距離ポテンシャルを立てる方が強い

元文書では

- Q/K 中心 ↔ 忘却場 Φ の臨界点
- 三角関数級数係数 ↔ 忘却曲率の固有値

と読んでいたが、これは少し比喩が先走っている。  
より強い定式化は、**head ごとに距離ポテンシャルを定義する**ことだ。

```text
V_h(Δ) = - Σ_f |q̄_{h,f}| |k̄_{h,f}| cos(ω_f Δ - φ_{h,f})
```

すると

```text
Φ_h(Δ) = -∂_Δ V_h(Δ)
F_h(Δ) = ∂_Δ^2 V_h(Δ)
```

を導入できる。

このとき

- `V_h` の極小 = その head が好む距離帯
- `Φ_h = 0` = 好みの転換点
- `F_h` = 距離選好の曲率

となる。

この定式化の利点は、忘却論の「場」「曲率」を **Q/K 中心そのもの**に無理やり同一化しないで、**TriAttention が実際に作る distance landscape** に結びつけられる点だ。  
つまり、忘却場は hidden state 全体に拡張される前に、まず **距離多様体上のポテンシャル**として具体化できる。

### 3.2 忘却強度ではなく「可制御な忘却」として読む

TriAttention の本質は、忘却が少ないことではない。  
本質は、

- 何を忘れるかが
- 局所 attention の瞬間値ではなく
- 安定な pre-RoPE 幾何から予測できる

ことにある。

したがって、忘却論との接続は

> TriAttention = 忘却を弱める装置

ではなく、

> TriAttention = 忘却を **幾何学的に可制御化する装置**

として読む方が深い。

この観点では、`R` は「忘却強度」ではなく **忘却法則の可読性** だ。  
そして budget `B` はその上にかかる **実効的な圧縮圧** である。

### 3.3 Paper IV への深化: `ρ_budget` と `ρ_eff` を分ける

Paper IV に本当に繋ぐなら、次の 2 量を分けるべきだ。

| 記号 | 意味 |
|:---|:---|
| `ρ_budget = B / L` | 見かけ上どれだけ token を残したか |
| `ρ_eff` | 実際にどれだけの有効自由度を保持したか |

TriAttention が示唆しているのは、

```text
ρ_eff >> ρ_budget
```

が起こりうるということだ。  
つまり token は大幅に削っても、**意味のある自由度**はそこまで減っていない。

この読み替えなら、Paper IV の効果量減衰定理と自然につながる。  
逆に `ρ_budget = ρ_eff` と置くと、一番面白い部分を取り逃がす。

### 3.4 Paper V への深化: 離散 RG 作用素としての TriAttention

TriAttention の window pruning を、単なる比喩でなく **離散 RG 作用素**として読むなら、次のように書ける。

```text
R_{β,B,θ}: C_t -> C_{t+β}^{(B)}
```

ここで

- `β`: coarse-graining の時間幅
- `B`: 残す自由度
- `θ`: モデル固有の幾何統計

である。

このとき本当に問うべきは:

1. `R_{β,B,θ}` を反復したとき、観測量 `O` はどこまで保存されるか  
2. どの head / layer が「早く fixed pattern に落ちる」か  
3. どの budget で相転移的な性能崩壊が起きるか

であって、これができれば TriAttention は **forgetful RG の工学的 toy model** になる。

## 4. Gemma 4 / S-009 への実用評価 — 改訂版

### 4.1 ここは元文書より前向きに書いてよい

Gemma 4 については、元文書がやや慎重すぎた。

- vLLM は Gemma 4 を公式サポート
- 31B dense は BF16 で 1x80GB 級が公式最小ライン
- アーキテクチャは **dual attention**  
  - local sliding-window
  - periodic global attention
  - final layer global
  - global layers で unified K/V + p-RoPE

したがって、**S-009 の基盤として Gemma 4 + vLLM は十分現実的**である。

### 4.2 ただし TriAttention 移植は「校正を回せば終わり」ではない

ここは逆に、元文書より厳密に見た方がいい。

TriAttention は RoPE 系 attention でうまくいくが、Gemma 4 の global layer は

- p-RoPE
- unified K/V
- local layer と異なる head geometry

を持つ。  
よって calibration guide をそのまま流すだけでは不十分で、**layer type ごとの分離校正**が必要になる可能性が高い。

| Gemma 4 層種別 | TriAttention 的な見通し |
|:---|:---|
| local sliding-window layer | 標準 RoPE に近く、TriAttention の仮定に比較的近い |
| global layer | p-RoPE と unified K/V のため、そのままでは score 設計がずれる可能性 |
| 最終 global layer | 誤剪定の影響が大きいので最も保守的に扱うべき |

### 4.3 S-009 で本当にやるべき gate

元文書の Step 1–5 は方向として正しい。ただし、実験 gate をもう少し厳密に切るとよい。

#### Gate 0: ベースライン確立

- Gemma 4 31B を vLLM で素のまま動かす
- まず 32K で検証し、いきなり 256K には飛ばない
- Full Attention / native Gemma 4 挙動の基準を取る

#### Gate 1: 層種別ごとの Q/K 幾何測定

- local layer と global layer を分けて `R_h` を出す
- p-RoPE の回転部分と非回転部分を分離して観察する
- `R` の平均だけでなく **分散・二峰性** を見る

ここで初めて、

- local では TriAttention 的
- global では別スコアが必要

といった結論が出せる。

#### Gate 2: score 再構成の replay 検証

本番 pruning 前に、

- 実 attention
- trig score
- norm score
- 混合 score

の相関を **head / layer type 別**に測るべきだ。

Gemma 4 に対して必要なのは「MRL が高いか」だけではなく、

> その layer で **TriAttention の score が本当に future importance proxy になっているか**

である。

#### Gate 3: conservative budget から始める

TriAttention README でも chat では budget 12000 を勧めている。  
Gemma 4 31B / 256K context / hybrid attention を考えると、S-009 の初手を 2048 にするのは攻めすぎだ。

初期探索は例えば:

- 32K context: `B = 8192` or `12000`
- 128K context: `B = 12000–24000`
- `β = 128` は維持しつつ、global layer だけは別 rule を試す

くらいが現実的。

#### Gate 4: S-009 の理論観測量を差し替える

元文書の `hidden state F(l)` は良いが、さらに次を足すと強い。

- `κ_h = R_h` の layer profile
- `ρ_eff` の layer / head profile
- Full vs TriAttention の hidden-state subspace overlap
- retained distance histogram の時間発展

これで初めて、

- 忘却場がどう変わるか
- coarse-graining で何が保存されるか
- Gemma 4 の hybrid attention がどの層で異質か

が見える。

## 5. 最終判定 — 修正版

| 評価軸 | 改訂判定 | 確信度 |
|:---|:---|:---|
| TriAttention の工学的価値 | **高い**。長文脈推論圧縮の有力手法 | 高 |
| Paper X への接続 | **有望**。ただし単一 `U_TriAtt` ではなく作用素族として書くべき | 中高 |
| Q/K 集中 ↔ 忘却場 | **直接同一視は弱い**。ただし距離ポテンシャル `V_h(Δ)` を経由するとかなり良くなる | 中 |
| Paper IV との接続 | **budget 比では弱い**。`ρ_eff` を導入すれば強くなる | 中 |
| Paper V との接続 | **RG 的比喩としては有望**。だがまだ実証前段階 | 中低 |
| Gemma 4 への実装可能性 | **基盤は高い**。vLLM 公式対応あり。ただし TriAttention 移植は layer-type 対応が要る | 中高 |
| S-009 への価値 | **高い**。TriAttention は理論ネタであると同時に、長文脈忘却実験の実用インフラにもなる | 高 |

## 6. 一文で言い切るなら

TriAttention は「忘却が少ない」技術ではなく、**忘却を安定な pre-RoPE 幾何に投影して、粗視化を制御可能にした技術**として読むのが最も深い。  
その読み替えを採るなら、忘却論との接続はかなり強くなる。ただし、その強さは **`R = α` のような直接同一視**ではなく、**`V_h(Δ)`・`ρ_eff`・`R_{β,B,θ}` という中間構造を立てたときに初めて得られる**。
