# PJ-07 Euporía ドメイン構造研究

> **目的**: Euporía 原理 (AY > 0) の適用ドメインを演繹的に導出し、
> 圏論的に定式化する。
>
> **公理**: EFE argmax = 行為可能性の最大化 (Euporía)
> **正典**: [axiom_hierarchy.md §Euporía](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

---

## 現状 (2026-03-11)

### 確定事項

| # | 事項 | 確信度 | 根拠 |
|:--|:-----|:-------|:-----|
| 1 | Euporía は6座標射影 (How) + 適用ドメイン (Where) の2軸構造 | [確信] | axiom_hierarchy.md L651-735 |
| 2 | Kalon はドメインではなく到達点 Fix(G∘F) | [確信] | /ele+ 反駁 矛盾1 |
| 3 | Hóros は二重性を持つ: ドメイン ∧ FEP前提条件 | [推定 70%] | Creator 洞察 + MaxEnt階層 |
| 4 | Linkage = 「チャンクの Markov blanket を構成する行為」 | [推定] | Creator 定義 |

### 暫定ドメイン構造

```
Euporía: AY(f) > 0
│
├── Cognition   (= HGK 体系)   — 認知主体の行為可能性
├── Description (= Týpos)       — 記述の行為可能性
├── Constraint  (= Hóros)       — 制約の行為可能性 [位置論争中]
└── Linkage     (= Index PJ)    — 情報チャンク連動の行為可能性
```

### 未解決の問い

| # | 問い | 優先度 | 方針 |
|:--|:-----|:-------|:-----|
| Q1 | ドメイン数は 3+1 or 4？ (Hóros の位置) | 高 | B の結果から逆算 |
| Q2 | 3ドメインの生成原理は？ (MECE の根拠) | 高 | FEP {μ,s,a,η} からの演繹を試みる |
| Q3 | Polynomial functors で Euporía を定式化可能か？ | 高 | **B プラン として着手** |
| Q4 | Týpos の「Helmholtz」に相当するものは何か？ | 中 | A0 (f: M→L) の分解構造 |
| Q5 | チャンクの MB の圏論的定式化の具体的な射は？ | 高 | Q3 の具体化 |
| Q6 | 「複雑系」は圏論で統一的変分原理を持てるか？ | 低 | 文献調査継続 |

---

## 研究ログ

### Session 1 (2026-03-11, 51b431fd)

- **C (反駁)**: /ele+ で5矛盾を検出。Kalon をドメインから除外
- **A (形式化)**: axiom_hierarchy.md に4ドメイン体系を追記 (L651-735)
- **MECE 検証**: 4ドメインの生成原理を分析中に Hóros の「FEP前提条件」性を発見
- **文献調査**: Spivak "Polynomial Functors" (2023/2025) がキーヒット
- **B 決定**: Polynomial functors で Linkage を定式化する方針を採択
- ROM: `rom_2026-03-11_euporia_domain_structure.md`
- **B (Polynomial Functors)**: `B_polynomial_linkage.md` を作成
  - Monomial y^B と AY の同型を発見: |B| = 行為可能性の数
  - Linkage-AY 同値定理: AY(Idx) > 0 ⟺ ∃c: |MB_1(c)| > |MB_0(c)|
  - **[DISCOVERY]** Hóros = polynomial functor のサブファンクター (方向の制限)
    → ドメインではなく制約条件として自然に出現

---

## MAP — 散在リソース

### 本ディレクトリ内

| ファイル | サイズ | 内容 |
|:---------|:-------|:-----|
| [B_polynomial_linkage.md](B_polynomial_linkage.md) | 10KB | Polynomial Functors による Linkage 定式化。Monomial y^B ≅ AY 同型の発見 |
| [C_noether_horos.md](C_noether_horos.md) | 16KB | Noether 定理と Hóros の関係。Hóros = polynomial functor のサブファンクター |

### Epistēmē (知識基盤)

| ファイル | サイズ | 内容 |
|:---------|:-------|:-----|
| [euporia.md](../../03_知識｜Epistēmē/euporia.md) | **694行** | **母文書** — Euporía 原理の完全定義。§1 ポジショニング, §2 定式化, §2b 射影体系, §2c 感度理論, §3 WF転用, §4 N-7関係, §5 実装, §6 Kalon判定, §7 未解決問い, §7.5 ドメイン体系 |
| [euporia_blindspots.md](../../03_知識｜Epistēmē/euporia_blindspots.md) | — | Euporía 盲点分析 — 見落としやすい AY 違反パターン |
| [wf_evaluation_axes.md](../../03_知識｜Epistēmē/wf_evaluation_axes.md) | — | 8軸 Rubric (α精度 + β簡潔 + 6射影テーゼ) — euporia.md §2b の操作的展開 |

### Kernel (正典)

| ファイル | 内容 |
|:---------|:-----|
| [axiom_hierarchy.md §Euporía](../../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md) | **正典** — Euporía(定理³) の公式定義。射影構造+感度理論+ドメイン体系 |
| [constructive_cognition.md](../../../00_核心｜Kernel/A_公理｜Axioms/constructive_cognition.md) | Týpos 公理 A0 の定義 — Description ドメインの基盤 |
| [kalon.md](../../../00_核心｜Kernel/B_核｜Kernel/kalon.md) | Kalon = Fix(G∘F) の数学的定義 — Generativity ⊂ AY |

### Mneme — ROM (5件)

| ROM | 内容 |
|:----|:-----|
| [rom_2026-03-11_euporia_principle.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-11_euporia_principle.md) | Euporía 原理確立セッションの ROM |
| [rom_2026-03-11_euporia_projections.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-11_euporia_projections.md) | 6座標射影の ROM |
| [rom_2026-03-11_euporia_sensitivity.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-11_euporia_sensitivity.md) | 感度理論 (d値) の ROM |
| [rom_2026-03-11_euporia_domain_structure.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-11_euporia_domain_structure.md) | ドメイン体系の ROM |
| [rom_2026-03-13_euporia_c1_prime.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-03-13_euporia_c1_prime.md) | Euporía C1' (最新改訂) の ROM |

### Mneme — Artifacts

| ファイル | 内容 |
|:---------|:-----|
| [euporia_domain_analysis_2026-03-12.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/euporia_domain_analysis_2026-03-12.md) | ドメイン分析セッション記録 |

### Mneme — KI (知識項目)

| KI | 内容 |
|:---|:-----|
| `theoretical_foundations` (Galois connections) | Euporía の随伴構造 (F⊣G) の形式化 |
| `theoretical_foundations` (FEP functor mapping) | FEP → 統計的関手写像 (AY の理論的基盤) |
| `kalon_principle` (FEP functor mapping) | Kalon-FEP 関手写像 — Generativity ⊂ AY の接続 |
| `theoretical_foundations` (structural scope constraints) | 構造的スコープ制約 — ドメイン MECE の根拠 |

### 関連 Boulēsis PJ

| PJ | 関連 |
|:---|:-----|
| [08_形式導出｜FormalDerivation](../08_形式導出｜FormalDerivation/) | Euporía は形式導出の「定理」部分。導出チェーンの一部 |
| [09_NeuroKalon](../09_NeuroKalon/) | Kalon の神経科学的基盤 — AY との実験的接続 |
| [11_統一索引｜TypeTheoreticIndex](../11_統一索引｜TypeTheoreticIndex/) | Linkage ドメインの型理論的定式化 |

---

*Created: 2026-03-11 | Updated: 2026-03-13 | PJ Owner: Creator + Claude*
