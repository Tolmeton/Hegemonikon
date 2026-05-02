---
rom_id: rom_2026-03-14_circulation_cognition_v54
session_id: e68b574b-b0cd-453c-8330-e01a6caf811a
created_at: 2026-03-14 12:27
rom_type: rag_optimized
reliability: High
topics: [循環幾何, 認知科学, ω, entropy_production, NESS, FEP, System1_System2, ADHD, Fisher_information, stiff_sloppy, information_geometry, cognitive_style, temporal_irreversibility]
exec_summary: |
  循環パラメータ ω の認知科学接続を v5.1→v5.4 で体系化。操作的定義 (3段階推定)、
  System 1/2 方向性修正 (ω大=System2)、7文献による実験的証拠体系を構築。
  C2 確信度 30%→70%。Chen (2025) stiff-sloppy FIM とのブロック対角対応を発見。
---

# 循環幾何 × 認知科学接続の深化：ω パラメータの多層的アプローチ {#sec_01_overview .information_geometry .cognitive_science}

> **[DECISION]** ω 大 = System 2 (熟慮・高EP・ウィルパワー消費)、ω 小 = System 1 (直観・低EP・省エネ)。方向性を修正し確定。

> **[DECISION]** C2 確信度: 30% → 60% → 70%。実験的証拠の蓄積により段階的に引き上げ。

> **[DISCOVERY]** Chen et al. (2025) の stiff/sloppy FIM 構造が、我々のブロック対角 G = g^(F) ⊕ g^{(c,F)} と構造的に対応する。ω 方向が stiff direction に含まれる可能性 [仮説 65%]。

## 1. 三者対応の基本構造 {#sec_02_triad .core_mapping}

> **[DEF]** 循環幾何の3パラメータと認知科学概念の対応:

| パラメータ | 幾何学的意味 | 認知科学的解釈 | 推定可能性 |
| --- | --- | --- | --- |
| θ (十分統計量) | 確率分布の自然パラメータ | 信念内容 = 「何を信じるか」 | V に依存 |
| ω (循環強度) | 確率流の非可逆成分 | 認知スタイル = 「どう考えるか」 | V から独立 |
| V (ポテンシャル) | 環境のエネルギー地形 | 環境・課題構造 | 外部条件 |

> **[FACT]** g^{(c,F)} = 1/ω² は V と独立 (ブロック対角性 G = g^(F)(θ) ⊕ g^{(c,F)}(ω))。
> → 「どう考えるか」(ω) の推定可能性は「何を信じるか」(V) の複雑さに影響されない。
> これが認知科学的に意味すること: 認知スタイルは信念内容から独立に観測・学習可能。

## 2. ω の操作的定義 — 3段階推定パイプライン {#sec_03_operational .measurement .pipeline}

> **[RULE]** ω 推定の3レベル:

```text
Level 1 (model-free):
  測定: Time-Irreversibility Index (TII) = ⟨x(t)·x(t+τ)⟩ の時間反転非対称性
  解像度: 低 (ω ≠ 0 の検出のみ)
  既存研究: Nartallo-Kaluarachchi (2025) review

Level 2 (model-based):
  手法: multivariate OU 過程 dX = -B(X-μ)dt + σdW のフィット
  推定: B = S + A の対称/反対称分解 → ω_k = A の固有値
  解像度: 中 (ω の大きさと空間パターン)
  先行研究: Wang et al. (2015) — potential + circulation の分解

Level 3 (information-geometric):
  手法: g^{(c,F)} = Fisher 計量の循環ブロックを直接推定
  検証: g^{(c,F)} が V (= S の固有値構成) に依存しないことを確認
  先行研究: 本研究の新規提案
```

## 3. System 1/2 方向性修正 {#sec_04_system12 .correction .fundamental}

> **[DECISION]** 初期仮説「ω 大 = System 1」を修正 → 「ω 大 = System 2」

> **[FACT]** 修正の根拠:

```text
1. エネルギー論: EP ∝ ω² — 循環コストは ω² に比例
   → 高 ω = 高コスト = System 2 (意志的・努力的)
   → 低 ω = 低コスト = System 1 (自動的・省エネ)

2. ウィルパワー: System 2 は意志力 (willpower) を消費する
   → 意志力消費 ∝ EP ∝ ω²
   → ω 大 = ウィルパワー消費大 = System 2

3. 実験データ整合:
   - sleep (ω ≈ 0): System 0 — 最低 EP
   - resting (ω 小): System 1 — 自動処理
   - task (ω 大): System 2 — 熟慮的処理
   → ω は覚醒-認知の連続体上のパラメータ
```

> **[CONFLICT]** 「直観は高速だがエネルギー消費は大きい可能性」への反論:
> "エネルギー" の定義に依存するが、FEP 文脈では EP (entropy production) が relevant。
> ウィルパワーのような意志力は確実に System 2 のほうが使う。
> 直観 (System 1) は高速だが EP 的には低コスト — 局所勾配追従。

## 4. 実験的証拠体系 {#sec_05_evidence .empirical .literature}

### 4.1 EP/Irreversibility と意識レベル {#sec_05a_consciousness}

> **[FACT]** 意識状態ごとの EP 階層:

| 状態 | EP (≈ω²) | 出典 | 被引用数 |
| --- | --- | --- | --- |
| 覚醒 → deep sleep | 高 → 低 | Idesis et al. 2023 | — |
| 健常 → Alzheimer | 高 → 低 | Cruzat et al. 2023, J. Neurosci. | 41 |
| 安静 → cognitive task | 低 → 高 | Nartallo-Kaluarachchi 2025 review | — |

> **[DISCOVERY]** Cruzat et al. (2023): AD で temporal irreversibility が global/local/network レベルで崩壊。
> 認知低下と直接相関。古典的神経認知マーカーより高い分類精度。
> → ω_trait が認知予備力 (cognitive reserve) のバイオマーカーとなる可能性。

### 4.2 Fisher 情報量と認知個人差 — Chen et al. (2025) {#sec_05b_chen .critical}

> **[DISCOVERY]** Chen et al. (2025) arXiv:2501.19106:
> pairwise maximum entropy model を task fMRI に適用。
> FIM の固有値分解 → **stiff dimensions** (小変動で大影響) / **sloppy dimensions** (大変動で小影響)。
> stiff dimensions の微小な個人差が認知パフォーマンスを予測。

> **[FACT]** 本研究との対応表:

| Chen et al. (2025) | 本研究 | 対応関係 |
| --- | --- | --- |
| Fisher Information Matrix | G = g^(F) ⊕ g^{(c,F)} | 同じ概念の異なるパラメタ化 |
| stiff dimensions | g^{(c,F)} = 1/ω² 方向 | [仮説] ω 方向は stiff |
| sloppy dimensions | g^(F)(θ) の冗長方向 | [仮説] V の冗長パラメータ |
| DMN-WMN 分離 | ブロック対角 G | 構造的類似 |
| 0-back vs 2-back | ω 小 vs ω 大 | System 1 vs System 2 |

> **[OPINION]** Chen の stiff-sloppy 構造は我々のブロック対角性の固有値分解的表現。
> もし ω 方向が stiff direction に含まれることが実験で確認されれば、
> 「認知スタイルは信念内容から独立に推定可能」が数学以外の実験的根拠からも支持される。

### 4.3 AuDHD と ω {#sec_05c_adhd .clinical}

> **[FACT]** 関連文献:

| 研究 | 対象 | 主要結果 |
| --- | --- | --- |
| Sohn et al. 2010 (93cit.) | ADHD 青年期 | 非線形 EEG complexity が定型と異なる |
| Papaioannou et al. 2021 | ASD + ADHD 成人 | MSE が群間で異なる |
| Kamiński et al. 2026 | ADHD 小児 | Complexity biomarker で分類 |

> **[RULE]** AuDHD 仮説:

```text
[仮説 40%] ADHD = ω_state の制御が不安定
  → 過集中 (hyperfocus) = 一時的に ω を極端に大きくする状態
  → 注意散漫 = ω が急激に低下する状態
  → 問題は ω の「値」ではなく ω のダイナミクス (dω/dt の分散)

[仮説 35%] ASD = ω_trait 自体が定型と異なる (方向は未確定)
```

## 5. trade-off 恒等式の認知的意味 {#sec_06_tradeoff .theorem}

> **[DEF]** g^(c) · g^{(c,F)} = (σ⁴/4) · I_F^{sp} — 循環コストと学習効率の積は V に依存しない

> **[FACT]** §5.4.3 (circulation_theorem.md v2.2) の改訂内容:
> trade-off 恒等式は Explore/Exploit の二項対立ではなく、ω の二面性:
> - g^(c) = ω² = 行使コスト (pragmatic) — ω を大きくすると高い
> - g^{(c,F)} = 1/ω² = 学習効率 (epistemic) — ω を小さくすると効率的
> → 同一パラメータ ω の二面性として trade-off が成立

## 6. 実験検証ロードマップ {#sec_07_roadmap .future}

> **[RULE]** 3段階実験計画:

```text
Phase 1 (Proof of concept): HCP resting-state fMRI
  → OU fitting → ブロック対角検証 → g^(c)·g^{(c,F)} ≈ const 確認

Phase 2 (認知相関): HCP + 認知タスクバッテリー
  → ω_trait/ω_state 算出 → 認知指標との相関 → stiff-sloppy 再現

Phase 3 (臨床応用): ADHD/ASD コホート + 定型対照
  → 群間 ω 分布比較 → ω_state ダイナミクス → 服薬 (methylphenidate) 効果
```

## 7. 残課題と確信度 {#sec_08_remaining}

| 課題 | 確信度 | 状態 |
| --- | --- | --- |
| ω ↔ cognitive style 対応 (C2) | [推定 70%] | 7文献で支持、直接研究未存在 |
| Chen stiff ≈ ω 方向 | [仮説 65%] | 構造的類似、直接検証未実施 |
| ADHD = ω_state 不安定 | [仮説 40%] | MSE/complexity 文献と整合 |
| ASD = ω_trait 異常 | [仮説 35%] | 方向未確定 |
| 因果方向 (EP → 認知 or 認知 → EP) | [仮説 50%] | 介入研究が必要 |

> **[FACT]** 新規性: ω を直接「認知スタイル」と呼ぶ研究はまだ存在しない。
> 定義的接続 (EP ↔ ω) は確立。解釈的接続 (ω ↔ cognitive style) は本研究の新規提案。

## 関連情報 {#sec_09_references}

- 関連ファイル: `problem_E_m_connection.md` §8.16-8.16.2 (v5.4)
- 関連ファイル: `circulation_theorem.md` §5.4.2-5.4.3 (v2.2)
- 関連 WF: /noe (深層認識), /lys (分析), /zet (探求)
- 先行 ROM: rom_2026-03-14_circulation_cognition (v5.1-5.3 分)

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "ω と認知スタイルの関係は？"
  - "循環幾何と認知科学の接続は？"
  - "System 1/2 の情報幾何学的解釈は？"
  - "ADHD の情報幾何学的モデルは？"
  - "entropy production と意識の関係は？"
  - "Chen et al. (2025) の stiff/sloppy と HGK の関係は？"
  - "trade-off 恒等式の認知的意味は？"
answer_strategy: |
  §2 (三者対応) → §3 (操作定義) → §4 (System 1/2) の順で基礎を確認してから
  §5 (実験的証拠) で裏付け。AuDHD 関連は §5.3 を参照。
  trade-off の認知的意味は §6。検証計画は §7。
  確信度は §8 の表で確認。全て 30-70% の範囲で、確定した結論はない。
confidence_notes: |
  C2 (ω ↔ cognitive style) = 70% — 7文献で間接的支持。直接的=新規提案。
  Chen 対応 = 65% — 構造的類似。直接検証未実施。
  ADHD 仮説 = 40% — EEG complexity 文献と整合するが方向未確定。
  全体: 「面白すぎる」が出発点。車輪の再発明ではないが、立証にはまだ道がある。
related_roms: []
search_expansion:
  - information geometry cognitive science
  - non-equilibrium steady state brain
  - solenoidal flow neural dynamics
  - Fisher information matrix neuroscience
  - cognitive reserve biomarker
  - ADHD entropy EEG complexity
  - Kahneman dual process information theory
  - time irreversibility consciousness
-->

---

*ROM burned at 2026-03-14 12:27 JST*
*Source: Session e68b574b — 循環幾何 × 認知科学接続 v5.1→v5.4*
*圧縮元: problem_E_m_connection.md §8.16-8.16.2 (~400行) + circulation_theorem.md §5.4 (~50行)*
