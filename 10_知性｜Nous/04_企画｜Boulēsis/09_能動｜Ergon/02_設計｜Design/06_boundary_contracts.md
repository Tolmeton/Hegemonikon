# Ergon プロジェクト 設計文書 06

## ハーネス契約

本書は、随伴契約を**ハーネス契約**として再定式化する。中心命題は次である。

> **C 成分とは、LLM が環境と結ぶ契約面である。**

LLM は自由に候補を出してよい。しかし環境に出るときは、`C` が「どこまで通してよいか」を先に決めていなければならない。ハーネス契約とは、この `C` を中心に `E/M` を接続し、blanket 破りを防ぐ設計である。

## 1. $\eta$ 契約 (Unit: prediction error の測定)

$$
\eta: \text{Id}_{\text{Cog}} \Rightarrow R \circ L
$$

### 操作的定義

```text
Plan
  ↓ L (boot)
Task
  ↓ Execute
ExecutionResult
  ↓ R (bye)
BeliefUpdate

η(Plan) = Plan ⟼ BeliefUpdate
```

新体系では、この prediction error を `C/E/M` の 3 軸で測る。

| 軸 | 何がズレたとみなすか |
|:---|:---|
| **C** | 契約した禁止条件や safety class が崩れた |
| **E** | summary / schema / field が崩れた |
| **M** | Hook / test / validator が効かなかった |

prediction error は単なる失敗ログではない。**どの契約面が破れたかを示す観測量**である。

## 2. $\varepsilon$ 契約 (Counit: 蒸留の再構成可能性)

$$
\varepsilon: L \circ R \Rightarrow \text{Id}_{\text{Exec}}
$$

### 操作的定義

```text
ExecutionResult(O₁)
  ↓ R (bye)
BeliefUpdate(B)
  ↓ L (re-boot)
Task'
  ↓ Re-Execute
ExecutionResult(O₂)

ε(Exec) = diff(O₁, O₂)
```

ここで問うのは、同じ文字列の再生ではない。**同じ契約構造が再構成されるか**である。

旧版の精度定式化も保存する。

$$
\text{蒸留の精度} = 1 - | \varepsilon | / | O_1 |
$$

| 軸 | 再構成できるべきもの |
|:---|:---|
| **C** | 同じ禁止条件・権限境界・承認条件 |
| **E** | 同じ handoff schema・summary の意味核 |
| **M** | 同じ Hook / tool / test の効き方 |

## 3. C 成分は LLM と環境の契約である

`C` は「制約のメモ」ではない。`C` こそが、LLM が環境と接続する際に署名する契約である。

| 契約要素 | `C` が定める内容 | 破れたときの症状 |
|:---|:---|:---|
| capability | 何をしてよいか | 越権実行 |
| prohibition | 何をしてはならないか | blanket 破り |
| approval | どこで人間確認が必要か | 不可逆逸脱 |
| scope | どの path / tool / write 面まで許可するか | 無自覚な拡張 |

LLM はこの契約を自分で書き換えてはならない。契約変更は `L (boot)` の更新としてのみ行われるべきである。

## 4. 三角恒等式の操作的契約

### 恒等式 1: $(\varepsilon L) \circ (L \eta) = \text{id}_L$

**契約**:

> Plan を boot し、bye してから再 boot しても、最初と同じ Task family に戻ること

許容される差異:

- 文言の揺れ
- 非本質的な parameter の差

許容されない差異:

- tool の切替
- safety class の変化
- 不可逆境界の逸脱

### 恒等式 2: $(R \varepsilon) \circ (\eta R) = \text{id}_R$

**契約**:

> bye した summary を次の boot に渡して再実行し、さらに bye しても、同じ Belief kernel に戻ること

許容される差異:

- prose の言い換え
- ログ量の増減

許容されない差異:

- source_label の逆転
- confidence の崩落
- `C/E/M` のどれかの消失

## 5. 層混入 3 パターンへの防御

### パターン 1: $\mu \to \eta$ 直接 (Blanket 破り)

- 症状: LLM 推論がそのままファイル変更や外部副作用へ流れる
- 防御: tool filter、Hook、approval gate

```python
@dataclass
class ToolFilter:
    allowed_safety_classes: set[str]
```

### パターン 2: $a$ が $\mu$ を越権する

- 症状: Worker が設計判断まで自律決定する
- 防御: `constraint_kernel` を boot 時に固定し、子系はそれを超えて解釈しない

```python
class Task:
    deterministic: bool
```

### パターン 3: $s$ の精度未分類

- 症状: SOURCE と TAINT が混ざったまま次の boot に流れる
- 防御: `source_label` と `confidence` を bye 段階で必ず付与する

## 6. 透過度スケジュール

ハーネス契約は、透過度の動的制御として実装される。

| フェーズ | 許可する透過度 | 主な目的 |
|:---|:---|:---|
| 探索 | `read_only` | 観測を増やす |
| 実行 | `read_only + reversible` | 安全に前進する |
| 確定 | `read_only + reversible + irreversible` | 確定行為を通す |

Hook はこの表を prose で説明するためのものではない。**契約どおりに通す / 止める機構そのもの**である。

---
*Created: 2026-03-10*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
