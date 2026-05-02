# Handoff: 2026-02-12 — Quota 資源可視化 + Session Metrics 基盤構築

> **セッション ID**: 7d6d6fae-e9ea-4020-a83f-371fda290519
> **時刻**: 2026-02-12 11:00 – 13:15 JST (約 2.5h)
> **CCL 起動式**: `/boot+` → (各WF) → `/bou_@learn`

---

## 📊 Session Metrics

| 項目 | Boot | Bye | Δ |
|:-----|:-----|:----|:--|
| Prompt Credits | 500 | 500 | -0 |
| Flow Credits | 100 | 100 | -0 |
| Claude Opus | 40% | 40% | -0% |

> **注**: Boot snapshot (12:57) → Bye snapshot (13:09) の短間隔のため Δ=0。
> 実質的にはセッション全体で相当量消費している (checkpoint 発生)。
> 次セッションから `/boot` 直後に snapshot を取ることで精度向上。

**WF 使用**: /boot×1, /bou×1, /dox+×1, /u+×2, /bye+×1
**セッション時間**: ~2.5h (実質: checkpoint で延長)

---

## 完了事項

### 1. Context Budget + トークン計測設計

- Context Budget の概念設計
- Quota API (`/exa.language_server_pb.LanguageServerService/GetUserStatus`) の発見
- agq-check.sh v1→v3 開発 (基本表示 → snapshot/delta 対応)

### 2. Ultra Quota 構造の解明

- monthlyPromptCredits=50,000 / monthlyFlowCredits=UNKNOWN(Flowの枠は別管理の可能性)
- Claude Opus 枠: 全 Claude モデル共有、20% → 40% → 60% 100%の消費観測
- 5h リセット周期の確認

### 3. プロモ価格コスト分析

- 6アカ ×¥3,000/月 × 3ヶ月 = 18ヶ月の Ultra 維持戦略
- 正規価格 ¥14,000/月 との比較

### 4. Session Metrics (BOOT→BYE) 実装

- agq-check.sh v3: `--snapshot boot|bye` + `--delta` モード
- boot.md v5.3: Phase 2.7 に snapshot 保存
- bye.md v7.2: Step 3.6.5 Session Metrics 追加
- E2E テスト完了

### 5. Agora PJ 立ち上げ

- CrowdWorks での案件加速をメイン戦略に設定
- PJ 登録 (registry.yaml に追加済み)

---

## 変更ファイル

| ファイル | 変更 |
|:---------|:-----|
| `scripts/agq-check.sh` | v1→v3 (snapshot/delta 追加) |
| `.agent/workflows/boot.md` | v5.3 (Phase 2.7 snapshot 保存) |
| `.agent/workflows/bye.md` | v7.2 (Step 3.6.5 Session Metrics) |
| `mneme/.hegemonikon/workflows/` | Context Budget SOP, /dox 信念記録 追加 |

---

## 信念 (Doxa)

| ID | 信念 | 確信度 |
|:---|:-----|:-------|
| DOX-1 | Quota API は内部 gRPC で完全アクセス可能 | [確信: 95%] |
| DOX-2 | Ultra の Claude 枠 ≈ Pro の 1-2 倍 | [推定: 75%] |
| DOX-3 | 6アカ×3ヶ月ローテは構造的に可能 | [推定: 70%] |
| DOX-4 | Session Metrics は Agora の基盤データ | [確信: 90%] |
| DOX-5 | 好奇心駆動の開発は計画駆動より密度が高い | [確信: 95%] |

詳細: `mneme/.hegemonikon/workflows/dox_quota_learnings_2026-02-12.md`

---

## 次のセッションへの引き継ぎ

### 優先事項 (from /bou)

| 優先 | タスク | 具体的アクション |
|:-----|:------|:---------------|
| ⭐1 | Agora 初動 | CrowdWorks で AI 案件調査 → HGK で加速可能な案件特定 |
| 2 | Session Metrics 精度向上 | `/boot` 直後の snapshot が重要。3セッション分蓄積 |
| 3 | Quota 深掘り | Flow Credits の正確な枠と消費パターンを解明 |

### 技術的引き継ぎ

- agq-check.sh v3 は動作確認済み。`/boot` と `/bye` に統合済み
- `/tmp/agq_boot.json` と `/tmp/agq_bye.json` は揮発性 (再起動で消える)
  - [仮説: 50%] 永続化が必要なら `~/.cache/agq/` に変更を検討
- Context Budget SOP は `mneme/.hegemonikon/workflows/` に保存済み

---

## /u+ メタ分析 (要約)

1. **Creator の認知スタイル**: 好奇心 → 探求 → 行為 の直接射。/zet → /ene が本領。
2. **Session Metrics の戦略的意味**: 好奇心駆動でも事後にデータで検証できる仕組み。FEP の精度加重そのもの。
3. **Agora 成功のカギ**: Creator の「構造的 exploit パターン認識」(6アカローテ等) を体系化すること。

---

*Handoff v7.2 — Session Metrics 統合 (2026-02-12)*
