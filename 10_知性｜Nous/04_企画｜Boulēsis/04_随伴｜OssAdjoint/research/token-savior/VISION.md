# token-savior ⊣ HGK 随伴吸収 VISION (`/ere+`, L3)

> **対象 OSS**: `Mibayy/token-savior` (`5067785ca5853f68e6b7f69fb6d89a086b55c6ea`, v2.6.0)
> **調査日**: 2026-04-20
> **調査方式**: static file-surface exploration only
> **HGK 対象面**: `Organon` / `OssAdjoint` / `Mekhane` / `Mneme` / `Lēthē` / `Oblivion`

---

## Phase 0 — Prolegomena

### S[0.1]: 探知対象

| 項目 | 値 |
|:---|:---|
| 主要問い | `token-savior` を HGK に **概念レベル** と **実装レベル** の両方で吸収できるか |
| 直近の設置先 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/token-savior/` |
| 概念候補 | `Organon` / `Lēthē` / `Oblivion` / `Mneme` |
| 実装候補 | `mekhane/symploke/`, `mekhane/mcp/`, `PhantazeinStore`, `context_rot` |

### S[0.2]: 範囲

| 探知面 | パス / Surface | MaxDepth | 注記 |
|:---|:---|:---:|:---|
| Upstream docs | `/tmp/token-savior-inspect/README.md`, `llms-install.md`, `docs/progressive-disclosure.md`, `pyproject.toml` | 1 | 公開仕様面 |
| Upstream code | `/tmp/token-savior-inspect/src/token_savior/` 直下の indexer / memory / workflow / server 周辺 | 3 | 主要実装面のみ |
| HGK doctrine | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/B_哲学｜Philosophy/organon.md` | 1 | Organon 正本 |
| HGK adjoint surface | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/` | 2 | 既存 OSS 随伴作法 |
| HGK implementation | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/` | 3 | Mneme / Symploke / MCP |
| 明示的に除外 | runtime boot, benchmark replay, server live execution | 0 | `/ere+` なので `/pei` はまだ行わない |

### S[0.3]: prior 棚卸し

| ID | prior | ラベル |
|:---|:---|:---|
| P1 | `token-savior` は persistent memory plugin に過ぎない | [TAINT: 推測] |
| P2 | Codex 接続が書いてあるなら HGK 深統合もすぐできる | [TAINT: 推測] |
| P3 | HGK の `Mneme/Phantazein` をそのまま置換できる | [TAINT: 推測] |
| P4 | 真の差分価値は memory engine だけである | [TAINT: 推測] |
| P5 | OSS 随伴の置き場は registry の `organon` path そのままにある | [TAINT: 推測] |

### S[0.4]: バイアスリスク

| バイアス | 水準 | 制御 |
|:---|:---:|:---|
| Prior依存 | HIGH | upstream 実装面を先に読む |
| 早期停止 | HIGH | docs だけで止めず code surfaces まで読む |
| 範囲曖昧化 | MED | path と surface を先に固定 |
| 知覚/解釈混同 | HIGH | Phase 1 は事実のみ、判断は Phase 2 へ送る |

受け取り: Tolmetes の要求は「概念吸収」と「実装吸収」の二重精査である。  
持ち越し: P1-P5 を事実で検証し、概念面と実装面を分離して地図化する。

[CHECKPOINT PHASE 0/3]

---

## Phase 1 — Ereuna

### S[1.1]: 信号記録

| 信号 | 知覚した事実 | SOURCE |
|:---|:---|:---|
| 🔍 package metadata | `token-savior-recall` は `v2.6.0`、Python `>=3.11`、license `MIT` | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/README.md#L5-L18], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/pyproject.toml#L5-L17] |
| 🔍 public thesis | upstream README は `Structural code navigation + persistent memory engine` と記述 | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/README.md#L45-L58] |
| 🔍 Codex config surface | `.mcp.json` 例に `TOKEN_SAVIOR_CLIENT: "codex"` がある | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/llms-install.md#L12-L28] |
| 🔍 multi-language index | `ProjectIndexer` の include patterns は `py/ts/tsx/js/jsx/go/rs/c/h/glsl/cs/java/gradle/md/json/yaml/toml/ini/env/xml/hcl/tf/Dockerfile` を含む | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/project_indexer.py#L145-L193] |
| 🔍 HGK-specific exclusion affinity | upstream indexer は `**/.claude/worktrees/**` と `**/.worktrees/**` を除外する | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/project_indexer.py#L223-L228] |
| 🔍 tool surface size | README は full profile `106` tools, `nav` `28`, `ultra` `17` と記述 | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/README.md#L176-L208] |
| 🔍 memory contract | README は `memory_index -> memory_search -> memory_get` の 3-layer progressive disclosure を記述 | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/README.md#L211-L223], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/docs/progressive-disclosure.md#L16-L63] |
| 🔍 memory handler surface | `_mh_memory_index`, `_mh_memory_search`, `_mh_memory_get` が `ts://obs/{id}` を使う | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/server_handlers/memory.py#L702-L902] |
| 🔍 memory schema | upstream SQLite schema に `observations`, `session_summaries`, `reasoning_chains`, `events`, `user_prompts`, `memory_cache`, `observation_links` がある | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory_schema.sql#L22-L176], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory_schema.sql#L218-L279] |
| 🔍 decay surface | decay rules は per-type TTL, zero-access rules, quarantine とは別の archive 候補選定を持つ | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory/decay.py#L16-L29], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory/decay.py#L117-L209] |
| 🔍 consistency surface | Bayesian validity, stale threshold `0.60`, quarantine threshold `0.40`, `git log -S symbol` による staleness check がある | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory/consistency.py#L17-L44], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory/consistency.py#L100-L239] |
| 🔍 context packing | `pack_context()` は knapsack-based selection、`score_symbol()` は query match / graph distance / recency / access を合成 | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/context_packer.py#L1-L85] |
| 🔍 slot lifecycle | `SlotManager` は git ref cache hit, changed files `<=20` で incremental update, multi-root resolve を持つ | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/slot_manager.py#L96-L149], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/slot_manager.py#L199-L259] |
| 🔍 warm start surface | `SessionWarmStart` は 32-dim signature で類似セッションを探し pre-warm する | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/session_warmstart.py#L1-L13], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/session_warmstart.py#L51-L170] |
| 🔍 workflow safety | `apply_symbol_change_and_validate()` は `verify_edit` → `run_impacted_tests` → optional rollback を 1 workflow にまとめる | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/workflow_ops.py#L15-L148] |
| 🔍 static edit cert | `verify_edit()` は signature/tests/exceptions/side-effects の 4 項目を静的証明として返す | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/edit_verifier.py#L1-L12], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/edit_verifier.py#L118-L160] |
| 🔍 checkpoint surface | checkpoint は project-local `.token-savior-checkpoints` に置かれ、path traversal guard を持つ | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/checkpoint_ops.py#L14-L29], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/checkpoint_ops.py#L94-L163] |
| 🔍 hook dependence | README は 8 Claude lifecycle hooks を記述し、sample config には `SessionStart`/`Stop` がある | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/README.md#L78-L96], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/hooks/memory-hooks-config.json#L1-L25] |
| 🔍 auto-extract surface | `TS_AUTO_EXTRACT=1` のとき PostToolUse で 0-3 observations を小モデル抽出する | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory/auto_extract.py#L1-L25], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/memory/auto_extract.py#L164-L211] |
| 🔍 HGK Organon doctrine | `Organon = 主体 (S) に随伴する実行圏 (T) のインスタンス`、Phase 1-3 を定義 | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/B_哲学｜Philosophy/organon.md#L10-L18], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/B_哲学｜Philosophy/organon.md#L54-L90] |
| 🔍 HGK Organon harness surface | Organon 文書は tools / verification / memory を `T` 側の構成要素として置く | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/B_哲学｜Philosophy/organon.md#L149-L188] |
| 🔍 HGK project continuity | `project_index` は SessionStart/Stop hook により自動読込・自動書出しされる | [SOURCE: /home/makaron8426/.claude/CLAUDE.md#L60-L64] |
| 🔍 HGK persistent store | `PhantazeinStore` は SQLite WAL を使い、`knowledge_nodes` と deterministic `observations` を持つ | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/phantazein_store.py#L91-L106], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/phantazein_store.py#L209-L250] |
| 🔍 HGK observation mirror | `upsert_observation()` は observation を `knowledge_nodes` に mirror する | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/phantazein_store.py#L549-L639] |
| 🔍 HGK search façade | `mneme_server.py` は `search`, `notebook`, `graph`, `code_symbol`, `absorption` を提供する | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/mneme_server.py#L486-L722] |
| 🔍 HGK code graph scope | `code_symbol_graph.py` は `Python 専用の symbol graph` と明記 | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/code_symbol_graph.py#L1-L7], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/code_symbol_graph.py#L29-L33] |
| 🔍 HGK distillation surface | `context_rot_status` / `context_rot_distill` が ROM 蒸留を提供する | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/context_rot.py#L5-L13], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/context_rot.py#L131-L147] |
| 🔍 HGK absorption surface | `absorption.py` は外部検索機構を吸収写像 manifest として扱う | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/search/absorption.py#L1-L6], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/search/absorption.py#L35-L45] |
| 🔍 OssAdjoint doctrine | OssAdjoint は `Replace / Leverage+Extend / Build` の三択で OSS を評価する | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/README.md#L1-L24] |
| 🔍 existing OSS adjoint style | `deerflow/VISION.md` は upstream 実装を読み、HGK landing zone に吸収先を割り当てる形式を取る | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/deerflow/VISION.md#L1-L24], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/deerflow/VISION.md#L48-L101] |
| 🚫 HGK-specific adapter | upstream 全文検索で `HGK|Hegemonikon|mneme|phantazein|context_rot` の一致を確認できなかった | [SOURCE: `rg -n "HGK|Hegemonikon|mneme|phantazein|context_rot" /tmp/token-savior-inspect`] |
| ⚡ registry/live path mismatch | registry の `organon` 抽象 path と live filesystem の主作業面は一致しなかった。live adjoint surface は `OssAdjoint` 側に存在した | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/registry.yaml#L519-L532], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/README.md#L1-L24] |

### S[1.2]: prior 検証

| prior | 結果 | SOURCE |
|:---|:---|:---|
| P1 `memory plugin に過ぎない` | ⚡ 否定。README と server surface には structural navigation / editing / checkpoint / workflow が含まれる | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/README.md#L45-L58], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/tool_schemas.py#L90-L260] |
| P2 `Codex 接続なら深統合もすぐ` | ⚡ 一部否定。MCP 接続面はあるが memory automation は Claude hooks 記述が中心 | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/llms-install.md#L12-L28], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/README.md#L78-L96] |
| P3 `Mneme/Phantazein を置換できる` | ⚡ 否定。HGK 側に canonical continuity と persistent store が既にある | [SOURCE: /home/makaron8426/.claude/CLAUDE.md#L60-L64], [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/mekhane/symploke/phantazein_store.py#L91-L106] |
| P4 `価値は memory だけ` | ⚡ 否定。multi-language index / workflow safety / checkpoint / context packing が存在する | [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/project_indexer.py#L145-L193], [SOURCE: https://github.com/Mibayy/token-savior/blob/5067785ca5853f68e6b7f69fb6d89a086b55c6ea/src/token_savior/workflow_ops.py#L15-L148] |
| P5 `置き場は registry organon path そのまま` | ⚡ 否定。live OSS 随伴作業面は `OssAdjoint/research/` に存在 | [SOURCE: /home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/README.md#L1-L33] |

### S[1.3]: 走査完了判定

| Surface class | planned | checked | 状態 |
|:---|---:|---:|:---|
| upstream docs | 4 | 4 | 完了 |
| upstream core code | 11 | 11 | 完了 |
| HGK doctrine / adjoint docs | 5 | 5 | 完了 |
| HGK implementation surfaces | 6 | 6 | 完了 |
| runtime execution | 0 | 0 | scope 外 |

受け取り: Phase 1 で static surface は閉じた。  
持ち越し: Phase 2 で `概念吸収` / `実装吸収` / `棄却枝` を分離する。

[CHECKPOINT PHASE 1/3]

---

## Phase 2 — Katalogē

### S[2.1]: 発見地図 — 概念吸収

| candidate | HGK target | 判定 | 理由 |
|:---|:---|:---|:---|
| `token-savior` を **Organon の T-side 実行器官** として読む | `Organon` | **Import** | upstream 実体は navigation / memory / checkpoint / workflow を持つ「外部装具」であり、`Organon` が定義する `T` に自然に乗る |
| `token-savior memory` を **U⊣N の補助器官** として読む | `Lēthē` / `Oblivion` | **Watch** | decay / TTL / quarantine / progressive disclosure は忘却論との接点が強い。ただし HGK canonical memory を直接置換する根拠にはならない |
| `token-savior` を **Mneme 正本** として採用する | `Mneme` / `Phantazein` | **Skip** | HGK には project continuity と canonical persistent store が既にあり、ここへ外部正本を入れると権威が二重化する |
| `token-savior` を **外部検索機構の吸収写像** として読む | `symploke/search/absorption.py` | **Import** | upstream は external code search / structural nav の具体物であり、HGK 既存の absorption map 語彙に乗せやすい |
| `token-savior` を **Autophonos/PKS の proactive feed** として読む | `PKS` / `Autophonos` | **Watch** | dashboard / notification / observation feed はあるが、主軸ではない |

### S[2.1-b]: 発見地図 — 実装吸収

| candidate | upstream surface | HGK landing zone | Strategy | viability | note |
|:---|:---|:---|:---:|:---:|:---|
| 多言語 structural index | `project_indexer.py` | `mekhane/symploke/code_symbol_graph.py` | 🟡 Leverage+Extend | High | HGK 現行は Python 専用。ここが最大の差分 |
| progressive disclosure memory UX | `memory_index/search/get` | `mneme_server.py` facade | 🟡 Leverage+Extend | High | store を替えず UX contract だけ吸収できる |
| slot manager + incremental update | `slot_manager.py` | `Mekhane` index cache / query layer | 🟡 Leverage+Extend | High | git ref cache / `<=20` files incremental は移植価値がある |
| context packing | `context_packer.py` | `context_rot` / `Ochēma` context injection | 🟡 Leverage+Extend | Medium | HGK にも蒸留はあるが packing scorer は別物 |
| warm start signatures | `session_warmstart.py` | Boot context / Motherbrain cache | 🟡 Leverage+Extend | Medium | session prewarm は HGK boot に吸収余地がある |
| Bayesian validity + quarantine | `memory/consistency.py` | `PhantazeinStore` observation meta | 🟡 Leverage+Extend | Medium | confidence は HGK にある。posterior validity は未実装 |
| TTL / decay / ROI GC | `memory/decay.py`, `memory/index.py` | `PhantazeinStore` maintenance jobs | 🟡 Leverage+Extend | Medium | 忘却論との接続は強いが canonical 導入は段階的にすべき |
| static EditSafety certificate | `edit_verifier.py` | `Jules` / `Synergeia` / edit workflows | 🟡 Leverage+Extend | High | 小さく持ち込める。検証面が明快 |
| checkpoint + rollback | `checkpoint_ops.py`, `workflow_ops.py` | `Jules` / `Hermēneus` edit pipeline | 🟡 Leverage+Extend | High | bounded mutation 前の rollback 面として相性が良い |
| hook-driven auto extract | `memory/auto_extract.py` | HGK hooks | 👀 Watch | Low-Med | client 依存が強く、追加 LLM call を伴う |
| full MCP manifest import | `server.py` profile system | Codex main MCP surface | ⛔ Skip | Low | `full` 106 tools は manifest が重い。最初は `nav` か `ultra` だけで十分 |

### S[2.2]: SOURCE ラベル最終確認

| source class | 件数 | 状態 |
|:---|---:|:---|
| upstream docs / metadata | 4 | SOURCE あり |
| upstream core implementation | 11 | SOURCE あり |
| HGK doctrine / adjoint docs | 5 | SOURCE あり |
| HGK implementation code | 6 | SOURCE あり |
| runtime / benchmark replay | 0 | scope 外、未主張 |

### S[2.3]: Coverage Check

| 領域 | coverage | 🕳️ GAP |
|:---|:---:|:---|
| static file-surface | 100% | なし |
| runtime behavior | 0% | server 起動、tool latency、index build time、local benchmark 再現は未検証 |
| benchmark claim validation | 0% | `97% fewer tokens`, `97.8% tsbench` は upstream claim のまま |

### S[2.4]: φ_SI / 随伴接続

**F: `token-savior → HGK`**

1. `project_indexer` → `code_symbol_graph` の多言語化
2. `memory_index/search/get` → `mneme_server` の progressive disclosure façade
3. `verify_edit` + `checkpoint` + `rollback` → `Jules/Synergeia` の bounded mutation workflow
4. `context_packer` + `session_warmstart` → `context_rot` / Boot Context の packing & prewarm

**G: `HGK → token-savior`**

1. `Organon` の語彙へ忘却すると、HGK 側の差分は「canonical memory / theory / adjoint doctrine」を落とした実用ハーネスになる
2. `Mneme/Phantazein` の差分を落とすと、残るのは「検索・短期注入・観測列」の実用面であり upstream と近づく
3. `Lēthē` の差分を落とすと、TTL / decay / quarantine / disclosure が memory hygiene pattern として残る

**Fix(G∘F) の候補像**

`token-savior` を HGK の **canonical memory ではなく Organon sidecar** として置き、  
HGK は `意味の正本` と `継続状態の正本` を保持し、  
`token-savior` は `多言語構造探索` と `bounded retrieval / bounded edit workflow` を担う。

### S[2.5]: [主観] + →次

[確信 0.88] 最も筋がよいのは **「OssAdjoint で研究し、Organon として意味づけ、Mekhane に部分実装を吸収する」** 三段構えである。  
[確信 0.83] 逆に最も危険なのは **「memory engine があるから Mneme を置換しよう」** という短絡で、ここは split-brain の入口になる。  
[推定 0.76] 実装順は `nav-only sidecar` → `multi-language index` → `progressive disclosure façade` → `EditSafety/checkpoint` がよい。decay/quarantine はその後でよい。

### Rejection Ledger

| 棄却枝 | 理由 |
|:---|:---|
| upstream をそのまま `Mneme` 正本にする | canonical continuity と persistent store が HGK 内に既にある |
| 初手から `full` profile を Codex MCP に追加する | manifest が重く、学習コストと誤作動面が大きい |
| hook automation を最初から mirror する | upstream は Claude lifecycle hook への依存が強く、Codex/HGK への直写は粗い |
| benchmark 数値を意思決定根拠に使う | ローカル再現がまだない |

### Carry-forward Manifest / Next Implementation

1. `Phase A` — research sidecar only  
   `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/research/token-savior/` を研究正本にする。
2. `Phase B` — MCP nav PoC  
   `TOKEN_SAVIOR_PROFILE=nav` か `ultra` で sidecar 接続する。`full` は使わない。
3. `Phase C` — HGK import 1  
   `project_indexer` の include/exclude / incremental update / multi-project slot を HGK index layer に吸収する。
4. `Phase D` — HGK import 2  
   `memory_index/search/get` の UX contract を HGK search façade に焼き付ける。store は HGK 正本のまま。
5. `Phase E` — safety workflow  
   `verify_edit` / `checkpoint` / `rollback` を `Jules` か `Synergeia` の bounded mutation に接続する。
6. `Gate` — Zero-Trust  
   外部 MCP 追加前に `/home/makaron8426/.claude/rules/horos-hub.md#L99-L109` の Zero-Trust を通す。

[CHECKPOINT PHASE 2/3]

---

## Phase 3 — Sphragis

### SQS

| 項目 | 判定 | 根拠 |
|:---|:---:|:---|
| S1 Target Defined | 1 | 対象と範囲を path + surface で固定した |
| S2 S/I Separated | 1 | Phase 1 は事実記述に限定し、判断は Phase 2 へ送った |
| S3 SOURCE Pure | 1 | 全主要発見に SOURCE を付した |
| S4 Coverage Rich | 1 | static file-surface は scope 内で閉じた |
| S5 Absence Recorded | 1 | HGK-specific adapter の不在、runtime 未実行を明記した |
| S6 φ_SI Connected | 1 | Organon / Lēthē / Mneme / Mekhane への接続先を明示した |

**判定**: `PASS (6/6)`

### Thought Record

**F:** upstream 15 surfaces と HGK 11 surfaces を読んだ。`token-savior` は memory-only ではなく structural nav + workflow safety + context packing を持つ。  
**D:** 最大の誤り源は「Codex 接続可 = HGK 深統合可」と「memory engine = Mneme 置換可」の短絡だった。  
**C:** runtime 検証をしていないので、性能・安定性・manifest 実測は未確定である。  
**A:** 次は `/pei` で `nav` profile の sidecar PoC を行い、`multi-language code nav` と `memory UX` のどちらが真に利くかを測る。  
**S:** この VISION の static-fit に対する確信度は **84%**。runtime-fit は未測定。

[CHECKPOINT PHASE 3/3]
