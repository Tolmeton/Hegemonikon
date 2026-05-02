# 01_記録｜Records

> **PURPOSE**: セッション記録の全保管庫。Handoff, セッション対話, ROM, 成果物, レビュー, ログ, 実行痕跡。

## サブディレクトリ (8)

| ディレクトリ | 内容 |
|:-----------|:-----|
| `a_引継｜handoff/` | セッション引継ぎ (/bye で生成) |
| `b_対話｜sessions/` | セッション対話ログ |
| `c_ROM｜rom/` | RAM→ROM 焼付け (/rom で生成) |
| `d_成果物｜artifacts/` | WF 実行成果物 |
| `e_レビュー｜reviews/` | クロスモデル検証結果 |
| `f_ログ｜logs/` | 実行ログ |
| `g_実行痕跡｜traces/` | CCL/WF 実行トレース |
| `z_旧構造｜legacy/` | 旧形式の記録 |

## MAP
- Phantazein MCP → セッション管理 (`phantazein_sessions`)
- Ochema MCP → ROM 生成 (`context_rot_distill`)

---
*Created: 2026-03-13*
