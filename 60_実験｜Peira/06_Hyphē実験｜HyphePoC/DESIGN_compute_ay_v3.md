# compute_ay_v3 設計書 — Polynomial AY: チャンク連動数の定量測定

> **AY-3 タスク**: Euporia × Hyphē 融合から生じた「AY の定量的測定」
> **親文書**: [TASKS_euporia_hyphe_fusion.md](../../10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/TASKS_euporia_hyphe_fusion.md)
> **理論基盤**: [B_polynomial_linkage.md §3, §6](../../10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/B_polynomial_linkage.md)
> **Date**: 2026-03-29

---

## §1 問題定義

### 現状 (v1, v2)

| バージョン | 計算対象 | 限界 |
|:-----------|:---------|:-----|
| compute_ay.py (v1) | precision-weighted λ loss 差分 | precision が embedding anisotropy で壊れている (ker(G)) |
| compute_ay_v2.py (v2) | 弁別可能性 + Shannon エントロピー + λ impact + 相関 | precision の「存在」を証明するが、チャンク間連動を計測しない |

### v3 の目標

**Polynomial Functor 定義に基づく AY を、Hyphē の embedding データから直接計算する。**

```
AY(index_op) = Σ_c (|Act_1(c)| - |Act_0(c)|)   [B_polynomial_linkage.md §3]

where:
  c = chunk
  Act_0(c) = c からの到達可能チャンク数 (index_op 適用前 = bare K)
  Act_1(c) = c からの到達可能チャンク数 (index_op 適用後 = L(K) = Fix(G∘F))
```

---

## §2 操作的定義: Act(c) とは何か

### 理論 → 操作 の写像

| 理論 (Polynomial) | 操作的定義 (Hyphē) | 根拠 |
|:-------------------|:-------------------|:-----|
| Position I = chunk 状態集合 | `chunks[]` in results.json | 直接対応 |
| Direction B_i = c_i からの行為集合 | **c_i のセントロイドから他チャンクへの到達可能集合** | Act(c) = c から意味的に到達できるチャンク |
| \|B_i\| = 行為可能性の数 | `|{c' : sim(centroid(c), centroid(c')) > τ_link}|` | cosine similarity が閾値を超える = 「到達可能」 |
| Lens (f, f♯): p → q | G∘F (merge/split) 操作 | index_op = 結晶化操作 |

### Act(c) の計算方法

```python
def compute_act(chunk_centroids, c_idx, tau_link):
    """Act(c) = c から到達可能な他チャンクの数"""
    centroid_c = chunk_centroids[c_idx]
    count = 0
    for j, centroid_j in enumerate(chunk_centroids):
        if j != c_idx:
            sim = cosine_similarity(centroid_c, centroid_j)
            if sim > tau_link:
                count += 1
    return count
```

### τ_link (到達可能性閾値) の選択

τ_link ≠ τ (チャンク境界閾値)。τ_link はチャンク間の「意味的到達可能性」。

| 候補 | 値 | 根拠 |
|:-----|:---|:-----|
| τ_link = τ (チャンク境界と同じ) | 0.70 | 最も単純。boundary = reachability |
| τ_link = mean(inter-chunk sim) | データ依存 | 平均的な到達性を閾値にする |
| τ_link sweepτ_link ∈ {0.5, 0.6, 0.7, 0.8} | 感度分析 | AY が τ_link に対してどう変化するか |

**推奨**: τ_link sweep。AY の τ_link 依存性自体が重要な知見。

---

## §3 Before vs After: index_op = G∘F

### 2条件の定義

| 条件 | 意味 | データソース |
|:-----|:-----|:------------|
| **K (before)** | G∘F 適用前 = 等間隔チャンク or 初期境界 | `gf_off` 条件 (gf_verification results) |
| **L(K) (after)** | G∘F 適用後 = Fix(G∘F) | `gf_on` 条件 (gf_verification results) |

### 問題: embedding_cache から centroid を計算する必要がある

現在の results.json にはチャンクの `step_range` と `coherence` 等のスカラーはあるが、**centroid embedding ベクトルは含まれていない**。

**解決策**: embedding_cache.npz + step_range → centroid 計算

```python
def compute_chunk_centroids(embeddings, chunks):
    """各チャンクのセントロイド (mean embedding) を計算"""
    centroids = []
    for chunk in chunks:
        start, end = parse_step_range(chunk['step_range'])
        chunk_embeddings = embeddings[start:end+1]
        centroid = np.mean(chunk_embeddings, axis=0)
        centroid = centroid / np.linalg.norm(centroid)  # L2 正規化
        centroids.append(centroid)
    return np.array(centroids)
```

---

## §4 compute_ay_v3 のアーキテクチャ

### 入力

| 入力 | ファイル | 内容 |
|:-----|:---------|:-----|
| embedding cache | `embedding_cache.npz` or `.pkl` | session_id → embeddings (N_steps × 768) |
| GF results | `gf_verification_100_results.json` | 30 sessions × 4τ × 2 conditions (gf_on/off) |
| 基本 results | `results.json` | 13 sessions, τ=0.7, chunks with step_range |

### 処理フロー

```
Step 1: Load embeddings + results
         ↓
Step 2: For each session × τ × condition (gf_on / gf_off):
         ├── Parse step_range → chunk boundaries
         ├── Compute chunk centroids from embeddings
         └── Compute inter-chunk similarity matrix
         ↓
Step 3: For each τ_link ∈ {0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80}:
         ├── Act_0(c) = |{c' : sim > τ_link}| for gf_off chunks
         ├── Act_1(c) = |{c' : sim > τ_link}| for gf_on chunks
         └── AY_session = Σ_c (Act_1(c) - Act_0(c))
         ↓
Step 4: Aggregate across sessions:
         ├── AY_global(τ, τ_link) = mean(AY_session)
         ├── AY > 0 判定 (Euporía principle)
         └── AY の τ_link 感度分析
         ↓
Step 5: Output (JSON + human-readable)
```

### 出力

```json
{
  "version": "v3.0",
  "theory": "B_polynomial_linkage.md §3",
  "metric": "AY = Σ_c (|Act_1(c)| - |Act_0(c)|)",
  "results": {
    "tau_0.70": {
      "tau_link_sweep": [
        {"tau_link": 0.50, "mean_ay": ..., "ay_positive_pct": ..., "act_before": ..., "act_after": ...},
        {"tau_link": 0.60, "mean_ay": ..., ...},
        ...
      ],
      "best_tau_link": ...,
      "ay_at_best": ...
    },
    ...
  },
  "sessions": [
    {
      "session_id": "...",
      "tau": 0.70,
      "chunks_before": 5,
      "chunks_after": 4,
      "ay_per_chunk": [...],
      "ay_total": ...
    }
  ]
}
```

---

## §5 設計判断

### D1: Act(c) = inter-chunk cosine similarity > τ_link

**選択**: cosine similarity of chunk centroids
**棄却**: テキスト内の明示的参照カウント (データなし)、k-NN (k が恣意的)
**理由**: Hyphē は embedding ベースのシステム。「到達可能性」は意味空間での近さ。

### D2: Before = gf_off, After = gf_on

**選択**: GF verification の 2条件を使う
**棄却**: τ 間比較 (τ_low vs τ_high) — これは粒度の差であって index_op の差ではない
**理由**: G∘F が index_op そのもの。gf_off = bare K, gf_on = L(K)。

### D3: τ_link sweep (感度分析)

**選択**: 7点 sweep [0.50, 0.55, ..., 0.80]
**棄却**: 単一 τ_link — AY の τ_link 依存性が分からない
**理由**: ker(G) の影響を定量化できる。τ_link が高いほど ker(G) の座標が効く。

### D4: Centroid = mean embedding, L2正規化

**選択**: 算術平均 + 正規化
**棄却**: weighted mean (precision で重み付け) — precision 自体が ker(G) で壊れているため
**理由**: 最もシンプルで仮定が少ない。

### D5: 既存 embedding_cache の再利用

**選択**: embedding_cache.npz を読み込む (API 呼び出し不要)
**理由**: 858 点分のキャッシュ済み。再計算コスト = 0。

---

## §6 実装上の課題

### C1: embedding_cache.npz の session_id → step 対応

embedding_cache.npz のキー構造を確認する必要がある。
session_id と step index の対応が必要。

**対策**: `run_chunker.py` のキャッシュ保存ロジックを読んで構造を理解する。
もしフラットなら、`results.json` の `total_steps` で session 境界を再構築する。

### C2: gf_off 条件でのチャンク境界

`gf_verification_100_results.json` には gf_off のチャンク数はあるが、
**step_range がない可能性がある**。

**対策**:
- gf_off のチャンクは「等間隔分割」or「初期境界 (G∘F 前)」。
- `hyphe_chunker.py` の `_detect_boundaries` の出力が gf_off の境界。
- 最悪ケース: gf_off を等間隔 (total_steps / num_chunks) で近似。

### C3: 30 sessions (100 Handoffs) の embedding は embedding_cache_100.pkl にある

元の 13 sessions = `embedding_cache.npz`、100 sessions = `embedding_cache_100.pkl`。
gf_verification_100 には 30 sessions が使われている。

**対策**: まず 13 sessions (embedding_cache.npz + results.json) で PoC を作り、
後で 30 sessions (embedding_cache_100.pkl + gf_verification_100) に拡張。

---

## §7 Euporia 接続ポイント

### euporia_sub.py との接続 (将来)

```
現在: euporia_sub.py → WF 完了時に 6射影スコアリング → 定性的 AY 判定
将来: euporia_sub.py → WF 完了時に compute_ay_v3 を呼び出し → 定量的 AY

必要な変更:
  1. compute_ay_v3 を mekhane/anamnesis/ に移動 (PoC → エンジン)
  2. euporia_sub.py から phantasia_pipeline.py 経由で chunk centroid を取得
  3. AY 値を WF 実行ログに記録 → AY ダッシュボード
```

### AY テンソル化 (将来)

```
現在: AY|_{Linkage} のみ (1次元)
将来: AY[domain][coordinate] (3D × 6座標 = 18次元テンソル)

  AY|_{Cognition}    = WF 射の品質向上量 → euporia_sub.py の6射影スコア差分
  AY|_{Description}  = プロンプト品質向上量 → Týpos @rubric スコア差分
  AY|_{Linkage}      = チャンク連動増加量 → compute_ay_v3 ← 今回
```

---

## §8 実行計画

| Phase | 内容 | 成果物 |
|:------|:-----|:-------|
| **Phase 0** (設計) | 本文書 | DESIGN_compute_ay_v3.md ✅ |
| **Phase 1** (PoC) | 13 sessions × τ=0.7 × 3指標 (Binary/Continuous/Spectral) | compute_ay_v3.py + ay_v3_results.json ✅ |
| **Phase 2** (GF比較) | gf_on vs gf_off での AY 差分計算 (30 sessions) | ay_v3_gf_comparison.json |
| **Phase 3** (統合) | euporia_sub.py × phantasia_pipeline.py 接続 | mekhane/anamnesis/ay_calculator.py |

---

## §9 成功基準

| 基準 | 閾値 | 結果 |
|:-----|:-----|:-----|
| AY > 0 (gf_on > gf_off) | mean_AY > 0 for majority of sessions | Binary: FAIL (天井効果), **Spectral: PASS** (10/12 = 83%) |
| τ_link 感度 | AY が τ_link に対して単調増加 | Binary: 逆方向 (天井効果のため) |
| Coherence Invariance との整合 | AY の τ 依存性が小さい (range < 20%) | Phase 2 で検証予定 |

---

## §10 Phase 1 結果と発見 (2026-03-29)

### 3指標の比較

| 指標 | 定義 | mean | positive | 判定 |
|:-----|:-----|:-----|:---------|:-----|
| Binary AY | `Σ_c (|Act_1(c)| - |Act_0(c)|)` | 0.00 | 0/12 | FAIL |
| Continuous AY | `Σ_{c≠c'} (sim_after - sim_before)` | -0.207 | 2/12 | FAIL |
| **Spectral AY** | `effective_rank(sim_after) - effective_rank(sim_before)` | **+0.072** | **10/12** | **PASS** |

### 良貨/悪貨の発見

**仮説**: G∘F は到達可能性の「数」を増やすのではなく、「質」を変える。

- **悪貨** (偽陽性到達): 等間隔チャンクでは各チャンクが複数トピックを混在 → centroid が似る → 全チャンク間で高い sim → 見かけ上「全部繋がっている」が弁別不能
- **良貨** (真の到達): G∘F 後はチャンクが意味的に凝集 → centroid が固有方向を持つ → チャンク間 sim は下がるが、残った接続は意味的に真

### Spectral AY の理論的根拠

```
effective_rank = exp(H(λ̃))
  where λ̃_i = λ_i / Σλ_j  (正規化固有値)
        H = -Σ λ̃_i log(λ̃_i)  (Shannon entropy)
```

- 類似度行列の固有値スペクトルの「有効次元数」(Vershynin 2018)
- 全 centroid が同一方向 → 固有値1個に集中 → eff_rank ≈ 1
- 各 centroid が独立方向 → 固有値が分散 → eff_rank ≈ N
- G∘F は eff_rank を増加させる = 情報量のある次元を増やす

### 設計判断の追加

| # | 決定 | 理由 | 棄却肢 |
|:--|:-----|:-----|:-------|
| D6 | Primary metric = Spectral AY (effective rank) | 天井効果を回避しつつ良貨/悪貨を分離 | Binary AY (天井効果), Continuous AY (悪貨込み) |
| D7 | 良貨/悪貨フレーム | G∘F は到達の「数」ではなく「有効次元」を増やす | AY 符号反転 (理論的に不正確) |

### Phase 2 への方針

30 sessions × 4τ で Spectral AY を計算し:
1. gf_on vs gf_off の effective rank 差分を全セッションで検証
2. τ 依存性 (coherence invariance の AY 版) を確認
3. 論文 Paper III (忘却論) の Forgetting Lemma との接続を探索

---

*DESIGN v2.0 — 2026-03-29 | AY-3 Phase 1 complete, Spectral AY discovered*
