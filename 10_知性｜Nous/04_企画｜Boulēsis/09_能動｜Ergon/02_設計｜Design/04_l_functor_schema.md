# Ergon プロジェクト 設計文書 04

## L (boot) 関手スキーマ

本書は、左随伴 `L` を**boot そのもの**として再定義する。`L` は Plan を Task に変換する抽象写像ではなく、**忘却の透過度を決めながら実行面を立ち上げる boot 関手**である。

## 1. 設計原理

`L: \text{Cog} \to \text{Exec}` は左随伴である。ハーネス設計学では、これを次のように読む。

$$
L: \text{Cog} \to \text{Exec}
$$

> **L = boot**

boot の本質は「全部をロードすること」ではない。必要な `C/E/M` だけを濃く通し、残りは忘れさせることにある。Markov blanket は壁ではなく**選択的透過膜**であり、`L` はその透過度を決める。

| safety_class | 何を意味するか | 典型例 |
|:---|:---|:---|
| `read_only` | 観測だけを許す | search, read, inspect |
| `reversible` | 戻せる副作用だけ許す | file edit, git diff, temp write |
| `irreversible` | 確認付きでしか通さない | publish, deploy, destructive write |

## 2. Plan 型 ($L$ の入力)

```python
@dataclass
class Plan:
    intent: str
    """何を達成したいか。自然言語でも CCL でもよい。"""

    context: str
    """boot 対象となる局所コンテキスト。要約よりも kernel を優先する。"""

    constraint_kernel: list[str]
    """C 軸。禁止条件、守るべき Nomoi、許容された capability。"""

    encoding_kernel: list[str]
    """E 軸。返答形式、schema、summary の器。"""

    mechanism_kernel: list[str]
    """M 軸。Hook、validator、tool contract、test。"""

    source_label: Literal["SOURCE", "TAINT", "WEAK_INPUT"] = "TAINT"
    depth: Literal["L0", "L1", "L2", "L3"] = "L2"
    confidence_threshold: float = 0.6
```

この型の要点は、旧来の `intent/context/depth` を残しつつ、boot で透過させる中身を `C/E/M` に分解した点にある。

## 3. Task 型 ($L$ の出力)

```python
@dataclass
class Task:
    tool_name: str
    parameters: dict[str, Any]

    safety_class: Literal["read_only", "reversible", "irreversible"]
    deterministic: bool

    boot_scope: Literal["task", "slice", "session", "child_blanket"]
    """どのスケールで boot されたか。"""

    plan_id: str
    expected_side_effects: list[str]
```

`Task` は「LLM がやること」のメモではない。**どの制約核が、どの scope で、どの tool に落ちたか**を記録する boot の生成物である。

## 4. 代表的な $L$ インスタンス

### 4.1 $L_{\text{task}}$

- `intent` を単一 task に落とす最小の boot
- 例: `hermeneus_run`, `periskope_search`

### 4.2 $L_{\text{slice}}$

- 複数 task を同じ `C/E/M` 束で展開する boot
- 例: UI と API と test を同時に触る修正

### 4.3 $L_{\text{session}} = \text{boot}$

- Rule / ROM / Handoff をセッション全体へロードする
- ふだん `boot` と呼んでいるものがこのインスタンスである

### 4.4 $L_{\text{isolate}}$

- 親 blanket から子 blanket を生成する boot
- サブエージェント委譲はこの型に属する

### 4.5 7 境界ツールへの対応

旧版で保持していた境界ツール群も、`L` の具体インスタンスとしてそのまま読める。

| ツール | $L$ の読み | boot の焦点 |
|:---|:---|:---|
| `hermeneus_run` | $L_{\text{CCL}}$ | 制約つき CCL 実行 |
| `hermeneus_execute` | $L_{\text{WF}}$ | WF 単位の実行面展開 |
| `ask_with_tools` | $L_{\text{agent}}$ | 高リスクな child blanket boot |
| `context_rot_distill` | $L_{\text{ROM}}$ | ROM 生成のための局所 boot |
| `periskope_research` | $L_{\text{research}}$ | 外部探索の boot |
| `run_digestor` | $L_{\text{eat}}$ | 消化候補生成の boot |
| `sekisho_gate` | $L_{\text{gate}}$ | 境界通過判定の boot |

とくに `ask_with_tools` は最大リスク面であり、旧版の安全性議論どおり `safety_class` によるフィルタを要求する。

## 5. 普遍性の読み替え

旧文書では「任意の Plan に対して Task が存在する」という自由関手的説明をしていた。新しい読みでは、

- `L` は Plan をそのまま環境へ投げない
- `L` は Plan を、**透過度・決定性・boot scope が明示された Task** に落とす
- `L` の普遍性とは、**どの忘却を伴って実行面を立ち上げるかを一意に定める能力**である

以上が、旧来の自由関手的説明を boot 関手として読み替えたときの核心である。

### EFE 最小化との対応

旧版の EFE 定式化もそのまま保存できる。

$$
\text{EFE}(a) =
\underbrace{-\text{epistemic value}}_{\text{探索: } \text{safety\_class} \in \{\text{read\_only}\}}
+
\underbrace{-\text{pragmatic value}}_{\text{実行: } \text{safety\_class} \in \{\text{reversible}, \text{irreversible}\}}
$$

`L` の `safety_class` 分類は、この 2 項分解をハーネスの透過度制御として実装したものである。

## 6. 設計上の帰結

- `L` は Plan のコピーではない。**Plan を局所 boot する関手**である。
- `L` の品質は、載せた情報量ではなく、どれだけ鋭く `C/E/M` を選んだかで決まる。
- Hook や tool filter は `L` の外の補助物ではない。**boot が持ち込む mechanism kernel の一部**である。

---
*Created: 2026-03-10*
*Refreshed: 2026-04-13 — ハーネス設計学への転換*
