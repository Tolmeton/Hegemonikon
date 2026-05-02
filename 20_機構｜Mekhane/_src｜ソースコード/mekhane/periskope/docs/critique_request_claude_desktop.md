# Periskopē クエリ生成パイプライン (V1-V3, V5) — 品質批評依頼

## 依頼内容

Periskopē Deep Research Engine のクエリ生成パイプラインに4つの新モジュール (642行) を追加した。
あなたにはローカルファイルシステムへのアクセス権がある。
**以下のファイルを直接読み**、設計・実装・学術的整合性の3軸で敵対的に批評してほしい。

---

## 読むべきファイル (5件 + 統合箇所)

### 新規モジュール (4件)

| # | ファイル | 行数 | 役割 |
|:--|:---------|:-----|:-----|
| 1 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi0_intent_decompose.py` | 163 | V1: LLM でクエリを核心概念・証拠タイプ・暗黙前提・検索視点・反証クエリに分解 |
| 2 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi0_query_planner.py` | 161 | V2: LLM で 3手先読みクエリ計画 (Survey → Analysis → Verification) を生成 |
| 3 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi0_source_adapter.py` | 204 | V3: ルールベースでソース特性に応じたクエリ変形 (LLM不使用) |
| 4 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/phi7_query_feedback.py` | 177 | V5: CoTループ内でV1/V2結果をイテレーション毎に注入 (LLM不使用) |

### 統合箇所 (engine.py 内の具体的な行範囲)

| # | ファイル | 行範囲 | 内容 |
|:--|:---------|:-------|:-----|
| 5 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/engine.py` | L69-90 | 新モジュールのインポート |
| | 同上 | L856-862 | Phase 0 呼び出し元 (返り値の 3-tuple 受取) |
| | 同上 | L1130-1175 | V1 意図分解 + V2 クエリ計画の呼び出しと self への保存 |
| | 同上 | L1245-1270 | V3 ソース適応の呼び出し (Φ3 後に配置) |
| | 同上 | L1545-1580 | V5 CoTループ統合 (analyze_iteration 後に injection) |

### 既存パイプラインの全体像

| # | ファイル | 読む目的 |
|:--|:---------|:---------|
| 6 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/__init__.py` | Φ0-Φ7 全フェーズのエクスポート一覧 |
| 7 | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/reasoning_trace.py` | CoT Search Chain の既存実装 (V5 が接続する対象) |

---

## アーキテクチャ (Phase 0 パイプライン)

```
ユーザークエリ
  ↓
NL API Entity Extraction (既存)
  ↓
[V1] phi0_intent_decompose (LLM: Gemini Flash, ~1s)
  → IntentDecomposition {core_concepts, evidence_type, implicit_assumptions, search_perspectives, negation_queries}
  → context string として後段に注入
  ↓
[V2] phi0_query_plan (LLM: Gemini Flash, ~1s)
  → QueryPlan {step1_survey, step2_analysis, step3_verification}
  → step1 のみ即座に候補追加。step2/3 は V5 が CoT ループで使用
  ↓
[Φ1] Blind-spot Analysis → [W3] Bilingual Expansion
  → 合流: negation_queries + plan_step1 + blind_spot_queries
  ↓
[Φ2] Divergent Thinking → [Φ3] Context Setting (query_type 分類)
  ↓
[V3] phi0_source_adapt (ルールベース, 0ms)
  → SourceAdaptedQueries {source_name → adapted_query}
  → Φ3 の query_type + V1 の core_concepts を使用
  ↓
[Φ4] Pre-search Ranking → Phase 1: 並列検索
  ↓
Phase 2.5: CoT Search Chain (iterative deepening)
  各イテレーションで:
    analyze_iteration → reasoning_step.next_queries
    ↓
    [V5] phi7_query_feedback (ルールベース, 0ms)
      iter 1: reasoning + V2.step2 注入
      iter 2: reasoning + V2.step3 注入
      iter 3+: reasoning + V1.assumptions + coverage_gaps
```

---

## 批評してほしい10の具体的問い

### A. 設計判断の妥当性 (3問)

1. **V1/V2 の LLM コスト**: 検索前に LLM を2回呼ぶ (各500ms-2s)。phi0_intent_decompose.py L120-124 と phi0_query_planner.py L122-126 を見て、このコストは品質向上で正当化できるか？ キーワード抽出やTF-IDF など non-LLM 手法で代替可能か？

2. **V3 がルールベースである判断**: phi0_source_adapter.py L86-116 の `_QUERY_TYPE_ADAPTATIONS` テンプレートを見て、これは LLM で動的に生成すべきか？ 静的テンプレートの利点 (0ms, 決定論的) と欠点 (柔軟性なし) のトレードオフは妥当か？

3. **V5 のイテレーション番号ハードコード**: phi7_query_feedback.py L98-116 の `if iteration == 1 ... elif iteration == 2 ... elif iteration >= 3` を見て、探索のダイナミクスを無視した単純化ではないか？

### B. 構造的脆弱性 (3問)

1. **Re-planning の欠如**: V2 が検索前に立てた計画を V5 が盲目的に注入する。step1 の結果が計画の前提を崩した場合、step2/step3 は無意味になる。engine.py L1545-1580 を見て、この脆弱性の深刻度を評価してほしい。

2. **エンジン状態汚染**: engine.py L1145-1172 で `self._intent` と `self._query_plan` をインスタンス変数に保存している。Phase 0 の一時的状態がエンジン全体のライフサイクルに漏れ出している。これは設計上の問題か？

3. **静かな劣化**: 4モジュール全てが例外時に空オブジェクトを返す (graceful degradation)。phi0_intent_decompose.py L160-162, phi0_query_planner.py L158-160 を確認。劣化の累積検知手段がないが、これで十分か？

### C. 学術的整合性 (3問)

1. **Query Decomposition の先行研究**: V1 の手法は DSP (Khattab et al., 2022), Self-Ask (Press et al., 2022), RARR (Gao et al., 2022) と比較してどうか？ 既知の reinvention か、異なるアプローチか？

2. **Source-Adaptive Query**: V3 の「ソース別クエリ変形」は Federated Search / Meta-Search の query adaptation と同じ問題か？ IR 文献で確立された概念か？

3. **Iterative Query Refinement**: V5 のフィードバック戦略は、RL-based query reformulation (Nogueira & Cho, 2017) や MCTS for search の知見を活用できていないか？

### D. 改善提案 (1問)

1. 上記の分析を踏まえ、**最も優先度が高い改善を3つ**、具体的なコード変更の方向性とともに提案してほしい。

---

## 期待する出力形式

```markdown
## 致命的問題 (すぐに直すべき)
- [問題] → [根拠: ファイル名 L行番号] → [修正提案]

## 重大問題 (次マイルストーンで対応)
- ...

## 軽微・改善提案
- ...

## 学術的位置づけ
- 先行研究との関係: ...
- 新規性の評価: ...

## 優先改善 Top 3
1. [改善内容] — [影響範囲] — [コード変更の方向]
2. ...
3. ...
```
