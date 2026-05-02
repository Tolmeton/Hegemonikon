# Handoff: AY v3 Spectral — Polynomial AY の定量測定

**Date**: 2026-03-29
**Session ID**: ay-v3-spectral
**Duration**: ~2h
**V[session]**: 0.12 (収束途上 — 正規化 AY は正だが効果量が微弱)

---

## Situation

前セッション (euporia-hyphe-fusion) で設計書 DESIGN_compute_ay_v3.md を完成。
本セッションで Phase 1 (PoC) と Phase 2 (30 sessions) を実装・実行した。

## Background

- AY (Affordance Yield) = G∘F が行為可能性をどれだけ増やすかの定量指標
- Polynomial Functor 定義: AY = Σ_c (|Act_1(c)| - |Act_0(c)|)
- Hyphē の embedding データ (768d Gemini embedding) から直接計算する

## Assessment

### 成果 (3 commits)

| Commit | 内容 |
|:-------|:-----|
| `6fa9b0d4f` | **compute_ay_v3.py** — Phase 1 PoC。3指標 (Binary/Continuous/Spectral AY)。13 sessions |
| `b92314fea` | **DESIGN v2.0** — Phase 1 結果と Spectral AY 発見を記録 |
| `89c458ec0` | **compute_ay_v3_phase2.py** — Phase 2。30 sessions × 3τ × 真の gf_on/gf_off + 正規化 AY |

### 変更ファイル一覧

| ファイル | 変更種別 |
|:---------|:---------|
| `60_実験/06_Hyphē実験/HyphePoC/compute_ay_v3.py` | **新規** |
| `60_実験/06_Hyphē実験/HyphePoC/ay_v3_results.json` | **新規** |
| `60_実験/06_Hyphē実験/HyphePoC/compute_ay_v3_phase2.py` | **新規** |
| `60_実験/06_Hyphē実験/HyphePoC/ay_v3_phase2_results.json` | **新規** |
| `60_実験/06_Hyphē実験/HyphePoC/DESIGN_compute_ay_v3.md` | 編集 (v2.0) |

### 実験結果の連鎖

```
Phase 1 — Binary AY = 0 (天井効果: sim 0.86-0.98 で二値化不能)
  ↓ Creator insight: 「良貨と悪貨がある」
Phase 1 — Spectral AY = +0.072, 10/12 sessions positive (83%)
  ↓ effective_rank(sim_after) - effective_rank(sim_before) で良貨/悪貨を分離
Phase 2 — Raw Spectral AY = 全セッション負 (チャンク数差が支配)
  ↓ gf_off はチャンク数が多い (境界検出あり+G∘F反復なし) → eff_rank が高い
Phase 2 — Normalized AY (eff_rank/N) = 全τで mean > 0
  ↓ チャンクあたりの情報効率で比較
```

### Phase 2 最終結果

| τ | AY_norm | positive | chunks_off | chunks_on |
|:--|:--------|:---------|:-----------|:----------|
| 0.70 | +0.004 | 11/30 (37%) | 8.3 | 6.9 |
| 0.75 | +0.002 | 16/30 (53%) | 21.0 | 15.6 |
| 0.80 | +0.002 | 22/30 (73%) | 49.4 | 34.0 |

### 決定事項

| # | 決定 | 理由 | 棄却肢 |
|:--|:-----|:-----|:-------|
| D6 | Primary metric = Spectral AY (effective rank) | 天井効果を回避しつつ良貨/悪貨を分離 | Binary AY, Continuous AY |
| D7 | 良貨/悪貨フレーム | G∘F は到達の「数」ではなく「有効次元」を増やす | AY 符号反転 |
| D8 | 正規化 AY (eff_rank/N) が Phase 2 の正しい指標 | チャンク数差が raw eff_rank を支配する | Raw eff_rank |

### 未解決・不確実性

| # | 項目 | 検証方法 |
|:--|:-----|:---------|
| C4 | 正規化 AY の効果量が微弱 (+0.002~0.004) | ker(G) 突破 (AY-1) で増幅されるか検証 |
| C5 | τ-invariance FAIL (range/mean = 1.03) | τ 依存性は正規化指標で再検定すべき |
| C6 | 統計的有意性未検定 | Wilcoxon signed-rank test or permutation test |

## Recommendation — Next Actions

1. **AY-1 着手** (ker(G) 突破):
   - `task_type=CLASSIFICATION` 実験 (Gemini embedding API 1行変更)
   - ker(G) = {Scale, Valence} が縮小 → 正規化 AY の効果量が増幅するか
   - 参照: `TASKS_euporia_hyphe_fusion.md` の AY-1 セクション

2. **統計検定**:
   - 正規化 AY の Wilcoxon signed-rank test (paired: 各 session の gf_on vs gf_off)
   - Bootstrap confidence interval for mean AY_norm

3. **設計書 v3.0 更新**:
   - Phase 2 結果 (正規化 AY + チャンク数差の交絡因子) を §10 に追記
   - D8 (正規化 AY) を §5 に追加

---

## 信念 (Doxa)

- G∘F は「チャンクあたりの情報効率」を向上させる — 量ではなく質の操作
- 効果量が微弱なのは ker(G) = {Scale, Valence} のせいと推測 — embedding の等方性が信号を潰している
- 良貨/悪貨フレームは Euporia 理論の重要な精密化 — AY > 0 は「接続の数」ではなく「接続空間の有効次元」で測るべき
- Phase 1 の「成功」は等間隔近似のアーティファクトだった — Phase 2 で誠実に修正できた

## Nomoi フィードバック

- 違反なし

## Session Metrics

| 項目 | 値 |
|:-----|:---|
| WF/Skill 使用 | /u+ ×1, /kop ×1 |
| Commits | 3 |
| 新規ファイル | 4 (2 scripts + 2 results) |
| 編集ファイル | 1 (DESIGN v2.0) |
| 行数 | ~650 (scripts) + ~6000 (JSON results) |

---

*R(S) generated: 2026-03-29 | Stranger Test: PASS*
