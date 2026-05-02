# 外部実証の忘却論的分析

> **Ergon プロジェクト** 理論文書 03。業界のハーネス実践知を忘却論で統一的に解釈する。

## 1. 実証データ一覧

### 1.1 定量的実証

| 出典 | 変更内容 | 効果 | 忘却論対応 |
|:---|:---|:---|:---|
| Can.ac Hashline (2026) | ツール形式の変更のみ | 15 モデル全改善。Grok: 6.7%→68.3%（10 倍）。トークン 20% 削減 | ker(H) の再設計 = 忘却の方向の最適化 |
| LangChain Terminal Bench 2.0 (2026) | ハーネス改善のみ | 30 位→5 位 (+13.7pt) | CM 戦略の最適化 |
| Vercel 事例 (2026) | ツール 80% 削除 | 速度・正確性が向上 | Complexity↓ = VFE↓ |
| Paper XI Exp0 (2026) | 構造的表記の注入 | 語彙 d=8.73, 品質 d≈0 | H3: dQ/dE ≈ 0, E→Var[Q] |

### 1.2 コンテキスト管理 3 原則 (Lance Martin)

| 原則 | 内容 | **忘却論対応** | Paper X 写像 |
|:---|:---|:---|:---|
| **Reduce** | コンテキストを積極的に縮小。古いツール結果を要約に置換 | G（収束関手）= 蒸留 | R_abstract (Summary 戦略) |
| **Offload** | 情報をプロンプトの外に出す。外部ファイル保存、原子的ツール | boot⊣bye = 外部に MB を構築 | boot⊣bye §4.3 |
| **Isolate** | サブエージェントに委譲。隔離コンテキストで実行、結果だけ返す | MB の外に MB を作る | Paper X §4.3 核心命題 |

### 1.3 設計原則

| 出典 | 原則 | 忘却論対応 |
|:---|:---|:---|
| Phil Schmid (2026) | モデル=CPU, ハーネス=OS | ハーネス H: C_LLM → C_task は OS のカーネルに相当 |
| Martin Fowler (2026) | ハーネス=制御と信頼性維持のツールと実践 | π_a (行為精度) の制御装置 |
| Anthropic (2026) | 初期化エージェント+コーディングエージェント二層構造 | L_boot の構造化（環境セットアップと実行の分離） |
| Anthropic (2026) | progress.json > Markdown | 決定的射（JSON）vs 確率的射（Markdown）の分離 |

---

## 2. 忘却論が予測していた知見

| 業界の経験的発見 | 忘却論の理論的予測 | 定理/命題 | 先行/後発 |
|:---|:---|:---|:---|
| ハーネスだけで 10 倍改善 | C が品質を決定する (H3) | XI H3 | 理論が先行 |
| ツールを減らすと性能向上 | ker(H) 縮小 = Complexity↓ | I: VFE 定義 | 理論が先行 |
| 100 ステップ超でモデルドリフト | Context Rot = 忘却の工学的観測 | X §1.1 | 同時 (AgentSwing 2026) |
| 作り込みすぎはアンチパターン | Drift-Performance 逆 U 字 | X X.3 | 理論が先行 |
| 壊して作り直せる前提で設計 | RG フロー: μ→0 で本質のみ残す | V β 関数 | 理論が先行 |
| Reduce/Offload/Isolate | CM 戦略 = 商関手族 {U_R} | X §3.2 | 理論が先行 |

---

## 3. GSD 概念の統合的再解釈

GSD 2.0 (2024-2025) の実践知も同一の枠組みで統一される:

| GSD 概念 | 忘却論的解釈 | CM 戦略対応 |
|:---|:---|:---|
| Context Pruning | G (収束関手) の部分適用 = Reduce | R_abstract |
| Fractal Summaries | R (bye) のスケール依存的適用 | R_abstract × Scale |
| Boundary Maps | C 軸（制約）の自然変換 | C_H の型整合性保証 |
| Stub Detection | ε (counit) の精度評価 | 自己検証ループ |
| Git Strategy | 等化子（可逆性保全）| Offload（外部永続化） |
| LLM/Deterministic Split | 確率的射 vs 決定的射の分離 | Hook (π_a) vs Rules (π_s) |

---

## 4. アンチパターンの忘却論的診断

### 4.1 ハーネスの過剰設計

timakin:「Manus は 6 ヶ月で 5 回作り直し。LangChain も 3 回再設計。」

忘却論的診断: **VFE の Complexity 項が Accuracy 項の改善を上回った。**
- ハーネスが複雑になるほど Complexity↑
- モデルの能力向上で、以前必要だった制約が不要に（Accuracy が自然に上がる）
- 結果: VFE が悪化 → 作り直しが必要

処方（P6 RG 蒸留）: ハーネスは μ→0 で保存される不動点構造のみで設計し、残りは削除。

### 4.2 ツール過多

Vercel:「包括的ツールライブラリ → ひどい挙動。80% 削除 → 速く正確に。」

忘却論的診断: **ツール数 = |Hom(a, η)| の増大 = 行為空間の拡大 = 選択の Complexity↑。**
- Paper IV 効果量減衰: K (交絡因子) が増えると r_obs が下がる
- ツール数 ∝ K → ツール増 = 性能低下は構造的帰結

処方（P1 + P4）: ツールは C_H で制約し、Hook で不要な呼び出しを環境的に阻止。

### 4.3 モデルドリフト（コンテキスト耐久性）

timakin:「100 ステップ以上で初期指示に従わなくなる。」

忘却論的診断: **Context Rot = Paper X の中心命題そのもの。**
- AgentSwing (Feng et al. 2026): "performance degrades significantly due to accumulation of irrelevant information"
- Paper X 命題 X.1: 最適忘却強度は状態依存
- Reduce/Offload/Isolate は全て Context Rot の緩和策

処方（P2 状態依存ロード）: ステップ数に応じてハーネスの忘却強度を動的に調整。

---

## 5. 再解釈の意義

業界の実践知を「ツール」として取り込むのではなく、忘却論の定理体系から演繹的に再解釈することで:

1. **なぜその仕組みが必要か** — VFE 最小化、ker(H) 最適化、CM 戦略の数理的根拠
2. **いつ拡張・省略すべきか** — 状態型 (Type 1/2/3) に基づく判断基準
3. **何が限界か** — Paper IV 二重天井、Paper X メタ二重天井

---

## 依存関係
- 01_markov_blanket.md: ハーネス関手 H の定義、H3 分離、VFE
- Paper X/XI: 理論的基盤
- 外部: timakin (2026), Can.ac, LangChain, Vercel, Anthropic, Phil Schmid, Martin Fowler

---
*Created: 2026-03-09 | Refreshed: 2026-04-12 — GSD 再解釈を外部実証の忘却論的分析に拡張*
