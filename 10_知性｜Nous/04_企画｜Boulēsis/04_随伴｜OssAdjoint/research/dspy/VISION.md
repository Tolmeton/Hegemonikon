# DSPy ⊣ Hermēneus 随伴統合ビジョン

> **優先度**: A (Phase A-② 精度の倍率器)
> **repo**: stanfordnlp/dspy (★ 32,400+)
> **論文**: Khattab et al. 2023 "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines" (577 citations)
> **最新版**: v2.5 (2025) → v3.0 ロードマップ (DAIS 2025)
> **HGK 対象**: Hermēneus (CCL コンパイラ / WF 実行エンジン)
> **ライセンス**: MIT (HGK Apache-2.0 と相容れる)
> **調査日**: 2026-03-14

---

## 1. DSPy とは何か

DSPy はプロンプトエンジニアリングを**コンパイラ問題**に変換するフレームワーク。

| 従来 | DSPy |
|---|---|
| 手書きプロンプトテンプレート | 宣言的 Signature (I/O 定義) |
| 試行錯誤でプロンプト改善 | Optimizer が自動チューニング |
| モデル変更で再調整 | Signature 不変、Optimizer が再コンパイル |

**核心思想**: "Programming, not prompting" — プロンプトはコンパイル対象であり、手書きするものではない。

### DSPy の3本柱

1. **Signature** — 入出力の型付き宣言 (`question: str → answer: str`)
2. **Module** — Signature を使うパイプライン部品 (`ChainOfThought`, `ReAct`, etc.)
3. **Optimizer** — Module のプロンプト・few-shot・重みを自動最適化

---

## 2. 既存の HGK 統合状況

📖 参照: `hermeneus/src/optimizer.py` (379行)

> [!IMPORTANT]
> **スケルトンが既に存在する。** BootstrapFewShot のみ実装済み。MIPROv2/COPRO は enum に定義されているがフォールバックで未実装。

### 現状の実装

| コンポーネント | ファイル | 状態 |
|---|---|---|
| `CCLExecutionSignature` | optimizer.py L104-108 | ✅ 基本形 (ccl+context→output) |
| `CCLModule` | optimizer.py L118-156 | ✅ ChainOfThought ラッパー |
| `CCLOptimizer` | optimizer.py L164-318 | ⚠️ BootstrapFewShot のみ |
| `MockOptimizer` | optimizer.py L348-370 | ✅ テスト用 |
| MIPROv2 | optimizer.py L44 (enum のみ) | ❌ 未実装 |
| COPRO | optimizer.py L43 (enum のみ) | ❌ 未実装 |

### 欠陥 (Gap)

| ID | 欠陥 | 影響 |
|:---|:---|:---|
| D-1 | MIPROv2 未実装 | Bayesian 最適化が使えない。BootstrapFewShot は探索が浅い |
| D-2 | Signature が1種類のみ | ccl+context→output しかない。WF ごとの特化 Signature がない |
| D-3 | 評価メトリクスが原始的 | 単語オーバーラップのみ。構造的品質 (Kalon 判定) が評価できない |
| D-4 | Multi-module 最適化なし | パイプライン全体 (CCL チェーン) の結合最適化ができない |
| D-5 | トレーニングデータなし | CCLExample の蓄積がゼロ。最適化を回す材料がない |
| D-6 | LM 固定 (OpenAI のみ) | `_configure_lm` が `OPENAI_API_KEY` ハードコード。Gemini/Claude 非対応 |
| D-7 | 最適化結果の永続化なし | 最適化したプロンプトが揮発する。次セッションで失われる |

---

## 3. 随伴マップ: DSPy ↔ HGK

### G (右随伴: DSPy → HGK に収束)

| DSPy 概念 | HGK 対応物 | 随伴の仕方 |
|---|---|---|
| `Signature` (宣言的 I/O) | CCL 型システム | CCL 式に入出力型を付与。`/noe+ :: context:str → insights:list[Insight]` |
| `Module` (パイプライン部品) | WF ステップ | 各 WF ステップを DSPy Module としてラップ |
| `BootstrapFewShot` | (既存) | few-shot 例の自動生成 |
| `MIPROv2` | (D-1: 未実装) | Bayesian 最適化で instruction + demo を同時最適化 |
| `COPRO` | (D-1: 未実装) | 座標上昇法でプロンプトを網羅的に改善 |
| `Evaluate` | Sekisho / Kalon 判定 | 品質メトリクスを DSPy の metric として注入 |
| `Assertion` | CCL 制約 (`C:{}`, `I:[]`) | 実行時アサーションでバックトラック |

### F (左随伴: HGK → DSPy に発散)

| HGK 概念 | DSPy への展開 |
|---|---|
| CCL 式 | Signature として形式化。修飾子 (+/-) が最適化深度を決定 |
| 24動詞 × 修飾 | 24 種の特化 Signature ファミリー |
| WF チェーン (`>>`, `~*`) | Multi-module DSPy Program として合成 |
| Sekisho 監査 | DSPy `Assertion` として組み込み |
| Sympatheia ログ | トレーニングデータのソース (D-5 解消) |

### Fix(G∘F): 不動点

```
CCL 式 ──F──→ DSPy Signature + Module
              ↓ (MIPROv2 最適化)
最適化されたプロンプト ──G──→ WF テンプレートに焼付
              ↓ (実行 + Sekisho 評価)
評価データ ──F──→ 次の最適化のトレーニングデータ
              ↓ (収束するまで繰り返し)
Fix(G∘F) = 自己改善する WF テンプレート
```

---

## 4. Import 候補の判定

| ID | candidate | 判定 | 理由 |
|:---|:---|:---|:---|
| D-01 | MIPROv2 Bayesian 最適化 | **Import** | 既存スケルトンの穴を埋める。3フェーズ (Bootstrap→Instruction→Bayesian) 全てが価値ある |
| D-02 | Signature 型システム強化 | **Import** | 24動詞 × 修飾の Signature ファミリー定義は CCL の表現力を構造的に向上させる |
| D-03 | Multi-module 最適化 (v2.5) | **Import** | CCL チェーン全体の結合最適化。`/bou+>>/ene+` のような合成 CCL の品質向上に直結 |
| D-04 | Assertion (実行時制約) | **Watch** | HGK は CCL 制約 + Sekisho で類似機能を持つ。重複リスク |
| D-05 | BetterTogether (student/teacher) | **Watch** | Ochēma の Claude/Gemini モデルルーティングと組合せ可能だが、統合コスト高 |
| D-06 | DSPy 3.0 HITL optimizer | **Watch** | Human-in-the-loop は Creator 協働パターンに合致。リリース待ち |
| D-07 | MLflow 連携 | **Skip** | HGK は Sympatheia + Motherbrain で独自のテレメトリを持つ。別系統不要 |

---

## 5. 実装ロードマップ

### Phase 0: データ基盤 (D-5 解消) — 前提条件

> 最適化にはトレーニングデータが必要。これが全ての前提。

- Sympatheia ログ + Sekisho 監査結果から `CCLExample` を自動収集
- `/noe+` 実行時の context→output ペアを永続化
- 目標: 主要動詞 (/noe, /bou, /ene, /lys, /ske) × 20例 = 100例

### Phase 1: MIPROv2 実装 (D-1 解消)

- `_create_optimizer()` の MIPROv2 分岐を実装
- LM 設定を Ochēma 経由に変更 (D-6 解消)
- 最適化結果を ROM 形式で永続化 (D-7 解消)

### Phase 2: Signature ファミリー (D-2 解消)

- 24動詞 × 修飾ごとの特化 Signature を定義
- `/noe+ :: context:str, prior_beliefs:list[str] → insights:list[Insight], confidence:float`
- `/ene :: plan:str, context:str → actions:list[Action], blockers:list[str]`

### Phase 3: Multi-module 最適化 (D-4 解消)

- CCL チェーン (`>>`, `~*`) を DSPy Program として合成
- パイプライン全体の結合最適化
- Sekisho 評価結果を metric として注入 (D-3 解消)

---

## 6. リスクと制約

| リスク | 深刻度 | 対処 |
|---|---|---|
| DSPy の LM 呼出コスト | 高 | MIPROv2 は最適化に大量の API call を消費。Ochēma のクォータ管理と連携必須 |
| トレーニングデータの品質 | 中 | Sympatheia ログの品質が低ければ最適化も低品質。Sekisho PASS のみ使用 |
| DSPy のバージョン追従 | 中 | v2.5→v3.0 の API 変更リスク。薄いアダプタ層で隔離 |
| 過学習 | 中 | 少数例で最適化すると特定パターンに過適合。交差検証必須 |

---

*Created: 2026-03-14 | Based on: DSPy v2.5 + Hermēneus optimizer.py 分析*
