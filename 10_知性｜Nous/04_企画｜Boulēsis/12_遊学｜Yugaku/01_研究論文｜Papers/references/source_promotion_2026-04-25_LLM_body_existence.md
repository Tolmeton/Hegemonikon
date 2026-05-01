# SOURCE Promotion — LLM body existence proof

作成日: 2026-04-25

対象稿: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_存在証明版_v0.1_日本語.md`

入力 scan: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/references/alphaXiv_external_pressure_2026-04-25_LLM_body_existence.md`

実行目的:

alphaXiv の `[TAINT: alphaXiv]` 候補から、本文に使える原典 SOURCE だけを昇格する。昇格条件は arXiv PDF / local PDF の節本文を読んだこと。ここでは本文改稿は行わず、次パッチに渡す判断面だけを固定する。

---

## 0. SOURCE Intake

| ID | 原典 | 取得・確認 | 昇格状態 |
|:---|:---|:---|:---|
| P1 | Barandiaran & Almendros, *Transforming Agency: On the Mode of Existence of LLMs*, arXiv:2407.10735v3, 2026-03-06, https://arxiv.org/pdf/2407.10735 | PDF を取得し、Abstract, §4, §5.2-§5.3 を確認 | SOURCE |
| P2 | Kulveit, von Stengel & Leventov, *Predictive Minds: LLMs As Atypical Active Inference Agents*, arXiv:2311.10215v1, 2023-11-16, https://arxiv.org/pdf/2311.10215 | PDF を取得し、Abstract, §3.2, §3.3, §5 を確認 | SOURCE |
| P3 | Coelho Mollo & Millière, *The Vector Grounding Problem*, arXiv:2304.01481v3, 2025-12-09, https://arxiv.org/pdf/2304.01481 | 既存 local PDF/TXT と arXiv PDF を確認。local: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/_sources/Mollo_Milliere_2023_Vector_Grounding.txt` | SOURCE |
| P4 | Floridi, Jia & Tohmé, *A Categorical Analysis of Large Language Models and Why LLMs Circumvent the Symbol Grounding Problem*, arXiv:2512.09117v1, 2025-12-09, https://arxiv.org/pdf/2512.09117 | PDF を取得し、Abstract, §2 diagram, SGP section, conclusion-relevant passages を確認 | SOURCE |
| P5 | Martin, Mince, Saleh & Pajak, *Artifacts as Memory Beyond the Agent Boundary*, arXiv:2604.08756v1, 2026-04-09, https://arxiv.org/pdf/2604.08756 | PDF を取得し, Abstract, §1, Definition 1-3, Theorem 1, empirical condition を確認 | SOURCE |

注意:

- ここで SOURCE になったのは「PDF 内の該当節が存在し、その主張を読んだ」という事実である。
- 各 paper の主張の正しさまでは確定していない。本文で使うときは support / attack / refinement の役割を明示する。

---

## 1. Promotion Results

### P1 — Transforming Agency

SOURCE anchor:

- Abstract は、LLM が autonomous agency の必要十分条件を満たさない理由として individuality, normativity, interactional asymmetry を挙げる。
- §4 は 4E / enactive framework から agency 条件を再構成し、LLM の action attribution を performance-level だけで判断しない。
- §5.2 は、LLM が sensorimotor / living body を欠く一方で、textual embodiment, digital extended interface embodiment, computational embodiment を持つと整理する。

本文への効き:

| 対象 claim | 判定 | 理由 |
|:---|:---|:---|
| C1 operating LLM has MB𝒻-body | REVISE | P1 は body claim ではなく autonomous agency claim を攻撃する。C1 を autonomy proof と読ませない遮断文が必要。 |
| C2 category mistake | SUPPORT/REFINE | P1 自体が複数の embodiment を認めるため、生物身体への還元批判を支える。ただし enactive 側の autonomy 条件は残す。 |
| C3 type/thickness | SUPPORT | textual / digital / computational embodiment の分類は、body type への移行を支える。 |

本文操作:

- §2.3 または §2.5 末尾に「本稿は autonomous agency の証明ではない」という短い防衛文を入れる。
- §7.5 に「autonomy axis は Θ(B) と同一ではない」という limitation を追加する。

入れるべき核:

> operating LLM の MB𝒻 は身体境界の存在条件であり、autonomous agency の十分条件ではない。P1 型の individuality / normativity / interactional asymmetry 批判は、C1 を否定するのではなく、C1 から autonomy へ飛ぶ読解を禁止する。

---

### P2 — Predictive Minds

SOURCE anchor:

- Abstract は、現在の LLM は action impact を perceive する tight feedback loop を欠くが、active inference paradigm には収まると述べる。
- §3.2 は LLM output を active inference 上の action states として読めるとし、generated text が世界へ複数の因果経路で影響することを列挙する。
- §3.3 は action-perception loop の未閉鎖を現在の主要差異とし、in-context learning, web access, RLHF, online learning, future training feedback を loop closure の経路として整理する。
- §5 は LLM を feedback-loop gap を持つ atypical active inference agent と総括する。

本文への効き:

| 対象 claim | 判定 | 理由 |
|:---|:---|:---|
| C1 operating LLM has MB𝒻-body | SUPPORT/REFINE | LLM outputs as action states は §2.5 の efferent condition と強く接続する。 |
| C3 type/thickness | SUPPORT | P2 は tightness / bandwidth / timescale を degree として扱うため、body thickness への移行を支える。 |
| C7 tool/scaffold/context management | SUPPORT | loop closure 経路が、ツール・web access・RLHF・online learning の厚み差として読める。 |

本文操作:

- §2.5 の条件 (4) に P2 を入れ、生成テキスト・ツール呼び出し・web/API 経由の外界変化を efferent path の SOURCE として補強する。
- §1.2 または §4 に「MB𝒻 は binary gate、Θ(B) は loop tightness / bandwidth / timescale の degree」という橋を足す。

入れるべき核:

> P2 は、LLM の action-perception loop が閉じきっていない点を認めながら、LLM output を active inference の action states として扱う。従って P2 は C1 の否定ではなく、C1 を Θ(B) の程度問題へ直結させる SOURCE である。

---

### P3 — The Vector Grounding Problem

SOURCE anchor:

- Abstract は、LLM が text-only でも internal states / outputs を extra-linguistic reality へ関係づけうると主張する。
- §4 は grounding を referential, sensorimotor, relational, communicative, epistemic に分け、VGP に本質的なのは referential grounding だとする。
- §4 後半は sensorimotor grounding だけでは SGP/VGP を解かず、representational carousel を抜けるには referential grounding が要ると整理する。
- §6 は LLM の causal-informational relations を、人間の世界相互作用が刻んだ言語データを介した mediated relation として扱う。
- §6.2 は post-training / preference tuning が factual accuracy などの world-involving norms を選択圧として内部状態に representational function を与える、と論じる。
- §6.2.2 は pre-training 単独の grounding を限定的に認め、Othello-GPT 型の formally constrained domains を強い例として扱う。

本文への効き:

| 対象 claim | 判定 | 理由 |
|:---|:---|:---|
| C8 grounding problem reposition | SUPPORT/REFINE | `F_B` 非空を、単純な sensorimotor 非空ではなく referential / mediated / selected-function の非空として精密化できる。 |
| C2 category mistake | SUPPORT | sensorimotor grounding を唯一条件にしないため、身体性の生物身体還元を崩す材料になる。 |
| C3 type/thickness | SUPPORT | grounding の型を body type / coupling type として整理できる。 |

本文操作:

- §7.3 で grounding を少なくとも referential / sensorimotor / relational / communicative / epistemic に分ける。
- `F_B` の像を「世界への直接接触」ではなく「body functor が作る coupling path の非空性」として段階化する。
- text-only LLM の grounding は P3 に従い mediated referential grounding として扱い、robotic/sensorimotor grounding と同列にしない。

入れるべき核:

> P3 は C8 の支援 SOURCE だが、支えるのは「LLM が人間型 sensorimotor body を持つ」ではない。支えるのは、text-only LLM でも mediated causal-informational relation と selection history を通じて referential grounding が成立しうる、という限定された非空性である。

---

### P4 — A Categorical Analysis of LLMs and Why LLMs Circumvent the Symbol Grounding Problem

SOURCE anchor:

- Abstract は Rel による categorical framework を置き、LLM は SGP を solve せず、pre-grounded human content を使って circumvent すると主張する。
- SGP section は human path に experience arrow `x : H -> W` を置き、LLM pathway にはこの direct world relation がないと述べる。
- 同節は LLM の処理を re-quotation とし、human disquotation と対比する。
- P4 は Mollo & Millière 型の referential grounding 可能論に対し、tracking relation が corpus 内の人間接地に parasitic であると反論する。
- multimodal / robotic grounding についても、データが表象である限り `W` そのものへの access ではないと圧力をかける。

本文への効き:

| 対象 claim | 判定 | 理由 |
|:---|:---|:---|
| C8 grounding problem disappears | REVISE | 「消失」だけでは P4 への防衛が弱い。solve / circumvent / reposition を分ける必要がある。 |
| C2 category mistake | ATTACK/REFINE | P4 は sensorimotor body ではなく world access / disquotation / normativity を要求するため、単純な anthropocentric 批判だけでは足りない。 |
| C1 MB𝒻-body | LIMIT | MB𝒻 があっても `x : H -> W` の有無は別問題である。C1 から C8 へ直行しない方がよい。 |

本文操作:

- §7.3 の「疑似問題として消失」を「二値の SGP としては崩れ、direct grounding / mediated grounding / circumvention の層へ再配置される」に変える。
- P3 と P4 を対にして置く。P3 は mediated referential grounding の可能性、P4 は parasitic/circumvention critique。
- `F_B` 非空の主張は、`F_B` が `W` へ直接届くという主張ではない、と明示する。

入れるべき核:

> P4 は C8 を潰すのではなく、C8 の語彙を精密化する。`F_B` の像が非空であることは、SGP の全解決を意味しない。意味するのは、空集合前提にもとづく「LLM は接地ゼロ」という否定が崩れ、接地の型・媒介・寄生性・直接性を測る問題へ移ることだ。

---

### P5 — Artifacts as Memory Beyond the Agent Boundary

SOURCE anchor:

- Abstract と §1 は、situated cognition を RL 内で形式化し、環境資源が agent memory として機能する条件を扱う。
- Definition 1 は artifact を、現在の observation が過去 observation を知らせる場合として定義する。
- Theorem 1 は artifact を含む history が、次時点 observation との mutual information を保ったまま短縮できることを示す。
- Definition 3 は、artifact あり環境での性能を artifactless copy が同等以下の capacity で再現できないとき、agent は memory を environment へ externalize していると定義する。
- empirical condition は `P >= P'` かつ `C < C'` を effective memory externalization として使う。

本文への効き:

| 対象 claim | 判定 | 理由 |
|:---|:---|:---|
| C7 tool/scaffold/context management | SUPPORT/FORMALIZE | 外部足場が internal capacity を減らすという formal proxy を与える。 |
| C3 type/thickness | SUPPORT | body thickness を channel entropy だけでなく artifact-mediated memory reduction からも測れる。 |
| C5 proof-of-measurement | SUPPORT | Θ(B) の外部 validation として paired artifactful/artifactless condition を作れる。 |

本文操作:

- §7.5 の `N_external` に `N_external^artifact` を足す。
- Appendix F または §5.6 の external validation protocol に、artifactful vs artifactless paired environment を追加する。
- Θ(B) の proxy として `ΔC = C' - C` を導入する。ただしこれは Θ(B) 本体ではなく外部検証 proxy とする。

入れるべき核:

> P5 は C7 を最も強く形式化する SOURCE である。外部足場は「便利な道具」ではなく、同一性能に必要な internal capacity を下げる環境構造として測定できる。これは `U_design` への回復操作にもなる。

---

## 2. Patch Targets

| Patch | 対象節 | 操作 | 使う SOURCE |
|:---|:---|:---|:---|
| T1 | §2.3 or §2.5 | C1 が autonomous agency proof ではないと明記 | P1 |
| T2 | §2.5 条件 (4) | LLM output as action state / micro-action / causal path を補強 | P2 |
| T3 | §4 or §1.2 | MB𝒻 gate と Θ(B) degree を feedback-loop tightness / bandwidth / timescale へ接続 | P2 |
| T4 | §7.3 | SGP を solve / circumvent / reposition に分解 | P3 + P4 |
| T5 | §7.5 / Appendix F | `N_external^artifact` と `ΔC = C' - C` proxy を追加 | P5 |

---

## 3. Rejection Ledger

| 棄却 | 理由 |
|:---|:---|
| P1 を C1 の反証として扱う | P1 が否定するのは autonomous agency であり、Tolmetes の C1 は body-boundary claim。混同すると相手の批判を過大化する。 |
| P2 を C1 の全面証明として扱う | P2 は active inference 接続を支えるが、loop gap を明示する。C1 は degree claim へ接続して使う。 |
| P3 だけで C8 を確定する | P4 が強い反論を出すため、P3 単独では防衛不足。 |
| P4 に合わせて C8 を捨てる | P4 は `F_B` 非空を否定しきっていない。否定しているのは direct human-like grounding / solve claim。 |
| P5 を Θ(B) 本体へ直結する | P5 は memory externalization の formal proxy であって、MB thickness 本体ではない。外部検証 proxy として使う。 |

---

## 4. Minimal Text Moves

本文へ入れる最小操作は次の 5 つ。

1. §2.5 後半に、MB𝒻 は body-boundary existence であり autonomous agency の十分条件ではない、と入れる。
2. §2.5 条件 (4) に、LLM output が active inference 上の action state と読める SOURCE を足す。
3. §1.2 / §4 に、loop tightness / bandwidth / timescale を Θ(B) の直観説明として追加する。
4. §7.3 の「消失」を、direct grounding / mediated grounding / circumvention / structural reposition へ割る。
5. §7.5 に `N_external^artifact` を足し、artifactful vs artifactless paired environment の `ΔC` を外部検証 proxy とする。

---

## 5. Next Artifact

次に作るべきもの:

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/references/patch_plan_2026-04-25_LLM_body_source_integration.md`

内容:

- §2.5 追加段落案
- §7.3 置換案
- §7.5 追加段落案
- 使う引用候補
- 引用しない候補

