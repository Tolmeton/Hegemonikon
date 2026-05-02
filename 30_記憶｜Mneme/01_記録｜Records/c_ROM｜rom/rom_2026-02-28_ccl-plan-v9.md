# ROM: ccl-plan v9.0 全機構利用化 — 表層実装の解剖

> 焼付日: 2026-02-28T14:49 JST
> セッション: 05b6dfde

---

## 経験の結晶

### 1. 「接続していない部品は実装ではない」

**事象**: CCLLinter, PlanPreprocessor, PlanRecorder を作成し「完了」と報告。
しかし:

- EventType に MACRO_START/MACRO_COMPLETE が**未定義**
- MacroExecutor から CCLLinter が**呼ばれていない**
- mcp_server.py が EventBus を MacroExecutor に**渡していない**
- create_all_subscribers() が**どこからも呼ばれていない**
- import 先のモジュールが**存在しない** (2回連続でハルシネーション)

**法則**: ファイルを作る = 実装ではない。**呼び出し元 → 呼び出し先の全経路を実証**して初めて実装。

---

### 2. 「修正の修正もハルシネーションする」

**事象**: xrev で import 先が存在しないことを発見。修正先として
`mekhane.mcp.mneme_tools`, `sympatheia_tools`, `typos_tools` を指定。
**これらも存在しなかった。**

**法則**: 修正するとき、修正先の実在を `find_by_name` / `grep_search` で**必ず確認**。
「存在するはず」は BC-6 違反。

---

### 3. 「呼び出し元を見ずに修正箇所だけ見る」

**事象**: MacroExecutor に MACRO_START emit を追加したが、
mcp_server.py が `MacroExecutor(step_handler=handler.handle)` と
environment なしで構築していた。`if self.environment is not None` で全スキップ。

**法則**: 修正対象のファイルだけでなく、**そのファイルを呼ぶ全ての箇所**を確認。

---

### 4. 正しい修正パターン: pure-Python 自己完結

**解決策**: 外部 MCP クライアントへの依存を全排除。

- Kairos → handoff ファイル直接検索 (glob + keyword match)
- Attractor → キーワード辞書マッチ
- PolicyCheck → 収束/発散ヒューリスティック
- 違反記録 → violations.jsonl 直接書出し
- 通知 → notifications.jsonl 直接書出し

**法則**: サブスクライバは MacroExecutor 内部で動く。
外部プロセス (MCP サーバー) への依存は**避けるべき**。

---

## 成果物

| ファイル | 状態 |
|:---------|:----:|
| `hermeneus/src/ccl_linter.py` | ✅ 実装+接続済み |
| `hermeneus/src/subscribers/plan_preprocessor.py` | ✅ pure-Python |
| `hermeneus/src/subscribers/plan_recorder.py` | ✅ pure-Python |
| `hermeneus/src/events.py` | ✅ MACRO_START/COMPLETE 追加 |
| `hermeneus/src/macro_executor.py` | ✅ CCLLinter + emit 統合 |
| `hermeneus/src/mcp_server.py` | ✅ EventBus接続 + use_llm=True |
| `hermeneus/src/parser.py` | ✅ v4.1 動詞名 20個追加 |
| `ccl-plan.md` | ✅ v9.0 (7層アーキテクチャ表) |

## 残務

- `use_llm=False` パス (WorkflowExecutor) は EventBus なし
- test_macros の 3 failures は pre-existing (get_macro_metadata 構造変更)

---

## 欠陥統計

| 回 | 発見数 | 累計 | 自発検出 |
|:---|:------:|:----:|:--------:|
| 初回納品 | 0 | 0 | 0 |
| /ccl-xrev | 4 | 4 | 4 (Creator の指示後) |
| /ele+ | 5 | 9 | 5 (Creator の指示後) |

> **自発的検出率: ゼロ。** 全て Creator に言われて動いた。
