# 形式導出 PJ (Formal Derivation)

> **PURPOSE**: FEP + Active Inference (POMDP) + Scope Constraints から HGK 32実体の一意構成を数学的に証明する。

## SCOPE

| 入る | 入らない |
|---|---|
| 形式的証明・反証との対話 | 実装コード (→ 20_機構) |
| 代数構造の定式化 | 座標定義そのもの (→ 00_核心/Kernel) |
| 情報幾何学的固有ベクトルの解析 | 圏論的構成の操作的側面 (→ 01_美論) |
| 3条件 (SC-H, SC-T, SC-E) の検討 | |

## MAP — 散在リソース参照

### 原典 (Kernel)
- [formal_derivation_v4.md](../../../00_核心｜Kernel/A_公理｜Axioms/formal_derivation_v4.md) — **L0 形式的導出 v4 (水準A条件付き)**
- [analysis_valence_formalization_2026-03-09.md](../../../00_核心｜Kernel/A_公理｜Axioms/analysis_valence_formalization_2026-03-09.md) — Valence 座標の形式化
- [analysis_semidirect_6x1_formal_2026-03-09.md](../../../00_核心｜Kernel/A_公理｜Axioms/analysis_semidirect_6x1_formal_2026-03-09.md) — 6×1 半直積の形式化
- [type_theory_formalization_vision.md](../../../00_核心｜Kernel/A_公理｜Axioms/D_メタ｜Meta/type_theory_formalization_vision.md) — 型理論による形式化ビジョン
- [criterion2_formalization.md](../../../00_核心｜Kernel/A_公理｜Axioms/D_メタ｜Meta/criterion2_formalization.md) — 基準2の形式化

### 計画・草案 (Mneme artifacts)
- [bou_formal_derivation_roadmap_2026-03-07.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/bou_formal_derivation_roadmap_2026-03-07.md) — 水準A昇格ロードマップ (鬼門整理)
- [sop_formal_derivation_2026-02-27.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/sop_formal_derivation_2026-02-27.md) — SOP
- [draft_formal_argument_v2_2026-03-07.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/draft_formal_argument_v2_2026-03-07.md) — 論証草案 v2
- [nous_formal_assumptions_2026-03-07.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/nous_formal_assumptions_2026-03-07.md) — 前提条件分析
- [nous_galois_formalization_2026-03-07.md](../../../30_記憶｜Mneme/01_記録｜Records/d_成果物｜artifacts/nous_galois_formalization_2026-03-07.md) — ガロア接続の形式化

### コンテキスト保存 (ROM / Handoff)
- [rom_2026-02-28_formal_derivation_proof_map.md](../../../30_記憶｜Mneme/01_記録｜Records/c_ROM｜rom/rom_2026-02-28_formal_derivation_proof_map.md) — 証明マップ ROM
- [ho_2026-03-07_formal_derivation_ele_dio.md](../../../30_記憶｜Mneme/01_記録｜Records/a_引継｜handoff/ho_2026-03-07_formal_derivation_ele_dio.md) — 形式導出 Elenchos+Diorthōsis Handoff

### 信念層の考察 (Doxa)
- [DX-014_formal_derivation.md](../06_信念｜Doxa/DX-014_formal_derivation.md) — DX-014 形式導出の各方面
- [nous_ExP_formalization_2026-02-14.md](../06_信念｜Doxa/nous_ExP_formalization_2026-02-14.md) — ExP 形式化

## STATUS

📍 現在地: formal_derivation_v4.md が水準A (Conditional) に到達。4ラウンドの Adversarial Review で収束
🕳️ 未踏: Minor 修正5件 (Q/P多様体区別、EFE 精密化等)。鬼門 #1 (4096 vs 24) の代数構造再定義
→次: 鬼門 #1 に着手 — 24動詞を生成する代数的ジェネレータの定式化

---

*Created: 2026-03-13*
