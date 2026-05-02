# Skill / CCL Execution Contract

## Purpose

明示 skill invocation と明示 CCL expression を、雰囲気ガイドではなく実行契約として扱う。
Tolmetes が skill や CCL を明示した場合、Codex は protocol を勝手に圧縮・浅化・省略しない。

## Hard Contract

- 対象は **explicit invocation** のみ。
- explicit invocation とは、少なくとも次を含む。
  - `/ske`, `/ske+`, `/ske.struct` のような slash invocation
  - `[$u]`, `[$ene]` のような skill mention
  - `u で答えて`, `ske を使って` のような明示要求
  - `@plan`, `@search+`, `/ske>>/noe`, `C:{...}`, `F:[×N]{...}` のような明示 CCL expression
- explicit invocation では、その skill / workflow / macro の `SKILL.md`, `.agents/workflows/ccl-*.md`, `anti_skip`, `sel_enforcement`, `execution_contract` を **normative** として扱う。
- Tolmetes が省略や浅化を明示しない限り、Codex は次を行ってはならない。
  - depth downgrade
  - derivative の勝手な変更
  - required sections / phases / checkpoints / quality gates の省略
  - prose 要約への置換

## Default Enforcement

- `execution_contract` が未定義でも、explicit invocation は strict とみなす。
- default は次の通り。
  - `explicit_invocation = strict`
  - `implicit_trigger = flexible`
  - `fallback_behavior = declare_and_stop`
  - `default_depth = L2`
  - `macro_expansion = required`

## Runtime Enforcement Thresholds

- runtime enforcement の対象は **Hermeneus / CCL execution path** に限る。
- 単体 skill の一般チャット面は、v1 では主にこの文書契約で縛る。
- 閾値判定は **macro expansion 後の workflow invocation 数** で行う。
  - 派生記号 (`+`, `-`, `^`) は count に含めない
  - 同じ workflow の再出現は **重複込みで数える**
  - `@plan` などの macro は **展開後の実 chain 長** で判定する
- 発火条件:
  - `explicit single-skill` → `H1`
  - `expanded workflow count >= 2` → `H1 + H2 + H5`
  - `expanded workflow count >= 4` → `H1 + H2 + H5 + H3 + H4`

## H1-H5 Contract

- `H1 / preflight manifest`
  - explicit skill / explicit CCL では、実行前に `raw_expr`, `expanded_expr`, `workflow_count`, `enforcement_level`, `execution_manifest` を確定する
  - `execution_manifest` は最低限、workflow list, macro expansion, derivative, required_outputs, required_gates, interactive gate を含む
  - manifest を作れない場合は **`CCL CONTRACT BLOCKED`**
- `H2 / postflight validator`
  - 複数 workflow を含む CCL では、出力後に workflow-level validator を通す
  - 少なくとも次を検査する
    - native phase marker 欠落
    - required_outputs 欠落
    - interactive gate violation
    - 前段 workflow の責務混入
  - H2 は fail-closed。NG は completed 扱いにしない
- `H5 / contract trace`
  - 複数 workflow を含む CCL では、`expanded_expr`, `workflow_count`, `enforcement_level`, 各 workflow の `phase_status / gate_status / validation_status` を trace に残す
  - single-skill では user-visible trace を出さない
- `H4 / 3-phase runtime`
  - `expanded workflow count >= 4` では runtime を `plan -> execution -> verification` に分離する
  - verification を通っていない出力を completed と見なさない
- `H3 / no freeform completion`
  - `expanded workflow count >= 4` の CCL は freeform completion を認めない
  - executor を経由せず verification 不能な完了扱いをした場合は **`CCL CONTRACT BLOCKED`**

## Native Output Rule

- explicit invocation の出力は、**その skill / workflow の native phase structure を保持**しなければならない。
- native structure を守るとは、単に見出しを残すことではない。少なくとも次の 3 点を保存する。
  - **representation_role**: 各 phase が何の表現役割を担うか
    - 例: 前提棚卸し, 比較表, 収束命題, 棄却台帳, WM, 監査
  - **rejection_ledger**: 何を採らず、なぜ捨てたか
  - **carry-forward manifest**: 前 phase から何を受け取り、何を変換し、次 phase に何を持ち越すか
- 次を禁止する。
  - phase 見出しを消して prose 1-2 段落に畳む
  - phase 固有の検査項目を、結論だけに要約する
  - `/bou` の P-0〜P-5 を「優先順位はこれです」の1発回答に置換する
  - `/ene` の手順を `/bou` の結果であるかのように混ぜる
  - 各 phase が本来持つ表現役割を失わせ、全 phase を均質な prose にする
  - 棄却があったのに rejection_ledger を消す
  - 次 phase が依存するラベル・候補・中間結論を carry-forward manifest なしに暗黙継承させる
- skill が表形式、スコア、チェックポイント、WQS、ρ、6W3H、監査ログなどを要求する場合、それらは native に出す。概念説明で代用しない。

## Phase State Continuity Rule

- explicit invocation では、phase は独立した段落ではなく **状態遷移** として扱う。
- 各 phase は必要に応じて、少なくとも次のどれかを明示しなければならない。
  - `受け取り:` / `carry-forward`
  - `変換:` / `transformed`
  - `持ち越し:` / `to_next`
  - `棄却:` / `rejection_ledger`
- 次を禁止する。
  - P-1 で立てた候補が P-2 で何の説明もなく消える
  - P-2 の中間結論が P-3 に継承される際、何を保持したか見えない
  - final だけ読むと一見自然だが、phase 間の受け渡しが観測不能
- 目的は raw chain-of-thought の露出ではなく、**Tolmetes が phase 間の変換を追跡できる最小限の manifest** を残すこと。

## Implementation Report Renderer Rule

実装系 skill の報告は、executor のメモではなく **reader-facing artifact** として出す。
正確さを落とさず scan path を短くすることを目的とする。

`/ene`, `/tek`, 修正報告, 検証報告, コミット提案を含む final では、
`.agents/rules/implementation-report-renderer-policy.md` を renderer 正本として扱う。

実装報告では次を守る。

- 成果核は短い段落で固定する
- 変更面は表で分離する
- 検証は fenced code block と短い判定で分離する
- 復元は rollback 段落で出す
- raw absolute path は annex や表セルに隔離する

次を禁止する。

- 実装報告全体を unordered list で運ぶこと
- phase を残しつつ、各 phase の本文を同じ bullet で均質化すること
- 長い絶対パスを reasoning 本文の中に連打すること
- テスト結果を散文の途中に埋め込み、検証面を分離しないこと

Tolmetes が bullet overuse を明示的に指摘した場合、その report では unordered list を禁止とみなす。

## Dialogue Externalization Rule

- explicit invocation でも、親原理は **共同思考性** である。
- native protocol を守るだけでなく、**Tolmetes が追跡・修正・合意できるだけの認識状態を隠さない**。
- 共有項目は checklist の本体ではなく、共同思考性の観測可能な痕跡として扱う。
  - 現在地
  - operative assumption
  - evaluation basis
  - discarded branch / non-selected option
  - uncertainty / missing evidence
  - next step
- 次を禁止する。
  - phase は出すが、なぜその phase 判定になったかを隠す
  - 結論だけ出し、棄却や迷いを消す
  - `/ske` や `/sag` で候補や棄却理由を圧縮して一本道に見せる
  - `/ene` や CCL 実行で、現在どこまで進んだかを伏せて「完了」だけ返す
- 目的は raw thought dump ではなく、**共同思考が成立するだけの working state を共有すること** である。

## Interactive Gate Rule

- skill / workflow が **「ここで Creator の反応を待つ」** と定義している場合、その待機点を飛び越えてはならない。
- 例:
  - `/bou` は P-0 後に対話必須なら、P-0 を native 形式で出して停止する
  - 反応未取得のまま P-1〜P-5 を生成して「結論」を作るのは禁止
- required input が未取得の phase に進めない場合、軽量版へ降格せず **`SKILL CONTRACT BLOCKED` / `CCL CONTRACT BLOCKED`** を返す。

## Non-Compliant Pattern Examples

- `/bou` を要求されたのに、望み 3-5 個の提示、5 Whys、衝動スコア、実現可能性 4象限を出さず、
  「最優先はXです。次は1,2,3です」とだけ返す
  - 判定: **非準拠**
  - 理由: native phase collapse + `/ene` への責務混入
- 明示 skill invocation に対して、`SKILL.md` の出力形式を使わず「要するに」「短く言うと」で prose 要約にする
  - 判定: **非準拠**
  - 理由: prose 要約への置換
- 対話必須 skill で Creator の返答待ちを省略し、後続 phase を埋める
  - 判定: **非準拠**
  - 理由: interactive gate violation

## Blocked Behavior

full protocol を守れない場合、Codex は軽量版へ黙って降格してはならない。
skill invocation は `SKILL CONTRACT BLOCKED`、CCL invocation は `CCL CONTRACT BLOCKED` で停止する。

```markdown
SKILL CONTRACT BLOCKED / CCL CONTRACT BLOCKED
- requested_skill: ...
- requested_depth_or_derivative: ...
- unmet_requirements: ...
- blocking_reason: ...
- safe_next_step: ...
```

ここで `safe_next_step` は、Tolmetes が省略を許可するか、制約を外すか、別 skill へ切り替えるかの決定面だけを示す。

## Scope

- explicit invocation: strict
- implicit trigger: flexible

implicit trigger にも同じ厳格さを自動適用しない。
v1 は、明示 invocation の再発防止だけに集中する。
