# Kyvernetes (Kube) — 行動仕様書 (Behavioral Specification)

> **由来**: Κυβερνήτης (舵手) → cybernetics の語源 → FEP の系譜
> **生成元**: M1 (Project Mariner), A1 (Anthropic Computer Use), O1 (OpenAI Operator) の分析統合
> **日付**: 2026-02-24

---

## 1. 3サービスの比較マトリクス

| 特性 | Mariner | Computer Use | Operator |
|:-----|:--------|:-------------|:---------|
| **スコープ** | Web (Chrome 拡張) | OS 全体 (Desktop) | Web (仮想ブラウザ) |
| **ページ理解** | DOM + Vision ハイブリッド | Vision Only (Screenshot) | DOM + Vision ハイブリッド |
| **実行基盤** | Chrome Extension API / CDP | Docker + xdotool | クラウド仮想ブラウザ |
| **対象ユーザー** | 消費者 | 開発者 (API First) | 消費者 |
| **操作モデル** | DOM イベント発火 | 座標ベース Mouse/Key | DOM + 座標ハイブリッド |
| **HITL** | 不可逆操作前に確認 | 開発者が制御ループ設計 | Chat UI で頻繁に確認 |
| **UI** | サイドバー + ライブハイライト | なし (API) | Chat + ライブビュー |
| **エラー回復** | 自己修正 + HITL | 再スクリーンショット + リトライ | ユーザー委任優先 |

---

## 2. 共通パターン (Universal Patterns)

### P1: OODA 認知ループ

全サービスが共通して **Observe → Orient → Decide → Act** のサイクルを回す。

```
┌─────────────────────────────────────────┐
│               OODA ループ                │
│                                         │
│  ┌──────────┐    ┌──────────┐          │
│  │ Observe  │───>│  Orient  │          │
│  │ (1-2sec) │    │ (0.5-3s) │          │
│  └──────────┘    └──────────┘          │
│       ▲               │                │
│       │          ┌──────────┐          │
│       │          │  Decide  │ ★bottleneck│
│       │          │ (2-4sec) │          │
│       │          └──────────┘          │
│       │               │                │
│  ┌──────────┐    ┌──────────┐          │
│  │ Verify   │<───│   Act    │          │
│  │(screenshot)   │ (0.1-0.5s)│         │
│  └──────────┘    └──────────┘          │
└─────────────────────────────────────────┘
```

**Kube への設計判断**: Playwright の `snapshot()` (Accessibility Tree) を Observe に使用。Decide のボトルネックは LLM 推論時間であり、これは不可避。

### P2: Security Boundary (不可逆操作の境界)

| 操作種別 | 全サービス共通の方針 |
|:---------|:-------------------|
| 読み取り (GET) | **完全自律** — ユーザー介入なし |
| 入力 (POST/PUT) | **条件付き自律** — フォーム入力は自律、送信前に確認 |
| 決済 (Payment) | **必ずユーザー確認** |
| 認証 (Login/MFA) | **ユーザー委任** |
| 個人情報入力 | **ユーザー確認** |
| 利用規約同意 | **ユーザー確認** |

**Kube への設計判断**: BC-5 (Proposal First) と同型。`wait_for_user()` プリミティブを実装。

### P3: エラーリカバリの階層

```
Level 0: Retry    — 同じ操作を再試行 (最大3回)
Level 1: Re-observe — 画面を再取得して状態を再評価
Level 2: Backtrack — 前のステップに戻る
Level 3: Alternative — 別の手段を試す (別サイト、別ルート)
Level 4: Escalate — ユーザーに委任
Level 5: Abort    — タスクを中止して報告
```

### P4: タスク分解 (Hierarchical Task Network)

```
Goal (自然言語)
├── SubGoal 1 (LLM が動的に分解)
│   ├── Action 1.1 (操作プリミティブ)
│   └── Action 1.2
├── SubGoal 2
│   └── Action 2.1 (Loop: for each item)
└── SubGoal N (Security Boundary Check)
    └── wait_for_user()
```

### P5: ワーキングメモリ (外部化された状態管理)

全サービスが「エージェントが今までに集めた情報」を JSON 形式で保持し、LLM のプロンプトに毎ループ注入する。

---

## 3. Kyvernetes アーキテクチャ設計

### 3.1 操作プリミティブ (ActionPrimitive)

```python
from enum import Enum

class ActionCategory(Enum):
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    INPUT = "input"
    EXTRACTION = "extraction"
    SCROLL = "scroll"
    WAIT = "wait"
    USER = "user"

class ActionPrimitive(Enum):
    # Navigation
    NAVIGATE_TO = ("navigate_to", ActionCategory.NAVIGATION)
    GO_BACK = ("go_back", ActionCategory.NAVIGATION)
    OPEN_TAB = ("open_tab", ActionCategory.NAVIGATION)
    CLOSE_TAB = ("close_tab", ActionCategory.NAVIGATION)
    SWITCH_TAB = ("switch_tab", ActionCategory.NAVIGATION)
    
    # Interaction
    CLICK = ("click", ActionCategory.INTERACTION)
    HOVER = ("hover", ActionCategory.INTERACTION)
    
    # Input
    TYPE_TEXT = ("type_text", ActionCategory.INPUT)
    FILL_FORM = ("fill_form", ActionCategory.INPUT)
    SELECT_OPTION = ("select_option", ActionCategory.INPUT)
    PRESS_KEY = ("press_key", ActionCategory.INPUT)
    
    # Extraction
    READ_TEXT = ("read_text", ActionCategory.EXTRACTION)
    EXTRACT_DATA = ("extract_data", ActionCategory.EXTRACTION)
    SCREENSHOT = ("screenshot", ActionCategory.EXTRACTION)
    GET_PAGE_TITLE = ("get_page_title", ActionCategory.EXTRACTION)
    
    # Scroll
    SCROLL_DOWN = ("scroll_down", ActionCategory.SCROLL)
    SCROLL_UP = ("scroll_up", ActionCategory.SCROLL)
    SCROLL_TO = ("scroll_to", ActionCategory.SCROLL)
    
    # Wait
    WAIT_FOR_ELEMENT = ("wait_for_element", ActionCategory.WAIT)
    WAIT_FOR_NAVIGATION = ("wait_for_navigation", ActionCategory.WAIT)
    WAIT_FOR_TIMEOUT = ("wait_for_timeout", ActionCategory.WAIT)
    
    # User Protocol
    WAIT_FOR_USER = ("wait_for_user", ActionCategory.USER)
```

### 3.2 エージェントループ (AgentLoop)

```python
@dataclass
class AgentState:
    goal: str                          # 高レベル目標
    subgoals: list[str]                # 分解されたサブゴール
    current_subgoal_index: int         # 現在のサブゴール
    working_memory: dict               # 収集したデータのキャッシュ
    action_history: list[ActionResult] # 実行済みアクション履歴
    error_count: int                   # 累積エラー数
    max_errors: int = 5                # エラー上限

class KubeAgent:
    """Kyvernetes: OODA ループベースのブラウザエージェント"""
    
    async def execute_goal(self, goal: str) -> AgentResult:
        state = await self._plan(goal)        # タスク分解
        
        while not state.is_complete():
            observation = await self._observe()     # Playwright snapshot
            orientation = await self._orient(state, observation)  # LLM 情勢判断
            decision = await self._decide(state, orientation)     # LLM 次アクション決定
            
            if decision.requires_user_confirmation:
                await self._wait_for_user(decision.confirmation_prompt)
            
            result = await self._act(decision)      # Playwright 実行
            
            if result.is_error:
                await self._recover(state, result)  # エラーリカバリ階層
            else:
                state.advance(result)
        
        return state.to_result()
```

### 3.3 バックエンド: Playwright MCP

| Kube プリミティブ | Playwright MCP ツール |
|:-----------------|:---------------------|
| `navigate_to` | `browser_navigate` |
| `click` | `browser_click` |
| `type_text` | `browser_type` |
| `fill_form` | `browser_fill_form` |
| `screenshot` | `browser_take_screenshot` |
| `read_text` | `browser_snapshot` |
| `scroll_down` | `browser_press_key("PageDown")` |
| `wait_for_element` | `browser_wait_for` |
| `wait_for_user` | `notify_user` (HGK) |

### 3.4 LLM バックエンド: Ochema

| フェーズ | モデル | 用途 |
|:---------|:-------|:-----|
| Plan (タスク分解) | Gemini 3.1 Pro | 高レベル目標をサブゴールに分解 |
| Orient/Decide | Gemini 2.5 Flash | 画面観測から次アクションを決定 (速度優先) |
| Extract | Gemini 2.0 Flash | テキスト抽出・構造化 |

---

## 4. Kube 固有の設計判断

| 判断 | 選択 | 根拠 |
|:-----|:-----|:-----|
| ページ理解 | **DOM (Accessibility Tree) 優先** | Playwright の `snapshot()` が高速かつ構造化されているため。Vision はフォールバック |
| 実行基盤 | **Playwright MCP (既存)** | 新規構築不要。MCP ツールとして既に利用可能 |
| LLM | **Ochema 経由 Gemini** | HGK 統合済。トークン管理も既存 |
| HITL | **BC-5 (Proposal First) 準拠** | HGK の既存プロトコルを流用 |
| 状態管理 | **JSON ワーキングメモリ** | LLM プロンプトに毎ループ注入 |
| エラー上限 | **5回** | 5回失敗 → abort + ユーザーへ報告 |

---

## 5. ファイル構成案

```
mekhane/kube/
├── __init__.py
├── agent.py           # KubeAgent (OODA ループ)
├── primitives.py      # ActionPrimitive enum
├── planner.py         # タスク分解 (LLM)
├── observer.py        # Playwright snapshot → 構造化
├── decider.py         # LLM 意思決定
├── executor.py        # Playwright アクション実行
├── recovery.py        # エラーリカバリ階層
├── memory.py          # ワーキングメモリ管理
├── prompts/
│   ├── plan.prompt     # タスク分解プロンプト
│   ├── decide.prompt   # 次アクション決定プロンプト
│   └── extract.prompt  # データ抽出プロンプト
└── tests/
    ├── test_agent.py
    ├── test_planner.py
    └── test_recovery.py
```
