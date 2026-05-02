---
rom_id: rom_2026-03-11_euporia_principle
session_id: 2c73d901-8926-4aaf-a6c7-6e6114414365
created_at: 2026-03-11 13:37
rom_type: distilled
reliability: High
topics: [euporia, affordance_yield, flow, kalon, axiom_hierarchy, theorem]
exec_summary: |
  Euporía (εὐπορία) 原理を発見・定式化。「全ての認知操作は行為可能性を増やさなければならない」。
  Flow (d=1) の定理として axiom_hierarchy.md に定理³として追記。Kalon の Generativity は AY の最適到達点。
---

# Euporía (εὐπορία) 原理の発見と定式化 {#sec_01_euporia}

> **[DECISION]** Euporía Principle = Flow (d=1) の定理 (体系核外)

## 経緯 {#sec_02_history}

> **[CONTEXT]** セッションの流れ

1. Creator: 随伴WF に「行為可能性のリストアップ」機構を組み入れたい
2. /u で分析 → EFE の pragmatic value 項の可視化として位置づけ
3. Creator: 「これはほぼすべてのWFに転用できる」→ 全WFへの普遍化
4. 米田の補題: Hom(B, −) > Hom(A, −) = 行為可能性の増大
5. Creator: 「認知は運動のためにある。Flow軸の中に内在するのでは」→ ポジショニング修正
6. Kalon の下流 → **Flow の上流** (定理³) に修正
7. 名前: Euporía (εὐπορία) = Aporía の対概念。Poros (道) = 射 (morphism)

## 確定事項 {#sec_03_decisions}

> **[DECISION]** 命題名: Euporía Principle (εὐπορία原理)

> **[DECISION]** 体系的位置: Flow (d=1) の定理。axiom_hierarchy.md 定理³

> **[DECISION]** 演繹チェーン

```
FEP → self-evidencing → Helmholtz Γ⊣Q → Flow I⊣A → ★ Euporía
```

> **[DECISION]** Kalon との関係

```
Euporía: AY(f) > 0 — 全 WF の必要条件
Kalon Generativity: AY = max at Fix(G∘F) — AY の最適到達点
方向: Euporía → Kalon (上流 → 下流)
```

> **[DECISION]** 深度別適用

| 深度 | 要件 |
|:-----|:-----|
| L0 | 明示不要 |
| L1 | pragmatic ≥ 1 |
| L2 | pragmatic ≥ 2 + epistemic ≥ 1 |
| L3 | pragmatic ≥ 3 + epistemic ≥ 2 + EFE根拠 |

> **[DECISION]** 実装方針: hermeneus 環境強制 (Choice B)

## 発見 {#sec_04_discoveries}

> **[DISCOVERY]** 認知は運動のためにある — 全WFの出力は行為可能性で評価すべき

> **[DISCOVERY]** η/ε だけでは随伴品質の評価が不完全 — pragmatic value 欠落

> **[DISCOVERY]** 命題は Kalon の下流ではなく Flow の上流に位置する

> **[DISCOVERY]** Poros (道) = 射 (morphism) — 語源的にも圏論的にも整合

## 成果物 {#sec_05_artifacts}

| ファイル | 変更内容 |
|:---------|:---------|
| `axiom_hierarchy.md` | 定理³ Euporía 追記 (概観テーブル + 本文63行) |
| `affordance_yield.md` | 概念ドキュメント (名前を Euporía に統一) |

## 未着手 {#sec_06_remaining}

- [ ] kalon.md への Generativity 属性更新 (精緻に)
- [ ] hermeneus 環境強制の実装
- [ ] 各 WF への具体的な組み込み
- [ ] Thesmos / θ7.x への追加
- [ ] ファイル名の変更 (affordance_yield.md → euporia.md)

## 関連情報

- 関連 WF: /eat, /ccl-read, 全随伴WF
- 関連 KI: kalon.md, axiom_hierarchy.md, affordance_yield.md
- 関連 Session: 2c73d901

<!-- ROM_GUIDE
primary_use: Euporía 原理の定義・位置づけ・実装方針の参照
retrieval_keywords: euporia, affordance yield, AY, 行為可能性, flow theorem, kalon generativity
expiry: permanent
-->
