# ハーネス設計学 (Ergon Project)

> **目的**: 忘却論に基づいて LLM ハーネスの理論と設計原理を定式化し、HGK 自身のハーネスを改善する。
>
> **圏論的意味**: Hegemonikon ⊣ Ergon
> HGK (内部状態 μ) と Ergon (能動状態 a) の間の随伴対。
> 左随伴 L: Cog → Exec (計画→実行 = boot) と
> 右随伴 R: Exec → Cog (結果→信念 = bye) の関係。
>
> **核命題**: ハーネスは**不均一な忘却場**である。その方向的構造が LLM の行為可能性を結晶化する。したがって設計対象は「何を考えさせるか」よりも「何を忘れさせ、何を通すか」である。

## 概念

- **Ergon (ἔργον)**: 仕事、行為、成果物。HGK が外界に作用するための制御インフラ。
- **ハーネス**: CLAUDE.md, rules, hooks, skills, MCP tools の総体。LLM の Markov blanket (b = s × a) を設計する学問。
- **忘却論との接続**: モノグラフ「工学的補助線」(V→VI→VII→X) の**終着点**。4論文の成果が実装に結実する場所。+ Paper XI (C/E 分離) + Paper A (制約 = 抽出ターゲット)。

## ディレクトリ構造

```
09_能動｜Ergon/
├── README.md                      # 本ファイル
├── 01_理論｜Theory/               # 忘却論に基づくハーネス理論 (Aisthēsis)
├── 02_設計｜Design/               # ハーネス設計パターン (Dianoia)
├── 03_検証｜Verify/               # HGK 批評と外部実証 (Ekphrasis)
└── 04_実装｜Impl/                 # HGK v2 実装計画 (Praxis)
```

## MAP

### 01_理論｜Theory (4件)
- [01_markov_blanket.md](./01_理論｜Theory/01_markov_blanket.md) — **ハーネスの忘却論的定式化** (H 関手, H3 分離, VFE, 6 原則)
- [02_adjunction_hgk_ergon.md](./01_理論｜Theory/02_adjunction_hgk_ergon.md) — HGK⊣Ergon 随伴対とハーネス関手
- [03_gsd_reinterpretation.md](./01_理論｜Theory/03_gsd_reinterpretation.md) — 外部実証の忘却論的分析 (GSD→timakin→Can.ac→LangChain)
- [04_scale_hierarchy.md](./01_理論｜Theory/04_scale_hierarchy.md) — ハーネスの RG フローとスケール階層

### 02_設計｜Design (6件)
- [01_active_states_spec.md](./02_設計｜Design/01_active_states_spec.md) — Isolate パターン (サブエージェント委譲)
- [02_boundary_maps_nt.md](./02_設計｜Design/02_boundary_maps_nt.md) — C/E/M 境界の自然変換
- [03_llm_deterministic.md](./02_設計｜Design/03_llm_deterministic.md) — LLM 確率的射 vs Hook 決定的射
- [04_l_functor_schema.md](./02_設計｜Design/04_l_functor_schema.md) — L (boot) 関手スキーマ
- [05_r_functor_schema.md](./02_設計｜Design/05_r_functor_schema.md) — R (bye) 関手スキーマ
- [06_boundary_contracts.md](./02_設計｜Design/06_boundary_contracts.md) — ハーネス契約

### 03_検証｜Verify (2件)
- [01_consistency_check.md](./03_検証｜Verify/01_consistency_check.md) — HGK 現行ハーネス批評
- [02_l_r_consistency.md](./03_検証｜Verify/02_l_r_consistency.md) — boot/bye 整合性検証

### 04_実装｜Impl (2件)
- [01_roadmap.md](./04_実装｜Impl/01_roadmap.md) — HGK ハーネス v2 ロードマップ
- [02_state_classification.md](./04_実装｜Impl/02_state_classification.md) — 状態型分類 (Paper X Type 1/2/3)

### 忘却論依存
- Paper I: 忘却関手 U, VFE = −Accuracy + Complexity
- Paper V: β 関数, 次元的頑健性定理
- Paper X: CM 戦略, boot⊣bye, Drift-Performance 逆 U 字
- Paper XI: H3 分離定理, C-E-M 3 軸, Face Lemma

### 外部実証
- timakin (2026): ハーネスエンジニアリング概念の整理
- Can.ac Hashline: ハーネス変更のみで 15 モデル改善 (Grok 10 倍)
- LangChain Terminal Bench 2.0: 30 位→5 位 (+13.7pt)
- Anthropic: 長時間稼働エージェント向け二層構造
- Phil Schmid: モデル=CPU, ハーネス=OS
- Martin Fowler: ハーネス=制御と信頼性維持のツールと実践

### 関連 PJ
- [04_随伴｜OssAdjoint](../04_随伴｜OssAdjoint/) — Agency-Agents 随伴
- [05_自律｜Autophonos](../05_自律｜Autophonos/) — 自律エージェント
- [08_形式導出｜FormalDerivation](../08_形式導出｜FormalDerivation/) — HGK⊣Ergon 随伴の形式導出

## 6 設計原理

| 原理 | 忘却論的根拠 | 処方 |
|:---|:---|:---|
| P1: C 最大化・E 最小化 | XI H3: dQ/dE ≈ 0 | rules を蒸留し E を圧縮 |
| P2: 状態依存ロード | X.1: 最適忘却は状態の関数 | タスク型に応じて動的ロード |
| P3: 逆 U 字の意識 | X.3: Drift-Performance | prior 占有率を 2-5% に維持 |
| P4: C を Hook で環境強制 | N-12 + XI §7.8.1 | rules の C 成分を Hook に移植 |
| P5: 3 軸安定性 | XI §9.6 Face Lemma | C/E/M 各軸の独立性を検証 |
| P6: RG 蒸留 | V β 関数 + V §3.4 | 不動点構造のみ保存し残りを削除 |

## STATUS

- **現状**: Theory 4件 + Design 6件 + Verify 2件 + Impl 2件 = **14ファイル**
- **刷新**: 2026-04-12 FEP サブエージェント設計 → 忘却論に基づくハーネス設計学に転換
- **次**: HGK ハーネス v2 の計測基盤と状態依存ロードの実装

---

*Created: 2026-03-09*
*Refreshed: 2026-04-12 — サブエージェント設計からハーネス設計学へ転換*
