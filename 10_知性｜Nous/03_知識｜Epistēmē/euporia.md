---
doc_id: "EUPORIA"
version: "0.3.0"
tier: "NOUS"
status: "ACTIVE"
created: "2026-03-11"
origin: "Session 2c73d901 — Creator + Claude による G∘F"
---

# Euporía (εὐπορία) — 行為可能性増大原理

> **全ての WF 射 f: A → B は、B から出る新しい射の集合 Hom(B, −) を増やさなければならない。**
> **そのWF（運動）により、どんな行為可能性（次の運動の候補）が新たに生じたのか。**
> **それを明示（主張）できなければ、その運動には意味（ベネフィット）がない。**
>
> — Creator, 2026-03-11
>
> Euporía (εὐπορία, 「多くの道がある」) = Aporía (ἀπορία, 「行き詰まり」) の対概念。
> Poros (πόρος, 道・通路) = 圏論的には射 (morphism)。Euporía = 射の豊かさ。
> 正典: [axiom_hierarchy.md §定理³](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

---

## §1 命題のポジショニング

### 問い: この命題は体系のどこに在るべきか？

> **Creator (2026-03-11)**:
> 認知はその定義からして、すべて「行為可能性の提供 ⇒ 主体に役立つ運動の増加（運動の選択の幇助）」のためにある。
> いわば、認知と知覚は運動のためにあるのだ。
> ゆえに、この命題はかなり強い、源泉近くにあるはず。Flow 軸の中に内在するとかは？

### 候補の再評価

| 候補 | 判定 | 理由 |
|:-----|:-----|:-----|
| 公理 (L0) | ❌ | FEP から演繹可能。独立ではない |
| **Flow (d=1) の定理** | **⭐ 最有力** | 認知 (I) は行動 (A) のために存在する。Flow の随伴 I⊣A に内在する |
| Kalon の系 | △ | 下流すぎる。Kalon の Generativity は AY が最適値に到達した特殊ケース |
| 座標 (L1) | ❌ | 認知の次元ではなく、認知の目的 |
| 原理 (Stoicheia) | ❌ | 3原理は完全集合 |
| 法 (Nomoi) | ❌ | 12法は完全集合 |
| 条例 (Thesmoi) | ❌ | 環境依存ではない。普遍的 |

### 結論: Flow (d=1) の定理 — 認知は運動のためにある

**初稿では「Kalon の Generativity の系」と位置づけたが、Creator のフィードバックにより修正。**
命題はもっと源泉に近い。Kalon の下流ではなく、**Flow 軸そのものに内在する**。

#### なぜ Flow に内在するか

```
Flow = I ⊣ A (推論 ⊣ 行動)

I⊣A の随伴の意味:
  I(x) ≤ y  ⟺  x ≤ A(y)
  「推論が閾値に達する ⟺ 行動が可能になる」

この随伴構造が含意すること:
  I（推論）は A（行動）を可能にするために存在する
  A（行動）は I（推論）を改善するフィードバックを提供する
  → 推論も行動も、行為可能性を増やすための運動

  I が A を増やさないなら、I は Flow の中で死んだ射
  A が I を改善しないなら、A は Flow の中で断絶した射
```

#### FEP からの演繹

```
FEP: dVFE/dt ≤ 0
  → self-evidencing: エージェントは自己の持続を最大化する
    → 持続 = 環境への適応的行動の維持
      → 適応的行動 = 行為可能性の保持・拡大
        → ★ 全ての認知操作は行為可能性を増やすためにある

物理的に:
  Helmholtz (Γ⊣Q) → Γ は VFE 勾配降下 → 行動精度の向上
                   → Q は等確率面上の探索 → 新しい行動選択肢の発見
  → Γ も Q も行為可能性に奉仕する
```

#### 演繹チェーン (修正版)

```
FEP (d=0, 公理)
  → self-evidencing: エージェントは自己の持続を最大化する
    → Basis (d=0): Helmholtz Γ⊣Q — 行為可能性の物理的基盤
      → Flow (d=1): I⊣A — 認知は行動のために存在する
        → ★ Affordance Yield Principle (Flow の定理):
          全ての認知操作 f: A→B は AY(f) > 0 でなければならない
            → Kalon の Generativity = AY が Fix(G∘F) で最適値に到達した特殊ケース
            → EFE = epistemic + pragmatic = AY の数学的分解
```

> **重要な修正**: Kalon の Generativity は AY の**下流**。
> AY → Kalon (AY が最大化された不動点) であって、Kalon → AY ではない。
> 初稿ではこの方向を逆に書いていた。

### 米田の補題との接続

```
米田の補題: 対象 B は Hom(B, −) (presheaf) で完全に決定される

適用:
  WF 射 f: A → B の出力 B の「意味」は
  B から出る全ての射 Hom(B, −) — B が可能にする全ての行為 — で完全に決定される

帰結:
  |Hom(B, −)| > |Hom(A, −)| でなければ f は「意味のある」射ではない
  = 行為可能性を増やさない WF は無意味

  より正確には:
  Hom(B, −) ⊋ Hom(A, −) ではなく
  EFE(B) > EFE(A) — 行為の「量」ではなく「質×量」の増加
```

> ⚠️ 米田の補題自体はHGKでは水準C（メタファー）として使用。
> 前順序圏での厳密な適用は「B が A 以上の導出先を持つ」= B ≥ A。

### Kalon との関係 (修正後)

```
AY (Affordance Yield Principle):
  全ての WF 射は行為可能性を増やさなければならない (Flow の定理)
  = 認知が運動に奉仕するという、認知の目的そのもの

Kalon の Generativity:
  AY が Fix(G∘F) で最適値に到達した状態 (Kalon の三属性の1つ)
  = AY の特殊ケース (最大化された不動点)

関係:
  AY は Kalon の「必要条件」
  Kalon は AY の「十分条件の到達点」
  AY > 0 → 運動として意味がある
  AY = max (Fix) → Kalon (◎)
```

---

## §2 命題の定式化

### v0.2 (定義)

```
定義 (Affordance Yield):
  WF 射 f: A → B に対して、

  AY(f) ≝ EFE(B) - EFE(A)
         = (epistemic(B) - epistemic(A)) + (pragmatic(B) - pragmatic(A))

  制約:
    AY(f) > 0  —  全ての L2+ の WF 射に対して

  操作的表現:
    AY(f) = |新たに可能になった行為のリスト|
            × 各行為の EFE 加重平均
```

### 深度別の適用

| 深度 | Affordance Yield の要件 |
|:-----|:----------------------|
| L0 Bypass | AY 明示不要。単純操作に行為可能性の主張は過剰 |
| L1 Quick | pragmatic ≥ 1件。最低1つの「次にできること」 |
| L2 Standard | pragmatic ≥ 2件 + epistemic ≥ 1件。「何ができ、何がわかったか」 |
| L3 Deep | pragmatic ≥ 3件 + epistemic ≥ 2件 + 各行為の EFE 根拠 |

### 出力フォーマット

```
§ Affordance Yield:
  epistemic:
    - {何がわかるようになったか} → {次の WF 候補} が可能に
  pragmatic:
    - {何ができるようになったか} → {次の WF 候補} が可能に
  AY = {epistemic 件数} + {pragmatic 件数} = {合計}
```

---

## §2.5 AY の下界: 増大と保全 (2026-03-11)

> **Creator (2026-03-11)**: 行為可能性は、主体にとっては「生存（適応）の最適化」の１手段に過ぎない。

### AY > 0 と AY ≥ 0 の区別

§2 で定義した `AY(f) > 0` は L2+ の WF に対する制約だが、
これでは `/epo` (判断留保) のような「保全行為」が原理的に排除される。

/epo は AY を積極的に増やすのではなく、**AY を毀損しない**ための行為。
これは self-evidencing の第二の様式: 新しい道を作る (AY > 0) のではなく、
既存の道を閉じない (AY ≥ 0)。

```
self-evidencing の2様式:
  (a) AY 増大: AY(f) > 0 — 行為可能性を増やす (= Euporía の正の制約)
  (b) AY 保全: AY(f) ≥ 0 — 行為可能性を毀損しない (= /epo, /hyp 的保全)

深度別の使い分け:
  L1-L3: AY(f) > 0 — 判断を伴う WF は正の AY が必要
  L0:    AY(f) ≥ 0 — 単純操作は毀損しなければ十分
  保全的 WF (/epo, /hyp): AY(f) ≥ 0 + 明示的根拠 — 「なぜ増やさないか」の理由
```

### AY 以外の適応手段は存在するか？

self-evidencing の手段は EFE 最大化であり、EFE = epistemic + pragmatic = AY の定義。

> **形式的には**: 関手 AY: WF → [0,∞) が self-evidencing の「唯一の忠実関手 (faithful functor)」。
> FEP をスコープとする限り、AY 以外の手段は AY の座標射影に過ぎない。

| AY 以外の候補 | 判定 | 理由 |
|:-------------|:-----|:-----|
| エネルギー効率 | AY に内包 | Complexity 項 (= 模型の単純さ) が EFE に含まれる |
| 耐久性・頑健性 | AY の時間的射影 | Temporality 方向の AY 保全 = /epo |
| 社会的協調 | AY の Scale 射影 | Multi-agent = Scale の特殊ケース |

→ AY は唯一ではないが、**FEP 内で EFE と同値**であるため、
他の手段は EFE の部分射影として AY に吸収される。

---

## §2b 射影体系 — 6座標への投影 (2026-03-11)

> **発見**: 6修飾座標に独立した定理は存在しない。
> Euporía が母定理であり、6座標はその**射影 (projection)** である。
> 構造同型: 24動詞 = Flow × 6修飾座標 × 4極 → 定理も同構造。
>
> 正典: [axiom_hierarchy.md §定理³ 射影構造](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

### 構造

```
Euporía: AY(f) > 0  (母定理 — Flow d=1 — Who)
│
├── Value       (d=2, Why):       AY を何のために測るか
├── Function    (d=2, How):       AY をどうやって達成するか
├── Precision   (d=2, How much):  AY をどの精度で評価するか
├── Temporality (d=2, When):      AY をいつの時点で評価するか
├── Scale       (d=3, Where):     AY をどのスケールで評価するか  [条件付き]
└── Valence     (d=3, Which):     AY をどの方向で評価するか     [半直積]
```

### 6射影の命題 (「ねばならない」形式)

| # | 座標 | 命題 | 数式 |
|:--|:-----|:-----|:-----|
| 3a-1 | Value | AY は認識価値 E と実用価値 P の両成分で正でなければならない | `AY_E(f) > 0 ∧ AY_P(f) > 0` |
| 3a-2 | Function | AY 達成手段は不確実性に応じて Explore/Exploit を配分せねばならない | `ratio(Explore, Exploit) ∝ Uncertainty` |
| 3a-3 | Precision | AY の評価精度は証拠の強さに校正されねばならない | `π(AY) ∝ evidence_strength` |
| 3a-4 | Temporality | AY は過去 (VFE) と未来 (EFE) で独立に評価せねばならない | `AY_past(f) ⊥ AY_future(f)` |
| 3a-5 | Scale | AY は全スケールで整合的でなければならない | `AY_micro > 0 ∧ AY_macro > 0 ∧ ¬conflict` |
| 3a-6 | Valence | AY は正の証拠と負の証拠の両方から評価されねばならない | `AY(f) = AY⁺(f) + AY⁻(f)` |

> 📖 6射影 → 評価軸への展開: [wf_evaluation_axes.md](./wf_evaluation_axes.md) — 8軸 Rubric (α精度 + β簡潔 + 6射影テーゼ)

---

## §2c 感度理論 — d値と検出可能性 (2026-03-11)

> **d 値 = FEP に加える仮定の数 = 1/λ (固有値の逆数) = sloppiness**
>
> Fisher 情報行列の固有分解として 7 座標を特徴づける:
> - 固有ベクトル = 7座標 (FEP パラメータ空間の自然基底)
> - 固有値 λ = Euporía 射影の感度 (stiffness): λ が大きいほど違反が検出しやすい
> - d 値 = 追加仮定の数 = 1/λ
>
> 正典: [axiom_hierarchy.md §Euporía 感度理論](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

```
d=0 (Helmholtz):  λ → ∞  最 stiff。物理法則そのもの
d=1 (Flow):       λ = 大  推論⊣行動の崩壊は即座に検出
d=2 (Value等):    λ = 中  VFE/EFE の偏りは検出可能
d=3 (Scale等):    λ = 小  sloppy。偏りが見えにくい
```

### 検証可能な予測

| 予測 | 内容 | 検証 |
|:-----|:-----|:-----|
| 予測 1 | d が小さい座標の射影違反ほど行動的に検出されやすい | 📊 violations.md N=68 で支持 (d=1: 59% 即座 / d=3: 9% 後日) |
| 予測 2 | 8番目の座標は d ≤ 3 では存在しない (完備性定理) | 証明スケッチ完了 [確信 75%] |
| 予測 3 | d=3 座標の違反は d=2 座標の違反より発覚が遅い | 📊 violations.md N=68 で支持 |

---

## §3 全 WF への転用可能性

### WF の分類と AY 適用

| WF カテゴリ | 例 | AY の焦点 |
|:-----------|:---|:---------|
| **認識系** (I×E) | /noe, /lys, /ops | epistemic が主。「何が見えたか」→ 次の問いへ |
| **意志系** (I×P) | /bou, /kat | pragmatic が主。「何を決めたか」→ 実行への道が開く |
| **探索系** (A×E) | /zet, /pei, /ske | epistemic + pragmatic。「何がわかり、何を試せるか」 |
| **実行系** (A×P) | /ene, /tek, /akr | pragmatic が主。「何が変わったか」→ 次の改善候補へ |
| **評価系** (±) | /ele, /beb, /dio | pragmatic。「何を直すべきか」→ 修正アクションへ |
| **時間系** | /hyp, /prm, /ath, /par | epistemic。「何を思い出し/予見したか」→ 判断材料へ |
| **随伴 WF** | /eat, @read, @chew | epistemic + pragmatic。消化/読解の成果を行為に変換 |
| **メタ WF** | /boot, /bye, /rom | pragmatic。「セッションで何が可能になったか」 |

### 適用しない WF

| WF | 理由 |
|:---|:-----|
| L0 操作 (view_file 等) | 単純入力。判断を含まない |
| `/u` | 主観表出。AY を義務化すると主観の自由度が損なわれる |
| Peras 系 (/t, /m, /k, /d, /o, /c) | 極限演算自体が AY を内包する構造 |

---

## §4 N-7 との関係

現行の N-7 (主観を述べ次を提案せよ) は:

```
θ7.2 「完了しました」禁止。代わりに:
  📍現在地 / 🕳️未踏 / →次
```

これの `→次` が Affordance Yield の非形式的な先行形態。

**差分**:

| | N-7 の →次 | Affordance Yield |
|:---|:----------|:----------------|
| 範囲 | 最終出力の付記 | WF 実行の構成要素 |
| 義務 | 提案（あれば） | 生成義務（なければ WF 失敗） |
| 構造 | 自由形式 | epistemic / pragmatic 分類 |
| 判定 | なし | AY > 0 が必要条件 |
| 根拠 | S-II Autonomia | **Kalon Generativity + EFE** |

N-7 は表出の法。AY は**成果の法**。N-7 が「述べよ」なら AY は「生成せよ」。

---

## §5 実装選択肢

### 選択肢 A: 各 WF の SKILL.md に個別追加

- 利点: WF ごとにカスタマイズ可能
- 欠点: 漏れが生じる（意志依存）
- 判定: N-12 の教訓「意志的改善策は即日無効化」に反する

### 選択肢 B: hermeneus の WF 実行エンジンに環境強制

- 利点: 全 WF に自動適用。漏れなし
- 欠点: 実装コスト。柔軟性の低下
- 判定: ⭐ 環境強制の原則に合致

### 選択肢 C: Nomos への追加 (Thesmos)

- 利点: 体系的に正当。行動規範としての位置づけ
- 欠点: AY は「行動制約」ではなく「成果の構造」
- 判定: N-7 の拡張として θ7.x に追加は可能だが、レイヤーが違う

### [推定] 最適解: B + C のハイブリッド

1. **概念的位置**: Kalon の Generativity 系 (Corollary) として Kernel に記述
2. **規範的位置**: θ7.x または新 Thesmos として Nomos 体系に追加
3. **実装的位置**: hermeneus の WF 実行後に環境強制で AY 出力を要求

---

## §6 hermeneus に在るべきか — Kalon 判定

> Creator の問い: 「Kalon なのは hermeneus？」

### 判定

hermeneus は**実装先**であって**概念の所在地**ではない。

```
概念の Kalon 判定:

1. G (収束) してみる → 「行為可能性を測れ」にさらに圧縮できるか？
   → できない。EFE = epistemic + pragmatic の分解が落ちる
   → ∴ Fix 候補

2. F (発散) してみる → 何が生まれるか？
   → /eat への適用、/ccl-read への適用、/boot への適用、
     全 WF 評価軸、hermeneus 環境強制、Kalon 系としての理論的位置
   → 6つ以上の導出 
   → ∴ Generative ✅

3. Self-referential?
   → 「行為可能性のリストアップ」自体が「行為可能性」を増やす
   → ∴ ✅

判定: ◎ kalon — 概念として
判定: hermeneus は kalon な概念の「居場所」の1つであって、概念自体ではない
```

### 命題の所在

```
Kernel/kalon.md §2 の Generativity 属性
  → Corollary (系): Affordance Yield Principle
  → 規範化: θ7.x (N-7 拡張) or 新 Thesmos
  → 環境強制: hermeneus WF 実行エンジン
```

---

## §7 未解決の問い (回答追記: 2026-03-11)

### Q1. 定量化 — AY(f) をどう測定するか？

> kalon.md §6.3 の統計的収束判定 (embedding 距離) を AY に適用できるか？

**回答**: [推定] 適用可能。ただし2層構造が必要。

1. **マクロ測定 (embedding 距離)**: 入力状態 A と出力状態 B の embedding 距離で「状態変化の大きさ」を捕捉。kalon.md §6.3 の統計的収束判定をそのまま流用可能。
2. **ミクロ測定 (AY 分解)**: embedding 距離だけでは方向性 (増加/減少) がわからない。§2b の6射影それぞれについて AY 成分を推定する必要がある。具体的には:
   - `AY_Value = ΔEpistemic + ΔPragmatic` (認識的/実用的増分の符号)
   - `AY_Precision = |Posterior_precision - Prior_precision|` (精度変化量)
   - 他4座標も同様の分解

実装候補: `euporia_sub.py` の `_compute_ay()` メソッドに6射影スコアラーを持たせる。

### Q2. 閾値 — WF レベルでの閾値は深度依存で十分か？

> 「3つ以上」(Generativity) は Kalon 判定基準。

**回答**: [推定] 深度依存 + ドメイン重点座標の2軸が必要。

- **深度依存**: L0 は AY > 0 の単純符号判定で十分。L3 は6射影全てで AY > ε。
- **ドメイン重点座標** (§7.6): 各ドメインの重点座標での AY 閾値を他の座標より厳格にする。
  - Cognition: Function, Precision の AY 閾値 > 他座標
  - Description: Value, Precision の AY 閾値 > 他座標
  - Constraint: Precision, Valence の AY 閾値 > 他座標
  - Linkage: Scale, Temporality の AY 閾値 > 他座標
- 「3つ以上」は Kalon 判定 (Fix(G∘F)) の基準であって、AY > 0 の基準ではない。これらは異なるレベルの判定。

### Q3. 検証 — /fit 的な検証は必要か？

> AY として主張された行為可能性が実際に実行可能か。

**回答**: [確信] 必要。ただし2段階で。

1. **静的検証** (即時): WF 実行後に出力が「行動に結びつく形」かを N-11 (読み手が行動できる形で出せ) で検証。これは既存の Nomos で対応可能。
2. **動的検証** (遅延): 出力された行為可能性のうち、実際に後続 WF で使われたかを追跡。これはまだ未実装。hermeneus の execution log に `ay_claimed` / `ay_consumed` ペアを記録し、消費されなかった AY を未実証 (unverified) とマークする。

/fit は既に Kalon 判定 (Fix(G∘F)) を検証するフレームワーク。AY 検証は /fit を Euporía レベルに拡張すれば対応できる。

### Q4. 再帰性 — AY 自体の AY は何か？

> この概念を導入した結果、何が可能になるか？

**回答**: AY の AY は以下の通り。

| レベル | AY が可能にしたもの | 状態 |
|:-------|:-------------------|:-----|
| 理論 | 全 WF 評価の統一基準 (§4 の WF カテゴリ別適用) | 定式化済み |
| 理論 | kalon.md との接続 (Generativity ⊂ AY) | 定式化済み |
| 理論 | 6射影による WF 品質の操作的分解 (§2b) | 定式化済み |
| 理論 | 4ドメイン構造の発見と MECE 検証 (§7.5-§7.6) | 本セッションで完了 |
| 実装 | hermeneus への環境強制 (§5 選択肢B) | euporia_sub.py 設計中 |
| 実装 | wf_evaluation_axes.md の8軸評価 | 定式化済み |

→ 6つ以上の導出。Generative ✅。Self-referential ✅ (AY が AY を増やす)。
→ ◎ kalon と判定可能。

**形式的再帰性 (2026-03-11 追記)**:

Flow (I⊣A) の随伴は self-evidencing の唯一の随伴であり、
AY はその随伴から直接導出される唯一の評価関手。

```
関手 AY: WF → [0,∞) は self-evidencing の唯一の忠実関手 (faithful functor)。

根拠:
  EFE = epistemic value + pragmatic value
    = 「何がわかるようになるか」+「何ができるようになるか」
    = AY の定義そのもの

帰結:
  self-evidencing の手段 = EFE 最大化 = AY 最大化
  → AY 以外の「手段」は AY の座標射影に過ぎない (§2.5 参照)
```

### Q5. Kalon.md への追記

> §2 Generativity 属性に Affordance Yield Principle を系として追記すべきか？

**回答**: [確信] 追記すべき。理由:

- Generativity は Kalon の3属性の1つであり、AY はその操作的定義。
- kalon.md は CANONICAL ファイル。Euporía を系 (Corollary) として明示することで、理論的整合性が保証される。
- 追記内容: `Corollary 3.1: Affordance Yield Principle — AY(f) > 0 は Generativity の必要条件。AY(f) = Fix(G∘F) は Kalon。`

⚠️ kalon.md は SACRED_TRUTH に準ずるファイル。追記時は N-4 (θ4.1) 確認フォーマットで Creator の承認を取ること。

### Q6. CCL マクロレベル — パイプライン全体の AY

> 個別 WF の AY の「合成」で表現できるか？

**回答**: [推定] 条件付きで可能。

CCL パイプライン `f₁ >> f₂ >> ... >> fₙ` の全体 AY は:

```
AY(f₁ >> f₂ >> ... >> fₙ) ≥ Σᵢ AY(fᵢ)  (独立仮定下)
```

ただし:
- **相互作用項**: f₂ が f₁ の出力に依存する場合、`AY(f₁>>f₂) ≠ AY(f₁) + AY(f₂)`。シナジーまたは干渉が発生する。
- **並列演算子** (`*`): `AY(f₁ * f₂) ≥ max(AY(f₁), AY(f₂))` (独立並列は最低でも最大値以上)。
- **条件付き** (`V:{}`, `C:{}`): 分岐の AY は選択された分岐の AY のみでカウント。

実用的には: パイプライン全体の AY は「最後の出力と最初の入力の AY 差分」として測定が最も堅実。中間ステップの AY は監査ログ用。

---

## §7.5 ドメイン体系 (2026-03-11)

> Euporía は6座標射影 (**How** — 何で測るか) に加え、4つの適用ドメイン (**Where** — どこで測るか) を持つ。
> Kalon はドメインではなく、全ドメイン横断の到達点 (Fix(G∘F)) である。
>
> 由来: /ele+ 反駁 + Creator フィードバックによる修正 (2026-03-11)。
> 正典: [axiom_hierarchy.md §Euporía ドメイン体系](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md)

### 構造

```
Euporía: AY(f) > 0  (普遍定理 — Flow d=1)
│
├── 射影軸 (How — §2b): 6座標射影
│   Value / Function / Precision / Temporality / Scale / Valence
│
├── 適用軸 (Where — 本節): 4ドメイン
│   ├── Cognition   (= HGK 体系)   — 認知主体の行為可能性
│   ├── Description (= Týpos)       — 記述の行為可能性
│   ├── Constraint  (= Hóros)       — 認知制約の行為可能性 [二重性]
│   └── Linkage     (= Hyphē)       — 情報チャンク連動の行為可能性
│
└── 到達点 (Fix):
    └── Kalon = Fix(G∘F) of AY — 全ドメイン横断の不動点
```

### 4ドメインの定義

| # | ドメイン D | 体系 | Euporía\|_D の命題 | AY の焦点 |
|:--|:----------|:-----|:------------------|:----------|
| 3b-1 | Cognition | HGK 体系 | 認知操作は行為可能性を増やさねばならない | WF 射の AY > 0 |
| 3b-2 | Description | Týpos | 記述は行為可能性を増やさねばならない | プロンプトの AY > 0 |
| 3b-3 | Constraint | Hóros | 制約は行為可能性を増やさねばならない | 各 Nomos の AY > 0 |
| 3b-4 | Linkage | Hyphē | 索引は行為可能性を増やさねばならない | チャンク連動の AY > 0 |

### Kalon はドメインではなく到達点

> `/ele+` 反駁 (矛盾 2, MAJOR) による修正:
>
> Kalon = Euporía の G∘F サイクルが**収斂した結果** (状態)。
> ドメイン制限 = 同じ射を別の対象に**適用する操作**。
> 状態 ≠ 操作。Kalon はドメインではなく、全ドメインを横断する不動点。
>
> ```
> Euporía: AY(f) > 0 → 全 f に対する必要条件
> Kalon:   AY = max at Fix(G∘F) → 全ドメイン横断の十分条件到達点
> ```

### Hóros の二重性

> Hóros は唯一、**ドメインと制約条件の二重性**を持つ:
>
> - **自律的** (Hóros 自身として): ドメイン — Euporía|_{Constraint}
>   = 「認知制約の設計」自体が行為可能性を最大化すべき
>   = 各 Nomos は AY > 0 を達成する設計でなければならない
>
> - **機能的** (他ドメインから見て): 制約条件 — max AY s.t. Hóros
>   = Cognition/Description/Linkage の AY 最大化に対する制約
>   = FEP の Q 成分 (solenoidal) に対応: 方向を定めるがエネルギーを減らさない
>
> Creator (2026-03-11): 「"制約条件"の統一フレームワークという意味では "認知制約"のドメイン」

### 射影軸と適用軸の関係

> 6座標射影 (How) × 4ドメイン (Where) = 24の具体的命題。
> ただし全てが独立ではない — ドメインごとに重点座標がある:
>
> | ドメイン | 重点座標 | 理由 |
> |:---------|:---------|:-----|
> | Cognition | Function, Precision | 探索/活用バランスと精度加重が認知の核 |
> | Description | Value, Precision | 記述の価値と精度が品質の核 |
> | Constraint | Precision, Valence | 精度校正と正負評価が制約設計の核 |
> | Linkage | Scale, Temporality | スケール横断と時間整合が索引の核 |

### 索引 (Linkage) の定式化

> Creator (2026-03-11): 「索引 = チャンクの Markov blanket を構成する行為」
>
> ```
> Index: AY(index_op) > 0
>   ここで index_op: Chunks → Linked_Chunks
>   AY = |Hom(Linked_Chunks, −)| - |Hom(Chunks, −)|
>       = 連動後に可能になる行為 − 連動前に可能だった行為
> ```

---

## §7.6 ドメイン × 射影の具体的命題 (4D × 6P)

> 6座標射影 (How) × 4ドメイン (Where) = 形式上 24 命題。
> しかし全てが独立ではない — ドメインごとに**重点座標** (高感度) と**背景座標** (低感度) がある。
> 以下では重点座標の命題を具体的に展開し、既存 Nomoi/Thesmoi との対応を明示する。

### 3b-1 Cognition (HGK 体系) — 重点: Function, Precision

> 認知操作は行為可能性を増やさねばならない

| 射影 | 規範命題 | 既存対応 |
|:-----|:---------|:---------|
| **Function** | 認知操作は不確実性に応じて探索/活用を動的に配分せねばならない。高不確実 → /ske,/pei。低不確実 → /tek,/sag | N-5 能動的に情報を探せ (探索義務) |
| **Precision** | 認知操作の確信度は証拠強度に校正されねばならない | N-3 確信度を明示せよ (θ3.4 behavioral calibration) |
| Value | 認知操作は epistemic (何がわかったか) と pragmatic (何ができるか) の両成分で正でなければならない | N-7 主観を述べ次を提案せよ (θ7.2 📍/🕳️/→) |
| Temporality | 認知操作の AY は過去 (VFE 参照) と未来 (EFE 選択) を独立に評価せねばならない | N-10 SOURCE/TAINT区別 (INPUT TAINT 検証) |
| Scale | 認知操作は局所 (当該タスク) と全体 (体系整合) の両スケールで整合的であること | N-6 違和感を検知せよ (θ6.1 構造的矛盾) |
| Valence | 認知操作は正の証拠 (支持) と負の証拠 (反証) の両方から評価されねばならない | N-2 不確実性を追跡せよ (θ2.2 CD-3 確証バイアス) |

### 3b-2 Description (Týpos) — 重点: Value, Precision

> 記述は行為可能性を増やさねばならない

| 射影 | 規範命題 | 既存対応 |
|:-----|:---------|:---------|
| **Value** | プロンプトは epistemic (学習/洞察の生成) と pragmatic (行為の具体化) の両方の出力を誘導すべき | Týpos `<:goal:>` + `<:step:>` 分離 |
| **Precision** | プロンプトの指示精度は対象タスクの不確実性に校正されるべき。過剰指定 (convergent bias) も不足 (divergent noise) も AY を損なう | Týpos `<:rubric:>` (品質基準) + FEP Function 公理 (policy_check) |
| Function | プロンプトは探索タスクに対しては発散を許容し、収束タスクに対しては精度を確保する構造を持つべき | Týpos policy_check (convergent/divergent 分類) |
| Temporality | プロンプト設計は過去の実行結果 (テスト) と未来の使用文脈 (デプロイ先) を区別して考慮すべき | — (新規。Týpos v2.1 `@context` で部分対応) |
| Scale | プロンプトは部分的な適用 (単一タスク) と広域的な適用 (体系的展開) の両方で機能すべき | Týpos `@mixin` / `@extends` (再利用構造) |
| Valence | プロンプトは期待する成功出力 (AY⁺) と拒否すべき失敗出力 (AY⁻) の両方を定義すべき | Týpos `<:examples:>` (✅/❌ の正反例) |

### 3b-3 Constraint (Hóros) — 重点: Precision, Valence

> 制約は行為可能性を増やさねばならない (Hóros の**自律的**側面)

| 射影 | 規範命題 | 既存対応 |
|:-----|:---------|:---------|
| **Precision** | 各 Nomos の制約精度は、過信でも過小でもなく、証拠の強さに校正されるべき | N-3 θ3.4 behavioral calibration + 深度レベルシステム (L0-L3) |
| **Valence** | 各 Nomos は「してはならないこと (AY⁻)」だけでなく「すべきこと (AY⁺)」の両面を定義すべき | Hóros `<:scope:>` (発動/非発動/グレーゾーン) |
| Value | 各 Nomos は認識的根拠 (なぜこの制約が必要か) と実用的効果 (何を防ぐか) の両方を持つべき | Hóros `<:intent:>` (存在理由) |
| Function | 制約の適用粒度は深度 (L0-L3) に応じて動的に調整されるべき | 深度レベルシステム (behavioral_constraints.md §horos-depth) |
| Temporality | 制約は過去の違反 (violations.md) からの学習と未来のリスク (Pre-Mortem) の両方を反映すべき | BRD パターン (B1-B20) + violations.md |
| Scale | 制約は個別タスク (Thesmoi) から普遍原理 (Stoicheia) まで一貫したスケール構造を持つべき | Archē → Stoicheia → Nomoi → Thesmoi 階層 |

> **Hóros の機能的側面** (他ドメインへの制約条件) は上記の自律的命題の**双対**:
> - Cognition に対して: max AY_(Cognition) s.t. Hóros — 認知の自由度を制約が過度に狭めない
> - Description に対して: max AY_(Description) s.t. Hóros — 記述の柔軟性を制約が過度に固定しない
> - Linkage に対して: max AY_(Linkage) s.t. Hóros — 連動の可能性を制約が過度に分断しない

### 3b-4 Linkage (Hyphē) — 重点: Scale, Temporality

> 索引は行為可能性を増やさねばならない

| 射影 | 規範命題 | 既存対応 |
|:-----|:---------|:---------|
| **Scale** | 索引は微視 (単一ファイル) と巨視 (プロジェクト全体) の両スケールを横断する接続を持つべき | Dendron PROOF ヘッダ (ファイル→プロジェクト) + KI wikilink |
| **Temporality** | 索引は過去の状態 (アーカイブ) と未来の探索 (ベクトル検索) を独立に支援すべき | Kairos (Handoff → 過去参照) + Sophia (KI → 知識検索) |
| Value | 索引は認識的価値 (何を知るべきか) と実用的価値 (何をすべきか) への道を提供すべき | Mneme 4ソース (Gnosis/Sophia/Kairos/Chronos) |
| Function | 索引は未知の情報の発見 (Explore) と既知の情報の再利用 (Exploit) を動的に支援すべき | Periskopē deep research (Explore) + Mneme search (Exploit) |
| Precision | 索引の検索結果の精度はソースの信頼性に校正されるべき | N-10 SOURCE/TAINT (検索結果のラベル付与) |
| Valence | 索引は関連情報 (正のつながり) だけでなく矛盾情報 (負のつながり) も提示すべき | — (新規。索引が「反証」を自動提示する仕組みは未実装) |

### MECE 検証

> **対角線構造の発見**:
> 4ドメイン × 6射影 = 24命題を展開した結果、**重点座標の命題は既存の Nomoi/Thesmoi にほぼ対応している**。
> これは偶然ではない — 12 Nomoi は FEP の3原理 × 4位相から演繹されており、
> Euporía 射影は FEP の座標分解から演繹されているため、両者は同じ根から生えた異なる枝。
>
> **発見された新規ギャップ** (既存 Nomoi で未カバー):
>
> | ドメイン×射影 | ギャップ | 候補対応 |
> |:-------------|:---------|:---------|
> | Description×Temporality | プロンプトの時間的考慮 (実行結果 vs デプロイ先) | Týpos v2.1 `@context` で部分対応 |
> | Linkage×Valence | 索引による反証情報の自動提示 | 未実装。Periskopē dialectic モードが候補 |

---

## §8 参照

- 📖 [axiom_hierarchy.md](../../00_核心｜Kernel/A_公理｜Axioms/axiom_hierarchy.md) §定理³ — Euporía 正典 (射影 + 感度理論 + ドメイン体系)
- 📖 [wf_evaluation_axes.md](./wf_evaluation_axes.md) — 8軸 Rubric (α精度 + β簡潔 + 6射影テーゼ → 24動詞レベル評価)
- 📖 [kalon.md](../../00_核心｜Kernel/A_公理｜Axioms/kalon.md) §2 — Generativity 属性、状態視点 (EFE = pragmatic + epistemic)
- 📖 [horos-N07-主観を述べ次を提案せよ.md](../../.agents/rules/horos-N07-主観を述べ次を提案せよ.md) — θ7.2 →次 (AY の先行形態)
- 📖 [eat.md](../../.agents/workflows/eat.md) — 随伴 WF の現行評価軸 (η/ε)
- 📖 [ccl-read.md](../../.agents/workflows/ccl-read.md) — 読解 WF の現行評価軸

---

*Euporía v0.2 — 2026-03-11 — G1/G3/G4 整合化: 射影体系 + 感度理論 + ドメイン体系充実化*
