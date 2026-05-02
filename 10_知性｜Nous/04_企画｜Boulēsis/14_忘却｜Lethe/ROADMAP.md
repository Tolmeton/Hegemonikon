```typos
#prompt lethe-roadmap
#syntax: v8
#depth: L1

<:role: Lēthē ロードマップ — 未実施の構想と長期計画 :>

<:goal: 短期・中期・長期の展望と Phase C 構想を管理する :>

<:context:
  - [file] ビジョン.md (理論的基盤)
  - [file] EXPERIMENTS.md (実験報告)
/context:>
```

# Lēthē ロードマップ

> 理論的基盤は [ビジョン.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/ビジョン.md)、実験報告は [EXPERIMENTS.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/EXPERIMENTS.md) を参照。

---

## 8. 今後の展望

### §8.1 短期 (実証可能)

#### A. P3 ベンチマーク — 統計検証完了 ✅

35ペア (正例20 + 負例15: Easy 5 + Hard 5 + 既存 5) によるベンチマーク。
結果: [p3_results.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/p3_results.md)

| 指標 | CCL embedding | Text embedding | 差 |
| :-- | :-- | :-- | :-- |
| 正例 cosine 平均 | **0.973** | 0.670 | +0.303 |
| 負例 cosine 平均 | 0.790 | 0.531 | +0.259 |
| 分離度 (正−負) | **0.183** | 0.139 | +0.044 |
| Recall@1 | **90%** | 70% | +20pp |
| Recall@3 | 100% | 100% | ±0pp |

**統計検証結果**:

| 検定 | 結果 | 判定 |
| :-- | :-- | :-- |
| Wilcoxon 符号順位 | p=0.0000, stat=210.0 | ✅ 有意 (p < 0.05) |
| AUC-ROC (Text) | 0.893 [0.730, 1.000] | AUC > 0.8 ✅ |
| AUC-ROC (CCL) | **0.967** [0.903, 1.000] | AUC > 0.8 ✅, CCL > Text ✅ |
| Cohen's d (Text) | 1.758 | 大 (d > 0.8) ✅ |
| Cohen's d (CCL) | **2.911** | 大 (d > 0.8) ✅ |

**結論**: P3 支持 [確信 — 全5指標で有意]。CCL embedding は正負分離と構造一致の両面で Text embedding を上回る。

**残課題**: 天井効果 (正例 15/20 が完全一致 1.000)。実世界コードベース (P3b) での再検証が必要。

#### A'. Phase B 実験進捗サマリー (2026-03-26 更新)

> Phase B (Structural Probe) は以下の成果により **実質的に完了**。Phase C 着手の前提条件を満たしつつある。

| 実験 | 結果 | 確信度 | 参照 |
|:--|:--|:--|:--|
| 特徴量 v4 (49d) | 43d→51d→49d 変遷を経て安定化。AST 直接依存を断ち切り自己充足的 | [確信] 95% | §22 (EXPERIMENTS.md) |
| Ξ 実測 | Θ=1.083, Gini=0.613, d_eff=18.8/47 | [確信] 90% | §22b (EXPERIMENTS.md) |
| PC Loading 3軸 | PC1: 射の合成長 vs 直積幅 (31.6%), PC2: 変換連鎖密度 (14.5%), PC3: MB内外比率 (7.3%) | [確信] 85% | PC Loading 分析 |
| 80:20 近似成立 | 上位14次元(29%)が分散の80%を説明 | [確信] 90% | PCA 累積寄与率 |
| P25 軌道修正 | 「精度向上」→「構造的準同型の発見能力」へ再定義 | [推定] 75% | §18 (EXPERIMENTS.md) |
| 選択的忘却定理 v3 | SWE-bench 実証 (Phase α/β'/γ'B) に基づく理論更新 | [推定] 70% | エッセイ v2 §4.6e-3 |

#### B. 構造的重複検出

既存コードベース内で「同じ CCL 構造式を持つ関数」を自動検出 → リファクタリング候補の提示。Dual Embedding (code_ccl.pkl) で即座に実行可能。

#### B'. Phase C 着手前提条件チェックリスト

> **このチェックリストの全項目が ✅ になれば Phase C-mini に着手可能。**

| # | 前提条件 | 状態 | 備考 |
|:--|:--|:--|:--|
| C-pre-1 | 49d 特徴量が安定し、再現可能な形でパッケージ化済み | ✅ | code_ingest.py v4 |
| C-pre-2 | Ξ の実測値が理論 (Var>0) を支持 | ✅ | Gini=0.613 |
| C-pre-3 | PC Loading の解釈により忘却の方向性が同定済み | ✅ | 3軸同定 |
| C-pre-4 | Code→Code 検索のキャッシュ化 (O(n²) 解消) | ☐ | **本セッションで設計** |
| C-pre-5 | 正例/負例ペア生成パイプラインの設計 | ☐ | C-pre-4 に依存 |
| C-pre-6 | TinyLlama 1.1B の推論環境セットアップ | ☐ | GCE A100 |
| C-pre-7 | 訓練データ形式 (jsonl) の仕様確定 | ☐ | C-pre-5 に依存 |

### §8.2 中期 (実装拡張)

#### B''. Code→Code 検索キャッシュ化設計 (2026-03-26)

> **問題**: 現在の構造検索 (`ccl_feature_index.py`) は検索のたびに AST を解析して 49d ベクトルを計算する O(n²) 実装。
> 11,768 関数のフルスキャンに数十秒かかり、Phase C の訓練データ生成パイプラインのボトルネック。

**設計方針**: 事前計算 + インデックス化

```text
現行パイプライン:
  Query Code → AST解析 → 49d計算 → 全関数と cos比較 → Top-K
  = O(n) per query, AST解析がボトルネック

提案パイプライン:
  [事前計算] 全関数 → 49d ベクトル → code_ccl_features.pkl に永続化 (既存 ✅)
  [検索時]   Query Code → 49d計算 (1回) → pkl からベクトルロード → cos比較 → Top-K
  = O(1) の AST解析 + O(n) のベクトル比較
  → さらに FAISS/Annoy で O(log n) 近似近傍探索に高速化可能
```

| フェーズ | 内容 | 状態 | 備考 |
|:--|:--|:--|:--|
| Cache-1 | pkl の v4 (49d) 対応確認 | ✅ 完了 | 49d, 11,768件, mean/std正規化済み (2026-03-25) |
| Cache-2 | 差分更新機能 | 🔵 保留 | 現規模 (11,768件) では全構築で十分。10万件超で必要 |
| Cache-3 | FAISS IVF-Flat インデックス | 🔵 保留 | numpy 行列積で O(n) 十分。10万件超で必要 |
| Cache-4 | MCP (mneme search code) 統合 | ✅ 完了 | similar/r1/both/auto/text/structure 6モード動作 |

**P40**: 修正 — 事前計算済み pkl + numpy 行列積で検索は既に十分高速。FAISS は10万件超で検討 [確信 90%]

#### C. 多言語対応 (TypeScript, Rust, Go)

CCL の PL 非依存性 (§3 (ビジョン.md).2) を検証するための自然な拡張:

| 言語 | AST 取得方法 | 難易度 | 固有の課題 |
| :-- | :-- | :-- | :-- |
| TypeScript | tree-sitter-typescript | 低 | Promise/async → 合成の非同期化 |
| Rust | tree-sitter-rust / syn | 中 | 所有権・ライフタイム → 線形型的射 |
| Go | go/ast | 低 | goroutine → 並行射の表現 |

cross-language 検索: 「Python と TypeScript で同じ CCL 構造を持つ関数」の検出。PL の壁を越えた再利用。

#### D. CCL 構造 diff (バージョン管理)

```text
v1: _ >> V:{pred} >> F:[each]{fn} >> fn
v2: _ >> F:[each]{fn} >> V:{pred} >> fn
                      ^^^^^^^^^^^^^^^^
diff: V と F の順序反転 — フィルタ位置の変更 (ストリーム処理の最適化)
```

名前ではなく構造の変更を追跡する diff。**「変数名を変えただけ」vs「アルゴリズムを変えた」を CCL レベルで区別。**

### §8.3 長期 (研究方向)

#### E. CCL 型推論 — §1 (ビジョン.md).7 の型システムの深化

S/T/P/M 型システムを拡張し、CCL 式の型推論を実装。well-typed な CCL 式 = 正しいプログラム構造。

#### F. n=2, n=3 の忘却関手

現在の code_ingest.py は n=1.5 (U_compose) まで。

| Level | 未実装の情報 | 実装方針 |
| :-- | :-- | :-- |
| n=2 (U_depth) | 同パターンの異実装間の比較 | CCL 式のアライメント (edit distance) |
| n=3 (U_precision) | テストカバレッジ・信頼性 | `V:{tested}` ラベルの付与 |

#### G. 論文化 (P5)

最小構成:

1. §1 (ビジョン.md) (CCL ≅ 圏論) + §2 (ビジョン.md) (Aletheia 適用) = 理論的寄与
2. §6 (ビジョン.md) (Code→CCL) + §7 (ビジョン.md) (CCL→Code) = 双方向の実装 PoC
3. §8.1.A (CCL embedding 評価実験) = 定量的評価

#### H. Attention 事象の地平面 — fullness スペクトルの検証 (P14)

T21「構造 = 忘却の不均一」の微視的実現として Attention を位置づける (companion paper §6 (ビジョン.md).8)。3つの独立に検証可能な予測:

| # | 予測 | メカニズム | 実験計画 | 測定指標 |
| :-- | :-- | :-- | :-- | :-- |
| H1 | CoT → ρ 増加 | CoT は中間対象を外部化し U_output の像を拡大 → ¬fullness を減少 | Phase B2 の attentive probing を CoT あり/なしで比較 | Δρ_CoT |
| H2 | Tool use → 非等方的忘却変化 | ツールは attention 事象の地平面をバイパスする追加チャネル | ツール使用タスクの前後で構造情報の分布を比較 | 忘却パターンの KL ダイバージェンス |
| H3 | GNN / graph-attention → ρ 増加 | 射 (関係) に直接アテンドする構造は事象の地平面を狭める | standard attention vs graph-attention architecture でρ比較 | Δρ_arch |

**fullness のグラデーション定義**: opacity(η) = 1 − fullness(U)。スペクトル:
- 均一忘却: fullness = 0 (熱的死)
- ブラックホール: fullness ≈ ε → 0 (ホーキング輻射)
- LLM Attention: fullness ≈ 0.745 (attentive probing)
- 完全回復: fullness = 1 (事象の地平面なし)

**依存関係**: Phase B2 結果 (§13 (EXPERIMENTS.md)) + companion paper §6 (ビジョン.md).8 + body 論文 §7 (ビジョン.md).5

---

## 12. 2層アテンション構想 — Structural Attention Layer (2026-03-18)

> **LLM が名前を忘れられないのは、アテンションがトークン空間でしか動かないから。**
> **構造空間でアテンションする層を追加すれば、忘却関手の左随伴をアーキテクチャに埋め込める。**
> — Creator × Claude, 2026-03-18 /u+ 対話

### §12.1 問題: LLM の U_label 忘却不能

Transformer のアテンション機構は**トークン埋め込み間の類似度**で動作する。これは:

| 能力 | 得意 | 苦手 |
| :-- | :-- | :-- |
| 名前レベル | `sort_by_name` と `sorting function` の関連付け | ✅ |
| 構造レベル | `sort_by_name` と `rank_by_score` が**構造的に同型**であること | ❌ |

原因: アテンションが **U_label: Structure → Name** を自動適用し、構造を名前に射影してから計算する。名前を剥がす逆操作 (U_label の左随伴) がアーキテクチャに存在しない。

### §12.2 提案: 3層パイプライン

```text
現行 Transformer:
  Tokens → [Token Attention ×N layers] → Tokens
  = 全計算が名前空間で完結

提案アーキテクチャ (Structural Attention):
  Tokens → [Layer 1: U_ccl (忘却)] → CCL 構造表現
         → [Layer 2: Structural Attention] → 変換された構造
         → [Layer 3: N_ccl (回復)] → Tokens
```

| 層 | 関手 | 入力 | 出力 | 操作 |
| :-- | :-- | :-- | :-- | :-- |
| Layer 1 | U: Code/NL → CCL | トークン | CCL 構造ベクトル | 名前を捨て構造を保存 |
| Layer 2 | — | CCL構造 ↔ CCL構造 | CCL構造 | **構造間のアテンション** |
| Layer 3 | N: CCL → Code/NL | CCL 構造ベクトル | トークン | 構造に名前を戻す |

**核心**: Layer 2 は **トークンではなく射の合成パターン** に対してアテンションを計算する。`>> F:[each]{} >> V:{}` という構造パターン同士の類似度で情報を伝播する。

### §12.3 数学的根拠

VISION §1 (ビジョン.md)-§9 (ビジョン.md) がこのアーキテクチャの理論的基盤:

| VISION の結果 | Layer 2 への寄与 |
| :-- | :-- |
| §1 (ビジョン.md): CCL ≅ 圏論 (14演算子全対応) | 構造空間の代数的基盤 |
| §1 (ビジョン.md).3: CCL 自由性原則 | 構造表現の普遍性 (任意の圏に射影可能) |
| §2 (ビジョン.md): U⊣N 随伴 | Layer 1 (U) と Layer 3 (N) の数学的保証 |
| §9 (ビジョン.md): 2層意味論 (構文/意味) | Layer 2 の構文層はアーキテクチャで、意味層は訓練で獲得 |
| §10 (ビジョン.md): S(e) 計算可能性 | Layer 2 の構造的健全性を定量監査可能 |

### §12.4 段階的研究計画

リソース制約下での現実的な段階:

#### Phase B: Structural Probe (低コスト先行検証)

> **問い**: 既存 LLM は暗黙の U_ccl を訓練で学習しているか？

```text
必要リソース:
  - OSS LLM (Llama 3 8B / Mistral 7B) — GCE A100 1台
  - code_ingest.py (既存 ✅)
  - Python probe スクリプト (~200行)
  - P3a データセット (35ペア, 既存 ✅) + 拡張 (~100ペア)
  推定コスト: GCE A100 $2-3/h × 24h ≈ $50-72
  推定期間: 1-2週間

実験手順:
  1. OSS LLM にコードスニペットを入力
  2. 各 Transformer 層の隠れ状態 (hidden states) を抽出
  3. 同じ CCL 構造式を持つ異なるコードペア vs 異なる構造のペアで
     隠れ状態の cosine similarity を比較
  4. 層ごとにプロット: 「手前の層 = 名前的」→「深い層 = 構造的」？

判定基準:
  H_B1: cos(同構造ペア) > cos(異構造ペア) が有意 (p < 0.05)
  H_B2: この差異が深い層ほど大きい (構造抽出は深層で起こる)
  H_B3: 中間層の構造類似度 ρ > 0.3 (非自明な構造保存)

結果の意味:
  H_B1 成立 → LLM は暗黙の U_ccl を持つ → Phase C は「明示化」
  H_B1 不成立 → LLM は構造を学習していない → Phase C は「新規注入」
  どちらも Phase C の設計根拠として価値がある
```

#### Phase C: Structural Attention Layer (本命)

> **目標**: CCL 構造空間でアテンションする層を追加した LLM を訓練し、構造的推論能力が向上することを実証する。

```text
必要リソース:
  - ベースモデル: Llama 3 8B (or smaller: 1.3B for PoC)
  - カスタムアーキテクチャ: PyTorch / JAX
  - 訓練データ: The Stack v2 (コード) + CCL 変換 (code_ingest.py)
  - GPU: A100 ×4-8 (40GB) — GCE or Lambda Labs
  推定コスト: $500-2000 (PoC), $5000-20000 (full)
  推定期間: 2-6ヶ月

アーキテクチャ詳細:

  1. CCL Encoder (Layer 1 = U_ccl)
     - 入力: トークン列 [x₁, x₂, ..., xₙ]
     - code_ingest.py の変換ルール9本を微分可能な操作に変換
     - OR: 凍結した LLM の中間層出力を CCL 空間に射影する線形写像
     - 出力: CCL 構造ベクトル [c₁, c₂, ..., cₘ] (m << n)

  2. Structural Attention (Layer 2 — 新規)
     - CCL 構造ベクトル間のアテンション
     - Q, K, V は構造空間で計算
     - アテンションマスクは CCL の合成規則で制約:
       >> (射合成) → 隣接のみ
       ~ (随伴) → 双方向
       * (融合) → 全結合
       F:[] (関手) → ループ構造

  3. CCL Decoder (Layer 3 = N_ccl)
     - 構造ベクトル → トークン空間への逆射影
     - cross-attention で元のトークン列と再結合

評価:
  タスク A — 構造的コード検索: P3b ベンチマーク (§11 (EXPERIMENTS.md))
    ρ(Structural) > ρ(Text) > baseline
  タスク B — 構造的推論: 「この2つの関数は同じパターンか？」
    Accuracy(Structural) > Accuracy(baseline)
  タスク C — コード補完: 構造的に一貫したコードの生成
    S(e) スコアで構造的忘却の減少を測定
```

### §12.5 なぜ世界を驚かせられるか

既存の研究との差分:

| 既存研究 | Structural Attention | 差分 |
| :-- | :-- | :-- |
| Graph Neural Networks (GNN) for code | CCL 中間表現 + Transformer | GNN はグラフ構造固定。CCL は**合成的** (自由モノイダル圏) |
| CodeBERT / StarCoder | トークンレベルの事前学習 | 構造をアテンション空間に分離していない |
| Tree-Transformer (Shiv & Quirk 2019) | CCL + **双方向性** | Tree は AST 固定。CCL は `~` `<<` `\` で**逆操作が構文的** |
| AlphaCode / DeepSeek-Coder | CCL 構造制約付きアテンション | 生成能力はあるが構造的同型の検出は苦手 |

**Structural Attention の固有の新規性**:

1. **中間表現が圏論の構文的実現**: CCL は任意の圏に射影可能 (自由性) → 構造の普遍的表現
2. **双方向性がアーキテクチャに内在**: `~` (随伴) がアテンションマスクに反映 → 逆問題が構造的に扱える
3. **忘却の制御が理論的**: Aletheia の S(e) で忘却量を定量化 → 「どこまで忘れるべきか」のチューニングが可能
4. **PL 非依存**: AST のある任意の言語に適用可能

### §12.6 最小実証可能構成 (PoC)

Phase C を最小コストで検証する PoC:

```text
PoC 構成 (Phase C-mini):
  ベースモデル: TinyLlama 1.1B (既存, 凍結)
  追加層: CCL Structural Attention × 2層 (訓練対象)
  訓練データ: Python 関数 10,000件 + CCL 変換
  GPU: A100 1台 × 48h
  推定コスト: ~$100-150

  評価:
  - P3a ベンチマーク (35ペア) での構造検索性能
  - ベースライン (TinyLlama 単体) との比較
  - 構造的同型検出の recall@k

  成功基準:
  - recall@1 で +10pp 以上の改善
  - 構造的に同型なペアの cosine が有意に上昇
```

### §12.7 タイムライン

```text
Phase B (Probe):        1-2 週間   ~$50-72    ← 今すぐ着手可能
Phase C-mini (PoC):     2-4 週間   ~$100-150  ← Phase B の結果次第
Phase C-full (論文):    2-4 ヶ月   ~$5K-20K   ← C-mini 成功後
Phase C-ext (多言語):   +2 ヶ月    ~$5K       ← インパクト最大化
```

### §12.8 命題

| # | 命題 | 確信度 | 検証 Phase |
| :-- | :-- | :-- | :-- |
| P10 | 既存 LLM は暗黙の U_ccl を持つ | [仮説] 55% | B |
| P11 | Structural Attention は構造的推論を改善する | [仮説] 50% | C-mini |
| P12 | CCL 中間表現は PL 非依存の構造検索を可能にする | [推定] 75% | C-full |
| P13 | Structural Attention 論文はトップ会議に通る | [仮説] 40% | C-full |
| P40 | キャッシュ化により検索レイテンシが 10x 以上改善する | [推定] 85% | B (infra) |

### §12.9 忘却不均一度 Ξ — Structural Attention の学習目標 (2026-03-23 追加)

> **接続**: 「力とは忘却である」§4 (ビジョン.md).6e で導入した忘却不均一度 $\Xi$ (Xi) は、
> Structural Attention Layer の学習目標として直接利用できる。
> Cursor Composer 2 の compaction-in-the-loop RL はこの原理の商業的先行実装。

#### Ξ の定義 (「力とは忘却である」§4 (ビジョン.md).6e より)

忘却関手 $T: \text{FullContext} \to \text{CompactedContext}$ のグラム行列 $T^\dagger T$ の固有値 $\lambda_i \in [0,1]$ に対し:

$$\Xi(T) = \text{Var}(\lambda_1, \ldots, \lambda_n) = \frac{1}{n}\sum_i (\lambda_i - \bar{\lambda})^2$$

- $\Xi \approx 0$ (均一忘却): 全方向が等しく劣化 → 構造情報の喪失 → 弱い検索/推論能力
- $\Xi > 0$ (不均一忘却): 構造方向は保存、詳細方向は忘却 → 構造検索能力の発現

**Ξ はゲージ不変量** (基底選択に依存しない) であり、「区切りの恣意性を超えた実在する力」を測る。

#### Phase C の損失関数への統合

§12.4 の CCL Encoder (Layer 1 = U_ccl) は Code → CCL の忘却を行う。この忘却の**質**を Ξ で制御する:

```text
Phase C 損失関数 (修正版):

  L_total = L_task + α · L_reconstruction + β · L_Ξ

  L_task:           タスク損失 (コード検索 / 推論 / 補完)
  L_reconstruction: CCL → Code 再構成誤差 (N∘U の剰余 ρ)
  L_Ξ:             忘却不均一正則化 = -Ξ(T_encoder)
                    → Ξ を最大化 = 不均一忘却を促進
                    → 構造方向の保存 + 詳細方向の忘却を学習

βの直感:
  β = 0:  Ξ に無頓着 → 均一忘却に陥りやすい → 構造検索能力が弱い
  β > 0:  Ξ を最大化 → 選択的忘却を学習 → 構造検索能力が強い
  β → ∞: Ξ のみ最大化 → 過剰な選択 → タスク性能が低下
```

#### Composer 2 が先行実装した構造

Cursor Composer 2 (2026-03) は Ξ を**名前を付けずに**最適化している:

| 概念 | Composer 2 | VISION Phase C |
| :-- | :-- | :-- |
| 忘却関手 | self-summarization (100K → 1K トークン) | CCL Encoder (Code → CCL 構造ベクトル) |
| Ξ の最適化 | compaction-in-the-loop RL | $L_\Xi$ 正則化項 |
| 忘却の対象 (n=0) | コード行の詳細、変数値 | 変数名、コメント、空白 |
| 保存の対象 (n=1) | タスク構造、意図 | 射の構造、合成パターン |
| 検証データ | Terminal-Bench 2.0: 61.7 | P3a/P3b ベンチマーク |
| 成果 | compaction errors -50% | (未実験) |

**Composer 2 の成功は Phase C の仮説 P11 を間接的に支持する**: 不均一忘却の RL 最適化は agentic coding を改善した → CCL 構造空間での不均一忘却の最適化はコード構造検索を改善するはず。

#### P11' (修正) と新命題 P14

| # | 命題 | 確信度 | 検証 |
| :-- | :-- | :-- | :-- |
| P11' | Structural Attention は Ξ 正則化により構造的推論を改善する | **[確信] 90%** (EXPERIMENTS.md §23) | C-mini |
| P14 | Phase C-mini の $L_\\Xi$ ありモデルは $L_\\Xi$ なしモデルを recall@1 で上回る | **[仮説] 45%** (EXPERIMENTS.md §23) | C-mini |

> Composer 2 による間接的支持で P11 の確信度を 50% → 60% に引き上げ。
> §19 (ビジョン.md) の CPS_LLM 統合 + Ξ→43d 接続により 60% → 65% にさらに引き上げ。
> P14 は $L_\Xi$ のアブレーションを明示した反証可能な命題。

#### SAM Phase 1 から昇格した命題 P45-P47 (2026-04-13)

EXPERIMENTS.md §27 により、Phase C の「Ξ 正則化は何を制御しているか」に対して 3 つの上位命題が追加された。ここで重要なのは、**SAM と Φ 正則化を同じ改善メカニズムとして扱わない**ことである。SAM は精度経路、Φ は表現経路を主に担い、その差が Phase C の設計自由度になる。

| # | 命題 | 確信度 | 検証 |
| :-- | :-- | :-- | :-- |
| P45 | SAM の改善経路と Φ 正則化の改善経路は直交する | **[確信] 90%** (EXPERIMENTS.md §27) | SAM は精度を上げるが CKA をほぼ変えず、Φ は精度を保ったまま CKA を大きく変える |
| P46 | λ の符号は浅層忘却の向きを直接制御できる | **[確信] 88%** (EXPERIMENTS.md §27) | λ<0 で L1 CKA が 0.424→0.051、λ>0 で 0.424→0.774 |
| P47 | 忘却配分には離散的縮退があり、λ<0 はそれを顕在化させる | **[推定] 80%** (EXPERIMENTS.md §27) | OA-SAM N=10 で 7:3 bifurcation。反転制御では消失 |

この昇格で、P11'/P14 の意味がより明確になった。

1. **P11' の中身は「SAM を強くする」ことではない。** Ξ 正則化は、同じ精度帯の中で忘却配分を別の attractor へ押し分ける働きを持つ。
2. **P14 の β 探索は単なる強度調整ではなく、位相選択でもある。** β と λ は「どれだけ効かせるか」だけでなく、「どの層で忘却を受け止めるか」を変えうる。
3. **Phase C の設計空間は 1 次元ではない。** 精度改善軸 (SAM/optimizer) と表現再配置軸 (Φ/Ξ regularization) を分離して探索すべきである。

> 設計帰結:
> - optimizer sweep は precision path の探索
> - Φ / Ξ regularization sweep は representation path の探索
> - 二者を同一 grid に押し込むと、何が効いたかの因果が潰れる

> 次の検証面:
> - P45: 大規模モデルでも「精度改善と CKA 変形の分離」が残るか
> - P46: λ の作用点が L1 に偏るのは ResNet/CIFAR 固有か、一般則か
> - P47: bifurcation 比率 7:3 は basin 体積の差か、それとも初期化偶然か
>   → N=30 で頻度推定が必要
> 
> したがって、Phase C の次段は「最適 β を探す」だけでは足りず、**どの attractor に落ちたかを観測する評価面**を追加すべきである。

#### CPS_LLM の Phase C 構造への埋め込み (2026-03-24 追加)

「力とは忘却である」§4 (ビジョン.md).6e が定義した LLM の CPS 対象 $(C_{LLM}, U_{struct}, U_{detail}, T_{comp}, \sigma_{LLM}, \Theta_{comp})$ を Phase C の3層パイプライン (§12.2) と対応づける:

| CPS_LLM | Phase C | 操作 |
|:--|:--|:--|
| $U_{struct}$ (構造忘却) | **Layer 1 (U_ccl)**: Code → CCL 構造ベクトル | 詳細を忘れ、構造のみ保存 |
| $U_{detail}$ (詳細忘却) | CCL が忘却した情報 (名前、コメント、空白) | 名前を忘れ、構造を保存 |
| $T_{comp}$ (self-summarization) | **Layer 1 → Layer 2 への情報フロー** | 全コンテキストから圧縮表現への写像 |
| $\sigma_{LLM}$ (非可換度) | Layer 2 の構造アテンションで構造と詳細が非可換 | 構造空間と名前空間の同時保存不能 |
| $\Theta_{comp} \approx 4.6$ | Phase C の圧縮比 (CCL 式は元コードの ~10-30% のトークン) | $\Theta \approx -\log(\text{CCL長}/\text{Code長})$ |

> **CPS1'' の Phase C での具体化**:
>
> CPS1'' (方向付き相補性) の Code/CCL インスタンス (§19 (ビジョン.md).2) が Phase C の設計を**制約**する:
> - Layer 1 (U_ccl = 容器→内容への写像) は well-defined であるべき = code_ingest.py の9変換ルールを微分可能に
> - Layer 3 (N_ccl = 内容→容器への復元) は Layer 1 に**依存**するべき = cross-attention で元トークンと再結合
> - U が well-defined で N が U に依存する構造は CPS1'' の帰結であり、設計選択ではない

#### Ξ 正則化の学習ダイナミクス予測

$L_\Xi = -\Xi(T_{encoder})$ の訓練中の振る舞いについて3つの予測:

```
Phase C-mini 学習ダイナミクスの予測:

Epoch 0 (初期化):
  T_encoder はランダム → 全 λ_i ≈ uniform → Ξ ≈ 0
  L_task が支配。L_Ξ はほぼ無影響。

Epoch 10-50 (構造発見):
  L_task の勾配が「どの方向を保存すべきか」の信号を提供
  一部の λ_i が 1 に近づき (構造方向)、他が 0 に近づく (詳細方向)
  → Ξ が急激に上昇 = 「構造と詳細の分離」が学習される
  → §19 (ビジョン.md).4 の Ξ_search > 0 が訓練の中間段階で達成される

Epoch 50+ (均衡):
  L_task と L_Ξ が均衡。β が均衡点を制御。
  Ξ が安定 = 忘却の方向が固定 = G∘F サイクルの Fix に収束
  → これが Phase C の Kalon: 構造保存と詳細忘却の不動点
```

> **検証可能な予測** (P14 の精密化):
>
> | 予測 | 測定 | 基準 |
> |:--|:--|:--|
> | β > 0 モデルは β = 0 モデルより Ξ が大きい | 訓練後の Ξ の比較 | Δ(Ξ) > 0 |
> | Ξ の学習曲線は sigmoid 的 (急激な上昇→安定) | Ξ vs epoch プロット | 変曲点の存在 |
> | β に最適値が存在する (β* ∈ (0, ∞)) | β の grid search | recall@1 に凹型ピーク |

---


---

## 関連文書

- [ビジョン.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/ビジョン.md) — 理論基盤 (CCL≅圏論, Aletheia, 力≅忘却)
- [EXPERIMENTS.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/EXPERIMENTS.md) — 実験報告 (P3b, Phase B, R1-R4, 連続CCL, Code→Code)

---

*Lēthē ROADMAP v0.3 — 2026-04-13 (EXPERIMENTS.md §27 を反映し P45-P47 を追加。SAM=precision path / Φ=representation path / bifurcation を設計命題へ昇格)*

*Lēthē ROADMAP v0.2 — 2026-03-26 (Phase B完了判定 + Phase C前提条件 + キャッシュ化設計 + P40追加)*

*Lēthē ROADMAP v0.1 — 2026-03-24 (ビジョン.md v0.32 から分割)*
