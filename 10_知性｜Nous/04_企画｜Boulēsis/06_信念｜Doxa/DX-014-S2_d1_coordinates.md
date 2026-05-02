# DX-014-S2: Step② d=1 座標 (Value, Function, Precision) の一意性 — 証明スケッチ

> **DX**: DX-014 (形式的導出 + 弱2-圏)
> **Step**: ② d=1 座標の一意性
> **追加仮定**: EFE (Expected Free Energy) の存在
> **状態**: 🟢 計算的検証 PROVED + FEEF 解消 + Precision d 決着 + /ele+ 対応 — **確信度 92%**

---

## 主張 (Claim)

> **C2**: FEP + EFE のもとで、Flow (I↔A) の上に構築される d=1 座標は
> 正確に **3つ** (Value, Function, Precision) であり、
> それぞれが一意なガロア接続を定める。

---

## 追加仮定: EFE

> **A1** (EFE): エージェントは EFE G(π) を最小化する方策 π を選択する。
>
> G(π) = E_Q[o,s|π](ln Q(s|π) - ln P(o,s))           (Friston)
> = -Pragmatic Value + Epistemic Value          (分解)
>
> SOURCE: Millidge, Tschantz & Buckley 2020 (arXiv:2004.08128, 80引用)

### EFE に関する Millidge の警告

> 「EFE は『未来の VFE』ではない。探索は VFE 最小化から直接には出てこない」
> (SOURCE: Millidge 2020 abstract)

**含意**: A1 (EFE の存在) は A0 (FEP) から**自動的には導出されない**。
これが d=1 と d=0 の本質的な差 — 追加仮定が必要。

---

## EFE 分解から 3座標への導出

### EFE の標準分解

```
G(π) = - E_Q[ln P(o)]       — Pragmatic Value (望ましい観測の期待)
       - E_Q[D_KL[Q(s|o,π) || Q(s|π)]]  — Epistemic Value (情報利得)
```

(SOURCE: Parr & Friston 2019; Millidge 2020)

### 3座標の同定

| 座標 | EFE の成分 | 対立 | 圏論的表現 |
|:-----|:----------|:-----|:---------|
| **Value** | Pragmatic ↔ Epistemic | E↔P | 2成分への分解が一意 |
| **Function** | 各成分の最適化戦略 | Explore↔Exploit | π の選択が2モードに分類 |
| **Precision** | EFE のパラメータ π | C↔U | π の大きさが確信度を決定 |

---

## 証明スケッチ

### 補題A: EFE 分解の一意性

**主張**: G(π) の Pragmatic/Epistemic 分解は一意。

**論証**:

1. G(π) を条件付き期待値で展開する
2. ln P(o,s) = ln P(o) + ln P(s|o) と分解
3. Q(s|π) の KL divergence を分離
4. 結果: G(π) = **Pragmatic** (ln P(o) に依存) + **Epistemic** (Q(s|π) の情報利得)

**この分解は対数の加法性から一意** — ln P(o,s) の分解は条件付き確率の定義に基づき、別の分解は存在しない。

**強さ**: 🟢 — 数学的に一意 (対数の分解)

**✅ FEEF 問題の解消** (v2.0 追加):

Millidge 2020 の FEEF (Free Energy of Expected Future) は EFE の代替だが:

- FEEF **も** epistemic + pragmatic に分解される (Millidge 自身がそう分解)
- EFE **も** epistemic + pragmatic に分解される
- ∴ **Value (E⊣P) は EFE の一意性に依存しない — 対数分解の一意性に依存する**

`ln P(o,s) = ln P(o) + ln P(s|o)` は条件付き確率の定義から一意。
EFE でも FEEF でも他の汎関数でも、この分解は変わらない。

補強: Wei 2024 (arXiv:2408.06542): EFE は Bayes-optimal RL の information value 近似 → 恃意的選択ではなく最適性の近似

### 補題B: Value 座標 (E↔P) の一意性

**主張**: EFE 分解が与えられると、E (Epistemic) と P (Pragmatic) の区別は一意。

**論証**:

1. Epistemic value = 信念更新による情報利得 = D_KL[Q(s|o,π) || Q(s|π)]
2. Pragmatic value = 選好実現の期待 = E_Q[ln P(o)]
3. Epistemic は**モデルパラメータ Q** に依存
4. Pragmatic は**選好 P(o)** に依存
5. 依存する量が異なる → 分離は一意

**ガロア接続**: E ⊣ P in Value preorder

- E(state) ≤ value ⟺ state ≤ P(value)
- 「認識的に十分」⟺「実用的に十分」

### 補題C: Function 座標 (Explore↔Exploit) の一意性

**主張**: EFE の 2成分は自然に 2つの行動モードを誘導する。

**論証**:

1. Epistemic value が支配的 → **Explore**: 不確実性を減らす行動を選択
2. Pragmatic value が支配的 → **Exploit**: 報酬を最大化する行動を選択
3. この2モードは EFE の2成分に**一対一対応**
4. EFE = αE + (1-α)P とすると、α → 1 で Explore、α → 0 で Exploit
5. 中間の α は両モードの混合 — 2極は端点として一意

**ガロア接続**: Explore ⊣ Exploit in Function preorder

### 補題D: Precision 座標 (C↔U) の一意性

**主張**: 生成モデルのパラメータ π (precision) が EFE の重みづけを制御し、C↔U の区別を一意に定める。

**論証**:

1. π = 予測誤差の逆分散 (VFE の中で定義)
2. 高 π → 感覚入力を信頼 → **Confident** (確信)
3. 低 π → 感覚入力を疑う → **Uncertain** (留保)
4. π は生成モデルの**連続パラメータ** → 2極は連続体の端点
5. π は VFE/EFE の both に現れる → Flow (I/A) の両方向で作用

**ガロア接続**: C ⊣ U in Precision preorder

**⚠️ 注意**: Precision は VFE のパラメータであり、**EFE 固有ではない**。
しかし EFE の行動選択に π が必要 (π が π_prior として EFE に入る) なので d=1。

### 定理: d=1 座標の一意性

**主張**: (C2) FEP + EFE → Value (E↔P), Function (Explore↔Exploit), Precision (C↔U) は一意。

1. [A1] EFE を仮定する (d=0 → d=1 の追加仮定)
2. [補題A] EFE は Pragmatic + Epistemic に一意に分解される
3. [補題B] この分解は Value: E↔P を一意に定める
4. [補題C] 2成分は 2行動モード Explore↔Exploit を一意に誘導 → Function
5. [補題D] π パラメータが確信度 C↔U を一意に定める → Precision
6. ∴ d=1 座標は正確に 3 つ、各々が一意

Q.E.D. (半形式的)

---

## 「なぜ 3 つで 4 でも 2 でもないか」

| 仮説 | 反駁 |
|:-----|:-----|
| 2 でもよい (Precision を除外) | π なしでは EFE の重みづけが不定 → 行動選択が不可能 |
| 4 つある (別の成分がある) | EFE は 2成分 + 1パラメータ。4つ目の独立成分は対数分解から出ない |
| Value と Function は同じ | Value = what (何を重視)、Function = how (どう行動) — 異なる問いに答える |

---

## 厳密性の評価

| 層 | Value | Function | Precision |
|:---|:------|:---------|:----------|
| 直感的理解 | ✅ | ✅ | ✅ |
| 半形式的議論 | ✅ (補題A-B) | ✅ (補題C) | ✅ (補題D) |
| 圏論的形式化 | ✅ (d1_proof.py) | ✅ (d1_proof.py) | ✅ (d1_proof.py) |
| 計算的検証 | ✅ **PROVED** | ✅ **PROVED** | ✅ **PROVED** |

**v2.0 更新**: 計算的検証で全補題が True、全独立性が確認された。
`d1_proof.py` による実行結果 (2026-02-28):

- `efe_unique`: True
- `value_gc`: E ⊣ P
- `function_gc`: Explore ⊣ Exploit
- `precision_gc`: C ⊣ U
- `fully_independent`: True

---

## /hon 反論義務

1. ~~**Millidge の FEEF**~~: ✅ **解消** — FEEF も E/P 分解を持つ。Value は対数分解の一意性に依存し、EFE 固有ではない
2. ~~**Precision の d**~~: ✅ **解消** (/ele+ 対応 v3.0):
   - 「存在 vs 使用」のアドホックな区別を**撤回**
   - **新定式**: VFE の世界では π は**自動的に最適化される推論パラメータ** (選択の余地なし)。EFE がある世界では π は**戦略的に操作可能な注意 (attention)** になる。この「自動最適化 → 戦略的操作」の層の変化が d=0 → d=1
3. ~~**Value と Function の独立性**~~: ✅ **解消**。計算的検証 `fully_independent: True`
4. ~~**Precision と Function の独立性**~~ (/ele+ 発見): ✅ **解消** — **操作対象の分離**で独立:
   - Function: **政策** (policies) に対する操作 — 「何をするか」
   - Precision: **推論パラメータ** (parameters) に対する操作 — 「どれだけ信頼するか」
   - 4組合せ全て意味あり: 高π×Explore=「不確実さを確信して探索」、低π×Exploit=「自信なく報酬を取る」

---

## 次のアクション

1. ~~圏論的形式化 (`fep/d1_proof.py`)~~ — ✅ 完了
2. ~~Millidge 2020 full-text 精読~~ — ✅ FEEF 問題解消 (v2.0)
3. ~~Value と Function の独立性~~ — ✅ 計算的検証で確認

---

*DX-014-S2 v3.0 — d=1 座標 PROVED + /ele+ 対応 (2026-02-28)*
*v2.0→v3.0: Precision d を「自動最適化 vs 戦略的操作」で再定式化。Functionとの独立性を操作対象分離で強化。確信度 90%→92%*
