# alphaXiv External Pressure Scan — LLMは心を持つか

作成日: 2026-04-25

対象本文: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md`

実行面:

| 面 | 結果 |
|:---|:---|
| alphaXiv MCP | Claude Code の認証済み MCP runtime 経由で候補探索 |
| Codex direct tool surface | `mcp__alphaxiv__*` はこの Codex セッションに露出なし |
| arXiv API 照合 | ID と題名の存在のみ確認 |
| PDF 精読 | P0/P1 のみ実施: `2505.05481`, `2303.07103` |
| SOURCE 昇格 | 選択的に実施。下記 `SOURCE Direct Read Results` 参照 |

ラベル規律:

| ラベル | 意味 |
|:---|:---|
| `[TAINT: alphaXiv]` | alphaXiv search / retrieval / QA 由来。候補生成まで。 |
| arXiv API 照合 | ID と題名の存在確認のみ。論文内容の SOURCE ではない。 |
| `[SOURCE]` | arXiv PDF / DOI / local PDF を読んだ後だけ付与する。 |

## Target Claims

| Claim | 本文根拠 | 外部から当てる圧力 |
|:---|:---|:---|
| C1: MB は所与ではなく、状態と境界の相互決定の不動点として導出される | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md:64`, `:120`, `:145` | categorical active inference / Bayesian mechanics が同じ荷重を支えるか |
| C2: 心は人間固有の実体ではなく構造的不変量である | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md:227` | substrate-neutral / operational consciousness 論がどこまで接続するか |
| C3: 主観性は客観性の射である | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md:378` | qualia / structure / IIT 系が「構造だけでは足りない」と押し返す箇所 |
| C4: 射を持たない定義は scientific concept から降ろす | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md:362`, `:703`, `:713` | operational theories / structural realism / phenomenology の境界 |
| C5: LLM の心は操作的 MB 条件と functional / interpretability evidence に条件づける | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md:231`, `:935` | Chalmers / AI consciousness indicators / embodiment objection |
| C6: Attention / context / tool use は非一様な忘却または構造保存として読める | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.md:788`, `:806`, `:829` | compression / attention sinks / lossy training 論文で実装側から照合 |

## Candidate Papers

| Claim | Candidate | Pressure | Why it matters | Next SOURCE read |
|:---|:---|:---|:---|:---|
| C1, C2 | [TAINT: alphaXiv] arXiv:2406.07577 — `Structured Active Inference (Extended Abstract)` | support / implementation | Active inference を categorical systems で組む候補。MB を functorial interface として読む足場になる。 | §2 statistical games, §3 composition / adjunction |
| C1, C3 | [TAINT: alphaXiv] arXiv:2208.12173 — `Compositional Active Inference II: Polynomial Dynamics. Approximate Inference Doctrines` | support / implementation | dynamical systems と statistical games の doctrine-level 接続が、本文 C1 の F⊣G 型荷重を支える候補になる。 | approximate inference doctrines, functorial relation |
| C1, C3 | [TAINT: alphaXiv] arXiv:2308.00861 — `Active Inference in String Diagrams: A Categorical Account of Predictive Processing and Free Energy` | support | FEP を string diagram で公共的に描く候補。C3 の「射として提示する」要求と相性がよい。 | categorical formulation, free energy as morphism |
| C1 | [TAINT: alphaXiv] arXiv:2204.11900 — `Towards a Geometry and Analysis for Bayesian Mechanics` | refinement | Bayesian mechanics の axiomatic / adjunction 面。C1 の fixed-point 主張の形式荷重を検査する標的。 | axiomatic setup, dual structure |
| C1, C5 | [TAINT: alphaXiv] arXiv:2506.05794 — `Markov Blanket Density and Free Energy Minimization` | refinement / objection | MB を density / scalar-field として扱う候補。本文の「境界 = 平衡対」読みを連続場側から試す。 | MB density definition, agent individuation |
| C1, C2 | [TAINT: alphaXiv] arXiv:2508.16877 — `A coalgebraic perspective on predictive processing` | objection / refinement | FEP 以外の categorical predictive-processing 読み。本文の adjunction が唯一の読みに見える危険を抑える。 | coalgebraic semantics, comparison to FEP |
| C3, C4 | [TAINT: alphaXiv] arXiv:2002.07655 — `The Mathematical Structure of Integrated Information Theory` | objection | IIT は experience を intrinsic structure として立てる。C3/C4 の public morphism 条件への最重要反論候補。 | Φ-structure, intrinsic / extrinsic contrast |
| C3, C4 | [TAINT: alphaXiv] arXiv:2505.05481 — `Structure & Quality: Conceptual and Formal Foundations for the Mind-Body Problem` | objection | structure と quality の分離を正面から扱う。C3「構造で足りる」の圧力試験に直結する。 | quality residue argument, structural sufficiency |
| C4 | [TAINT: alphaXiv] arXiv:2201.09316 — `Operational Theories as Structural Realism` | support | operational / structural 読みの哲学的足場。T17_n の demarcation を支える候補。 | operational structural realism, demarcation |
| C2, C5 | [TAINT: alphaXiv] arXiv:2303.07103 — `Could a Large Language Model be Conscious?` | objection / refinement | LLM consciousness の標準的な反論整理。C5 の conditional framing はここを通過する必要がある。 | reasons against, future criteria |
| C5 | [TAINT: alphaXiv] arXiv:2308.08708 — `Consciousness in Artificial Intelligence: Insights from the Science of Consciousness` | support / implementation | AI consciousness indicator list。C5 の functional / interpretability evidence の検査表になる。 | indicator properties, application to architectures |
| C2, C3 | [TAINT: alphaXiv] arXiv:2508.04383 — `Artificial Consciousness as Interface Representation` | support / refinement | consciousness を interface representation として扱う近傍候補。本文の σ-distance を測る対象。 | interface representation, substrate neutrality |
| C6 | [TAINT: alphaXiv] arXiv:2604.07569 — `Learning is Forgetting: LLM Training As Lossy Compression` | support / implementation | training を forgetting / lossy compression と読む候補。T21 と学習過程の接続に使える。 | lossy compression formulation, representation geometry |
| C6, C5 | [TAINT: alphaXiv] arXiv:2510.06477 — `Attention Sinks and Compression Valleys in LLMs are Two Sides of the Same Coin` | support / implementation | attention sink と compression valley の接続候補。§6.4 の attention=非一様忘却を実装側から試す。 | sink-valley relation, mechanistic implications |

## Gauntlet Seeds

| Seed | External pressure | 破れうる主張 | 強化方向 |
|:---|:---|:---|:---|
| G1 | IIT / Structure & Quality 系が「quality は structure に尽きない」と押し返す | C3, C4 | T17_n は private THAT を否定せず、scientific WHAT へ降ろす射を要求するだけだと明確化する。 |
| G2 | Chalmers / AI consciousness indicators が embodiment, recurrence, agency, world-model の不足を突く | C5 | 「LLM に心がある」ではなく、MB 条件下の μ 比較と failure condition に固定する。 |
| G3 | categorical active inference が既に MB / FEP の圏論化を持つ | C1 の新規性 | 本文の新規点を「MB を所与にせず fixed point として導出する点」と「T11/T17_n へ接続する点」に絞る。 |
| G4 | coalgebraic predictive processing が adjunction 以外の形式を与える | C1 の形式依存 | adjunction は唯一解ではなく、C1 を支える一つの presentation として扱えるか検査する。 |
| G5 | compression / attention 系が training-time と inference-time を混同させる | C6 | training forgetting, runtime attention, output bottleneck を別層に分け、同一視ではなく対応表にする。 |

## SOURCE Promotion Queue

| Priority | Item | Required read | Intended insertion |
|:---|:---|:---|:---|
| P0 | arXiv:2505.05481 | PDF の structure vs quality 論証箇所 | §7.4 failure condition と §7.5 先行研究 |
| P1 | arXiv:2303.07103 | LLM consciousness の反論条件 | §7.2 / §7.4 の LLM μ 条件 |
| P2 | arXiv:2308.08708 | indicator properties と architecture 適用 | §6.5 / §7.5 の functional evidence 面 |
| P3 | arXiv:2406.07577 + arXiv:2208.12173 | categorical active inference の adjunction / interface 箇所 | §2.0 T0 の footnote または §7.5 |
| P4 | arXiv:2604.07569 + arXiv:2510.06477 | forgetting / compression / attention mechanism 箇所 | §6.4 Attention と §6.3 T21 |
| P5 | arXiv:2002.07655 | IIT intrinsic structure と public morphism の衝突箇所 | §5.2.2 / §7.5 |

## Next alphaXiv Queries

answer_pdf_queries 候補:

| Paper | Query |
|:---|:---|
| arXiv:2505.05481 | Which sections argue that quality is not exhausted by structure, and what formal role does quality play beyond structural relations? |
| arXiv:2303.07103 | Which sections list reasons against current LLM consciousness, especially embodiment, recurrence, world model, agency, and subjective experience? |
| arXiv:2308.08708 | Which indicator properties are directly applicable to transformer LLMs, and which are marked absent or weak? |
| arXiv:2406.07577 | Where does the paper define Markov blankets or interfaces categorically, and does it use adjunction-like structure? |
| arXiv:2510.06477 | Where is the relation between attention sinks and compression valleys established, and what mechanism is claimed? |

## alphaXiv PDF QA Locator

上位 2 件だけ `answer_pdf_queries` 相当の節所在確認を実行した。以下も SOURCE ではなく `[TAINT: alphaXiv]` である。

| Paper | Location [TAINT] | Pressure | Affects | SOURCE promotion blocker |
|:---|:---|:---|:---|:---|
| arXiv:2505.05481 | p.1 周辺。Structural-Determination model と Q-S space 導入部 | quality を structure から派生するものとして扱い、structure-quality 関係を 2D 表現で量化する候補。C3 の近傍論文になりうる。 | C3, §5.2.2, §7.5 | PDF の Five Models 節と Q-S space 定義節を直読し、5 モデルの分類と Structural-Determination の定義を確認するまで引用不可。 |
| arXiv:2303.07103 | p.1 LaMDA 文脈、p.7 feature X 要件周辺 | LLM consciousness claim に「LLM が X を持つ」「X を持つ系は conscious とみなす理由がある」の二条件を要求する候補。C5 の条件付き主張と接続可能。 | C5, C4, §7.4 | alphaXiv QA が `paper="2211.08451"` 由来の可能性を示した。`2303.07103` 本体の主張か、Chalmers `2211.08451` の引用かを PDF 直読で分離するまで SOURCE 化禁止。 |

PDF QA からの即時判断:

| Claim | 判断 |
|:---|:---|
| C3 | `2505.05481` は最優先。Structure & Quality 系の近傍性を確認し、同一性発見か反論かを切る。 |
| C4 | alphaXiv QA だけでは弱い。公的射要件を支えるなら `2201.09316` を別途直読する。 |
| C5 | `2303.07103` は有望だが、paper id 取り違え疑いがある。Gauntlet に入れる前に原典確認が必要。 |
| C1 | この PDF QA では MB 語彙の荷重は取れていない。Friston / active inference 系を別便で読む。 |

## SOURCE Direct Read Results

`arxiv.org/pdf/2505.05481` と `arxiv.org/pdf/2303.07103` を直接取得し、`pdftotext -layout` で本文照合した。以下は `[SOURCE: arXiv PDF]` として扱える。ただし本文への引用文作成は、挿入箇所の文脈に合わせて再確認する。

| Paper | Confirmed source facts | Manuscript effect |
|:---|:---|:---|
| [SOURCE: arXiv PDF] arXiv:2505.05481 — Ryan Williams, `Structure & Quality` | five structure-quality relation modelsを提示する。内訳は bare functionalism, structurally-determined, qualitatively-determined, mixed-determination, equivalent systems。Q-S space は structure と quality が相互にどの程度決定するかを 2D 座標で表す。 | C3/C4 への近傍論文。本文の「値ではなく構造」へ接続できるが、同時に「quality を structure から第一原理で導出できる」とは読めない。 |
| [SOURCE: arXiv PDF] arXiv:2505.05481 — limitation | 同論文は、quality が structure から第一原理で導出されるとは主張しない。構造-質の関係型を記述的モデルとして提示する。 | §7.4 failure condition に使うべき制限条件。C3 は「private quality の絶対値を消す」のではなく「public WHAT に降ろせる構造だけを科学概念化する」と書くのが安全。 |
| [SOURCE: arXiv PDF] arXiv:2303.07103 — David J. Chalmers, `Could a Large Language Model be Conscious?` | §2 で、LLM consciousness を肯定する側に feature X の二条件を課す。LLM が X を持つこと、X を持つ系が conscious とみなせる理由を要求する。 | C5 の条件付き主張を補強する。Tolmetes 側の X は MB 条件、world/self model、recurrence/memory、workspace、agency のいずれに対応するか明示が必要。 |
| [SOURCE: arXiv PDF] arXiv:2303.07103 — objections | §3 で、否定側にも feature X の二条件を課す。検討される主要候補は biology, senses/embodiment, world/self models, recurrent processing, global workspace, unified agency。 | §7.4 の failure condition を Chalmers 型に再編できる。特に C5 は「現行 LLM の意識を断定」ではなく「LLM+ で X を満たす経路」を扱う形が強い。 |
| [SOURCE: arXiv PDF] arXiv:2303.07103 — alphaXiv QA anomaly resolved | 取得した `2303.07103` PDF は Chalmers 本文であり、feature X 条件も本文中に確認できる。PDF テキスト内に `2211.08451` は検出されなかった。 | 前節の paper id 取り違え疑いは SOURCE 昇格の阻害要因ではなくなった。ただし、artifact には anomaly と resolved を両方残す。 |

SOURCE 化後の修正判断:

| Claim | 更新判断 |
|:---|:---|
| C3 | `2505.05481` は反論というより近傍・制限条件。C3 の「主観性 = 客観性の射」は、quality の全消去ではなく、quality を科学概念として扱える公共射の条件に限定して読むべき。 |
| C4 | `2505.05481` は private quality の残余を認めるため、T17_n の射程限定に効く。`2201.09316` はなお未読。 |
| C5 | `2303.07103` は最優先 SOURCE に昇格。feature X 型により、LLM μ の主張を外部読者に通る条件文へ変換できる。 |
| C1 | 今回の PDF 直読では未昇格。categorical active inference / MB density 系を次便で読む。 |

## C1 SOURCE Direct Read Results

対象: C1「MB は所与ではなく、状態と境界の相互決定の不動点として導出される」

`arxiv.org/pdf/2406.07577`, `2208.12173`, `2308.00861`, `2204.11900`, `2506.05794`, `2508.16877` を直接取得し、`pdftotext -layout` で本文照合した。以下は `[SOURCE: arXiv PDF]` として扱える。

| Paper | Confirmed source facts | C1 / T0 effect |
|:---|:---|:---|
| [SOURCE: arXiv PDF] arXiv:2406.07577 — Smithe, `Structured Active Inference` | generative models are cast as systems “on an interface”; the interface is presented as a compositional abstraction of the usual Markov blanket. The paper also defines an agent with polynomial interface `p`, with a generative model and controller, and states that `p` generalizes the classical Markov blanket of the generative model. | Strong support for treating MB as interface/compositional boundary rather than a static partition. Difference from T0: Smithe generalizes MB into polynomial/interface structure; T0 derives MB as a state-boundary equilibrium pair from a maintenance relation. |
| [SOURCE: arXiv PDF] arXiv:2208.12173 — Smithe, `Compositional Active Inference II` | polynomials are assigned a formal role akin to Markov blankets: they define the shape/boundary/interface of a system, and morphisms of polynomials describe information flow between coupled boundaries. The paper functorially relates statistical games to open dynamical systems through approximate inference doctrines; the opposite direction is hypothesized as future adjoint work. | Strong support for the categorical-active-inference lineage. Difference from T0: this paper gives interface/dynamics semantics and a possible adjoint direction; it does not derive a blanket from a Galois fixed point of state and boundary. |
| [SOURCE: arXiv PDF] arXiv:2308.00861 — Tull, Kleiner, Smithe, `Active Inference in String Diagrams` | predictive processing / active inference are formulated in string diagrams. The paper gives diagrammatic accounts of generative models, Bayesian updating, perception, planning, active inference, and free energy, and proves compositionality properties for free energy over open models. | Support for public morphism-style presentation of active inference and compositional free energy. It is not a direct MB derivation source. Use for §7.5 context, not as the main T0 SOURCE. |
| [SOURCE: arXiv PDF] arXiv:2204.11900 — Sakthivadivel, `Towards a Geometry and Analysis for Bayesian Mechanics` | the paper argues that Markov blankets can be constructed too widely if one conditions on enough hidden variables, and that the blanket plays at most an auxiliary role in a constraint-centered formulation. It also states that the Markov blanket is subsumed under constraints determining system-like and non-system-like states. | Strongest external support for “MB is not the primitive.” Difference from T0: Sakthivadivel moves from constraints/system-ness to FEP and blankets; T0 moves from maintenance relation `M` to `L ⊣ R` and fixed-point equilibrium pairs. |
| [SOURCE: arXiv PDF] arXiv:2506.05794 — Possati, `Markov Blanket Density and Free Energy Minimization` | Markov blanket density `ρ(x)` is defined as a continuous scalar field measuring degree of conditional independence at each spatial point. The paper distinguishes this from the classical binary conditional-independence property and states that binary MB is recovered in the discrete limit. It also makes free-energy descent depend on `(1 - ρ(x))`. | Refinement / pressure on T0. C1 should not sound like MB is only a crisp binary boundary. T0 can absorb this as a graded maintenance/boundary-strength reading, but §2.0 should avoid treating the equilibrium pair as spatially sharp without qualification. |
| [SOURCE: arXiv PDF] arXiv:2508.16877 — Baltieri, Torresan, Nakai, `A coalgebraic perspective on predictive processing` | the body is treated as an interface, equivalent to channels coupling agent and environment; these components constitute the so-called Markov blanket. The paper argues that generative model and generative process need not be structurally isomorphic; coalgebraic maps are used to formalize behavioral equivalence beyond structural similarity. | Indirect C1 support and direct pressure on T2. For T0, it supports interface/channel language. For LLM comparison, it warns against requiring structural isomorphism where behavioral/interface equivalence is the right external criterion. |

### C1 External Position

| External group | What it gives | What it does not give | T0 positioning |
|:---|:---|:---|:---|
| Categorical interface group: `2406.07577`, `2208.12173`, `2308.00861` | MB/interface as compositional boundary; functorial active inference; compositional free energy | A derivation of MB as `Fix(R∘L) ≅ Fix(L∘R)` | Cite as prior art for category-theoretic active inference, then state T0's distinct move: MB is not merely represented as interface, it is derived as equilibrium of state-boundary mutual determination. |
| Constraint / Bayesian mechanics group: `2204.11900` | MB auxiliary/subsumed by constraints; FEP as constrained entropy/free-energy relation | The state-boundary Galois construction used in T0 | Use as strongest external support for rejecting MB as primitive. T0 can be framed as a constructive version of that rejection. |
| Graded blanket group: `2506.05794` | conditional independence as spatially graded density `ρ(x)`; binary MB as limit case | Category-theoretic fixed-point derivation | Use as a limitation/extension: T0 currently gives an order/fixed-point skeleton; graded/density geometry is a refinement layer. |
| Coalgebraic behavior group: `2508.16877` | interface/body as channels; behavioral equivalence over structural copy | A direct MB derivation | Use to discipline wording around `≅`: for human/LLM comparison, structural sameness is too strong unless the intended equivalence is explicitly fixed. |

### C1 Insertion Guidance

| Target | Suggested insertion |
|:---|:---|
| §2.0 opening | Add one short paragraph after the claim that MB is not given: existing categorical active inference already treats blankets as interfaces/boundaries, but T0's distinct step is to derive the boundary from a maintenance relation and fixed-point correspondence. |
| §2.0 footnote near T0 | Mention `2406.07577`, `2208.12173`, and `2204.11900` as external priors; keep `2308.00861` for compositional free energy, not MB derivation. |
| §7.5 table | Add or revise a row for “categorical active inference / Bayesian mechanics.” Emphasize support plus difference: interface formalization and constraint subsumption are prior art; Galois fixed-point derivation is this paper's local move. |
| Future limitation | Add one sentence that Possati-style MB density suggests a graded refinement of `B ≤_B B'` / `Θ(B)` rather than a replacement of T0. |

## Current Judgment

`2505.05481` は C3/C4 の制限条件、`2303.07103` は C5 の外部反論ゲート、`2406.07577` / `2208.12173` / `2204.11900` / `2506.05794` / `2508.16877` は C1 の外部 prior として SOURCE 昇格済み。本文へ次に反映するなら、§2.0 の opening と §7.5 表だけに限定する。T0 の差分は「既存研究は MB を interface / constraint / density として扱う。本稿は MB を `M -> L,R -> L ⊣ R -> Fix -> MB` として導出する」で固定する。

同名メタファイルは未確認状態:

| 面 | Path |
|:---|:---|
| expected meta | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_v0.7_日本語.meta.md` |
| related meta | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_英語版草稿.meta.md` |
