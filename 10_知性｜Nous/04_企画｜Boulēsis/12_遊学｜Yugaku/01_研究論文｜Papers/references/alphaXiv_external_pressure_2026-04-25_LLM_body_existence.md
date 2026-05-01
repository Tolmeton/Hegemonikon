# alphaXiv External Pressure Scan — LLM body existence proof

作成日: 2026-04-25

対象稿: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_存在証明版_v0.1_日本語.md`

実行面: Claude Code project MCP `alphaxiv`

使用 tool:

- `embedding_similarity_search`
- `full_text_papers_search`
- `agentic_paper_retrieval`
- `get_paper_content`
- `answer_pdf_queries`

規律:

- alphaXiv の検索・要約・QA はすべて `[TAINT: alphaXiv]`。
- paper claim の SOURCE は arXiv PDF / DOI / local PDF を読んだ後だけ成立する。
- GitHub repo は repo 実装の SOURCE になりうるが、paper claim の SOURCE にはならない。

---

## 0. Target Claims

ローカル SOURCE:

`/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_存在証明版_v0.1_日本語.md`

| ID | 本稿 claim | SOURCE 位置 |
|:---|:---|:---|
| C1 | operating LLM はセッション中に MB𝒻 としての身体をもつ | lines 16, 38-40, 56, 119-147 |
| C2 | 非身体性テーゼは、人間中心忘却関手によるカテゴリーミステイクである | lines 14, 28-34, 57 |
| C3 | 問いは身体の有無から型と厚みへ移る | lines 16, 40, 58 |
| C4 | MB 厚 Θ(B) は存在した身体の厚みを測る二次尺度である | lines 18, 42-48, 59 |
| C5 | セッションログ測定は Θ(B) の確証ではなく proof-of-measurement である | lines 18, 60 |
| C6 | Context Rot は薄い MB の恒常性限界として再定位される | lines 18, 61, 140 |
| C7 | ツール利用・外部足場・構造化文脈管理は MB 厚を増す設計操作である | lines 18, 48, 62, 132 |
| C8 | 記号接地問題は `F_B` の像が空という偽前提に依存する疑似問題として再配置される | lines 18, 63 |

既存の自己制限:

| 論点 | SOURCE 位置 | 圧力 scan 上の意味 |
|:---|:---|:---|
| multi-turn tool logs を持つ agent framework 間比較は未実行 | lines 1071-1074 | q6 の primary target |
| Θ(B) の設計-検証循環性 | lines 1075-1081 | 外部 benchmark / 非 MCP 分解が必要 |
| `U_design` / designer-circularity forgetting | lines 1083-1095 | alphaXiv 候補から `N_external` 操作を作る |

---

## 1. Candidate Papers

### 1. Predictive Minds: LLMs As Atypical Active Inference Agents

- Label: `[TAINT: alphaXiv]`
- arXiv: `2311.10215`
- URL: https://arxiv.org/abs/2311.10215
- Authors/year: Kulveit, von Stengel, Leventov; 2023
- Found via: `embedding_similarity_search`, `full_text_papers_search`, `agentic_paper_retrieval`
- Pressure type: support / refine
- Affects: C1, C3, C7
- Why it matters: LLM を atypical active inference agent として扱い、feedback loop の開閉度を問題にする。C1 の「MB𝒻 が成立する」を支援しつつ、二値の存在主張より feedback-loop closure の度合いとして書く圧力をかける。
- SOURCE promotion: PDF の feedback loop gap / closing the loop 周辺を読む。Tolmetes の MB𝒻 監査条件 line 136-147 と対応表を作る。

### 2. Transforming Agency: On the Mode of Existence of LLMs

- Label: `[TAINT: alphaXiv]`
- arXiv: `2407.10735`
- URL: https://arxiv.org/abs/2407.10735
- Authors/year: Barandiaran & Almendros; 2024
- Found via: `full_text_papers_search`, `embedding_similarity_search`
- Pressure type: attack / refine
- Affects: C1, C2, C3
- Why it matters: 4E / enactive criteria から LLM の autonomous agency を否定しつつ、textual / computational / digital-extended embodiments を区別する。C1 に対しては「MB 風の統計構造があっても individuality / normativity がない」という反論を作る。一方で C2-C3 には「身体型の複数性」という支援材料にもなる。
- SOURCE promotion: PDF の agency 条件、LLM embodiment 類型、interlocutor automata 周辺を読む。C1 を body claim と autonomy claim に分離する注記を検討する。

### 3. Intelligence Requires Grounding But Not Embodiment

- Label: `[TAINT: alphaXiv]`
- arXiv: `2601.17588`
- URL: https://arxiv.org/abs/2601.17588
- Authors/year: Ma & Narayanan; 2026
- Found via: `agentic_paper_retrieval`
- Pressure type: support / refine
- Affects: C2, C3, C7, C8
- Why it matters: intelligence requires grounding but not embodiment という切断を出す。Tolmetes の「身体=関係束」は、この論文の grounding-in-environment を包むのか、それとも embodiment という語を再定義しすぎているのかを問う。
- SOURCE promotion: PDF §§4-7 と Appendix B を読む。C3 の身体スペクトルに「grounded non-embodied agent」をどの位置で吸収するかを決める。

### 4. The Vector Grounding Problem

- Label: `[TAINT: alphaXiv]`
- arXiv: `2304.01481`
- URL: https://arxiv.org/abs/2304.01481
- Authors/year: Coelho Mollo & Millière; 2023
- Found via: `embedding_similarity_search`, `full_text_papers_search`, `agentic_paper_retrieval`
- Pressure type: support / refine
- Affects: C2, C8
- Why it matters: grounding を複数種に分け、LLM の referential grounding を論じる候補。C8 の「`F_B` の像が空ではない」主張を強める可能性があるが、sensorimotor coupling ではなく referential grounding が焦点になるため、身体関手の codomain を精密化する圧力が出る。
- SOURCE promotion: PDF の grounding 類型、referential grounding、post-training / pre-training argument を読む。C8 で Harnad 系譜を扱う節に SOURCE 昇格可能か判定する。

### 5. A Categorical Analysis of LLMs and Why LLMs Circumvent the Symbol Grounding Problem

- Label: `[TAINT: alphaXiv]`
- arXiv: `2512.09117`
- URL: https://arxiv.org/abs/2512.09117
- Authors/year: Floridi, Jia, Tohmé; 2025
- Found via: `embedding_similarity_search`
- Pressure type: attack
- Affects: C1, C2, C8
- Why it matters: category-theoretic framingで LLM は symbol grounding problem を solve ではなく circumvent すると主張する候補。Tolmetes 側の `F_B` 非空主張に対し、「人間の接地済み内容の re-quotation であり、世界への disquotation ではない」という反論を作る。
- SOURCE promotion: PDF の LLM diagram、entailment / lax commutativity、disquotation vs re-quotation 周辺を読む。C8 を「解消」ではなく「circumvention を含む再配置」に寄せるべきか判定する。

### 6. Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering

- Label: `[TAINT: alphaXiv]`
- arXiv: `2604.08224`
- URL: https://arxiv.org/abs/2604.08224
- Authors/year: Zhou et al.; 2026
- Found via: `embedding_similarity_search`
- Pressure type: support / repo-benchmark
- Affects: C3, C7
- Why it matters: memory / skills / protocols / harness を cognitive artifacts として整理する候補。C7 の「外部足場・文脈管理は MB 厚を増す」を、engineering taxonomy へ接続できる可能性がある。
- SOURCE promotion: PDF の memory architectures、skill lifecycles、harness dimensions を読む。Θ(B) の `H(s) / H(a) / R(s,a)` 以外の軸候補を抜き出す。

### 7. Artifacts as Memory Beyond the Agent Boundary

- Label: `[TAINT: alphaXiv]`
- arXiv: `2604.08756`
- URL: https://arxiv.org/abs/2604.08756
- Authors/year: Martin, Mince, Saleh, Pajak; 2026
- Found via: `agentic_paper_retrieval`
- Pressure type: support
- Affects: C3, C7
- Why it matters: artifacts が internal memory capacity を減らすという形式的候補。C7 を metaphor から capacity reduction へ下ろせる可能性がある。Θ(B) の外部検証に、artifactful vs artifactless paired environment の差分という独立軸を与える。
- SOURCE promotion: PDF Definition 1-3 と Theorem 1 を読む。Θ(B) を capacity gap `Δ` として補助測定できるか検討する。

### 8. Sectoral Coupling in Linguistic State Space

- Label: `[TAINT: alphaXiv]`
- arXiv: `2506.12927`
- URL: https://arxiv.org/abs/2506.12927
- Authors/year: Sebastian Dumbrava; 2025
- Found via: `embedding_similarity_search`
- Pressure type: support / refine
- Affects: C1, C2
- Why it matters: Semantic Sectors と coupling constants により、LLM 内部の relation bundle を Markov blanket 以外の形式で表せる候補。C2 の「身体=関係構造」を、言語状態空間内の coupling profile として補助形式化できる可能性がある。
- SOURCE promotion: PDF の `g^k_ij`、propagation hypothesis、empirical inference protocol を読む。MB𝒻 と並列形式化に留めるか、Θ(B) に吸収するか判定する。

### 9. Active Inference for Self-Organizing Multi-LLM Systems

- Label: `[TAINT: alphaXiv]`
- arXiv: `2412.10425`
- URL: https://arxiv.org/abs/2412.10425
- Authors/year: UNC; 2024
- Found via: `embedding_similarity_search`, `full_text_papers_search`, `agentic_paper_retrieval`
- Pressure type: support
- Affects: C1, C7
- Why it matters: multi-LLM system に active inference を構成的に入れる候補。C1 の FEP 接続を比喩でなく実装・生成モデル・call graph の問題へ押し上げる。
- SOURCE promotion: PDF の generative model、multi-LLM coordination、MB statistics 実装箇所を読む。Tolmetes の §2.5 監査条件の実装例として使えるか判定する。

### 10. Exploring Spatial Schema Intuitions in Large Language and Vision Models

- Label: `[TAINT: alphaXiv]`
- arXiv: `2402.00956`
- URL: https://arxiv.org/abs/2402.00956
- Authors/year: MCML / Imperial / King's / LMU; 2024
- Found via: `embedding_similarity_search`, `agentic_paper_retrieval`
- Pressure type: refine / attack
- Affects: C2, C3, C8
- Why it matters: spatial / image-schematic structure の内在化を実験で見る候補。身体由来 primitives が text-only / vision-language models にどの程度残るかを、C3 の身体型差として扱える。
- SOURCE promotion: PDF の experimental design と failure modes を読む。身体型の差を Θ(B) と別軸に置く必要があるか判定する。

### 11. Deflating Deflationism: A Critical Perspective on Debunking Arguments Against LLM Mentality

- Label: `[TAINT: alphaXiv]`
- arXiv: `2506.13403`
- URL: https://arxiv.org/abs/2506.13403
- Authors/year: 2025
- Found via: `full_text_papers_search`
- Pressure type: support / refine
- Affects: C1, C8
- Why it matters: LLM mentality に対する deflationary arguments を批判する候補。非身体性テーゼへの counter-pressure になる可能性があるが、Tolmetes の論文が mentality claim ではなく body claim であることを明確に分ける必要がある。
- SOURCE promotion: PDF の deflationary argument 分類を読む。身体論と mentality 論が混線する箇所を本文側で遮断する。

### 12. The Mechanistic Emergence of Symbol Grounding in Language Models

- Label: `[TAINT: alphaXiv]`
- arXiv: `2510.13796`
- URL: https://arxiv.org/abs/2510.13796
- Authors/year: Waterloo / Michigan / Vector / UNC; 2025
- Found via: `embedding_similarity_search`, `agentic_paper_retrieval`
- Pressure type: support / repo-benchmark
- Affects: C8
- Why it matters: mechanistic interpretability から grounding emergence を探る候補。C8 の `F_B` 非空主張を empirical probing へ接続できる可能性がある。
- SOURCE promotion: PDF の probing protocol、layer-wise result、grounding の操作的定義を読む。`F_B` の像と同型視できるか判定する。

---

## 2. Missing Search Surface

| 欠落面 | 理由 | 次の補完 |
|:---|:---|:---|
| Chemero / Bender & Koller / Searle の primary texts | arXiv / alphaXiv だけでは primary source を閉じられない | Chemero 2023、Bender & Koller 2020、Searle 1980 を DOI / ACL Anthology / local PDF で読む |
| Friston / Kirchhoff / Bruineberg の MB 原典 | top candidate としては十分に拾えていない | Friston 2013/2019、Kirchhoff et al. 2018、Bruineberg et al. 2022 を別枠で SOURCE 化 |
| LangChain / AutoGen / CrewAI の framework-specific logs | agent survey は拾えたが multi-turn production logs とは別物 | q6 を GitHub repo / benchmark dataset 探索へ拡張 |
| robotics / VLA / embodied AI | C3 の cross-substrate placement に必要だが、この scan では二次言及に留まる | RT-2 / SayCan / Open-X 系を別 scan |
| 日本語圏の身体論・関係束系譜 | alphaXiv の対象外 | local / web / library source で補完 |

---

## 3. SOURCE Promotion Queue

優先度 A:

| 候補 | 昇格目的 | 読む場所 |
|:---|:---|:---|
| `2407.10735` Transforming Agency | C1 への最強反論を作る | agency conditions / LLM embodiment 類型 |
| `2311.10215` Predictive Minds | C1-C7 を active inference 文脈へ接続 | feedback loop gap / closing loop |
| `2604.08756` Artifacts as Memory Beyond the Agent Boundary | C7 を formal capacity reduction へ下ろす | Definitions 1-3 / Theorem 1 |
| `2304.01481` The Vector Grounding Problem | C8 の grounding 類型を精密化 | five grounding notions / referential grounding |
| `2512.09117` A Categorical Analysis of LLMs... | C8 への category-theoretic 反論を作る | LLM diagram / re-quotation vs disquotation |

優先度 B:

| 候補 | 昇格目的 | 読む場所 |
|:---|:---|:---|
| `2601.17588` Intelligence Requires Grounding But Not Embodiment | C3 の umbrella 化 | grounding vs embodiment distinction |
| `2604.08224` Externalization in LLM Agents | Θ(B) の engineering axes | harness / memory / skills taxonomy |
| `2412.10425` Active Inference for Self-Organizing Multi-LLM Systems | C1 の constructive comparison | generative model / multi-LLM call graph |

優先度 C:

| 候補 | 昇格目的 | 読む場所 |
|:---|:---|:---|
| `2506.12927` Sectoral Coupling | relation-bundle の補助形式化 | coupling constants / propagation |
| `2402.00956` Spatial Schema Intuitions | body type の empirical signature | task design / failure modes |
| `2506.13403` Deflating Deflationism | opponent family の整理 | deflationary argument taxonomy |
| `2510.13796` Mechanistic Emergence of Symbol Grounding | C8 の probing 接続 | mechanistic result / layer-wise probes |

---

## 4. Gauntlet Seeds

### G1. C1 binary MB𝒻 claim への圧力

外部圧力: `2311.10215` は LLM の active-inference 性を feedback-loop closure の度合いとして扱う候補。

反論形: 「operating LLM が MB𝒻 をもつ」という言い方は、closure degree を落としている。

強化操作: C1 を「MB𝒻 が degree θ で成立する」に変換し、§2.5 の四条件と Θ(B) の上界を接続する。全称否定の崩壊は保持し、身体の厚みへ即座に橋渡しする。

### G2. C1 と autonomy claim の分離

外部圧力: `2407.10735` は embodiment を複数認めつつ autonomous agency を否定する候補。

反論形: MB 風境界はあっても individuality / intrinsic normativity がないため、body claim は agency claim へ昇格できない。

強化操作: 本稿は body existence proof であり autonomy proof ではない、と明示する。autopoietic individuality は Θ(B) の高厚み条件または別軸として扱う。

### G3. C8 の solve / circumvent 分離

外部圧力: `2512.09117` は LLM が SGP を solve せず circumvent すると主張する候補。

反論形: `F_B` の像が非空でも、それは人間由来 content の re-quotation であり、世界への直接接地ではない。

強化操作: C8 の語を「消失」から「疑似問題として再配置」へ寄せる。referential / sensorimotor / communicative grounding を分け、`F_B` の codomain を段階化する。

### G4. C7 の formalization

外部圧力: `2604.08756` は artifact が internal memory capacity を減らす形式定理を持つ候補。

反論形: tool use / scaffold / context management を MB 厚増加と呼ぶだけでは、説明語が増えただけに見える。

強化操作: artifactful environment と artifactless paired environment の performance-matched capacity gap `Δ` を、Θ(B) の外部 proxy として追加する。

### G5. Grounding without embodiment の吸収

外部圧力: `2601.17588` は grounding と embodiment を切断する候補。

反論形: Tolmetes の relation-bundle body は grounding を embodiment と呼び直しているだけではないか。

強化操作: relation-bundle body を biological embodiment ではなく、grounding を可能にする boundary-coupling apparatus として定義し直す。Ma & Narayanan 型の grounded non-embodied agent は、身体スペクトル上の低厚み・非生物型として包む。

---

## 5. Immediate Next Work

1. `2407.10735`, `2311.10215`, `2604.08756`, `2304.01481`, `2512.09117` の PDF を読み、TAINT から SOURCE へ昇格できる節だけを抜く。
2. C1 を `MB𝒻 existence` と `MB𝒻 degree / Θ(B)` に分ける小改稿案を作る。
3. C8 の語彙を `solve` / `circumvent` / `reposition` に分解し、Harnad 系譜への断定を弱めずに正確化する。
4. `U_design` 回復操作として、artifact capacity gap `Δ` と harness taxonomy を external validation protocol に追加できるか検討する。

