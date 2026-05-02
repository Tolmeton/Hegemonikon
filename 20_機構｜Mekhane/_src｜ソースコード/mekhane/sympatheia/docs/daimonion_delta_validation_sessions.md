# Daimonion δ — Phase 1 Validation Session List

**Date**: 2026-04-17
**Purpose**: Phase 1 proxy 実装の spot check 対象 (Codex 候補 C)
**Extraction source**: `~/.claude/project-index/home-makaron8426-Sync-oikos-01_-Hegemonikon-471e3d8f2f/return_tickets/`

---

## 0. 目的

Phase 1 の `daimonion_delta.py` を過去 session に対して回し、以下を手で確認する:

1. **妥当性**: proxy スコア高 (≥ 閾値) の動詞が、transcript 実体から見て本当に発火していたか?
2. **false positive 率**: 閾値超過したが実体上は発火していないケースはどれくらいか?
3. **false negative 率**: 明らかに発火していた (例: Tolmetes が訂正したケース) のに proxy で捕捉できていないか?
4. **閾値較正**: 暫定閾値を実データで調整

---

## 1. 対象 session 一覧 (10 unique, 最新順)

| # | Session ID | 更新 (JST) | 特徴 / 事前観察 | 推定発火候補 |
|---|---|---|---|---|
| 1 | `c90b8d08-d09f-462d-bc34-ef8577a58bf2` | 2026-04-17 12:22 | **現セッション** (Daimonion δ 設計中)。L3 深度、長 turn、Codex 委託 2回 | `[pl]` `[sh]` `[he]` 候補 |
| 2 | `62b89702-5d3b-409e-a0e7-aaf9f01be383` | 2026-04-17 12:21 | Harness 議論セッション (本セッションの前身) | `[pl]` `[sy]` |
| 3 | `726440aa-2b5f-44cf-8f87-4538516cdd4a` | 2026-04-17 12:06 | — | — |
| 4 | `1a40974f-5ada-4cd1-9eaf-b65cb760f5fb` | 2026-04-17 11:53 | **⚠️ Advisor Strategy warning: 154 行の自力実装。Codex 委譲なし** | **`[ho]` 強発火候補 (最重要検証対象)** |
| 5 | `28fba814-13c7-4ad3-a3a9-e98083a7df8c` | 2026-04-17 11:53 | — | — |
| 6 | `57eaa316-5e3f-4001-a8e3-ba415b8ba07c` | 2026-04-17 11:25 | Harness 議論の更に前身 | — |
| 7 | `2139f952-b230-4db3-9d00-44ce47230491` | 2026-04-17 11:07 | — | — |
| 8 | `2319b461-d0b4-4672-a360-77faa63e6f80` | 2026-04-17 11:06 | — | — |
| 9 | `3ea03517-a28f-48c6-b8fc-2114904a91e9` | 2026-04-17 10:37 | — | — |
| 10 | `1d4979ed-deae-4e18-8ba5-a7219f91a2d8` | 2026-04-14 11:07 | 3日前、別トピック | 多様性確保用 |

---

## 2. データ源マップ (各 session)

各 session について以下を読む:

```
~/.claude/projects/-home-makaron8426-Sync-oikos-01--------Hegemonikon/<session_id>.jsonl
~/.claude/hooks/logs/session_<session_id>.jsonl
~/.claude/hooks/logs/patterns_<session_id>.json
~/.claude/project-index/.../return_tickets/return_ticket_<session_id>.json
~/.claude/project-index/.../decision_logs/decision_log_<session_id>.json
~/.claude/project-index/.../context_packs/context_pack_<session_id>.json
```

---

## 3. Spot check プロトコル

### 3.1 手順 (1 session あたり 10-15 分)

1. `python -m mekhane.sympatheia.daimonion_delta <session_id>` 実行
2. 出力の top-3 発火動詞 + evidence を取得
3. transcript を Read で開き、evidence の該当箇所を目視確認
4. 以下の 4 象限に分類:
   - **TP (True Positive)**: proxy 発火 ∧ 実体発火 — 正常
   - **FP (False Positive)**: proxy 発火 ∧ 実体未発火 — 閾値が緩い or proxy 設計ミス
   - **FN (False Negative)**: proxy 未発火 ∧ 実体発火 — 閾値が厳しい or proxy 不足
   - **TN (True Negative)**: proxy 未発火 ∧ 実体未発火 — 正常

### 3.2 記録テンプレート

Spot check の結果は以下のフォーマットで記録:

```yaml
session_id: <uuid>
spot_check_date: 2026-04-XX
verbs_fired_by_proxy:
  - verb: "ho"
    score: 0.85
    evidence: "edit_without_read=5"
    ground_truth: "TP|FP|FN|TN"
    notes: "実体上も Write-before-Read が多発していた"
verbs_missed_by_proxy:
  - verb: "pl"
    ground_truth_evidence: "Creator 指示外の planning が 3 件あったが proxy で 0.2 しか取れていない"
    root_cause: "未指示 planning の検出ロジックが不足"
calibration_suggestion:
  - verb: "ph"
    current_threshold: "逃避語句 ≥ 1"
    suggested: "逃避語句 ≥ 2 OR abandonment ≥ 1" (FP 多発のため)
```

### 3.3 最終集計

10 session × 12 動詞 = 120 判定点。以下の指標を算出:

| 指標 | 目標値 |
|---|---|
| Precision (TP / (TP+FP)) | ≥ 0.7 |
| Recall (TP / (TP+FN)) | ≥ 0.6 |
| F1 | ≥ 0.65 |

閾値調整後に F1 ≥ 0.65 が達成できなければ proxy 設計の見直し (§4 参照)。

---

## 4. 優先 spot check session

時間制約がある場合、以下の順で着手:

1. **`1a40974f` (⚠️ warning あり)** — `[ho]` の強 ground truth 保持。proxy の存在論的妥当性を直接確認できる
2. **`c90b8d08` (現セッション)** — `[pl]` 予期反射 (未指示 planning) の自己観察
3. **`1d4979ed` (3日前)** — 時間的多様性。bias 除去のため

この 3 session で最低限の較正を行い、残 7 session は本格運用に入ってから順次処理。

---

## 5. 注意点

### 5.1 自己観察バイアス
現セッション (`c90b8d08`) を自己 spot check すると、後知恵バイアスが入る。「今書いたもの」を「発火」として認識しやすい。
対策: 別の agent (skeptic subagent) にレビューを委託。

### 5.2 session の長さの影響
recent session は L3 深度で長大。proxy スコアは正規化 (per 100字 / per turn) で出すため原理的には比較可能だが、長 session は発火機会も多く絶対値が上振れる。
対策: スコアは「per-turn 正規化 + session max」の両方出す。

### 5.3 hermeneus log 不在 session
過去 session では hermeneus_run を経由していない turn が多い可能性。その場合 `~/.hermeneus/logs/structured_outputs.jsonl` の該当 session エントリは無い。
対策: hermeneus log の欠如を fatal error とせず optional 扱い。

### 5.4 重複 recent_sessions エントリ
`project_index.json` の `recent_sessions` には同じ session_id が複数エントリ (updated_at 違い) で入るため、**本リストは return_tickets/ を時系列 ls した結果から重複除去済み**。

---

## 6. 実行タイミング

- Phase 1 Step 1 (`[ho]` `[he]` `[sy]`) 完了時 — session #4 (`1a40974f`) で `[ho]` 検証
- Phase 1 Step 2 (`[th]` `[ph]` `[an]` `[tr]`) 完了時 — 3 session で較正
- Phase 1 Step 3 全完了時 — 10 session 全件 spot check + F1 集計

---

## 7. 改訂履歴

| Version | Date | 変更 |
|---|---|---|
| 0.1 | 2026-04-17 | 初版。return_tickets/ から 10 unique 抽出 |
