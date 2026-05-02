---
rom_id: rom_2026-03-17_kalon_j_idempotent
session_id: f3da7b08-b1d1-48b2-afdf-9b5aeadc91c0
created_at: 2026-03-17 11:47
rom_type: rag_optimized
reliability: High
topics: [kalon, J一意性, Morita同値, コーシー完備, 冪等射, 前順序圏, CCC, LFPT, axiom_hierarchy]
exec_summary: |
  kalon.md v2.5-2.7: J の一意性問題を Morita 同値 + コーシー完備化で解決。
  4種の射の全数走査により非恒等冪等射の不存在を確認。水準 B+ → A- 昇格。
  M1-LFPT 接続を誠実に下方修正 (B+/90% → B/82%)。
---

# kalon.md J 一意性 & 冪等射検証 {#sec_01_j_uniqueness}

> **[DECISION]** J の一意性は Morita 同値水準で解決。水準 B+ → A- に昇格 (v2.7)。

## §2.1 Morita 同値論証 (3層) {#sec_02_morita .decision}

> **[FACT]** 3層論証で J の「選択の恣意性」問題を解消した。

| 層 | 定理 | 内容 | 水準 |
|:---|:-----|:-----|:-----|
| 1 | Morita 同値 | PSh(J) ≅ PSh(J') ⟺ J と J' が Morita 同値 | A |
| 2 | コーシー完備化 | 各 Morita 同値類にコーシー完備化 J̄ が一意に存在 | A- |
| 3 | 密度定理 | J は M の最小生成集合 (密度的) | B |

**論拠**: Borceux, Handbook of Categorical Algebra I, Ch. 6。

## 冪等射自明性の厳密検証 {#sec_03_idempotent .discovery}

> **[DISCOVERY]** J が前順序圏 (axiom_hierarchy.md L465) であることから、非恒等冪等射は構造的に存在不能。

### 4種の射の走査 {#sec_04_morphism_scan}

| 射の種類 | 方向性 | End(j) への寄与 | 根拠 |
|:---------|:-------|:----------------|:-----|
| 演繹射 (FEP→修飾座標) | 一方向 (d増加) | dom≠cod → 寄与なし | axiom_hierarchy.md 階層構造 |
| 生成射 (Flow,座標→動詞) | 一方向 (多→1) | dom≠cod → 寄与なし | 24動詞の生成規則 |
| 制約射 (Stoicheia×Phase→Nomos) | 一方向 | dom≠cod → 寄与なし | 12法の演繹構造 |
| X射 (K₆ の15辺 = 30射) | **双方向** | 前順序圏 ⟹ \|End(j)\| ≤ 1 | axiom_hierarchy.md L465 |

> **[RULE]** 前順序圏 ⟹ |Hom(a,b)| ≤ 1 ⟹ End(j) = {id_j} ⟹ 非恒等冪等射は存在不能。

### 論理チェーン {#sec_05_logic_chain}

```
J が前順序圏 (axiom_hierarchy.md L465)
→ |Hom(a,b)| ≤ 1 (∀ a,b)
→ |End(j)| ≤ 1 (∀ j)
→ End(j) = {id_j} (恒等射のみ)
→ 非恒等冪等射は存在しない
→ J はコーシー完備 (自明に)
→ J ≅ J̄ (標準的代表元)
→ 水準 B+ → A- に昇格
```

> **[CONFLICT]** L2 豊穣圏 / L3 弱2-圏として J を解釈する場合、Hom に複数要素が入りうるため、この結論は成立しない可能性がある。現段階では前順序圏の定義 (L0-L1) に限定した議論。

## M1-LFPT 接続の修正 (v2.6) {#sec_06_m1_lfpt .decision}

> **[DECISION]** Point surjectivity は構成不能 → CCC の役割は K^K の存在保証に限定。

- **旧 (v2.4)**: CCC + point surjectivity → LFPT → M1。水準 B+/90%
- **新 (v2.6)**: Point surjectivity は Ω の明示的計算により不成立。CCC は K^K 存在を保証し、M1 は §4.9 の直接構成で示す。水準 B/82%

> **[FACT]** LFPT 適用には point surjective な対象が必要だが、M (= PSh(J)) 内の K は Sub のファミリー (P(24) × Prec × Struct) であり、point surjective にならない。

## 次の課題 {#sec_07_next}

> **[CONTEXT]** M の CCC 性の検証が残存。PSh(J) ≅ M の主張において、M が CCC であることの確認が必要。

- M = PSh(J) は圏論的に CCC (presheaf 圏は CCC)。ただし J の構造に依存する部分の検証が未完。
- CCC 構造: 積 (×)、冪対象 (⟹)、terminal object (1) の明示的構成が課題。

## 関連情報 {#sec_08_related}

- 関連ファイル: [kalon.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/kalon.md), [axiom_hierarchy.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)
- 関連 ROM: rom_2026-02-27_kalon_lfpt_verification.md
- 関連 Session: ebe36f9f (遊学エッセイ v2 レビュー), f3da7b08 (本セッション)

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "J の一意性はどう解決されたか？"
  - "J の冪等射は自明か？ なぜ？"
  - "M1-LFPT 接続の水準はいくつか？ なぜ下方修正したか？"
  - "コーシー完備化とは何か？ J の場合どうなるか？"
  - "前順序圏の仮定はどこで使われているか？"
answer_strategy: "前順序圏の定義 (axiom_hierarchy.md L465) を起点に、End(j) の一意性 → 冪等射不存在 → コーシー完備性の論理チェーンで回答"
confidence_notes: "全論証は J が前順序圏であるという仮定に依存。L2+ で解釈する場合の留保あり"
related_roms: ["rom_2026-02-27_kalon_lfpt_verification"]
-->
