---
doc_id: "FLOW_AFF_EFF_DECOMPOSITION"
version: "0.1.0"
tier: "KERNEL"
status: "PROPOSAL"
created: "2026-03-23"
parent: "axiom_hierarchy.md §Flow"
---

```typos
#prompt flow-afferent-efferent-decomposition
#syntax: v8
#depth: L3

<:role: Flow 座標の Afferent×Efferent 分解 — s/μ/a との演繹的関係の精査 :>
<:goal: Flow が1座標か2座標かを演繹的に決定し、体系構造への含意を示す :>
```

# Flow 座標の Afferent×Efferent 分解

> **問題**: axiom_hierarchy v5.1 で導入された Afferent×Efferent 分解 (§Flow L203-214) と、
> 従来の s/μ/a 三分割の間に構造的不整合がある。
> H-series 前動詞は φ_SA (S∩A 象限) から生まれるが、s/μ/a にはこの象限が存在しない。

---

## §1. 不整合の定位

| 記述 | Flow の値 | φ_SA | H-series の存在根拠 |
|:---|:---|:---|:---|
| s/μ/a (三値) | 3 (S, I, A) | 存在しない | ❌ 説明不能 |
| Afferent×Efferent (2×2) | 4象限 | 第4象限 | ✅ φ_SA × 6修飾座標 = 12 |

**s/μ/a で H-series が生まれる場所がない** — これは体系の内部矛盾。

---

## §2. φ_SA はどこで忘却されたか

### MB の形式的定義

Markov blanket (Friston 2019 "A particular physics", Da Costa 2021) は以下を定義する:

```
エージェント状態 x_agent = (b, μ)
b = blanket states (μ と η を条件付き独立にする)
条件: ∂f_μ/∂η = 0, ∂f_η/∂μ = 0
```

### blanket 状態の分類

各 blanket 状態 b_i は、2つの**独立な結合条件**で分類される:

| 条件 | 意味 | 記号 |
|:---|:---|:---|
| ∂f_i/∂η ≠ 0 | 環境 η がこの状態に結合する | **Afferent** |
| ∂f_i/∂μ ≠ 0 | 内部 μ がこの状態に結合する | **Efferent** |

**独立性の根拠**: μ ⊥ η | b (条件付き独立) であるため、η→b_i の結合と μ→b_i の結合は
異なる（条件付き独立な）ソースからの影響であり、構造的に独立。

### 4象限

|  | Efferent Yes (∂f/∂μ≠0) | Efferent No |
|:---|:---|:---|
| **Afferent Yes** (∂f/∂η≠0) | **S∩A** (反射弧 = φ_SA) | **S** (純知覚) |
| **Afferent No** | **A** (純行為) | **I** (内部推論) |

### 忘却の正確な箇所

```
MB 定義 (∂f_μ/∂η = 0, ∂f_η/∂μ = 0)
  ↓ [演繹的] 2つの独立二値で分類
  ↓
  4象限: S, I, A, S∩A  ← MB の数学から直接導出
  ↓
  ★ ここで「s ∩ a = ∅」を仮定 ★  ← 忘却の正確な箇所
  ↓
  3値: s, μ, a           ← 追加仮定1つを含む派生物
```

> **s ∩ a = ∅** は MB の数学的定義が要求するものではない。
> 多くの物理系 (感覚ニューロン ≠ 運動ニューロン) では合理的近似だが、
> 反射弧 (脊髄反射、habitual control) では s ∩ a ≠ ∅ が実在する。

---

## §3. Afferent×Efferent が原始的であることの論証

| Step | 内容 | 根拠 |
|:---|:---|:---|
| 1 | MB は b を介して μ と η を分離する | MB の定義 |
| 2 | 各 b_i に η 結合 (Aff) と μ 結合 (Eff) は独立に存在しうる | μ ⊥ η \| b |
| 3 | ∴ (Aff, Eff) ∈ {Yes,No}² で分類 | 2つの独立二値の直積 |
| 4 | ∴ 4象限が MB 定義から演繹 | 追加仮定ゼロ (Layer A) |
| 5 | s/μ/a は Step 4 に「s ∩ a = ∅」を追加 | 追加仮定1つ |

**仮定の少ない方が原始的**: Afferent×Efferent は追加仮定ゼロ。s/μ/a は追加仮定1つ。
∴ Afferent×Efferent が原始記述。

---

## §4. Helmholtz (Basis) との関係

### Helmholtz は FEP の前提であり帰結ではない

Helmholtz 分解 (任意のベクトル場 = gradient + solenoidal) は**数学的定理**であり、
FEP が成立するための前提条件。FEP はこれを解釈する: Γ = VFE 最小化, Q = 探索。

| 側面 | Helmholtz (Γ⊣Q) | FEP | Afferent×Efferent |
|:---|:---|:---|:---|
| 性質 | **数学的定理** | 物理的解釈 (公理) | 構造分類 |
| 問い | HOW: 力学の成分は？ | WHAT: なぜ定常か？ | WHERE: どこに繋がるか |
| 依存 | なし (純粋数学) | Helmholtz を前提 | MB 仮定を前提 |

### 導出チェーン (修正版)

```
Helmholtz 分解 (数学的定理: f = gradient + solenoidal)
  → FEP: Γ = VFE 最小化, Q = 探索 という解釈 (L0, 公理)
    → + MB 仮定 (d=1)
      → Afferent (∂f/∂η ≠ 0)        ← d=1 座標①
      → Efferent (∂f/∂μ ≠ 0)        ← d=1 座標②
      ↛ Flow (旧 d=1 単一座標)       ← Aff×Eff の射影 (s∩a=∅ 仮定)
```

> **Helmholtz と Afferent/Efferent は直交する概念**:
> - Helmholtz: 力学の**成分分解** (Γ/Q) → 12演算子を生む
> - Afferent×Efferent: 状態の**結合構造分類** → 4象限を生む
> - 動詞 = 12演算子 × 4象限 = 48認知操作

---

## §5. 体系への含意 (PROPOSAL — 未確定)

### 座標数の変更

| 項目 | v5.1 現行 | PROPOSAL |
|:---|:---|:---|
| d=1 座標 | Flow (1) | Afferent (1) + Efferent (1) |
| 座標合計 | 7 (1+3+3) | 8 (2+3+3) |
| 動詞生成 | Flow(S/I/A) × 6mod × 2極 = 36 | 4象限 × 6mod × 2極 = 48 |
| 体系核 | 44 (1+7+36) | 要再計上 |

### 検討事項 (順に考える)
1. 48動詞のうち S∩A の12を Poiesis に含めるか H-series に留めるか
2. 体系核の数え方 (44 → ?)
3. K₃ → K₄ への拡張
4. 新シリーズの必要性

---

*Created: 2026-03-23 — Flow Afferent×Efferent 分解の精査 (PROPOSAL, DRAFT)*
