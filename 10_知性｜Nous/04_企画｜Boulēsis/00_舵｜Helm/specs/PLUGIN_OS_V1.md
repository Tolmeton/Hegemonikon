# HGK Plugin OS Architecture V1.0

> **Version**: 1.0
> **Date**: 2026-02-28
> **Origin**: /sop+ (公式仕様消化) → /noe+ nous (関手精緻化) → Creator 対話 (kernel 再認識)

---

## 本質

```
FEP:    「全ての認知は予測誤差最小化で説明できる」
Plugin: 「全ての拡張は 10要素で構成できる」

Plugin は認知フレームワークの MECE フォーマット。拠り所。
```

---

## 10要素アーキテクチャ

### 互換層 (E1-E7) — Claude.ai Plugin 公式仕様準拠

| # | 要素 | 性質 | ディレクトリ | HGK 対応 |
|:--|:-----|:-----|:-----------|:---------|
| E1 | **Skills** | 宣言的 (何を) | `skills/` | `.agent/skills/` (35) |
| E2 | **Commands** | 命令的 (やれ) | `commands/` | WF + CCL マクロ |
| E3 | **Agents** | 委譲的 (任せる) | `agents/` | Colony / Synergeia |
| E4 | **Hooks** | 反応的 (起きたら) | `hooks/` | Sympatheia / n8n |
| E5 | **MCP servers** | 接続的 (繋ぐ) | `.mcp.json` | MCP サーバー群 (7) |
| E6 | **LSP servers** | 知覚的 (見る) | `.lsp.json` | Dendron (部分) — Optional |
| E7 | **Settings** | 構成的 (整える) | `settings.json` | 構成ファイル |

### 拡張層 (X1-X4) — HGK 固有。他プラットフォームでは gracefully ignored

| # | 要素 | 性質 | ディレクトリ | HGK 対応 |
|:--|:-----|:-----|:-----------|:---------|
| X1 | **CCL** | 代数的 (合成する) | `ccl/` | `nous/ccl/` — 認知代数 |
| X2 | **Constraints** | 統治的 (制限する) | `constraints/` | `.agent/rules/` — BC |
| X3 | **State** | 持続的 (覚える) | `state/` | Handoff / KI / Mneme |
| X4 | **Foundation** | 公理的 (根拠づける) | `foundation/` | `kernel/` — SACRED_TRUTH |

---

## ディレクトリ構造

```
hgk-plugin/
├── .claude-plugin/
│   └── plugin.json          # 互換メタデータ
├── plugin.yaml              # HGK 拡張メタデータ
│
│  ── 互換層 (E1-E7) ──
├── skills/                  # E1: SKILL.md ファイル群
├── commands/                # E2: スラッシュコマンド定義
├── agents/                  # E3: サブエージェント定義
├── hooks/                   # E4: イベントフック
├── .mcp.json                # E5: MCP サーバー設定
├── .lsp.json                # E6: LSP サーバー設定 (Optional)
├── settings.json            # E7: デフォルト設定
│
│  ── 拡張層 (X1-X4) ──
├── ccl/                     # X1: 演算子・マクロ定義
├── constraints/             # X2: 行動制約 (BC)
├── state/                   # X3: 状態管理定義
├── foundation/              # X4: 公理・定理体系
│
├── assets/
└── README.md
```

---

## 関手 F: IDE → Plug

| 性質 | 判定 | 備考 |
|:-----|:-----|:-----|
| **忠実 (faithful)** | ✅ | 射の方向は保存される |
| **充満 (full)** | ✅ (X4追加後) | Foundation 層で正当化構造が保存される |
| **本質的全射** | ✅ | 全要素に IDE 対応物あり (E6 は Optional) |

**Kalon**: 0.95 (残り 0.05 = Drift: 未知の未知)

---

## Claude.ai との互換性

```
Claude.ai Plugin ロード時:
  → .claude-plugin/plugin.json を読む
  → E1-E7 を認識・適用
  → X1-X4 は無視 (unknown keys)
  → 機能的に動作する

HGK APP ロード時:
  → plugin.yaml を読む
  → E1-E7 + X1-X4 を全て認識・適用
  → 完全な認知フレームワークとして動作する
```

---

## 起源

> 「Claude.ai の全機能を食べて、HGK APP を認知 OS にする」 — Creator
> 「このIDEの機構はすべてPluginの関手だと思う」 — Creator
> 「基盤層はもうすでにHGKにないの？？無いのはまずくない？」 — Creator

---

*V1.0 — 2026-02-28 Creator 対話から構造化*
