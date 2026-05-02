# 認知操作の道具化 (Organon Project)

> **目的**: axiom_hierarchy v6.0 の L2 (48 認知操作) と L3 (弱2-圏) を **operational completion** し、HGK 認知動詞を prompt (SKILL.md) から code (MCP モジュール) に昇格させる。
>
> **圏論的意味**: UI (prompt) ⊣ Organon (code)
> 左随伴 L: prompt → code (SKILL dispatch → MCP 呼出)
> 右随伴 R: code → prompt (実行結果 → 自然言語応答)
>
> **核命題**: 48 認知操作は Γ (VFE 降下) と Q (等 VFE 循環) の両側を持つが、現状の SKILL.md は Γ 側のみ実装。Organon は Q を補完し、弱2-圏 L3 を実行可能形式で完成させる。
>
> **1文再定義**: Organon は、**CCL が記述し、harness gate が runtime の厚みを切り替え、Daimonion δ が being を観測する、HGK の meta-harness runtime** である。
>
> **Wave 0.5 (kernel contract)**: Wave 1 に入る前に、`CCL → harness gate → Daimonion δ observe` という最小 loop を固定する。これは 48 / X / Q を増やす前に、記述・実行・観測の 3 相が同じ runtime で閉じることを確認する薄い前段である。
>
> **Hooks 定義面の確定**: Claude Code hooks は Organon において universal bus ではなく、**doing 面の離散 event を切り出す layered bus** である。hooks 自体は 48 / X / Q / δ を直接運ばず、`48-seed`、`gate-only`、`Q-window`、`δ-anchor` に分配される。

## 概念

- **Organon (ὄργανον)**: 道具、手段、器官。アリストテレスの論理学書名。「認知の道具箱」。
- **operational completion**: axiom v6.0 で理論的に定義された構造 (L2 48 + X 15 + Q 15) を実行可能 code として具体化すること。
- **Ergon との関係** (補完):
  - Ergon: HGK ハーネス自体を**削る** (RG 蒸留 / prior 縮小 / Hook 環境強制)
  - Organon: HGK 認知動詞を**充填する** (L2 Γ/Q 完成 / X-Q dispatcher 実装)
  - 両者は「prose → code 昇格」の方向を共有。Ergon P4 (C を Hook で環境強制) は Organon dispatcher の物理実装を共有しうる。

## ハーネス理論との接続

Organon は単なる「認知動詞の実装 PJ」ではない。2026-04-17 から 2026-04-18 にかけて固定された HGK ハーネス理論の **code 側の受け皿** として置かれている。

圧縮すると、現在の理論線は次の 3 段である:

| 段 | 核主張 | Organon にとっての意味 |
|---|---|---|
| **A: meta-harness 線** | harness は計算階層を貫通する普遍構造であり、CCL は LLM 階層の ISA である | Organon は `prompt → code` の左随伴として、CCL を実行可能面へ降ろす |
| **B: runtime harness 線** | depth は説明文ではなく、実行時にハーネス重量を切り替える制御信号である | `mekhane/mcp/` の harness gate は Organon runtime の下位基盤になる |
| **D: sensor harness 線** | harness は行為面だけでなく being 面を観測するセンサーでもある | `daimonion_delta.py` は H-series evaluator の既存実装核として再利用される |

この整理により、Organon の役割は明確になる。

| 相 | 何をするか | 現在の受領面 |
|---|---|---|
| **記述** | LLM をどう動かすかを書く | CCL / hermeneus |
| **実行** | どの厚さの runtime を起動するか決め、dispatch / schedule する | harness gate / X / Q |
| **観測** | doing ではなく being のズレを検知する | Daimonion δ |

- **A を受ける**: CCL を「LLM のアセンブリ言語」と見たとき、Organon はその code 側の命令実行面になる
- **B を受ける**: depth-driven harness selection は「どの厚さの runtime を起動するか」を決める前段になる
- **D を受ける**: Daimonion δ は H-series 12 中動態の proxy 観測として、Organon の `observe()` 面へ接続される

ここで hooks の位置づけを誤ると、Organon 全体が崩れる。hooks は runtime の全相を担うものではない。

| 層 | hooks の役割 | 後段で確定するもの |
|---|---|---|
| **入口層** | lifecycle event の切出し | raw event |
| **seed 層** | doing 面の粗い射影 | 48-seed |
| **制御層** | permission / gate / authority | gate-only |
| **時間層** | 再帰・変化の窓 | Q-window |
| **接地層** | drift 解析の時系列アンカー | δ-anchor |

逆に、次のものは hooks 単体では確定しない。

- **fine-grained 48 分類**: semantic layer が必要
- **X-series**: dispatch / sequence の runtime が必要
- **Q-series の本体**: scheduler / temporal recurrence が必要
- **being 観測**: Daimonion δ が必要

したがって Organon は、ハーネス理論から見れば **meta-harness の operational completion** である。ここで重要なのは、**48 evaluator / X dispatcher / Q scheduler は Organon の identity ではなく、この 3 相を code に落とした結果として現れる実装形**だということだ。理論の比喩をコードへ降ろすだけではなく、runtime の冗長性・型・循環・観測を持った実装面として、HGK の「偶然動いている」を「構造的に動く」へ押し進める。

## ディレクトリ構造

```
15_道具｜Organon/
├── README.md                      # 本ファイル
├── meta.md                        # 論文化用台帳 (F⊣G 宣言 + 核主張)
├── 01_理論｜Theory/               # axiom → Organon の演繹
│   └── harness_lenses.md          # harness を読む複数視点 (Euporía lens 他)
├── 02_設計｜Design/               # 三層アーキテクチャ (Layer α/β/γ)
├── 03_検証｜Verify/               # Wave ごとの検証
└── 04_実装｜Impl/
    └── 01_roadmap_v0.1.md         # Wave 0-5 実装計画
```

## 理論ノート

Organon は「認知操作の道具化」を扱う。その前提として、**道具 (harness) 自体をどう読むか** が重要になる。harness には複数の正当な読み方 (lens) があり、どの lens を選ぶかで前景化される性質が変わる。

- [01_理論｜Theory/harness_lenses.md](./01_理論｜Theory/harness_lenses.md) — harness を読む複数 lens の集約。現状は以下を収録:
  - **Lens 1: Euporía view** — 行為可能性を開く装置
  - **Lens 2: FT stochastic architecture view** — 確率的機械の耐久層
  - **Lens 3: CCL=ISA / meta-harness view** — 階層越境するアセンブリ層
  - **Lens 4: Daimonion δ view** — being 層の観測センサー
  - **Lens 5** 以降として Pachaar 12-component などの operational lens を追加予定

## 設計ノート

- [02_設計｜Design/organon_kernel_contract.md](./02_設計｜Design/organon_kernel_contract.md) — Wave 0.5 の正本。`CCL → harness gate → Daimonion δ observe` を `DepthSignal → HarnessProfile → ObservationAnchor` として固定する。
- [02_設計｜Design/hook_runtime_layers.md](./02_設計｜Design/hook_runtime_layers.md) — H2/H4/H5 を `hook 側の ingress/control/observation stack` として固定する三層メモ。README の `hooks = layered bus` を runtime 境界へ降ろす。
- [02_設計｜Design/daimonion_signal_lexicon.md](./02_設計｜Design/daimonion_signal_lexicon.md) — H5 hook pilot の `signals` 語彙正本。何が signal で何が anchor だけかを固定する。
- [02_設計｜Design/sensor_triad_formal.md](./02_設計｜Design/sensor_triad_formal.md) — Tool/Text/Being の 3 sensor を 48 座標へ射影する観測設計。
- [02_設計｜Design/python_sensor_lexicon.md](./02_設計｜Design/python_sensor_lexicon.md) — SKILL.md 48 から Python Sensor 用 lexicon を抽出する辞書設計。

## 核資産マップ (既存実装)

| 層 | 既存 | 状態 |
|---|---|---|
| Basis (L0.T) | `mekhane/fep/basis.py` HELMHOLTZ_OPERATORS 12 | ✅ v6.0 対応 |
| 0-cell registry | `mekhane/fep/two_cell.py` (48 0-cell + Associator + 検証器) | ✅ v5.4 対応 |
| Evaluator 24 | `mekhane/fep/` (telos/horme/akribeia/chronos 等) | 🟡 v3.0 旧体系 |
| Adjunction | `mekhane/fep/adjunction_builder.py` | 🟡 部分 |
| Daimonion δ | `mekhane/sympatheia/daimonion_delta.py` (H-series proxy 観測) | ✅ |
| Harness gate | `mekhane/mcp/` (拡張B Phase 1 完了) | ✅ |
| Q-series 15 | — | 🕳️ **未実装** |
| X-series 15 runtime | 部分的 | 🕳️ **未実装** |
| SKILL.md 48 | `~/.claude/skills/` | ✅ UI 層 |

## 実装 Wave (概要)

| Wave | 内容 | 目安工数 |
|---|---|---|
| 0 | Gap analysis (v3.0 24 vs v6.0 48) | 1 週 |
| 0.5 | kernel contract 固定 (`CCL → harness gate → Daimonion δ observe`) | 2-3 日 |
| 1 | Layer α: 48 evaluator 完成 (S極 12 + H-series 12 追加) | 2-3 週 |
| 2 | Layer β: X-series 15 dispatcher (CCL `>>` 型システム) | 2-3 週 |
| 3 | Layer γ: Q-series 15 scheduler (時間的循環) | 3-4 週 |
| 4 | 外部化 (MCP 公開 + SKILL.md bidirectional bridge) | 2 週 |
| 5 | 論文化 (並行) | — |

詳細: [04_実装｜Impl/01_roadmap_v0.1.md](./04_実装｜Impl/01_roadmap_v0.1.md)

## 依存関係

### 内部
- `00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md` v6.0 (L2 48 + 体系核外 X 15 + Q 15)
- `mekhane/fep/` (既存 24 evaluator + two_cell.py + basis.py)
- `mekhane/sympatheia/daimonion_delta.py` (H-series proxy 観測)
- `mekhane/mcp/` (harness_gate, gateway_hooks)
- `hermeneus` (CCL 実行エンジン)

### 並行 PJ
- [09_能動｜Ergon](../09_能動｜Ergon/) — ハーネス削減 (補完関係)
- [08_形式導出｜FormalDerivation](../08_形式導出｜FormalDerivation/) — HGK⊣Organon 随伴の形式的導出候補

### 外部比較対象
- axiom_hierarchy 起点の論文群: Paper I 方向性定理 / Paper V β 関数 / Paper VI 結晶化
- Akshay Pachaar 2026 (12-component harness), LangGraph, CrewAI, Claude Agent SDK

## 6 設計原理 (案)

| 原理 | 根拠 | 処方 |
|:---|:---|:---|
| **O1: Γ/Q 対称性保存** | axiom L294 Basis Γ⊣Q | 全 48 動詞に Γ 関数と Q 関数の両方を実装 |
| **O2: X/Q 双対分離** | axiom L547 + Q 循環定理 P₁ | X = 順序的結合 (1-cell dispatch), Q = 循環的探索 (2-cell scheduler) |
| **O3: 既存資産の再利用優先** | 2 年間の mekhane/fep/ 投資 | 新規実装より共通 interface 抽出を優先 |
| **O4: SKILL.md は UI 層として残す** | prompt と code の bi-directional bridge | 破壊的変更禁止。backend 呼出経路を追加 |
| **O5: 象限純粋性** | axiom L250 象限純粋性原則 | S 動詞は I に委譲、I 動詞は A に委譲、A 動詞は受領のみ |
| **O6: Daimonion δ 統合** | H-series proxy 観測が既存 | H-series evaluator = δ の gamma/Q 拡張 |

## STATUS

- **現状**: 3相再定義 + Wave 0.5 kernel contract 文書化まで完了
- **次**: Wave 0 gap analysis (`~/.claude/plans/organon-wave0.md`) → `ObservationAnchor` / `observe()` adapter の実装位置決定

---

*Created: 2026-04-19*
*Tolmetes 承認: 2026-04-19 (新 PJ 作成 / 名称 Organon / 番号 15 / 今セッション ドラフト / Wave 0 advisor plan 発射準備)*
