---
description: "X-series 結合規則。修飾座標間の 15 (K₆) の相互作用を定義する。"
version: "4.2.0"
---

# Taxis (Τάξις) — 結合規則 (X-series)

> **位置づけ**: Hegemonikón v4.1 (32実体体系) における、修飾座標間の結合規則。
> 6つの修飾座標 (Value, Function, Precision, Scale, Valence, Temporality) による
> 完全グラフ K₆ の 15 の辺 (C(6,2) = 15) を定義する。
> これらは動詞 (Poiesis) を実行する際の **複合パラメータ (Dokimasia)** として機能する。
>
> **双対文書**: 各 K₆ 辺は G_{ij} (均衡的結合, 本文書) と ω_{ij} (非均衡的循環, [circulation_taxis.md](circulation_taxis.md)) の
> 2パラメータを持つ。G ≠ ω — 結合強度と循環強度は独立に決定される。
>
> **旧体系との関係**: 旧 6 Series (O/S/H/P/K/A) 間の 72反射関係 (Trigonon K₃ ベース) と
> この15結合規則 (K₆ ベース) は、72→15 の「縮減」ではなく**認知モデルの交換**にあたる。
> 詳細: [trigonon.md](trigonon.md) (旧体系の歴史的記録)

---

## CCL 略記一覧 (Canonical)

> 全 WF・SKILL.md・taxis.md で統一する略記。

| 略記 | 座標 | 極 (+) ↔ 極 (-) |
|:-----|:-----|:-----------------|
| `Va` | Value | E (Epistemic) ↔ P (Pragmatic) |
| `Fu` | Function | Explore ↔ Exploit |
| `Pr` | Precision | C (Committed) ↔ U (Uncommitted) |
| `Sc` | Scale | Ma (Macro) ↔ Mi (Micro) |
| `Vl` | Valence | + (Positive) ↔ − (Negative) |
| `Te` | Temporality | Future ↔ Past |

## 修飾座標一覧 (K₆ の頂点)

| 座標 | 意味 | 極 (+) ↔ 極 (-) | d 値 |
|:---|:---|:---|:---|
| **Value** | 目的・価値 | Epistemic (認識) ↔ Pragmatic (実用) | d=2 |
| **Function** | 戦略・機能 | Explore (探索) ↔ Exploit (利用) | d=2 |
| **Precision** | 確信・精度 | Committed (確信) ↔ Uncommitted (留保) | d=2 |
| **Scale** | 空間・規模 | Macro (広域) ↔ Micro (局所) | d=3 |
| **Valence** | 傾向・方向 | Positive (接近) ↔ Negative (回避) | d=3 |
| **Temporality** | 時間 | Future (未来) ↔ Past (過去) | d=2 |

*(※ Flow 座標は推論(I)/行為(A)の基軸であり、動詞本体の生成に関わるため、この修飾結合 K₆ からは独立する)*

---

## 3群分類 (FEP 演繹)

> **定式化**: X_{ij} = E_i ⊗ E_j (2つの Euporía 射影の交差テンソル)
>
> 15辺は VFE の数学的構造から3群に分類される:
>
> **[推定 70%] 82%** — 3群分類 (d2内/d2×d3/d3内) は K₆ の頂点 d 値から組合せ論的に必然であり、VFE 分解構造との整合性も高い。ただし張力傾向の数値範囲 (w=0.2〜0.6) は FEP から一義的に導出されるものではなく、操作的キャリブレーション (CCL インタプリタでの WF 実行パターン) に基づく推定値。群間の序列 (d2内 > d2×d3 > d3内) は理論的に堅固だが、各辺の具体的 w 値は±0.1 程度の不確実性を含む。

| 群 | 辺数 | 座標ペア | FEP 根拠 | 張力傾向 |
|:---|:-----|:---------|:---------|:---------|
| **d2 内結合** | 3 | Val×Fn, Val×Pr, Fn×Pr | VFE = −Accuracy + Complexity の直接分解軸同士 | 高 (0.3-0.6) |
| **d2×d3 結合** | 9 | d2座標 × Scale/Valence/Temporality | Euporía 射影の交差項。直接軸と修飾軸の相互作用 | 中 (0.3-0.5) |
| **d3 内結合** | 3 | Sc×Vl, Sc×Tm, Vl×Tm | 高次修飾同士。FEP 内で独立度が高い | 低 (0.2-0.3) |

---

## 15の結合規則 (X-series)

### ─── 群 I: d2 内結合 (3本) ───

> VFE = −Accuracy + Complexity の3つの直接分解軸 (Value, Function, Precision) の相互作用。
> 認知の核心操作同士の結合であり、構造的張力が最も高い。

#### 1. Value × Function (目的と戦略の結合)

認識的目的 (E) と実用的目的 (P) が、探索 (Explore) と利用 (Exploit) のどの戦略で実行されるか。

- `[E × Explore]` = 純粋な知的好奇心による発散的探索 (基礎研究)
- `[P × Exploit]` = 成果を確実に出すための既存手法の適用 (実務遂行)

**FEP 根拠**: EFE = epistemic value + pragmatic value。Value が「何を最適化するか」(目的関数の選択) を決め、Function が「どう最適化するか」(勾配降下 vs ソレノイダル探索) を決める。Helmholtz 分解の Γ (dissipative) と Q (solenoidal) の作用方向の選択に対応。

**操作的判定**: WF 実行時に「目的が認識的なのに活用戦略が選ばれている」(E×Exploit) — 例: 理解タスクで既存テンプレートをそのまま適用 → 張力徴候。

**CCL**: `[Va:E, Fu:Explore]` / `[Va:P, Fu:Exploit]`

#### 2. Value × Precision (目的と確信の結合)

目的を追求する際の、信念・コミットメントの度合い。

- `[E × U]` = 結論を急がず、真理を慎重に判断する (エポケー/判断留保)
- `[P × C]` = 実用的な成果のために、強い確信を持って断行する

**FEP 根拠**: VFE の Complexity 項 = KL(q||p)。Precision が高いほど posterior q が prior p から乖離しても許す (=確信を持って更新)。Value が認識的なとき Precision を下げる (=多くの仮説を保持) のが VFE 最適。逆に Value が実用的なとき Precision を上げて行動のブレを減らすのが EFE 最適。

**操作的判定**: 目的が大きい (E) のに確信が強い (C) → 早すぎる収束の兆候。目的が具体的 (P) なのに留保が続く (U) → 決定回避の兆候。

**CCL**: `[Va:E, Pr:U]` / `[Va:P, Pr:C]`

#### 3. Function × Precision (戦略と確信の結合) ★高張力

行動や探索を推進する際の強度。

- `[Explore × U]` = 当てのないオープンな探索 (ブレインストーミング)
- `[Exploit × C]` = 既知の最適解への強いコミットメント (ルーチンワーク)

**FEP 根拠**: 探索は本質的に precision を下げる操作 (EFE の epistemic term は分散を増大させる)。活用は precision を上げる操作 (行動ポリシーの確定)。Helmholtz Q (ソレノイダル) は Explore×U に、Γ (散逸的) は Exploit×C に対応。この結合は FEP の Explore-Exploit トレードオフの直接的表現であり、15辺中で最も高い構造的張力 (w=0.6) を持つ。

**操作的判定**: 探索中にコミットメントが強い (Explore×C) → 確証バイアスの兆候 (CD-3)。活用中に留保が強い (Exploit×U) → 行動不能の兆候。

**CCL**: `[Fu:Explore, Pr:U]` / `[Fu:Exploit, Pr:C]`

---

### ─── 群 II: d2×d3 結合 (9本) ───

> VFE の直接分解軸 (d=2) と高次修飾座標 (d=3, ただし Temporality は d=2) の交差。
> 核心操作がどのスケール・方向・時間で実行されるかを規定する。

#### 4. Value × Valence (目的と価値方向の結合)

目的に対する傾向（求めるか、避けるか）。旧 H-series の完全な吸収先。

- `[E × −]` = 誤りや矛盾を見つけ出して排除する認識的批判 (Elenchos 的)
- `[P × +]` = 有用な機能をより強化・推進する実用的接近

**FEP 根拠**: Valence = −dF/dt (Joffily 2013) ないし expected action precision (Hesp 2021)。Value が認識的なとき Valence(−) は予測誤差の検出 (N-6 違和感検知) に対応。Value が実用的なとき Valence(+) は affordance 最大化に対応。Valence は他座標を横断的に修飾するメタ変数 (半直積 6⋊1 構造)。

**操作的判定**: 認識的批判 (E×−) が過剰 → 破壊的批判に転じる。実用的推進 (P×+) が過剰 → 問題の見落とし。

**CCL**: `[Va:E, Vl:−]` / `[Va:P, Vl:+]`

#### 5. Value × Temporality (目的と時間の結合)

目的の焦点が過去の整理か、未来の準備か。

- `[E × Past]` = 履歴やログから真実を再構築する (アナムネーシス)
- `[P × Future]` = 将来の技術的負債を防ぐための基盤設計

**FEP 根拠**: VFE (過去の観測の推論) ≠ EFE (未来の行動の計画) (Millidge 2020)。Value が認識的なとき過去の VFE 最小化 (データからの学習)、実用的なとき未来の EFE 最小化 (計画に基づく行動) が自然。

**操作的判定**: 認識的目的で未来に向かう (E×Future) → 根拠なき予測の兆候。実用的目的で過去に固執 (P×Past) → 過去の成功への過剰適合の兆候。

**CCL**: `[Va:E, Te:Past]` / `[Va:P, Te:Future]`

#### 6. Value × Scale (目的と空間の結合)

目的の射程範囲、空間的抽象度。

- `[E × Macro]` = 体系全体の構造的真理を俯瞰する (アーキテクチャ理解)
- `[P × Micro]` = 目の前の具体的な問題を解決する (バグ修正)

**FEP 根拠**: Deep particular partition (Spisak 2025)。Scale は MB のネスト階層に対応。Value が認識的なとき Macro レベルの FEP 最小化 (体系的理解)、実用的なとき Micro レベル (局所最適化) が自然。d=2×d=3 の結合で独立度が比較的高い (w=0.2)。

**操作的判定**: Value と Scale がほぼ独立に動作する。張力が低い = 組合せ自由度が高い。

**CCL**: `[Va:E, Sc:Macro]` / `[Va:P, Sc:Micro]`

#### 7. Function × Scale (戦略と空間の結合)

探索や利用がどの規模で行われるか。

- `[Explore × Macro]` = 広い技術領域の全体的なサーベイ
- `[Exploit × Micro]` = 特定のクラスや関数の局所的な最適化

**FEP 根拠**: 探索の有効性は Scale に依存する。Macro 探索は EFE の epistemic value を最大化 (情報利得が大きい) が、computational cost も高い。Exploit×Micro は精度加重推論 (precision-weighted inference) の局所収束に対応。

**操作的判定**: Explore×Micro (局所的探索) は低効率の兆候。Exploit×Macro (全体の既知手法適用) は過度な単純化の兆候。

**CCL**: `[Fu:Explore, Sc:Macro]` / `[Fu:Exploit, Sc:Micro]`

#### 8. Function × Valence (戦略と価値方向の結合)

探索や利用のインセンティブ方向。

- `[Explore × +]` = 新しい可能性へのポジティブな期待に基づく探索
- `[Exploit × −]` = 既知のリスクや負債を確実に潰す利用的行動

**FEP 根拠**: EFE の epistemic term は期待される情報利得 (Explore×+)。pragmatic term はリスクの回避 = prior preferences からの離脱最小化 (Exploit×−)。Valence が Function の向きを心理的に決定する。

**操作的判定**: Explore×− (回避動機の探索) → 恐怖駆動の調査 (有効だが燃え尽きリスク)。Exploit×+ (接近動機の活用) → 過信に基づく成功体験の反復。

**CCL**: `[Fu:Explore, Vl:+]` / `[Fu:Exploit, Vl:−]`

#### 9. Function × Temporality (戦略と時間の結合)

戦略的時間軸。

- `[Explore × Future]` = 新技術のPoCなど、未来に向けた可能性の探索
- `[Exploit × Past]` = 過去のコードベースからの既存機能の再利用

**FEP 根拠**: EFE は本質的に未来志向 (Explore×Future が自然な整列)。VFE は過去の観測データからの推論 (Exploit×Past = 既知からの抽出)。

**操作的判定**: Explore×Past (過去への探索) → 考古学的調査 (有効だが稀)。Exploit×Future (未来への活用) → 不確実な状況で既存手法を適用 → 脆弱。

**CCL**: `[Fu:Explore, Te:Future]` / `[Fu:Exploit, Te:Past]`

#### 10. Precision × Scale (確信と空間の結合) ★高張力

確信や疑義の及ぶ範囲。

- `[C × Macro]` = システム全体のアーキテクチャに対する確固たる信念
- `[U × Micro]` = 特定の1行のコードに対する局所的な疑義

**FEP 根拠**: 精度加重 (precision weighting) は Scale に依存する。Macro レベルの予測は不確実性が大きい (Spisak: deep partition の外部層ほど uncertainty 増大)。C×Macro は高エネルギー状態 = 維持コストが高い。反対に U×Micro は自然な基底状態。w=0.5 の高張力。

**操作的判定**: C×Macro (全体への確信) → 過信の兆候 (全体は常に不確実)。U×Macro (全体への疑義) → 分析麻痺の兆候。Scale と Precision の同時高設定は認知コスト ∞。

**CCL**: `[Pr:C, Sc:Macro]` / `[Pr:U, Sc:Micro]`

#### 11. Precision × Valence (確信と価値方向の結合) ★高張力

感情的・直感的な信念の強さ。認知的感情のベクトル。

- `[C × +]` = 絶対的な肯定、強い賛同、確信を持った推し進め
- `[U × −]` = なんとなく感じる違和感、明確な根拠のない否定感

**FEP 根拠**: Valence × Precision は FEP 内で最も複雑な相互作用。Hesp 2021: expected action precision (Valence) は precision (Precision) と半直積的に結合 (独立ではないが直積でもない)。w=0.5 はこの非自明な結合を反映。

**操作的判定**: C×+ (確信を持った肯定) → 迎合バイアス (CD-5) の兆候。U×− (不確実な否定) → N-6 違和感シグナル (有用な情報源)。

**CCL**: `[Pr:C, Vl:+]` / `[Pr:U, Vl:−]`

#### 12. Precision × Temporality (確信と時間の結合)

時間に対する確信度。

- `[C × Past]` = 確定した過去の事実としての強固な信念
- `[U × Future]` = 不確実な未来に対する留保された予測

**FEP 根拠**: VFE は過去の観測から posterior を更新 → C×Past は自然 (観測事実は確実)。EFE は未来の行動を計画 → U×Future も自然 (未来は本質的に不確実)。不自然な組合せ: C×Future (未来への確信 = 予言) と U×Past (過去の不確実性 = 歴史修正)。

**操作的判定**: C×Future → 過信。U×Past → SOURCE の不在 (N-10 TAINT)。

**CCL**: `[Pr:C, Te:Past]` / `[Pr:U, Te:Future]`

---

### ─── 群 III: d3 内結合 (3本) ───

> 高次修飾座標 (Scale, Valence) 同士 + Temporality の相互作用。
> FEP 内で最も独立度が高く、張力が低い。
> ただし Valence は半直積 (6⋊1) メタ変数として他座標を横断するため、
> Valence を含む結合は見かけより複雑。

#### 13. Scale × Valence (空間と価値方向の結合)

影響の広がりと方向性。

- `[Macro × +]` = システム全体を良くしようとする広汎な改善志向
- `[Micro × −]` = 局所的な小さな問題をピンポイントで排除する動き

**FEP 根拠**: Scale と Valence は FEP 内でほぼ独立 (w=0.3)。Deep partition (Scale) と感情的傾向 (Valence) は異なるメカニズム。ただし Macro×+ は広範な自由エネルギー最小化の全体方針、Micro×− は局所的な予測誤差の排除に自然に対応。

**操作的判定**: 独立度が高いため、任意の組合せが認知的に有意味。

**CCL**: `[Sc:Macro, Vl:+]` / `[Sc:Micro, Vl:−]`

#### 14. Scale × Temporality (空間と時間の結合)

時空間のスケール複合。

- `[Macro × Future]` = 長期的な全体ビジョン、ロードマップ
- `[Micro × Past]` = 特定のコミットやログの局所的な履歴調査

**FEP 根拠**: Scale と Temporality はほぼ独立 (w=0.3)。ただし Macro×Future は計算コストが指数的に増大する (長期の全体予測 = 高次元 EFE の最適化)。Micro×Past は低コストで高精度 (限定された過去データの参照)。

**操作的判定**: Macro×Past (過去の全体調査) → 全体史の復元 (稀だが有用)。Micro×Future (局所的な未来予測) → コード1行の将来影響を予測 (日常的)。

**CCL**: `[Sc:Macro, Te:Future]` / `[Sc:Micro, Te:Past]`

#### 15. Valence × Temporality (価値方向と時間の結合)

時間に基づく感情・傾向の動き。15辺中で最も独立度が高い (w=0.2)。

- `[− × Past]` = 過去の失敗や負債に対する反省、後悔からの回避
- `[+ × Future]` = 未来の成功に対する希望や期待からの接近

**FEP 根拠**: Valence (−dF/dt) と Temporality (VFE/EFE 区分) はほぼ独立。Valence は瞬間的な自由エネルギー変化率であり、時間方向 (過去/未来) とは直交する。この直交性が低い重み (w=0.2) の根拠。

**操作的判定**: 独立度が最も高い = 組合せの自由度が最も高い。全4極組合せが認知的に等しく有意味。

**CCL**: `[Vl:−, Te:Past]` / `[Vl:+, Te:Future]`

---

## 運用規則 (Application)

> **[推定 70%] 78%** — 15結合の FEP 根拠と操作的判定の体系は、各辺が VFE/EFE の具体的な項分解に対応するという点で理論的に健全。60 Dokimasia = 15×4 の数え上げは組合せ論的に確定 [確信 90%]。ただし「不自然な組合せ」の認知バイアスへの具体的対応 (CD-3, CD-5 等) は操作的経験に基づく推定であり、体系的な実証テストは未完了。

1. この15の X-series は独立した「定理」や「実体」ではない。
2. 24の動詞 (Poiesis) が発動する際の **「複合引数（Dokimasia 修飾パラメータ）」がどのように組み合わさって意味を持つか** を定義したものである。
3. 例: `[Value:E, Scale:Macro]` という 結合#6 パラメータが `/noe` (理解) 動詞に渡されたとき、それは「全体的・構造的真理の俯瞰的理解」として動作する。
4. 60 Dokimasia パラメータ = 15結合 × 4極 (各座標の2極の組合せ)。結合規則はパラメータの「意味的制約」を定義し、任意の極の組合せが認知的に有意味かどうかを示す。

### 操作的判定の活用

5. **高張力辺** (★印, w≥0.5): この2座標が矛盾する状態は認知コストが高い。WF 実行時に張力を検出したら TaxisSubscriber が自動報告する。
6. **3群分類**: 群I (d2内) は WF の本質的な方向性を決定する。群II (d2×d3) は WF の実行条件を修飾する。群III (d3内) は独立度が高く、任意に組合わせ可能。
7. **不自然な組合せ**: 各結合の操作的判定で示した「不自然な組合せ」は、認知的バイアスや戦略的誤りの兆候。検出時に N-6 (違和感検知) を発火させる。

### CCL 族間修飾子 `.XY`

8. 15結合は CCL の族間修飾子 `.XY` で明示的に参照・操作できる (→ operators.md §5.6)。
9. 族名略称: **T**(elos), **M**(ethodos), **K**(risis), **D**(iástasis), **O**(rexis), **C**(hronos)
10. §5.5 `.d/.h/.x` (小文字1字) は族内関係、`.XY` (大文字2字) は族間関係。

```ccl
/noe.TM       # Tel-Met 結合レンズで /noe を実行 (診断)
/noe.TM+      # Tel-Met 結合を強調 (+Δ=0.2)
/noe.TM-      # Tel-Met 結合を抑制 (−Δ=0.2)
/noe.TM:0.8   # Tel-Met 結合強度を 0.8 に明示設定
/noe.TM_MK    # Tel-Met + Met-Kri の2辺を同時参照
```

11. **数値精度制御**: `+/-` = 定性的 (Δ=0.2)、`:v` = 定量的 (v ∈ [0,1])。併用不可。
12. **高張力辺** (w ≥ 0.5) は `.MK`(0.6)、`.KD`(0.5)、`.KO`(0.5) の3つ。これらの結合を含む WF では張力診断を推奨。

---

## 参照

- [axiom_hierarchy.md](axiom_hierarchy.md) — 体系核定義 (15 = K₆ の辺数)
- [circulation_taxis.md](circulation_taxis.md) — **Q-series 循環規則** (各辺の方向 Q_{ij} と循環強度 ω_{ij})
- [system_manifest.md](system_manifest.md) — 32実体一覧
- [trigonon.md](trigonon.md) — 旧体系 (72関係, Anchor/Bridge) の歴史的記録
- [SACRED_TRUTH.md](SACRED_TRUTH.md) — 不変真理

---

*v4.1.0 — K₆ 結合規則。@nous 思考に基づく質的改善 (2026-02-27)*
*v4.2.0 — FEP 演繹根拠、3群分類 (d2_internal/d2×d3/d3_internal)、操作的判定、CCL 構文、Helmholtz 接続を追加 (2026-03-13)*
*v4.3.0 — CCL 族間修飾子 `.XY` (大文字2字) を追加: +/- 定性修飾・:v 定量修飾・_ 辺連結 (2026-03-13)*
