# IMPL_SPEC: F10 — Plugin OS（認知プラグインシステム）

> **AMBITION 要件**: Claude.ai の全機能を食べて、HGK APP を認知 OS にする
> **PLUGIN_OS_V1**: 10 要素アーキテクチャ (E1-E7 互換層 + X1-X4 拡張層)
> **ステータス**: 🔴 設計段階 / 仕様策定済み / 実装未着手

---

## 1. 概要

Plugin OS は HGK APP の拡張基盤。全ての能力（Skills, WF, MCP, CCL, BC）を
**ポータブルなパッケージ**にまとめ、IDE に依存しない認知フレームワークを実現する。

**核心**: `FEP : 認知 = Plugin : ソフトウェア拡張` — 同型の MECE フレームワーク。

**反証結果** (2026-02-27): Claude.ai の「Skills + Commands + Connectors」は**偽**。
公式仕様直読で 7 要素 (E1-E7) を特定。HGK は +3 要素 (X1 CCL, X2 BC, X3 State, X4 Foundation)
で 10+1 要素に拡張し、超えた。

---

## 2. 10 要素アーキテクチャ

### 互換層 (E1-E7) — Claude.ai Plugin 公式仕様準拠

| # | 要素 | 性質 | ディレクトリ | HGK 既存対応 | 実装状態 |
|:--|:-----|:-----|:-----------|:-----------|:---------|
| E1 | **Skills** | 宣言的 (何を) | `skills/` | `.agent/skills/` (35) | 🟢 既存 |
| E2 | **Commands** | 命令的 (やれ) | `commands/` | WF + CCL マクロ | 🟢 既存 |
| E3 | **Agents** | 委譲的 (任せる) | `agents/` | Colony / Synergeia | 🟢 既存 |
| E4 | **Hooks** | 反応的 (起きたら) | `hooks/` | Sympatheia / n8n | 🟢 既存 |
| E5 | **MCP servers** | 接続的 (繋ぐ) | `.mcp.json` | MCP サーバー群 (8) | 🟢 既存 |
| E6 | **LSP servers** | 知覚的 (見る) | `.lsp.json` | Dendron (部分) | 🟡 Optional |
| E7 | **Settings** | 構成的 (整える) | `settings.json` | 構成ファイル | 🟢 既存 |

### 拡張層 (X1-X4) — HGK 固有。他プラットフォームでは gracefully ignored

| # | 要素 | 性質 | ディレクトリ | HGK 既存対応 | 実装状態 |
|:--|:-----|:-----|:-----------|:-----------|:---------|
| X1 | **CCL** | 代数的 (合成する) | `ccl/` | `nous/ccl/` — 認知代数 | 🟢 既存 |
| X2 | **Constraints** | 統治的 (制限する) | `constraints/` | `.agent/rules/` — BC | 🟢 既存 |
| X3 | **State** | 持続的 (覚える) | `state/` | Handoff / KI / Mneme | 🟢 既存 |
| X4 | **Foundation** | 公理的 (根拠づける) | `foundation/` | `kernel/` — SACRED_TRUTH | 🟢 既存 |

---

## 3. ディレクトリ構造

```
hgk-plugin/
├── .claude-plugin/
│   └── plugin.json          # 互換メタデータ (Claude.ai が読む)
├── plugin.yaml              # HGK 拡張メタデータ (HGK APP が読む)
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
├── assets/                  # アイコン, テンプレート等
└── README.md
```

---

## 4. データモデル

### plugin.yaml (HGK 拡張メタデータ)

```yaml
# HGK Plugin Manifest
id: "com.hegemonikon.core"
name: "Hegemonikón Core"
version: "1.0.0"
description: "FEP に基づく認知ハイパーバイザーフレームワーク"
author: "HGK / Creator"
license: "proprietary"

# 要素宣言 (10要素)
elements:
  skills:
    glob: "skills/**/*.md"
    count: 35
  commands:
    glob: "commands/**/*.md"
    includes_ccl_macros: true
  agents:
    - id: colony-coo
      model: "claude-opus-4.6"
      role: "COO"
    - id: colony-engineer
      model: "gemini-3-pro"
      role: "Engineer"
  hooks:
    - event: "session.start"
      handler: "hooks/on-boot.sh"
    - event: "session.end"
      handler: "hooks/on-bye.sh"
  mcp_servers:
    config: ".mcp.json"
  lsp_servers:
    config: ".lsp.json"
    optional: true
  settings:
    config: "settings.json"

# 拡張層 (X1-X4)
extensions:
  ccl:
    operators: "ccl/operators.md"
    macros: "ccl/macros/"
  constraints:
    glob: "constraints/**/*.md"
    always_on: true
  state:
    handoff_dir: "state/handoffs/"
    ki_dir: "state/knowledge/"
  foundation:
    sacred_truth: "foundation/SACRED_TRUTH.md"
    axiom_hierarchy: "foundation/axiom_hierarchy.md"

# 互換性
compatibility:
  claude_ai: true     # .claude-plugin/plugin.json が存在
  hgk_app: true       # plugin.yaml が存在
  other: "graceful"   # X1-X4 は無視される
```

### TypeScript 型定義

```typescript
interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;

  elements: {
    skills: { glob: string; count: number };
    commands: { glob: string; includes_ccl_macros: boolean };
    agents: AgentDef[];
    hooks: HookDef[];
    mcp_servers: { config: string };
    lsp_servers?: { config: string; optional: boolean };
    settings: { config: string };
  };

  extensions: {
    ccl: { operators: string; macros: string };
    constraints: { glob: string; always_on: boolean };
    state: { handoff_dir: string; ki_dir: string };
    foundation: { sacred_truth: string; axiom_hierarchy: string };
  };

  compatibility: {
    claude_ai: boolean;
    hgk_app: boolean;
    other: 'graceful' | 'strict';
  };
}

interface AgentDef {
  id: string;
  model: string;
  role: string;
}

interface HookDef {
  event: string;      // 'session.start' | 'session.end' | 'file.change' | ...
  handler: string;    // スクリプトパス
}

interface PluginRegistry {
  plugins: PluginEntry[];
}

interface PluginEntry {
  id: string;
  name: string;
  version: string;
  path: string;       // インストール先パス
  enabled: boolean;
  installed_at: string;
  elements_loaded: string[];  // ['skills', 'commands', 'ccl', ...]
}
```

---

## 5. API 仕様

### 新規 (全て実装が必要)

| Method | Path | 説明 |
|:-------|:-----|:-----|
| GET | `/api/plugins` | インストール済み Plugin 一覧 |
| GET | `/api/plugins/{id}` | Plugin 詳細 (manifest + 状態) |
| POST | `/api/plugins/install` | Plugin インストール (パスまたは URL) |
| DELETE | `/api/plugins/{id}` | Plugin アンインストール |
| PUT | `/api/plugins/{id}/enable` | Plugin 有効化 |
| PUT | `/api/plugins/{id}/disable` | Plugin 無効化 |
| POST | `/api/plugins/validate` | Plugin manifest 検証 |
| GET | `/api/plugins/{id}/elements` | Plugin の要素一覧 (E1-E7, X1-X4) |

### `/api/plugins/{id}` レスポンス例

```json
{
  "id": "com.hegemonikon.core",
  "name": "Hegemonikón Core",
  "version": "1.0.0",
  "enabled": true,
  "path": "/path/to/hgk-plugin",
  "elements": {
    "skills": { "count": 35, "loaded": true },
    "commands": { "count": 24, "loaded": true },
    "agents": { "count": 6, "loaded": true },
    "hooks": { "count": 2, "loaded": true },
    "mcp_servers": { "count": 8, "loaded": true },
    "ccl": { "operators": 15, "macros": 12, "loaded": true },
    "constraints": { "count": 12, "always_on": true, "loaded": true },
    "state": { "handoffs": 87, "kis": 42, "loaded": true },
    "foundation": { "loaded": true }
  },
  "compatibility": {
    "claude_ai": true,
    "hgk_app": true
  }
}
```

---

## 6. フロントエンド実装ステップ

### Phase 1: Plugin ローダーコア

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 1-1 | `PluginLoader` クラス — plugin.yaml パース + 検証 | `src/plugin/loader.ts` [NEW] |
| 1-2 | `PluginRegistry` — インストール済み Plugin 管理 | `src/plugin/registry.ts` [NEW] |
| 1-3 | HGK 自体を「Plugin #0」として自動認識 | `src/plugin/self-register.ts` [NEW] |

### Phase 2: Plugin 管理 UI

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 2-1 | Plugin 一覧ビュー (設定画面内) | `src/views/plugins.ts` [NEW] |
| 2-2 | Plugin 詳細パネル (要素一覧 + 有効/無効切替) | `src/views/plugin-detail.ts` [NEW] |
| 2-3 | バックエンド API 実装 | `mekhane/api/routes/plugins.py` [NEW] |

### Phase 3: Claude.ai 互換エクスポート

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 3-1 | HGK → `.claude-plugin/` エクスポーター | `src/plugin/exporter.ts` [NEW] |
| 3-2 | plugin.yaml → plugin.json 変換ロジック | `mekhane/plugin/converter.py` [NEW] |
| 3-3 | CLI: `hgk plugin export --target claude` | `mekhane/plugin/cli.py` [NEW] |

### Phase 4: MCP Apps 統合 (L5 埋込層)

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 4-1 | `@mcp-ui/client` 導入 + PoC | `package.json`, `src/plugin/mcp-app-renderer.ts` [NEW] |
| 4-2 | sandboxed iframe + CSP 設定 (Tauri v2) | `src-tauri/tauri.conf.json` |
| 4-3 | 既存 MCP サーバーに `registerAppTool` 追加 | MCP サーバー各ファイル |

### Phase 5: Plugin ビルダー

| Step | 内容 | ファイル |
|:-----|:-----|:---------|
| 5-1 | GUI Plugin 作成ウィザード | `src/views/plugin-builder.ts` [NEW] |
| 5-2 | テンプレート生成 (scaffolding) | `mekhane/plugin/scaffold.py` [NEW] |
| 5-3 | Plugin マーケットプレイス UI (将来) | `src/views/marketplace.ts` [NEW] |

---

## 7. Claude.ai 互換性

```
Claude.ai Plugin ロード時:
  → .claude-plugin/plugin.json を読む
  → E1-E7 を認識・適用
  → X1-X4 は無視 (unknown keys = gracefully ignored)
  → 機能的に動作する

HGK APP ロード時:
  → plugin.yaml を読む (優先)
  → E1-E7 + X1-X4 を全て認識・適用
  → 完全な認知フレームワークとして動作する
```

### 関手 F: IDE → Plugin

| 性質 | 判定 | 備考 |
|:-----|:-----|:-----|
| **忠実 (faithful)** | ✅ | 射の方向は保存される |
| **充満 (full)** | ✅ (X4追加後) | Foundation 層で正当化構造が保存される |
| **本質的全射** | ✅ | 全要素に IDE 対応物あり (E6 は Optional) |

---

## 8. IDE 脱出ロードマップ

```
Phase 0 (現在): Antigravity IDE → .agent/ → HGK
Phase 1 (F10):  HGK APP → Plugin System → HGK (IDE 非依存)
Phase 2 (将来): Plugin → Claude.ai Marketplace / 任意ホスト
```

| マイルストーン | 説明 | 前提 |
|:-------------|:-----|:-----|
| M1: Self-Recognition | HGK 自体を Plugin #0 として認識 | Phase 1 |
| M2: Export to Claude | `.claude-plugin/` エクスポート | Phase 3 |
| M3: MCP Apps | 外部アプリの APP 内埋め込み | Phase 4 |
| M4: Marketplace | Plugin の公開・配布 | Phase 5 |
| M5: IDE 完全脱出 | Antigravity なしで全機能動作 | M1-M4 |

---

## 9. テスト戦略

| テスト種別 | 内容 |
|:----------|:-----|
| 単体テスト | `test_plugin_loader.py` — manifest パース・検証 |
| 単体テスト | `test_plugin_converter.py` — YAML→JSON 変換 |
| 統合テスト | HGK Plugin #0 が全 10 要素をロードできること |
| 互換テスト | エクスポートした `.claude-plugin/` が Claude.ai Plugin 仕様に準拠 |
| E2E | Plugin 管理 UI → インストール → 有効/無効 → アンインストール |
| 非機能 | Plugin ロード < 1 秒 / 10 要素並列解析 |

---

## 10. 依存関係

| 依存先 | 種別 | 状態 |
|:-------|:-----|:-----|
| `.agent/skills/` (35 files) | E1 データソース | 🟢 既存 |
| `.agent/workflows/` | E2 データソース | 🟢 既存 |
| `hgk/api/colony.py` | E3 Agent 実装 | 🟢 MVP |
| `mekhane/ergasterion/n8n/` | E4 Hooks 実装 | 🟢 既存 |
| MCP サーバー群 (8) | E5 接続先 | 🟢 稼働中 |
| `mekhane/dendron/` | E6 LSP (部分) | 🟡 Optional |
| `.agent/rules/` | X2 制約ソース | 🟢 既存 |
| `kernel/SACRED_TRUTH.md` | X4 公理ソース | 🟢 不変 |
| `@mcp-ui/client` (npm) | L5 MCP Apps | 🔴 未導入 |
| OpenClaw パターン | T-14 Tool Policy | 🟡 分析済み |

---

## 11. 起源

> 「Claude.ai の全機能を食べて、HGK APP を認知 OS にする」 — Creator
> 「このIDEの機構はすべてPluginの関手だと思う」 — Creator
> 「基盤層はもうすでにHGKにないの？？ 無いのはまずくない？」 — Creator
> 「さっさと出たいよこんな箱」 — Creator (IDE 脱出の意志)

---

*IMPL_SPEC F10 v1.0 — 2026-03-08*
*Based on: AMBITION.md F10 + PLUGIN_OS_V1.md (2026-02-28)*
