# Scale 座標の d 値分析: 階層構造は FEP の必然か

**結論**: Scale は **d=3 を維持** — [推定 70%] 70% 確信度 (旧 80% → 分析により上方修正)
**日付**: 2026-03-09

---

## 1. 問い

Scale (Micro ↔ Macro) の導出距離を d=3 (モデリング選択) から d=2 (FEP 帰結) に引き上げられるか？

Temporality (d=3 → d=2) の成功パターン:
```
MB → 条件付き独立性 → 部分観測 (定義レベルの同一性) → EFE → Past≠Future
```
Scale でも同種のチェーンを構築できるか？

## 2. 攻め筋と結果

### 2a. 再帰的構成チェーン (Friston 2019)

Friston 2019 "A free energy principle for a particular physics" (296引用):
> "statistical independencies, mediated by Markov blankets, speak to a **recursive composition** of ensembles (of things) at increasingly higher spatiotemporal scales."

Kirchhoff 2018 "The Markov blankets of life" (346引用):
> "autonomous systems are hierarchically composed of **Markov blankets of Markov blankets**"

**破綻点**: "speak to" / "can" ≠ "entail" / "must"
- **反例**: 単一粒子の MB システム。MB は存在するが Sub-MB は存在しない
- Da Costa 2021 "Bayesian mechanics for stationary processes" (66引用) はまさに**単一 MB** の形式化であり、FEP は**特別な仮定なしに**単一スケールで成立する

### 2b. NESS 維持チェーン

攻め筋: NESS (非平衡定常状態) の維持には内部的組織化が必然 → 組織化が階層を生む？

**破綻点**: 内部的組織化 ≠ 階層。組織化は Precision (精度行列の構造) で記述可能であり、Scale を必要としない。

### 2c. Temporality との決定的な差異

| 側面 | Temporality (d=2 ✅) | Scale (d=3) |
|:-----|:-----|:-----|
| MB → X の論理 | 定義的含意: 条件付き独立性 = 部分観測 | 構成的可能性: MB は入れ子**可能** |
| 反例の存在 | なし (全 MB は部分観測) | あり (単一粒子 MB に入れ子なし) |
| 最小定式化 | 単一 MB + FEP → POMDP (必然) | 単一 MB + FEP → FEP 成立 (階層不要) |
| 文献合意 | 批判なし | Biehl 2020 が formal errors 指摘 |

## 3. 残る攻め筋 (将来の検討)

1. **Friston の「十分に持続する系は必然的に入れ子化する」議論**: 持続 → 自由エネルギー勾配 → 勾配が大きい系は分化する → 分化 ≈ 階層？ ただし「分化」→「入れ子 MB」の論理が不明確

2. **繰り込み群との接続**: 物理学の繰り込み群は「スケール間のデカップリング」を定式化する。FEP + 繰り込み = 必然的階層？ Beck & Ramstead (2023, 4引用) が探索中だが未証明

3. **生物学的議論**: Palacios et al. 2017 "Biological self-organisation" — 自己組織化するシステムはパターン形成を通じて多スケール構造を持つ。しかしこれは経験的観察

## 4. 結論

| 評価 | 詳細 |
|:-----|:-----|
| 最終判定 | **Scale = d=3 維持** |
| 確信度 | [推定 70%] 70% (旧 80% → 「なぜ d=3 か」が明確になった分、確信度は上方修正) |
| 理由 | **MB の入れ子は FEP から帰結しない**。構成的可能性 ≠ 数学的必然性。反例あり |
| d=2 への条件 | 「持続する MB システムは必然的に入れ子化する」が数学的に証明されれば d=2 |

## 5. 参照論文

| 論文 | 引用数 | 役割 |
|:-----|:-------|:-----|
| Friston 2019 "Particular physics" | 296 | 再帰的構成の主張 (構成的) |
| Kirchhoff 2018 "Blankets of life" | 346 | 入れ子 MB の経験的議論 |
| Da Costa 2021 "Bayesian mechanics" | 66 | 単一 MB の形式化 (反例) |
| Biehl 2020 "Technical critique" | 11 | Friston 2019 の数学的批判 |
| Beck & Ramstead 2023 "Dynamic MB" | 4 | 繰り込みとの接続 (進行中) |
| Palacios 2017 "Self-organisation" | 34 | 自己組織化の生物学的観察 |

---
*Analysis completed: 2026-03-09 20:45 JST*
