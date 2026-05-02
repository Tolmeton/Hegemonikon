# Hook Runtime Layers — H2/H4/H5 三層設計メモ

> **位置付け**: [../README.md](../README.md) で確定した「hooks = layered bus」を、Organon の runtime 境界へ具体化するための設計補遺。
>
> **上位台帳**: [../README.md](../README.md) の Hooks 定義面, [sensor_triad_formal.md](./sensor_triad_formal.md) §3.2.1 の hooks 定義域制約。
>
> **非同一性**: 本文書の H2/H4/H5 は、README の Layer α/β/γ (48 evaluator / X dispatcher / Q scheduler) と別である。こちらは **hook 側の ingress/control/observation stack**、あちらは **Organon 本体の evaluator/dispatcher/scheduler stack** である。
>
> **1文要約**: H2 が raw prompt/session を薄い operational contract に整え、H4 が hook event を `48-seed / gate-only / Q-window / δ-anchor` に配線し、H5 がその後段で being/drift を観測する。
>
> **確信度**: [確信 87%] H4 主軸は README と `/sag.strict` から演繹的 (Level B)。H5 の実測精度と alert rate は pilot が必要 (Level C)。

---

## §1 目的

Claude Code hooks を「周辺自動化の寄せ集め」ではなく、Organon にとっての **outer control plane** として扱うため、hook 側の責務分界を 3 層に固定する。

ここで固定したいことは 2 つだけである。

1. hooks は **universal bus ではない**
2. それでも hooks は **runtime の入口と境界** を担当する

この 2 条件を同時に満たすには、hook 面を 1 枚岩にせず、`H2 → H4 → H5` の三層として読む必要がある。

---

## §2 三層の骨格

| 層 | 仮説 | 役割 | 入力 | 出力 | 失敗像 |
|---|---|---|---|---|---|
| **H2** | Prompt/Session Compiler | raw input を最小限の operational contract に整える | SessionStart, UserPromptSubmit, CwdChanged | Contract | contract が厚くなり会話を硬直化 |
| **H4** | Organon Hook Kernel | hook event を分類・配線する outer control plane | hook event stream 全体 | `48-seed`, `gate-only`, `Q-window`, `δ-anchor` | hooks を universal bus 扱いして責務が崩壊 |
| **H5** | Being Sensor Mesh | drift / being を観測する後段 sensor plane | `Q-window`, `δ-anchor`, Text/Tool/δ 由来 signal | Drift signal, anomaly, recency state | signal 過多で alert fatigue |

### §2.1 H2 は主役ではなく前段

H2 は「Prompt/Session Compiler」という名前だが、Organon の identity はここにない。
ここでやるのは、自由な対話を型で縛ることではなく、**後段の H4 が最低限扱える形に整えること**だけである。

たとえば H2 は次のような「薄い」情報だけを持てばよい。

- 今セッションの主題は何か
- watch すべき path / worktree / phase はあるか
- 高リスク操作が含まれるか
- H4 に渡す authority/gate の初期条件は何か

逆に、H2 が 48 分類や X/Q scheduler の本体まで持ち始めると、H4/H5 を食い潰す。

### §2.2 H4 は主軸

H4 は hooks の**意味付けを独占**しない。やるのは意味の確定ではなく、**event の配線**である。

このとき H4 の一次出力は README と `sensor_triad_formal.md` に揃えて、次の 4 種だけに制限する。

| 出力型 | 意味 | 後段 |
|---|---|---|
| **48-seed** | doing 面の粗い一次射影 | Tool Sensor / evaluator |
| **gate-only** | authority / permission / policy 制御 | harness gate |
| **Q-window** | 時間的循環や変化の観測窓 | scheduler / recurrence logic |
| **δ-anchor** | drift 解析の時系列アンカー | Daimonion δ / H5 |

つまり H4 は「何が起きたか」を完全に理解する層ではなく、「この event は次にどの面へ渡すべきか」を切る **traffic controller** である。

### §2.3 H5 は hooks の外に少しはみ出す

H5 は hook そのものではない。hook は H5 にとって**接地アンカー**ではあっても、being の観測器そのものではない。

H5 の役割は、次のような「doing だけでは見えない変化」を扱うことにある。

- 作業が止まっているのに drift だけが増えている
- FileChanged が繰り返されるが、意味のある収束が起きていない
- Notification / StopFailure / TeammateIdle が示す recency anomaly
- δ が拾う `[th]`, `[ph]`, `[an]`, `[pl]` の未言語化

H5 は therefore `sensor_triad_formal.md` の Tool/Text/Being 3 sensor と接続される。

---

## §3 明示的な非目標

三層化にあたり、先に捨てるものを固定する。

### §3.1 H1 は独立戦略として残さない

`Policy Mesh` は H4 の `gate-only` 断面で十分である。独立主張として持つと、hooks の主役を再び gate に戻してしまう。

### §3.2 H3 は現時点で採らない

`Versioned Hook Pack` は発想としては魅力があるが、現在の `~/.claude/settings.json` 中心の managed hook 運用と ownership 競合を起こす。今は runtime 境界を固める方が先である。

### §3.3 hooks 単体で 48 / X / Q / δ を完結させない

これは README で既に出ているが、ここで再固定する。

- hooks 単体では **fine-grained 48** は確定しない
- hooks 単体では **X-series** は確定しない
- hooks 単体では **Q-series の本体** は確定しない
- hooks 単体では **being** は観測できない

ゆえに H4 は kernel ではあるが、**全知の kernel ではない**。

---

## §4 現在の hook 面への写像

2026-04-21 時点の `~/.claude/settings.json` では、少なくとも次の event surface が有効である。

- `SessionStart`
- `UserPromptSubmit`
- `CwdChanged`
- `PreToolUse`
- `PermissionRequest`
- `PostToolUse`
- `PostToolUseFailure`
- `FileChanged`
- `Notification`
- `PreCompact`
- `Stop`
- `StopFailure`
- `TeammateIdle`

この surface を H2/H4/H5 に写像すると次のようになる。

| event | 主担当層 | 一次出力 | 意味 |
|---|---|---|---|
| `SessionStart` | H2 | Contract | session の初期条件を整える |
| `UserPromptSubmit` | H2 | Contract update | 今ターンの task intent を薄く確定する |
| `CwdChanged` | H2 | Contract update / `Q-window` | 作業文脈の切替を contract と時間窓の両面で記録 |
| `PreToolUse` | H4 | `gate-only` | 実行前の authority / policy 分岐 |
| `PermissionRequest` | H4 | `gate-only` | 明示許可面の制御 |
| `PostToolUse` | H4 | `48-seed` | doing 面の粗い一次射影 |
| `PostToolUseFailure` | H4 | `48-seed` + `δ-anchor` | failure を seed と drift 両面へ渡す |
| `Stop` | H4 | `48-seed` + `Q-window` | ターン終了の結果面を記録 |
| `StopFailure` | H4/H5 | `Q-window` + `δ-anchor` | failure recency の強いアンカー |
| `FileChanged` | H5 | `Q-window` | 変化の反復と収束不足を観測する窓 |
| `Notification` | H5 | `δ-anchor` | 外部割込・状態遷移の接地 |
| `TeammateIdle` | H5 | `δ-anchor` | idle / stuck の recency anchor |
| `PreCompact` | H5 | `Q-window` | compact 前後の drift と loss を比較する窓 |

### §4.1 reference surface に残す event

hooks reference 上は `TaskCreated`, `TaskCompleted`, `SubagentStart`, `SubagentStop` も event surface にある。
現行 HGK で未使用でも、設計上は reserved slot として持っておく価値が高い。

| reference event | 想定層 | 役割 |
|---|---|---|
| `TaskCreated` | H4/H5 | scheduler 起点の `Q-window` を開く |
| `TaskCompleted` | H5 | 収束成功/失敗の recency 比較 |
| `SubagentStart` | H4 | outer control plane 上の delegation 入口 |
| `SubagentStop` | H4/H5 | child run の終端 anchor |

---

## §5 三層の I/O 契約

### §5.1 H2 output: Operational Contract

H2 の出力は、大げさな AST ではなく、後段が読める最小限の envelope とする。

```text
OperationalContract
- session_id
- turn_id
- task_intent
- risk_level
- working_scope
- watch_paths
- authority_profile
- observation_budget
```

ここで重要なのは `task_intent` よりも `working_scope` と `observation_budget` である。
H4/H5 は「何をするか」だけでなく、「どこを見続けるべきか」を受け取る必要があるからである。

### §5.2 H4 output: Hook Envelope

H4 は各 hook event を次のような envelope に正規化する。

```text
HookEnvelope
- event_name
- provenance
- route_kind        # 48-seed / gate-only / Q-window / δ-anchor
- payload
- contract_ref
- next_sink
```

`next_sink` の例:

- `tool_sensor`
- `harness_gate`
- `q_scheduler`
- `daimonion_delta`
- `audit_log`

### §5.3 H5 output: Drift Signal

H5 の出力は block 判定そのものではなく、**drift を後段に見せる signal** である。

```text
DriftSignal
- signal_id
- source_mix        # FileChanged / Idle / StopFailure / δ ...
- axis              # recency / repetition / avoidance / stall
- severity
- evidence
- suggested_sink
```

`suggested_sink` は直ちに block するとは限らない。初期段階では次の 3 段階で十分である。

- `info`
- `soft_warning`
- `route_to_delta`

---

## §6 3 層と Organon 本体の接続

三層は Organon 本体 (Layer α/β/γ) の手前にいる。

| hook 側 | 本体側 | 接続の意味 |
|---|---|---|
| **H2** | Layer α/β/γ 共通 | runtime に入る前の task/authority/observation 条件を揃える |
| **H4** | Layer α, β, γ への配線 | event を seed / gate / time / anchor に仕分ける |
| **H5** | Layer γ + δ + Sensor Triad | recurrence / drift / being を本体へ返す |

図にすると次の順で読むとよい。

```text
raw prompt/session
  -> H2 thin compile
  -> H4 hook kernel
     -> 48-seed  -> Layer α / Tool Sensor
     -> gate-only -> harness gate
     -> Q-window -> Layer γ / recurrence
     -> δ-anchor -> H5 / Daimonion δ
  -> H5 being sensor mesh
     -> DriftSignal
```

ここで `Layer α/β/γ` は Organon の本体であり、H2/H4/H5 はその**前室と壁面**である。

---

## §7 最小実装順序

### §7.1 Step A: H2 を薄く作る

最初にやるべきは H2 の巨大化ではない。`SessionStart` と `UserPromptSubmit` を使い、最低限の `OperationalContract` を jsonl / envelope として残すだけでよい。

この段階では次の 4 field だけでも開始できる。

- `task_intent`
- `risk_level`
- `working_scope`
- `watch_paths`

### §7.2 Step B: H4 route table を固定する

次に、現行 hook script 群を `route_kind` で読み直す。
関心は script の中身より、**この event はどの面へ流すべきか** である。

この段階でまず固定すべきなのは次の 4 ルートである。

1. `PreToolUse` / `PermissionRequest` -> `gate-only`
2. `PostToolUse` / `Stop` -> `48-seed`
3. `FileChanged` / `PreCompact` -> `Q-window`
4. `StopFailure` / `TeammateIdle` / `Notification` -> `δ-anchor`

### §7.3 Step C: H5 を sensor triad に接続する

最後に H5 を `sensor_triad_formal.md` の Tool/Text/Being 3 sensor と接続する。

初期 PoC の問いは単純でよい。

- `FileChanged` が増えているのに `TaskCompleted` が増えないか
- `TeammateIdle` の直後に `[ph]` / `[th]` 系 drift が増えるか
- `StopFailure` は次ターンの回避行動と相関するか

H5 は最初から万能である必要はない。むしろ **recency / repetition / stall** の 3 軸に絞った方がよい。

---

## §8 開いた論点

1. **H2 の薄さをどこで止めるか**
   contract を厚くしすぎると prompt runtime を食う。`working_scope` 以上を H2 に持たせるかは再審が必要。

2. **H5 の signal を誰が最終判断するか**
   H5 は drift を出すだけに留めるか、soft gate まで持つか。初期段階は `route_to_delta` までが安全。

3. **永続化面を jsonl で止めるか**
   三層とも軽量に始めるなら jsonl で十分だが、Wave 3 以降は DuckDB/Parquet の方が recency 解析に向く。

4. **Task 系 event をいつ local hook 面へ昇格させるか**
   reference surface にはあるが、現行 HGK では未使用。H5 PoC の後に導入判断するのが妥当。

---

## §9 決定核

- H2 は前段補助であり、主役ではない
- H4 は hooks の主軸であり、event の意味確定ではなく配線を担う
- H5 は hooks の外側にはみ出しつつ、being/drift を観測する
- よって Organon における hooks 活用は、**H2 で薄く整え、H4 で配線し、H5 で drift を読む** という三層で固定する

この読み方なら、README の「hooks は layered bus」という命題と、`sensor_triad_formal.md` の「hooks は universal bus ではない」という制約が両立する。
