---
rom_id: rom_2026-03-10_unified_index_axiom_debate
session_id: 0e1a0ad4-5dea-40bd-a473-10dcbd6c9617
created_at: 2026-03-10 11:35
rom_type: distilled
reliability: High
topics: [unified_index, axiom, yoneda, information_bottleneck, kalon, fep, elenchos]
exec_summary: |
  統一インデックス理論の公理を /noe+ で v0.1 (6公理) として生成し、
  /ele+ で全公理を論駁。米田の補題を代替提案したが、
  Creator の「情報理論でなくていいの？」で IB (Information Bottleneck) に修正。
  IB = VFE の構造同型を発見。公理の美しさについて /u で議論予定。
---

# 統一インデックス理論: 公理論争の記録 {#sec_01_overview}

> **[DECISION]** v0.1 の 6 公理は全て「設計決定」であり「公理」ではない。論駁済み。

> **[DECISION]** Information Bottleneck = VFE の構造同型。索引版 Helmholtz の候補。

> **[DISCOVERY]** 米田の補題はグラフ索引のみに適用。FTS/Embedding/Metadata は説明不可。

## 公理候補の変遷 {#sec_02_evolution}

| 段階 | 候補 | 結果 |
|:-----|:-----|:-----|
| /noe+ v0.1 | 6 公理 (VFE_K, UniversalDoc, TypedRelation, Adjunction, DomainFunctor, Precision) | /ele+ で全論駁。「設計決定であり公理ではない」 |
| /ele+ 代替A | 米田の補題 (知識版) `x ≅ Hom(-, x)` | Creator の反駁: グラフ索引のみ。FTS/Embedding は説明不可 |
| /ele+ 代替A 修正 | Information Bottleneck `max I(T;Y) - β·I(X;T)` | VFE と構造同型。全索引型をカバー。ただし美しさに疑問 |

## 核心的発見 {#sec_03_core}

> **[FACT]** IB と VFE の構造同型:
> - VFE = -Accuracy + Complexity
> - IB = -I(T;Y) + β·I(X;T)
> - Accuracy ↔ I(T;Y), Complexity ↔ I(X;T)

> **[FACT]** 索引の 4 種類と圧縮の関係:
> - FTS: 文書 → 単語頻度 (Content 軸)
> - Embedding: 文書 → ベクトル (Semantics 軸)
> - Graph: 文書 → 関係 (Structure 軸) ← 米田はここのみ
> - Metadata: 文書 → 属性 (Attribute 軸)

> **[DISCOVERY]** 提案した階層:
> - L0: FEP (公理 — HGK 共通)
> - L0.T: Information Bottleneck (定理¹ — d=0)
> - L1: Content / Semantics / Structure / Attribute (4座標)

## 未解決の問い {#sec_04_open}

> **[CONFLICT]** IB は正しいが Kalon か？ Týpos のような独自性があるか？
> FEP/圏論のように本質を一言で言えるか？

> **[CONFLICT]** 4 座標 (Content/Semantics/Structure/Attribute) の FEP 的導出が未完。「なぜ 4 なのか」の原理的根拠がない。

> **[CONFLICT]** そもそも索引に「固有の公理」は必要か？ FEP+応用定理で十分ではないか？

## 関連ファイル {#sec_05_related}

- /noe+ 出力: `e_出力/noe_unified_index_axioms_2026-03-10.md`
- /ele+ 出力: `e_出力/ele_unified_index_axioms_2026-03-10.md`
- 公理階層: `kernel/axiom_hierarchy.md`
- Kalon 定義: `kernel/kalon.md`

<!-- ROM_GUIDE
primary_use: 統一インデックス理論の公理議論の参照
retrieval_keywords: unified index, axiom, yoneda, information bottleneck, IB, VFE, kalon, 公理, 索引, 統一
expiry: permanent
-->
