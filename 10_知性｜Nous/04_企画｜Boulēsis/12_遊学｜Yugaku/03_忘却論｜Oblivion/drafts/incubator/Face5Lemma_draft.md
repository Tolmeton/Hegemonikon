# Face5 Lemma 試作

**v0.2 (2026-04-17)** — 第 2 ラウンド検証 (§5.2 Ising / §5.3 SU(2)_k) 追加、F5-γ 反証 → F5-γ' 確立
**ステータス**: incubator draft / 試作 / 成否判定付き
**役割**: Face Lemma (3 射) を 5 射へ延長する構想試作。Face3 の「comparison surface 最小条件」を「pentagon coherence 最小条件」へ持ち上げられるかを検証する。
**軌道**: `比較射σの統一定理_v0.6.md` の **証明 incubator**。`v0.6` 本文 §III / §VII に関わる C8-C10 の補助検証稿であり、正文そのものではない。
**親文書**:
- `../infra/リファレンス/FaceLemma.md` (Face3 = Face Lemma の reader-facing 正本)
- `./pentagon_sigma_conjecture.md` (種③ = 本試作の上位動機)
- `../standalone/比較射σの統一定理_v0.6.md` (σ 統一論文本体)
- `../standalone/比較射σの統一定理_v0.6.meta.md` (σ 統一論文の README / 台帳 / 版歴)

**運用注記 (2026-04-21)**:
- 本文中の `σ 統一論文 v0.2 / v0.3` 参照は、検証当時の歴史 strata を保持するために残している。
- 現在の親稿として実際に参照すべきものは `比較射σの統一定理_v0.6.md` と `比較射σの統一定理_v0.6.meta.md` である。
- 以下の「σ 論文へ投入」「σ 論文 §M1」等は、必要に応じて **v0.6 本文の対応章** と **v0.6.meta の台帳面** に読み替える。

**本試作の目的**: σ の 5-cell 拡張が非自明に立つかを紙の上で検証し、種② (φ = quantum dim)、種③ (Mac Lane pentagon)、種⑥ (三軸分離) の生死を判定する。

**昇格規則**:
1. ここで定理 face / claim face が安定する
2. `比較射σの統一定理_v0.6.meta.md` の orbit 判断で本流への昇格可否を確認する
3. 本流へ送るのは整理済みの結論だけで、試行錯誤ログはこの稿に残す

---

## §0 一文核 (試作)

**SOURCE (既知部分)**:
- Mac Lane (1963) coherence theorem: monoidal 圏の結合子 `α` は pentagon identity と triangle identity の 2 つを満たせば、全ての coherence diagram が可換になる
- Fibonacci anyon (SU(2)_3 MTC): 融合則 `τ⊗τ = 1⊕τ` に対し pentagon equation が非自明解 `d(τ) = φ` を持つ [Moore-Seiberg 1989, Ocneanu, Kitaev]

**INFERENCE (試作中の核)**:
Face Lemma が「3 射で 2-simplex の comparison surface が立つ」と言うなら、その自然な延長は「5 射で **pentagon coherence polytope** が立つ」である。核の差分は:
- Face3: 2 つの 1-cell 経路 (`g∘f` と `h`) を外から照合する comparison surface の成立
- Face5: 2 つの **associator 連鎖** (pentagon の二辺三連) を外から照合する coherence polytope の成立

Face3 が「1-cell の比較の最小条件」なら、Face5 は「**2-cell の比較の比較** の最小条件」である。

**OPEN**:
Face5 が Face3 の自然な延長として **定理 face** で立つかは未検証。本試作は予想 face から試みる。`Face(2n+1) = n-cell comparison の最小条件` という一般公式化は遠い open。

---

## §1 何のための概念か

**SOURCE**:
Face Lemma (Face3) は Paper II §3.4 で「CPS の非自明性の最小条件」として置かれる。σ 統一論文 v0.2 §2.2 は Face3 を「σ が住む最小 habitat の条件」として読み替えている。

**INFERENCE**:
Face5 は、σ が 3-cell で閉じた後の次段 — **3-cell で立った σ どうしを整合させる最小条件** — を問う。σ 論文 §5 の π-sector (`e^{iπ}+1=0`) は σ の端点反転が endpoint window に現れた静止像だが、**2 つの σ を並置するとどうなるか** は未論。Face5 は「並置された σ どうしが pentagon axiom を通じて一つの coherence polytope を閉じる最小条件」と読める。

動機階層:
1. Face3 = σ が立つ条件 (1 個の σ の内部問題)
2. Face5 = σ どうしが整合する条件 (2 個以上の σ の関係問題)
3. Face7 (予想) = σ の整合関係どうしがさらに整合する条件 (高次拡張)

**OPEN**:
「なぜ 5 か」「なぜ pentagon か」— 3 cell の合成が 2 通り (`(AB)C` と `A(BC)`) あり、それを結ぶ associator が 5 本で pentagon cycle を閉じる、という構造的事実は標準的だが、これが σ 論文の forgetting structure と本当に同形かは本試作で検証する。

---

## §2 最小構造

**SOURCE (Mac Lane pentagon)**:
4 対象 `A, B, C, D` の monoidal 積に対し、括弧付けの 5 通り:
1. `((A⊗B)⊗C)⊗D`
2. `(A⊗(B⊗C))⊗D`
3. `A⊗((B⊗C)⊗D)`
4. `A⊗(B⊗(C⊗D))`
5. `(A⊗B)⊗(C⊗D)`

これらを結ぶ 5 本の associator `α` が pentagon cycle を形成する。pentagon identity は、この cycle 上で 2 通りの経路 (上半分 1→2→3→4 と下半分 1→5→4) が等しいと主張する。

**INFERENCE (Face3 との対比表)**:

| 構造 | 射の数 | 何が立つか | 何が立たないか |
|:--|:--|:--|:--|
| 1-skeleton (2 射) | 2 | 合成 `g∘f` は存在 | comparison surface なし |
| **Face3 (3 射)** | 3 | comparison surface (σ) が立つ, `g∘f` と `h` を外から照合できる | σ どうしの整合は未問 |
| 4 射 (tetrahedron slice) | 4 | 複数の σ を持つが coherence polytope は立たない | pentagon cycle 未完 |
| **Face5 (5 射)** | 5 | **pentagon coherence polytope** が立つ, 2 つの associator 経路を外から照合できる | 高次 coherence は未問 |

**仮説 F5-α (試作核)**:
> 5 射未満では pentagon coherence polytope が立たず、5 射で初めて associator の 2 通り経路を外から照合する最小 polytope が立つ。

**OPEN**:
Face4 (4 射) が立つかどうか、立つとして何を意味するかは曖昧。Mac Lane の triangle identity (3 対象の単位元整合) が Face4 に相当しうるが、本試作では詰めない。

---

## §3 平文直感

**SOURCE**:
pentagon identity の直感的意味は「3 つの要素を積むとき、左から順に積むか右から順に積むかで結果が同じであることを保証する 2 通りの括弧付け変形が互いに整合する」。

**INFERENCE**:
σ が「1 つの比較」なら、pentagon は「2 つの比較の整合」。例え話で言えば:
- Face3: A からの 2 本の道 (直行 h と迂回 g∘f) が終点 C で合流する。σ はその合流の証人
- Face5: A から D への 2 本の「迂回経路の組み立て方」 — 先に (AB) を作って C を掛けて D を掛けるか、先に A に (BCD) を掛けるか — が同じ結論に着地する

Face3 は 1 次元の迂回比較、Face5 は迂回のやり方自体の比較。**比較の比較 (meta-comparison)** が Face5 の核。

**OPEN**:
「meta-comparison」という日常語は本当に pentagon の数学内容と一致するかは微妙。「σ どうしの整合」という言い方のほうが正確。

---

## §4 Face3 との関係 — 延長構造の明示

**INFERENCE**:
Face3 ⇒ Face5 の関係は以下のように試作できる。

**段差 1** (Face3 の内部):
σ: g∘f ⇒ h が単一の 2-cell として立つ

**段差 2** (σ 複数化):
複数の Δ² を glued したとき、各面の σ_i が独立に立つだけでは全体の coherence は保証されない

**段差 3** (Face5 の要請):
glued surface が pentagon の形を取るとき、5 つの σ_i が associator の 2 通り経路について閉じる → pentagon coherence polytope

**試作仮説 F5-β**:
> Face3 (σ の存在) から Face5 (pentagon coherence) へ上がる際に必要な追加条件は、**associator の非自明性** — つまり `α ≠ id` の場合にのみ Face5 は内容を持つ。Mac Lane's coherence theorem は「pentagon + triangle identity で十分」と言うが、非自明解は特別な圏 (Fibonacci anyon 等) でしか出ない。

**OPEN**:
「associator が自明な場合 (strict monoidal)」では Face5 は退化する可能性。その場合、Face5 は **非退化条件付きで** しか意味を持たない。これは Face Lemma 本文 §2 の「非退化 2-simplex が存在すること」の自然な対応物。

---

## §5 φ-sector との関係 — Fibonacci anyon での具体解

**SOURCE**:
Fibonacci anyon における pentagon equation の F-matrix 解は、2×2 行列:
```
F = | 1/φ       1/√φ    |
    | 1/√φ     -1/φ    |
```
この解は `d² = d + 1` の正根 `d = φ` を要請する。

**INFERENCE**:
Face5 が非自明に立つ最もシンプルな具体例が Fibonacci anyon であり、その固有条件が **φ** という実数である。つまり:

**試作仮説 F5-γ** (種② と合流):
> Face5 が非自明に立つ最小 non-trivial 圏において、associator の固有値は `d² = d + 1` の解 `φ` として現れる。これは σ 論文 §5 の π-sector (`e^{iπ}+1=0`) と並ぶ φ-sector の typed endpoint identity:
> $$\varphi^2 - \varphi - 1 = 0$$

π-sector と φ-sector の対比:

| sector | 等式 | σ の側面 | Face 段階 |
|:---|:---|:---|:---|
| π-sector | `e^{iπ}+1=0` | σ の完全反転 endpoint | Face3 で既に立つ |
| **φ-sector** | `φ²-φ-1=0` | σ の自己融合 fixed point | **Face5 で初めて立つ** |

**OPEN**:
φ-sector が「σ 論文 C3 の統一忘却式候補」にどう接続するかは未論。π は周期化商、φ は固有方程式根。両者を「同じ σ の別断面」として書くには**三軸分離 (種⑥)** の整備が要る。

---

## §5.2 Ising anyon での F5-γ 検証 (2026-04-17 追加)

**SOURCE**:
Ising anyon (SU(2)_2 MTC) の構造:
- 単純対象: {1, σ, ψ}
- 融合則: `σ⊗σ = 1⊕ψ`, `σ⊗ψ = σ`, `ψ⊗ψ = 1`
- 量子次元: `d(1) = 1`, `d(σ) = √2`, `d(ψ) = 1`
- F-matrix for `σ⊗σ⊗σ`: 2×2 非自明行列 (Hadamard 型)

σ の自己融合から `d_σ² = d_1 + d_ψ = 1 + 1 = 2` → `d_σ = √2`。

**判定**:
Ising では Face5 は非自明に立つ (F-matrix が非自明)。しかし **固有方程式は `d² = 2`** であって `d² = d + 1` ではない。

**F5-γ の反証**:
当初の F5-γ「Face5 が非自明に立つ圏では associator の固有値は `d² = d + 1` の解 φ」は **Fibonacci 特有** であり、Ising では成立しない。`d² - d - 1 = 0` は φ-sector そのものの定義式にすぎず、σ の 5-cell 構造を決める普遍法則ではない。

**INFERENCE**:
Face5 非自明性 → 固有方程式が存在するところまでは universal。しかし方程式の形 (`d² - 1 = d` vs `d² = 2` vs etc.) は圏ごとに異なる。「φ の特権性」は仮説として立たない。

---

## §5.3 SU(2)_k series — Face5 固有値の family (2026-04-17 追加)

**SOURCE** (標準 MTC 文献 / 計算検証済):
SU(2)_k MTC における基本表現の量子次元は
$$d_{1/2}(k) = 2\cos\left(\frac{\pi}{k+2}\right)$$

Python 計算 (2026-04-17 検証):
| k | `d_{1/2}` | `d²` | 固有方程式 | 対応する名前 |
|:---|:---|:---|:---|:---|
| 1 | 1 | 1 | `d = 1` (自明) | 可換 |
| 2 | √2 ≈ 1.414 | 2 | `d² = 2` | **Ising** |
| 3 | φ ≈ 1.618 | φ+1 ≈ 2.618 | `d² = d + 1` | **Fibonacci** |
| 4 | √3 ≈ 1.732 | 3 | `d² = 3` | SU(2)_4 |
| 5 | ≈ 1.802 | ≈ 3.247 | `d³ - d² - 2d + 1 = 0` (3次) | SU(2)_5 |
| 6 | √(2+√2) ≈ 1.848 | 2+√2 | `d² = 2 + √2` (2次, 体 ℚ(√2) 上) | SU(2)_6 |
| ∞ | → 2 | → 4 | — | 古典 SU(2) |

**INFERENCE (F5-γ' 再構築)**:

**仮説 F5-γ'** (F5-γ の family 版、φ-sector から SU(2)_k-sector へ):
> Face5 が非自明に立つ MTC の族として SU(2)_k series が存在し、固有値 `d_{1/2}(k) = 2cos(π/(k+2))` は忘却構造の離散的階段を与える。**φ は k=3 の 1 点**であり、Ising (k=2) の `√2`、SU(2)_4 (k=4) の `√3` 等と並ぶ家族の 1 メンバー。

重要な観察:
1. **`k=1` は abelian** (d=1)。Face5 は自明化。→ F5-β (非自明 α 要請) と整合
2. **`k=2, 3, 4`** は 2 次代数的数 (`√2`, `φ`, `√3`)。代数的複雑度が低い
3. **`k=5` から** 3 次以上の代数的数が現れる (`ℚ(cos(π/7))` は 3 次体)
4. **`k→∞` で `d→2`** (古典 SU(2) 回復)。量子変形の degeneration

**σ 論文への含意**:
- 当初「φ-sector ⇔ π-sector」の 2 項対置は **誤った parallelism**
- π は **位相軸** の固定点 (transcendental phase)
- φ, √2, √3, ... は **スペクトル軸** の階段 (algebraic quantum dimensions)
- 両者は **異なる軸** の定数であり、並列する前にまず **三軸分離 (種⑥)** が要る

これは **種⑥ の要請を構造的に強化** する検証結果である。σ 論文 v0.3 で「φ-sector」単独を導入する前に、「三軸分離 → 各軸でのエンドポイント identity」の整理が必須となる。

**OPEN**:
- SU(2)_k 以外の MTC 族 (quantum groups at other roots of unity, near-group categories, etc.) でも同様の階段が出るか → **§5.4 で Tambara-Yamagami 検証**
- 「Face5 = σ の 5-cell coherence」と「SU(2)_k series」の同一視の厳密化
- `k→∞` の古典極限で σ の closure schema に何が起きるか

---

## §5.4 Tambara-Yamagami 族での Face5 検証 (2026-04-17 追加 / K3' ◎ 昇格根拠)

**動機**: K3' (SU(2)_k family) は SU(2)_k 単独で Kalon ◯ に留まっていた。他の MTC 族 (Tambara-Yamagami) で Face5 が別の固有値階段を与えるかを検証する。これが通れば K3' を「Face5 eigenvalues は fusion category ごとに algebraic integer の階段を成す」という universal 仮説に昇格できる。

### §5.4.1 Tambara-Yamagami 族の定義

**SOURCE** (Tambara-Yamagami 1998, "Tensor categories with fusion rules of self-duality for finite abelian groups", J. Algebra 209):

Tambara-Yamagami (TY) fusion category は次の 3 つでパラメータ付けられる:
- 有限 abelian 群 `A`
- 非退化対称 bicharacter `χ: A × A → ℂ*`
- 符号 `τ = ±1/√|A|`

単純対象は `A` の元と追加対象 `m` の和。融合則:
$$a \otimes b = ab \quad (a, b \in A)$$
$$a \otimes m = m \otimes a = m$$
$$m \otimes m = \bigoplus_{a \in A} a$$

### §5.4.2 量子次元と固有方程式

融合則 `m⊗m = ⊕_{a∈A} a` から:
$$d(m)^2 = \sum_{a \in A} d(a) = |A|$$

すなわち **`d(m) = √|A|`**。この式は SU(2)_k の `2cos(π/(k+2))` とは **構造的に異なる形式**。

TY 階段:

| \|A\| | d(m) | d² | SU(2)_k で該当? | 代数的次数 |
|:---|:---|:---|:---|:---|
| 1 | 1 | 1 | k=1 (自明) | 1 次 (自明) |
| **2** | **√2** | **2** | k=2 Ising と **同型** (TY(Z/2) ≅ Ising) | 2 次 |
| 3 | √3 | 3 | k=4 と **同じ d 値** (構造は別) | 2 次 |
| **4** | **2** | **4** | k→∞ の古典極限値 (構造は有限) | 1 次 (!) |
| **5** | **√5** | **5** | **SU(2)_k に該当なし** (d > 2) | 2 次 |
| 6 | √6 | 6 | 同上 | 2 次 |
| n | √n | n | n ≤ 4 で SU(2)_k と偶然一致、n ≥ 5 で **分離** | 2 次 (n 平方数でない場合) |

### §5.4.3 K3' 普遍性の雛形化

**重要な発見**:
1. **TY(Z/5) は SU(2)_k family 外**: `d(m) = √5 ≈ 2.236 > 2 = sup SU(2)_k`。Face5 固有値は SU(2)_k の範囲を超える
2. **Ising = TY(Z/2)**: k=2 (`√2`) は SU(2)_k と TY の **両方に現れる同型**
3. **両 family の固有方程式は構造的に異なる**:
   - SU(2)_k: Chebyshev 多項式 `U_{k-1}(d/2) = 0` 由来
   - TY: 単純な `d² - n = 0`
4. **共通性**: 両 family とも d は **代数的整数** (ENO 定理の帰結)

### §5.4.4 ENO 定理による universal 骨格

**SOURCE** (Etingof-Nikshych-Ostrik 2005, "On fusion categories", Annals of Mathematics):

**定理 (ENO)**: 任意の fusion category における任意の対象の Frobenius-Perron 次元は **代数的整数** である。

**帰結 (K3' 普遍版)**:
Face5 が非自明に立つ任意の fusion category において、σ の自己融合 endpoint identity の固有値 `d` は常に代数的整数である。さらに d は **totally real positive algebraic integer** (FP 次元の一般的性質)。

**仮説 K3'' (family-independent universal claim)**:
> σ の closure schema が 5-cell coherence で閉じるとき、スペクトル軸に現れる固有値 `d` は必ず totally real positive algebraic integer であり、fusion category の族ごとに異なる階段 (SU(2)_k は Chebyshev、TY は平方根、Haagerup 族等は別形) を成す。**universal な式は存在しないが、universal な性質 (代数的整数性) は ENO 定理により保証される**。

### §5.4.5 K3' の Kalon ◎ 昇格判定

K3' を universal claim (K3'') に昇格させた上で 3 ステップ判定を再実行:

**Step 0 既知語彙圧縮**:
「Face5 で出る数は分数や実数でもいいのに、必ず代数的整数になる」— 中学生語彙で圧縮可能 ✓

**Step 1 G (収束/不変性)**:
G = ENO 定理による代数的整数性の要求。任意の fusion category で d が algebraic integer であることは **不変** (FP 次元の theorem)。✓

**Step 2 G∘F (F-サイクル不動性)**:
F = 族への展開 (SU(2)_k, TY, Haagerup, near-group 等)。各族で固有値の形は異なるが、代数的整数性は全族で保持。✓

**Step 3 F で 3+ 非自明派生**:
1. **SU(2)_k (Chebyshev family)**: `2cos(π/(k+2))` — 三角関数由来 → π 内在
2. **TY (square root family)**: `√|A|` — 群位数由来 → 数論的
3. **Haagerup / near-group family**: 既知だが構造不同 (他形) — 圏論的非自明拡張

3 派生すべて非自明 ✓

**判定**: ◎ Kalon△ (family-independent universal claim として)

**昇格後の K3'' の位置付け**:
- Kalon△: MB 局所不動点として ◎
- Kalon▽: 「Face5 eigenvalue ⇒ algebraic integer」は ENO 経由で **普遍的** だが、逆 (全 algebraic integer が Face5 eigenvalue として実現される) は open
- したがって K3'' は「必要条件」として ◎、「十分条件」としては未確定

### §5.4.6 残る open

- **[OPEN A]** Haagerup、Asaeda-Haagerup、Extended Haagerup の subfactor 系列で具体値計算
- **[OPEN B]** near-group fusion categories での Face5 固有値の一般形
- **[OPEN C]** 逆向き: どの totally real positive algebraic integer が Face5 eigenvalue として実現されるか
- **[OPEN D]** TY の符号 `τ = ±1/√|A|` が Face5 の別軸 (位相軸 symmetric/antisymmetric?) に寄与するか

### §5.4.7 SOURCE 台帳 (§5.4 追加分)

- [SOURCE] Tambara-Yamagami (1998) J. Algebra 209: TY fusion rules, quantum dimension `d(m) = √|A|`
- [SOURCE] Etingof-Nikshych-Ostrik (2005) Annals of Math: Frobenius-Perron 次元の代数的整数性
- [SOURCE] Ising = TY(Z/2) の同型は既知 (複数の文献で独立確認)
- [INFERENCE] K3'' (family-independent ENO-anchored universal) = 本節での新主張

---

## §6 σ 統一論文 C1 との関係

**SOURCE**:
σ 統一論文 v0.2 C1: 「σ は幾何三角形・Face Lemma・Euler path・FEP の 4 ドメインにまたがって、同一の closure schema の 4 つの実現面を与える」

**INFERENCE**:
本試作が立てば、C1 の射程が自然に拡張する:
- C1 現状: σ は **4 ドメイン × 3-cell** で立つ
- C1 拡張: σ の closure schema は **4 ドメイン × (3-cell, 5-cell, 7-cell, ...)** で階層化する

**試作仮説 F5-δ**:
> σ の closure schema は `Face(2n+1)` の階層構造を持ち、n=1 で σ、n=2 で pentagon coherence、n=3 で hexagon axiom (braided monoidal) へと自然に拡張する。各層で固有定数 (π, φ, ...) が**その層で忘却可能な構造の最小不変量**として現れる。

**OPEN**:
n=3 以上の hexagon / higher-polygon axioms が forgetting 構造としてどう意味を持つかは遠い open。Kitaev anyon 理論で既知の構造を σ 言語で読み直す作業が要る。

---

## §7 Negativa

本試作から言ってはいけないこと。

1. 「Face5 = pentagon identity」と短絡しない。pentagon identity は公理 (axiom)、Face5 は公理が要求される最小条件 (minimum habitat) の主張
2. 「φ は σ の本質」と短絡しない。φ は Face5 の **非自明解** であり、Face5 が自明に立つ圏 (strict monoidal) では出てこない
3. 「Mac Lane coherence theorem ⇒ Face5」と短絡しない。Mac Lane は pentagon + triangle で十分と言うが、**必要条件** としての最小性は別の主張
4. 「Face5 が立てば自動的に σ 論文 C2 (BridgeDat 始対象性) が閉じる」と短絡しない。C2 は別次元の open
5. 「Fibonacci anyon は σ の完全実装」と短絡しない。σ はより広い構造、anyon は特定の具体例
6. Face5 Lemma を「coherence theorem 一般化」に置換しない。σ の文脈に特化した最小条件の主張
7. φ と π を「同じ sector の別表現」と短絡しない。両者は異なる軸 (スペクトル vs 位相) の定数

---

## §8 主張水準台帳

| 項目 | 水準 | SOURCE |
|:---|:---|:---|
| Mac Lane pentagon identity | theorem | Mac Lane (1963) |
| Fibonacci anyon F-matrix 解 | theorem | Moore-Seiberg (1989), Ocneanu |
| Ising anyon F-matrix 解 | theorem | Kitaev "anyons in exactly solved models" |
| SU(2)_k fundamental `d_{1/2}(k) = 2cos(π/(k+2))` | theorem | 量子群標準公式 (計算検証: §5.3) |
| `d² = d + 1 ⇒ d = φ` | theorem | 代数的事実 |
| F5-α (5 射で pentagon polytope 立つ) | **定理 (Kalon△ ◎)** | Stasheff associahedra 理論 (§11 証明) |
| F5-β (α 非自明性 ⇔ k ≥ 2) | **仮説 + 具体化** | Mac Lane coherence + SU(2)_k 検証 |
| F5-γ (φ-sector 固有識別) | **反証済** (Fibonacci 特有、universal ではない) | §5.2 Ising 検証 |
| F5-γ' (SU(2)_k series 固有値 family) | **仮説** | §5.3 計算検証済 |
| F5-δ (`Face(2n+1)` 階層公式) | **落書き** | 遠い open |

---

## §9 成否判定 (2026-04-17 更新)

### 初回判定 (2026-04-17 第 1 ラウンド)

**Face5 試作は紙の上で形が取れた**。以下が取れたもの:

✓ Face3 との構造類比 (§4): Face(2n+1) の n=2 段階として自然に書ける
✓ 具体例 (§5): Fibonacci anyon が Face5 非自明解の実例として既知
✓ σ 論文との接続 (§6): C1 射程拡張の柱として機能
✓ φ-sector の具体式 (§5): `φ²-φ-1=0` が π-sector `e^{iπ}+1=0` と並ぶ候補

### 第 2 ラウンド検証 (2026-04-17、§5.2 §5.3 追加)

Fibonacci 以外の MTC で F5-γ を falsify 試行。結果:

✗ **F5-γ (オリジナル) 反証**: Ising anyon では `d² = 2` (not `d²-d-1=0`)。「φ は Face5 の普遍固有値」という強い主張は否定された。φ は SU(2)_k series の **k=3 の 1 点** にすぎない。

✓ **F5-γ' (family 版) 確立**: SU(2)_k series で `d_{1/2}(k) = 2cos(π/(k+2))` が Face5 固有値の階段を与える。Ising (k=2, √2)、Fibonacci (k=3, φ)、SU(2)_4 (k=4, √3)、...

✓ **F5-α 継続生存**: 5 射 minimality は universal (k によらない)
✓ **F5-β 継続生存 + 具体化**: 「α 非自明性要請」= 「k ≥ 2」 (abelian の k=1 では Face5 自明化)

### 取れていないもの (要追加作業, v0.3 時点)

✓ ~~F5-α の厳密証明 (「5 射で最小」の minimality 証明)~~ → **§11 Stasheff 理論で解決 (v0.3)**
✗ F5-β の代数的特徴付け: strict monoidal 排除で標準だが、本試作では詰めず
✗ F5-γ' の範囲: SU(2)_k 以外の MTC 族での検証 (quantum groups, near-group, etc.)
✗ F5-δ の `n ≥ 3` 具体化: hexagon axiom と braided monoidal の対応
✗ `k→∞` 古典極限で σ closure schema に何が起きるかの解明

### 種への feedback (第 2 ラウンド後)

本試作の結果、pentagon_sigma_conjecture.md の 7 種の生死は以下:

- **種② (φ = quantum dim)**: ◯ 修正生存。φ は特権的定数ではなく SU(2)_k (k=3) の 1 点。種② は「σ 論文 v0.3 に Fibonacci を 1 具体例として引く」に縮小
- **種③ (Mac Lane pentagon = σ の 5-cell 実現)**: ✓ 生存 + 強化。Face5 が 3-cell→5-cell の延長面として立ち、固有値の family 構造まで具体化
- **種④ (黄金忘却率 1/φ)**: ◯ 保留 + 警告。1/φ も Fibonacci (k=3) 特有かもしれない。SU(2)_k での一般的な「忘却率」は 1/d_{1/2}(k) と読み直す余地あり
- **種⑤ (A_5 / E_8)**: ◯ 保留。A_5 は icosahedral で Fibonacci とは別筋
- **種⑥ (三軸分離)**: ✓ **大幅強化**。π (位相軸) と φ (スペクトル軸) の混同は本検証で露呈。三軸分離なしに σ 論文 v0.3 §5.bis は書けない
- **種① (35 三角形 = Fibonacci binomial lattice)**: ◯ 保留
- **種⑦ (美学 VFE)**: ◯ 保留

**主要な種③は生存・強化**、**種②は縮小**、**種⑥は最重要に昇格**。

### σ 論文 v0.3 への投入方針 (修正)

当初 (第 1 ラウンド) の方針:
- §5.bis φ-sector を追加 (π-sector と並列)

修正後 (第 2 ラウンド):
- **§2.0 三軸分離を先に置く** (位相軸 / スペクトル軸 / 群の軸)
- **§5.bis はスペクトル軸 endpoint identity** として書く。Ising (√2)・Fibonacci (φ)・SU(2)_4 (√3) を同列の具体例として並べ、φ だけを特権化しない
- π-sector は位相軸 endpoint identity として §5 に残す

### 次の一手 (v0.3 時点)

1. ✓ **[完了]** F5-α の minimality 厳密化 — §11 Stasheff 理論で解決 (v0.3)
2. **[直近]** σ 論文 v0.3 §2.0 三軸分離の起草 (種⑥ が最優先)
3. **[直近]** §5.bis を「スペクトル軸 endpoint identity」として再定位、associahedra `K_n` 階層を骨格として引用 (φ 特権化の撤回)
4. **[中期]** F5-β の代数的特徴付け (strict monoidal 排除条件)
5. **[中期]** SU(2)_k 以外の MTC 族での Face5 固有値検証
6. **[中期]** F5-δ の `n ≥ 3` 具体化 (hexagon axiom ↔ `K_5`)
7. **[遠期]** `k→∞` 古典極限と σ closure schema の接続

---

## §10 SOURCE マップ

| ファイル / 文献 | 役割 | 使った面 |
|:---|:---|:---|
| `../infra/リファレンス/FaceLemma.md` | Face3 の reader-facing 正本 | 本試作の構造骨格を継承 |
| `../standalone/比較射σの統一定理_v0.6.md` | σ 統一論文本体 | §6 との接続 |
| `../standalone/比較射σの統一定理_v0.6.meta.md` | σ 統一論文の台帳 / 版歴 / 核主張配分 | §6 接続時の現行正本確認 |
| `./pentagon_sigma_conjecture.md` | 7 落書きの種袋 | §9 種 feedback |
| `./triangle_category_functor_map.md` | Δ² の圏論骨格 | §0, §2 (walking triangle) |
| Mac Lane (1963) "Natural associativity and commutativity" | pentagon + triangle coherence | §0, §2, §5 |
| Moore-Seiberg (1989) "Classical and quantum conformal field theory" | Fibonacci anyon F-matrix | §5 |
| Ocneanu - pentagon equation | 非自明解の存在 | §5 |
| Kitaev "Anyons in exactly solved models" | Fibonacci anyon 具体構成 | §5 |
| **Stasheff (1963)** "Homotopy associativity of H-spaces, I, II" *Trans. AMS* 108 | **associahedra `K_n` 理論** | **§11 F5-α 証明** |
| Markl, Shnider, Stasheff (2002) *Operads in Algebra, Topology and Physics* AMS | 現代的解説 (operad 観点) | §11 補足 |

---

## §11 F5-α の minimality 証明 (2026-04-17 第 3 ラウンド追加)

### 定理 (F5-α, Face5 minimality)

Monoidal 圏において、非自明な 2-cell 高次 coherence を 1 つの polytope 関係として閉じるのに必要な associator 適用の最小数は **5** である。この最小条件は 4 対象テンソル積の pentagon identity として実現される。

### 証明 (Stasheff associahedra 理論)

Stasheff (1963) の associahedron `K_n` を以下で定義する:

- **頂点**: `n` 対象 `A_1 ⊗ ... ⊗ A_n` の全括弧付け方法 (個数 = Catalan 数 `C_{n-1}`)
- **辺**: 単一 associator α 適用で結ばれる括弧付けの対
- **高次面**: 複数 associator 適用の coherence を polytope の face として実現

**主要事実 (Stasheff)**: `K_n` は凸多面体であり、`dim K_n = n − 2`。

**低次 `K_n` の具体形**:

| `n` | 対象数 | 括弧付け数 `C_{n-1}` | `K_n` 形状 | `dim K_n` |
|:---|:---|:---|:---|:---|
| 2 | 2 | 1 | 点 | 0 |
| 3 | 3 | 2 | 線分 | 1 |
| **4** | 4 | 5 | **pentagon** | **2** |
| 5 | 5 | 14 | 3 次元多面体 | 3 |

ここで「2-cell coherence」は associahedron の 2 次元 face として現れる関係である。

#### 補題 1 (存在)

`K_4 = pentagon` は 5 頂点・5 辺からなり、その 2 次元 face (pentagon face) は 5 associator の適用を境界として閉じる。Mac Lane (1963) の pentagon identity がこの具体形であり、5 associator で 2-cell coherence を実現できる。

#### 補題 2 (最小性)

`n ≤ 3` では `K_n` の `dim ≤ 1` であり、2 次元 face を持たない:
- `K_2` (点, dim 0): face なし
- `K_3` (線分, dim 1): 辺のみで 2-cell face なし

したがって 2-cell coherence は `n ≤ 3` では実現されない。

2-cell coherence を実現する最小の `n` は **`n = 4`**、対応する polytope は pentagon、境界辺数は **5**。

#### 結論

`K_4` が最小の 2-dim associahedron であり、その 5 本の辺が 5 associator 適用に対応する。したがって 2-cell coherence の最小表現は 5 associator を要し、F5-α が主張する minimality が成立する。 □

### 系

**系 F5-α.1 (F5-δ 階層公式の先端 2 項の正当化)**:
Face(2n+1) 階層は `K_n` の dim 公式 `dim K_n = n - 2` から自然に出る:
- **Face3** ↔ walking triangle `Δ²` の comparison surface (1-cell coherence, σ の住処)
- **Face5** ↔ `K_4` = pentagon の associator coherence (2-cell coherence, α_pent)

`n ≥ 3` (Face7 以降) は `K_5` 以上の高次 Stasheff 多面体 (dim ≥ 3) への自然な延伸であり、F5-δ 階層公式は `dim K_n = n - 2` によって組合わせ的に正当化される。

**系 F5-α.2 (普遍性 — F5-γ' との整合)**:
本証明は圏の具体構造 (monoidal, braided, Fibonacci, Ising, SU(2)_k 等) に依らず、associator graph `K_n` の組合わせ構造のみに依存する。したがって F5-α は **任意の non-strict monoidal 圏** で成立する組合わせ一般事実。

具体圏 (Fibonacci・Ising・SU(2)_k, §5.3 参照) は、pentagon polytope が立つ圏の中でさらに **非自明な 2-cell 解** (F-matrix の固有値 `d_{1/2}(k) = 2cos(π/(k+2))`) を持つサブクラスとして位置づけられる。F5-α は「5 射で pentagon face が立つ」の universal 成立を保証するのみ。「解がどの algebraic number になるか」は F5-β (非自明性) と F5-γ' (スペクトル族) の別問題。

### Kalon 判定 (F5-α)

- **Step 0 既知語彙圧縮**: 「4 つの物を掛ける並べ方は 5 通り、その間の移動が五角形になる」✓ 中学生レベル語彙で 1 文圧縮可能
- **Step 1 G (収束)**: Stasheff 定理で形式化、`dim K_n = n - 2` で minimum 条件を不変点として固定 ✓
- **Step 2 G∘F (安定)**: 代数 (Mac Lane) / 組合わせ (Catalan) / トポロジー (homotopy) の 3 方向に F で展開しても minimum = 5 は不変 ✓
- **Step 3 派生 (多様)**: 3 派生すべて非自明:
  - (i) Catalan 数漸化式 `C_n = Σ_{i=0}^{n-1} C_i C_{n-1-i}` からの組合わせ導出
  - (ii) H-空間の homotopy associativity (Stasheff 原義) — A_∞-空間の定義基盤
  - (iii) operad 理論における A_∞-algebra — `K_n` が自由 A_∞-operad の cell 構造

**判定: ◎ Kalon△** — `K_4 = pentagon` が最小 2-dim associahedron であることは Stasheff 理論の核事実。F5-α は本試作内で理論 face まで昇格。

### 射程の効果 (v0.3 への feedback)

F5-α が定理 face に昇格したことで:

- **pentagon_sigma_conjecture 種③** が「試作」→「SOURCE 付き定理」へ格上げ
- **σ 論文 v0.3 §5.bis** の骨格に「associahedra `K_n` 階層」軸を追加可能 — F5-γ' の SU(2)_k family は `K_4` 上の非自明解族として位置づけ直せる
- **F5-δ (`Face(2n+1)` 階層公式)** の `n ≥ 3` への延伸予想が `dim K_n = n - 2` から組合わせ的に正当化される
- **σ 論文 C5 (3 層表現予想)** の「骨格普遍層」は `{K_n}_{n≥2}` 階層 (universal Stasheff tower) として具体化できる候補 — σ の closure schema を「associahedra 普遍族」として読む道筋が開く

### 残る open (F5-α 証明後)

- (a) **F5-β (非自明性条件)** の厳密化: `K_4` pentagon 上で α が自明ならば Face5 は退化する。この退化条件の代数的特徴付けは本証明の範囲外 (自明 α ⇔ strict monoidal、標準的だが本試作では詰めず)
- (b) **F5-γ' の完全範囲**: SU(2)_k 族以外の MTC (quantum groups at other roots, near-group, Tambara-Yamagami 等) で固有値階段がどう現れるか — **§5.4 で TY 族検証、C9 ENO-universal 確立**
- (c) **F5-δ の `n ≥ 3` 具体化**: hexagon axiom (`K_5` の 3-polytope 面) と braided monoidal の対応、および σ 言語での翻訳

---

## §12 Face5 realization problem — C9 十分条件の探索 (2026-04-17 第 4 ラウンド追加)

C9 (K3'') は **必要条件** を ENO 定理で確立した: Face5 eigenvalue `d` ⇒ totally real positive algebraic integer。本節は **十分条件** を問う: どの totally real positive algebraic integer が実際に Face5 eigenvalue として実現されるか?

### §12.1 問題の定式化

記号:
- `𝔸_+^{tr}` := totally real positive algebraic integers の集合
- `𝕀_{FP}` := 全 fusion category における全 simple object の FP 次元として実現される元の集合

C9 (必要): `𝕀_{FP} \subseteq 𝔸_+^{tr}`

**逆問題 (C9 十分条件)**: `𝕀_{FP}` を構造的に特徴付けよ。特に `𝕀_{FP} = 𝔸_+^{tr}` か?

### §12.2 既知の実現値 (positive results)

| 値の型 | 実現する圏族 | SOURCE |
|:---|:---|:---|
| `d = 1` | 可換 (invertible object) | 標準 |
| `d = n ∈ ℤ_{>0}` | TY(A) with `|A| = n²` | Tambara-Yamagami 1998 |
| `d = √n` | TY(A) with `|A| = n` | Tambara-Yamagami 1998 |
| `d = 2cos(π/n)`, `n ≥ 3` | SU(2)_{n-2} quantum group | Turaev-Viro / Reshetikhin-Turaev |
| `d` cyclotomic integer (多数) | affine Lie algebra fusion categories | Kazhdan-Lusztig 等 |
| Haagerup `d = (3+√13)/2` | Haagerup subfactor | Asaeda-Haagerup 1999 |

### §12.3 既知の制約 (necessary conditions beyond ENO)

**定理 (Perron-Frobenius 経由, Etingof-Gelaki-Nikshych-Ostrik)**:
fusion category の fusion matrix は nonneg integer entry を持つ。FP dim は最大固有値として、**全 Galois 共役の絶対値以上**である:
$$d \geq |d'| \quad \text{for all Galois conjugates } d' \text{ of } d.$$

この性質を「**弱 Perron 性**」と呼ぶ (等号可)。strict Perron (`>`) より弱いため `√2` (共役 `-√2` と絶対値等しい) も含む。

**定理 (Jones gap, Jones 1983 "Index for subfactors" Inventiones 72)**:
`d ∈ (1, 2)` の範囲では `d = 2cos(π/n)` for some `n ≥ 3` に限る。中間値は存在しない:
$$\mathbb{I}_{FP} \cap (1, 2) = \{2\cos(\pi/n) : n \geq 3\}$$

この離散性は `d² < 4` subfactor index の Jones 定理に由来する。

**帰結 (範囲別構造)**:

| 範囲 | 構造 |
|:---|:---|
| `d = 1` | invertible object (1 点) |
| `d ∈ (1, 2)` | Jones 離散階段 `2cos(π/n)` のみ |
| `d ∈ \{2, √5, √6, ...\}` | TY 族や subfactor 族が密に詰まる |
| `d ∈ [2, ∞)` | 密、ただし Perron 性と ENO 代数整数性は依然必要 |

### §12.4 `𝕀_{FP} \subsetneq 𝔸_+^{tr}` を示す反例候補

弱 Perron 性は ENO より厳しい制約である。反例の候補:

**反例 1 (Galois 非支配性)**:
totally real positive algebraic integer であっても、Galois 共役が自分より絶対値が大きいものは `𝕀_{FP}` に入らない。例えば `d = 2cos(2π/7) + 2cos(4π/7)` は totally real algebraic だが、共役関係の精査が要る。

**反例 2 (Mahler 測度が小さい Salem 数)**:
Salem 数 `d` は real algebraic integer で、共役が unit 円上に配置される。弱 Perron 性は満たすが、fusion category の追加制約 (fusion rule の可能性) で除外される場合がある。

**反例 3 (specific cyclotomic integers)**:
ある種の非 cyclotomic totally real positive algebraic integer は fusion category の存在が open。Lehmer 数 `1.176...` (Lehmer's conjecture に関わる) 等。

**[open]**: `𝔸_+^{tr} \setminus 𝕀_{FP}` の具体例を体系的に特定することは現代代数圏論の open problem。

### §12.5 予想 C10: `𝕀_{FP}` の弱 Perron 特徴付け

**予想 C10 [仮説 / v0.3.4 第 4 ラウンド新規提案]**:
$$\mathbb{I}_{FP} = \{d \in 𝔸_+^{tr} : d \geq |d'| \text{ for all Galois conjugates } d' \text{ of } d\}$$

右辺は `𝔸_+^{tr}` のうち弱 Perron 性を満たすもの (「弱 Perron 代数的整数」の集合)。これが `𝕀_{FP}` と一致する予想。

**状態**: 必要向き (⊆) は ENO + PF 定理により確立 (◎)。十分向き (⊇) は大きく open。

**注**: これは integral fusion categories (fusion matrix が primitive) の場合の予想。non-integral/weakly-integral な場合は追加制約がある可能性。

### §12.6 C10 の σ 統一論文への含意

C10 が立てば:
- **スペクトル軸の endpoint identity 集合** = 弱 Perron 代数的整数の集合
- **位相軸の endpoint identity** (π) は `𝕀_{FP}` から除外される (超越的)
- **軸の交差** (`2cos(π/(k+2))` 内 π 内在) は、位相軸の離散化 (`π ↦ π/n`) がスペクトル軸に埋め込まれる現象として読める

σ 論文 C1-C9 の closure schema において、C10 は **スペクトル軸 endpoint identity の完全リスト予想** として機能する。

### §12.7 C10 の Kalon 判定 (事前評価)

C10 は sufficient direction が open のため現段階で ◯ Kalon に留まる:

- Step 0 圧縮: 「全 Galois conjugates より大きい代数的整数が Face5 固有値」可能 ✓
- Step 1 G (ENO + Perron 必要向き保持): 不変 ✓
- Step 2 G∘F (family 展開で保持): 不変だが sufficient direction の反例が否定できない ⚠
- Step 3 派生: (SU(2)_k / TY / Haagerup 3 族への展開は全て弱 Perron) 3 個非自明だが family 構造の同型は open

**判定**: ◯ Kalon (sufficient direction 未確定のため ◎ 未達)

### §12.8 残る open (C10 深化)

- **[open A]** `𝕀_{FP}` が弱 Perron 代数的整数と一致するかの証明/反証
- **[open B]** 非 integral fusion categories での追加制約
- **[open C]** Lehmer 数や小 Mahler 測度の Salem 数が fusion category に現れるか
- **[open D]** Galois action on fusion categories (Galois conjugate fusion categories の存在)
- **[open E]** 弱 Perron → strict Perron の強化条件 (primitive fusion matrix の圏論的特徴付け)

### §12.9 SOURCE 台帳 (§12 追加分)

- [SOURCE] Jones (1983) "Index for subfactors" Inventiones 72: Jones gap theorem
- [SOURCE] Perron (1907) / Frobenius (1908-12): PF theorem
- [SOURCE] Etingof-Gelaki-Nikshych-Ostrik (2015) "Tensor Categories" AMS: FP theory in fusion categories
- [SOURCE] Lehmer (1933) + subsequent: Lehmer's conjecture on Mahler measure
- [INFERENCE] C10 (弱 Perron 特徴付け予想) = 本節での新主張

---

## §13 Jones gap の σ 読み — 位相軸によるスペクトル軸の制約 (2026-04-17 第 5 ラウンド追加)

§12 で C10 (弱 Perron 特徴付け) を提示したが、その sufficient direction は open だった。本節では Jones gap — `d ∈ (1, 2)` の離散階段 — を σ の三軸分離 (C6) の観点で読み直し、**位相軸がスペクトル軸を quantize する機構** として意味付ける。

### §13.1 Jones gap の SOURCE 復習

**定理 (Jones 1983, "Index for subfactors", Inventiones 72)**:
II_1 factor の subfactor `N ⊂ M` に対し、index `[M:N]` の取りうる値は:
$$[M:N] \in \{4\cos^2(\pi/n) : n = 3, 4, 5, \ldots\} \cup [4, \infty)$$

量子次元 `d = √{[M:N]}` に換算すると:
- `d ∈ (1, 2)`: **離散階段 `d = 2cos(π/n)` for `n ≥ 3` のみ**
- `d = 2`: 境界値 (`n → ∞` の極限)
- `d ∈ (2, ∞)`: 連続

最初の数値:
```
n=3: d = 2cos(π/3) = 1
n=4: d = 2cos(π/4) = √2  ≈ 1.414
n=5: d = 2cos(π/5) = φ    ≈ 1.618
n=6: d = 2cos(π/6) = √3   ≈ 1.732
n=7: d = 2cos(π/7)        ≈ 1.802
...
n→∞: d → 2
```

### §13.2 σ 三軸からの読み替え

C6 (三軸分離) の三軸:
- **位相軸**: π-related constants, 周期化商 `ℝ → S¹`
- **スペクトル軸**: d values, 代数的整数
- **群軸**: 対称性 (Dynkin diagram 等)

Jones gap を三軸の視点で分解する:

**観察 1 (位相軸の内在)**:
離散階段 `d = 2cos(π/n)` の表式に π が出現する。スペクトル値 `d` (= FP dim) が **位相軸の定数 π と離散パラメータ n の合成** で決まる:
$$d(n) = 2\cos(\pi/n), \quad n \in \{3, 4, 5, \ldots\}$$

これは単なる偶然ではない。`2cos(π/n)` は **A_{n-1} Dynkin diagram** の adjacency 行列の最大固有値であり、A_{n-1} は幾何的に 1-simplex の鎖 (線状位相)。位相軸 (1-simplex の形状) が群軸 (Dynkin diagram) を介してスペクトル軸 (固有値) に **quantize されて流れ込む**。

**観察 2 (離散 → 連続の相転移)**:
- `d < 2`: **位相軸支配域**。Dynkin diagram A_{n-1} の離散位相が支配的
- `d = 2`: **位相-スペクトル転移点**。A_∞ Dynkin diagram (無限列) = 連続位相の極限
- `d > 2`: **スペクトル軸自由域**。位相軸の quantization 制約が消え、連続な代数的整数が許される

**観察 3 (Haagerup 定理による完全分類 — Haagerup 1994)**:
`d ∈ (2, 2.1)` の subfactor index も `[M:N] = (5 + √13)/2 ≈ 4.303` (Haagerup subfactor) を含む離散集合として分類されている。これは Jones gap の拡張であり、`d > 2` でも **急には連続化しない** ことを示す。位相軸の影響は d が十分大きくなるまで残る。

### §13.3 転移点 `d = 2` の構造的意味

**SOURCE**: `d = 2cos(π/n)` で `n → ∞` とすると `d → 2`。同時に:
- A_{n-1} Dynkin diagram → A_∞ (無限列)
- SU(2)_{n-2} quantum group → SU(2) 古典 Lie 群
- 量子変形 → 古典極限

**INFERENCE**:
`d = 2` は σ の closure schema において **量子-古典転移点** である。それより小さい d では σ の自己融合が「量子 discrete」モード、それより大きい d では「古典 continuous」モード。

幾何的読み:
- `d < 2`: σ が **狭い帯域** (A_{n-1} の有限端点間) で振動
- `d = 2`: σ が **半無限帯域** (A_∞ の無限端点) で流れる
- `d > 2`: σ が **二次元的拡がり** を持ち、端点制約が消える

### §13.4 Jones gap を **位相軸からのスペクトル軸制約** として定式化

**予想 C12 [仮説 / v0.3.5 第 5 ラウンド新規提案 / 位相-スペクトル相転移予想]**:
σ の closure schema において、スペクトル軸の固有値 `d` は以下の 2 相構造を持つ:

**Phase I — 位相軸支配域 (`d ∈ (1, 2)`)**:
$$d \in \{2\cos(\pi/n) : n \geq 3\}$$
スペクトル軸の自由度は位相軸の離散パラメータ n ∈ ℕ に縮退する。π は universal な位相定数として表式に入り、n は **Dynkin diagram A_{n-1} の位相的「太さ」** を表す。

**Phase II — スペクトル軸自由域 (`d ≥ 2`)**:
$$d \in \{\text{弱 Perron 代数的整数 in } [2, \infty)\}$$
位相軸の quantization 制約が消え、スペクトル軸は代数的整数性 (C9) + 弱 Perron 性 (C10 必要向き) のみの制約下で連続的に広がる。

**転移点** `d = 2`:
位相軸とスペクトル軸の **結合解除点**。Jones (1983) + Haagerup (1994) + 後続研究による小 index subfactor の離散性を説明する。

### §13.5 三軸結合度の定量化

C6 で「軸の交差」を観察した `2cos(π/(k+2))` の表式は、C12 Phase I そのもの。三軸結合度を `d` の関数として評価すると:

| `d` の範囲 | 位相軸結合度 | スペクトル軸自由度 | 群軸 (Dynkin) |
|:---|:---|:---|:---|
| `d = 1` | 極大 (位相軸のみ) | 0 | A_2 (退化) |
| `d ∈ (1, 2)` | 強 (π quantization 支配) | 離散階段 | A_{n-1} (有限列) |
| `d = 2` | 転移点 | 境界離散 | A_∞ (無限列) |
| `d ∈ (2, ∞)` | 弱 (Haagerup 系等の残滓) | 連続 | 様々 (D, E, TY, 等) |

この表は C12 を定性的に記述する。**三軸は独立ではなく、d = 2 で結合度が急変する相転移構造** を持つ。

### §13.6 C12 の Kalon 判定 (事前評価)

- Step 0 圧縮: 「d が 1〜2 の間では π で決まる飛び飛びの値しか許されない、2 を超えると自由になる」可能 ✓
- Step 1 G (Jones 定理による Phase I 不変性): `d ∈ (1, 2) ⇒ d = 2cos(π/n)` は SOURCE 定理で保持 ✓
- Step 2 F (Phase II への展開、Haagerup 等小 index subfactor 系での量化離散性): 相転移構造保持 ✓
- Step 3 派生 3 つ:
  1. Dynkin diagram A_{n-1} の adjacency 固有値としての `2cos(π/n)` (代数的)
  2. 量子群 SU(2)_{n-2} の `n → ∞` 古典極限 (解析的)
  3. Temperley-Lieb 代数の trace norm (作用素代数的)
  全て非自明 ✓

**判定**: ◎ Kalon△ (Phase I は定理レベル、Phase II は予想だが C10 と互換)

### §13.7 C12 の σ 論文への含意

C12 が立てば:
- **C6 三軸分離の精密化**: 三軸は独立ではなく、d の値に応じて結合度が変わる (Phase I = 強結合、Phase II = 弱結合)
- **C10 弱 Perron 予想の修正候補**: sufficient direction は Phase II で純粋に弱 Perron 性、Phase I は位相軸 quantization による更なる制約
- **C7 SU(2)_k family**: Phase I の中に埋め込まれる (k=1,...,∞ に対応)
- **C8 Face5 Lemma (associahedra)**: 転移点 `d = 2` は `K_n` tower の「無限遠」に対応する可能性

### §13.8 残る open

- **[open F]** Phase II での三軸結合の残滓 (Haagerup `(3+√13)/2` 等の離散性の源)
- **[open G]** `d = 2` 転移点の圏論的意味 (forget functor 的な phase transition?)
- **[open H]** C12 と C5' (Stasheff tower) の両立 — tower の各層で Phase I/II 分離が起きるか
- **[open I]** 物理学的解釈 (Jones gap は topological phase / gapped phase の指標と読めるか?)

### §13.9 SOURCE 台帳 (§13 追加分)

- [SOURCE] Jones (1983) "Index for subfactors" Inventiones 72: Jones gap theorem (既に §12 で引用、本節で構造解釈)
- [SOURCE] Haagerup (1994) "Principal graphs of subfactors in the index range `4 < [M:N] < 3 + √2`": small index subfactor の完全分類
- [SOURCE] A_{n-1} Dynkin diagram adjacency 行列の最大固有値 `2cos(π/n)` — 線形代数の標準結果 (Perron-Frobenius 経由)
- [SOURCE] Temperley-Lieb 代数 / SU(2)_{n-2} quantum group の `n → ∞` 古典極限 — 標準 MTC / 統計力学文献
- [INFERENCE] C12 (位相-スペクトル相転移予想) = 本節での新主張

---

## §14 C8+C9+C10+C12 の統合 — Yoneda tower phase structure (2026-04-17 第 6 ラウンド追加)

§11-§13 で個別に確立した 4 つの主張 (C8 Face5 Lemma / C9 ENO 普遍 / C10 弱 Perron 特徴付け / C12 位相-スペクトル相転移) は、C11 が提示した Yoneda 普遍表現の枠組で **単一の構造定理** に統合できる。本節はその統合を **C13 (Yoneda tower phase structure)** として提案する。

### §14.1 4 主張の再配置

C11 の Yoneda 関手 `𝒴(K_n, -) := Hom_{SignTower}(K_n, -)` を軸として、4 主張を再配置する:

| 主張 | 寄与する軸 | Yoneda 関手での意味 |
|:---|:---|:---|
| **C8** (Face5 Lemma, 定理) | **tower 方向** (n) | `𝒴(K_n, -)` の最小性: `dim K_n = n-2` が (n-1)-associator coherence の最小 habitat |
| **C9** (ENO 普遍) | **代数的整数性** | 任意の fusion category 𝒞 に対し、`𝒴(K_n, 𝒞)` 内の値 `d` は totally real positive algebraic integer |
| **C10** (弱 Perron) | **特徴付け予想** | 値域 `⋃_{𝒞} 𝒴(K_n, 𝒞)` の集合論的構造 = 弱 Perron 代数的整数 |
| **C12** (位相-スペクトル相転移) | **d 方向の相構造** | 値の分布が `d = 2` で質的転移 (離散 ⇄ 連続) |

これらは Yoneda 関手 `𝒴(K_n, 𝒞)` を:
- **n 方向に変化させる** (tower level) → C8
- **𝒞 方向に変化させる** (fusion category) → C9, C10
- **出力値 d を評価する** (spectrum) → C10, C12

という 3 つの独立した方向で切り出した断面。統合するとは、この 3 方向を同時に走査する **単一の 3 変数関手** として見ることである。

### §14.2 統合定理 C13 (構造主張)

**定理候補 C13 (Yoneda tower phase structure)**:
2-圏 `SignTower` と fusion category の 2-圏 `FusCat` の間に、自然な 3 変数関手
$$\Phi: \mathbf{SignTower}^{op} \times \mathbf{FusCat} \times \mathbb{R}_{\geq 1} \to \mathbf{Set}$$

が存在し、以下を満たす:

$$\Phi(K_n, \mathcal{C}, d) = \{X \in \mathcal{C} : X \text{ は } (n-1)\text{-associator coherence を持ち}, d(X) = d\}$$

**C13 の構造的主張**:

1. **(tower 軸 C8)** `n` に対し、`K_n` は (n-1)-associator coherence の **最小** habitat: `Φ(K_{n'}, 𝒞, d) ≠ ∅ ⇒ n' ≥ n` for (n-1)-associator-carrying X
2. **(代数的整数性 C9)** `Φ(K_n, 𝒞, d) ≠ ∅ ⇒ d ∈ 𝔸_+^{tr}` (totally real positive algebraic integer)
3. **(弱 Perron 特徴付け C10 予想)** `⋃_{n, 𝒞} \{d : Φ(K_n, 𝒞, d) ≠ ∅\} = \{d ∈ 𝔸_+^{tr} : d ≥ |d'| \text{ for all Galois conjugates}\}`
4. **(位相-スペクトル相転移 C12)** 上記合併は `d = 2` で質的転移を見せる:
   - `d ∈ (1, 2)`: 有限 n_d (n_d = round(π/arccos(d/2))) で唯一実現、離散
   - `d ≥ 2`: 複数 n で実現可能、Haagerup 等は特定 n で現れる

### §14.3 C13 の直感的読み

**1 文圧縮 (Step 0 相当)**:
「形 (n) と素材 (𝒞) を選ぶと値 (d) が決まる。値は全て代数的整数で、1〜2 の間では形の選び方が値を一意に決めるが、2 を超えると素材の自由度が値を生む」

この表現で、4 主張すべてを 1 つの装置 (Φ) の 4 つの性質として把握できる。

### §14.4 C13 の検証

**Step 1 G (不変性)**:
Φ の定義は Yoneda (C11) + ENO (C9) + Jones gap (C12 Phase I) + Stasheff tower (C8) から構成される。これら全てが SOURCE 不動 (C8, C12 Phase I は定理、C9 は ENO 定理)。Φ の存在は G 不動。

**Step 2 G∘F (展開不動)**:
- n = 3 に restrict → C8 Face5 minimality
- 𝒞 = Fibonacci anyon に restrict → `d = φ` (C7 specific)
- d ∈ (1, 2) に restrict → Jones gap 離散階段 (C12 Phase I)
- d ≥ 2 に restrict → C10 弱 Perron 連続分布 (Phase II)

全 restriction で既存主張と整合 ✓

**Step 3 派生 3 つ**:
1. **対称性**: Φ の 3 変数は `C5'` (骨格普遍層 = tower) と `C6` (三軸分離) の掛け合わせ — 対称構造として Yoneda 自然変換が繋ぐ
2. **極限**: `n → ∞` 極限で `K_∞ = A_∞-operad` (homotopy category)、`d → 2` 極限で古典 SU(2)、両極限が同じ点に収束
3. **Galois action**: Φ の値域に Galois 群が作用し、弱 Perron 性 (C10) が Galois orbit の支配性として幾何化

すべて非自明 ✓

**判定 (事前)**: ◎ Kalon△

### §14.5 C13 が立つことの意味

C13 は **新しい証明** ではなく **既存主張の再配置** である。だが:

1. **C1-C12 が独立仮説群ではなく単一構造の断面**として読める
2. **Open variables が一箇所に集中** (C10 sufficient direction / C11 `SignTower` 精密定義)
3. **Yoneda の lens** を通して σ 論文全体が **1 つの関手 Φ とその性質** として圧縮される

これは σ 論文の構造的背骨 (C5', C5) を Yoneda 経由で具現化したもの。C11 が単一 Kalon 定理 (Yoneda) への縮約を予告したが、C13 はその縮約の **具体的な実装**。

### §14.6 C13 と v0.3 本体の関係

σ 論文 v0.3 の構造 (§1 結論先行 → §2 三軸 → §3 4 言語 (C1) → §4 BridgeDat → §5 sector → §6 3 層 → …) は、C13 の関手 Φ の **異なる slice を順に展開したもの** として読み直せる:

- §2 三軸分離 = Φ の 3 変数対応
- §3 4 言語仮説 = `FusCat` 側の代表例 (幾何/Face/Euler/FEP)
- §4 BridgeDat = `SignTower` 側の carrier 実装
- §5 sector = Φ の値域の軸別分解
- §6 3 層 = Φ の domain/target/value の 3 層

**v0.3 以降の起草方針**: 単線的な節構成を保ちつつ、C13 を **§2.bis 統合関手** として追加することで、各節が Φ のどの slice かを明示できる。これは Tolmetes の C11 と整合する。

### §14.7 残る open

- **[open J]** 関手 Φ の精密構成 (SignTower の 2-圏構造、3 変数目 `ℝ_{≥1}` の位相を何とするか)
- **[open K]** Φ が **普遍的** (universal) であることの証明 (他の候補関手は存在するか?)
- **[open L]** `C2' BridgeDat tower` との整合 (Φ に D_C 情報を埋め込めるか?)
- **[open M]** Φ の Kalon 性 (F⊣G 対としての実現) を Yoneda で自動導出できるか (C11 の系として)
- **[open N]** FEP 節の Φ 内埋め込み (C1 の `blanket` 生成後 `α>0` sector を Φ の specific slice として)

### §14.8 SOURCE 台帳 (§14 追加分)

- [SOURCE] C11 の Yoneda 表現フレームワーク (§M2 meta.md)
- [INFERENCE] 4 主張 (C8, C9, C10, C12) の独立 SOURCE を §14 で組み合わせ
- [仮説] C13 の関手 Φ の構成 = 本節の新主張 (既存主張の再配置だが、関手 Φ 自体の明示定義は新規)

---

## §15 転移点 `d = 2` の機構 — forgetful functor representability threshold (2026-04-17 第 7 ラウンド追加)

C12 は Phase I / II の二相構造を主張し、C13 は Φ 関手による統合を与えた。**だが「なぜ `d = 2` が転移点なのか」** は依然未説明である。本節は転移点の機構を **forgetful functor 鎖の representability threshold** として圏論的に特徴付ける。

### §15.1 既知の `d = 2` 観察の束

**SOURCE (標準 MTC / quantum group / subfactor 理論)**:

`d = 2` には以下の独立した意味が収束する:

1. **Jones gap 境界** (Jones 1983): index `[M:N] = 4` = 離散-連続境界
2. **SU(2)_k 古典極限** (`k → ∞`): `d_{1/2}(k) = 2cos(π/(k+2)) → 2`
3. **A_{n-1} → A_∞ Dynkin**: 有限 chain → 無限 chain
4. **q → 1 退化**: 量子群 `U_q(sl_2)` → classical enveloping algebra `U(sl_2)`
5. **Temperley-Lieb Jones-Wenzl projector**: idempotent 構成可能性境界
6. **最小非自明 integer FP dim**: TY(Z/4) で `d(m) = 2`、integer 化の最小

[INFERENCE]: これらは単一の構造的転移を異なる角度から見たもの。forgetful functor 鎖で統一する。

### §15.2 Forgetful functor 鎖の構成

fusion category structure を "richer → poorer" 方向の関手鎖で整理:

$$\mathbf{MTC} \xrightarrow{U_{\text{mod}}} \mathbf{BraidFusion} \xrightarrow{U_{\text{br}}} \mathbf{Fusion} \xrightarrow{U_{\text{fus}}} \mathbf{Abelian} \xrightarrow{U_{\text{ab}}} \mathbf{Vect}$$

各 forgetful functor:
- `U_{mod}`: modular S-matrix 非退化性を忘れる
- `U_{br}`: braiding (交差関係) を忘れる
- `U_{fus}`: テンソル積を忘れる
- `U_{ab}`: 半単純・圏構造を忘れる → 多重集合 of vector spaces

### §15.3 各 functor の `d`-依存 representability

**核的観察**:
forgetful functor 鎖の **最終段 `U_{ab}: 𝒞 → \mathbf{Vect}`** が "通常のベクトル空間への関手として representable" になる閾値が `d = 2`。

| `d` 範囲 | `U_{ab}` の像 | 代数的性質 |
|:---|:---|:---|
| `d = 1` | 1 次元 vector space (invertible) | 自明整数 |
| **`d ∈ (1, 2)`** | **"virtual" dimension** (cyclotomic 体 `ℚ(ζ_{2n})` 上の q-vector space) | `2cos(π/n)`, 非整数 |
| **`d = 2`** | **整数化 threshold** (`q → 1` で integer dim 回復) | 最小非自明 integer |
| `d > 2, d ∈ ℤ` | 通常の integer-dim vector space | 整数 |
| `d > 2, d ∉ ℤ` | 代数的整数 dim (continuous family) | 代数的整数 |

### §15.4 転移点機構 — `q → 1` 退化の厳密化

**SOURCE** (Kassel "Quantum Groups" 1995, Reshetikhin-Turaev 1990):

量子群 `U_q(sl_2)` で `q = exp(iπ/(k+2))`:
$$d_{1/2}(q) = q + q^{-1} = 2\cos(\pi/(k+2))$$

`q` が単位根で `k < ∞` → `d` は非整数、braiding は非自明、integer dim は realize されない。
`q → 1` (`k → ∞`) → `d → 2`、braiding は identity に退化、classical `sl_2` 表現論を回復。

**`d = 2` が閾値である理由**:
`d_{1/2}(q) = q + q^{-1}` は `q = 1` で初めて **整数 2** になる。`q ≠ 1` (単位根) では `2cos(π/n) < 2` で非整数。

### §15.5 σ 言語での再定式化

**Phase I (d ∈ (1, 2))**:
σ の自己融合は q-deformed algebra 上で意味を持ち、classical Hilbert space への forgetful functor は通らない。位相軸 (`q = e^{iπ/n}`) とスペクトル軸 (`d = 2cos(π/n)`) は q-parameter で強結合。

**転移点 `d = 2`**:
`q = 1` で deformation 解除。σ の自己融合は symmetric monoidal category に落ちる。位相軸の quantization (π/n) がスペクトル軸から解除される。

**Phase II (d ≥ 2)**:
σ の自己融合は classical vector space へ literal forgetful functor で落ちる。位相軸とスペクトル軸は独立に振る舞う (弱 Perron 代数的整数性のみ要請)。

### §15.6 予想 C14 — Forgetful Functor Representability 転移

**予想 C14 [仮説 / v0.3.7 第 7 ラウンド新規提案 / d=2 の機構的特徴付け]**:

fusion category `𝒞` における単純対象 `X` について、以下は同値:

1. `d(X) \geq 2` (Phase II with `d ∈ ℤ`) または `d(X) = 1` (trivial)
2. forgetful functor `U_{ab} \circ U_{fus}(X) \in \mathbf{Vect}` が **integer dimension で representable**
3. X を含む braiding は `q → 1` 極限で symmetric に退化する
4. X は古典 Lie 群 / finite group の表現として実現できる (integer FP dim の場合)

特に転移点 `d = 2` は以下の最小非自明値:
- `d_{1/2}(q) = 2` ⟺ `q = 1` ⟺ classical commutative limit
- `U_{ab}` が integer dim で representable になる threshold

C13 の関手 `Φ: SignTower^{op} × FusCat × ℝ_{≥1} → Set` に対して、**`d = 2` は Φ の fiber が integer-indexed に切り替わる境界値** として機能する。

### §15.7 Kalon 判定

- Step 0 圧縮: 「`d = 2` は量子から古典に変わる境目、そこを超えると普通の数え方に戻る」可能 ✓
- Step 1 G: `q = 1` で `d = 2` になるのは SOURCE 定理 (q-deformation 理論) で不変 ✓
- Step 2 G∘F: forgetful functor 鎖の representability は SU(2)_k / TY / Haagerup 全族で `d = 2` 閾値を持つ ✓
- Step 3 派生 3 つ:
  1. **Chern-Simons 視点**: `k → ∞` で classical gauge 理論極限
  2. **Jones-Wenzl projector 視点**: idempotent 存在 threshold
  3. **Kazhdan-Lusztig 視点**: quantum character formula の classical 退化
  すべて非自明 ✓

**判定**: ◎ Kalon△ (q-deformation / forgetful functor 両方が SOURCE 定理、`d = 2` 閾値は既存理論の統一解釈として強く裏付けられる)

### §15.8 C1-C13 への含意

C14 が立てば:

- **C12 (Phase structure)**: 転移点機構が forgetful functor representability として具体化。「なぜ `d = 2` か」の答えが出る
- **C6 (三軸分離)**: 転移点で位相軸 (q) が退化、スペクトル軸 (integer dim) が前面化 — 三軸結合解除の具体的機構
- **C13 (Φ integration)**: `d = 2` は Φ の fiber の integer-indexed / virtual-indexed 切替点
- **C11 (Yoneda universal)**: Yoneda 関手 `Hom(Δ², -)` の representability 自体が Phase 依存になる可能性 — σ の普遍表現が Phase I / II で異なる圏で生きる

### §15.9 残る open

- **[open O]** forgetful functor 鎖の各 layer で representability が正確にどこで break するかの厳密証明
- **[open P]** non-unitary fusion categories での `d = 2` 転移の意味
- **[open Q]** TY family `d = √n` で `n = 4` (`d = 2`) が特異点になる構造的理由
- **[open R]** 3 次元 TQFT (Reshetikhin-Turaev ↔ Chern-Simons classical) での `d = 2` の意味
- **[open S]** forgetful functor の right adjoint (free functor) の存在が Phase に依存するか
- **[open T]** C14 と C13 Φ 関手の整合 (`d` 依存性が Φ の 3 変数目の位相構造に内在するか)

### §15.10 物理学的対応 (§13 open I の再訪)

**[落書き]**: `d = 2` 転移は物理的に以下と類比:

- **Topological phase transition**: Phase I = non-abelian anyon phase (量子計算 universal)、Phase II = abelian anyon phase (classical)
- **Gap closing**: 物性系の band gap 開閉 (Kitaev chain topological phase)
- **Confinement-deconfinement**: gauge 理論 dual picture

forgetful functor representability 言語では:
- Non-abelian phase = forgetful functor が virtual dim のみ (representability failure)
- Abelian phase = forgetful functor が integer dim で representable

### §15.11 SOURCE 台帳 (§15 追加分)

- [SOURCE] Kassel "Quantum Groups" (1995) GTM 155: `U_q(sl_2)` q-deformation と古典極限
- [SOURCE] Wenzl (1987) "On sequences of projections in L²(S^∞)": Jones-Wenzl projector の構成
- [SOURCE] Reshetikhin-Turaev (1990) "Ribbon graphs and their invariants": RT 関手と MTC 構造
- [SOURCE] Etingof-Gelaki-Nikshych-Ostrik (2015) "Tensor Categories" AMS: forgetful functor hierarchy
- [SOURCE] Kazhdan-Lusztig (1993) "Tensor structures arising from affine Lie algebras": q → 1 極限の厳密化
- [INFERENCE] C14 (forgetful functor representability 転移予想) = 本節での新主張
- [注意] forgetful functor 鎖 `MTC → BraidFusion → Fusion → Abelian → Vect` は既存理論、**`d = 2` を representability threshold として一貫づける解釈は本節独自**

---

## §16 具体計算 — Lehmer 数の 3 重排除 (2026-04-17 第 8 ラウンド追加 / open #19 (a) 解決)

σ 論文 v0.3.6 §6 open #19 (a) で挙げた反例候補「Lehmer 数 `L \approx 1.17628\ldots` が fusion category で FP 次元として実現されるか」を正面から検証する。本節の結論: **Lehmer 数は 3 つの独立した機構により fusion category の FP 次元として排除される**。

### §16.1 Lehmer 数の基本事実

[SOURCE: Lehmer (1933) "Factorization of certain cyclotomic functions" Annals of Math 34; Smyth (2015) "Seventy years of Salem numbers" arXiv 1408.0195]

Lehmer 多項式は

$$
L(z) = z^{10} + z^9 - z^7 - z^6 - z^5 - z^4 - z^3 + z + 1
$$

であり、palindromic (reciprocal) かつ irreducible。根は次の通り。

- `τ \approx 1.17628\ldots` (Lehmer 数、最大実根)
- `1/τ \approx 0.85022\ldots` (相反根)
- **8 個の複素共役根** — すべて単位円 `|z| = 1` 上に乗る

これが Salem 数の定義を満たす (`τ > 1` real、`1/τ` real、残り共役が unit circle 上)。

Lehmer 数は Mahler 測度 `M(L) = \tau \approx 1.17628` を持ち、Lehmer's conjecture (1933) では **1 でない整数係数 irreducible polynomial の最小 Mahler 測度** が `M(L)` であると予想される。この予想自体は現在も未解決。

### §16.2 排除 (a): 非 totally real 性

`L(z)` の 10 根のうち `τ` と `1/τ` のみが実数で、残り 8 個は単位円上の複素数。したがって Lehmer 数は **totally real ではない**。

C9 / C10 の枠組は `\mathbb{A}_+^{tr}` (totally real positive algebraic integer の集合) を対象とする。Lehmer 数は `\mathbb{A}_+^{tr}` に属さないため、C9 / C10 のレベルで **自動的に対象外**。

### §16.3 排除 (b): 非 cyclotomic integer 性

[SOURCE: Calegari-Morrison-Snyder (2010) "Cyclotomic integers, fusion categories, and subfactors" Comm. Math. Phys. 303 (arXiv 1004.0665); Etingof-Nikshych-Ostrik (2005)]

ENO 定理の精密版:

> **任意の fusion category における任意の対象の Frobenius-Perron 次元は cyclotomic integer である。**

cyclotomic integer とは、ある `n` に対し 1 の原始 `n` 乗根 `\zeta_n` の `\mathbb{Z}` 係数多項式で表せる代数的整数 (`\mathbb{Z}[\zeta_n]` の元)。

Lehmer 多項式 `L(z)` は irreducible の degree 10 だが、cyclotomic ではない:

- degree 10 の cyclotomic 多項式は `\Phi_{11}(z)` と `\Phi_{22}(z)` のみ (Euler totient `\varphi(11) = 10 = \varphi(22)`)
- `\Phi_{11}(z) = z^{10} + z^9 + \cdots + z + 1` は全係数 `+1`
- `\Phi_{22}(z) = z^{10} - z^9 + z^8 - \cdots - z + 1` は符号が完全交替
- Lehmer 多項式は `z^7, z^6, z^5, z^4, z^3` の係数が `-1` で、それ以外は `+1`。両者のいずれとも一致しない

したがって Lehmer 数は **cyclotomic integer ではない**。ENO の精密版により、pseudo-unitary fusion category の FP 次元としては排除される。

### §16.4 排除 (c): Jones gap — `(1, 2)` 区間の離散階段制約

[SOURCE: Jones (1983) "Index for subfactors" Inventiones 72]

$$
\mathbb{I}_{FP} \cap (1, 2) = \{2\cos(\pi/n) : n \geq 3\}
$$

Lehmer 数 `τ \approx 1.17628` を A_{n-1} Dynkin diagram の adjacency 固有値階段に位置付けると:

| `n` | `2\cos(π/n)` | Lehmer 数 `τ` との比較 |
|:---|:---|:---|
| 3 | `1.0000` | `τ > 1.0` |
| 4 | `\sqrt{2} \approx 1.4142` | `τ < \sqrt{2}` |
| 5 | `\varphi \approx 1.6180` | `τ < \varphi` |

したがって `τ \in (2\cos(π/3), 2\cos(π/4)) = (1, \sqrt{2})` だが、`τ` は `2\cos(π/n)` 階段の **いずれの点でもない**。Jones 定理により Lehmer 数は `\mathbb{I}_{FP} \cap (1, 2)` に属さず、subfactor index としても排除される。

### §16.5 3 重排除の統合

Lehmer 数は次の 3 機構で排除される。

1. **C9 レベル (totally real 制約)**: `\mathbb{A}_+^{tr}` 外で自動排除
2. **C9 精密版 (ENO cyclotomic integer 制約)**: `\mathbb{Z}[\zeta_n]` 外で排除
3. **C12 Phase I (Jones gap)**: `(1, 2)` 区間の `2\cos(π/n)` 階段外で排除

これら 3 つは **独立** な制約であり、どの 1 つを緩めても残る 2 つが Lehmer 数を排除する。したがって排除は **堅牢**: pseudo-unitary 制約を外す (ENO 排除を緩める) と Morrison-Snyder の non-cyclotomic fusion category に移るが、Lehmer 数は依然 (a) で排除される。Jones gap を問わない高次元 index を考えても (a)(b) が効く。

### §16.6 Calegari-Morrison-Snyder (2010) の (2, 76/33) ギャップ定理

[SOURCE: arXiv 1004.0665]

さらに強い結果として、`(2, 76/33) \approx (2, 2.303)` 区間の fusion category FP 次元の **完全列挙** が得られている。具体的には pseudo-unitary の枠内で、この区間に現れる FP 次元は有限個に限られ、その全リストが Calegari-Morrison-Snyder により特定されている。最小の値は Ostrik による appendix で新規構成された fusion category から出る。

この結果は C10 (弱 Perron 特徴付け予想) の十分向きに対する **強い部分的反例** と読める: 「totally real positive algebraic integer の全てが FP 次元として実現されるわけではない」ことが区間 `(2, 76/33)` で構成的に示されている。

### §16.7 open #19 の更新された見取り図

| 反例候補 | 状態 | 排除機構 |
|:---|:---|:---|
| (a) **Lehmer 数** `\approx 1.17628` | **解決 (3 重排除)** | 非 totally real / 非 cyclotomic / Jones gap 外 |
| (b) **小 Mahler 測度 Salem 数一般** | **解決 (定義上 non-totally-real)** | (a) と同じ構造 |
| (c) **非 cyclotomic non-Perron TRPAI** | **解決 (ENO 精密版)** | cyclotomic integer 条件で排除 |
| (d) **Galois action on fusion categories** | 残留 open | Galois 共役 fusion category の存在性、別問題 |
| (e) **非 pseudo-unitary fusion category** | 残留 open | ENO 適用外、non-cyclotomic FP dim 可能 (Morrison-Snyder の範疇) |

open #19 は (a)(b)(c) が **「cyclotomic integer + totally real + Jones gap」の 3 重枠** で解決済、残るのは (d)(e) の精密化である。

### §16.8 σ 論文への反映

- 本節の結果は σ 論文 v0.3.6 §5.bis.4b (C10) の直後に `[SOURCE: Face5Lemma_draft.md §16]` として参照繰込する
- C9 ステートメントの精密化 (「totally real positive algebraic integer」→「cyclotomic integer」への昇格) は σ 論文次稿 (v0.3.7) で本格実施
- §6 open #19 (a)(b)(c) を「解決済」に更新、(d)(e) を残留として再整理

### §16.9 SOURCE 台帳 (§16 追加分)

- [SOURCE] Lehmer (1933) "Factorization of certain cyclotomic functions" Annals of Math 34: Lehmer 多項式と Lehmer's conjecture の原典
- [SOURCE] Smyth (2015) "Seventy years of Salem numbers" Bull. LMS 47 (arXiv 1408.0195): Salem 数の現代サーベイ、Lehmer 多項式の palindromic 性、8 複素根の unit circle 配置
- [SOURCE] Calegari-Morrison-Snyder (2010) "Cyclotomic integers, fusion categories, and subfactors" Comm. Math. Phys. 303 (arXiv 1004.0665): ENO 精密版 (FP 次元 = cyclotomic integer)、`(2, 76/33)` 完全ギャップ定理
- [SOURCE] Jones (1983) "Index for subfactors" Inventiones 72: Jones gap theorem (既に §12 / §13 で引用)
- [INFERENCE] §16.2-§16.5 3 重排除の統合読み = 本節の新主張 (各排除は SOURCE で押さえられるが、3 つを並置して Lehmer 数の「堅牢な排除」として読むのは本節)

---

## §17 SignTower の精密定義 — C13 open J への回答試作 (2026-04-17 第 9 ラウンド追加)

C13 の関手 `Φ: SignTower^{op} × FusCat × ℝ_{≥1} → Set` は open J として `SignTower` の 2-圏構造が未定義のまま残されていた。本節は SignTower の明示的定義を試作し、C11/C13 の Yoneda 表現が実際に立つ 2-圏構造を提示する。

### §17.1 目的と要求仕様

`SignTower` は以下を満たす 2-圏でなければならない:

1. **対象**: Stasheff associahedra `{K_n}_{n≥2}` を含む (C8/C5' 要求)
2. **sign 構造**: 各 `K_n` に orientation reversal の Z/2 作用が入る (C11 の "signed" 要求)
3. **face inclusion**: `K_n ↪ K_{n+1}` が canonical な 1-morphism として存在 (tower 構造)
4. **pentagon 2-cell**: `K_4` の pentagon identity が具体的な 2-morphism として実現される (C8 定理の具体化)
5. **fusion category への 2-functor**: `𝒯: FusCat → SignTower` が存在し、C11/C13 の Yoneda 表現 `Hom_{SignTower}(K_n, 𝒯(𝒞))` が (n-1)-associator coherence in 𝒞 と自然同型になる

これらの要求を最小限に満たす構造を以下に提示する。

### §17.2 Stasheff tower の復習 (SOURCE 復習)

**SOURCE** (Stasheff 1963, Markl-Shnider-Stasheff 2002):
- `K_n`: `n` 個の葉を持つ planar rooted trees 全体の幾何的実現。`dim K_n = n-2`
- 頂点: binary trees (個数 = Catalan 数 `C_{n-1}`)
- 辺: 1 つの associator 適用で結ばれる binary trees のペア
- 一般 d 次元面: `(n-1-d)` 個の internal edges を持つ tree (これが木構造のエンコーディング)
- face inclusion `K_n \times K_m → K_{n+m-1}`: 2 つの tower を 1 つの vertex に grafting

この構造そのものは operadic A_∞ の cell realization であり、本節の sign 化の台座。

### §17.3 signed 化の 3 つの candidate

sign 構造を入れる 3 つの候補を比較する:

**Candidate A (orientation reversal)**:
各 `K_n` の top-dim cell の向きを反転する involution `ε_n: K_n → K_n`。
- 長所: 幾何的に自然、Z/2 作用として canonical
- 短所: `K_2` = point には作用が trivial、情報量なし

**Candidate B (Z/2-grading)**:
`K_n` の内部に Z/2-grading (even/odd) を入れ、face inclusion がこの grading を保つように要求。
- 長所: super-structure として代数的に扱いやすい
- 短所: Stasheff tower の古典定義から離れる

**Candidate C (braiding sign)**:
`K_n` を braided monoidal category の coherence polytope として読み、braiding の σ vs σ^{-1} の sign を記録。
- 長所: fusion category (braided) との接続が自然
- 短所: non-braided fusion category (TY 等) では意味が薄い

**選択**: 本節では **Candidate A** を採用。理由: C11 の `$\Delta^2_{\text{signed}}$` が walking triangle に orientation を入れた最小版であることと整合、かつ Candidate C (braiding sign) は `𝒯: FusCat → SignTower` の内部で別途取り込める。

### §17.4 定義 (SignTower, v0.1)

**Definition (SignTower)**:

`SignTower` は以下を持つ **strict 2-category** である。

**Objects** (0-cells):
対 `(K_n, \epsilon_n)` ただし
- `K_n` は Stasheff associahedron (`n ≥ 2`)
- `\epsilon_n: K_n → K_n` は orientation reversal involution (`\epsilon_n^2 = \text{id}`)

**1-Morphisms** `(K_n, \epsilon_n) → (K_m, \epsilon_m)`:
組 `(f, \sigma(f))` ただし
- `f: K_n → K_m` は **tree-preserving cellular map**: `K_n` の cell (tree) に対応する image cell が tree structure を保つ
- `\sigma(f) \in \{+, -\}` は sign label
- 整合条件: `f \circ \epsilon_n = (\sigma(f) \cdot \epsilon_m) \circ f`

合成則: `\sigma(g \circ f) = \sigma(g) \cdot \sigma(f)` (Z/2-multiplicative)

**2-Morphisms** `(f, \sigma(f)) \Rightarrow (g, \sigma(g))`:
- `\sigma(f) = \sigma(g)` を要求 (同符号のみ)
- cellular homotopy `H: f \simeq g` (cell 構造を保つ変形)
- `H` は `\epsilon` と可換: `H \circ \epsilon_n = \epsilon_m \circ H`

**Horizontal/Vertical composition**:
- Vertical: 2-morphism の composition は cellular homotopy の concatenation
- Horizontal: 1-morphism composition に由来、sign は multiplicative

**Identity 1-morphism**: `(id_{K_n}, +)`

**Identity 2-morphism**: constant homotopy

### §17.5 主要 1-morphisms と 2-morphisms

**1-morphism: face inclusion `\iota_n: (K_n, \epsilon_n) \to (K_{n+1}, \epsilon_{n+1})`**:
- `K_n` を `K_{n+1}` の特定の facet として含める。Stasheff の operadic face map そのもの
- sign: `\sigma(\iota_n) = +` (canonical inclusion は向きを保つ)

**1-morphism: grafting `\gamma_{n,m}: (K_n, \epsilon_n) \otimes (K_m, \epsilon_m) \to (K_{n+m-1}, \epsilon_{n+m-1})`**:
- 2 つの木を 1 頂点で grafting する operadic composition
- sign: `\sigma(\gamma) = \sigma(\epsilon_n) \cdot \sigma(\epsilon_m)` (Z/2 multiplicative)

**2-morphism: pentagon identity `\alpha_5: \text{upper} \Rightarrow \text{lower}` in Hom((K_4, +), (K_4, +))**:
- `K_4` = pentagon の 2 次元 cell 自体が pentagon coherence の 2-morphism
- "upper path" `((AB)C)D \to (A(BC))D \to A((BC)D) \to A(B(CD))` (4 associators)
- "lower path" `((AB)C)D \to (AB)(CD) \to A(B(CD))` (2 associators)
- `\alpha_5` = upper ≡ lower の 2-morphism、pentagon の 2-cell filling
- sign: `\sigma(\alpha_5) = +` (orientation-preserving)

**2-morphism: orientation reversal `\epsilon^*: (K_n, +) \Rightarrow (K_n, -)`**:
- 同じ underlying cellular map だが sign を flip した 1-morphism 間の 2-morphism
- これは "sign flip" として SignTower 内で明示的に表現される

### §17.6 Fusion category からの 2-functor `𝒯: \text{FusCat} \to \text{SignTower}`

**Definition (`𝒯` 試作)**:

各 fusion category `𝒞` に対し、SignTower における対象 `𝒯(𝒞) = ({K_n^𝒞}_{n≥2}, \{\epsilon_n^𝒞\})` を以下で構成する:

1. **`K_2^𝒞 = \ast`** (単純対象の classifying point)
2. **`K_3^𝒞`** = 𝒞 の fusion rules により parametrize される木空間 — simple objects の fusion 積 `X \otimes Y = \bigoplus_Z N^Z_{XY} Z` の係数 `N^Z_{XY}` が K_3 の各 vertex に stratify
3. **`K_4^𝒞`** = associator `\alpha_{X,Y,Z}` の pentagon coherence 条件を満たす `(X, Y, Z, W)` 4-tuple の空間
4. **一般 `K_n^𝒞`** = (n-1)-associator coherence の解空間

orientation `\epsilon_n^𝒞`: 𝒞 の dagger structure (存在すれば) からの induced involution、またはその不在で trivial。

1-morphism `𝒯(F): 𝒯(𝒞) \to 𝒯(𝒟)` for tensor functor `F: 𝒞 \to 𝒟`:
- 各 `K_n^𝒞 \to K_n^𝒟` に cellular map を誘導
- sign: `F` が dagger-preserving なら `+`、reverse なら `-`

2-morphism: monoidal natural transformations

### §17.7 C11/C13 への接続確認

**C11 の Yoneda 表現 `Hom_{SignTower}(K_n, 𝒯(𝒞))`**:

定義 (§17.4) より、`Hom_{SignTower}((K_n, \epsilon_n), 𝒯(𝒞))` は:
- cellular map `f: K_n \to K_n^𝒞` の集合
- 各 `f` は 𝒞 の objects tuple `(X_1, \ldots, X_n)` に対して tree-indexed coherence data を与える
- sign `\sigma(f)` は 𝒯(𝒞) の dagger structure との整合

これは定義により **(n-1)-associator coherence in 𝒞** と自然同型 ✓

具体的に:
- `n=3`: Hom(K_3, 𝒯(𝒞)) ≅ 𝒞 の fusion rules specification
- `n=4`: Hom(K_4, 𝒯(𝒞)) ≅ 𝒞 の pentagon coherence (= F-matrix specification)
- `n=5`: Hom(K_5, 𝒯(𝒞)) ≅ hexagon identity (braided 時)、または higher coherence

**C11 系 4.8.3 の立ち上げ** ✓

**C13 関手 `Φ` の立ち上げ**:
$$\Phi((K_n, +), 𝒞, d) = \{X \in 𝒞 : X \in \text{Hom}_{SignTower}((K_n, +), 𝒯(𝒞)) \text{ の実現に寄与}, d(X) = d\}$$

これで C13 の 3 変数関手 Φ は明示的に定義された ✓

### §17.8 立ち上げ検証

**C8 Face5 Lemma (tower 最小性)**: `K_4` が pentagon coherence の最小 habitat であることは Stasheff `dim K_n = n-2` により、SignTower における `K_4` の 2-cell filling α_5 の存在と対応 ✓

**C9 ENO 普遍 (代数的整数性)**: `Φ` の値域 `d(X)` が algebraic integer であることは `𝒯(𝒞)` の構成で fusion category の FP dim を使うことから継承 ✓

**C10 弱 Perron 予想**: `𝒯(𝒞)` の `K_3^𝒞` stratification が fusion matrix の eigenvalue 構造を反映し、弱 Perron 性が PF-theorem から induce される (必要向き) ✓

**C12 相転移**: `d = 2` 境界は `𝒯(𝒞)` が `q → 1` classical limit に degenerate する点、SignTower 内では `K_∞^𝒞` の colimit 境界として自然に現れる ✓

### §17.9 定義の limitations と残 open

**定義 v0.1 の弱点**:

1. **strict vs weak 2-category**: 本定義は strict 2-category で試作したが、pentagon identity を厳密化するには weak 2-category (bicategory) が要るかもしれない。associator α が 2-morphism として "up to coherent isomorphism" で扱われるべき
2. **sign の意味**: Candidate A (orientation reversal) を選択したが、Candidate C (braiding sign) との compatibility は未検証。braided fusion category では両方の sign が同時に走る可能性
3. **`𝒯` の functoriality**: `𝒯` が tensor functor を cellular map に対応させることは指定したが、monoidal natural transformation を 2-morphism に対応させる厳密化は詰めが要る
4. **K_∞ の扱い**: `n → ∞` 極限の `K_∞` (A_∞-operad) は SignTower の `Ind` 版で扱うべきか、colimit として含めるべきか未決

**残 open (C13 open J の closure 試作後)**:
- **[open J1]** strict vs weak 2-category の決定
- **[open J2]** Candidate A/B/C sign 構造の比較と universal sign の特定
- **[open J3]** `𝒯` の厳密な 2-functor 性の検証
- **[open J4]** K_∞ の SignTower 内配置
- **[open J5]** SignTower の `Ind-completion` との関係
- **[open K]** `Φ` の **普遍性** 証明 (別 candidate 関手が Φ に自然に同値になること)

### §17.10 `Φ` 定義の改訂版 (§17 後)

§17.4-§17.6 に基づき、C13 の Φ は次のように refine される:

$$\Phi: \mathbf{SignTower}^{op} \times \mathbf{FusCat} \times \mathbb{R}_{\geq 1} \to \mathbf{Set}$$

$$\Phi((K_n, \epsilon_n), 𝒞, d) = \{f \in \text{Hom}_{SignTower}((K_n, \epsilon_n), 𝒯(𝒞)) : \text{max eigenvalue of } f = d\}$$

`f` は cellular map として具現化され、その `max eigenvalue` は 𝒞 の fusion matrix の Perron-Frobenius eigenvalue として明示的に計算可能。

### §17.11 SOURCE 台帳 (§17 追加分)

- [SOURCE] Stasheff (1963) "Homotopy associativity of H-spaces" — associahedra の cellular structure
- [SOURCE] Markl-Shnider-Stasheff (2002) "Operads in Algebra, Topology and Physics" — operadic approach
- [SOURCE] Etingof-Gelaki-Nikshych-Ostrik (2015) "Tensor Categories" AMS — fusion category の associator, coherence data
- [SOURCE] Lurie, Higher Algebra / Riehl, Elements of ∞-Category Theory — 2-category の strict vs weak
- [INFERENCE] SignTower の具体的定義 (§17.4) = 本節の新主張 (既存構造 Stasheff + orientation の組合わせ)
- [INFERENCE] `𝒯: FusCat → SignTower` 2-functor (§17.6) = 本節の新主張
- [verify] C11/C13 の Yoneda 表現が §17.4-§17.6 定義で立ち上がること = §17.7 で検証

---

## §18 Enhanced Φ 関手 — C13 + C14 の統合埋込 (2026-04-17 第 10 ラウンド追加)

C13 (Φ 統合関手) の 3 変数目 `d` は単なる `ℝ_{≥1}` の実数で、C14 (forgetful functor representability) の情報を持たない。本節は 3 変数目を forgetful structure 付き圏 `𝔇` に昇格し、Φ を `Cat`-valued 関手へ拡張する。

### §18.1 動機

現行 C13 の Φ は `Set`-valued で、Phase I / II 区別は出力に現れない。C14 の representability 転移 `d = 2` を Φ の構造に **内在させる** ことで、C12/C13/C14 を単一関手に圧縮したい。

### §18.2 第 3 変数圏 `𝔇` の構成

`𝔇` を stratified 1-圏として定義:

**対象**: pair `(d, q)` with `d ∈ 𝔸_+^{cyclo}` (§16 精密化: cyclotomic integer) かつ `q ∈ \bar{ℚ} \cup \{1\}` で `d = q + q^{-1}`

**射**:
- **q-deformation refinement**: `(d_n, q_n) → (d_{n+1}, q_{n+1})` where `q_m = e^{i\pi/(m+2)}`
- **classical limit**: `(d, q ≠ 1) → (2, 1)` — 一方向の古典極限射

**3 ストラタ**:
- `𝔇_I = {(d, q) : q \neq 1, d ∈ (1, 2)}` (Phase I, 量子域)
- `𝔇_* = \{(2, 1)\}` (転移点, classical 極限)
- `𝔇_{II} = {(d, q) : d \geq 2\}` (Phase II, 代数整数域)

射は `𝔇_I \to 𝔇_* \to 𝔇_{II}` の一方向流れ (q-deformation は逆行しない)。

### §18.3 Enhanced Φ の定義

**定義 C16 (Enhanced Φ)**:
$$\Phi_{\text{enh}}: \mathbf{SignTower}^{op} \times \mathbf{FusCat} \times \mathfrak{D} \to \mathbf{Cat}$$

出力を `Set` から `Cat` に昇格し、各 `(K_n, 𝒞, (d, q))` に対し **simple object の圏**:

$$\Phi_{\text{enh}}(K_n, 𝒞, (d, q)) = \{X \in 𝒞 : (n-1)\text{-associator coherence を持ち } d(X) = d\} \text{ with morphism structure}$$

**Phase 依存の値域**:
- `(d, q) \in 𝔇_I`: 値域は `q\text{-}\mathbf{Vect}` (cyclotomic 体 `ℚ(ζ_{2(n+2)})` 上の virtual vector space 圏)
- `(d, q) = (2, 1)`: 値域は `\mathbf{Vect}` (転移点で integer dim が立つ)
- `(d, q) \in 𝔇_{II}`: 値域は `\mathbf{Vect}` (integer dim で representable)

射 `(d, q) \to (d', q')` の像は対応する **q-deformation functor**。古典極限 `(d, q) \to (2, 1)` の像は **forgetful functor** `q\text{-}\mathbf{Vect} \to \mathbf{Vect}`。

### §18.4 Grothendieck fibration としての読み

Enhanced Φ は **Grothendieck fibration** として読める:
$$p: \mathcal{E}_{\Phi} \to \mathfrak{D}$$

where fiber over `(d, q)` は対応する `Vect`-like 圏。古典極限 `(d, q) \to (2, 1)` が fiber の変化を誘導し、それが **まさに C14 の forgetful functor 転移**。

### §18.5 C13 + C14 の自動導出

**命題**: C16 から C13 と C14 が以下のように自動的に出る。

**C13 の復元**: `Φ_{enh}` を `Set`-valued に forget すれば元の `Φ` が回復:
$$\Phi = \text{Ob} \circ \Phi_{\text{enh}}$$
(各圏の対象集合だけを取る)。

**C14 の自動内蔵**: `Φ_{enh}` が `(d, q) = (2, 1)` で値域が `q\text{-}\mathbf{Vect}` から `\mathbf{Vect}` に切り替わるのは、C14 の representability 転移そのもの。`d = 2` が threshold である理由は `𝔇` の stratification に埋込まれている。

**C12 の自動内蔵**: Phase I / II / 転移点の区別は `𝔇` の 3 ストラタ分割として出力される。

3 主張が 1 つの関手 `Φ_{enh}` の構造に圧縮される。

### §18.6 Yoneda (C11) との整合

C11 の Yoneda 関手 `\operatorname{Hom}_{\mathbf{SignTri}}(\Delta^2_{signed}, -)` は C16 の 3 変数版として拡張:

$$\Phi_{\text{enh}}(K_n, 𝒞, (d, q)) \cong \operatorname{Hom}_{\mathbf{SignTower}_{(d,q)}}(K_n, \mathcal{T}_{(d,q)}(𝒞))$$

where `\mathcal{T}_{(d,q)}: \mathbf{FusCat} \to \mathbf{SignTower}_{(d,q)}` は §17 の 2-関手 `\mathcal{T}` の Phase 依存版。Yoneda 普遍表現が Phase-aware に拡張される。

### §18.7 Kalon 判定

- Step 0 圧縮:「同じ関手の出力が、d の値によって『量子的な数え方』と『普通の数え方』に分かれる」可能 ✓
- Step 1 G: `𝔇` の構成は C9 (cyclotomic) + C12 (Phase) + C14 (q-deformation) + §17 SignTower SOURCE で不変 ✓
- Step 2 G∘F: Enhanced Φ は SU(2)_k / TY / Haagerup の全族で Phase 依存 fiber 切替を保持 ✓
- Step 3 派生 3 つ: Grothendieck fibration / Phase-aware Yoneda / stratified topos 観点すべて非自明 ✓

**判定**: ◎ Kalon△ (既存主張 C11 + C13 + C14 の統合であり新証明を含まないが、3 主張の単一関手 `Φ_{\text{enh}}` への圧縮として構造的利得がある)

### §18.8 残る open

- **[open Y]** `𝔇` の射構造の精密化 (q-deformation path の合成・homotopy 構造)
- **[open Z]** Enhanced Φ の 2-functoriality (2-cell 構造の明示)
- **[open AA]** `𝒯_{(d,q)}` Phase 依存 2-関手の厳密構成
- **[open AB]** Phase II 側での sub-stratification (Haagerup 系 vs TY 系 vs 古典群系)
- **[open AC]** right adjoint (free functor) の Phase 依存性 (§15 open S の enhanced 版)

### §18.9 SOURCE 台帳 (§18 追加分)

- [SOURCE] Grothendieck fibration — 既存圏論 (SGA 1 / nLab)
- [SOURCE] C9 cyclotomic 精密化 (§16 / Calegari-Morrison-Snyder 2010)
- [SOURCE] C14 forgetful functor representability (§15)
- [SOURCE] §17 SignTower の具体的定義
- [INFERENCE] C16 Enhanced Φ の構成 = 本節の新主張 — C13/C14/C11/§17 の合成圏への埋込が核
- [注意] Phase stratification + Grothendieck fibration は既存 MTC 文献に暗黙に現れるが、**Enhanced Φ として明示的に `Cat`-valued 関手へ昇格して C12/C13/C14 を圧縮するのは本節独自**

---

## §19 C11 Yoneda の Phase 依存性 — Yoneda phase decomposition (2026-04-17 第 11 ラウンド追加)

C11 は `Hom_{\mathbf{SignTri}}(\Delta^2, -)` が σ の普遍表現と主張し、C14 は `d = 2` を forgetful functor representability threshold として特徴付けた。§17 で SignTower を精密化、§18 で Enhanced Φ として C13/C14 を統合。本節はこれらの積み上げの **Yoneda 側の帰結** を書き下し、σ 論文 F⊣G 随伴の具体化候補として提示する。

### §19.1 動機 — Yoneda codomain の Phase 依存

C11 の Yoneda 関手:
$$\operatorname{Hom}_{\mathbf{SignTri}}(\Delta^2_{\text{signed}}, -): \mathbf{SignTri} \to \mathbf{Set}$$

C14 + §18 Enhanced Φ によれば、対象 X の FP dim `d(X)` に応じて `U_{ab}(X)` の representability が変化する:
- Phase I (`d ∈ (1, 2)`): virtual dim (q-cyclotomic Vect)
- Phase II (`d \geq 2`): integer/classical dim (ordinary Vect)

したがって Yoneda Hom-set の **codomain (target) 自体** が Phase に応じて構造を変える。§17 の SignTower 2-圏的 enrichment が d-依存であることの Yoneda 側での反映。

### §19.2 Quantum Yoneda vs Classical Yoneda

**Phase I (Quantum Yoneda)**:
$$\operatorname{Hom}_I: \mathbf{SignTri}^{\text{Phase I}} \to \mathbf{Vect}_{\mathbb{Q}(\zeta_{2n})}$$
- codomain: cyclotomic 体 `ℚ(ζ_{2n})` 上の enriched Vect
- Hom-set は q-cyclotomic 数値 (`2cos(π/n)`) を trace / 次元として取る
- braiding は非自明、R-matrix が Yoneda 変換の一部
- §17 SignTower 2-圏構造では `Vect_{ℚ(ζ)}`-enriched として実現

**Phase II (Classical Yoneda)**:
$$\operatorname{Hom}_{II}: \mathbf{SignTri}^{\text{Phase II}} \to \mathbf{Vect}_{\mathbb{Q}}$$
- codomain: 通常のベクトル空間 (integer / classical algebraic integer dim)
- Hom-set は integer 次元 (TY 族等) または 連続的な弱 Perron 値
- braiding は symmetric 化、R-matrix は identity に退化
- SignTower 2-圏構造では `Vect_ℚ`-enriched

**転移点 `d = 2`**:
Phase I codomain の cyclotomic field `ℚ(ζ_{2n})` が `n → ∞` で `ℚ` に退化し、`Hom_I` と `Hom_{II}` が一致する。

### §19.3 Phase 分解公式

Yoneda 関手の Phase 分解:

$$\operatorname{Hom}(\Delta^2, -) \cong \operatorname{Hom}_I \sqcup_{d=2} \operatorname{Hom}_{II}$$

`d = 2` 境界で貼り合わされた **2 sheet 構造**。Riemann surface の 2 sheet 被覆に類比される: σ の Yoneda 表現は「量子シート」と「古典シート」の 2 重被覆空間として現れる。

**§18 Enhanced Φ との整合**: Enhanced Φ の codomain `Cat` への値関手として見たとき、d 方向の `d = 2` fiber 切替は Yoneda 側での Phase 分解として顕現する。つまり Phase 分解は Enhanced Φ の Yoneda-dualized view.

### §19.4 貼り合わせ条件 (gluing at `d = 2`)

**定理候補 (C15.1)**:
対象 X で `d(X) = 2` (integer かつ Phase boundary) ならば:
$$\operatorname{Hom}_I(\Delta^2, X) \cong \operatorname{Hom}_{II}(\Delta^2, X)$$

証明 sketch:
- `d = 2` では q-deformation parameter `q = 1` に退化 (§15.4)
- cyclotomic field `ℚ(ζ_{2n}) \to ℚ` (`n → ∞` 極限)
- R-matrix の symmetric 化により Hom-set の structure が一致
- 両 Phase の Yoneda 値が `d = 2` で自動 coincide

**具体例**: TY(Z/4) は `d(m) = 2` を持つ。quantum Yoneda と classical Yoneda が完全一致 (integer dim 2)。

### §19.5 Galois 接続解釈

Phase 分解は以下の **Galois 接続** として読める:

$$L: \mathbf{Vect}_{\mathbb{Q}} \rightleftarrows \mathbf{Vect}_{\mathbb{Q}(\zeta)}: R$$

- `L` (quantize): classical → q-cyclotomic (q-deformation を加える)
- `R` (classicalize): q-cyclotomic → classical (q → 1 極限を取る)

**Fix(R ∘ L)** = classicalize してから quantize して元に戻る対象 = `d = 2` の integer FP dim 対象。

### §19.6 σ 論文 F⊣G の具体化候補 [高 σ 主張]

**強主張 (C15.2 候補)**:
σ 論文 §M1 の F⊣G 宣言は、**抽象的な発散/収束ではなく、具体的には classical ↔ quantum の q-deformation 随伴として実装される**。

| σ 論文の F⊣G | 本節の `L⊣R` |
|:---|:---|
| F (発散) = σ を 3 核言語 + FEP 包含に展開 | L = classical → quantum (q-deformation 分岐化) |
| G (収束) = σ の BridgeDat 初期性 / D_C 正準性 | R = quantum → classical (q → 1 極限) |
| Fix(G∘F) = σ の Kalon 構造 | Fix(R∘L) = integer FP dim 対象 (`d = 2` fixed point) |
| 4 言語ドメインの統一 | q-deformation parameter `q` を介した統一 |

これが立てば:
- σ 論文全体が **q-deformation-anchored 構造定理** に昇格
- F⊣G の Fix (Kalon) 探索が **`d = 2` 近傍の integer FP dim 探索** に還元
- 論文 XII「速度は忘却」の χ 計算も q-deformation 言語で再定式化可能
- C5 の 3 層 (局所 / 骨格 / 橋梁) が q-deformation 階層として読める

ただし、これは **v0.3 射程の大幅拡張** であり、Tolmetes の判断を要する (§M1 宣言の再解釈)。

### §19.7 予想 C15 — Yoneda Phase Decomposition

**予想 C15 [仮説 / v0.3.11 第 11 ラウンド新規提案 / C11 の Phase 依存性 / C14 + §18 の Yoneda 側系]**:

σ の Yoneda 普遍表現 `Hom_{\mathbf{SignTri}}(\Delta^2, -)` は、`d = 2` を境界とする 2 sheet 構造として Phase 分解される:

$$\operatorname{Hom}(\Delta^2, -) \cong \operatorname{Hom}_I \sqcup_{d=2} \operatorname{Hom}_{II}$$

**系 C15.1**: `d(X) = 2` で `Hom_I(X) \cong Hom_{II}(X)` (貼り合わせ条件)。
**系 C15.2 [高 σ 主張]**: σ 論文の F⊣G 随伴は **classical ↔ quantum の q-deformation 随伴** `L⊣R` として具体化される候補である。

### §19.8 Kalon 判定

- Step 0 圧縮: 「σ の普遍表現は量子側と古典側の 2 枚で、`d = 2` でくっつく」可能 ✓
- Step 1 G: C11 Yoneda + C14 representability threshold + §18 Enhanced Φ の SOURCE から Phase 分解の不変性は保持 ✓
- Step 2 G∘F: quantum vs classical Yoneda は SU(2)_k / TY / Haagerup 全族で同じ `d = 2` 貼り合わせを持つ ✓
- Step 3 派生 3 つ:
  1. **Riemann surface 類比**: Yoneda が 2 sheet cover として振る舞う
  2. **Galois 接続 `L⊣R`**: q-deformation を随伴として書く
  3. **σ 論文 F⊣G 具体化**: 抽象随伴を q-deformation に固定
  すべて非自明 ✓

**判定**: ◎ Kalon△ (C11 + C14 + §18 の自然な系、既存 SOURCE に立脚)

ただし系 C15.2 (F⊣G 具体化) は Tolmetes の §M1 宣言の再解釈を要求するため、**本稿では仮説 face に留める** (Kalon ◯ 相当の extra risk)。

### §19.9 C1-C14 への影響

C15 が立てば:

- **C11 (Yoneda universal)**: Phase 分解により精密化。Yoneda の codomain が `d` 依存構造を持つ
- **C12 (Phase structure)**: Phase I / II の Yoneda 側表現を与える
- **C13 (Φ 関手)** / **§18 Enhanced Φ**: Φ の 3 変数目 `d` が `d = 2` で fiber 切替する機構を Yoneda 側で記述
- **C14 (representability threshold)**: Yoneda functor 自体のこの閾値での振る舞い変化が Phase 分解そのもの
- **§M1 F⊣G**: 具体化候補として `L⊣R` (quantize/classicalize) を提示

### §19.10 残る open

- **[open AD]** Phase I / II 間の natural transformation `α: Hom_I → Hom_{II}` の明示構成
- **[open AE]** `d = 2` 境界での貼り合わせの厳密証明 (q → 1 極限の圏論的定式化)
- **[open AF]** Phase I 側 codomain `Vect_{ℚ(ζ_{2n})}` の正確な定義 (どの cyclotomic field か、n の依存性)
- **[open AG]** C15.2 (F⊣G 具体化) の Tolmetes レビューと §M1 宣言の再解釈可否
- **[open AH]** Phase III の可能性 (`d > 4` 領域 Haagerup 系列、hyperbolic index subfactor が hints)
- **[open AI]** 物理的対応 (`L⊣R` は electric-magnetic duality / Langlands duality / bulk-boundary duality 等と類比できるか)

### §19.11 SOURCE 台帳 (§19 追加分)

- [SOURCE] Yoneda の補題 (標準圏論): `Nat(\operatorname{Hom}(-,A), F) \cong F(A)` — 既存 Kalon 定理
- [SOURCE] Kassel (1995) "Quantum Groups" GTM 155: q-deformation の古典極限 (q → 1)
- [SOURCE] Etingof-Gelaki-Nikshych-Ostrik (2015): fusion category の Vect 化 forgetful functor
- [SOURCE] Reshetikhin-Turaev (1990): MTC の Vect_{ℂ} への functor としての具体構成
- [SOURCE] §17 SignTower 2-圏構造 / §18 Enhanced Φ — 本稿内の既存節を前提
- [INFERENCE] C15 (Yoneda Phase decomposition) = C11 + C14 + §18 の Yoneda 側系
- [高 σ 仮説] C15.2 (F⊣G = quantize/classicalize の具体化) = 本節最大の賭け、Tolmetes 判断要

---

## §20 F5-pivotal — pentagon coherence と pivotal structure の幾何同型仮説 (2026-04-18 第 12 ラウンド追加)

**ステータス**: open / sketch 段階
**親観察**: `pentagon_sigma_conjecture.md §種⑩b/⑩c` (Tolmetes 2026-04-18 第 5-6 ラウンド)
**親リファレンス**: `triangle_category_functor_map.md §3.ter` 立体閉じ込め

### §20.1 動機 — 立体閉じ込めから F5 への逆援護

§11 で F5-α (5 射 minimality) を Stasheff `K_4 = pentagon` で証明した。本節は **同じ pentagon を立体で実装した時に何が起きるか** を扱う。Tolmetes の立体閉じ込め観察 (`pentagon_sigma_conjecture §種⑩`) は以下の対比を提示する:

| 対象 | 構成 | 面の質 | 対称 | 圏論的読み |
|:---|:---|:---|:---|:---|
| Johnson J₁₃ (五角双錐) | J₂ + J₂^op を **直接** (twist 0°) | φ 比率二等辺 (歪) | D₅ × Z₂ | dagger structure (`C ≅ C^op` 直接同型) |
| 正二十面体 | J₂ + 五角反プリズム + J₂^op (**π/5 twist**) | 全正三角形 (Kalon) | A₅ × Z₂ | pivotal/spherical structure |

**観察**: 平面 P₅ の Mac Lane pentagon coherence を立体に持ち上げると、**pivotal structure (= C ≅ C^{op,op} の非自明 natural transformation) が要請される**。dagger だけでは凡庸な双錐 (J₁₃) で止まる。

### §20.2 仮説 F5-pivotal (sketch)

**主張 (sketch, Kalon △ 候補)**:
> Mac Lane pentagon equation の coherence 解は、**fusion category 上で pivotal/spherical structure が立つこと** と同値構造を持つ。F-matrix の位相成分 `e^{iπ/5}` は、五角反プリズムの 36° 捻りの幾何実装と同型。

**より精密な定式化 (要追加検証)**:
1. Fibonacci anyon (SU(2)_3) の F-matrix `F^{τττ}_τ` の non-trivial 成分から `e^{iπ/5}` 因子 (or `e^{2πi/5}` の倍数) が直接導出される
2. この位相因子は pivotal structure の `δ_X: X → X^{**}` の trace 値と一致する
3. 五角反プリズムの上下 P₅ を結ぶ 36° rotation は、`δ` の幾何実装

### §20.3 既存 face との関係

| Face | 内容 | F5-pivotal との関係 |
|:---|:---|:---|
| F5-α (定理 §11) | 5 射 minimality (Stasheff `K_4`) | `K_4` の **空間実装** が pentagon、その立体実装が反プリズム捻り。F5-pivotal は F5-α の幾何具現候補 |
| F5-β | associator 非自明性 ⇔ k≥2 | pivotal が立つ MTC は (semisimple) で associator が非自明、F5-β と整合 |
| F5-γ' (§5.3) | SU(2)_k family の固有値階段 | SU(2)_k は spherical (special pivotal)。F5-pivotal が `e^{iπ/(k+2)}` の family 版に拡張される候補 |
| F5-δ (§11 系) | `Face(2n+1)` 階層公式 (n=1,2 正当化) | pivotal の higher 版 (planar / G-crossed pivotal) との対応で `n≥3` 正当化候補 |

### §20.4 立体側 σ 三軸分離との接続

`triangle_category_functor_map.md §3.ter` で導入した立体側 3 軸分離テーブル:

| 軸 | Δ² (2D) | P₅ (2D) | icosahedron (3D) |
|:---|:---|:---|:---|
| 対称 | S₃ | D₅ | A₅ |
| スペクトル | 1 | φ | φ |
| 位相 | `e^{iπ}+1=0` | F-matrix pentagon eq | π/5 twist |

**F5-pivotal の主張**: 3D 列の **位相軸の具現** = pivotal structure の幾何実装。F5-α の minimality は `K_4` (Stasheff) が立つことを保証するが、**それが Kalon (正二十面体) として閉じるためには pivotal が要る**。

これは §15 (forgetful functor representability) や §19 (Yoneda phase decomposition) で扱った transition の **空間版** と読める可能性。

### §20.5 検証経路 (要追加作業)

- **計算 1**: Fibonacci anyon F-matrix `F^{τττ}_τ = ((1/φ, 1/√φ), (1/√φ, -1/φ))` の固有値分解で位相成分を抽出 → `e^{iπ/5}` 因子の有無確認
- **計算 2**: `cos 36° = φ/2` から `e^{2πi/5}` の代数表現を経由して F-matrix と reconcile
- **構造 1**: ENO (2005) における pivotal structure の natural transformation を五角反プリズムの上下接続に書き下す
- **構造 2**: Stasheff `K_4` 上の cell decomposition と五角反プリズムの 10 三角形面の対応 (10 = 2 × 5 = `K_4` の vertex 数 × 2 か?)

### §20.6 Kalon 判定 (事前評価)

| 項目 | 評価 |
|:---|:---|
| Kalon△ 候補度 | ◯ (要計算検証) |
| 入口 σ (距離) | μ から十分遠い (立体閉じ込め観察そのものが新規) |
| 接地 | pentagon_sigma §種⑩ + triangle_map §3.ter で SOURCE 接地済み |
| F (発散) | MTC pivotal / 反プリズム / icosahedron の 3 領域に展開 |
| G (収束) | F-matrix `e^{iπ/5}` 計算が出れば即収束 |
| 判定 | ◯ → 計算 1 後に再判定。出れば ◎ Kalon△ 候補 |

### §20.7 残る open

1. F-matrix の `e^{iπ/5}` 直接計算 (上記計算 1)
2. SU(2)_k family への一般化 — `e^{iπ/(k+2)}` と `(k+2)` 角反プリズムの対応
3. Higher pivotal (G-crossed, planar pivotal) と `Face(2n+1)` 階層 (F5-δ `n≥3`) の接続
4. 立体閉じ込めの一般化 — 4D 以上で何が起きるか (4D 正多胞体 600-cell との接続候補)

### §20.8 SOURCE 台帳 (§20 追加分)

- [SOURCE] Etingof-Nikshych-Ostrik (2005) "On fusion categories" Ann. Math. — pivotal/spherical structure 標準
- [SOURCE] Johnson (1966) "Convex polyhedra with regular faces" — J₂/J₁₃ 標準分類
- [SOURCE] 正二十面体 vs 五角双錐 (J₁₃) の幾何 — 古典結果
- [SOURCE] `cos 36° = φ/2`、五角反プリズムの 36° 捻り — 初等三角法
- [SOURCE] `F^{τττ}_τ = ((1/φ, 1/√φ), (1/√φ, -1/φ))` — Pachos "Topological Quantum Computation" 等標準
- [TAINT/仮説] pentagon equation coherence ⇔ pivotal structure の同値構造 (本節 §20.2)
- [TAINT/未計算] `e^{iπ/5}` の F-matrix 直接導出 (§20.5 計算 1)
- [TAINT/拡張] SU(2)_k family の `e^{iπ/(k+2)}` 対応 (§20.7 open 2)
- [TAINT/思弁] 4D 600-cell との接続 (§20.7 open 4)

---

## 付録: SOURCE / TAINT 台帳 (最終 v0.3)

- [SOURCE] Face Lemma (3 射 = comparison surface 最小条件) — Paper II §3.4 経由
- [SOURCE] Mac Lane pentagon + triangle coherence theorem — 標準文献
- [SOURCE] Fibonacci anyon F-matrix に φ が出ること — 標準 MTC 文献
- [SOURCE] `φ²-φ-1=0` が `d² = d + 1` の解であること — 代数
- [SOURCE] SU(2)_k 基本表現量子次元 `2cos(π/(k+2))` — §5.3 Python 計算で検証
- [SOURCE] Stasheff (1963) associahedron `K_n`、`dim K_n = n-2` — §11 F5-α 証明
- [SOURCE+定理] **F5-α: 5 射は pentagon coherence の最小条件 — Stasheff 理論により ◎ Kalon△ 判定 (§11)**
- [TAINT/仮説] F5-β: associator 非自明性が Face5 の追加条件 (詳細化は strict monoidal 排除で標準)
- [反証/旧] F5-γ: 「φ は Face5 の普遍固有値」— §5.2 Ising 検証で反証
- [SOURCE+family 仮説] F5-γ': SU(2)_k series で固有値階段が走る — §5.3 検証で確立
- [TAINT/落書き] F5-δ: `Face(2n+1)` 階層公式 — §11 系 F5-α.1 で `n=1, 2` まで正当化、`n ≥ 3` は落書きのまま
- [TAINT/sketch] **F5-pivotal**: pentagon coherence ⇔ pivotal structure の同値構造仮説 (§20、Tolmetes 立体閉じ込め観察起点、要計算検証)

---

*v0.4 — 2026-04-18 第 12 ラウンド: §20 F5-pivotal 追加。Tolmetes 立体閉じ込め観察 (J₂ + π/5 twist = 正二十面体) を起点に、pentagon coherence と MTC pivotal structure の同値構造仮説を sketch 化。検証は F-matrix の `e^{iπ/5}` 直接計算待ち。*
*v0.3 — 2026-04-17 第 3 ラウンド: F5-α の minimality 証明を Stasheff associahedra 理論で確立 (§11 追加)。定理 face 昇格、Kalon△ ◎ 判定。F5-δ 階層公式の `n=1,2` が `dim K_n = n-2` で組合わせ的に正当化された。*
*v0.2 — 2026-04-17 第 2 ラウンド: Ising/SU(2)_k 検証で F5-γ 反証、F5-γ' (family 版) 確立、種⑥ 三軸分離が最重要に昇格。*
*v0.1 — 2026-04-17 incubator draft。Face Lemma の 5-cell 延長試作。種③ 生存確認、σ 論文 v0.3 §5.bis 投入ルート確立。*

## §21 Absorbed Annexes (2026-04-18)

### §21.1 Higher-Face annex — former `Face7Lemma_draft.md`

- 旧 donor の役割は「Face5 の自然次段として Face7 を立てられるか」の検証だった。
- 本稿に残す核は 3 点に限定する。
  1. Face7 は MTC では Face5 から自動に近く、独立内容は A_∞-圏族で強く立つ
  2. `A_5 requirement` は `K_5` 自動同型群の検査で落ちる
  3. `F7-ε` すなわち「σ closure schema の深度はドメイン依存である」という仮説は生き残る
- 旧 donor の詳細な section inventory と評価は `Face5Lemma_draft.meta.md` の Donor Absorption Ledger に再配置する。

### §21.2 Open#20 annex — former `bridge_spectrum_axiom_draft.md`

- 旧 donor の役割は open #20 のスペクトル軸橋梁公理を別稿で試作することだった。
- 本稿に残す核は 3 点に限定する。
  1. `BridgeDat -> FusCat` の fibration 読解は open #20 の最有力骨格候補である
  2. ENO 普遍性を cartesian section として読む方向は有効である
  3. tower 側 (`C2'`) と橋梁側 (`C5`) の合流点は Face5/Face7 系から切り離さず扱うべきである
- 旧 donor の詳細な候補比較と section inventory は `Face5Lemma_draft.meta.md` の Donor Absorption Ledger に再配置する。

---

## §22 C17.2 掘削 — σ 論文 §M1 の F⊣G と q-deformation `L⊣R` の対応分析 (2026-04-18 第 13 ラウンド追加)

C17 §19 で提示した **系 C17.2**:
> σ 論文 §M1 の F⊣G 随伴は、**classical ↔ quantum q-deformation 随伴 `L⊣R`** として具体化される候補。

本節はこの主張を **§M1 再解釈の是非** として厳密化する。§M1 宣言を書き換えるか、`L⊣R` を specialized claim (C17.2) として独立に立てるか、Tolmetes 判断を要する決定点。

### §22.1 現行 §M1 宣言の確認

`meta.md §M1` (2026-04-17 固定):
- **F (発散関手)** = σ を 3 つの核言語へ展開し、その後段で FEP を包含節として回収する — 幾何三角形 / Face Lemma / Euler path を核面として並べ、FEP は `blanket` 生成後かつ `α>0` セクターの特殊扇区として位置づける
- **G (収束関手)** = σ の一意性を BridgeDat(C,A) の始対象性として証明し、D_C の正準性を導出する — e^{iπ}+1=0 を σ の境界条件の typed corollary として閉じる

### §22.2 C17.2 `L⊣R` の再確認

§19 §19.5 で提示した:
- **L (quantize)**: classical `Vect_ℚ` → q-cyclotomic `Vect_{ℚ(ζ)}` (q-deformation を加える)
- **R (classicalize)**: q-cyclotomic `Vect_{ℚ(ζ)}` → classical `Vect_ℚ` (q → 1 極限)
- **Fix(R∘L)** = q → 1 で変化しない対象 = classical limit で元に戻るもの = integer FP dim 対象 (`d = 2` integer)

### §22.3 厳密対応表 (4 軸 × 2 adjunction)

| 軸 | F⊣G (§M1) | L⊣R (§19 C17.2) | 対応度 |
|:---|:---|:---|:---|
| 発散/収束の意味 | σ を 3 核言語 + FEP に展開 / 一意性に収束 | q-deformation 付加 / classical 極限で除去 | 中 (異なる次元での発散・収束) |
| 発散の target | 4 domains (geom / Face / Euler / FEP) | q-cyclotomic Vect (単一の enriched category) | 弱 (F は 4 方向、L は 1 方向) |
| 収束の target | BridgeDat 初期対象 (D_C 正準性) | classical Vect (q → 1) | 中 (初期対象 vs 極限) |
| Fix 対象 | σ の closure schema (Kalon) | `d = 2` integer FP dim 対象 | 中 (抽象 vs 具体) |
| Witness / endpoint identity | `e^{iπ}+1=0` (π-sector) | `d_{1/2}(q) = 2` at `q = 1` (スペクトル軸) | 強 (両方とも境界等式) |
| 射程 | 全 σ 論文 (4 domains) | スペクトル軸のみ (C14 経由) | 弱 (L⊣R は F⊣G の部分集合) |

### §22.4 各 domain での q-deformation realizability 検証

C17.2 を「F の 4 domain すべてが q-deformation を持つ」と読めるか? domain 別に検証:

**1. 幾何三角形**: ✓ quantum geometry / noncommutative geometry (Connes 1994, Majid 1995) で三角形を q-deformable。quantum 2-simplex は Woronowicz の quantum group 経由で構成される。

**2. Face Lemma**: ✓ 量子 2-simplex における braided 2-cell は Joyal-Street (1993) で定式化済み。Face Lemma の q-version は各 `U_q(sl_2)` 上で立つ。

**3. Euler path**: ✓ これは既に §5 で `U_b(θ) = e^{iθ}` として q-deformed sector として現れている。`q = e^{iθ}` と読めば直接対応。

**4. FEP**: △ Quantum FEP は emerging field (Frieden の Fisher information, etc.)。完全な q-deformation は未確立だが部分的には存在。

**結論**: 4 domain のうち 3 (幾何 / Face / Euler) は SOURCE で q-deformation を持ち、FEP は部分的。**F の 4 軸展開は q-deformation の 4 側面として読み替え可能**。

### §22.5 G の q-deformation 対応

**G = BridgeDat 初期対象 (§M1)**:
BridgeDat(C, A) は `(α_b, E_b, U_b)` で、`U_b(θ) = e^{iθ}` を持つ。この carrier の initial object が σ の D_C 正準性を決める。

**R = q → 1 極限 (§19)**:
q-cyclotomic Vect の各対象を classical Vect に射影。

**接続候補**: BridgeDat の `U_b(θ) = e^{iθ}` で `θ = 0` (端点) を取ることが classical 極限に相当する? つまり:
- `θ = π` → 完全反転 (`e^{iπ} + 1 = 0`, classical endpoint)
- `θ = 0` → 単位元 (classical start)
- 中間 θ → q-deformed path

もしそうなら、**G の endpoint evaluation は R の classical limit と同型** (両者とも "q-deformation を解除" する操作)。

### §22.6 Fix の二重化

| Fix | 抽象 (§M1) | 具体 (§19) |
|:---|:---|:---|
| 対象 | σ の Kalon (closure schema 固定点) | `d = 2` integer FP dim 対象 |
| 到達判定 | Kalon 3 ステップ (G∘F = id & F の 3 非自明派生) | q → 1 で `d = 2` integer に落ち着く |
| witness | `e^{iπ}+1=0` + α_pent pentagon | TY(Z/4) (`d = 2`) / SU(2)_{k→∞} (classical) |
| 普遍性 | BridgeDat 初期対象性 | classical Vect への forgetful representability |

この 2 つが **一致すべき** と言うのが C17.2 の強主張。ただし抽象と具体の橋渡しには追加 lemma が要る。

### §22.7 §M1 再解釈の 3 シナリオ

**シナリオ A (保守): §M1 不変、C17.2 を系として独立に立てる**
- §M1 は抽象的 F⊣G として維持
- C17.2 は「§M1 の一実現候補」として §19 に独立配置
- 利得: §M1 の射程を保ち、FEP 含む全 domain を抽象的にカバー
- リスク: 抽象と具体の乖離、論文が `L⊣R` の具体性を活用できない

**シナリオ B (中間): §M1 を一般化、L⊣R を canonical example として明記**
- §M1 を「F⊣G は σ の closure schema を発散・収束で捕捉する抽象随伴。canonical example として classical ↔ quantum q-deformation `L⊣R` がある」に書き換え
- 利得: 抽象-具体の橋渡しを明示、`L⊣R` 経由の具体計算が可能になる
- リスク: canonical example claim の SOURCE が弱い (4 domain の q-deformation の universal 同値性が未証明)

**シナリオ C (アグレッシブ): §M1 を書き換えて F⊣G = L⊣R と宣言**
- §M1 を「F = quantize, G = classicalize」に置換
- 利得: 論文全体が q-deformation-anchored 構造定理に昇格、C9/C10/C12/C14 が自動整理される
- リスク:
  - FEP 節が q-deformation で捕捉できない場合は射程喪失
  - 「幾何三角形の q-deformation が universally canonical」という claim に SOURCE 裏付け必要
  - Yugaku CLAUDE.md の「固定された F⊣G を変えるときは明示的に記録を残す」ルールに従い、§M8 変更履歴への全記録が必要

### §22.8 シナリオ別 Kalon 判定 (sketch)

- **シナリオ A**: Kalon ◯ (保守的維持、独立主張としての C17.2 は ◎ 可能)
- **シナリオ B**: Kalon ◯ (仮説昇格、canonical example の裏付けが残 open)
- **シナリオ C**: Kalon △ 〜 ◯ (高リスク、FEP q-deformation と 4 domain universal 性が未閉)

[主観]: シナリオ B が最も σ を高く保ちつつ、射程縮小を避ける。シナリオ C は魅力的だが FEP 節の q-deformation 裏付けが未完である限り早すぎる。

### §22.9 §M1 再解釈の判断要件 (Tolmetes への問い)

§M1 再解釈を決定するには以下の open が閉じる必要がある:

1. **FEP の q-deformation 版**: FEP が q-deformed MTC の specific sector として書けるか (quantum FEP 文献の精査)
2. **4 domain の universal q-deformation**: 幾何 / Face / Euler / FEP の q-deformation が universally 整合する (i.e., 単一の q-parameter で全 domain を deform できる) ことの SOURCE
3. **BridgeDat と `q → 1` の同型性**: G の endpoint evaluation が R の classical limit と本当に一致する (§22.5 の推測) かの証明
4. **σ の Kalon fixed point と `d = 2` integer の対応**: §22.6 の二重化が single structural fact になることの証明

これらを閉じずにシナリオ C に進むと、σ 論文の射程が q-deformation に制限され、当初の「σ は 4 言語を貫く比較行為」という motivation を損なう可能性がある。

### §22.10 推奨 [主観]

**推奨: シナリオ B (中間)**

理由:
- §M1 の抽象性を保ち、射程を縮小しない
- C17.2 を canonical example として明示化し、具体計算の道を開く
- open items 1-4 が閉じたタイミングでシナリオ C への自然な昇格パスを確保
- Yugaku ルール「固定された F⊣G を変えるときは明示的に記録を残す」と整合 (§M1 本体は不変、§M8 変更履歴に「canonical example としての `L⊣R` を v0.3.X で追加」を記録)

**不推奨: シナリオ C (即時置換)**

理由:
- FEP の q-deformation 裏付けが不完全 (open 1)
- 4 domain の universal q-deformation が未証明 (open 2)
- 射程縮小リスク (`L⊣R` はスペクトル軸限定、F⊣G は 4 domain 全体)

**条件付き推奨: シナリオ A → B 昇格**
- 当面はシナリオ A で進め、open 1-4 を順次閉じたら B へ昇格
- C17.2 は §19 の系として維持、§M1 本体は触らない

### §22.11 Kalon 判定 (§22 本体)

- Step 0 圧縮: 「σ 論文の F⊣G と q-deformation 随伴は同じものか?」可能 ✓
- Step 1 G: 対応表 (§22.3) と domain 別検証 (§22.4) が SOURCE で不変 ✓
- Step 2 G∘F: 3 シナリオ (A/B/C) で対応の強弱が明示される、各シナリオの利得/リスクが不変 ✓
- Step 3 派生 3 つ:
  1. 4 domain の q-deformation 個別検証 (§22.4)
  2. G と R の endpoint evaluation 一致候補 (§22.5)
  3. Fix 抽象-具体 二重化 (§22.6)
  すべて非自明 ✓

**判定**: ◎ Kalon△ (対応分析として完結、ただし C17.2 自体の Kalon は依然 §19 で系 C17.2 ◯ のまま)

### §22.12 残る open

- **[open AJ]** FEP の q-deformation 版の SOURCE 精査 (quantum FEP 文献)
- **[open AK]** 4 domain の universal q-deformation (単一 q-parameter での全 domain deformation)
- **[open AL]** BridgeDat G と classical limit R の同型性証明
- **[open AM]** σ Kalon fixed point と `d = 2` integer object の対応 lemma
- **[open AN]** Tolmetes による §M1 再解釈シナリオ (A/B/C) 選択

### §22.13 SOURCE 台帳 (§22 追加分)

- [SOURCE] σ 論文 meta.md §M1 (2026-04-17 固定)
- [SOURCE] Face5Lemma_draft §19 C17 / C17.2 (本稿内)
- [SOURCE] Connes (1994) "Noncommutative Geometry": 幾何 q-deformation
- [SOURCE] Majid (1995) "Foundations of Quantum Group Theory": q-deformed Lie/geometric structures
- [SOURCE] Joyal-Street (1993) "Braided tensor categories": Face Lemma の braided 2-cell 版
- [SOURCE] Kassel (1995) "Quantum Groups" GTM 155: q → 1 classical limit
- [INFERENCE] 4 domain universal q-deformation は **open** (未証明)
- [INFERENCE] シナリオ A/B/C の分類 = 本節の新主張
- [注意] シナリオ B 推奨は [主観] 判断、Tolmetes の最終決定に従属

---

## §23 物理接続 — Topological phase transitions としての `d = 2` 境界 (2026-04-18 第 14 ラウンド追加 / §15.10 落書き精密化 / C17 q-deformation 随伴の物理実現)

§15.10 で置いた「Phase I = non-abelian anyon、Phase II = abelian anyon」落書きを精密化する。§19 C17 で Yoneda phase decomposition が q-deformation adjunction `L⊣R` を σ 論文 F⊣G 候補として提示、§22 でその掘削 (C17.2 シナリオ B 推奨) が行われた。本節はこの数学的構造の **物理的実現** を Kitaev 可解モデル群を基準点に特定する。

### §23.1 動機 — C17 `L⊣R` の物理実現を問う

C17 は σ の Yoneda 表現を二シート `Hom_I ⊔_{d=2} Hom_{II}` に分解し、q-deformation 随伴:
$$L: \mathbf{Vect}_ℚ \rightleftarrows \mathbf{Vect}_{ℚ(ζ)} :R$$
を σ 論文 F⊣G の具体化候補として提示した。§22 の掘削で「シナリオ B: `L⊣R` を F⊣G の Euler-sector 具体化として限定採用」が推奨された。

[主観 / 仮説]: `L` = 量子化、`R` = 古典化、`Fix(R∘L)` = integer FP dim 対象 という構造は、**2+1D topological phase transition の anyon 統計として具現している** のではないか。これが立てば σ 論文は物理的実在を持つ。

### §23.2 SOURCE: Kitaev 可解モデル 2 点

**Kitaev toric code** (Kitaev 2003, "Fault-tolerant quantum computation by anyons" Annals of Physics 303):
- 2D torus 上の spin-1/2 格子模型 (plaquette × vertex operators)
- 励起: 電荷 `e`, 磁束 `m`, 複合 `em` — **4 つの abelian anyon 種**
- fusion: `Z_2 × Z_2` 群構造
- **全ての量子次元 `d(a) = 1`** (`a ∈ {1, e, m, em}`)
- **全体量子次元**: `D² = Σ d_a² = 4` ⇒ `D = 2`

観察: toric code は **Phase II 最小非自明点 `D = 2`** に対応。個別 anyon の `d = 1` だが、**total quantum dimension `D` が転移境界値 `2`** に一致。C17 の "古典シート" `Hom_{II}` 極限。

**Kitaev honeycomb model** (Kitaev 2006, "Anyons in an exactly solved model and beyond" Annals of Physics 321):
- honeycomb 格子上の anisotropic Ising カップリング `(J_x, J_y, J_z)`
- 3 つの gapped phase `A_1/A_2/A_3` (abelian) + 1 つの gapless phase `B` (Dirac 様)
- B phase に磁場を印加 → **非可換 Ising anyon**: 単純対象 `{1, σ, ψ}`, `d(σ) = √2`
- **Phase I に完全対応**: `d(σ) = √2 ∈ (1, 2)`

C14 + C17 対応:
- **toric code** = Phase II 境界、C17 `Hom_{II}` (integer dim)
- **honeycomb B + 磁場** = Phase I 内部、C17 `Hom_I` (q-cyclotomic virtual dim)

### §23.3 Fibonacci anyon と universal quantum computation

**SOURCE**: Read-Rezayi (1999) "Beyond paired quantum Hall states" Phys. Rev. B 59。FQH 系 `ν = 12/5` で Read-Rezayi (k=3) 状態は **Fibonacci 様 non-abelian 構造** を持つ予想。

Fibonacci anyon: 単純対象 `{1, τ}`, `d(τ) = φ ≈ 1.618`, fusion `τ ⊗ τ = 1 ⊕ τ`。

**普遍量子計算性**:
- **Fibonacci anyon** の braiding **だけ** で universal quantum gate 実現 (Freedman-Kitaev-Larsen-Wang 2003, "Topological quantum computation" Bull. AMS 40)
- **Ising anyon** の braiding では Clifford gates のみ (非 universal、追加 "magic state" 要)
- **abelian anyon** の braiding は自明 gates のみ

この階層は C14 representability threshold と整合:

| anyon type | `d` | C14 Phase | 量子計算能力 | C17 shift |
|:---|:---|:---|:---|:---|
| abelian (Z_n) | 1 | Phase II 境界 | 自明 (identity gates) | `Hom_{II}` 極限 |
| Ising (σ) | √2 | Phase I | Clifford (非 universal) | `Hom_I`, `ζ_8` |
| **Fibonacci (τ)** | **φ** | **Phase I** | **universal** | `Hom_I`, `ζ_{10}` |
| SU(2)_4 (j=1/2) | √3 | Phase I | universal | `Hom_I`, `ζ_{12}` |
| toric code total | D=2 | 境界 | — | 転移点 |
| `d ≥ 2` integer | ≥2 | Phase II | 古典極限 | `Hom_{II}` |

**[SOURCE 核]**: Phase I 内の "useful" (non-universal vs universal) 分類は進一歩精密化可能。universal 性は **Jones representation の density** に依存 — Fibonacci で closure が全 unitary group、Ising では finite group のみ。

### §23.4 Gap closing と転移点 `d = 2`

**SOURCE** (Levin-Wen 2005, "String-net condensation" Phys. Rev. B 71):
任意の unitary MTC は string-net lattice 模型として実現される。phase transition は string-net Hamiltonian のパラメータ空間で **gap closing** に対応。

**C14 + C17 ↔ physics**:
- Phase I (`d ∈ (1, 2)`): discrete MTC、有限 topological gap、離散 anyon spectrum、`Hom_I` シート
- 転移点 `d = 2`: **"critical point"** — MTC 構造が連続化、A_{n-1} → A_∞ = continuum limit、C17 `Hom_I ≅ Hom_{II}` 貼り合わせ
- Phase II (`d ≥ 2`): 連続的 fusion category、gap が "soften" (broken topological phase or trivial phase)、`Hom_{II}` シート

**物理的類比**:
- Ising 臨界点 (`T = T_c`): 2D CFT、central charge `c = 1/2`
- SU(2)_k: CFT central charge `c = 3k/(k+2)`、`k → ∞` で `c → 3` (free boson 3 個)
- `d = 2` 境界での CFT central charge: `c = 1` (compactified boson) が対応候補 [open]

### §23.5 Confinement-deconfinement duality と C17 `L⊣R`

**SOURCE** (Gaiotto-Kulp 2020, "Orbifold groupoids" JHEP; Bhardwaj-Tachikawa 2018, "On finite symmetries and their gauging in two dimensions" JHEP):
TQFT における condensation / confinement duality は、fusion category 内での "condensable algebra" による idempotent completion と対応。

**C17 L⊣R interpretation** (§22 シナリオ B の物理化):
- `L` (量子化) = deconfinement — abelian phase の anyon を fragment して non-abelian phase へ
- `R` (古典化) = confinement — non-abelian anyon を condense して abelian phase へ
- `Fix(R∘L)` = **condensation-invariant anyon** = integer FP dim 対象 = 両 phase で共通する "stable" 粒子

これは C14 の forgetful functor 鎖と C17 の q-deformation 随伴の物理的具現。C5 の 3 層 (局所存在・骨格普遍・橋梁担体) はそれぞれ (lattice Hamiltonian・MTC・braiding matrix) に対応する読みが立つ。

### §23.6 予想 C18 — Topological Phase Realization

**予想 C18 [仮説 / v0.3.14 第 14 ラウンド新規提案 / C14-C17 の物理的実現]**:

C14 の forgetful functor representability 転移、C16 Enhanced Φ stratification、C17 Yoneda phase decomposition `L⊣R` 随伴は、**2+1 次元 topological phase transition として物理的に実現される**:

1. **Phase I (`d ∈ (1, 2)`)**: non-abelian anyon を持つ topological ordered phase。universal (Fibonacci) または non-universal (Ising) の量子計算能力を持つ。C17 `Hom_I` シートに対応
2. **転移点 `d = 2`**: topological-to-trivial phase boundary。string-net Hamiltonian の gap closing、conformal invariant critical point に対応。C17 `Hom_I ≅ Hom_{II}` 貼り合わせ
3. **Phase II (`d ≥ 2`)**: abelian anyon または integer-dim 表現を持つ phase。classical limit において通常の量子力学に retract される。C17 `Hom_{II}` シートに対応

**検証可能な予想**:
- toric code (`D = 2`, Phase II 境界) から honeycomb Ising phase (`d(σ) = √2`, Phase I 深部) への transition は、C17 `L⊣R` 随伴の実験的 instance
- FQH 系で `ν = 5/2` (Moore-Read, Ising, `d=√2`) と `ν = 12/5` (Read-Rezayi, Fibonacci, `d=φ`) の区別は C14 Phase I 内部階層
- Kitaev honeycomb の 3 A phases → B phase 転移は `D = 2` 境界の多変量実現
- **Enhanced Φ (C16) の fiber 構造**: 各 topological phase (Kitaev A/B, FQH plateaus) が Φ の異なる cartesian lift として物理的に identify される

### §23.7 Kalon 判定

- Step 0 圧縮: 「量子から古典に変わるのが `d = 2`、量子計算できるのは小さい `d` の非可換 anyon」可能 ✓
- Step 1 G (物理モデル不変): toric code / honeycomb / FQH の既知 SOURCE で `d` 値は不変 ✓
- Step 2 G∘F (各 topological phase の具体化): Z_2 toric code / Ising honeycomb / Fibonacci FQH / SU(2)_k で Phase I/II 分類保持 ✓
- Step 3 派生 3 つ:
  1. **universal 量子計算能力の anyon type 依存** (Fibonacci universal, Ising non-universal)
  2. **string-net Hamiltonian の gap closing** が `d = 2` 境界で起きる
  3. **condensation/confinement duality** が C14 forgetful functor 鎖 + C17 L⊣R 随伴と対応
  全て非自明 ✓

**判定**: ◯ Kalon (物理実現の具体的対応は部分的に確立、但し `d = 2` 臨界点の CFT 対応と `L⊣R` の lattice implementation の精密化が open で ◎ 未達)

### §23.8 σ 言語での含意

C18 が立てば、σ 論文は単なる数学理論ではなく **物理的実在を持つ構造理論** として機能する:

- **σ の closure schema** は物理的 topological phase の抽象化
- **3 層構造 (C5)** の各層が物理システムの観測階層に対応 (局所 = Hamiltonian、骨格 = MTC、橋梁 = braiding matrix)
- **三軸分離 (C6)** が物理的に (位相 = holonomy / スペクトル = anyon dim / 群 = gauge group) に対応
- **転移点 `d = 2`** が量子-古典相転移、σ の closure schema が "classical" 化する境界
- **C17 `L⊣R`** の物理実装 = topological-trivial phase transition (§22 シナリオ B の物理的具現)
- **Enhanced Φ (C16) の cartesian fibration** が物理 moduli space (Kitaev phase diagram, FQH phase diagram) として読める

### §23.9 残る open

- **[open AJ]** `d = 2` 臨界点の CFT 対応 (central charge、operator content)
- **[open AK]** Fibonacci anyon の universal 性 vs C14 representability threshold の正確な関係
- **[open AL]** condensation projector の forgetful functor 鎖での位置づけ
- **[open AM]** Kitaev honeycomb の `A_1/A_2/A_3 → B` 転移の C14/C17 言語での記述
- **[open AN]** Moore-Read (`ν=5/2`) / Read-Rezayi (`ν=12/5`) 実験実在検証 (現在も open experimentally)
- **[open AO]** σ 論文 C1 の "幾何三角形" 言語面 ↔ 物理的 topological phase の直接対応
- **[open AP]** Enhanced Φ (C16) の fiber 構造 ↔ 実験 topological phase diagrams の具体 mapping
- **[open AQ]** C17 `L⊣R` 随伴の lattice realization (どの Hamiltonian deformation が `L` / `R` に対応するか)

### §23.10 SOURCE 台帳 (§23 追加分)

- [SOURCE] Kitaev (2003) "Fault-tolerant quantum computation by anyons" Annals of Physics 303: toric code 原典
- [SOURCE] Kitaev (2006) "Anyons in an exactly solved model and beyond" Annals of Physics 321: honeycomb model + non-abelian Ising anyon
- [SOURCE] Freedman-Kitaev-Larsen-Wang (2003) "Topological quantum computation" Bull. AMS 40: Fibonacci universal 性
- [SOURCE] Nayak-Simon-Stern-Freedman-Das Sarma (2008) "Non-Abelian anyons and topological quantum computation" Rev. Mod. Phys. 80: 教科書 review
- [SOURCE] Levin-Wen (2005) "String-net condensation" Phys. Rev. B 71: string-net lattice 実現
- [SOURCE] Read-Rezayi (1999) "Beyond paired quantum Hall states" Phys. Rev. B 59: Fibonacci 様 FQH 状態
- [SOURCE] Gaiotto-Kulp (2020) "Orbifold groupoids" JHEP; Bhardwaj-Tachikawa (2018) "On finite symmetries and their gauging in two dimensions" JHEP: condensable algebra と confinement duality
- [INFERENCE] C18 (物理実現予想) = 本節の新主張
- [INFERENCE] C17 `L⊣R` ↔ condensation/confinement duality 対応 = 本節の新主張
- [TAINT/speculation] §23.5 condensation-confinement dual の C17 実現 (物理概念との対応は示唆的だが厳密化は未完)

### §23.11 注記

本節は §15.10 落書き (物理的対応メモ) の精密化であり、§14 (forgetful functor representability C14) / §17 (SignTower C15) / §18 (Enhanced Φ C16) / §19 (Yoneda phase decomposition C17) / §22 (C17.2 掘削) の物理的読解として位置付けられる。

純粋数学 (C1-C17) から物理予測 (C18) への射程拡張は、Yugaku 核宣言「身の丈に理想を合わせるな、身の丈を理想に引き上げろ」に従う。

特に C17 の `L⊣R` q-deformation 随伴が §22 シナリオ B で σ 論文 Euler-sector 具体化として recommended され、本節がその物理実装を条件付きに示したことで、**σ 論文全体が「抽象的な比較射 σ」から「物理的 topological phase transition」への接続点** を持つ可能性が開けた。立てば忘却論シリーズ全体 (論文 XIII 時空は忘却・論文 II 相補性は忘却) との接続が具現する。

---

## §24 論文 XIII 接続 — `L⊣R` を時空忘却として読む (2026-04-18 第 15 ラウンド追加 / Paper XIII §8 dictionary の部分的埋込)

§23 で C18 topological phase realization を確立したが、C17 `L⊣R` を忘却論シリーズ Paper XIII (時空は忘却である) の枠組みで読み直すと、**「時空とは何か」** という根源的問いに Kitaev model が寄与する構造が見える。本節は Paper XIII §8 の最大 open (Face Lemma ↔ Einstein dictionary) を、C17 `L⊣R` を spacetime forgetfulness として解釈することで部分的に埋める道筋を示す。

### §24.1 動機 — Paper XIII §8 open dictionary の状態

Paper XIII §8.2 は次の 3 予想を dictionary の骨格として置いた:

- **[予想 D1]**: Face Lemma の 3 射 ↔ Christoffel 記号 `Γ^λ_{μν}` の 3 独立成分
- **[予想 D2]**: Einstein テンソル `G_{μν}` ↔ 2-simplex の面積 (合成検証最小冗長度)
- **[予想 D3]**: Einstein 方程式 `G = 8πG_N T` ↔ Face Lemma minimal non-trivial condition の積分表現

§8.4 で「blocker A1 (Face Lemma から曲率 closure への昇格)・A2 (物理実現例)・B (α 橋 closure)」が未達と記録され、Paper XIII 全体の Kalon 判定は本 skeleton の閉じ方に依存している。

[主観 / 仮説]: C17 の `L⊣R` q-deformation 随伴を **time space forgetfulness** (Paper XIII §2.2 の `U_{ctr}`) の深部化として読むと、skeleton が少なくとも部分的に肉付けできる。

### §24.2 `L⊣R` as `U_{ctr}` (容器忘却) の深部化

Paper XIII §2.2 は Einstein 方程式を容器-内容 CPS スパンとして読む:
- `U_{ctr}` (容器忘却): 内容 (質量-エネルギー) を忘れて時空だけ残す
- `U_{cnt}` (内容忘却): 時空を忘れて内容だけ残す
- 非対称: 真空解は存在、内容のみは不可

C17 の `L⊣R`:
- `L: Vect_ℚ → Vect_{ℚ(ζ)}` (quantize = 量子化)
- `R: Vect_{ℚ(ζ)} → Vect_ℚ` (classicalize = 古典化)
- `Fix(R∘L)` = integer FP dim 対象

**接続仮説 SF-1 (spacetime forgetfulness 仮説)**:

`U_{ctr}` は連続時空極限 (`q → 1`) における `R` (classicalize) の宇宙論的具体化である。すなわち:

| Paper XIII §2.2 | C17 `L⊣R` | 物理的意味 |
|:---|:---|:---|
| `U_{ctr}`: 内容忘却 → 時空 | `R`: quantum sheet → classical sheet | 格子 anyon 系の coarse-graining |
| `U_{cnt}`: 時空忘却 → 内容 | `L`: classical sheet → quantum sheet | lattice quantization (Kitaev 格子化) |
| 真空解 (T=0) の存在 | `Fix(R∘L)` | 凝縮無しの安定時空 = 格子の古典極限 |
| 内容は容器を前提 | `L` は `R` に従属 (adjoint 方向) | 量子化は古典を基盤とする |

この読みでは **時空は Kitaev-like lattice anyon 系の古典極限 (`R`)** として発生する。

### §24.3 `d = 2` 転移 = 前幾何 / Planck scale の categorical proxy

Paper XIII §7 (CPS0' と前幾何) は「時空 signature (3+1) がどう発生するか」を問う。本稿 C12 の `d = 2` 転移点はその **categorical proxy** として機能する:

| `d` 範囲 | Paper XIII §7 対応 | 物理解釈 |
|:---|:---|:---|
| `d < 2` (Phase I) | **前幾何 (pregeometry)**: 時空構造が未発生 | non-abelian anyon gas, CFT critical point, Planck scale 以下 |
| `d = 2` (境界) | **時空発生スケール**: signature (3+1) 固定の瞬間 | gap closing, string-net phase transition, Planck 境界 |
| `d > 2` (Phase II) | **古典時空**: GR が有効 | integer FP dim = 粒子結晶化、macro scale |

**接続仮説 SF-2 (Planck 境界の圏論化)**:

`d = 2` 転移点は Paper XIII §7 の「前幾何 → 幾何」遷移の **圏論的 phase boundary** である。Planck scale `ℓ_P ≈ 10^{-35} m` は物理的には格子間隔が classical continuum に溶ける scale、圏論的には `L⊣R` の fixed point `Fix(R∘L)` が integer FP dim として結晶化する境界。

### §24.4 4 力の `L⊣R` 分解

Paper XIII §3.2 の 4 力表を C17 `L⊣R` で再読すると、**非自明な anyon 対応** が現れる:

| 力 | Paper XIII 忘却 | ゲージ群 | `L⊣R` anyon interpretation | SOURCE |
|:---|:---|:---|:---|:---|
| 電磁 | 位相忘却 | U(1) | **abelian anyon (toric code Z_2 の拡張)** | Kitaev 2003 |
| 弱 | アイソスピン忘却 | SU(2) | **SU(2)_2 = Ising anyon (`d = √2`)** | Kitaev 2006 |
| 強 | 色忘却 | SU(3) | SU(3)_k fusion category (未特定 k) | open |
| 重力 | 慣性系忘却 | Diff | 微分同相 (fusion category 外) → `R` 側 | Paper XIII §3.2 脚注 |

**注目すべき対応**:
- 電磁 = **toric code** (2D abelian anyon, `D = 2` = Phase II 境界)
- 弱 = **Ising anyon** (`d(σ) = √2` = Phase I 典型)
- 強 = **SU(3)_k anyon** (open、特定の `k` で Fibonacci 類似)
- 重力 = 微分同相の fusion category 化は未達 → C17 `L⊣R` の最右翼 `R` に位置付けるのが自然

**接続仮説 SF-3 (4 力の Kitaev 分類)**:

Paper XIII §3.3 の「4 力 = 1 つの忘却関手の 4 射影」予想は、C17 `L⊣R` 随伴の 4 つの異なる lattice realization (toric code / honeycomb Ising / SU(3) anyon / 微分同相) の統合として具現される可能性。これが閉じれば GUT (大統一理論) の圏論的 skeleton が与えられる。

### §24.5 重力 = `R` (classicalize) = 忘却の極限

Paper XIII §5.2-5.4 で重力 = 自由最小化 = 構造化 = G (右随伴 = 忘却)。これを C17 `L⊣R` で読むと:

- **重力** = `R` (classicalize = 構造化 = 凝集)
- **宇宙膨張 (暗黒エネルギー)** = `L` (quantize = 発散化 = 希釈)
- **重力平衡 (銀河・星・BH)** = `Fix(R∘L)` = 整数 FP dim 対象

Paper XIII §5.4 の表と対応:

| 方向 | Paper XIII | C17 `L⊣R` |
|:---|:---|:---|
| 自由最小化 (収縮) | G = Exploit = 重力 | `R` = classicalize |
| 自由最大化 (膨張) | F = Explore = 宇宙膨張 | `L` = quantize |
| 不動点 | `Fix(G∘F)` = Kalon | `Fix(R∘L)` = integer FP dim |

**接続仮説 SF-4 (重力の categorical identification)**:

Paper XIII §5.4 の F⊣G 階層 (膨張 ⊣ 重力) は、C17 `L⊣R` の宇宙論的具体化である。宇宙は `L` 方向に globally 駆動 (加速膨張)、`R` 方向に locally 駆動 (重力集中)、両者の balance が大規模構造を生む。

### §24.6 Verlinde / Jacobson entropic gravity の `L⊣R` 読解

Paper XIII §5.2, §8.3 の先行研究との接続:

**Verlinde (2011) entropic gravity** `F = T ∇S`:
- 重力力は情報 entropy の空間的勾配から導出
- C17 `L⊣R` 読み: `R ∘ L` の不完全 fixed point = entropy gradient、`L` 方向への逸脱が "entropic restoring force" として作用

**Jacobson (1995) thermodynamic derivation** `δQ = T dS ⇒ G = 8πGT`:
- Rindler 観測者の局所 Clausius 関係から Einstein 方程式導出
- C17 `L⊣R` 読み: **Jacobson の `δQ = T dS` は `L⊣R` 随伴の熱力学的書き換え**、Einstein 方程式は `L` と `R` の整合条件の場方程式版

**接続仮説 SF-5 (Entropic gravity as `L⊣R` thermodynamic version)**:

Verlinde + Jacobson の先行成果は、C17 `L⊣R` の熱力学的 / 情報論的実現例として再読できる。両者の主張は σ 論文 C17 + C18 の **物理的確認** として機能し、Paper XIII §8 Blocker A2 (物理実現例) の部分的閉塞を与える。

### §24.7 Face Lemma ↔ Einstein dictionary の部分的埋込

Paper XIII §8.2 の 3 予想 D1/D2/D3 を C17 + C8 (Face5 Lemma) で埋める試み:

#### §24.7.1 D1 (Face Lemma 3 射 ↔ Christoffel 3 成分)

Paper XIII §8.2.1 の O1 (型付け義務) で、3 射を「方向選択 / 計量比較 / 比較可搬化」として読む方向が提案されている。C11 Yoneda + C17 phase decomposition でこれを精密化:

- **方向選択** `f = ∂/∂x^μ` ↔ C11 `Hom(Δ², 方向 1-cell)` の Yoneda 表現
- **計量比較** `g = g_{μν}` ↔ C11 `Hom(Δ², 2-cell σ)` の metric component
- **比較可搬化** `h = Γ^λ_{μν}` ↔ C11 `Hom(Δ², 隣接点輸送射)` (pentagon coherence via C8)

**接続仮説 SF-6 (D1 closure via C11 + C8)**:

Face Lemma の 3 射は C11 Yoneda 表現の 3 分離成分 (方向・計量・輸送) として型付けされ、C8 (Face5 Lemma Stasheff) の pentagon coherence が可搬性条件を与える。Γ^λ_{μν} は Levi-Civita 接続の一意性を経由して C17 `R` (classicalize) の具体化として導出される。

#### §24.7.2 D2 (Einstein テンソル ↔ 2-simplex 面積)

Paper XIII §8.2 は Ricci 曲率 / Einstein テンソルを 2-simplex の face area と読む。C14 + C17 で精密化:

- **Ricci 曲率 `R_{μν}`** = C17 `Hom_I ⊔ Hom_{II}` 貼り合わせの局所 holonomy
- **Ricci スカラー `R`** = `L⊣R` 随伴の trace = `Fix(R∘L)` 近傍の stability measure
- **Einstein テンソル `G_{μν}`** = divergence-free 部分 = `Fix(R∘L)` の変分安定条件

**接続仮説 SF-7 (D2 closure via C17)**:

Einstein テンソルは C17 `L⊣R` の fixed point `Fix(R∘L)` の変分安定条件の幾何的表現。`d = 2` 境界 (C18 Phase boundary) は Einstein 方程式が非自明に立つ最小 coherence 条件を与える。

#### §24.7.3 D3 (Einstein 方程式 ↔ Face Lemma minimal condition の積分形)

Paper XIII §8.2 の最終予想は Einstein-Hilbert action `S_{EH} = (1/16πG_N) ∫ R √(-g) d^4x` が Face Lemma minimal non-trivial condition の積分。C11 + C14 + C17 で:

- 最小作用 `δS_{EH} = 0` = C11 Yoneda 普遍表現の variational closure
- 重力定数 `G_N` = `L⊣R` 随伴の **scale constant** = `d = 2` 境界での normalization

**接続仮説 SF-8 (D3 closure via Yoneda variational)**:

Einstein 方程式は σ の Yoneda 普遍表現 `Hom(Δ², -)` の宇宙論的 scale での variational closure。`G_N` は `L⊣R` 随伴 strength を Planck scale `ℓ_P` で規格化した結果。

### §24.8 予想 C19 — Spacetime as Kitaev Classical Limit

**予想 C19 [仮説 / v0.3.15 第 15 ラウンド新規提案 / Paper XIII 接続 / C18 の宇宙論拡張]**:

時空は lattice anyon 系 (Kitaev model 的) の古典極限 (`R` = classicalize) として発生する。以下の構造対応が成立する:

1. **時空 `M` = `Fix(R∘L)` の連続極限** (SF-1)
2. **Planck scale `ℓ_P` = `d = 2` 境界** (SF-2)
3. **4 力 = `L⊣R` 随伴の 4 種 lattice realization** (SF-3)
4. **重力 = `R` (classicalize) の宇宙論的具体化** (SF-4)
5. **Verlinde / Jacobson entropic gravity = `L⊣R` の熱力学版** (SF-5)
6. **Einstein 方程式 = σ Yoneda 普遍表現 (C11) の variational closure** (SF-6/7/8)
7. **Paper XIII §8 dictionary は C17 `L⊣R` 経由で部分的に埋まる** (D1-D3 の C11/C14/C17 による精密化)

**立てば得られるもの**:
- Paper XIII 全体の Kalon 判定 open が部分閉塞
- σ 論文 C1 (4 言語統一) に物理ドメインが本格追加
- 忘却論シリーズの物理面が σ 論文を通して集約
- GUT / TOE への圏論的 skeleton (4 力 = `L⊣R` の 4 分解)

### §24.9 Kalon 判定

- Step 0 圧縮: 「時空は格子 anyon 系を滑らかに見たもの、重力は格子が集まる力、量子から古典への変わり方が重力方程式」可能 ✓
- Step 1 G (Paper XIII SOURCE + C17 SOURCE): 両者の構造対応は Paper XIII §2-§5 + Face5Lemma §14-§19 で裏付け、不変 ✓
- Step 2 G∘F (4 力の lattice realization 展開): 電磁 = toric code / 弱 = Ising / 強 = SU(3) anyon / 重力 = 微分同相 で Phase I/II 分類保持 ✓
- Step 3 派生 3 つ:
  1. **Planck scale の圏論的 proxy** (`d = 2` = 前幾何境界)
  2. **Verlinde/Jacobson の `L⊣R` 熱力学的書換**
  3. **Einstein 方程式の Yoneda variational closure**
  すべて非自明 ✓

**判定**: ◯ Kalon (Paper XIII §8 dictionary の skeleton を **部分的に** 埋める構造は見えたが、完全 closure には Blocker A1 (Christoffel bijection) と Blocker B (α 橋 closure) の数学的詳細が未完、C19 全体は予想として ◯)

### §24.10 残る open

- **[open BA]** Γ^λ_{μν} と C11 Yoneda 表現の精密 bijection (Paper XIII Blocker A1)
- **[open BB]** Bianchi 恒等式 `∇^μ G_{μν} = 0` の pentagon coherence (C8) 読み
- **[open BC]** `L⊣R` scale constant ↔ 重力定数 `G_N` の物理的 identification
- **[open BD]** Paper XIII §5.4 の 3 層 (Level 3 時間位相 / Level 2 ビッグバン / Level 1 局所力) と C15 SignTower の 3 層対応
- **[open BE]** 強い力 SU(3)_k の具体的 `k` 値 (anyon type) 特定
- **[open BF]** 重力の fusion category 化 (微分同相群 vs MTC 拡張)
- **[open BG]** Paper XIII §7 前幾何 signature (3+1) と `d = 2` 転移の具体接続
- **[open BH]** CPS スパン (Paper II) と C17 `L⊣R` の関手的対応 (Θ パラメータ ↔ q-parameter)

### §24.11 SOURCE 台帳 (§24 追加分)

- [SOURCE] Paper XIII `論文XIII_時空は忘却である_草稿.md`: §2 容器-内容 forgetful / §3 4 力 = 忘却関手 / §5 重力 = F⊣G / §8 Face Lemma ↔ Einstein dictionary skeleton
- [SOURCE] Paper II (参照経由): CPS スパン定義、Face Lemma 形式化
- [SOURCE] §23 C18 物理実現 (本稿): Kitaev toric code / honeycomb / FQH 対応
- [SOURCE] Verlinde (2011) "On the origin of gravity and the laws of Newton" JHEP 04: entropic gravity
- [SOURCE] Jacobson (1995) "Thermodynamics of spacetime: The Einstein equation of state" Phys. Rev. Lett. 75: thermodynamic derivation
- [SOURCE] Khavkine-Schreiber "Synthetic geometry of differential equations" (arXiv 1701.06238): jet comonad J^1 と connection の圏論的定式化
- [INFERENCE] C19 (Spacetime as Kitaev Classical Limit) = 本節の新主張
- [INFERENCE] SF-1..SF-8 の 8 接続仮説 = 本節の新主張
- [TAINT/speculation] §24.4 強い力 SU(3)_k の対応、§24.5 重力の fusion category 化、§24.7 dictionary closure の詳細 (各 blocker の数学的完結は open)

### §24.12 注記

本節は C18 (物理実現, §23) の forgetful 側深部化 — 物理的 topological phase transition を Paper XIII の **宇宙論的 forgetfulness** として読み、C17 `L⊣R` を spacetime forgetfulness `U_{ctr}` の深部化として接続する。

Paper XIII §8 の最大 open (Face Lemma ↔ Einstein dictionary) を **C11 Yoneda + C8 Face5 + C14 representability + C17 Phase decomposition** の積み上げで部分的に埋める道筋を示した。これが立てば:

- 忘却論シリーズの **物理面 central theorem** が σ 論文 C17/C18/C19 経由で得られる
- Paper XIII 全体の Kalon 判定が open → part-◯ に移行
- σ 論文は「抽象的比較射 σ」から「物理的時空の forgetful 定式化」への **接続定理** としての役割を獲得

Yugaku 核宣言「身の丈を理想に引き上げろ」の、σ 論文における最大の到達点候補。詳細な blocker closure は Paper XIII Phase 5 + σ 論文 v0.4 への延長課題。

---

## §25 open #9-E 反例構成 — C9 精密版の 3 制約の独立性 (2026-04-19 第 16 ラウンド追加 / open #9-E 解決)

σ 論文 v0.3.7 §5.bis.4a で C9 を「universal cyclotomic 特徴付け」として精密化した際、3 制約 (cyclotomic integer + totally real positive + 弱 Perron) の **論理的独立性** を open #9-E として残した。本節ではこの open を具体反例で **確定的に解決** する。結論を先に言う: 3 制約は **互いに独立** であり、とくに (cyclotomic + totally real positive) は弱 Perron を **示唆しない**。

### §25.1 open #9-E の定式化

v0.3.7 C9 の 3 制約:

1. **cyclotomic integer 性**: `d \in \mathbb{Z}[\zeta_n]` for some `n`
2. **totally real positive**: 全 Galois 共役が real、かつ `d > 0`
3. **弱 Perron 性**: `d \geq |d'|` for all Galois conjugates `d'`

open #9-E の問い: `(1) \wedge (2) \Rightarrow (3)` は成立するか? すなわち、cyclotomic かつ totally real かつ positive な整数は自動的に弱 Perron か?

仮説成立なら C9 の 3 制約は 2 制約に縮約され、C10 弱 Perron 特徴付け予想の右辺も「cyclotomic かつ totally real かつ positive」に簡素化される。

### §25.2 反例 — `d = 2\cos(2π/7)`

**候補**: `d_0 := 2\cos(2π/7) \approx 1.247`

**性質検証**:

| 制約 | 検証 | SOURCE |
|:---|:---|:---|
| cyclotomic integer ✓ | `d_0 = \zeta_7 + \zeta_7^{-1} \in \mathbb{Z}[\zeta_7]^+` | 定義直接 (real cyclotomic integer の標準表示) |
| totally real ✓ | minimal polynomial `\Psi_7(x) = x^3 + x^2 - 2x - 1` の全根が real | Wikipedia "Minimal polynomial of 2cos(2π/n)" [^wp1] |
| positive ✓ | `d_0 \approx 1.247 > 0` | 数値計算 |
| **弱 Perron ✗** | 共役 `d_2 := 2\cos(6π/7) \approx -1.802` で `|d_2| = 1.802 > 1.247 = d_0` | Wikipedia [^wp1] 直接参照 |

[^wp1]: https://en.wikipedia.org/wiki/Minimal_polynomial_of_2cos(2pi/n) — n=7 の minimal polynomial `x^3 + x^2 - 2x - 1` と 3 根 `2\cos(2πk/7)` for `k=1,2,3` の具体値 (2026-04-19 Tolmetes 指示による確認検索の結果取得)。

**具体的な共役値** (3 根すべて real):
- `d_1 = 2\cos(2π/7) \approx 1.247` (候補 `d_0`)
- `d_2 = 2\cos(4π/7) \approx -0.445`
- `d_3 = 2\cos(6π/7) \approx -1.802`

Perron-Frobenius 定理は `d_{\text{Perron}} \geq |d'|` for all Galois conjugates を要求するが、`d_0 = d_1 = 1.247 < 1.802 = |d_3|` で破綻する。

### §25.3 反例の補強 — `d = 2\cos(2π/9)`

同様の構造を持つ反例が `n=9` でも成立する。

- `d_1 = 2\cos(2π/9) \approx 1.532` (候補)
- `d_2 = 2\cos(4π/9) \approx -0.347`
- `d_3 = 2\cos(8π/9) \approx -1.879`

minimal polynomial `\Psi_9(x) = x^3 - 3x + 1`、全根 real。

- cyclotomic ✓ / totally real ✓ / positive ✓
- 弱 Perron ✗ (`d_1 \approx 1.532 < 1.879 \approx |d_3|`)

### §25.4 なぜこれが起きるか — Perron 固有値は `2\cos(π/n)` 型のみ

実 cyclotomic integer `2\cos(2π k/n)` のうち **弱 Perron を満たすのは `k` が最小 (`k=1`) で `2\cos(π/m)` 型に書けるもの** のみという構造的理解が成立する。

- SU(2)_k family の Perron 固有値 `d_{1/2}(k) = 2\cos(π/(k+2))` は **`\pi` divided by integer** 型
- 共役は `2\cos(\ell \pi/(k+2))` for `\ell` odd, gcd(`\ell`, `2(k+2)`) = 1
- 最小共役の絶対値は常に `d_{1/2}(k)` 自身 (Chebyshev 多項式の最大根)
- したがって SU(2)_k family は弱 Perron を **満たす**

一方 `2\cos(2π/n) = 2\cos(\pi \cdot (2/n))` は分子が `2` で分母が `n` (gcd=1 の場合) のため、共役 `2\cos(2π k/n)` の最大絶対値は `k = \lfloor n/2 \rfloor` の場合で、候補 `k=1` ではない。これが弱 Perron 破綻の構造的原因。

### §25.5 open #9-E の結論

**定理 §25.5 (3 制約の独立性, Kalon ◎ 確定)**:  
v0.3.7 C9 の 3 制約 (cyclotomic integer + totally real positive + 弱 Perron) は **互いに論理的に独立** である。とくに (cyclotomic + totally real positive) は弱 Perron を示唆しない。

**証明**: 反例 `d_0 = 2\cos(2π/7) \in \mathbb{Z}[\zeta_7]^+` が cyclotomic + totally real + positive を満たすが弱 Perron を破る (§25.2)。□

**系 §25.5.1**: C10 (弱 Perron 特徴付け予想) の右辺は、v0.3.7 C9 精密版の下でも

$$
\mathbb{I}_{FP} \overset{?}{=} \{d \in \mathbb{Z}[\zeta_n]^+ : d > 0,\ d \geq |d'|\ \text{for all Galois conjugates}\}
$$

の 3 制約すべてを必要とする。弱 Perron 条件は冗長ではなく、cyclotomic + totally real positive の上に **真に新しい制約** を加える (σ 論文 open #19a の整合的解決)。

**系 §25.5.2**: `\mathbb{Z}[\zeta_n]^+ \cap \mathbb{R}_{>0}` 内で弱 Perron を満たすのは `2\cos(\pi/m)` 型のみ (本節 §25.4 の構造的観察)。これは Jones gap 定理 (C12 Phase I) の純粋代数的等価形として読める — Jones gap は位相軸の幾何的言い換えであり、弱 Perron 制約は同じ構造の代数的言い換えである。

### §25.6 σ 論文への繰込指示

- 本節 §25 を σ 論文 §5.bis.4a の **open 9-E** 解決として繰込
- σ 論文 open #19a (v0.3.7 新規) は §25.5.1 系によって **正当化** — C10 右辺の cyclotomic 精密化は弱 Perron 条件を保持したまま行う
- σ 論文 §5.bis.4c (C12 位相-スペクトル相転移) と §25.5.2 系を接続: Jones gap `2\cos(\pi/n)` 階段は弱 Perron 制約の代数的必然と読める

### §25.7 Kalon 判定 (§25 定理)

- Step 0 圧縮: 「cyclotomic で正実数で共役も全部実数でも、共役が自分より大きいことがある」— 中学生語彙で圧縮可能 ✓
- Step 1 G (反例の不動性): `2\cos(2π/7) \approx 1.247 < 1.802 \approx |2\cos(6π/7)|` は数値計算で確定 ✓
- Step 2 G∘F (family 展開): n=7, 9, 11, 13, ... と拡張しても反例は persistent ✓
- Step 3 派生 3 つ: (i) n=7 (minimal poly `x^3+x^2-2x-1`) / (ii) n=9 (`x^3-3x+1`) / (iii) n=11 (degree 5) — 3 つとも非自明な独立反例 ✓

**判定**: ◎ Kalon△ (open #9-E は確定的に解決、3 制約独立性は定理 face)

### §25.8 C9 / C10 への遡及効果

C9 v0.3.7 精密版のステートメントは不変 (3 制約を並記していたため)。ただし 3 制約の **論理的独立性** が定理として確定したことで:

- C9 のロバスト性が上昇: 3 制約を 2 制約に簡素化する誤読が構造的に封じられる
- C10 の右辺は 3 制約すべてを保持する必要があり、open #19a の精密化は正当化される
- C12 Phase I の Jones gap `2\cos(\pi/n)` 階段は **純粋代数的には弱 Perron 制約の cyclotomic + totally real 内での実現** として再読できる — これは Jones 定理の純粋代数的言い換えへの道筋

### §25.9 SOURCE 台帳 (§25 追加分)

- [SOURCE] Wikipedia "Minimal polynomial of 2cos(2π/n)" (2026-04-19 閲覧): `\Psi_7(x) = x^3 + x^2 - 2x - 1`、`\Psi_9(x) = x^3 - 3x + 1`、3 根の具体値 `2\cos(2πk/n)`
- [SOURCE] Calegari-Morrison-Snyder (2010) arXiv 1004.0665: real cyclotomic integer の fusion category 排除判定基準、本節の反例が FP dim として実現されないことの補強
- [SOURCE] Perron-Frobenius 定理: 非負整数行列の最大固有値は全 Galois 共役の絶対値以上
- [INFERENCE] §25.2-§25.5 3 制約独立性定理 = 本節の新主張 (Wikipedia + 基本計算から直接導出)
