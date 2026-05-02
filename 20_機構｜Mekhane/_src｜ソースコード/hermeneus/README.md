# Hermēneus — CCL 実行保証コンパイラ

> **Ἑρμηνεύς** (Hermēneus) = 翻訳者、解釈者
> CCL を実行可能な形式に翻訳し、実行保証を提供する

---

## 概要

Hermēneus は CCL (Cognitive Control Language) の解析・実行エンジン。
3層ルーティング (直接実行 / Compile-Only / LLM 全自動) と
**Precision-Aware Routing** (bge-m3 浅層↔深層分析) を統合した
ハイブリッドアーキテクチャ。

## アーキテクチャ

```
CCL Input → Parser → AST → Precision Router → Execution Strategy
                              │
                              ├─ 直接実行 (無修飾/-): Claude → view_file → WF 直接実行
                              ├─ Compile-Only (+): dispatch → WF 埋込 + 自動検索 → Claude 実行
                              └─ LLM 全自動: dispatch → execute → Gemini 実行
```

### 3層ルーティング (θ12.1 v4.4)

| CCL 形式 | ルーティング先 | 検索 | Precision |
|:---------|:-------------|:-----|:----------|
| `/verb` or `/verb-` | Claude 直接実行 | なし | 不要 |
| `/verb+` | Compile-Only (hermeneus_run) | Gnōsis/Periskopē/S2 自動注入 | ✅ 消費 |
| 演算子あり / `@macro` | LLM 全自動 (hermeneus_run) | Gemini 制御 | ✅ 消費 |

### Precision-Aware Routing (Activity 3)

bge-m3 の浅層 (L1-4) と深層 (L21-24) の cos sim から context の precision を算出:

- **高 precision** (≥0.672): exploit — 検索スキップ、直接実行
- **中 precision** (0.658-0.672): balanced — Gnōsis のみ
- **低 precision** (<0.658): explore — 全3検索系統

```python
from hermeneus.src.precision_router import compute_context_precision, route_execution

p_ml = compute_context_precision("分析対象テキスト")
strategy = route_execution(p_ml, ccl_depth=3)
# → ExecutionStrategy(search_budget=3, gnosis_search=True, ...)
```

## 主要モジュール

```
hermeneus/
├── README.md                  # このファイル
├── PROJECT.md                 # プロジェクトステータス
├── PROOF.md                   # Hegemonikón 公理対応
├── docs/                      # 設計ドキュメント
├── src/                       # ソースコード (55ファイル, ~2.1MB)
│   ├── __init__.py            # パッケージ API
│   ├── cli.py                 # CLI インターフェース
│   ├── parser.py              # CCL パーサー (F:/I:/W:/L: 対応)
│   ├── ccl_ast.py             # AST 定義 (11 ノード型)
│   ├── ccl_ir.py              # 中間表現 (Precision Gradient 統合)
│   ├── ccl_linter.py          # 静的解析 (未定義演算子検出)
│   ├── dispatch.py            # 3層ルーティング・WF 解決
│   ├── mcp_server.py          # MCP サーバー (9ツール)
│   ├── macro_executor.py      # マクロ実行エンジン (ASTWalker)
│   ├── precision_router.py    # Precision-Aware Routing
│   ├── executor.py            # WF 実行エンジン
│   ├── verifier.py            # Multi-Agent Debate
│   ├── audit.py               # 監査レポート
│   ├── ax_pipeline.py         # /ax 全体分析パイプライン
│   ├── peras_pipeline.py      # Peras (極限演算)
│   ├── skill_registry.py      # .typos スキルレジストリ
│   └── ...                    # 他 40 モジュール
└── tests/                     # テスト (756 関数)
    ├── test_parser.py
    ├── test_precision_router.py  # 17 tests
    └── ...
```

## MCP ツール

| ツール | 機能 |
|:-------|:-----|
| `hermeneus_run` | **CCL をアトミックに解析+実行** (dispatch+execute) |
| `hermeneus_dispatch` | CCL を AST に解析 (実行なし) |
| `hermeneus_execute` | WF を LLM で実行 |
| `hermeneus_compile` | CCL を LMQL にコンパイル (デバッグ用) |
| `hermeneus_audit` | 監査レポートを取得 |
| `hermeneus_list_workflows` | WF 一覧取得 |

## テスト

```bash
# 全テスト
pytest hermeneus/tests/ -v

# Precision Router テスト
pytest hermeneus/tests/test_precision_router.py -v
# → 17/17 passed
```

## 依存

| パッケージ | 用途 | 必須 |
|:-----------|:-----|:-----|
| `mcp` | MCP サーバー | ✅ |
| `transformers`, `torch` | bge-m3 (Precision Router) | ❌ (fallback あり) |
| `asyncio` | 並列実行 | ✅ |

---

*Created: 2026-01-31 | Updated: 2026-03-15 (Precision-Aware Routing / 3層ルーティング)*
