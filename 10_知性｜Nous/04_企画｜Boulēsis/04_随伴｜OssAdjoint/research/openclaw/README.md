# OpenClaw 深掘り調査

> **優先度**: S (最多 import candidates: 12件)
> **repo**: openclaw/openclaw
> **詳細分析**: [OPENCLAW_ANALYSIS.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/openclaw/OPENCLAW_ANALYSIS.md) (86KB, 17モジュール, ~11,200行ソース読了)

## import_candidates (adjoint_map.yaml L208-219)

| # | candidate | HGK 対象 | 優先度 | 判定 | 備考 |
|:--|:----------|:---------|:-------|:-----|:-----|
| T-03 | Tool Loop Detection (624行) | F6/F9 暴走防止 | 🔴 最重要 | **[Import]** | 4検知器カスケード (ping-pong, no-progress等) を完全移植 |
| T-01 | ~~Compaction~~ → **Hyphē Pipeline** | **F2 動的ナレッジ** | 🔴 最重要 | **[Leverage+Extend]** | OpenClaw の制御機構 (cap/3段fallback) を import し、Hyphē Dissolve⇒Recrystallize で実現。lossy 圧縮は不採用 |
| T-02 | Context Window Guard (75行) | F4 メーター・ガード | 🔴 最重要 | **[Import]** | cap パターンによる強制的コスト制御 |
| T-04 | Exec Approval (2,060行) | F4 N-4 承認フロー | 🟠 高 | **[Import]** | 7段バリデーション (Proposal First 実装) |
| T-05 | Skill System (761行) | F10 L1 Plugin 層 | 🟠 高 | **[Watch]** | 6段優先度と二分探索プロンプト制限 (設計参考) |
| T-06 | Hooks System (1,253行) | F10 E4 Plugin 層 | 🟠 高 | **[Watch]** | Void/Modifying 2モードと同期 Promise 検出ガード |
| T-08 | Model Fallback (1,700行) | F9 モデルルーティング | 🟡 中 | **[Watch]** | FailoverReason 分類体系とクールダウンチェック |
| T-09 | Memory MMR+Decay (2,400行) | F1 知識検索品質 | 🟠 高 | **[Import]** | BM25+Vector マージと Evergreen (BC免除) の時間減衰 |
| T-07 | Session Utils (2,053行) | F2 ノート管理 | 🟡 中 | **[Watch]** | canonicalKey 解決とアーカイブクリーンアップ |
| T-10 | Query Expansion (807行) | F1 FTS クエリ前処理 | 🟡 中 | **[Watch]** | FTS-only モードでの言語別ストップワード |
| T-11 | Skills UI (980行) | F10 Skills 管理画面 | 🟢 参考 | **[Skip]** | UI実装は設計パターンのみ参考 |
| T-12 | Sessions UI (450行) | F2 ノート・UI | 🟢 参考 | **[Skip]** | UI実装は設計パターンのみ参考 |

## 追加発見 (Phase A & C)

| # | candidate | HGK 対象 | 優先度 | 判定 | 備考 |
|:--|:----------|:---------|:-------|:-----|:-----|
| T-13 | System Prompt Builder (705行) | F1 プロンプト構成 | 🟠 高 | **[Import]** | セクション独立化 + PromptMode (full/minimal) |
| T-14 | Tool Policy Pipeline (109行) | F10 ツール許可制御 | 🟠 高 | **[Import]** | 7段フィルタと Plugin-only 保護 |
| T-15 | Session Write Lock (505行) | F6 並列書き込み保護 | 🟡 中 | **[Watch]** | stale検出付き再入可能ロック |
| T-16 | Cache Trace (257行) | F4 パイプライン診断 | 🟢 参考 | **[Skip]** | メッセージダイジェスト追跡 |
| T-17 | Tool Display (1,121行) | F4 実行コマンド視覚化 | 🟡 中 | **[Watch]** | コマンドラインの人間可読要約 (265行の巨人) |
| T-18 | Security Audit (1,021行) | F4 ヘルスチェック拡張 | 🟠 高 | **[Import]** | 構造化 Finding + Deepモードプローブ |
| T-19 | Skill Code Scanner (427行) | F10 Plugin 安全性 | 🟠 高 | **[Import]** | env-harvesting 検出等 (Basanos L0 拡張) |
| T-20 | Plugin System (1,529行) | F10 Plugin ロード | 🟡 中 | **[Watch]** | Discovery→Manifest→Loader の3層アーキテクチャ |

## 次のアクション

- [x] 各 T-xx の OPENCLAW_ANALYSIS.md 該当セクションを精読
- [x] Import / Skip / Watch を判定
- [ ] 🔴最重要の3タスク (T-01, T-02, T-03) の実装計画 (implementation_plan.md) を作成

---

*Created: 2026-02-28*
