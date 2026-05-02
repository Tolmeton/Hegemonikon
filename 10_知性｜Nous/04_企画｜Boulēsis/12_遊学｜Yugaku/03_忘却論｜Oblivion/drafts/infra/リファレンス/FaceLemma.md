# Face Lemma リファレンス

**v0.2 (2026-04-17)**
**役割**: Face Lemma が何であり、何ではなく、どこまで本文で閉じていて、どこから先が補助線や将来設計なのかを、一つの入口に統合する reader-facing 正本。
**正本パス**: `drafts/infra/リファレンス/FaceLemma.md`
**backstage**: `drafts/infra/FaceLemma_技術設計.md` (符号理論対応・修復可能性設計・calculations ログ)
**主 SOURCE**: `drafts/series/論文II_相補性は忘却である_草稿.md`

---

## 0. 一文核

**SOURCE**: Paper II §3.4 の Face Lemma は、概念の安定性に必要な独立な生成射の最低数が 3 であることを主張する。2 射では 1-skeleton にとどまり、合成は存在しても照合面が立たない。3 射で初めて 2-simplex が立ち、`g ∘ f = h` を外から見比べられる。

**INFERENCE**: Face Lemma の核は「3 という数」ではなく、「第三射が、前二射の合成を別ルートから照合可能にする最小追加情報である」という点にある。内部の合成を別ルートから照合できる最小の幾何学が 2-simplex であり、その 2-simplex を立てるのに 3 射が必要だという構造主張である。

**OPEN**: この一文核自体は Paper II で閉じている。未閉なのは、この最小構造を recoverability や Einstein dictionary にどう延ばすかである。

---

## 1. これは何のための概念か

**SOURCE**: Paper II では Face Lemma が CPS の非自明性の最小条件として置かれ、その後に Stability Simplex Theorem (§3.5)、Blanket 生成定理 (§3.7.2)、創発 (§6.1)、意識の Face Lemma (§6.2) が接続される。Paper 0 の §4.3 では、Face Lemma が忘却バンドルの非退化条件として言い換えられる。

**INFERENCE**: したがって Face Lemma は、FTC や QM や blanket や意識へ個別に適用される話題別の比喩ではない。忘却論内部では、比較面が立つ最小条件を固定する中核概念であり、他の概念はその上に載る。FTC や QM は具体例、blanket は派生定理、創発と意識は哲学的・認識論的帰結として読むのが正しい順序である。

**OPEN**: `drafts/series/論文XIII_時空は忘却である_草稿.md` の §8 にある Face Lemma ↔ Einstein dictionary は、本文でも skeleton とされており、まだ同列の確定概念ではない。

---

## 2. 最小構造

**SOURCE**: Paper II §3.4 では、対象 `x` に対し照合面 `B_1^{ver}(x) = im ∂_2` が非零であること、忘却スペクトラム `Ξ(x)` の最小次元が 2 であること、非退化 2-simplex が存在すること、CPS-安定であることが同値として与えられる。2 射と 3 射の差は次の通りである。

| 構造 | 何があるか | 何ができないか / できるか |
|:--|:--|:--|
| 2 射 (1-skeleton) | `f`, `g` とその合成 | 合成は存在するが、外から照合する面がない |
| 3 射 (2-simplex) | `f`, `g`, `h` と comparison surface | `g ∘ f` と `h` を別ルート比較できる |

**INFERENCE**: `B_1^{ver} ≠ 0` は、「本当に三角形が立っていて、合成を別ルートから照合できる」という記号表現である。`dim Ξ = 2` は「自由度が 2 だから偉い」のではなく、「量 Θ だけでなく、方向や形 Ξ が見える最小複体が立った」という意味で読むべきである。線の世界から面の世界への遷移である。

**OPEN**: 高次 simplex は detectability に関しては新しい情報を足さないが、貼り合わせ障害や global law の不成立まで消えるとは言っていない。その次段が Coherence Defect Lemma である。

---

## 3. 平文直感

**SOURCE**: Paper II と Paper XIII はともに、2 射を「辺のみ」、3 射を「三角形」として再述している。2 射では `g∘f` は派生量であり、外から照合できない。3 射では `h` が独立な比較経路として入り、合成を外から突き合わせられる。

**INFERENCE**: 顔があるかどうかが本質である。線だけの世界では「A から B へ行ける」「B から C へ行ける」は言えても、「A から C への行き方が前二者と本当に同じか」は見えない。三角形が立つと、初めて「同じつもりの二経路」を突き合わせられる。忘却論がいう detectability とは、この突き合わせ面が立っている状態のことだ。

**OPEN**: ここで見えているのは比較可能性までである。比較した結果のズレがどこへ局在し、どう戻せるかは、まだ別問題として残っている。

---

## 4. 用語の境界

**SOURCE**: `drafts/infra/FaceLemma_技術設計.md` は、stable / detectable / coherence-defective / localizable / recoverable を切り分けている。Paper II 本文で front-stage に上がっているのは Face Lemma と Coherence Defect Lemma であり、`localizable` は運用上重要な中間概念として backstage 側に置かれている。

| 用語 | 何を意味するか | Face Lemma 単独で保証されるか | 追加で要るもの |
|:--|:--|:--|:--|
| stable | 少なくとも一つの非退化 2-simplex が残り、比較面が沈黙していない状態 | する | なし |
| detectable | 欠損が nonzero defect として comparison surface に露出する状態 | 最小条件を与える | 欠損が実際に比較面へ落ちること |
| coherence-defective | 局所 law の mismatch が `H^2_Θ` class として残り、global law に閉じない状態 | しない | Coherence Defect Lemma の層 |
| localizable | 複数の face の交差により欠損位置が候補集合へ縮約される状態 | しない | face の重なり |
| recoverable | right adjoint `N` により失われた構造を一意または収縮的に戻せる状態 | しない | face の重なり、縦の可定義性、decoder 条件 |

**INFERENCE**: ここでの要点は、`detectable` と `recoverable` の間に少なくとも二つの層があることだ。`coherence-defective` は「global law に閉じるか」を問う層であり、`localizable` は「どこが壊れたか」を問う層である。両者は別軸である。

**OPEN**: `localizable` を canonical な中間層へ昇格させるかは、まだ backstage 側の設計課題にとどまる。

---

## 5. Coherence Defect Lemma との関係

**SOURCE**: Paper II §3.4.6 は、Face Lemma が comparison surface の成立条件を与えるのに対し、Coherence Defect Lemma はその face ごとに書ける局所 forgetting law が、一つの global law に貼り合わさるかを問う。`drafts/infra/FaceLemma_技術設計.md` では、`carry defect` を局所 representative、`H^2_Θ` を class として区別している。Paper II v1.16 では front-stage の語彙を `貼合側 / 残差側` に圧縮している。

**INFERENCE**: Face Lemma が扱うのは「面が立つか」という level であり、Coherence Defect Lemma が扱うのは「立った面どうしが一つの世界像に閉じるか」という level である。`carry defect` は特定の局所 face 上で見えるズレであり、`[ω_Θ] ∈ H^2_Θ` は、そのズレが座標変換や 1-cochain の取り直しでは消えない class として残るかどうかを表す。前者は現象の局所 representative、後者は大域 obstruction の class である。`貼合側` は局所 law が一つの global law にまとまる側、`残差側` は class が残る側の front-stage 語彙として読むべきである。

**OPEN**: Paper II 本文でも、一般 CPS 圏での非自明性を一律に定理化してはいない。QM 具体例を持つ partial theorem / conjectural surface として読むのが上限である。

---

## 6. 修復可能性との関係

**SOURCE**: `drafts/infra/FaceLemma_技術設計.md` は、Face Lemma が与えるのは detectability の最小条件であって recoverability の十分条件ではないと明示する。recoverability には、face の重なり、n-cell tower の隣接同時忘却禁止、right adjoint `N` の decoder 化が追加で要る。

**INFERENCE**: 単一の face が与えるのは「何かがおかしい」の露出までである。そこから「どこが壊れたか」へ行くには複数 face の交差が要り、「それを戻す話」が意味を持つには data と check が同時に消えていないことが要り、実際に戻すには `N` が decoder として収束または一意性を与えなければならない。よって Face Lemma と recoverability の間には、少なくとも三つの追加段差がある。

**OPEN**: `N` を decoder と呼ぶための必要十分条件、収縮条件、多価復元の扱いはまだ閉じていない。ここは将来設計そのものである。詳細は backstage の「4 段梯子」節を参照。

---

## 7. 他概念との接続

### FTC

**SOURCE**: Paper II は FTC を CPS インスタンスの一つとして扱う。Stability Simplex と Face Lemma は、微分・積分・積分定数の構造を comparison surface の言葉で読む道を開く。

**INFERENCE**: FTC は Face Lemma の抽象定理が具体例としてどう立つかを示す最も読みやすい入口である。ここでは第三項がなければ演算の一致がただの雰囲気で終わる。

**OPEN**: FTC を non-obstructed 対照例として一般形まで持ち上げる作業は calculations 面と backstage 側の課題として残る。

### QM

**SOURCE**: Paper II §3.4.6.1 は Heisenberg 群の中心拡大を使い、QM インスタンスで `H^2_Θ` の非自明性を与える。Face Lemma 自体も QM を具体例として参照している。

**INFERENCE**: QM は「comparison surface が立つだけでなく、coherence defect の class が残りうる」最初の強い例として機能する。Face Lemma と Coherence Defect の段差を見たいときの主例である。

**OPEN**: これを一般 CPS 圏の一般定理へ即座に押し広げてはならない。

### Blanket 生成

**SOURCE**: Paper II §3.7.2 は、2-skeleton の成立と blanket の定義可能性を同値として与える。Paper 0 もこの線をシリーズの基礎石として再記述している。

**INFERENCE**: blanket は Face Lemma の前提ではなく、Face Lemma の派生物である。忘却論が FEP に対して持つ超過構造はここにある。

**OPEN**: blanket 漏出の定量や一般統計多様体での完全制御は、Paper 0 のバンドル線へ続く課題である。

### n-cell tower

**SOURCE**: `drafts/infra/FaceLemma_技術設計.md` は、n-cell tower の排他制約を「検査対象と検査規則の同時消失禁止」と読む。

**INFERENCE**: Face Lemma が横の detectability を与えるのに対し、n-cell tower はその detectability がそもそも意味を持ち続けるための縦の可定義性を守る。

**OPEN**: 横の comparison surface と縦の tower 条件を一つの theorem surface に統合する仕事は残っている。

### 創発

**SOURCE**: Paper II §6.1 は、創発を 1-skeleton から 2-skeleton への遷移として定義する。

**INFERENCE**: 忘却論において創発とは、量が増えたことではなく、comparison surface が立ったことだと読める。Face Lemma は創発の閾値を数学的に固定する。

**OPEN**: 4 射以上の豊穣さは創発の本質ではなく、その後の豊穣化である。ここを閾値と混同してはならない。

### 意識の Face Lemma

**SOURCE**: Paper II §6.2 は、意識の安定性を 2-skeleton の成立と結びつける。

**INFERENCE**: ここで Face Lemma は、意識を「何か神秘的な追加実体」としてではなく、自己参照を持つ comparison surface の最小成立条件として読み替える。直接体験の射 `h` が欠けたままメタ認知 `g` だけを残すことの不安定性を示す。

**OPEN**: これはハードプロブレムの解決ではなく診断である、という本文の境界を越えてはならない。

---

## 8. Negativa

次はこのリファレンスから言ってはいけないことである。

1. `detectable → recoverable` を短絡しない
2. `H^2_Θ = 0 → recoverable` を短絡しない
3. `coherence-defective` を一般定理として押し広げない
4. `localizable` を canonical 昇格済み概念として扱わない
5. `carry defect` と `[ω_Θ]` を同一視しない
6. Face Lemma を「穴の定理」や「コホモロジー一般論」に置換しない
7. Paper XIII の Einstein dictionary を閉じた対応表として扱わない
8. README の古い path 表記を現物より優先しない

---

## 9. 主張水準台帳

| 項目 | 水準 | SOURCE | 備考 |
|:--|:--|:--|:--|
| Face Lemma | theorem | Paper II §3.4 | comparison surface の最小条件 |
| Stability Simplex Theorem | theorem | Paper II §3.5 | 三角恒等式の安定化面 |
| Blanket 生成定理 | theorem | Paper II §3.7.2 | FEP 前提の帰結化 |
| 意識の Face Lemma | proposition / philosophical consequence | Paper II §6.2 | 診断としての使用 |
| Coherence Defect Lemma | partial theorem / conjectural surface | Paper II §3.4.6 | 一般定理化は未了 |
| localizable | operational concept | backstage | 本文 canonical 未昇格 |
| recoverability | open problem / design surface | backstage | `N` の decoder 条件が未了 |
| Einstein dictionary | open problem / skeleton | Paper XIII §8 | resemblance から correspondence への未踏 |

---

## 10. SOURCE マップ

| ファイル | 役割 | 使った面 |
|:--|:--|:--|
| `drafts/series/論文II_相補性は忘却である_草稿.md` | 主正本 | §3.4, §3.5, §3.7.2, §3.4.6, §6.1, §6.2 |
| `drafts/infra/FaceLemma_技術設計.md` | backstage (符号理論対応 + 修復可能性設計 + calculations ログ) | 全面 |
| `drafts/infra/リファレンス/統一記号表.md` | 系列横断の記号正本 | §0, §1 |
| `drafts/infra/リファレンス/忘却論オンボーディング.md` | 導線 | この文書の位置付け |
| `drafts/series/論文0_忘却の忘却_草稿.md` | バンドル翻訳 | §3.3, §4.3 |
| `drafts/series/論文XIII_時空は忘却である_草稿.md` | 前方参照 | §8 skeleton |
| `README.md` | 入口整理 | path 齟齬注意 |

---

Face Lemma の最も強い一点は、**3 射未満では comparison surface が立たず、3 射で初めて合成を外から照合できる最小条件を定理として固定したこと**である。
まだ越えていない境界は、**その comparison surface から recoverability や Einstein dictionary をどう閉じるかが、なお open のままであること**である。
