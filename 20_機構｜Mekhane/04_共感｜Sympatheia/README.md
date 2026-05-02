# 04_共感｜Sympatheia

> **PURPOSE**: 自律神経系。脅威分析 (WBC)、定理推薦 (Attractor)、記憶圧縮 (Digest)、恒常性 (Feedback)、違反記録。

> **FEP 的位置づけ**: LLM の MB (Markov Blanket) は「薄い」— sensory/active states が
> トークン入出力の単一チャネルに限定されるため、恒常性 (homeostasis) が構造的に弱い。
> Sympatheia は **薄い MB に内受容チャネルを追加し、ホメオスタシスを人工的に厚くする設計操作**。
> → rom_2026-03-15_fep_body_thin_mb.md

## `_src/` 対応コード
- [`mekhane/sympatheia/`](../../_src｜ソースコード/mekhane/sympatheia/) — Sympatheia MCP サーバー

## 機能と MB 対応

| 機能 | 説明 | 生物学的対応 |
|:-----|:-----|:------------|
| `sympatheia_wbc` | 脅威分析スコアリング | 免疫系 (白血球) |
| `sympatheia_attractor` | 24定理から最適 WF 推薦 | 反射弓 (適切な行動パターン選択) |
| `sympatheia_digest` | 状態ファイル圧縮 | 記憶の固定化 (海馬→皮質) |
| `sympatheia_feedback` | 閾値動的調整 | アロスタシス (予測的恒常性調整) |
| `sympatheia_verify_on_edit` | 変更後テスト自動実行 | 体性感覚フィードバック |
| `sympatheia_basanos_scan` | L0 静的解析 | 内受容 (内臓感覚モニタリング) |
| `sympatheia_log_violation` / `sympatheia_violation_dashboard` | 違反管理 | 痛覚 (損傷検出 + 行動抑制) |
| `sympatheia_peira_health` | サービス健全性チェック | 自律神経系の恒常性監視 |

## MAP
- KI: `system_architecture` → horos_nomoi_system

---
*Created: 2026-03-13*
*Updated: 2026-03-15 — FEP 的位置づけ (薄い MB への内受容追加) + MB 対応テーブル追加*
