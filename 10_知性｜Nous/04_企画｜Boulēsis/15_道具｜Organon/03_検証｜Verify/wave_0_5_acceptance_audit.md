# Wave 0.5 Acceptance Audit

> **位置付け**: Organon Wave 0.5 の検収レポート初版。design 正本 (`02_設計｜Design/organon_kernel_contract.md`) の §7 Acceptance Criteria A1-A7 と、現実装 (`mekhane/mcp/`, `mekhane/organon/`) の照合。
>
> **読者**: Tolmetes (advisor 出力としての判断面提示用)。
>
> **上位台帳**:
> - [../README.md](../README.md) §STATUS
> - [../02_設計｜Design/organon_kernel_contract.md](../02_設計｜Design/organon_kernel_contract.md) §7 (A1-A7)
> - [../04_実装｜Impl/01_roadmap_v0.1.md](../04_実装｜Impl/01_roadmap_v0.1.md) §6 (現在地)
>
> **照合対象実装**:
> - `mekhane/mcp/depth_resolver.py`
> - `mekhane/mcp/harness_gate.py`
> - `mekhane/mcp/harness_map.yaml`
> - `mekhane/organon/__init__.py`
> - `mekhane/organon/observe.py`
> - `mekhane/organon/sensor_reading.py`
> - `mekhane/organon/diagnostics.py`
> - `mekhane/organon/text_sensor.py`
> - `mekhane/organon/tool_sensor.py`
> - `mekhane/organon/tool_sensor_adapter.py`
>
> **確信度**: [推定 80%] symbol 存在と signature 整合は確認済み。runtime 動作 (apply の no-op、ObservationAnchor の post-hoc 接続) は smoke test 未実施のため断定しない。

---

## §0 結論サマリ

| ID | 内容 | 判定 | 根拠 |
|---|---|---|---|
| A1 | `_depth` explicit input が期待 depth に解決される | ✅ contract 整備 / smoke 未実施 | `depth_resolver.py:_ARG_EXPLICIT="_depth"` + `resolve_depth` |
| A2 | CCL modifier `--/-/+/++` が L0-L4 に対応 | ✅ 完全一致 | `_MODIFIER_TO_DEPTH` (`++→L4, +→L3, ""→L2, -→L1, --→L0`) |
| A3 | HarnessProfile が 7 key を持つ | ✅ 完全一致 | `_PROFILE_KEYS = (alpha, beta, gamma, periskope, rom_persist, subagent_allowed, bypass_llm_only)` |
| A4 | `HGK_HARNESS_GATE=disabled` で `apply()` が no-op | ✅ env key 整備 / smoke 未実施 | `_DISABLE_ENV_KEY="HGK_HARNESS_GATE"` + `_DISABLE_VALUE="disabled"` |
| **A5** | observe adapter が ObservationAnchor を作る | ✅ **達成 (v0.3 update)** | `mekhane/organon/anchor.py` 新設 (Composer 2 実装、184 行)。`ObservationAnchor` は frozen=True / slots=True で 9 fields (`invocation_id, session_id, depth, profile, delta_source, delta_scores_ref, alerts_ref, timestamp, confidence`) を持つ。import smoke / dataclass introspection で確認済 |
| **A6** | ObservationAnchor は δ score 即時計算を要求しない | ✅ **達成 (v0.3 update)** | `observe_anchor` は `delta_scores_provider` を closure で lazy 化し、`delta_scores_ref()` を明示呼出するまで provider を invoke しない。test_anchor.py の `test_observe_anchor_does_not_compute_delta_immediately` で確認 (Composer 2 報告: 3 passed) |
| A7 | README / meta / roadmap が design note を参照 | ✅ 達成 | README L96-100 で `organon_kernel_contract.md` 参照確認 |

**核所見 (v0.3 update)**: A5/A6 は案 I (両系統別 symbol で共存) を採用し、`mekhane/organon/anchor.py` に `ObservationAnchor` + `observe_anchor` を新設したことで達成。既存 `observe.py` (sensor_triad orchestrator) は無変更。Wave 0.5 acceptance 7 件すべて closed-out。

---

## §1 観測面の乖離 (核所見)

### §1.1 二系統が同じ symbol path に重なっている

| 軸 | Wave 0.5 §5.2 で予約された adapter | 現実装 `mekhane/organon/observe.py` |
|---|---|---|
| 設計起点 | `02_設計｜Design/organon_kernel_contract.md` §5.2 | `02_設計｜Design/sensor_triad_formal.md` §3-§4 |
| 入力 | `invocation, depth, profile, session_id` | `assistant_text, session_id, tool_log_path, tool_log_dir, strict` |
| 出力型 | `ObservationAnchor` (9 fields) | `SessionObservation` (4 fields) |
| 粒度 | invocation-local anchor | session-aggregate observation |
| depth / profile 受領 | 必須 (Gate→Obs sequence) | 受領なし |
| Daimonion δ 接続 | `delta_source / delta_scores_ref / alerts_ref` で post-hoc 参照 | 接続なし。Being Sensor 自体が未実装 |
| 主目的 | Wave 1 `CognitiveOp.observe()` の adapter contract を `compute_delta_scores(session_id)` に橋渡しする | Tool/Text Sensor の MECE 観測 + Pattern 3 (表層語彙のみ) 等の捏造検出 |
| 検収面 | A5/A6 (anchor 形式と非即時性) | sensor_triad_formal.md §7 Diagnostic Matrix の R1-R6 |

### §1.2 なぜ衝突したか (推定)

1. `sensor_triad_formal.md` (2026-04-20 v0.1) は Layer α に **observe() 面** を具体化する設計として書かれており、`observe()` という symbol を Tool/Text/Being Sensor の orchestrator として予約していた。
2. `organon_kernel_contract.md` (2026-04-24) が後発で、Wave 0.5 §5.2 で `observe(invocation, depth, profile, session_id) -> ObservationAnchor` を adapter contract として予約した。両者は粒度も目的も違うが、symbol 名 `observe` が衝突した。
3. Codex は `sensor_triad_formal.md` を読んで `observe.py` を 2026-04-24 17:35 に着手 (kernel_contract.md の同日 18:51 改訂より早い)。Codex の実装は sensor_triad 系列に対して忠実で、瑕疵ではない。
4. 結果として、`mekhane/organon/observe.py` は **sensor_triad の orchestrator** になり、Wave 0.5 §5.2 が予約した **invocation-local adapter** は code 上に未着地のまま残った。

### §1.3 [SOURCE] ラベル付きの観測

- [SOURCE: `mekhane/organon/observe.py:1-66`] `observe_session(assistant_text, ...) -> SessionObservation`。`SessionObservation` は `(session_id, tool_reading, text_reading, findings)` の 4 field
- [SOURCE: `02_設計｜Design/organon_kernel_contract.md:122-141`] Wave 0.5 §5.2 で予約された `observe(invocation, depth, profile, session_id) -> ObservationAnchor`。`ObservationAnchor` は `(invocation_id, session_id, depth, profile, delta_source, delta_scores_ref, alerts_ref, timestamp, confidence)` の 9 field
- [SOURCE: `02_設計｜Design/sensor_triad_formal.md:51-58`] Tool / Text / Being の 3 sensor を 48 座標に射影する設計。Being Sensor は `mekhane/sympatheia/daimonion_delta.py` (既存 981 行) を再利用すると明記
- [SOURCE: `mekhane/organon/__init__.py:5-22`] 公開 symbol に `ObservationAnchor` は無く、`SessionObservation` のみ

---

## §2 入出力面 (A1-A4) の照合

### §2.1 A1: explicit `_depth` 解決

[SOURCE: `mekhane/mcp/depth_resolver.py:54`] `_ARG_EXPLICIT = "_depth"` で invocation 引数 key を予約。同 file に `resolve_depth(arguments)` が定義されている。優先順位 1 (`_depth`) を最優先で読む実装と読める。

判定: ✅ contract 整備 / smoke test (`_depth=L3` を渡して `HarnessDepth.L3` が返る) は未実施。

### §2.2 A2: CCL modifier 対応

[SOURCE: `mekhane/mcp/depth_resolver.py:42-48`]
```
_MODIFIER_TO_DEPTH = {
    "++": HarnessDepth.L4,
    "+":  HarnessDepth.L3,
    "":   HarnessDepth.L2,
    "-":  HarnessDepth.L1,
    "--": HarnessDepth.L0,
}
```

design §3.2 と完全一致。`depth_from_ccl_modifier` は `"++/--"` を `"+/-"` より先に match する longest-match 実装。判定: ✅。

### §2.3 A3: HarnessProfile 7 key

[SOURCE: `mekhane/mcp/harness_gate.py:57-65`]
```
_PROFILE_KEYS = (
    "alpha", "beta", "gamma",
    "periskope", "rom_persist",
    "subagent_allowed", "bypass_llm_only",
)
```

design §4.2 の 7 key と完全一致。判定: ✅。

### §2.4 A4: HGK_HARNESS_GATE=disabled で no-op

[SOURCE: `mekhane/mcp/harness_gate.py:53-54`] `_DISABLE_ENV_KEY = "HGK_HARNESS_GATE"`, `_DISABLE_VALUE = "disabled"`。同 file に `def apply(...)` (line 204) と `def is_bypass(profile)` (line 279) が存在。docstring に「HGK_HARNESS_GATE=disabled env var -> apply() becomes a no-op」(line 25) と明記。

判定: ✅ contract 整備 / smoke test (`os.environ["HGK_HARNESS_GATE"]="disabled"` 状態で `apply` が flag を変更しない) は未実施。

### §2.5 A7: docs cross-reference

[SOURCE: `../README.md:96`] organon_kernel_contract.md を Wave 0.5 正本として参照。
[SOURCE: `../04_実装｜Impl/01_roadmap_v0.1.md:62`] 同じく参照。
[SOURCE: `../meta.md`] 未読。次セッションで確認候補。

判定: ✅ (README + roadmap で確認、meta.md は未読)。

---

## §3 観測面の乖離詳細 (A5 / A6)

### §3.1 ObservationAnchor 型の不在

[SOURCE: `mekhane/organon/__init__.py`] 公開 symbol を grep:
- 含まれる: `SensorReading`, `SessionObservation`, `LayerAlphaSensorReading`, `LayerAlphaSeed`, `ToolSeedReading`, `ToolSensorSnapshot`, `DiagnosticFinding`
- 含まれない: `ObservationAnchor`

[SOURCE: `rg "ObservationAnchor" 20_機構｜Mekhane/_src｜ソースコード` 2026-05-02 実行] ヒット 0 件。`ObservationAnchor` 文字列は `mekhane/_src/` 配下のいずれの `.py` にも存在しない。repo-wide では `Organon/{meta,README,roadmap,audit,kernel_contract}.md` と handoff jsonl 数件のみで、すべて docs 側。

design §5.2 は ObservationAnchor の 9 field (invocation_id / session_id / depth / profile / delta_source / delta_scores_ref / alerts_ref / timestamp / confidence) を要求するが、現 code は 4 field の SessionObservation のみ提供。

### §3.2 depth / profile が観測層に届いていない

design §6 の Mermaid sequence は `Gate-->>Obs: depth + profile + session_id` と書かれているが、`observe_session` の signature は `assistant_text, session_id, timestamp, tool_log_path, tool_log_dir, strict` で **depth も profile も受け取っていない**。

帰結: 同じ session_id 内で異なる harness depth (L0 と L3) で 2 回 invocation した場合、現 SessionObservation はそれを区別できない。Wave 0.5 §5.2 が ObservationAnchor で区別したかった粒度が落ちている。

### §3.3 Daimonion δ への post-hoc 接続が無い

design §5.2 の `delta_source = "posthoc_e_proxy"` / `delta_scores_ref` / `alerts_ref` は、`mekhane/sympatheia/daimonion_delta.py` の `compute_delta_scores(session_id)` への lazy reference を ObservationAnchor 内に埋め込む契約だった。

現実装は `daimonion_delta.py` を一切 import していない。観測 orchestrator (`observe_session`) と Being Sensor (Daimonion δ) は **設計上 §3.2 で「Being Sensor = δ 既存 981 行を再利用」と書かれているが、実装上はまだ繋がっていない**。

### §3.4 これは実装不足ではなく設計衝突

Codex は sensor_triad_formal.md を読んで実装した。それは正しい。瑕疵は実装側ではなく、**`observe.py` という symbol path が二系統 (Wave 0.5 §5.2 / sensor_triad_formal.md) に同時予約された design 側**にある。

---

## §4 判断面 (Tolmetes 選択)

### 案 I (advisor default 推し): **両系統を別 symbol で共存させる**

- 現 `mekhane/organon/observe.py` の `observe_session` / `SessionObservation` を **Sensor Triad orchestrator** として保持
- Wave 0.5 §5.2 が要求する invocation-local adapter を `mekhane/organon/anchor.py` に新設し、`ObservationAnchor` 型と `observe(invocation, depth, profile, session_id) -> ObservationAnchor` を実装
- `ObservationAnchor.delta_scores_ref` は `daimonion_delta.compute_delta_scores(session_id)` への lazy callable で接続
- `SessionObservation` と `ObservationAnchor` は同一 session_id を key に **後で join できる** ように設計 (両者を破壊的に統合しない)

理由:
- 二系統は粒度 (invocation-local vs session-aggregate) と目的 (depth/profile の post-hoc anchor vs Tool/Text 4象限 MECE 観測) が異なる
- 1 symbol に詰めるとどちらの contract も歪む
- Codex の既存実装に破壊的変更を加えずに Wave 0.5 acceptance を満たせる
- Wave 1 `CognitiveOp.observe()` を anchor.py 側に紐づければ、Sensor Triad 系の進化と独立に動く

工数: Codex/Composer 2 委託で 1-2 セッション (anchor.py 新設 + smoke test)。

### 案 II: **Wave 0.5 §5.2 を改訂し、SessionObservation を正本化**

- design 文書 §5.2 を sensor_triad 系列に寄せて改訂
- ObservationAnchor を SessionObservation に統合 (depth/profile field を SessionObservation に追加)
- A5/A6 を「session-aggregate 観測が depth/profile を保持する」に再定義

理由 (採るなら):
- 二系統を維持するコストを払わない
- 観測面を 1 系統に倒すことで mental model が単純化

退けた理由:
- invocation-local 粒度を捨てると、同 session 内の異なる depth invocation が観測上区別不能になる
- Wave 1 `CognitiveOp.observe()` が「自分の操作を anchor として登録する」契約に立てなくなる
- design の合理性 (粒度分離) を実装都合で消す方向

### 案 III: **両系統を同型変換で接続する adapter 層を作る**

- ObservationAnchor を「session_id + invocation_id を key に SessionObservation を後から lookup する」 view として実装
- 物理的には SessionObservation が backing store、ObservationAnchor は projection

理由 (採るなら):
- 案 I より型を 1 つ減らせる

退けた理由:
- 観測タイミングの非対称性 (anchor は invocation 時刻に作る / SessionObservation は session 後段で aggregate) を view で吸収するのは概念的に重い
- 案 I の方が「Wave 0.5 が adapter contract と言ったもの」をそのまま実装できる

---

## §5 [主観] と次の一手

### [主観] (basis: §1.2 の経緯推定 + §3.4 の構造判断)

advisor 立場では **案 I を推す**。理由は単純で、Wave 0.5 §5.2 の設計意図 (invocation-local anchor / depth-profile 受領 / δ post-hoc 接続) と、sensor_triad_formal.md の設計意図 (4象限 MECE / Tool-Text-Being 独立観測 / Pattern 3-8 検出) は **両方とも捨てるべきではない**。両系統が `observe.py` という path を奪い合っているのは設計事故であって、構造的な必然ではない。

二系統を別 symbol で立てれば、Wave 1 `CognitiveOp.observe()` は anchor 系に乗り、Pattern 3 の捏造検出 (sensor_triad R2 rule) は SessionObservation 系に乗る。両者を将来 join するか否かは Wave 2 以降の経験で決めればよい。

### Closed-out (v0.3, 2026-05-02)

案 I (両系統別 symbol で共存) を採用、N1 を Composer 2 で実装。Codex 経路は `--contract-mode` 削除と stdin 待ち問題で 2 連続 fail し、composer2-worker subagent に振替えた。

**実装結果**:
- `mekhane/organon/anchor.py` 新設 (184 行) — `ObservationAnchor` dataclass (frozen=True, slots=True, 9 fields) + `observe_anchor` 関数
- `mekhane/organon/__init__.py` Edit (+4 行) — ObservationAnchor / observe_anchor を `__all__` に追加
- `mekhane/tests/test_anchor.py` 新設 (88 行) — A5/A6 検収 3 件 (Composer 2 報告: 3 passed、独立 import smoke で frozen/slots/9 fields 確認)
- 既存 `observe.py` (sensor_triad orchestrator) は無変更

**Composer 2 設計上の細部**:
- `profile` は `MappingProxyType` でラップ (frozen=True が dict 内容まで freeze しないため、Codex 指摘で immutable view に変換)
- lazy callable は `def _make_lazy(...)` パターン (ruff E731 lambda 警告対応)

**残課題 (次バージョン候補、本 audit の closed-out には影響なし)**:
- E1: Codex Bridge Edge 指摘 — `delta_scores_provider` の non-callable 受領 / provider 例外時の挙動が契約化されていない (現状: docstring 明記または `callable()` validation を v0.2 で検討)
- E2: closure-cell mutation 防御は `session_id: str` の局所束縛では過剰 (loop late-binding ではない)。実害なしだが、次回 refactor で `def _make_lazy` の意図を docstring に書く価値あり
- E3: pytest 独立再実行 (.venv に pytest 不在のため未実施)。Composer 2 報告と Claude 独立 introspection で実装の品質は確認済だが、CI 整備が望まれる
- E4: Codex 経路 (cli_agent_bridge stdin 待ち) は別 task として残る

### →次 (Wave 0.5 closed、次の判断分岐面)

| 次手 | 内容 | 工数 | 担当適性 |
|---|---|---|---|
| **F2** | E1/E2 を anchor.py v0.2 で patch (provider 例外契約 + closure docstring) | 0.3 セッション | Claude / Composer 2 |
| **F3** | meta.md §M0.7 を読み、Wave 0.5 contract と上位台帳の整合を再確認 | 0.3 セッション | Claude |
| **F4** | Wave 1 `CognitiveOp` protocol 設計 (`02_設計｜Design/01_cognitive_op_protocol.md`) に進む | 1-2 セッション | Claude |
| **F5** | Codex 経路 stdin 問題の調査 (cli_agent_bridge / codex CLI 0.124.0 挙動) | 0.5 セッション | Claude |
| **F6** | venv に pytest 入れて A5/A6 を独立再検証 (CI 補強) | 0.2 セッション | Claude |
| **F7** | `organon_kernel_contract.md` §5.2 末尾に「symbol 衝突回避ルール」(anchor.py vs observe.py) を追記 | 0.3 セッション | Claude (Edit) |

stop_if:
- 「Wave 0.5 はもう closed、別 PJ に行く」→ F2-F7 すべて保留

---

*Created: 2026-05-02*
*Status: v0.3 (案 I 採用 closed-out, A5/A6 達成)*
*Next review: 残課題 E1-E4 を次バージョン anchor.py v0.2 / Wave 1 着手時に再検討*

## §6 改訂履歴

| Version | Date | 変更 |
|---|---|---|
| v0.1 | 2026-05-02 | 初版。A5/A6 の gap 検出と 3 案提示 |
| v0.2 | 2026-05-02 | Codex Bridge audit feedback 受領: A5「型が存在しない」断定への repo-wide rg 証跡を §0 と §3.1 に追記 (`rg "ObservationAnchor" mekhane/_src` 0 件) |
| v0.3 | 2026-05-02 | 案 I closed-out。Composer 2 で anchor.py 実装完了 (184 行 + tests 88 行)、A5/A6 達成。Codex 経路 fail (2 回連続 — `--contract-mode` 引数削除 + stdin 待ち timeout) で composer2-worker 振替。残課題 E1-E4 は次バージョン候補として明示。delegate-codex.sh は L120-125 patch (--contract-mode forwarding 削除) で復旧、memory feedback_codex_invocation_path.md update 済 |
