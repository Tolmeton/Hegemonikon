# Handoff: Euporia × Hyphē 融合 — 連携明示 + AY 設計

**Date**: 2026-03-29
**Session ID**: euporia-hyphe-fusion
**Duration**: ~2h
**V[session]**: 0.15 (十分に収束)

---

## Situation

Euporia (07_行為可能性) は Linkage ドメインの理論で Hyphē を参照していたが、
実装・実験リソースへの明示的リンクが乏しく、130+ 実験の知見が未統合だった。

## Background

- Euporia: AY > 0 原理。3ドメイン (Cognition/Description/Linkage) + Hóros (横断)
- Hyphē: Linkage ドメインの実装。Phantasia エンジン + HyphePoC 実験 (858 similarity 点)
- 両者は「Linkage = Hyphē (η: 外部状態)」として理論的に結合済みだったが、
  ファイル間のリンクと実験データの統合がなかった

## Assessment

### 成果 (3 commits)

| Commit | 内容 |
|:-------|:-----|
| `f1981e246` | **Euporia ⇔ Hyphē 連携明示** (4ファイル +100/-9行): README MAP にHyphēセクション, euporia.md §7.5 に実験知見テーブル, blindspots にker(G)進捗, B_polynomial に§6 Hyphē対応 |
| `1170df038` | **AY 3件タスク定義** (TASKS_euporia_hyphe_fusion.md): AY-1 ker(G)突破, AY-2 Coherence Invariance転用, AY-3 AY定量測定 |
| `eb323e4c7` | **compute_ay_v3 設計書** (DESIGN_compute_ay_v3.md): Polynomial AY の定量測定。5設計判断+3実装課題+4Phase計画 |

### 変更ファイル一覧

| ファイル | 変更種別 |
|:---------|:---------|
| `10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/README.md` | 編集 (MAP拡充, 確定事項+3, Session 2, 日付更新) |
| `10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/euporia.md` | 編集 (v0.8.0, §7.5 Hyphē統合, Polynomial↔Hyphē, §8参照) |
| `10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/euporia_blindspots.md` | 編集 (C1'.2, 射の不在Hyphē進捗, ker(G)情報) |
| `10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/B_polynomial_linkage.md` | 編集 (§6 Hyphē対応, v0.4) |
| `10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia/TASKS_euporia_hyphe_fusion.md` | **新規** (AY 3件タスク定義) |
| `60_実験｜Peira/06_Hyphē実験｜HyphePoC/DESIGN_compute_ay_v3.md` | **新規** (compute_ay_v3 設計書) |

### 決定事項

| # | 決定 | 理由 | 棄却肢 |
|:--|:-----|:-----|:-------|
| D1 | Act(c) = inter-chunk cosine sim > τ_link | Hyphē は embedding ベース。到達可能性 = 意味空間の近さ | テキスト内明示的参照カウント (データなし), k-NN (k が恣意的) |
| D2 | Before/After = gf_off / gf_on | G∘F が index_op そのもの | τ間比較 (粒度差であって index_op の差ではない) |
| D3 | τ_link sweep [0.50..0.80] | AY の τ_link 依存性自体が知見 | 単一 τ_link (感度分析不能) |
| D4 | Centroid = mean embedding, L2正規化 | precision が ker(G) で壊れているため重み付け不適 | precision-weighted mean |
| D5 | 既存 embedding_cache.npz 再利用 | 858点キャッシュ済み。再計算コスト=0 | API再呼出 |

### 未解決・不確実性

| # | 項目 | 検証方法 |
|:--|:-----|:---------|
| C1 | embedding_cache.npz の session_id → step 対応 | `run_chunker.py` のキャッシュ保存ロジックを読む |
| C2 | gf_off 条件での step_range 有無 | `gf_verification_100_results.json` の構造を精査 |
| C3 | 30 sessions の embedding は embedding_cache_100.pkl にある | まず 13 sessions でPoC → 30 sessions に拡張 |

## Recommendation — Next Actions

1. **AY-3 Phase 1 実装** (`compute_ay_v3.py`):
   - `embedding_cache.npz` のキー構造確認 (`run_chunker.py` L38-39 周辺)
   - 13 sessions × τ=0.7 × τ_link sweep で AY 計算
   - 設計書: `60_実験/06_Hyphē実験/DESIGN_compute_ay_v3.md`
   - 参照: `TASKS_euporia_hyphe_fusion.md` の AY-3 セクション

2. **AY-3 Phase 2** (Phase 1 成功後):
   - `gf_verification_100_results.json` + `embedding_cache_100.pkl` で gf_on vs gf_off のAY差分計算
   - 成功基準: mean_AY > 0 (gf_on > gf_off) for majority of sessions

3. **AY-1 着手** (AY-3 完了後):
   - `task_type=CLASSIFICATION` 実験 (Gemini embedding API 1行変更)
   - ker(G) = {Scale, Valence} が縮小するかを AY-3 の基盤で測定

---

## 🧠 信念 (Doxa)

- Euporia と Hyphē の融合は「地図を描いた」段階。3本の道 (AY) が見えている
- compute_ay_v3 で AY が数値になれば、HGK は「認知操作の価値」を測定できる最初のフレームワークになる
- ker(G) = {Scale, Valence} の突破は embedding 選択の問題であり、理論は健全

## ⚡ Nomoi フィードバック

- 違反なし

## Session Metrics

| 項目 | 値 |
|:-----|:---|
| WF/Skill 使用 | /his ×1 (回顧) |
| Commits | 3 (連携明示 + タスク定義 + 設計書) |
| 新規ファイル | 2 (TASKS, DESIGN) |
| 編集ファイル | 4 (README, euporia.md, blindspots, B_polynomial) |
| 行数 | +461 / -9 |

---

*R(S) generated: 2026-03-29 | Stranger Test: PASS*
