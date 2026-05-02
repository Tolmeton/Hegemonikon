# S-003: Claude × Gemini 分業 — 構想 v3

> **Created**: 2026-03-14
> **Updated**: 2026-03-17 — Hub 深化 (S-006 Stage 1 推奨エンジン + テストスイート)
> **Status**: Phase 1 完了 (Maturity 4) → Phase 2 着手待ち
> **Sprint**: S-003/S-006 (Claude × Gemini 分業体制 + Hub MCP 深化)
> **Phase 1 完了**: 2026-03-17 — Hub MCP 骨格 + Shadow + Gate + 推奨エンジン + テスト 29件

## 核心

```
旧 (v2): Gemini がたたき台 → Claude が 1 or 5 → 完成
新 (v3): Hub MCP が全射を統制。Claude → Gemini の関係を「指摘・実装・相談」の射の束として管理
```

**Gemini = 部下 (統制対象)**。Claude が指示・委託・監査する全ての射が Hub を通過する。

## アーキテクチャ (V-008 統合)

```
Creator
  ↕ 対話 (高 precision)
Claude (control plane — 監督・判断・品質)
  │
  ▼
Hub MCP (routing plane — 全射が通過)
  ├── Shadow: 自動反証 (全呼出に対して)
  ├── Gate: 品質監査 (Sekisho 統合)
  └── Packet: 返却票 + カプセル化 (V-009)
  │
  ▼
各 MCP (data plane — 実働部隊)
  ├── ochema (Gemini 同期) ├── hermeneus (CCL)  ├── periskope (検索)
  ├── mneme (記憶)         ├── sympatheia (恒常) ├── jules (非同期)
  ├── sekisho → Hub に統合  ├── digestor (消化)  └── typos (Skill)
```

## 射の束: Claude → Gemini の3つの射

| 射 | ツール | Hub での統制 |
|:---|:---|:---|
| **指摘** (反証・監査) | Shadow Gemini + Sekisho | Hub routing plane で全呼出を監視 |
| **実装** (コード生成) | Jules + ask_with_tools | Hub 経由で委託 → 返却票回収 |
| **相談** (セカンドオピニオン) | ask_cortex + ask_chat | Hub 経由 + コンテキスト共有 |

> **v2 の誤り**: 「指摘」の射だけを Ochema 内に実装 (B22: 射を忘却)。
> **v3 の修正**: 全射を Hub routing plane で統制。

## ツール優先度

| 優先度 | ツール | 特性 | 用途 |
|:-------|:-------|:-----|:-----|
| **1 (最優先)** | `ochema ask_with_tools` | ローカル・同期・ファイルアクセス可 | コード調査、分析、設計レビューのたたき台 |
| **2** | `ochema ask_cortex` | ローカル・同期・軽量 | 数式検証、概念チェック、セカンドオピニオン |
| **3** | `ochema start_chat` + `send_chat` | ローカル・同期・マルチターン | 対話的な壁打ち、煮詰め |
| **4 (非同期)** | `jules create_task` / `batch_execute` | クラウド・非同期 | **レビュー向き**。コードレビュー、PR 監査 |

> **Creator 判断**: Jules はクラウド + 非同期 → たたき台には使いにくい。レビュー系に使うべき。

## 設計原則

1. **Gemini の出力は TAINT** — Claude が SOURCE に昇格させる
2. **Material Not Script** — Gemini の出力をそのまま Creator に渡さない
3. **まず ochema** — ローカル+同期を完全に使いこなしてから Jules へ
4. **3 並列は初期目標** — 通信オーバーヘッドが支配的にならない範囲
5. **Hub = 一石二鳥** — Shadow + Sekisho を routing plane に統合 (V-008)

## 成熟度

| 段階 | 定義 | 状態 |
|:---|:---|:---|
| 1 | Ochema/Jules が動く | ✅ |
| 2 | Shadow が Ochema 内で暫定動作 | ✅ (2026-03-16) |
| 3 | Hub MCP 骨格 (routing + shadow + gate) | ✅ (2026-03-17) |
| 4 | Hub 推奨エンジン (S-006 Stage 1) + テスト 29件 | ✅ (2026-03-17) |
| 5 | 射の束 (指摘+実装+相談) の統制的運用 | Phase 2 |
| 6 | V-008 Phase 2+ (直接通信許可リスト) | 長期 |

## Phase 0 検証結果 (2026-03-16)

- Shadow Gemini ピギーバック動作確認 (imp=0.6, comp=0.4, conf=70%)
- コンテキスト拡張: reasoning フィールド + 5000文字上限
- **構造的限界**: Ochema 内配置のため、Claude の全アクションの一部しか監視できない → Phase 1 で Hub に移動

## 次のステップ

1. ~~ochema 系ツールの実戦投入~~ ✅
2. ~~返却品質の評価と改善~~ ✅ (Shadow ピギーバック確認)
3. ~~Hub MCP 骨格の設計と実装~~ ✅ (routing + shadow + gate)
4. ~~Hub 推奨エンジン (S-006 Stage 1)~~ ✅ (キーワード × TOOL_SCORES)
5. ~~テストスイート~~ ✅ (29件 全 PASS)
6. **[次] IDE 接続統合** (Antigravity → Hub MCP 経由に変更)
7. S-006 Stage 2 (委任実行) + Stage 3 (完全秘書)
8. 射の束 (指摘+実装+相談) の統制的運用

