# Ergon プロジェクト 設計文書 05

## R (bye) 関手スキーマ

本書は、右随伴 `R` を**bye そのもの**として再定義する。`R` は実行結果を説明文へ変える補助写像ではない。**次の boot に残すべき fixed point だけを選び出す蒸留関手**である。

## 1. 設計原理

`R: \text{Exec} \to \text{Cog}` は右随伴であり、実行結果を belief へ蒸留する。ハーネス設計学では、これを次のように読む。

$$
R: \text{Exec} \to \text{Cog}
$$

> **R = bye**

bye の本質は情報削減ではない。**次の `L (boot)` に再投入できる核だけを残すこと**である。

| 保持すべき | 忘却すべき | 対応軸 |
|:---|:---|:---|
| 制約の差分 | 中間ログの冗長行 | C |
| summary の意味核 | 書き換え履歴の全量 | E |
| 実際に効いた Hook / tool | 一時的な試行錯誤 | M |
| prediction error | 予測通りだった細部 | C/E/M 横断 |

## 2. ExecutionResult 型 ($R$ の入力)

```python
@dataclass
class ExecutionResult:
    plan_id: str
    tool_name: str
    raw_output: str | dict
    exit_status: Literal["success", "failure", "partial", "timeout"]
    actual_side_effects: list[str]
    duration_ms: int
    verification: dict | None = None
```

この型は raw な結果を受けるが、`R` の仕事はそれを丸ごと belief にすることではない。**何を kernel として残し、何を忘却してよいかを判定すること**にある。

## 3. BeliefUpdate 型 ($R$ の出力)

```python
@dataclass
class BeliefUpdate:
    source_label: Literal["SOURCE", "TAINT", "WEAK_INPUT"]
    confidence: Literal["確信", "推定", "仮説"]
    belief_delta: Literal["new", "updated", "confirmed", "refuted"]

    constraint_delta: str
    """C 軸。何が新しい禁止条件 / 例外 / 安全判断として残るか。"""

    encoding_summary: str
    """E 軸。次の boot に渡す summary / handoff / ROM の核。"""

    mechanism_receipt: str
    """M 軸。どの Hook / tool / test が実際に効いたか。"""

    prediction_error: str | None = None
    next_action: str | None = None
    plan_id: str = ""
```

旧来の `summary` を `constraint_delta / encoding_summary / mechanism_receipt` に分解したのが要点である。これにより蒸留後の kernel が `C/E/M` のどこに属するかを見失わない。

## 4. 代表的な $R$ インスタンス

### 4.1 $R_{\text{task}}$

- 単一 Task の結果を短い Belief Update にする
- 典型出力: `prediction_error`, `next_action`

### 4.2 $R_{\text{slice}}$

- 複数 Task の結果をまとめて Fractal Summary にする
- 典型出力: 契約更新、統合テストの帰結

### 4.3 Paper X CM 戦略としての $R$

Paper X の CM 戦略でいう `DA / Sum / KLN` は、**`R` がどの粗さで蒸留するかの 3 インスタンス**として読める。

- **DA**: 直近の判断に必要な最短蒸留
- **Sum**: 複数結果を束ねる中域蒸留
- **KLN**: 次の session や child handoff に耐える核蒸留

名称の展開より重要なのは、3 つとも `R` の仕事、すなわち**実行結果から再 boot 可能な核を残す操作**だという点である。

### 4.4 $R_{\text{session}} = \text{bye}$

- セッション全体を Handoff / ROM / Rule Delta にする
- ふだん `bye` と呼んでいるものがこのインスタンスである

### 4.5 旧版 7 境界ツールとの対応

旧版で具体化していた境界ツール群も、`R` の蒸留面として保存できる。

| ツール | $R$ の読み | 典型的に残す kernel |
|:---|:---|:---|
| `hermeneus_run` | $R_{\text{CCL}}$ | 検証結果と next action |
| `ask_with_tools` | $R_{\text{agent}}$ | TAINT 判定と逸脱警告 |
| `context_rot_distill` | $R_{\text{ROM}}$ | ROM 生成結果 |
| `periskope_research` | $R_{\text{research}}$ | 原典確認が必要な synthesis |
| `sekisho_gate` | $R_{\text{gate}}$ | gate 通過の SOURCE 記録 |
| `run_digestor` | $R_{\text{eat}}$ | 消化候補の束 |
| `hermeneus_execute` | $R_{\text{WF}}$ | WF 完了の belief receipt |

この表の意味は、道具名を列挙することではない。**どの実行結果も `R` を通った瞬間に kernel 化される**という構図を明示することにある。

## 5. 忘却率と Scale

忘却率の議論は数値競争ではない。どの Scale に合わせて bye したかを読むための指標である。

$$
\text{Forgetting Rate} = 1 - \frac{|\text{BeliefUpdate}|}{|\text{ExecutionResult}|}
$$

| Scale | 典型的な bye 出力 | 忘却率の目安 | 意味 |
|:---|:---|:---|:---|
| Task | Belief Update | 0.40-0.70 | 次の一手だけ残す |
| Slice | Fractal Summary | 0.70-0.90 | 契約と能力だけ残す |
| Session | Handoff / ROM | 0.80-0.95 | 固定点構造だけ残す |

### $\varepsilon$ との関係

$$
R \varepsilon \circ \eta R = \text{id}_R
$$

bye の粗視化が荒すぎると、次の boot で再構成できず $\varepsilon$ が破れる。逆に細かすぎると Context Rot を招く。したがって `R` の仕事は、**Scale に応じた fixed point を残すこと**に尽きる。

旧版の関心事だった「忘却が過剰か、過少か」という論点もここに含まれる。忘却が過剰なら再現性が落ち、過少なら prior が肥大化する。

## 6. source_label の決定規則

`R` は内容だけでなく、信頼度の地形も蒸留する。

```python
if verification and verification.get("verdict") == "PASS":
    source_label = "SOURCE"
elif exit_status == "success" and tool_name in DETERMINISTIC_TOOLS:
    source_label = "SOURCE"
elif tool_name in EXTERNAL_SYNTHESIS_TOOLS:
    source_label = "TAINT"
else:
    source_label = "WEAK_INPUT"
```

このラベルがないと、次の `L (boot)` が平坦な prior を読み込んでしまい、忘却の地形が失われる。

---
*Created: 2026-03-10*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
