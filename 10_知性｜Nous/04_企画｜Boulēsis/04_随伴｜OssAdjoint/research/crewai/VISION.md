# CrewAI ⊣ Synteleia 随伴統合ビジョン (L3)

> **優先度**: B → ④ (Phase C: 構成力)
> **repo**: crewAIInc/crewAI (`lib/crewai/src/crewai/`)
> **HGK 対象**: Synteleia (`mekhane/synteleia/`)
> **調査日**: 2026-03-14 (L3 コードレベル対照版)
> **SOURCE**: crew.py, base_agent.py, process.py (GitHub main), orchestrator.py, base.py (ローカル)

---

## 1. コードレベル構造比較

### 1.1 エージェント定義

| 観点 | CrewAI `BaseAgent` | Synteleia `AuditAgent` |
| --- | --- | --- |
| **基底** | `BaseModel` (Pydantic) + `ABC` | `ABC` のみ (素の Python) |
| **必須フィールド** | `role`, `goal`, `backstory` (str) | `name`, `description` (クラス属性) |
| **ツール** | `tools: list[BaseTool]` | なし (各エージェントが独自実装) |
| **LLM** | `llm: Any` (Agent 毎に切替可) | Kritai L2/L3 のみ backend 引数 |
| **MCP** | `mcps: list[MCPServerConfig]` | なし |
| **Knowledge** | `knowledge`, `knowledge_sources` | なし |
| **コア抽象メソッド** | `execute_task(task, context, tools)` | `audit(target: AuditTarget) → AgentResult` |
| **タイプ判別** | なし (汎用) | `supports(target_type: AuditTargetType)` |
| **設定方法** | YAML config → dict → `Agent(**config)` | Python コードでハードコード |
| **バリデーション** | Pydantic `model_validator`, `field_validator` | なし |

**構造差異の本質**: CrewAI は *汎用マルチエージェント* で Agent に `role/goal/backstory` を渡し Task を execute。Synteleia は *監査特化* で Agent に `AuditTarget` を渡し `AgentResult` を返す。

### 1.2 オーケストレーション

| 観点 | CrewAI `Crew` | Synteleia `SynteleiaOrchestrator` |
| --- | --- | --- |
| **基底** | `FlowTrackable, BaseModel` (Pydantic) | 素の Python クラス |
| **エージェント登録** | `agents: list[BaseAgent]` (Field) | `poiesis_agents` + `kritai_agents` (コンストラクタ) |
| **タスク概念** | `tasks: list[Task]` (Agent に Task を割当) | なし (`AuditTarget` が暗黙の Task) |
| **実行モード** | `Process.sequential` / `.hierarchical` Enum | `parallel: bool` (ThreadPoolExecutor) |
| **エントリ** | `kickoff(inputs)` → `_run_sequential_process()` | `audit(target)` → `_audit_parallel()` or `_audit_sequential()` |
| **階層構成** | L1 のみ (manager_agent で階層化) | L1/L2/L3 ファクトリ (`with_l2()`, `with_multi_l2()`, `with_l3()`) |
| **結果統合** | `CrewOutput` (last task output) | `AuditResult` (全 AgentResult 集約, severity 分類) |
| **非同期** | `akickoff()`, `kickoff_async()` | なし |
| **メモリ** | `memory: bool / Memory` (cross-session) | なし |
| **コールバック** | `before_kickoff_callbacks`, `after_kickoff_callbacks`, `step_callback`, `task_callback` | なし |
| **イベント** | `crewai_event_bus.emit()` + `EventListener` | なし |
| **ストリーミング** | `stream: bool` → `CrewStreamingOutput` | なし |

### 1.3 プロセス実行

| 観点 | CrewAI | Synteleia |
| --- | --- | --- |
| **Sequential** | Task を順番に実行、前 Task の output を次の context に | 全エージェントを順番に実行 (`_audit_sequential`) |
| **Parallel** | なし (Process Enum に未定義) | `ThreadPoolExecutor` で全エージェント並列 (`_audit_parallel`) |
| **Hierarchical** | manager_agent がタスク割当を決定 | L2/L3 ファクトリで段階的にエージェントを追加 |
| **Consensual** | `# TODO` (未実装) | ConsensusAgent (L3) — 複数 LLM の majority voting |

---

## 2. Gap 分析 (コードレベル)

| ID | 欠陥 | Synteleia 現状 | CrewAI 参考 | 影響 |
| --- | --- | --- | --- | --- |
| D-1 | **エージェント定義がハードコード** | `OusiaAgent()` 等を `__init__` でインスタンス化 (orchestrator.py L66-77) | YAML → `Agent(**config)` + `_create_task()` (crew.py) | 新エージェント追加に Python コード変更が必要 |
| D-2 | **タスク概念の不在** | `AuditTarget` は「何を監査するか」のみ。「誰がどの順で何をする」の指示がない | `Task(description, agent, expected_output, tools)` | エージェント間の実行順制御が不可能 |
| D-3 | **イベントシステムなし** | 監査結果の WBC 通知のみ (`notify_wbc`) | `crewai_event_bus` + `EventListener` + 13+ event types | 実行中のフック・計測・UI連携が困難 |
| D-4 | **非同期実行なし** | `ThreadPoolExecutor` (スレッドベース) | `akickoff()` (ネイティブ async/await) | I/O バウンドの LLM 呼出でスケーラビリティ制限 |
| D-5 | **Agent レベル LLM/Tool 設定なし** | L2 エージェントのみ backend 引数 | 全 Agent に `llm`, `tools`, `max_iter`, `mcps` | L1 エージェント (パターンベース) と L2+ を同じインターフェースで扱えない |
| D-6 | **バリデーションなし** | 型ヒントのみ | Pydantic `model_validator` + `field_validator` | 不正な設定がランタイムまで検出されない |
| D-7 | **コールバック/フックなし** | なし | `before_kickoff_callbacks`, `step_callback`, `task_callback` | 実行フローの拡張性が低い |

---

## 3. Import 候補の判定 (L3 改訂)

| ID | 候補 | 判定 | コードレベル根拠 |
| --- | --- | --- | --- |
| C-01 | **Agent YAML 宣言的構成** | **Import** | `BaseAgent` の Pydantic フィールド構造 → `AuditAgent` を Pydantic 化し、YAML `config` からインスタンス生成可能にする |
| C-02 | **Task 概念の導入** | **Import** | `Task(description, agent, expected_output)` → 監査の「何を、誰が、何の出力を」を宣言的に分離。現在は `AuditTarget` が全てを兼ねている |
| C-03 | **Hierarchical プロセス** | **Watch** | CrewAI の `manager_agent` パターン vs Synteleia の L1→L2→L3 ファクトリ。Synteleia は独自の階層モデルが既にある |
| C-04 | **イベントバス** | **Watch** | `crewai_event_bus` → Synteleia は `notify_wbc` だけ。EventBus パターンは Sympatheia WBC/通知との統合で価値あり |
| C-05 | **ネイティブ async** | **Watch** | `akickoff()` → ThreadPoolExecutor → asyncio 変換。L2/L3 の LLM 呼出は async 化で大幅高速化の可能性 |
| C-06 | **Flows (イベント駆動 WF)** | **Skip** | HGK は CCL チェーンで同等機能。二重実装リスク |
| C-07 | **Cross-session メモリ** | **Skip** | HGK は ROM/Handoff/Mneme で成熟した記憶体系あり |
| C-08 | **Agent 間委譲 (`allow_delegation`)** | **Skip** | Synteleia は独立監査モデル。エージェント間委譲は監査品質を損なう |

---

## 4. Fix(G∘F) 随伴構造 (L3 精密化)

```
F: HGK 24動詞 → CrewAI-style Agent/Task YAML
   /noe → Agent(role="deep_analyzer", goal="構造認識", tools=[view_file, mneme_search])
   /dia → Agent(role="judge", goal="品質判定", tools=[synteleia_audit])
   組成 /noe+>>/dia+ → [Task(noe_agent), Task(dia_agent)] + Process.sequential

G: Agent/Task YAML → Synteleia 実行エンジン
   YAML → AuditAgent Pydantic インスタンス化
   Task リスト → Orchestrator.audit() 実行
   AuditResult → 評価データ

Fix(G∘F): 実行評価 → 動詞組成の改善 → 再実行 → 収束
   条件: F∘G ≈ Id (YAML→実行→YAML で元の意図が保存される)
```

### 実装上の核心

1. **F (動詞→YAML)**: CCL パーサー (Hermēneus) の出力を拡張し、Agent YAML テンプレートを生成
2. **G (YAML→実行)**: `SynteleiaOrchestrator.__init__` を YAML config ローダーに改造
3. **F∘G ≈ Id 検証**: 生成した YAML を再パースし、元の動詞組成と一致するかテスト

---

## 5. 実装ロードマップ (L3)

### Phase 0: AuditAgent Pydantic 化

**ファイル**: `mekhane/synteleia/base.py`

```python
# 現在
class AuditAgent(ABC):
    name: str = "BaseAgent"
    description: str = "Base audit agent"

# 改修案
class AuditAgent(BaseModel, ABC):
    name: str = Field(default="BaseAgent")
    description: str = Field(default="Base audit agent")
    config: dict[str, Any] | None = Field(default=None)

    @model_validator(mode="after")
    def apply_config(self) -> Self: ...
```

**影響**: Pydantic 化により YAML config → `AuditAgent(**config)` が可能に。基本的な API 互換は維持 (後方互換)。

### Phase 1: Config YAML ローダー

**新規ファイル**: `mekhane/synteleia/config_loader.py`

- YAML ファイルから `AuditAgent` / `AuditTarget` をインスタンス化
- CrewAI の `_setup_from_config()` パターンを参考
- 既存のハードコード構成もそのまま動作 (フォールバック)

### Phase 2: Task 概念の導入

**新規ファイル**: `mekhane/synteleia/task.py`

- `AuditTask(target, agent, expected_output, condition)` を定義
- `SynteleiaOrchestrator.audit()` を Task リストベースに拡張
- `ConditionalTask` パターン (CrewAI) を参考に条件分岐を導入

### Phase 3: Phase C (F構成) 統合

- CCL 動詞組成 → Agent/Task YAML 自動生成パイプライン
- Hermēneus の WorkflowExecutor と Synteleia Config Loader の接続
- F∘G ≈ Id 検証テスト

---

*L3 Deep Dive: 2026-03-14 — SOURCE: CrewAI GitHub main + Synteleia ローカルソース*
