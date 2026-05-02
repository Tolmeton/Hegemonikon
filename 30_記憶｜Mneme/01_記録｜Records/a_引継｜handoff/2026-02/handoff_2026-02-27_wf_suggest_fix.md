# Session Handoff: 2026-02-27 WF Suggestion & TM Grammar Fix

## 1. Context (Where we are)

Antigravity IDE の機能不全（`/` によるWFサジェストが1件も出ない）をデバッグし、解決したセッション。

## 2. Findings (What we learned)

- **根本原因**: `~/.gemini/antigravity/global_workflows/` のMarkdown内に含まれるコードブロックの言語指定（例: ` ```bash `）が、IDEの Language Server (Go) 内で TextMate (TM) Grammar を持たないことに起因し、パーサー全体をクラッシュさせていた。
- **影響の拡大**: IDE側の取得関数 (`fzr`) が `Promise.all` で全WFファイルを取得しているため、1ファイルのパースエラーが発生すると `Promise` 全体が reject され、サジェスト一覧が空配列になるという脆弱性だった。
- **解決策の確立**: コードブロックの言語指定を除去（` ```bash ` → ` ``` `）するだけでパースエラーを回避可能であると実証した。
- **再生成・同期手法**: `~/.gemini/antigravity/regenerate_global_workflows.sh` を作成。`nous/workflows/`（完全版）から、言語指定のみを除去した安全版を `global_workflows/`（IDEサジェスト用）へ自動生成する仕組みを構築した。

## 3. Operations (What we did)

- 二分探索テストによる原因ファイルおよび原因行の絞り込み。
- `regenerate_global_workflows.sh` の実装と全87ファイルの安全な復元。
- `/ccl-learn` による学びの言語化と抽出。

## 4. Next Actions (What to do next)

- [ ] 今後、Hegemonikón ワークフロー (`nous/workflows/`) を追加・変更した際は、必ず `~/.gemini/antigravity/regenerate_global_workflows.sh` を実行して `global_workflows` を同期すること。

---
*Created by: Antigravity AI (Claude) | Mode: Verification*
