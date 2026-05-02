```typos
#prompt ccl-readme
#syntax: v8.4

<:role: CCL (Cognitive Control Language) — 認知制御言語 親 PJ :>

<:goal:
  CCL を「意味論 / 忘却関手 / 言語処理系」の三面から統合する。
  かつてばらばらに置かれていた Kalon (圏論的意味論) / Lethe (忘却関手の計算的実現) / ccl-pl (言語処理系) を、
  同一対象 CCL の三角形として相互参照可能にし、「目移り」を「親 PJ 内の角度切替」に再配置する。
:>

<:context:
  - [knowledge] CCL = Cognitive Control Language。HGK 認知母体の演算記述系
  - [knowledge] 三面の関係:
    意味論 (Semantikē) — CCL 演算子の圏論的・群論的意味付与 (理論)
    忘却 (Lethe) — CCL = 自由モノイダル圏の構文的実現 / 忘却関手 U の左随伴 (理論⊣実験)
    処理系 (CCL-PL) — `.ccl` を実装正本とする汎用 PL (実装)
  - [file] 01_意味論｜Semantikē/ — 旧 01_美論｜Kalon (Phase L1 完了 / L2 `>*` 形式化が次)
  - [file] 02_忘却｜Lethe/ — Phase A-B 完了 / Phase C QLoRA 着手前
  - [file] 03_処理系｜CCL-PL/ — ADR-0001/0002 確定済 / v0.x bootstrap backend
:>
```

# Project CCL — 認知制御言語

## 三面構造

CCL は3つの異なる側面から研究されている。これらは独立した PJ ではなく、**同一対象の三角形**である。

| 子 PJ | 側面 | 核心問い | Status |
|:---|:---|:---|:---|
| **[01_意味論｜Semantikē](./01_意味論｜Semantikē/)** | 圏論的意味論 (理論) | CCL 演算子に何の数学的意味を与えるか | L1 ✅ / L2 `>*` 形式化 🔴 |
| **[02_忘却｜Lethe](./02_忘却｜Lethe/)** | 忘却関手 (理論⊣実験) | CCL は U: Code→CCL の像か | Phase A-B ✅ / Phase C 着手前 |
| **[03_処理系｜CCL-PL](./03_処理系｜CCL-PL/)** | 言語処理系 (実装) | CCL を汎用 PL として動かせるか | v0.x bootstrap (Python transpile) |

## 三面の相互参照

- **Semantikē → Lethe**: CCL の14演算子の圏論的定義 (Semantikē) が、Lethe の「CCL ≅ 圏論」主張を支える
- **Semantikē → CCL-PL**: 演算子の意味論 (Semantikē) が、処理系の実行意味 (CCL-PL) の正本
- **Lethe → CCL-PL**: Code→CCL トランスパイラ (Lethe 実装) は CCL-PL の上流コンポーネント
- **CCL-PL → Semantikē**: `.ccl` 構文凍結と extension protocol が、新演算子の意味論候補を実装側から提供

## 関連する隣接 PJ (CCL 親 PJ には**含めない**)

- **[11_肌理｜Hyphē](../11_肌理｜Hyphē/)** — CKDF / Markov blanket チャンク理論。Lethe と「**理論⊣実験**」のペア (Hyphē README L13-18) を組むが、Hyphē の核心は CKDF で CCL は手段。独立 PJ として保持
- **[00_核心｜Kernel/A_公理｜Axioms/F_美学｜Kalon/](../../../00_核心｜Kernel/A_公理｜Axioms/F_美学｜Kalon/)** — Kalon (καλόν) は Kernel の公理概念。旧 `01_美論｜Kalon/` は本 PJ の `01_意味論｜Semantikē/` に改名され、Kalon 名は Kernel 専用に返した

## 移行履歴

| Date | 変更 | Phase |
|:---|:---|:---|
| 2026-05-02 | 親 PJ `16_CCL｜CCL/` 作成 + skeleton README | Phase A ✅ |
| 2026-05-02 | `01_美論｜Kalon/` → `16_CCL｜CCL/01_意味論｜Semantikē/` に移動・改名 (12 backlinks 更新; archive 4件はスキップ) | Phase B1 ✅ |
| TBD | `14_忘却｜Lethe/` → `16_CCL｜CCL/02_忘却｜Lethe/` に移動 (119 backlinks) | Phase B2 🔲 |
| TBD | `/ccl-pl/` (Hegemonikon 直下) → `16_CCL｜CCL/03_処理系｜CCL-PL/` に移動・改名 (440 backlinks) | Phase B3 🔲 |
| TBD | 親 README 完成 (各子 PJ の現状反映) | Phase C 🔲 |

---

*Created: 2026-05-02 — Phase A skeleton*
