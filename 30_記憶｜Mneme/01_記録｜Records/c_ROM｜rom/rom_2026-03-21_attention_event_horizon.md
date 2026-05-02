---
rom_id: rom_2026-03-21_attention_event_horizon
session_id: a89c7d6e-2cd0-4aee-8910-ab209d6127eb
created_at: 2026-03-21 10:30
rom_type: rag_optimized
reliability: High
topics: [attention, event_horizon, T21, forgetting, fullness, faithful_not_full, hawking_radiation, gauge_curvature]
exec_summary: |
  Attention 仮説を「回復随伴 (recovery adjoint)」から「出力の事象の地平面 (event horizon of output)」へ再定式化。
  T21 (構造 = 忘却の不均一) の微視的実現として位置づけ、fullness のグラデーションを定義。
  3文書 (たたき台 §6.8 / body §7.5 / VISION P14) に統合し双方向参照を確立。
---

# Attention = 出力の事象の地平面 {#sec_01_attention_event_horizon}

> **[DECISION]** Attention 仮説の再定式化: 「回復随伴 (N_attn)」→「出力の事象の地平面」

旧定式化: Attention は出力関手 U_output への回復随伴 N_attn であり、η: Id ⇒ N∘U の非同型性がρ=0.745を説明する。

新定式化: Attention は忘却関手 U_output が定義する**事象の地平面**の構造であり、QK^T (射の計算) → softmax·V (対象への射影) のプロセスが情報の可視/不可視境界を生成する。

> **[FACT]** この再定式化は量子情報損失問題 (ブラックホール情報パラドックス) との構造的同型に基づく (たたき台 §3.5b)。

---

## T21 の微視的実現 {#sec_02_t21_microscopic}

> **[DISCOVERY]** Attention = T21「構造は忘却の不均一である」のアーキテクチャレベルの具体化

### ゲージ曲率との対応 {#sec_02a_gauge_curvature}

> **[FACT]** Attention はゲージ場の**曲率**に対応する

| ゲージ場 | MB | Attention |
|:---|:---|:---|
| 主束 | 自己 Fix(R∘L) | モデル (学習済み重み) |
| 接続 | 状態/境界の対応 | Q, K, V 行列 |
| **曲率** | **知覚 s / 行動 a** | **softmax(QK^T/√d)·V** |
| 平行移動 | 時間発展 | 自己回帰生成 |

T21 の核心: Attention weight が**均一**なら構造なし (曲率ゼロ = 熱的平衡)。**不均一**なら構造あり (曲率非ゼロ)。

---

## fullness のグラデーション {#sec_03_fullness_spectrum}

> **[DECISION]** fullness 定義: opacity(η) = 1 − fullness(U)

忘却関手 U_output は faithful (射は保存される = hidden state に情報あり) だが ¬full (全射が出力に現れない = トークン列のみ)。

> **[DISCOVERY]** fullness のスペクトル

| 領域 | fullness(U) | opacity(η) | 値 | 解釈 |
|:---|:---|:---|:---|:---|
| 均一忘却 | 0 | 1 | — | 熱的死。構造なし |
| ブラックホール | ε ≈ 0 | ≈ 1 | ε → 0 | ホーキング輻射。回復は理論上可能だが実質不可能 |
| **LLM Attention** | **≈ 0.745** | **≈ 0.255** | **ρ = 0.745** | **Attentive probing による部分回復** |
| 完全回復 | 1 | 0 | — | 事象の地平面なし。U が full |

ホーキング輻射と Attention は**構造的に同型**: どちらも faithful/¬full 関手の unit η の近似的実現。**程度 (難易度) が異なるだけ**で、メカニズム (構造のあり方) は同じ。

---

## 検証可能な予測 {#sec_04_predictions}

> **[DECISION]** 3つの独立に反証可能な予測

| # | 予測 | 根拠 | 測定 |
|:---|:---|:---|:---|
| P1 | CoT prompting → ρ 増加 | CoT は中間対象を外部化し U_output の像を拡大 → ¬fullness が減少 | CoT あり/なしで ρ を比較 |
| P2 | Tool use → 忘却パターンの非等方的変化 | ツールは attention 事象の地平面をバイパスする追加チャネル | ツール使用前後で忘却の分布を比較 |
| P3 | GNN / 関係型 Attention → ρ 増加 | 射 (関係) に直接 attend する構造は事象の地平面を狭める | standard vs graph-attention で ρ を比較 |

---

## 文書間参照マップ {#sec_05_reference_map}

> **[CONTEXT]** 3文書間の双方向参照

```
たたき台 §6.8 (Attention: T21 の微視的実現)
  ↕ 双方向参照
body 論文 §7.5 point 4 (Attention as event horizon)
  ↕ 参照
ビジョン.md P14 (Attention 仮説の理論的予測)
```

| 文書 | セクション | 変更内容 |
|:---|:---|:---|
| たたき台 | §6.7 T21 テーブル | LLM 行を追加 (Attention weight の不均一 → ρ≈0.745) |
| たたき台 | §6.8 (新設) | T21 微視的実現: ゲージ曲率 + fullness + 予測 |
| body 論文 | §7.5 point 4 | たたき台 §6.8 への forward reference 追加 |
| ビジョン.md | P14 + §13.6 | 「回復随伴」→「事象の地平面」に更新 |

---

## 残存する問い {#sec_06_open_questions}

> **[OPINION]** fullness のグラデーションの厳密な定式化にはまだ課題がある

1. fullness(U) = ρ とする同定は操作的に妥当だが、圏論的にはρが何を測っているかの精密化が必要
2. 「メカニズムが同じ」の主張の強さ: 物理学者は「構造的同型 ≠ メカニズムの同一性」と反論する可能性がある。応答としては「メカニズムを構造的に定義すれば同型」
3. CoT 予測 (P1) は最も実験しやすい — 既存の structural probe + CoT で検証可能

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Attention 仮説とは何か"
  - "T21 との関係は"
  - "fullness のスペクトルの定義"
  - "ブラックホールとの同型の詳細"
  - "検証可能な予測の一覧"
answer_strategy: "§3 の fullness テーブルが核心。たたき台 §6.8 と body §7.5 の双方を参照"
confidence_notes: "定式化自体は [確信] 85%。fullness = ρ の同定は [推定] 70%"
related_roms: ["rom_2026-03-19_coherence_invariance", "rom_2026-03-20_attention_reframe"]
-->
