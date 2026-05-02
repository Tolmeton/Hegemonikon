# AIDB (AI Database) Article Collection Status

## 1. Project Overview

AIDB is a project dedicated to collecting and indexing AI-related news, summaries, and research articles to build a comprehensive knowledge base for the Hegemonikón system.

## 2. Phase Progress

| Phase | Description | Status | Details |
| :--- | :--- | :--- | :--- |
| **Phase 1-3** | Bulk Article Collection | ✅ Complete | **795 articles** collected as markdown. |
| **Phase 4** | Refinement & Metadata | ✅ Complete | Formatting and publish date extraction. |
| **Phase 5** | LanceDB Indexing (KB) | ✅ Complete | **1,331 chunks** indexed for semantic search (Restored 2026-02-06). |
| **Phase 6** | arXiv Automation | ⏳ Pending | Weekly auto-collection of arXiv papers from AIDB links. |

## 3. Storage & Infrastructure

- **Knowledge Base (Vector)**: `mekhane/gnosis/lancedb/` (Index: `aidb`).
- **Raw Data Reference**: `mekhane/gnosis/` (Source markdown relocated from legacy `forge/Raw/aidb/`).
- **Management Script**: `hegemonikon/mekhane/peira/scripts/aidb-kb.py`.

## 4. Current Usage

- **Semantic Search**: CLI tool `aidb-kb.py search "query"` allows for fast retrieval of related AI trends.
- **RAG Integration**: Linked to the `Gnōsis` RAG engine used by the AI agent during technical consultation.

## 5. Digestion Depth Audit (2026-02-05)

A `/fit` diagnostic audit revealed that while AIDB is successfully indexed, it has not yet been "Naturalized" into the system's operational logic.

### Audit Verdict: 🔴 Superficial (表面付着)

| Metric | Status | Evidence |
| :--- | :--- | :--- |
| **Workflow Integration** | ❌ 0% | No `nous/workflows` currently utilize `aidb-kb.py`. |
| **Lineage Tracking** | ❌ 0% | AIDB articles are not referenced in the `lineage` fields of system components. |
| **Autonomous Access** | ❌ 0% | The `Digestor` and `Auto-Digest Agent` (WBC) prioritize arXiv over AIDB. |

**Mitigation Plan**:

1. **Workflow Integration**: ✅ **Complete**. Enable `aidb-kb.py` search within the `/sop` (Standard Operating Procedure) workflow (PHASE 0.5).
2. **Metabolic Expansion**: Update the `Digestor` pipeline to include high-value AIDB technical articles in the "Chemotaxis" phase.
3. **Traceability**: Enforce reference to AIDB source articles when updating `SKILL.md` or `lineage` metadata.
4. **Active Metabolism**: Read and implement article content iteratively to move from "Search" to "Eat".

## 6. Data Recovery Success (2026-02-06)

A "Metabolic Failure" was resolved through a surgical recovery of the system's "Bone Marrow" (raw articles).

### Recovery Timeline

- **Blocker Identification**: 2026-02-05. Identified missing raw data in the Debian environment.
- **Hypothesis Testing**: Scanned local ZIP archives and Google Drive.
  - *Result*: ZIPs contained only session metadata; G-Drive was missing the core markdown articles.
- **Surgical Discovery**: Detected 762 markdown files within the **Windows Recycle Bin** on the external drive (`/media/makaron8426/04CCD284CCD27002/$RECYCLE.BIN/...`).
- **Restoration**:
  1. Copied 762 articles to `mekhane/peira/Raw/aidb/`.
  2. Rebalanced the dataset (761 valid articles confirmed via `aidb-kb.py stats`).
  3. Re-downloaded the BGE ONNX embedding model.
- **Current Status**: **✅ Operational**. Internal KB search (PHASE 0.5) is now functional on the full 761-article dataset.

## 7. Naturalization & Digestion Registry (Step 2)

As of **2026-02-06**, the system has transitioned to **Step 2 (Iterative Digestion)**. Following the `/m` (本気モード) and `/jukudoku` protocols, the focus is on manual deep reading and selective implementation.

### Prioritized Content: LLM Agent & Prompt Engineering

The following high-value substrates have been identified for prioritized digestion:

| ID | Title | Key Topic | Status |
| :--- | :--- | :--- | :--- |
| **95916** | 人を支えるAIの現在地 (多角的ダイジェスト) | **Best-of-∞**, GDPVAL, Moral Evol | ✅ Jukudoku Complete |
| **72854** | 競争環境でのLLMエージェントが自発的に協力し始める現象 | Multi-Agent Cooperation | ⏳ Pending |
| **72609** | 複数LLM協調アプローチ「マージング」「アンサンブル」「協力」 | Ensemble Strategies | ⏳ Pending |
| **76468** | プロンプト自動生成手法『Minstriel』 & LangGPT | Meta-Prompting | ❌ Premium (Empty) |
| **73575** | ドメイン知識適応「読解タスクテキスト変換」 | Domain Adaptation | ⏳ Pending |
| **71720** | エージェント化手法「SelfGoal」 (サブゴール木構造解体) | Planning & Goal Decomposition | ⏳ Pending |

### Key Findings from Step 2 (Iterative Digestion)

#### 1. Best-of-∞: Asymptotic Performance of Test-Time Compute (95916)

- **Source**: `arxiv:2509.21091` (found via AIDB 95916).
- **Insight**: Increasing "Test-time compute" (generating multiple answers and voting) significantly improves performance.
- **Optimization**: "Best-of-∞" suggests dynamic sampling:
  - **High Variance**: If initial answers are diverse, increase sampling/voting count.
  - **High Consensus**: If answers converge quickly, decrease count to save compute.
- **Application**: Targeted for **Synergeia** enhancement (Variance-adaptive majority vote).

#### 2. GDPVAL: Real-World Economic Task Evaluation (95916)

- **Source**: OpenAI Research.
- **Insight**: Models fail most when instructions are "short and ambiguous."
- **Confirmation**: This reinforces the **Zero Entropy Preprocessing** protocol in Hegemonikón.

### Protocol: /jukudoku

All articles in Step 2 MUST be processed via the `/jukudoku` (Deep Reading) protocol to ensure zero-blind-spot naturalization before any implementation or skill update.

## 8. Additional Knowledge Substrates (Discovery 2026-02-06)

A secondary, high-quality knowledge substrate was identified in the local "Archive" directory.

- **Source**: `/home/makaron8426/ダウンロード/Brain/99_🗃️_保管庫｜Archive/AI用ナレッジベース/AI用ナレッジベース［Web］`
- **Quantity**: **197 articles** (Markdown format).
- **Quality**: Full-text available for all articles (unlike AIDB premium-locked articles).
- **Themes**: RAG defects, Persona engineering, Prompt strategies, Multi-agent coordination, etc.
- **Role**: Serves as a primary alternative to premium-locked AIDB articles.

## 9. Content Integrity Audit (2026-02-06)

A statistical audit was performed on the AIDB substrate to evaluate accessibility.

- **Total Articles**: 761
- **Premium Locked**: 316 (**42%**)
- **Free Full-Text**: 445 (**58%**)
- **Verdict**: While nearly half are locked, the usable majority (58%) and the high-density "Digest" articles provide sufficient "Bone Marrow" for system naturalization.

## 10. Substrate 2: Brain KB Digestion Project (2026-02-06)

Following the identification of the 198-article "Brain KB" collection, a systematic digestion project has been initiated to replace the loss-leader premium AIDB articles with full-text insights.

### 10.1. Progress Tracker

- **Target Count**: 198 articles.
- **Completed**: 16 articles (**8.1%**).
- **Status**: 🔴 Initial Stage (Goal: >10% by NEXT).

### 10.2. Completed Items Registry

| Date | Article | Core Insight | Implementation Target |
| :--- | :--- | :--- | :--- |
| 2026-02-06 | 増加するだけで向上...法則 | Inference Scaling Law: $c \approx \exp(a \cdot k^{-b})$ | Synergeia Adaptive Sampling |
| 2026-02-06 | ReConcile 円卓会議 | 3-step convergence / Confidence Abstention | Specialist v2.1 |
| 2026-02-06 | Mem0 メモリ設計 | Fact Extraction -> Contextual Update | Anamnesis Auto-Update |
| 2026-02-06 | RAG 19の欠陥パターン | 98% defect rate; Embedding bottleneck (34%) | Gnōsis Quality Audit |
| 2026-02-06 | 21の性質 (プロンプト) | 6 axes; Additive properties failure | Skill Framework Refinement |
| 2026-02-06 | メタ認知プロンプティング | 5-stage cognitive loop (MP) | Specialist /dia workflow |
| 2026-02-06 | BDI 実装 | Belief-Desire-Intention ontology | Agent Internal State |
| 2026-02-06 | 生産環境AIエージェント 9BP | SRP, Tool-calling, KISS, Portability | Synergeia/Jules Architecture |
| 2026-02-06 | 推論特化型LLMの弱点 | Completeness (44%) vs Logic (7%) | Quality Gates (Edge Cases) |
| 2026-02-06 | 計画のステップ...目標見失う | Goal Drift; Telos re-injection | Long-running workflows |
| 2026-02-06 | 指示が増えるとLLMはどうなる | Instruction limit (150-250); Omission | Prompt Chunking / Tiered Task |
| 2026-02-06 | AIエージェント本番運用実態 | 68% Human-in-the-loop; Custom Orch | Human-Agent Symbiosis |
| 2026-02-06 | 心の理論実装 | Hypothesis Generation/Evaluation cycle | Multi-Agent ToM |
| 2026-02-06 | RAGの失敗パターン7選 | Retrieval, Augmentation, Generation gaps | Gnōsis Quality Gate |
| 2026-02-06 | MetaRAG | Monitoring-Evaluation-Planning (5 loop) | RAG Accuracy Optimization |
| 2026-02-06 | 信頼できるAI組織設計 | HRO Principles (5 axes); Scaling axes | Specialist Tiered Design |

---
*Updated: 2026-02-06. References: Brain KB, conversion_id: bot-f7bf082b-0c48-4859-9df7-04e3a0339d98.*
