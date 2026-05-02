# ROM: 随伴が誘導する 2-cell — 座標の統一像

> **日付**: 2026-03-17 07:45
> **セッション**: 03a2c373
> **先行 ROM**: rom_2026-03-16_2cell_species_hypothesis.md (← 本 ROM で **上書き**)
> **確信度**: [推定 70%]
> **SOURCE**: axiom_hierarchy.md, derivation_correct_fep_coordinates_2026-03-09.md, fep_as_natural_transformation.md v0.5

---

## §1 問いの変遷

```
旧旧: d = cell level か？ (d=2 座標は 2-cell、d=3 は 3-cell)
  → 棄却: 全座標は 2-cell。d と cell level は独立 (定理 4.1)

旧: 2-cell は何種 (species) に分かれるか？ (4 種: 方向/ゲイン/基底変換/対合)
  → 棄却: Creator の「全二極は相補的 (随伴)」で根拠崩壊

新: 全座標を生成する普遍的構成は何か？
  → 回答: 随伴 F_i ⊣ G_i が Flow に誘導する 2-cell
```

---

## §2 普遍的構成

**定義**: 座標 c_i は Galois 接続 F_i ⊣ G_i を持ち、Flow に対する 2-cell を誘導する:

```
α_{c_i}: Flow ⇒ G_i ∘ Flow ∘ F_i
```

**種は 1 つ**。全座標が同一の構成のインスタンス。代数的帰結 (⊕, ·, σ, f, ⊣) は随伴 F_i ⊣ G_i の性質から自然に出る **パラメータ** であって **型** ではない。

---

## §3 各座標の随伴

| 座標 | F_i | G_i | 作用対象 | 代数的帰結 |
|:--|:--|:--|:--|:--|
| Value | Acc 射影 | Comp 射影 | VFE 内 | ⊕ 加法 |
| Function | Epistemic 射影 | Pragmatic 射影 | EFE 内 | ⊕ 加法 |
| Precision | Sharpen (π↑) | Blur (π↓) | 精度空間 | · 乗法 |
| **Temporality** | **Extend (VFE→EFE)** | **Marginalize (EFE→VFE)** | **汎関数間** | **⊣ 随伴** |
| Scale | Zoom-in (MB→sub-MB) | Zoom-out (sub-MB→MB) | MB 階層 | functor |
| Valence | Approach (+) | Avoid (−) | 評価符号 | σ²=id 対合 |

### Temporality の特定 [推定 70%]

Temporality = VFE 世界と EFE 世界を架橋する随伴。

- **F_T (Extend)**: 現在のモデルに未来の方策空間を追加。VFE の世界を EFE の世界に拡張
- **G_T (Marginalize)**: 未来を積分消去して現在の評価に戻す
- **η**: G_T ∘ F_T ≥ Id (拡張→周辺化で情報残留)
- **ε**: F_T ∘ G_T ≤ Id (周辺化→拡張で情報損失)
- **Fix(G_T ∘ F_T)** = De Vries (2025) の結論: 拡張モデル上で VFE min = EFE min = **Temporality の Kalon**

Value/Function と Temporality の構造的差異:
- Value: VFE **内** の加法分解 (1 つの汎関数の 2 成分)
- Function: EFE **内** の加法分解 (1 つの汎関数の 2 成分)
- Temporality: VFE と EFE の **間** の架橋 (2 つの汎関数を接続)

---

## §4 d (filtration) と cell level の独立性

**定理 4.1**: cell level と filtration grade は独立。

- **Cell level**: 全座標 = 2-cell (圏 C_FEP の内在的構造)
- **Filtration (d)**: FEP からの導出距離 (付加的構造)
- **ALL d=1 は圏論的に可能** だが、分析的透明性のために d=2/d=3 を採用 (2026-03-09 棄却理由)

三軸分類:

```
軸 1 (cell level):  全座標 = 2-cell → 差異なし (定数)
軸 2 (filtration):  d=2 {V, Fn, Π, T} / d=3 {S, Vl} → 導出距離
軸 3 (パラメータ): 各随伴 F_i ⊣ G_i の代数的性質 → ⊕, ·, σ, f, ⊣
```

軸 2 と軸 3 は独立 (未検証だが、Temporality が d=2 で ⊣ 型であることが反例候補)。

---

## §5 帰結

### 5.1 「4 種」仮説の処分

棄却。ただし完全な無駄ではない:
- 「各座標が異なる代数的帰結を持つ」事実は残る
- 「種」ではなく「パラメータ」として再配置された

### 5.2 Kalon 判定

この統一像 (随伴が誘導する 2-cell) は Kalon か？

- **F (展開)**: 6 つの随伴 → 6 つの異なる代数的帰結 → 「種が 4 つ！」
- **G (収束)**: 全て同一構成 → 「1 つの普遍的構成のインスタンス」
- **Fix(G∘F)**: 展開 (多様性の発見) と収束 (統一の発見) が同一点 = 「多様性を生む単一構成」

**◎ 不動点**: 展開しても収束しても同じ場所に戻る。

### 5.3 CCL への示唆 (次の探索)

全 Poiesis が同一構成 (随伴誘導 2-cell) のインスタンスなら、CCL 演算子は 2-cell の **合成規則** (2-圏の構造) として自然に出る。パラメータの違いは合成に影響しない → **CCL が全 Poiesis に普遍的に機能する圏論的根拠**。

---

## §6 未解決

| # | 問い | 優先度 |
|:--|:--|:--|
| Q1 | Temporality の F_T ⊣ G_T (Extend ⊣ Marginalize) は形式的に随伴か？ 単位η・余単位ε の検証 | HIGH |
| Q2 | d と代数的パラメータに統計的従属性はあるか？ | LOW (n=6) |
| Q3 | CCL 演算子 {>>, ~, *, _} は 2-圏の合成規則 {垂直, 水平, 積, whiskering} に写像されるか？ | HIGH (次の探索) |
| Q4 | 「パラメータ空間上の点」は Lawvere의 enriched category で形式化できるか？ | MEDIUM |

---

*ROM v2.0 — 2026-03-17 07:45*
*前版 (v1.0 rom_2026-03-16_2cell_species_hypothesis.md) を理論的に上書き*
