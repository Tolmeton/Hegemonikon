# Prior Preferences C の出自分析: 多層構造

**結論**: C は多層構造。**C₀ (NESS attracting set) は FEP 内**。C₁-C₃ は Layer B。
**日付**: 2026-03-09

---

## 1. 問い

EFE の中の C (prior preference, ln P(o_τ)) はどこから来るのか？
C は FEP の内部から帰結するか、それとも外から与えるパラメータか？

## 2. 核心的発見: 多層 C

| 層 | 名称 | C の形態 | 由来 | FEP 内/外 | 具体例 |
|:--|:--|:--|:--|:--|:--|
| **C₀** | Base | NESS attracting set | MB → 定常分布 p(o) の存在 | **FEP 内 (Layer A)** | 物理粒子の安定軌道 |
| **C₁** | Homeostatic | Interoceptive set-point | 生物学的制約 | **Layer B** | 体温 36.5°C, pH 7.4 |
| **C₂** | Learned | 経験的選好 | 環境相互作用 | **Layer B** | 食の好み, 安全な場所 |
| **C₃** | Goal | 外生的目標 | 設計者/Creator | **外部** | RL の報酬関数, HGK の WF 目標 |

### C₀ の FEP 帰結性

Friston 2022 "FEP made simpler" (135引用):
> "self-organisation as sentient behaviour that can be interpreted as **self-evidencing**"

- NESS を持つ系は attracting set を持つ
- attracting set = その系が「典型的に占める状態の分布」p(o)
- **この p(o) が暗黙の C₀**
- Self-evidencing = C₀ を維持する行為

```
FEP → NESS → attracting set → p(o) 定常分布
                                    ↓
                            C₀ = ln p(o) = 暗黙の prior preference
```

**C₀ は全ての FEP システム (岩石含む) が持つ**: 岩石の C₀ は「岩石として存在し続ける」(= NESS 上の位置を保つ)。

### C₁ 以上は外生的

Seth & Friston 2016 (678引用):
> "bodily states are regulated by autonomic reflexes that are enslaved by **descending predictions from deep generative models** of our internal and external milieu"

- C₁ (体温 36.5°C) は FEP からは導出されない
- 生物学的進化が C₁ の「値」を決定する
- FEP は「C₁ を持つシステムがどう振る舞うか」を記述するが、「C₁ が何であるべきか」は言わない

### C の除去実験 (Sajid et al. 2021)

> "removing prior outcomes preferences from expected free energy, active inference reduces to **optimal Bayesian design** (information gain maximization)"

- C を取り除いても active inference は成立する (探索のみ)
- C を加えると pragmatic value が生まれる (目標指向行動)
- → C は EFE の構造に**組み込み可能な**成分だが**必須ではない**

## 3. HGK への含意

### C は座標ではなくパラメータ

C は 7 座標のどれにも**属さない**が、複数の座標に**影響する**:
- **Value (E↔P)**: C が pragmatic value の方向を定義する
- **Function (Explore↔Exploit)**: C の確信度が探索/活用バランスを決める
- **Temporality (Past↔Future)**: C は未来の状態に対する評価基準

→ C は Valence のような半直積的修飾子ではなく、**生成モデルのパラメータ**。座標系 d 値の問題とは別カテゴリ。

### 座標系との関係

```
座標系: Flow × Value × Function × Precision × Scale × Temporality ⋊ Valence
               ↑           ↑           ↑
               C は複数座標の「評価基準」を設定するパラメータ
               座標自体ではなく、座標空間上の「方向」を決める
```

## 4. 確信度

| 判定 | 確信度 |
|:-----|:-------|
| C₀ は FEP 内 (NESS attracting set) | [推定 70%] 80% |
| C₁-C₃ は Layer B / 外部 | [確信 90%] 90% |
| C は座標ではなくパラメータ | [推定 70%] 75% |

## 5. 参照論文

| 論文 | 引用数 | 役割 |
|:-----|:-------|:-----|
| Friston 2022 "FEP made simpler" | 135 | Self-evidencing + NESS = 暗黙の C₀ |
| Seth & Friston 2016 "Interoceptive inference" | 678 | C₁ (homeostatic) の内受容的起源 |
| Sajid et al. 2021 "Expected utility" | 19 | C 除去 → Bayesian design (探索のみ) |
| De Vries 2025 "EFE as VI" | 4 | C を生成モデルに組み込む形式化 |
| Shin et al. 2021 "Prior preference learning" | 11 | C₂ の学習メカニズム |

## 6. 未解決

1. C₀ と C₁ の**境界**はどこか (NESS set-point と homeostatic set-point の区別)
2. C の精度 (precision of C) はどう決まるか — これは Precision 座標との交差
3. C の**時間変化** — C₂ は学習で変わるが、C₀ は NESS が変わらない限り不変

---
*Analysis completed: 2026-03-09 21:10 JST*
