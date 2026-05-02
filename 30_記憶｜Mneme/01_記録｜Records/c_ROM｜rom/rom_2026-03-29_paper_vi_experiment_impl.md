---
rom_id: rom_2026-03-29_paper_vi_experiment_impl
session_id: AY-2_coherence_invariance
created_at: 2026-03-29 17:30
rom_type: distilled
reliability: High
topics: [Paper VI, 実験実装, rho_judge, Layer 2, E2', E3', /exe 欠陥修正, LLM-as-judge]
exec_summary: |
  Paper VI 実験の /exe 構造的欠陥チェック → 5件 (🔴2 🟡3) 発見 → 修正 → Layer 2 実装完了。
  核心修正: embedding sim ではなく LLM-as-judge をドメイン固有 ρ として使う。
  3ファイル作成: EXPERIMENT_paper_vi.md, rho_judge.py, run_paper_vi_experiment.py
---

# Paper VI 実験実装 — /exe 欠陥修正 + Layer 2 コード

## [DECISION] /exe で発見した5件の構造的欠陥と修正

| # | 欠陥 | 修正 |
|:--|:--|:--|
| W1 🔴 | ドメイン混同: Hyphē そのままでは Linkage の再測定 | ドメイン固有 ρ (LLM-as-judge) |
| W2 🔴 | τ すり替え: similarity threshold ≠ depth/granularity | depth = token budget, granularity = 分割数 N |
| W3 🟡 | depth 操作が離散3条件 | 5条件 (50/200/500/1000/2000 tokens) |
| W4 🟡 | granularity = 情報量変化 | 同一内容の分割数 N (3/5/10/15/20) |
| W5 🟡 | ker(G) が Linkage と同一 | LLM-as-judge ρ でドメイン固有 ker(G) |

## [DECISION] 2層実験構造

- **Layer 1**: Hyphē そのまま。CoT/SKILL テキストに適用。G∘F の汎用性確認
- **Layer 2**: ドメイン固有 ρ (LLM-as-judge) + ドメイン固有 τ。核心の検証

## [DISCOVERY] 実装の核心: rho_judge.py

抽象基底 `RhoMeasure` を定義し、embedding cosine sim と LLM-as-judge を統一:

```python
class RhoMeasure(ABC):
    def __call__(self, i: int, j: int) -> float: ...
    def similarity_trace(self, indices: list[int]) -> list[float]: ...

class EmbeddingRho(RhoMeasure): ...  # Linkage 用
class JudgeRho(RhoMeasure): ...      # Cognition/Description 用
```

`gf_iterate_with_rho()`: hyphe_chunker.py の gf_iterate と同じロジックだが ρ を差し替え可能。

## 成果物

| ファイル | 場所 | 内容 |
|:--|:--|:--|
| EXPERIMENT_paper_vi.md | HyphePoC/ | 実験設計書 (Layer 1+2, 成功基準) |
| rho_judge.py | HyphePoC/ | ρ 抽象化 + LLM-as-judge + gf_iterate_with_rho |
| run_paper_vi_experiment.py | HyphePoC/ | Layer 2 ランナー (E2'+E3'+分析) |

## 実行方法

```bash
cd "60_実験｜Peira/06_Hyphē実験｜HyphePoC"
python run_paper_vi_experiment.py --domain both --backend ochema
```

## 次回アクション

1. **Ochema/cortex 接続確認** → API 疎通テスト
2. **E2' (Cognition) 実行** → 10タスク × 5depth × 5τ × ON/OFF
3. **E3' (Description) 実行** → 10SKILL × 5N × 5τ × ON/OFF
4. **結果分析** → C̄ range を算出し Paper VI §5/§6 に記入

## 成功基準

| 基準 | Layer 2 E2' | Layer 2 E3' |
|:--|:--|:--|
| C̄ τ-range (G∘F ON) | < 0.05 | < 0.05 |
| C̄ τ-range (G∘F OFF) | > 0.05 | > 0.05 |
| C̄ domain-param range (G∘F ON) | < 0.05 (depth) | < 0.05 (N) |

<!-- ROM_GUIDE
primary_use: 次セッションで実験実行時の文脈復元
retrieval_keywords: Paper VI, 実験, rho_judge, Layer 2, LLM-as-judge, E2', E3', run_paper_vi_experiment
expiry: permanent
-->
