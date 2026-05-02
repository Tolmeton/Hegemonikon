---
type: rom
created: 2026-03-09T16:57:00+09:00
depth: L3
topic: Temporality d=2 確定 — POMDP 必然性 + Epistemic Prior 必然性
semantic_ids:
  - temporality_d2_confirmed
  - pomdp_fep_necessity
  - epistemic_prior_necessity
  - markov_blanket_partial_observability
  - self_evidencing_exploration
depends_on:
  - rom_2026-03-09_coordinate_rescue_valence_temporality.md
confidence: 90%
---

# ROM: Temporality d=2 確定

## 1. 核心的発見

### POMDP = FEP の数学的帰結 (Layer A, NOT Layer B)

Markov blanket の条件付き独立性:
```
p(μ,η|s,a) = p(μ|s,a)·p(η|s,a)
```
→ 内部状態は外部状態を**直接観測できない** = **部分観測性の定義そのもの**
→ POMDP は「モデリング選択 (Layer B)」ではなく「FEP の帰結 (Layer A)」

### 完全な演繹チェーン (6段)
```
1. FEP → Markov blanket を要請
2. MB → 条件付き独立性 → 部分観測性 (POMDP)
3. POMDP → 受動的情報取得だけでは不十分
4. Self-evidencing → 能動的探索が必然 (Friston 2015, 668cit)
5. 探索必然 → EFE が FEP 内で帰結 (De Vries 2025)
6. VFE (Past) ≠ EFE (Future) → Temporality = 独立座標 d=2
```

## 2. 座標系の最終構成

| d | 座標 | 確信度 | 備考 |
|:--|:-----|:-------|:-----|
| 0 | Helmholtz | 100% | Basis. 体系核外 |
| 1 | Flow | 100% | MB仮定のみ |
| 2 | Value | 95% | VFE/EFE 分解 |
| 2 | Function | 95% | EFE 行動選択 |
| 2 | Precision | 95% | 予測誤差逆分散 |
| **2** | **Temporality** | **90%** | **本セッションで d=3→d=2** |
| 3 | Scale | 80% | 階層的仮定 |
| 3 | Valence (6⋊1) | 85% | 半直積構造 |

## 3. 反論と応答

| 反論 | 応答 |
|:-----|:-----|
| サーモスタットは探索しない | 完全観測系。MB 定義上 POMDP ではない |
| 非定常でなければ不要 | 初期不確実性 >0 で探索必要 |
| EFE 以外の探索は？ | FEP 内の探索記述は EFE が唯一 (De Vries 2025) |

## 4. 参照論文

| 論文 | 引用数 | 役割 |
|:-----|:-------|:-----|
| Friston 2015 "Active inference and epistemic value" | 668 | Epistemic value が探索/搾取を解決 |
| Friston 2022 "FEP made simpler" | 135 | Self-evidencing の定式化 |
| De Vries 2025 "EFE as Variational Inference" | 4 | EFE = VFE on augmented model |
| Millidge 2020 "Whence the EFE?" | 80 | VFE ≠ EFE の証明 |
| Pezzulo 2021 "Evolution of brain architectures" | 83 | T/H 独立の進化的証拠 |
| Da Costa 2020 "Active inference synthesis" | 245 | 離散空間での能動推論統合 |

## 5. 変更ファイル

- `axiom_hierarchy.md` — Temporality d=2 確定, テーブル2行追加
- `analysis_epistemic_prior_necessity_2026-03-09.md` — 新規
- `analysis_pomdp_necessity_2026-03-09.md` — 新規

## 6. 未踏

1. **Scale d=3→d=2**: 階層的生成モデルは FEP の必然か
2. **Valence 公式定式化**: 4候補から1つ選択
3. **Prior preferences C の出自**: preference prior はどこから
4. **非近視の程度**: temporal horizon の必要十分条件

---
*ROM burned: 2026-03-09 16:57 JST*
