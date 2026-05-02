# PROOF: [L2/実験] <- 60_実験｜Peira/oblivion
# 実験計画: Gemma 4 忘却場プロファイリング

> **ID**: EXP-OBL-GEMMA4
> **起源**: S-009 (Pinakas SEED)
> **起案日**: 2026-04-03
> **状態**: 計画策定完了 / 未実行
> **確信度**: [推定 55%] — パイプライン互換性は高い (extract/compute 共に model-agnostic 設計) が、(1) N<d 共分散安定性、(2) ハイブリッドアテンション config の実在性、(3) cross-model 比較の統制条件、(4) ハイブリッドアテンションにおける統計多様体の連続性、(5) PCA 次元依存性、(6) D_KL 有限サンプルバイアスの層タイプ依存性 が未検証。/exe+ 監査 🔴3件(C-1〜C-5) + /ele+ 反駁 🟠5件(C-6〜C-10) → 制約 §3.5 で対処

---

## §1. 目的

Gemma 4 31B Dense の忘却場プロファイル (Φ(l), α(l), F(l)) を測定し、
既存の Dense モデル (Mistral-7B, Qwen2-1.5B) との**アーキテクチャ横断比較**を実施する。

### 検証命題

| ID | 命題 | 根拠 |
|:---|:-----|:-----|
| **G4-H1** | U 字ポテンシャル構造はアーキテクチャに不変 | Mistral-7B / Qwen2-1.5B の既存データで確認済。Gemma 4 で再現されれば普遍性の証拠 |
| **G4-H2** | ハイブリッドアテンション (sliding-window + global 交互) は忘却場に周期的パターンを生む | sliding-window 層は局所的情報のみ保持 → Φ(l) が奇偶で振動する可能性 |
| **G4-H3** | α(l) の S 字遷移は Gemma 4 でも中間層付近で発生する | α-N1 予測の一般性検証。deeper model (31B) では遷移幅 l₀ が相対的に狭い可能性 |
| **G4-H4** | F(l) のピークは α≈0 遷移面に局在する | P3b 予測の cross-model 検証 |

---

## §2. 被験体スペック

| 項目 | Gemma 4 31B Dense |
|:-----|:-------------------|
| **HF model name** | `google/gemma-4-31b` |
| **パラメータ** | 31B (Dense) |
| **アテンション** | **ハイブリッド**: sliding-window (局所) + full global attention を交互配置 |
| **RoPE** | Proportional RoPE (p-RoPE) |
| **K/V** | 統一 K/V キャッシュ (global 層) |
| **コンテキスト窓** | 256K tokens |
| **VRAM (BF16)** | ~52 GB → **A100 80GB** |
| **VRAM (4bit)** | ~16-18 GB → L4 24GB で可 |
| **ライセンス** | Apache 2.0 |
| **リリース日** | 2026-04-02 |

### 対照群

| モデル | パラメータ | アテンション | 既存データ | 備考 |
|:-------|:-----------|:-------------|:-----------|:-----|
| Mistral-7B-v0.1 | 7B | **sliding-window attention (W=4096)** | `theta_b_external/` — CKA, attention entropy | ⚠️ 均一ではない。Gemma 4 SWA との比較に有用だが「均一対照」にはならない |
| Qwen2-1.5B | 1.5B | 均一 self-attention | `pei_p1_qwen2_1_5b_results.json` | 均一対照 |
| TinyLlama-1.1B | 1.1B | 均一 self-attention | P3 パイプラインテスト用 | 均一対照 |
| LLaMA-2-7B (**追加検討**) | 7B | **full self-attention** | 未取得 | 🔑 真の均一 full attention 対照。Mistral (SWA) との対比で SWA 効果を分離 |

---

## §3. 実験設計

### Phase 1: Hidden State 抽出

**既存パイプライン**: `50_自律研究｜Autoresearch/p3_alpha_force/extract_hidden_states.py`

```bash
# A100 80GB, BF16
python extract_hidden_states.py \
    --model google/gemma-4-31b \
    --num-samples 200 \
    --pooling mean \
    --max-length 512 \
    --dtype bfloat16 \
    --output results_gemma4_31b/
```

**互換性チェックリスト**:
- [ ] `transformers` ライブラリが Gemma 4 アーキテクチャに対応しているか確認
- [ ] `output_hidden_states=True` が全層を返すか確認
- [ ] hidden state の shape が (batch, seq_len, hidden_dim) か確認
- [ ] ハイブリッドアテンションの層数・交互パターンを model config から取得
- [ ] A100 80GB で BF16 のメモリフットプリント確認 (~52GB + KV cache)

**想定出力**: `hidden_states.npz` — shape (L+1, 200, hidden_dim)

### Phase 2-5: 情報幾何量の計算

**既存パイプライン**: `50_自律研究｜Autoresearch/p3_alpha_force/compute_geometry.py`

```bash
python compute_geometry.py --input results_gemma4_31b/ --pca-dim 64
```

**計算される量**:

| 量 | 定義 | Phase |
|:---|:-----|:------|
| g(l) | Fisher 計量 = (1/N) Σ ‖Δh‖² | 2 |
| Φ(l) | 忘却場 = D_KL(p_l ‖ p_L) | 2 |
| T(l) | Chebyshev 形式 = C₁₁₁/g₁₁ | 3 |
| α(l) | α-パラメータ = tanh(c·κ(l)) | 4 |
| F(l) | 忘却曲率 = (α/2)·T·[∂Φ/∂l + Φ·∂α/∂l] | 5 |

### §3.5 制約と前提

> [!IMPORTANT]
> 以下の制約は /exe+ (2026-04-03) および /ele+ (2026-04-03) で検出された脆弱性への対処。
> C-1〜C-5: 運用的制約 (/exe+ 由来)。C-6〜C-10: 理論的前提制約 (/ele+ 由来)。

#### 運用的制約 (C-1〜C-5, /exe+ 由来)

| ID | 制約 | 根拠 | 対処 |
|:---|:-----|:-----|:-----|
| **C-1** | **PCA 圧縮は Phase 2 の必須前提条件** | N=200, d≈5120 → N<d で共分散行列がランク不足。`np.cov` → `np.linalg.inv` が数値的に不安定 | `compute_geometry.py` は PCA (d'=64) を Phase 2 で最初に実行する。**PCA をスキップしてはならない**。d'=64 なら N=200>d'=64 で安定 |
| **C-2** | **全モデルで同一プロンプトセットを使用** | Cross-model 比較の科学的妥当性。プロンプト差異が忘却場に与える影響を排除 | `load_code_samples(num_samples=200, seed=42)` の合成コードスニペットを全モデル共通で使用。**seed=42 を変更しない**。既存データが異なる seed の場合は再取得 |
| **C-3** | **`use_cache=False` を必ず指定** | KV cache が VRAM を追加消費。31B BF16 (~52GB) + KV cache で A100 80GB を超過しうる | `extract_hidden_states.py` L439 で既に `use_cache=False`。CLI では **`--max-length 512`** が上限。OOM 時は `--max-length 256` にフォールバック |
| **C-4** | **Phase 6 実行前に `AutoConfig` のフィールド名を実機確認** | `config.attention_pattern` は推測的フィールド名。実在しなければ Phase 6 が実行不能 | タスク1 (互換性確認) で `AutoConfig.from_pretrained('google/gemma-4-31b')` を実行し、ハイブリッドアテンション関連フィールドの実名を確定。**確定するまで Phase 6 のコード作成を開始しない** |
| **C-5** | **E4B テストは「パイプライン互換」のみ確認。31B 固有の問題は別途検証** | E4B と 31B Dense はアーキテクチャが異なる可能性。E4B 成功 ≠ 31B 動作保証 | タスク2 を「E4B でパイプライン実行可能」に限定し、タスク3 の冒頭で小サンプル (N=5) の 31B テストを追加 |

#### 理論的前提制約 (C-6〜C-10, /ele+ 由来)

| ID | 制約 | 矛盾根拠 | 対処 |
|:---|:-----|:---------|:-----|
| **C-6** | **ハイブリッドアテンション下での統計多様体の連続性を検証** | sliding-window→global の層遷移で、Fisher 計量 g(l) の差分 Δh は「同一多様体上のパラメータ移動」ではなく「異なる統計多様体間の写像」を測定している可能性。G4-H2 の周期パターンがアテンション機構の artifact か忘却の構造かを判別不能 | **Phase 6 に層タイプ別 Fisher 計量分布検定を追加**: sliding 層のみ / global 層のみで g(l), Φ(l) を分離計算し、Mann-Whitney U 検定で有意差を判定。有意差 (p<0.05) があれば「統計多様体が層タイプ間で不連続」→ G4-H2 は解釈に注意が必要。有意差がなければ単一多様体仮定は妥当 |
| **C-7** | **Mistral-7B は sliding-window attention (W=4096) であり「均一 self-attention」ではない** | 対照群が「均一対照」として不適切。Mistral SWA と Gemma 4 SWA は部分的に同じ機構 → cross-model 比較の交絡因子 | 対照群テーブルを修正済。アテンション構造による3群分類: (1) full attention (LLaMA-2-7B, 追加検討), (2) SWA (Mistral-7B), (3) hybrid (Gemma 4)。**LLaMA-2-7B を追加すれば SWA 効果を分離可能** |
| **C-8** | **PCA 次元 d'=64 が最適である根拠がない** | d'=64 で Φ(l) の Critical な情報が切り捨てられる可能性。d≈5120 → d'=64 で 98.75% の次元を破棄 | **Phase 2-5 に PCA 感度分析を追加**: d'∈{32, 64, 128, 256} で Φ(l) を再計算し U 字構造の安定性を確認。d' 依存で消滅する構造は artifact と判定。**先行検証**: Qwen2-1.5B の既存データで感度分析を先行実行 (低コスト) |
| **C-9** | **D_KL の有限サンプルバイアスが層タイプ依存する可能性** | ガウス近似の D_KL は有限サンプルバイアス ≈ (d'+1)/2N を持つ。sliding 層と global 層で分散構造が異なれば、バイアス量も層タイプ依存 → G4-H2 の偽陽性 | **Phase 2 の Φ(l) 計算時にバイアス補正を適用**: bias = (d'+1)/2N (d'=64, N=200 → bias≈0.16)。sliding/global 群間の Φ(l) 差が補正後も 10%超ならパターンは真と判定 |
| **C-10** | **「完全成功」基準が C-6〜C-9 の解決を暗黙に前提** | G4-H2 の検証には C-6 (多様体連続性) と C-9 (バイアス補正) が必要。G4-H4 の検証には C-8 (PCA 依存性) の排除が必要 | 成功基準 §6 を修正: 完全成功の定義に「C-6〜C-9 の検証を含む」を明記 |

### Phase 2-5 追加: PCA 感度分析 (C-8 対処)

```bash
# d' を変えて Φ(l) の安定性を検証
for DIM in 32 64 128 256; do
  python compute_geometry.py --input results_gemma4_31b/ --pca-dim $DIM --output results_gemma4_pca${DIM}/
done
```

**判定基準**: d'=64 → d'=128 で U 字構造の peak 位置が ±2 層以内に安定していれば d'=64 は妥当。Peak が移動する場合は d'=128 を採用。

### Phase 6 (新規): ハイブリッドアテンション解析

既存パイプラインにない、Gemma 4 固有の解析:

1. **層タイプのラベリング**: model config からどの層が sliding-window / global かを取得
2. **層タイプ条件付き統計**: g(l), Φ(l), α(l), F(l) を sliding-window / global で分離
3. **奇偶パターン検定**: 忘却場に層タイプ依存の周期構造があるか (G4-H2 の検証)
4. **統計多様体連続性検定 (C-6 対処)**: sliding 群と global 群で g(l) の分布に有意差があるか Mann-Whitney U 検定を実施。p<0.05 なら「多様体不連続」を報告
5. **D_KL バイアス補正 (C-9 対処)**: Φ(l) から bias=(d'+1)/2N を差し引き、補正前/補正後の比較プロットを生成

```python
# 追加コード案 (compute_geometry.py への拡張)
def label_layer_types(model_name: str) -> list[str]:
    """Gemma 4 の各層が sliding-window か global かを返す。"""
    from transformers import AutoConfig
    config = AutoConfig.from_pretrained(model_name)
    # config.attention_pattern or similar field
    # → ["sliding", "global", "sliding", "global", ...]
    ...
```

### Phase 7: Cross-Model 比較

| 比較 | 方法 |
|:-----|:-----|
| U 字ポテンシャル | Φ(l/L) を正規化した層位置でオーバーレイ |
| α 遷移構造 | sigmoid フィット (l_c, l_0) の比較 |
| F(l) ピーク位置 | peak_layer / L の比較 |
| Schur-Horn | Gini(diag) ≤ Gini(spec) の全モデル確認 |

---

## §4. 実行計画

| # | タスク | 環境 | 依存 | 推定時間 |
|:--|:-------|:-----|:-----|:---------|
| 1 | `transformers` の Gemma 4 対応確認 + **`AutoConfig` フィールド名確定 (C-4)** | local | — | 15 min |
| 2 | `extract_hidden_states.py` の互換性テスト (E4B, CPU/小サンプル) **※パイプライン互換のみ確認 (C-5)** | local | 1 | 30 min |
| 3 | Phase 1: Hidden State 抽出 (31B, A100)。**冒頭で N=5 小テスト→OOM回避確認 (C-3,C-5)** | Colab A100 | 2 | ~30 min (根拠: 7B≈5min/200samples, 31B≈4.5x→~22min。余裕込み30min) |
| 4 | Phase 2-5: 情報幾何量計算 **※PCA スキップ禁止 (C-1)** | Colab A100 | 3 | ~30 min |
| 5a | **PCA 感度分析: d'∈{32,64,128,256} で Φ(l) 再計算 (C-8)** | Colab A100 | 4 | ~20 min |
| 5b | Phase 6: ハイブリッドアテンション解析 + **多様体連続性検定 (C-6)** + **D_KL バイアス補正 (C-9)** **※タスク1でフィールド確定済が前提 (C-4)** | local | 1,4 | 1.5h |
| 6 | Phase 7: Cross-Model 比較プロット **※同一 seed=42 (C-2)、Mistral は SWA として分類 (C-7)** | local | 5a,5b | 1h |
| 7 | 結果の解釈・Pinakas/Handoff 更新 | local | 6 | 30 min |

**クリティカルパス**: 1 → 2 → 3 → 4 → 5 → 6 → 7
**ボトルネック**: タスク3 (Colab A100 のセッション確保)

---

## §5. リスクと対策

| リスク | 確率 | 影響 | 対策 | 制約 |
|:-------|:-----|:-----|:-----|:-----|
| `transformers` が Gemma 4 未対応 | 低 (10%) | 高 | `pip install --upgrade transformers` で最新版。それでもダメなら vLLM 経由 | — |
| A100 80GB でもメモリ不足 (**KV cache 込み**) | 中 (25%) | 中 | `use_cache=False` (既定) + `--max-length 256` フォールバック。**タスク3 冒頭で N=5 テスト** | C-3 |
| hidden_states の返却がアーキテクチャ固有 | 中 (25%) | 中 | HF model card で出力形式確認。必要なら extraction コード分岐 | C-5 |
| sliding-window 層の hidden state が global と質的に異なり PCA が歪む | 中 (30%) | 低 | 層タイプ別 PCA / 全層統一 PCA の両方で計算し比較 | — |
| U 字ポテンシャルが再現されない | 低 (15%) | 高 (論文に影響) | 否定結果も論文化価値あり。「ハイブリッドアテンションでは U 字が変形する」は新発見 | — |
| **`AutoConfig` にアテンションパターンフィールドが存在しない** | **中 (35%)** | **中** | **タスク1 で実機確認。存在しない場合はソースコード / 論文から手動マッピング** | **C-4** |
| **既存モデルのデータが異なるプロンプトで取得されている** | **中 (40%)** | **高** | **全モデル seed=42 の合成コードで再取得。既存データは参考値に格下げ** | **C-2** |

---

## §6. 成功基準

| レベル | 基準 | 前提条件 |
|:-------|:-----|:---------|
| **最小成功** | Phase 1-5 が正常完了し、Gemma 4 の忘却場プロファイルが得られる | C-1, C-3 の充足 |
| **標準成功** | G4-H1 (U 字不変性) が PCA 感度分析 (C-8) で安定的に支持される。Cross-model 比較グラフが同一プロンプト (C-2) で作成される | C-1〜C-5, C-8 の充足 |
| **完全成功** | G4-H1〜H4 が C-6 (多様体連続性検定) と C-9 (バイアス補正) を経て検証される。ハイブリッドアテンションの忘却場への影響が、SWA artifact か忘却構造かが判別された状態で定量化される | **C-1〜C-10 全ての充足** |

---

## §7. 関連ファイル

| ファイル | 用途 |
|:---------|:-----|
| `50_自律研究/p3_alpha_force/extract_hidden_states.py` | Phase 1 パイプライン |
| `50_自律研究/p3_alpha_force/compute_geometry.py` | Phase 2-5 パイプライン |
| `theta_b_external/measure_attention_cka_v2.py` | θ_b / CKA 測定 (参考) |
| `oblivion/verify_llm_blanket.py` | blanket 遷移速度検証 (理論ベース) |
| `linkage_hyphe.md` | Hyphē 理論定義 |

---

## §8. 発展的研究テーマ (Phase 2 以降)

1. **MoE 26B の忘却場**: Dense 31B と MoE 26B の比較 → expert routing の忘却への影響
2. **API↔重み接続**: Gemini 3.1 Pro (API 介入実験データ) と Gemma 4 (重みレベルデータ) の統一分析
3. **量子化の忘却場への影響**: BF16 vs 4bit 量子化で Φ(l) がどう歪むか
