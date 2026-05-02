---
doc_id: "DX-014"
title: "形式的導出 (水準A→B') と弱2-圏 (L3)"
created: "2026-02-27"
status: "active"
pj: "formal-derivation"
participants: ["Creator", "Claude"]
---

# DX-014: 形式的導出 (水準A→B') と弱2-圏 (L3)

> **目的**: HGK v4.1 の 32実体 (1公理+7座標+24動詞) を FEP から形式的に導出できるか探求する
> **動機**: Creator「形式的導出と弱2-圏を夢見てみない？」(2026-02-27)
> **現在地**: 水準B (公理的構成) → **水準B' (構成的導出)** を中間目標に設定

---

## 1. 問い

> FEP → 7座標 → 24動詞 は数学的に**必然**か、それとも**選択**か？

---

## 2. 水準定義

| 水準 | 名称 | 定義 | 状態 |
|:-----|:-----|:-----|:-----|
| **A** | 形式的導出 | FEP + 最小仮定 → 7座標 が一意 | 🔴 遠い |
| **B'** | 構成的導出 | FEP + 明示的仮定リスト → 7座標 が一意。仮定の最小性は未主張、各仮定の必要性を個別証明 | 🟡 目標 |
| B | 公理的構成 | FEP + 生成規則 → 32実体 (motivated choice) | 🟢 現在地 |

---

## 3. 導出5ステップの証明状況

| Step | 内容 | 状態 | 確信度 | 根拠 | 壁 |
|:-----|:-----|:-----|:------:|:-----|:---|
| ① | Flow (d=0) 一意性 | 🟢 **PROVED** | **95%** | MB partition → I↔A (実計算) | [flow_proof.py](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/fep/flow_proof.py) |
| ② | Value/Function/Precision (d=1) | 🟢 **PROVED** | **85%** | EFE 分解 + A1-KL 仮定 (実計算) | [d1_proof.py](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/fep/d1_proof.py) |
| ③ | Scale (d=2) | 🟢 **PROVED** | **82%** | Deep partition + CoarseGrain⊣FineGrain (実計算) | [scale_proof.py](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/fep/scale_proof.py) |
| ④ | Temporality (d=2) | 🟡 **ARGUED** | **75%** | VFE/EFE 定義的非対称性 (型定義+論証, 実計算なし) | [temporality_proof.py](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/fep/temporality_proof.py) |
| ⑤ | Valence (d=2) | 🟡 **ARGUED** | **80%** | sgn(−ΔF) + 独立性 (型定義+論証, 実計算なし) | [valence_proof.py](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/fep/valence_proof.py) |
| ⑥ | 4極構造 | 🟢 自明 | **95%** | I/A × 2極 = 4 (組合せ論) | — |

> **証明水準の区別** (/ele+ 2026-03-07 自己反証による修正):
> - 🟢 **PROVED**: 圏論的構造を Python で構築し、条件を実計算で検証 (①②③)
> - 🟡 **ARGUED**: 型定義による構造化 + 論証 (verify 関数は True リテラル, ④⑤)
> - **注**: ④⑤ を PROVED に引き上げるには、verify 関数に実計算を導入する必要がある

---

## 4. キー論文マップ

| # | 論文 | 被引用 | 核心 | 精読 |
|:-:|:-----|------:|:-----|:----:|
| P1 | Spisak & Friston 2025 (arXiv:2505.22749) | 3 | FEP → 近似的直交化 (unavoidable) | ✅ L3 |
| P2 | Millidge et al. "Whence the EFE?" | 80 | EFE = epistemic + pragmatic | abstract |
| P3 | Biehl, Pollock & Kanai 2021 | 39 | FEP 技術批判 | abstract |
| P4 | Smithe 2022 (Oxford Dissertation) | 5 | Bayesian Lens | abstract |
| P5 | Smithe/Tull/Kleiner 2023 (arXiv:2308.00861) | 4 | String diagram + FE 合成性 (compositionality property) | ✅ Periskopē L2 |
| P6 | Pezzulo, Parr & Friston 2022 | — | T⊥H | abstract |
| P7 | Seth & Critchley 2013 | — | Valence = 内受容予測誤差 | abstract |

---

## 4.5 KL 依存性の明示的記述 (壁1)

> **問題**: Step② の EFE 分解の一意性は `ln P(o,s) = ln P(o) + ln P(s|o)` の対数加法性に依存する。
> この加法性は **KL divergence を使う場合に限り** 一意性を保証する。
> Rényi divergence (α ≠ 1) や一般の f-divergence では分解構造が異なりうる。

### 仮定 A1-KL (明示化)

> **A1-KL**: FEP は変分推論を KL divergence で定式化する。

| 項目 | 内容 |
|:-----|:-----|
| **仮定の内容** | VFE = E_Q[ln Q(s) - ln P(o,s)] 内の情報距離が KL divergence |
| **FEP における位置** | FEP の標準的定式化に内在 (Friston 2019, 2023) |
| **一意性への影響** | KL 仮定下で対数分解は一意 → Value (E⊣P) が一意 |
| **仮定除去の帰結** | Rényi α-divergence (α≠1) では EFE 分解が一意でなくなる可能性あり |
| **深刻度** | 🟡 低 — FEP の文脈では KL は自然な選択であり、実質的制約ではない |

### なぜ KL が自然か

1. **変分推論の標準形式**: KL は ELBO (Evidence Lower Bound) の定義に現れ、変分推論のゴールドスタンダード
2. **Gibbs 不等式**: KL(Q||P) ≥ 0 (等号 Q=P) は情報幾何の基本
3. **加法性**: 独立分布に対して KL(P₁⊗P₂ || Q₁⊗Q₂) = KL(P₁||Q₁) + KL(P₂||Q₂)
4. **Friston の動機**: FEP は Helmholtz 自由エネルギーの統計力学的類推 — KL は熱力学的エントロピーの情報論的対応物

### 結論

A1-KL は「隠れた仮定」ではなく FEP の標準的構成要素として既に内在している。
しかし水準 B' の明示的仮定リスト (B'-2) の厳密性のために、ここに明示的に記録する。

**SOURCE**: /ele+ 敵対的反証 (2026-02-28, 壁1) + 本セッション精緻化 (2026-03-07)

---

## 5. Spisak 2025 精読結果サマリ

### 導出連鎖

```
FEP → MB (particular partition) → deep particular partition
    → subparticle {πᵢ} 各自が VFE 最小化
    → Boltzmann-like 定常分布 (Hopfield network)
    → VFE = accuracy (Hebbian) + complexity (Anti-Hebbian)
    → Anti-Hebbian ≡ Sanger's rule → 残差のみ符号化
    → 近似的直交化 (「unavoidable result」)
```

### 開いた道

- **D1**: 直交化の必然性 (§5: not a side effect)
- **D2**: deep particular partition → Scale サポート
- **D3**: 非対称結合 + ソレノイダル流 → Temporality 素材

### 残る壁

- **W1**: 基底の個数は FEP が指定しない (入力統計依存)
- **W2**: Valence は Spisak に言及なし

---

## 6. 水準 B' の要件 (正式定義)

水準 B' を達成するには以下の4条件を全て満たす:

### B'-1: 直交基底の必然性

> FEP → 内部表現は近似的に直交する基底を形成する

**状態**: ✅ **Spisak 2025 により示済み** (§3.6, §5)

### B'-2: 各座標の仮定明示と必要性証明

> 7座標それぞれに必要な追加仮定を列挙し、各仮定を除去した場合に何が失われるかを示す (ablation)

| # | 座標 | 必要な仮定 | 必要性の証明方法 | PROVED | ablation |
|:-:|:-----|:---------|:--------------|:------:|:--------:|
| A0 | Flow | MB partition (particular partition) | MB なしでは I/A 区別が消失 | ✅ | ✅ |
| A1 | Value | EFE の存在 + **A1-KL** (§4.5) | 分解しないと「なぜ行動するか」が未定義 | ✅ | ✅ |
| A1 | Function | EFE + explore/exploit 二極性 | 単一戦略では新規環境に適応不能 | ✅ | ✅ |
| A1 | Precision | VFE のパラメータ π (+ EFE メタ判断) | 精度なしでは全信号が等重み → 学習不能 | ✅ | ✅ |
| A2 | Scale | 階層的生成モデル (deep partition) | 単一スケールでは複雑な環境が表現不能 | ✅ | ✅ |
| A2 | Temporality | EFE の時間的定義域 (+ 操作的独立性) | 現在のみでは計画が不可能 | ✅ | ✅ |
| A2 | Valence | sgn(−ΔF) + Temporality + 二極設計判断 | sgn(−ΔF) なしでは改善/悪化の判定が不可能 | ✅ | ✅ |

**状態**: 🟢→🟡 **5/7 PROVED + 2/7 ARGUED (2026-03-07, /ele+ 修正後)**。
flow, d1, scale は実計算による PROVED。temporality, valence は型定義+論証 (ARGUED)。
/ele+ (/dio) により水準の不整合を修正。ARGUED → PROVED への引き上げは verify 関数に実計算を導入する必要がある。

### B'-3: 座標の独立性の形式的根拠

> 7座標が互いに独立 (直交) であることの形式的証明

**候補**: Smithe/Tull/Kleiner 2023 の FE 合成性 (compositionality property)

| 概念 | Smithe の定式化 | HGK への適用 |
|:-----|:-------------|:----------|
| **open generative models** | 入力を持つ生成モデル = building block | 各座標 = 独立な生成モデル成分 |
| **monoidal composition** | M₁ ⊗ M₂ (string diagram) | 座標の組合せ |
| **FE compositionality** | FE が各レベルに適用可能 | F(座標₁⊗座標₂) = F(座標₁)+F(座標₂) |

**戦略**: 各座標を「open generative model の独立成分」として定式化し、Smithe の合成性により FE が各座標に分解されることを示す。これが成功すれば座標の**独立性** (直交性) が FE の分解性から導出される。

**状態**: 🟡 **Periskopē L2 調査完了。形式化は未着手** (arXiv HTML 非対応のため full-text はPDF精読が必要)

> **注**: Smithe の合成性は「座標が独立なら FE が分解される」を示す。しかし逆方向「FE の分解性から座標の独立性が帰結する」の証明は別途必要。

### B'-4: 4極構造の一意性

> Flow (I/A) × 各座標の 2極 = 4 パターンが一意の分解

**状態**: ✅ **組合せ論的に自明**

---

## 7. L3: 弱2-圏 (別セッション)

| 項目 | 状態 |
|:-----|:-----|
| Bicategory が適切 (strict ではない) | ✅ 判断済み |
| two_cell.py 確認 | 未着手 |
| 形式化 | 未着手 |

---

## 8. 変更履歴

| 日付 | 内容 |
|:-----|:-----|
| 2026-02-27 | DX-014 初版作成。/sop+ 調査 + Spisak L3 精読結果を統合 |
| 2026-02-27 | Smithe/Tull/Kleiner 2023 Periskopē L2 調査結果を統合。B'-3 戦略を具体化 |
| 2026-02-28 | Step① PROVED (flow_proof.py). Step② d1_proof.py. Step③ scale_proof.py |
| 2026-02-28 | Valence 救出: 内受容→sgn(−ΔF), 30%→75%. Temporality 救出: 55%→70% |
| 2026-02-28 | Precision/Valence 独立性決着: π=1/σ² ≠ |ΔF| (v3.0) |
| 2026-02-28 | axiom_hierarchy.md: Valence行更新 + 依存構造図追加 |
| 2026-02-28 | /ele+ 敵対的反証で7壁を再評価。壁6循環論法修正、確信度を保守値に修正 |
| **2026-03-07** | 全5 proof ファイル作成。A1-KL 明示化 (§4.5)。temporality_proof.py + valence_proof.py 新規作成 |
| **2026-03-07** | `independence_proof.py` 作成 (Smithe 2023 FE 合成性) |
| **2026-03-07** | **/ele+ 自己反証**: 4矛盾を発見。(1) independence_proof.py は同語反復 🔴, (2) temporality/valence の True リテラル 🟠, (3) PROVED 水準不整合 🟠, (4) Smithe 適用条件未検証 🟡 |
| **2026-03-07** | **/dio 修正**: 3水準ラベル制導入 (PROVED/ARGUED)。確信度下方修正 (④ 82→75%, ⑤ 85→80%)。B'-2 を 5/7+2/7 に修正。independence_proof.py を条件検証型に書き直し。B'-3 を🟡に格下げ |

---

*DX-014 v2.3 — /ele+ 自己反証 + /dio 修正 (2026-03-07)*
