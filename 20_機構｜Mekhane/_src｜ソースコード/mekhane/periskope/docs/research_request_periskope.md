# Periskopē クエリ生成パイプライン (V1-V3, V5) — 学術的裏付け調査依頼

## 依頼内容

Periskopē Deep Research Engine のクエリ生成パイプラインに4つの新モジュールを追加した。
これらの設計判断が学術的に妥当か、先行研究で裏付けられるか（または反駁されるか）を調査してほしい。

あなたにはローカルファイルシステムへのアクセス権がある。
**以下のソースコードを直接読み**、設計の背景を理解した上で調査してほしい。

---

## 読むべきファイル

| # | ファイル | 役割 |
|:--|:---------|:-----|
| 1 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi0_intent_decompose.py` | V1: LLM でクエリを意図分解 |
| 2 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi0_query_planner.py` | V2: LLM で 3手先読みクエリ計画 |
| 3 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi0_source_adapter.py` | V3: ルールベースでソース適応 |
| 4 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi7_query_feedback.py` | V5: CoTループ内フィードバック |
| 5 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/reasoning_trace.py` | 既存 CoT Search Chain (V5 接続先) |
| 6 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/engine.py` L1130-1580 | 統合箇所 |

---

## 4機構 × 調査したい学術的問い

### V1: Intent Decomposition (phi0_intent_decompose.py)

**実装の要点**: LLM (Gemini Flash) にクエリを渡し、JSON で {core_concepts, evidence_type, implicit_assumptions, search_perspectives, negation_queries} を抽出。結果を後段 Φ1-Φ4 のコンテキストとして注入。

**調査したい問い**:

- Query Decomposition は検索品質 (Recall/Precision) を統計的に有意に向上させるか？
- 「暗黙前提の抽出 → 反証クエリへの変換」は IR/QA の文献で確立された手法か？
- DSP (Demonstrate-Search-Predict), Self-Ask, RAQA, ReAct における分解戦略との比較
- 分解の粒度 (2-5 概念) は最適か？ 先行研究での最適 granularity の知見は？

### V2: Lookahead Query Planning (phi0_query_planner.py)

**実装の要点**: LLM で 3 ステップの検索計画を事前生成 (Survey → Analysis → Verification)。step1 のみ即座に検索候補に追加、step2/3 は CoT Search Chain の後続イテレーションで V5 経由で注入。

**調査したい問い**:

- 検索前の事前計画 (pre-search planning) は有効か？
- IRCoT (Trivedi et al., 2022), ITER-RETGEN (Shao et al., 2023) における「計画」の役割
- 3 ステップという粒度は最適か？ 段階的深化の最適ステップ数についての知見
- 事前計画 vs 結果駆動型計画 (plan-then-search vs search-then-plan) の比較研究

### V3: Source-Adaptive Query Transformation (phi0_source_adapter.py)

**実装の要点**: Φ3 の query_type 分類結果 + V1 の core_concepts を使い、ルールベースでソース別クエリ変形。例: academic クエリ → Semantic Scholar にはそのまま / Reddit には "ELI5 {query}" / GitHub には "{core_concept} implementation"。

**調査したい問い**:

- ソース別のクエリ変形は Federated Search / Meta-Search の文献で研究されているか？
- Query Routing と Query Adaptation の区別は IR で確立されているか？
- 深層学習ベースのソース適応 (learned query adaptation) の先行研究は？
- テンプレートベース (静的) vs 生成ベース (動的) の変形手法の比較

### V5: Iterative Query Feedback (phi7_query_feedback.py)

**実装の要点**: CoT Search Chain の各イテレーションで、V1 の暗黙前提と V2 のクエリ計画を合成して次のクエリを強化。イテレーション番号に応じた戦略: iter1=step2注入 (narrowing), iter2=step3注入 (verification), iter3+=前提検証 + coverage gap。

**調査したい問い**:

- Iterative Query Refinement の最良アプローチは何か？
- RL-based query reformulation (Nogueira & Cho, 2017) との関係
- MCTS for search / Bayesian query optimization の先行研究
- Query reformulation における「計画注入のタイミング」のエビデンス
- Relevance Feedback (Rocchio Algorithm) との構造的類似性/相違性

---

## 出発クエリ候補 (10本)

1. `query decomposition multi-hop question answering retrieval augmented generation`
2. `iterative retrieval augmented generation query planning pre-search strategy`
3. `federated search query adaptation source-specific transformation meta-search`
4. `iterative query refinement reinforcement learning search reformulation`
5. `chain of thought search iterative deepening information retrieval 2024`
6. `DSP demonstrate search predict Khattab query decomposition pipeline`
7. `Self-Ask compositional question answering Press 2022`
8. `IRCoT interleaving retrieval chain of thought Trivedi 2022`
9. `ITER-RETGEN iterative retrieval generation synergy Shao 2023`
10. `query reformulation user intent decomposition neural information retrieval`

---

## 特に知りたいこと (優先度順)

1. **V1 の「暗黙前提 → 反証クエリ」変換**: これは IR で確立された手法か？ もしそうなら、確立した論文を特定してほしい。もしそうでないなら、最も近い先行研究を示してほしい。

2. **V2 の「3手先読み」の最適性**: 段階的深化 (progressive deepening) における最適ステップ数は研究されているか？ 3 が経験的に妥当かどうかのエビデンス。

3. **V3 の位置づけ**: Federated Search の query routing/adaptation が同じ問題を解決しているなら、V3 は reinvention である。そうでないなら、V3 の新規性を学術的に位置づけてほしい。

4. **V5 のイテレーション依存戦略**: 計画を段階的に注入する (iter1→step2, iter2→step3) アプローチは、学術的に正当化できるか？ Curriculum Learning や Progressive Training との類似性は？

---

## 期待する出力

### 各機構について

```markdown
### V{N}: {機構名}

#### 先行研究 (論文名, 著者, 年, 被引用数)
- {論文}: {1行要約}
- ...

#### 設計判断の裏付け
- 裏付け状況: [強い裏付け / 部分的裏付け / 裏付けなし / 新規 (先行研究なし)]
- 根拠: {具体的な論文・実験結果への参照}

#### 本実装との差分
- {先行研究のアプローチ} vs {本実装のアプローチ}: {差分の分析}

#### 改善の示唆
- 学術的知見から示唆される具体的な改善: {内容}
```

### 総合評価

```markdown
## 総合評価

| 機構 | 裏付け | 新規性 | 改善余地 |
|:-----|:-------|:-------|:---------|
| V1   | ?      | ?      | ?        |
| V2   | ?      | ?      | ?        |
| V3   | ?      | ?      | ?        |
| V5   | ?      | ?      | ?        |

## 最も重要な学術的知見 Top 3
1. ...
2. ...
3. ...
```
