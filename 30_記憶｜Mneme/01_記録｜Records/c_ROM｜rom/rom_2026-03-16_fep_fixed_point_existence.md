---
rom_id: rom_2026-03-16_fep_fixed_point_existence
session_id: 97f74f23-f9e9-40e8-8d24-eb4a8e9bc99f
created_at: 2026-03-16 23:25
rom_type: rag_optimized
reliability: Medium
topics: [FEP, fixed-point, Banach, Lawvere, Grothendieck, fibration, NESS, epsilon-approximate, lax-fixed-point, Kalon, double-category, active-inference, VFE, contraction-mapping]
exec_summary: |
  FEP における不動点 F* = Fix(Q∘Γ) の存在条件を圏論的に形式化。
  Banach-Lawvere 縮小写像条件 (知覚推論)、Grothendieck fibration の不変切断 (能動推論)、
  ε-近似/lax/ω-極限 (NESS) の3層で構成。Kalon ◎/◯/✗ との形式的接続を確立。
search_expansion:
  synonyms: [不動点定理, contraction mapping, enriched category, Cauchy completeness, non-equilibrium steady state, attractor, omega-limit, invariant section, moving target]
  related_concepts: [Helmholtz decomposition, Markov blanket, information attenuation, variational inference convergence]
  abbreviations: [VFE, NESS, KL, D_FEP]
---

# FEP 不動点存在条件の形式化 {#sec_01_overview}

> **[DECISION]** 5つの不動点定理を評価し、**Banach-Lawvere** が FEP に最適と決定 (◎)。
> Lambek, Knaster-Tarski, Lawvere 不動点定理は不適 (✗)。随伴不動点は補助的 (◯)。

> **[DISCOVERY]** 能動推論で Ext が変化する場合、不動点は「点」ではなく **Grothendieck fibration 上の不変切断**。
> D_FEP (double category) の垂直射が fibration の基底変換に対応する。

> **[DISCOVERY]** Kalon の操作的判定 (◎/◯/✗) が不動点理論の3層に自然に対応:
> ◎ = 厳密不動点、◯ = ε-近似不動点、✗ = 降下流初期段階。

---

## §1. 問題定式化 {#sec_02_problem}

> **[FACT]** §1.2 で「lim_{t→∞} F_t = F* ∈ Fix(Q∘Γ)」と定式化。以下が未解決だった:

1. **存在**: Q∘Γ の不動点はいつ存在するか？
2. **一意性**: 不動点は一意か？ (局所的極小の可能性)
3. **到達可能性**: 降下流は不動点に到達するか、近づくだけか？

---

## §2. 候補定理の評価 {#sec_03_theorem_evaluation}

> **[DECISION]** 5定理の FEP 適合性評価:

| 定理 | 適用条件 | FEP 適合性 | 判定 |
|:--|:--|:--|:--|
| Lambek (初期代数) | ω-連続 + 始対象 | VFE の計量的降下を汲み取れない | ✗ |
| Knaster-Tarski | 完備束 + 単調 | [Ext,Int] の VFE 順序は前順序。完備束ではない | ✗ |
| **Banach-Lawvere** | **完備 Lawvere 空間 + 縮小写像** | **§1.4 の VFE 構成と直接接続** | **◎** |
| 随伴不動点 | Γ⊣Q の η/ε | 構造を決定するが存在を保証しない | ◯ |
| Lawvere 不動点 | A → A^A 全射 | FEP の生物学的妥当性を逸脱 | ✗ |

> **[RULE]** Banach-Lawvere が ◎ の理由: §1.4 の VFE を Lawvere enriched metric space として定義しているため、Banach の定理が自然に適用可能。

---

## §3. 定理 1.5.2 — Banach-Lawvere 条件 (知覚推論) {#sec_04_banach_lawvere}

> **[DEF]** 以下の3条件が満たされるとき、F* = Fix(Q∘Γ) が一意に存在し収束する:

1. **Cauchy 完備性**: VFE-エンリッチ関手圏 [Ext, Int] が Cauchy 完備
2. **縮小写像条件**: ∃k ∈ [0,1) s.t. VFE(Φ(F), Φ(G)) ≤ k · VFE(F, G) ∀F,G
   - Φ := Q∘Γ (Helmholtz モナドの underlying endofunctor)
3. **VFE 厳密降下**: VFE(F_{t+1}) < VFE(F_t) (F_t ≠ F* の場合)

> **[FACT]** 物理的解釈:

| 条件 | 物理的意味 |
|:--|:--|
| 完備性 | Int が十分な表現力を持つ (十分に多くのモデルが利用可能) |
| 縮小写像 | Markov blanket を通じた情報減衰 — 各更新ステップで不確実性の一定割合が解消 |
| 厳密降下 | 全ての非最適状態から改善可能 — アルゴリズムが停滞しない |

> **[RESOLVED]** 縮小写像条件 k < 1 の形式的証明を §1.5.2b で完成 (定理 1.5.2b)。以下の §3.1 参照。

### §3.1. 定理 1.5.2b — Dobrushin 縮小係数 η < 1 の証明 {#sec_04a_dobrushin}

> **[FACT]** 3 ステップ証明:

1. **Step 1** (T>0 → 厳密正密度): Langevin 方程式 dx=f(x)dt+σdW (σ²=2k_BT) において、有限温度 T>0 → σ>0 → Hörmander の定理 → p_τ(s|e) > 0 ∀s,e (コンパクト空間上)。
2. **Step 2** (overlap → η_TV < 1): p(s|e)≥δ>0 → Σ_s min(K(s|x₁),K(s|x₂)) ≥ |S|·δ > 0 → η_TV(K) ≤ 1-|S|·δ < 1 (Dobrushin の古典的結果)。
3. **Step 3** (TV→KL 接続): Makur & Zheng (2020) の f-発散縮小係数比較定理 → η_KL(K) ≤ g(η_TV(K)) < 1。

> **[FACT]** 温度依存の上界 (定理 1.5.2b'): η_KL(S) ≤ 1 - c·exp(-ΔV/k_BT)。高温→η→0 (最大縮小)、低温→η→1 (非縮小)。

> **[FACT]** 退化条件 (η=1): T=0 (非物理的) / 単射チャネル (完全知覚) / δ-関数遷移 (決定論的)。

> **[CONFIDENCE]** [確信 85%] — 各ステップは標準的 (Hörmander, Dobrushin, Makur-Zheng)。残存不確実性: 非コンパクト空間での一様下界の存在。

---

## §4. 定義 1.5.3 — Grothendieck 不変切断 (能動推論) {#sec_05_grothendieck}

> **[DEF]** 能動推論の列 Ext_0 → Ext_1 → ... は関手圏の列を生成:
> [Ext_0, Int] → [Ext_1, Int] → ... (Grothendieck fibration の基底変換)

> **[DISCOVERY]** 不動点は fibration 上の **不変切断 (invariant section)**:
> σ* = (F*_t) s.t. F*_t ∈ [Ext_t, Int], VFE_t(F*_t) ≤ ε ∀t

> **[FACT]** 意味: 環境がどう変化しても、「その環境に対して ε-最適なモデルを維持し続ける」関手の軌道。

> **[RULE]** D_FEP (§2.4 の double category) との接続: D_FEP の垂直射 (能動推論 A: Ext → Ext') が fibration の基底変換に対応する。

---

## §5. NESS の形式化 — 「近づくが到達しない」 {#sec_06_ness}

> **[DEF]** 生きている系 (NESS) は完全な不動点に到達しない。3つの形式化:

**A. ε-近似不動点**: VFE(F, Φ(F)) ≤ ε を満たす F の集合。降下流はこの集合に進入・滞留。

**B. Lax 不動点**: 厳密な F ≅ Φ(F) ではなく、自然変換 Φ(F) ⇒ F の存在を許容。VFE が常に下界を持つ。

**C. ω-極限集合**: 降下流 (F_t) の ω-極限 ω(F_0) = ∩_{n≥0} cl({F_t : t ≥ n}) がアトラクタとして機能。

---

## §6. Kalon との接続 {#sec_07_kalon}

> **[DISCOVERY]** Kalon = Fix(G∘F) の操作的判定 (kalon.md §6.1) との自然な対応:

| 判定 | 不動点理論 | 意味 |
|:--|:--|:--|
| ◎ (kalon) | Fix(Q∘Γ) の厳密不動点 | 理想。G∘F で不変 |
| ◯ (許容) | ε-近似不動点 | 現実の NESS。改善可能だが十分に近い |
| ✗ (違和感) | 降下流の初期段階 | VFE が大きく、G (蒸留) が大幅に必要 |

> **[OPINION]** この対応は Kalon の定義「Kalon(x) ⟺ x = Fix(G∘F)」と不動点存在条件を統一する。Kalon は FEP の不動点の操作化であり、FEP の不動点は Kalon の形式化である。この自己参照構造自体が kalon の三属性 (不動点/展開可能/自己参照) を満たす。

---

## §7. 残存課題 {#sec_08_remaining}

> **[CONFLICT]** 以下の3点が未解決:

1. ~~**縮小写像条件の物理的正当化**~~: ✅ **解決済み** — §3.1 で Dobrushin 係数 η<1 の形式的証明を完成 (定理 1.5.2b)。
2. **Grothendieck fibration の具体的構成**: D_FEP (double category) のどの構造が fibration に対応するか。
   - 方向: D_FEP の垂直射の圏を基底とする fibration を構成。
3. **ε-近似 / lax / ω-極限の最適選択**: FEP に最も適切な「近づくが到達しない」の形式化はどれか。
   - [OPINION] ε-近似 が物理的に最も自然 (NESS の定義と直接対応)。Lax は圏論的に最もエレガント。ω-極限は力学系的に最も正統。3つは排他的ではなく、ε-近似 ⊂ lax ⊂ ω-極限 の包含関係が成立する可能性がある。

---

## §8. 確信度と文脈 {#sec_09_confidence}

> **[FACT]** 確信度: [推定 80%] (旧: 70% → 縮小写像条件解決により +10%)

**根拠**:
- Banach-Lawvere 条件の構造的整合性は高い
- 縮小写像条件の物理的正当化 → ✅ §3.1 で Dobrushin 係数の形式的証明完了
- Grothendieck fibration の不変切断は D_FEP (§2.4) と整合的だが具体的構成が未完
- Kalon との接続は圏論的に自然

**先行する ROM**: rom_2026-03-16_fep_categorical_formalization.md (VFE + D_FEP)

**参照ファイル**: fep_as_natural_transformation.md v0.5 (§1.5)

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "FEP の不動点はいつ存在するか？"
  - "能動推論で環境が変わる場合の不動点はどう定義される？"
  - "Kalon と不動点定理の関係は？"
  - "生きている系が完全な平衡に達しない理由の形式化は？"
  - "Banach の不動点定理は FEP にどう適用されるか？"
answer_strategy: "§3 (Banach-Lawvere) → §4 (Grothendieck) → §5 (NESS) の3層で段階的に回答。§6 で Kalon 接続を補足。"
confidence_notes: "縮小写像条件の物理的正当化が最大の不確実性要因。ε-近似 vs lax vs ω-極限の選択は未決。"
related_roms: ["rom_2026-03-16_fep_categorical_formalization"]
-->
