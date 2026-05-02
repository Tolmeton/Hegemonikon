# GPT-Researcher 深掘り調査

> **優先度**: A
> **repo**: assafelovic/gpt-researcher
> **stars**: 15,000 (adjoint_map 記載値 — 要鮮度検証)
> **HGK 対象**: periskopē (Deep Research Engine)

## import_candidates

1. **STORM 多視点質問生成 → Φ1 盲点分析の強化**
   - Stanford STORM の多視点質問生成手法
   - HGK での用途: Periskopē の Φ1 (盲点分析) フェーズの質問品質向上
   - 判定: [ ]

2. **LangGraph DAG → engine.py (2856行) のモノリシック分割**
   - GPT-Researcher の LangGraph ベースの DAG 実行
   - HGK での用途: Periskopē engine.py のモジュール分割パターン
   - 判定: [ ]

## 調査対象ファイル

- [ ] `gpt_researcher/agent.py` — エージェント定義
- [ ] `gpt_researcher/master/` — マスタープラン生成
- [ ] `multi_agents/` — マルチエージェント連携

## 判定

| candidate | 判定 | 理由 |
|:----------|:-----|:-----|
| STORM 質問生成 | [ ] | |
| LangGraph DAG | [ ] | |

---

*Created: 2026-02-28*
