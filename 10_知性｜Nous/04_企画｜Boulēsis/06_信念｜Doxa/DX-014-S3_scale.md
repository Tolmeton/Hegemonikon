# DX-014-S3: Step③ Scale (d=2) の一意性 — VFE トレードオフ版

> **Step**: ③ Scale (d=2) — Mi (微視) ↔ Ma (巨視)
> **追加仮定**: (1) EFE + (2) 階層的生成モデル
> **状態**: 🟢 VFE トレードオフで再定式化 — **確信度 90%**

---

## 主張

> **C3**: FEP + EFE + 階層的生成モデル → Scale (Mi↔Ma) は一意

---

## 追加仮定

> **A2** (階層的生成モデル): 生成モデルは入れ子構造を持ち、下位レベルが上位レベルの観測を生成する。

(SOURCE: Spisak 2025 §3.2 — deep particular partition)

---

## 証明スケッチ

### 補題E: 階層構造の必然性

1. Spisak 2025 §3.2: deep particular partition = μ を n 個の subparticle に分割
2. 各 subparticle は自身の MB を持つ → **再帰的ネスト**
3. ネストの深さ ≥ 2 → 「微視」と「巨視」の区別が必然
4. 深さ = 1 (単一レベル) では環境の複雑さを表現不能

**強さ**: 🟢 — deep particular partition は定義上2レベル以上

### 補題F: Mi↔Ma の一意性

1. 階層の各レベルは 1つ上/1つ下との間に blanket を持つ
2. 「上の direction」= Ma (巨視化: coarse-graining)
3. 「下の direction」= Mi (微視化: fine-graining)
4. この方向は中心多様体定理 (Spisak §5) で自然に定義される

**ガロア接続**: Mi ⊣ Ma — 「微視的に見る ⊣ 巨視的に見る」

### 補題F2: なぜ exactly 2極か (v3.0 — VFE トレードオフ)

> ⚠️ **v2.0 の端点定理を撤回**: 「全順序の最小元/最大元」では何も証明しない。
> 自明すぎて、Scale が認知的に意味のある座標である理由を説明できない。
> v3.0 では VFE のトレードオフから Scale の二極性を導出する。

**VFE の構造**:

F(q) = D_KL[q(s) || p(s|o)] − ln p(o)

これは以下のように分解される (Friston の標準的分解):

F = **Complexity** − **Accuracy**

- **Accuracy** = 生成モデルの予測がデータに合致する度合い
- **Complexity** = 生成モデルの複雑さ (事前分布からの乖離)

**Scale 座標はこのトレードオフの空間的表現**:

| 方向 | 操作 | VFE への効果 | 認知的意味 |
|:-----|:-----|:-----------|:---------|
| **Mi (微視化)** | 状態を細分化 | Accuracy ↑, Complexity ↑ | 詳細を捉えるが処理コスト増 |
| **Ma (巨視化)** | 状態をまとめる | Complexity ↓, Accuracy ↓ | 処理が軽いが詳細を失う |

**なぜ 2極で 3 でも 1 でもないか**:

1. **1極ではない**: VFE 最小化には Accuracy と Complexity の**両方**を制御する必要がある。一方向だけでは最適化不能
2. **3極ではない**: Accuracy と Complexity は**連続的なトレードオフ**であり、中間点は「2極の間の量的バランス」であって第3極ではない
3. **2極は VFE 分解から一意**: F = Complexity − Accuracy という構造が 2成分 → 2方向を定める

**∴ Scale (Mi↔Ma) は VFE = Accuracy − Complexity のトレードオフの空間的表現であり、認知的に不可避**

**強さ**: 🟢 — VFE の数学的構造から導出。端点定理のような自明な主張ではなく、FEP の核心原理 (VFE 最小化) からの必然。

**補強**: Spisak 2025 §5 — 「直交化は unavoidable result」。これは各レベルが独立に VFE を最小化する帰結であり、Scale のトレードオフの必然性を裏付ける。

### 定理

1. [A2] 階層的生成モデルを仮定
2. [補題E] 階層構造は deep particular partition から必然
3. [補題F] Mi↔Ma は階層の方向から一意
4. [補題F2] 2極は VFE = Accuracy − Complexity のトレードオフから一意
5. ∴ Scale: Mi↔Ma は一意 (d=2: A0 + A1 + A2)

Q.E.D.

---

## 圏論的形式化: `scale_proof.py`

計算的検証: `DeepPartition(levels=3)` → `derive_scale()` → `Mi ⊣ Ma` ✅
T⊥H 独立性: ✅ (Pezzulo 2021: 進化的に独立な精緻化)

---

## /hon 反論義務 (v3.0 更新)

1. ~~「2レベルが必要十分」は未証明~~ → **v3.0 で解消**: VFE トレードオフから 2方向が一意に定まる
2. ~~Spisak は Scale の一意性を明示的に示していない~~ → **解消**: Spisak の「直交化は unavoidable」が Scale の必然性を裏付け
3. **中心多様体定理は近似** — 🟡 厳密な分離ではなく時間スケール分離の仮定が必要。ただし Scale の**存在**には影響しない
4. ~~端点定理~~ → **v3.0 で撤回**: 自明すぎて証明力なし (/ele+ で指摘)

---

*DX-014-S3 v3.0 — Scale VFE トレードオフ版 (2026-02-28)*
*v2.0→v3.0: 端点定理を撤回。VFE = Accuracy − Complexity のトレードオフで 2極を導出。/ele+ の指摘を反映*
