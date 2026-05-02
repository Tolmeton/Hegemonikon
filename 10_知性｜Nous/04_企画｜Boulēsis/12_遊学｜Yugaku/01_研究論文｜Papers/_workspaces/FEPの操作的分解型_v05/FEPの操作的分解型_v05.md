# 自由エネルギー原理の操作的分解型: 体系的分類と認知アーキテクチャ座標導出

**著者**: [Creator] および Claude (Antigravity AI)

**日付**: 2026-04-29 (草稿 v0.7 / 48-frame B+C 改稿)

**投稿先候補**: arXiv cs.AI

---

## 要旨

**自由エネルギー原理** (Free Energy Principle; FEP) は、自己組織化システムを理解するための統一的な変分枠組みを与える。しかし、その数学的構造は複数の異なる分解を許しており、それらの相互関係はまだ体系化されていない。本稿は、FEP の **操作的分解型** を体系的に分類し、それが認知アーキテクチャの座標層をどのように導出するかを問う。操作的分解型とは、FEP の中核的な変分量、境界構造、方策構造、内部パラメータ、または階層構造が独立した二項へ分けられる、数学的に異なる仕方である。本稿はまず 9 つの安定した分解型を扱い、それらを **構成距離**、すなわち基本的な変分自由エネルギー (Variational Free Energy; VFE) に対して追加される仮定の数によって組織する。Scale は、階層的生成モデルと scale-free active inference に基づく **D9 Scale decomposition** として、FEP 内部から強導出される第 9 分解型である。旧 8 型版の盲検検証では 8 型中 6 型が独立に回復されたが、この実験は n=1 の予備観測であり、現行の 9 型分類については再試予定のプロトコルとして位置づける。

本稿はさらに、これらの型が認知アーキテクチャの操作空間に **座標層** を与えるだけでなく、FEP 内部から Basis、Afferent / Efferent の方向構造、6 つの修飾座標を導出することを示す。ここで注意すべきなのは、分解型と座標が 1 対 1 に対応するとは限らないという点である。Scale は D9 Scale decomposition として独立分解型であり、同時に L1 の Scale 座標を支える FEP 内部構造でもある。型の数と L1 の座標面は 1 対 1 に一致する必要がない。旧稿で中心に置いた二層フィルタは、24 操作を生成する完全性証明ではなく、座標間の直接結合と媒介結合を判定する局所的な admissibility lemma として再定位される。改稿後の中心主張は、FEP 内部から導出される座標層が 4 象限、すなわち外的知覚、推論、行為、中動態を横断することで **36 Poiesis + 12 H-series = 48 認知操作** が得られるという点にある。本稿の防衛核は、構造的 CE 層と意味論的 CI 層の分離である。FEP が導出するのは座標層と 48 slots であり、語名・CCL 呼称・ギリシャ語ラベルは別の構成層に属する。本稿はこの分離を通じて、FEP に接地した認知アーキテクチャを、過剰な語彙導出主張ではなく、反証可能な構造仮説として提示する。

**キーワード**: 自由エネルギー原理、能動推論、認知アーキテクチャ、変分推論、分解理論

---

## 1. 序論

### 1.1 問題: FEP の分解「動物園」

自由エネルギー原理 (FEP; Friston, 2019) は、生物システムおよび人工システムにおける知覚、行為、学習を理解するための統一的枠組み候補として現れてきた。その中核において、FEP は、自己組織化システムが変分自由エネルギーを最小化すると述べる。変分自由エネルギーとは surprise、すなわち負の対数証拠の上界である。

しかし、FEP の数学的構造は **複数の異なる分解** を許す。変分自由エネルギー $F$ は Complexity minus Accuracy として書ける (Friston, 2019)。同時に、Energy minus Entropy、すなわち Helmholtz 分解としても書ける。期待自由エネルギー (Expected Free Energy; EFE) $G$ は、epistemic value と pragmatic value へ分解される (Parr & Friston, 2019)。同時に、risk と ambiguity へも分解される。状態空間は Markov blanket によって internal states と external states へ分割される (Pearl, 1988; Friston, 2019)。階層拡張は scale decomposition を導入する (Friston, 2008)。精度重み付けは confidence dimension を導入する (Feldman & Friston, 2010)。内受容推論は valence dimension を導入する (Seth & Critchley, 2013)。

これらの分解は FEP 文献全体に散在しており、体系的な分類を持たない。そのため、3 つの問題が生じる。

1. **冗長性**: いくつかの分解は代数的に等価である。たとえば VFE の 3 つの $d=0$ 分解がそうである。しかし、この等価性は明示されることが少ない。
2. **構造の欠落**: 分解 **同士の関係**、すなわちどれが独立で、どれが他から導出可能なのかが形式化されていない。
3. **設計上の曖昧さ**: FEP を認知アーキテクチャ、たとえば AI システムの設計に用いるとき、どの分解をアーキテクチャの「軸」にすべきかを選ぶ原理的方法がない。

### 1.2 本稿の貢献

本稿は、これらの問題に 4 つの貢献で応答する。

1. **体系的分類**: 標準的な FEP 文献に現れる、数学的に異なるすべての分解型を列挙し、**構成距離**、すなわち基本的 VFE に対する追加仮定の数によって組織する。

2. **盲検プロトコル**: 本分類が事後的な貼り合わせではないことを検査するため、盲検列挙プロトコルを定義する。旧 8 型版では、本分類を知らない大規模言語モデルが 8 型中 6 型を独立に回復した。ただし現行稿では、この結果を検証済み証拠としては用いず、再試予定の予備観測として扱う。

3. **座標導出**: 分解型と FEP 内部構造が、認知アーキテクチャの操作空間を切る座標層を導出する。FEP は、Basis、Afferent / Efferent の方向構造、6 つの修飾座標を内部から導出する。ただし、分解型と座標は 1 対 1 に対応しない。Scale は D9 Scale decomposition として独立分解型であり、階層的生成モデルから導かれる座標でもある。旧稿の二層フィルタは、座標間の直接結合と媒介結合を判定する局所的な admissibility lemma として再配置される。

4. **48-frame 定理**: 現行の認知操作空間を、4 象限 × 6 修飾座標 × 2 極として定式化する。外的知覚、推論、行為の 3 象限が 36 Poiesis を生成し、外的知覚と行為の交差である中動態が 12 H-series を生成する。これにより、総数は 48 認知操作となる。

### 1.3 射程と限界

本稿が **主張しない** ことを明示する。

- 9 つの分解型が **可能な唯一の** 分解であるとは主張しない。2026 年時点の **標準的 FEP 文献** に現れる安定した型であると主張する。Scale は D9 Scale decomposition として扱うが、型表の完全性は今後の再試・再集計で検査される。
- 座標枠と語名を混同しない。主張するのは、Basis、Afferent / Efferent、6 つの修飾座標が FEP 内部の分解、境界、方策、精度、階層、時間、内受容構造から導出されることである。主張しないのは、それらの座標から 48 個の語名、ギリシャ語ラベル、CCL 呼称が一意に導出されることである。
- 48 認知操作の語名、ギリシャ語ラベル、CCL 呼称が FEP から直接導出されるとは主張しない。FEP が導出するのは座標層であり、呼称体系は別の構成層に属する。
- 二層フィルタは、精度重み付き方策選択から来る基準 1 と、身体化されたエージェントの内受容 / 外受容非対称性から来る基準 2 を含む。改稿後の本稿では、このフィルタを 48 操作の生成原理ではなく、座標間の直接結合 / 媒介結合を判定する局所的制約として扱う。

### 1.4 方法論的核: CE / CI 分離

本稿は外部読者に対して FEP から入る。FEP は読者がすでに知っている理論的地盤であり、そこから操作的分解型、座標層、48-frame へ進むほうが、Hegemonikon の内部語彙から入るより検査可能性が高い。

ただし、論証の核は FEP から語名を導くことではない。現行の公理階層では、L1 から L2 への移行は **構造的 CE** と **意味論的 CI** に分かれる。CE は、象限、座標、極、slot 数のような構造である。CI は、語名、ギリシャ語ラベル、CCL 呼称、skill 名のような命名・運用層である。本稿が守るのは前者であり、後者を FEP から直接演繹したとは主張しない。

---

## 2. 背景

### 2.1 自由エネルギー原理

[標準的 FEP 導入。VFE、Markov blankets、Active Inference。Friston 2019、Parr et al. 2022 から拡張予定。]

### 2.2 能動推論と POMDP 枠組み

[POMDP 定式化。方策、EFE、精度。Da Costa et al. 2020 から拡張予定。]

### 2.3 FEP 分解に関する先行研究

筆者の知る限り、FEP の分解型を体系的に列挙し分類した先行研究は存在しない。Parr, Pezzulo & Friston (2022) は包括的な教科書的処理を与えているが、分解を構成距離によって組織しておらず、それらの独立性も分析していない。Friston (2019) は力学の Helmholtz 分解を導入するが、それを VFE 分解と関係づけていない。Parr & Friston (2019) における EFE 分解は代替定式化として提示されるが、認知アーキテクチャ設計に対する構造的含意は分析されていない。

---

## 3. 方法

### 3.1 列挙プロトコル

本稿は、次の標準的 FEP 論文を体系的にレビューした。

- Friston (2019): "A free energy principle for a particular physics"
- Parr & Friston (2019): "Generalised free energy and active inference"
- Da Costa et al. (2020): Bayesian mechanics
- Parr, Pezzulo & Friston (2022): *Active Inference* (MIT Press)
- Seth & Critchley (2013): Interoceptive inference
- Feldman & Friston (2010): Attention, uncertainty, and free energy
- Pezzulo, Parr & Friston (2022): Temporal depth
- Spisak & Friston (2025): Self-orthogonalizing attractor networks

各論文について、FEP の中核量、すなわち VFE、EFE、力学、状態空間が成分へ因子化、分解、分割される箇所をすべて抽出した。採用基準は 2 つである。

1. **数学的相違性**: その分解が、既出のいかなる分解とも等価でない二項対立を導入していること。
2. **操作的関連性**: その分解が、少なくとも 1 つの実装または理論分析で用いられていること。

### 3.2 予備的な盲検検証実験

本分類が実在する数学的構造を反映しているのか、それとも事後的カテゴリ化にすぎないのかを検査するため、予備的な盲検実験を行った。ただし、この実験は現行稿の validation ではなく、再試設計の出発点である。

**設定**: 大規模言語モデル (Gemini 3.1 Pro) に次の指示を与えた。

- FEP の中核量に関する、数学的に異なる **すべての** 分解を列挙せよ。
- 数学的表現、概念上の区別、構成距離を与えよ。
- FEP から導かれる認知アーキテクチャには言及しないこと。

**重要な統制**: システム指示は明示的に次のように述べた。「あなたは 'HGK'、'Hegemonikon'、または FEP から導かれるいかなる認知アーキテクチャについても知識を持たない」。

**評価**: モデルによる独立列挙を、本稿の 9 分解型と比較し、次を数える。旧 8 型版の実験結果は履歴として保持するが、現行版では再集計を行う。

- **Hits**: モデルが独立に同定した型。
- **Misses**: モデルが同定できなかった型。
- **Extras**: モデルが同定したが、本分類には含まれない型。

### 3.3 48-frame 対応の盲検プロトコル

§3.2 の盲検実験は、旧 8 型分類が FEP 文献から独立に回復されるかを検査した予備実験である。これは方法が粗く、対象も古いため、現行稿では validation としては用いない。これとは別に、本稿のより強い主張、すなわち「FEP 分解型と FEP 内部構造が、48-frame の CE 層を支えるだけの座標制約を与える」という主張には、追加の盲検プロトコルが必要である。

検査すべき反論は明確である。

> 48-frame は FEP から出たのではなく、既存の Hegemonikon 操作体系に FEP を後から当てはめただけではないか。

この反論を処理するため、本稿では以下の protocol を事前固定する。現時点では仮設計であり、再試予定の検証面である。ここから結果はまだ主張しない。

#### 3.3.1 入力遮断

盲検列挙者には、FEP 文献と一般的な active inference 文献のみを渡す。以下は渡さない。

- Hegemonikon / HGK / CCL に関する文書。
- 36 Poiesis、12 H-series、48-frame という語。
- ギリシャ語ラベル、skill 名、動詞名。
- 本稿 §5 以降の座標表。

列挙者に求める出力は、FEP の中核量がどのような二項対立、方向構造、階層構造、パラメータへ分解されるかの一覧である。

#### 3.3.2 二段階評価

評価は 2 段階に分ける。

**Stage A: decomposition recovery**<br>
列挙者が、FEP 文献から数学的に異なる分解型を回復できるかを評価する。ここでは 48-frame への写像はまだ行わない。

**Stage B: coordinate recovery**<br>
独立評価者が、Stage A の出力だけを見て、そこに次の制約面が含まれるかを判定する。

| 制約面 | 成功条件 | 失敗条件 |
|:---|:---|:---|
| Basis | Helmholtz / solenoidal-dissipative / gradient-flow 分解が回収される | 力学的基底が一切出ない |
| Directionality | inference/action と internal/external の組から、Afferent / Efferent に相当する方向差が回収される | 推論と行為、内外境界が無関係な項としてしか出ない |
| Value | Markov blanket の internal / external 区別から、目的値の内外方向に相当する差が回収される | 内外境界が方策評価や目的値の方向と結びつかない |
| Function | epistemic / pragmatic または exploration / exploitation の対立が回収される | 方策選択の機能差が出ない |
| Precision | precision weighting が独立パラメータとして回収される | confidence / uncertainty が FEP 内部量として出ない |
| Scale | hierarchical generative model、deep generative model、または scale-free active inference から Micro / Macro に相当する階層差が回収される | 階層・粒度・スケール差が FEP 内部量として出ない |
| Temporality | VFE / EFE、past / future、temporal depth の対立が回収される | 時間方向が出ない |
| Valence | interoceptive inference または affective valence が FEP 内部セクターとして回収される | 内受容・情動符号が外部付加物としてしか出ない |

#### 3.3.3 判定基準

盲検 protocol の判定は、次の 3 段階で記録する。

| 判定 | 条件 | 含意 |
|:---|:---|:---|
| **Fail** | Basis または Directionality が回収されない | 48-frame の FEP 接地は失敗する |
| **Weak pass** | Basis と Directionality が回収され、6 修飾座標のうち少なくとも 4 つが FEP 内部構造、方策構造、階層構造、または内部パラメータとして回収される | FEP は CE 層を支持するが、弱い座標面を明示したうえで §6.2 の主張を制限する必要がある |
| **Strong pass** | Basis、Directionality、Value、Function、Precision、Scale、Temporality、Valence が回収される。Scale は階層構造として、Precision と Valence は内部パラメータまたは内受容セクターとして回収されればよい | FEP から 48-frame の CE 層が blind に支持される。ただし語名・CCL 呼称の導出までは主張しない |

この protocol で将来成功した場合、得られるのは CE 層、すなわち 4 象限、6 修飾座標、2 極、48 slots に対する blind support である。これは FEP から語名を演繹したという証明ではない。語名、ギリシャ語ラベル、H-series の個別名は CI 層に属し、別の検証を要する。

---

## 4. 結果: 分解型階層

### 4.1 9 つの型

| 型 | 名称 | 二項対立 | 距離 | 出典 |
|:---|:---|:---|:---:|:---|
| D1 | Helmholtz | Solenoidal ↔ Dissipative | 0 | Friston 2019 |
| D2 | Markov Blanket | Internal ↔ External | 1 | Pearl 1988, Friston 2019 |
| D3 | Inference ⊣ Action | Inference ↔ Action | 1 | Friston 2019 |
| D4 | VFE = Accuracy − Complexity | Accuracy ↔ Complexity | 0 | Standard |
| D5 | EFE = Epistemic + Pragmatic | Epistemic ↔ Pragmatic | 2 | Parr & Friston 2019 |
| D7 | Temporal (VFE ↔ EFE) | Past ↔ Future | 2 | Pezzulo et al. 2022 |
| D8 | Precision weighting | Certain ↔ Uncertain | 1* | Feldman & Friston 2010 |
| D9 | Scale decomposition | Micro ↔ Macro | 3 | Friston 2008; Friston et al. 2024 |
| D10 | Interoceptive gradient | + ↔ − | 2* | Seth & Critchley 2013 |

*注: D8 と D10 にアスタリスクを付すのは、これらが FEP の数学的構造と認知科学を橋渡しするためである。D9 は、階層的生成モデルと scale-free active inference に基づく Scale decomposition であり、座標としての Scale を支える独立型である。§7.1 と §7.2 を参照。*

D9 は、単一のスカラー量を二項へ分ける代数的分解ではない。生成モデルを階層レベルへ分け、同じ変分原理が複数の粒度で反復されることから生じる階層分解である。したがって、本稿では、Scale を座標としてだけでなく、FEP 内部の独立分解型として扱う。ただし、型の数と座標の数は一致する必要がない。

### 4.2 盲検実験の結果

| 指標 | 結果 |
|:---|:---:|
| Gemini が発見した候補型 | 8 |
| 本分類との一致 | 再集計対象 |
| Gemini が見落とした型 | D8 (型としての Precision)、D10 (型としての Valence) |
| Gemini の余剰型 | 再監査対象 |

**解釈**: 旧 8 型版の 6/8 評価は、方法が粗く、現行稿の validation としては使わない。再試では、Gemini 出力に hierarchical generative model / scale-free active inference が独立分解として出ていたかを再集計する。見落とされやすい型は、Precision、Valence、および Scale の階層分解としての扱いである。

**構成距離の一致**: Gemini は、同じ 4 層階層 ($d=0, 1, 2, 3$) を独立に導出し、割り当ても整合的であった。

### 4.3 型から座標への対応監査

§5 へ進む前に、分解型と 48-frame の座標の対応強度を分ける。ここでの目的は、FEP から語名を導出することではなく、どの座標が FEP 分解型または FEP 内部構造からどの経路で導出されるかを明示することである。

| 座標 | 主な対応型 | 対応強度 | 判定 |
|:---|:---|:---|:---|
| Basis | D1 Helmholtz | 強対応 | Helmholtz 分解は操作空間の力学的基底として使える。ただし、それ自体は認知操作名を生まない。 |
| Directionality | D3 Inference ⊣ Action (+D2 Markov Blanket) | 強対応 | Inference / Action は Efferent 側の切断を与え、Markov blanket は internal / external の境界を与える。両者を合わせて Afferent / Efferent の 4 象限へ lift する。 |
| Value | D2 Markov Blanket | 強対応 | Internal / External の対立は、目的値の内外方向として読むことができる。ただし D2 は Directionality にも関与するため、二重使用を明示する。 |
| Function | D5 EFE = Epistemic + Pragmatic | 強対応 | Epistemic / Pragmatic は Explore / Exploit の機能差として自然に対応する。 |
| Precision | D8 Precision weighting | 内部導出 | FEP 内の精度重みとして導かれる。標準的な分解型としては盲検実験で回収されていないが、座標としては FEP 内部パラメータから導出される。 |
| Scale | D9 Scale decomposition / 階層的生成モデル | 強対応 | FEP が生成モデルを階層化し、同じ変分原理を複数の粒度で反復する以上、局所レベルと上位レベルの差は内部構造として生じる。Micro / Macro は、この階層差の最小二項射影である。 |
| Temporality | D7 Temporal (VFE ↔ EFE) | 強対応 | VFE / EFE の時間差は Past / Future の座標として読める。 |
| Valence | D10 Interoceptive gradient | 内部導出 | 内受容推論と情動符号から導かれる。標準的な分解型ではなく、FEP の内受容セクターから現れる符号座標である。 |

この表から、C1 の主張は次のように精密化される。Basis、Directionality、Value、Function、Scale、Temporality は FEP 分解型から直接に導出される。Precision と Valence は標準的な「分解型」として常に列挙されるわけではないが、FEP 内部の精度重みと内受容推論から座標として導出される。したがって、弱いのは座標そのものではなく、分解型リストと L1 座標面の 1 対 1 対応である。特に Scale は D9 Scale decomposition として強導出する。

---

## 5. 座標導出と 48-frame

### 5.1 型から座標導出へ

各二項対立を「認知操作の名前」へ直結させるのではなく、操作空間を切る座標層へ導出する。D1 は独立した操作座標ではなく、FEP 的運動を支える基底として働く。D3 は Afferent / Efferent の方向構造への橋として扱う。6 つの修飾座標は、それぞれ二項対立を持つ。

| 座標面 | 由来する型 | 対立 | 本稿での役割 |
|:---|:---|:---|:---|
| Basis | D1 (Helmholtz) | — | 操作空間の力学的基底 |
| Directionality | D3 (+D2) | Afferent ↔ Efferent | 外的知覚・推論・行為・中動態を分ける方向構造 |
| Value | D2 | External ↔ Internal | 目的値の向き |
| Function | D5 | Explore ↔ Exploit | 戦略機能 |
| Precision | D8 | Certain ↔ Uncertain | 確信度 |
| Scale | 階層的生成モデル | Micro ↔ Macro | 射程・粒度 |
| Temporality | D7 | Past ↔ Future | 時間方向 |
| Valence | D10 | + ↔ − | 接近 / 退避、内受容的符号 |

ここで注意すべき点は、FEP が語名を直接に生むのではないということである。FEP が導出するのは、上のような座標層である。語名、ギリシャ語ラベル、CCL 呼称は、この座標層の上に置かれる別の構成層である。

### 5.2 四象限への lift

現行の認知操作空間は、Flow を単一の基底として固定する 24 操作体系ではない。Afferent / Efferent の方向構造は、操作空間を 4 つの象限へ分ける。

| 象限 | 記号 | 役割 | 操作数 |
|:---|:---|:---|---:|
| 外的知覚 | `S` | 環境から信号を受け取る | 12 |
| 推論 | `I` | 内部で構造を変換する | 12 |
| 行為 | `A` | 環境へ働きかける | 12 |
| 中動態 | `S∩A` | 知覚と行為が分かれる前の自動的・前反省的な being | 12 |

各象限には、6 つの修飾座標と 2 極が掛かる。したがって、

$$
|\mathcal{O}| = 4 \times 6 \times 2 = 48
$$

である。このうち、`S`、`I`、`A` の 3 象限は doing の操作であり、合計 36 Poiesis を形成する。`S∩A` は doing 以前の being の操作であり、12 H-series を形成する。

### 5.3 H-series: 中動態の 12 操作

H-series は、24 操作への後付けではない。H-series は、4 象限モデルにおける `S∩A` 象限そのものである。これは、知覚と行為がまだ分離していない状態、すなわち自動的・身体的・前反省的な応答の層を表す。

FEP 的に言えば、`S∩A` は感覚入力と行為出力が、まだ明示的な推論操作へ分離される前の反射弧である。システムは外界からの信号を受け取るだけでもなく、意図的に環境へ働きかけるだけでもない。入力によって状態が変わり、その変化がただちに姿勢、注意、接近、退避、予期、習慣化として現れる。この「する」と「される」の未分化な領域が、中動態である。

したがって H-series は、Poiesis の 36 操作に付け足される補助語彙ではない。Afferent / Efferent を 2 つの二値方向として展開すると、外的知覚、推論、行為だけでなく、知覚と行為が同時に立ち上がる `S∩A` 象限が残る。この第 4 象限を空欄にすると、FEP 系における反射的・習慣的・前反省的な最小化過程が操作空間から抜け落ちる。48-frame は、この抜けを閉じるために H-series を core として含む。

外部読者向けに言えば、H-series は「もうひとつの動詞リスト」ではなく、doing に先立つ being の操作面である。たとえば、危険信号に対して身体が先にこわばる、既習パターンに対して手が先に動く、場の全体像が一瞬で姿勢を変える、といった応答は、知覚、推論、行為のどれか一つへきれいに分解しにくい。ここではシステムが能動でも受動でもなく、変化が起こる場所そのものになっている。この意味で `S∩A` は中動態である。

ただし、doing と being は断絶した二分類ではない。現行公理階層では、その境界は Hom-space の Drift として扱われる。つまり、ある操作が熟練、習慣化、反射化するほど、明示的な doing から `S∩A` の being へ近づく。逆に、反射的応答を意識化して調整すると、being は doing へ戻る。H-series を core に入れる理由は、この往復可能な境界を操作空間から消さないためである。

| 座標 | 極 1 | 極 2 |
|:---|:---|:---|
| Value | `[tr]` 向変 | `[sy]` 体感 |
| Function | `[pa]` 遊戯 | `[he]` 習態 |
| Precision | `[ek]` 驚愕 | `[th]` 戸惑い |
| Scale | `[eu]` 微調和 | `[sh]` 一望 |
| Valence | `[ho]` 衝動 | `[ph]` 恐怖 |
| Temporality | `[an]` 想起再現 | `[pl]` 予期反射 |

これらは「推論する」「行為する」「観察する」という動詞より前に働く。したがって、本稿でいう 48-frame は、認知を doing の列挙に閉じ込めず、being の層を同じ操作空間へ含める。

### 5.4 二層フィルタの再定位

旧稿では、二層フィルタを 24 操作体系の完全性証明として用いた。この役割は放棄する。二層フィルタは 48 操作を生成しない。生成するのは、4 象限 × 6 修飾座標 × 2 極という frame である。

ただし、二層フィルタは不要になるわけではない。改稿後の本稿では、二層フィルタを座標間の **直接結合 / 媒介結合** を判定する局所的制約として扱う。

第一層の認知的共線性は、Function と Precision のように、同じ操作パラメータを異なる面から読んでいるペアを検出する。第二層の認知的到達可能性は、Value × Precision や Scale × Precision のように、Valence などの媒介座標を通らずには安定に結合できないペアを検出する。

したがって、二層フィルタの正しい位置は「操作空間の generator」ではなく、「操作空間内の transition constraint」である。

### 5.5 要約

本稿の §5 は、旧稿の 24 操作生成節を次の形へ置き換える。

1. FEP 分解型と FEP 内部構造は座標層を導出する。
2. 座標層は 4 象限へ lift される。
3. 3 象限が 36 Poiesis を形成し、`S∩A` が 12 H-series を形成する。
4. 総数は 48 である。
5. 二層フィルタは、完全性証明ではなく局所的な接続制約として残る。

---

## 6. 48-frame の完全性と未証明点

自然な反論がある。48 操作は FEP から導出されたのか、それとも既存の Hegemonikon 側の操作体系を FEP に当てはめただけなのか。本稿はこの反論を、主張の層を分けることで処理する。

### 6.1 48-frame 定理

**定理 2**: FEP 内部から導出される Afferent / Efferent の方向構造は 4 象限を与え、各象限に FEP 内部から導出される 6 つの二項修飾座標が掛かる。したがって、認知操作空間はちょうど 48 個の slots を持つ。

**証明**: 象限集合を $Q = \{S, I, A, S \cap A\}$ とする。修飾座標集合を $C = \{\text{Value}, \text{Function}, \text{Precision}, \text{Scale}, \text{Valence}, \text{Temporality}\}$ とする。各座標は 2 極を持つ。したがって、slot 集合は

$$
\mathcal{O} = Q \times C \times \{+, -\}
$$

であり、

$$
|\mathcal{O}| = |Q| \cdot |C| \cdot 2 = 4 \cdot 6 \cdot 2 = 48
$$

である。∎

**系**: `S`、`I`、`A` に属する 36 slots は Poiesis、`S∩A` に属する 12 slots は H-series である。

### 6.2 防衛核: CE / CI 分離

この定理は、48 個の語名が FEP から直接演繹されることを意味しない。ここで証明されるのは **CE 層**、すなわち構造的 slot の完全性である。

本稿の方法論的防衛核はここにある。FEP から直接に導くのは、名前ではなく、slot を支える座標構造である。現行公理階層の語で言えば、L1 から L2 への移行は **構造的 CE** と **意味論的 CI** に分かれる。CE は、外的知覚・推論・行為・中動態という象限、6 つの修飾座標、各座標の 2 極、そして 48 slots の数え上げである。CI は、その slot にどの語名、ギリシャ語、CCL 呼称、skill 名を与えるかである。

| 層 | 本稿で扱うもの | 主張強度 |
|:---|:---|:---|
| CE | 象限、座標、極、slot 数 | FEP 分解型と FEP 内部構造から導出される |
| CI | 語名、ギリシャ語、CCL 呼称、運用上の skill 名 | FEP から直接導出しない |

この分離を置かなければ、本稿は「FEP から語名まで導いた」という過剰主張になる。それは反論に耐えない。一方で、この分離は主張の後退でもない。本稿の主張は、FEP が操作空間の座標層を導出し、その座標層から 4 象限 × 6 修飾座標 × 2 極の 48-frame が得られる、という構造主張である。語名の一意性を放棄しても、CE 層の slot 完全性は残る。

### 6.3 二層フィルタの残る役割

二層フィルタは、48-frame の slot 数を決めない。しかし、slot 間の遷移や合成を考えるときには残る。

たとえば、Function × Precision は、方策選択における精度重み付けによって共線的になりうる。Value × Precision は、身体化されたエージェントでは Valence を介した媒介を必要としうる。これらの制約は、どの操作がどの操作へ直接遷移できるか、どの操作が媒介を必要とするかを記述する。

したがって、二層フィルタは「48 操作を生む定理」ではなく、「48 操作空間上の局所的な接続制約」である。

### 6.4 未解決 blocker

本稿は、48-frame を提示しただけでは完成しない。次の blocker が残る。

| ID | blocker | 本稿での扱い |
|:---|:---|:---|
| F1 | 分解型と L1 座標の関係が誤読されうる | §4 の型表と §4.3 の座標導出を分離する。Scale は D9 Scale decomposition として強導出する。ただし FEP 側 9 型と L1 側 8 座標は 1 対 1 対応しない。 |
| F2 | FEP から CCL を導いたのか、CCL に合うよう FEP を読んだのかが循環しうる | §3.3 に blind protocol の仮設計を置いた。旧 n=1 実験は validation として使わず、再試後に本文または appendix に記録する。 |
| F7 | FEP type と座標の対応が 1 対 1 でない | 「分解型としての列挙」と「座標としての導出」を区別し、Scale / Precision / Valence の導出ルートを明示する。 |
| H1 | H-series の読者向け説明が薄い | §5.3 を、反射弧 / 中動態 / being / Hom-space Drift の 4 線で厚くする。 |
| C1 | CE/CI 分離が本文だけで読者に伝わるか未検証 | §6.2 を本稿の防衛核として昇格し、語名導出の放棄と slot 完全性の維持を同時に示す。 |

### 6.5 要約

48-frame の完全性は、FEP から語名や運用上の呼称まですべてを演繹したという主張ではない。正確には、次の構造主張である。

1. FEP 分解型と FEP 内部構造は座標を導出する。
2. その座標層は、Afferent / Efferent の方向構造を通じて 4 象限へ lift される。
3. 4 象限 × 6 修飾座標 × 2 極により、48 slots が得られる。
4. 語名と CCL 呼称は、FEP の直接導出物ではなく、別の構成層である。

---

## 7. 議論

### 7.1 非標準分解型からの座標導出

本稿の候補型のうち、D8: Precision と D10: Valence は、旧 8 型版の盲検実験では独立に発見されなかった。これは本分類の弱点ではなく、**特徴** である。

- D8 (Precision) は、FEP 数学の中ではパラメータ ($\gamma$、逆温度) として存在するが、通常は **分解型** として提示されない。本稿が precision を座標へ昇格させるのは、方策選択におけるその役割 (Feldman & Friston, 2010) と、Spisak & Friston (2025) による計算論的実証に基づく。したがって Precision は外部 bridge ではなく、FEP 内部パラメータから導かれる座標である。

- D10 (Valence) は、身体性、すなわち内受容推論という FEP 内部の特定セクターを必要とする (Seth & Critchley, 2013)。エージェントが内受容予測誤差と外受容予測誤差を区別するという仮定を FEP に加えることで、接近 / 退避、または正 / 負の符号が生じる。

本稿は、この 2 座標を「FEP 外部からの付加物」として扱わない。むしろ、標準的な分解型としては見落とされやすいが、FEP 内部のパラメータ化および内受容セクターから座標として導出されるものとして扱う。

### 7.2 Scale の D9 強導出

Scale は、FEP の階層構造から導出される座標であり、D9 Scale decomposition として独立した操作的分解型でもある。Friston (2008) の階層的生成モデルでは、下位レベルの予測誤差が上位レベルの原因によって拘束され、同じ変分原理が複数のレベルで反復される。さらに scale-free active inference は、同じ能動推論の形式が異なる粒度にまたがって保たれることを示す。したがって、FEP 系には単一レベルの局所的最適化だけでなく、複数レベルを横断する最適化が内部的に含まれる。

この差を操作空間へ射影すると、Micro / Macro の二項対立が得られる。Micro は、単一レベル、局所状態、近傍予測誤差に対する操作である。Macro は、複数レベル、階層全体、または上位生成モデルによる拘束を扱う操作である。この二項対立は Function とは異なる。Function は探索 / 活用という方策目的の差であり、Scale はどの粒度で同じ変分原理を適用するかの差である。また Temporality とも異なる。Temporality は past / future の時間的非対称性であり、Scale は階層レベル間の粒度差である。

したがって、Scale は FEP 文献からの弱い比喩ではない。FEP が階層的生成モデルとして実装され、scale-free active inference として複数粒度へ拡張されるなら、Scale は L1 の Scale 座標を支える内部構造であると同時に、FEP 側の第 9 操作的分解型である。未解決なのは Scale の導出強度ではなく、9 型分類を blind protocol でどこまで独立再現できるかである。

### 7.3 反証条件

筆者の先行研究における自己反証プロトコルに従い、次の条件を置く。

| 条件 | 何を反証するか |
|:---|:---|
| F1 | 独立列挙が、本稿の 9 分解型では説明できない FEP 分解型を安定に生む |
| F2 | §3.3 の blind protocol において、事前に 48-frame を知らない評価者が Basis / Directionality / 主要修飾座標を回収できない |
| F3 | H-series を `S∩A` 象限として置くよりも、より小さい操作空間が同等の被覆力を持つ |
| F4 | 二層フィルタが transition constraint としても機能せず、座標間の直接結合 / 媒介結合を説明しない |
| F5 | 非二項対立、たとえば三項 Precision が、48-frame より簡潔で予測力のある体系を生む |
| F7 | FEP type と 6 修飾座標の対応が、分解型と座標導出の区別を置いてもなお恣意的にしか見えない |

### 7.4 限界

1. **n=1 の盲検実験**: 検査した LLM は 1 つだけであり、旧実験の方法も粗い。現行稿では validation ではなく予備観測として扱う。今後は複数モデルと人間のドメイン専門家を含めるべきである。
2. **身体性仮定**: 基準 2 は、エージェントが内受容推論能力、すなわち内受容状態と外受容状態を区別する生成モデルを持つことを仮定する。これは生物エージェントでは標準的だが、すべての人工エージェントに適用できるとは限らない。非身体的エージェントでは、Valence 媒介を前提にした transition constraint が弱まる可能性がある。
3. **48 操作は frame であって、常時活性化リストではない**: 48 slots は操作空間の構造であり、実践上すべての操作が同じ頻度で活性化されるとは主張しない。どの操作がどの環境で実際に活性化されるかは経験的検査を要する。
4. **H-series の外部説明は発展途上である**: H-series は現行正本では system core だが、外部読者にとっては最も unfamiliar な部分である。本稿では反射弧、中動態、being、Hom-space Drift で説明したが、実例と反例はさらに厚くする必要がある。

---

## 8. 結論

本稿は、FEP の操作的分解型に関する体系的分類を提示し、これらの型と FEP 内部構造が認知アーキテクチャ設計に必要な座標層を導出することを示した。改稿後の中心は、旧 24 操作体系の完全性証明ではない。中心は、FEP 内部から Basis、Afferent / Efferent の方向構造、6 修飾座標が導出され、それらが 4 象限へ lift されることで、36 Poiesis と 12 H-series からなる 48-frame が得られるという主張である。Scale は D9 Scale decomposition として FEP 内部から強導出される。

この主張は、FEP から語名までを演繹するものではない。FEP が導出するのは座標層であり、語名と運用上の呼称は別の構成層に属する。この分離により、本稿は、純粋数学の形式性と工学的ヒューリスティックのあいだに立つだけでなく、FEP を認知操作空間の coordinate derivation として読むための反証可能な出発点を与える。

---

## 参考文献

- Barrett, L. F. (2017). *How Emotions Are Made*. Houghton Mifflin.
- Barrett, L. F., & Simmons, W. K. (2015). Interoceptive predictions in the brain. *Nature Reviews Neuroscience*, 16(7), 419-429.
- Bechara, A., Damasio, A. R., Damasio, H., & Anderson, S. W. (1994). Insensitivity to future consequences following damage to human prefrontal cortex. *Cognition*, 50(1-3), 7-15.
- Da Costa, L., et al. (2020). The relationship between dynamic programming and active inference. *Front. Comput. Neurosci.*
- Damasio, A. (1994). *Descartes' Error*. Putnam.
- Damasio, A. (1996). The somatic marker hypothesis and the possible functions of the prefrontal cortex. *Phil. Trans. R. Soc. B*, 351(1346).
- Feldman, H., & Friston, K. (2010). Attention, uncertainty, and free-energy. *Front. Hum. Neurosci.*, 4.
- Flavell, J. H. (1979). Metacognition and cognitive monitoring: A new area of cognitive-developmental inquiry. *American Psychologist*, 34(10), 906-911.
- Friston, K. (2008). Hierarchical models in the brain. *PLoS Comput. Biol.*, 4(11).
- Friston, K. (2019). A free energy principle for a particular physics. *arXiv:1906.10184*.
- Friston, K., Heins, C., Verbelen, T., Da Costa, L., Salvatori, T., Markovic, D., Tschantz, A., Koudahl, M., Buckley, C., & Parr, T. (2024). From pixels to planning: scale-free active inference. *arXiv:2407.20292*.
- Kalai, A. T., Nachum, O., Vempala, S. S., & Zhang, Y. (2025). Why language models hallucinate. *arXiv:2509.04664*.
- Parr, T., & Friston, K. J. (2019). Generalised free energy and active inference. *Biol. Cybern.*, 113(5-6).
- Parr, T., Pezzulo, G., & Friston, K. J. (2022). *Active Inference*. MIT Press.
- Pattisapu, C., Verbelen, T., Pitliya, R. J., Kiefer, A. B., & Albarracin, M. (2024). Free energy in a Circumplex Model of emotion. *arXiv:2407.02474*.
- Pearl, J. (1988). *Probabilistic Reasoning in Intelligent Systems*. Morgan Kaufmann.
- Pezzulo, G., Parr, T., & Friston, K. J. (2022). The evolution of brain architectures for predictive coding and active inference. *Phil. Trans. R. Soc. B*.
- Seth, A. K., Suzuki, K., & Critchley, H. D. (2011). An interoceptive predictive coding model of conscious presence. *Front. Psychol.*, 2, 395.
- Spisak, T., & Friston, K. (2025). Self-orthogonalizing attractor networks from the free energy principle. *arXiv*.
- Stephan, K. E., et al. (2016). Allostatic self-efficacy: A metacognitive theory of dyshomeostasis-induced fatigue and depression. *Front. Hum. Neurosci.*, 10.

---

*草稿 v0.7 — 2026-04-29*
*状態: 24 操作中心の旧稿から 48-frame 中心へ spine を置換中。§5-6 は改稿済み。Scale は D9 Scale decomposition として強導出。§3.3 の blind protocol は再試予定の仮設計として保持。本文の防衛核は CE/CI 分離と H-series の外部説明へ移行中。*
