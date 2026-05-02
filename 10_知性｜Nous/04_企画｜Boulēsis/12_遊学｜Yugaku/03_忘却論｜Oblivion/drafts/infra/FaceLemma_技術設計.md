# Face Lemma 技術設計 (backstage)

**v0.2 (2026-04-17)**
**役割**: Face Lemma / Coherence Defect Lemma を、符号理論の語彙で再読し、そこから recoverability までを忘却論の内部語彙で延ばすための共通正本。
**目的**: 「安定」「検出可能」「整合欠損的」「修復可能」を曖昧な形容ではなく、忘却論内部の冗長性条件として再定義し、detectability から recoverability への段差を飛躍ではなく段階差として固定する。
**canonical surface**: 2026-04-14 現在、Coherence Defect Lemma の主表示は chain 側の `H_2^{coh}` ではなく、cochain 側の `H^2_{\Theta}` に置く。
**reader-facing**: `drafts/infra/リファレンス/FaceLemma.md`

---

## 0. 一文核

Face Lemma は **圏論版 syndrome 条件** であり、Coherence Defect Lemma は **局所 forgetting law の大域持ち上げ障害** を測る次段補題である。`carry defect` はその局所 representative、`H^2_{\Theta}` は座標変換で消えない class として読む。

Face Lemma は **最小の syndrome 面** を与えるが、修復可能性はそれだけでは立たない。修復可能性が立つには、**face の重なり**、**縦の可定義性の維持**、**右随伴 `N` の decoder 化** が追加で要る。

---

# 第 I 部: 符号理論対応

## 1. 二つの軸

忘却論では、誤り検出構造を少なくとも二つの軸に分けて見なければならない。

| 軸 | 忘却論で見ているもの | 符号理論での直感 |
|:---|:---|:---|
| **横** | 同一階層の中で別ルート比較ができるか | syndrome / parity check |
| **縦** | その比較機構がそもそも定義可能か | data bit と check bit の同時消失禁止 |

Face Lemma は主に横軸の最小条件を与える。
Coherence Defect Lemma は、その横軸で立った複数の比較面に書かれた局所法則が、**大域的に一つの law へ貼り合わさるか** を測る。
n-cell tower の排他制約は、これらの検査機構が意味を失わないための縦条件を与える。

---

## 2. Hamming / LDPC / Face Lemma / Coherence Defect Lemma / n-cell tower 対応表

| 観点 | Hamming | LDPC | Face Lemma | Coherence Defect Lemma | n-cell tower |
|:---|:---|:---|:---|:---|:---|
| **主役** | 少数のパリティ検査式 | 疎な多数の検査式ネットワーク | 3射が閉じる 2-simplex | 局所 forgetting law の 2-cocycle class | $U_n$ 系列の縦依存 |
| **冗長性の担体** | 検査ビット | Tanner graph 的な多重拘束 | 第3の射 $h$ | `carry defect` とその class $H^2_{\Theta}$ | 下位層を前提に上位層が立つこと |
| **何を比べるか** | 受信語と検査式 | 局所整合の束 | $g \circ f$ と $h$ | 局所 law が大域 1-cochain に吸収されるか | $U_n$ が消した対象を $U_{n+1}$ が必要とするか |
| **検出信号** | syndrome $\neq 0$ | unsatisfied checks | 合成ドリフト / carry defect / 曲率 | non-trivial coherence-defect class $[\omega_{\Theta}] \in H^2_{\Theta} \neq 0$ | 上位検査の定義域消失、または欠損の露出 |
| **主な果実** | 局所検出 | 分散局在化と反復修正 | 最小 detectability | structural non-globalizability / topological residual | 検査機構の可定義性 |
| **壊れ方** | 検査ビットも失うと silent error | trapping set / check erasure | 2射に退化すると方向が見えない | face ごとの law はあるが一つの global law に閉じない | $U_n$ と $U_{n+1}$ が同時活性だと定義不能 |
| **位置づけ** | 最小の誤り検出模型 | 分散拘束模型 | 最小の構造検出模型 | 最小の整合欠損測度 | 検出模型の存在条件 |

---

## 3. なぜ Hamming より LDPC に近いか

Hamming は Face Lemma の局所模型として非常に良い。
だが忘却論が必要とするのは、単一の三角形ではなく、**複数の face が重なったときに何が起こるか** である。

したがって対応は次のように読むのが自然である。

- **Hamming** = Face Lemma の最小検出模型
- **LDPC** = 多数の Face Lemma を貼り合わせた分散拘束模型
- **Coherence Defect Lemma** = その貼り合わせが一つの global law に閉じるのか、obstruction / topological residual を残すのかを分ける補題
- **n-cell tower** = それらの検査面が意味を持つための縦の依存台帳

重要なのは、LDPC 類比の果実を repair 一辺倒で読まないことである。
比較面が多いほど復元しやすくなることもあるが、逆に **局所 law の束だけが残って global law に閉じない** なら、それは修復の入口ではなく障害物である。

---

## 4. 四概念の再定義

### 4.1 安定 `stable`

忘却論において安定とは、

> **部分忘却の後でも、縦に定義可能性が残り、横に少なくとも一つの非退化 2-simplex が残る状態**

である。「壊れない」という意味ではない。むしろ「壊れてもまだ比較面が残る」という意味である。

### 4.2 検出可能 `detectable`

検出可能とは、

> **残存する独立経路比較によって、欠損が defect として非零に露出する状態**

である。符号理論的には syndrome が立つことに対応する。Face Lemma では、3 射があり $g \circ f$ と $h$ を突き合わせられることに対応する。

### 4.3 整合欠損的 `coherence-defective`

整合欠損的とは、

> **各 face では局所 forgetting law が書けても、それらが大域的には一つの 1-cochain に吸収されない class が残る状態**

である。Paper II の本文と揃えるため、主表示は cochain 側に置く。対象 $x$ に対し

```text
C^1_nd(St(x);k) --d^1--> C^2_nd(St(x);k) --d^2--> C^3_nd(St(x);k)
Z^2_Θ(x) := ker(d^2)
B^2_Θ(x) := im(d^1)
H^2_Θ(x) := Z^2_Θ(x) / B^2_Θ(x)
```

とすると、

- `ω_Θ` = 局所 forgetting law の mismatch を表す 2-cocycle representative
- `B^2_Θ` = 1-cochain の再定義で吸収できる mismatch
- `[ω_Θ] ≠ 0 ∈ H^2_Θ` = 吸収できない整合欠損 class が残る

を意味する。

直感的には、「各三角形の上では話が合っているが、三角形どうしを貼ると一つの世界像に閉じない」状態である。これが **structural non-globalizability** であり、相補性の非可消な残差を与える。

### 4.4 修復可能 `recoverable`

修復可能とは、

> **残存する複数の face と右随伴 $N$ により、失われた構造を一意または収縮的に再構成できる状態**

である。重要なのは、**`H^2_{\Theta} = 0` だけでは recoverable と言えない** ことである。`H^2_{\Theta} = 0` が与えるのは、局所 mismatch が cochain の再定義で吸収できることだけである。実際の修復には、

- face の重なりによる局在化
- n-cell tower による縦の可定義性
- 右随伴 $N$ の decoder 条件

が追加で必要になる。

### 4.5 局在化可能 `localizable`

operational な中間概念として、

> **複数の face の交差により、欠損位置が候補集合へ縮約される状態**

を `localizable` と呼ぶ。本文 canonical 四分法にはまだ上げず、本ノートで管理する。

---

## 5. 関係式

四概念の関係は次のように読む。

```text
stable              = 比較面がまだ立っている
detectable          = その比較面に欠損が実際に現れる
coherence-defective = 局所 law の mismatch が class として残る
recoverable         = 現れた欠損から元の構造を戻せる
```

したがって:

- 安定でも、欠損が盲点方向に落ちれば未検出でありうる
- 検出できても、`[\omega_{\Theta}] \neq 0` なら構造的に修復不能でありうる
- `H^2_{\Theta} = 0` でも、decoder 条件がなければ recoverable とは言えない

`detectable → recoverable` を直結させないことが、このノートの核心である。

---

## 6. 忘却は bit-flip か erasure か

この対応を使うとき、忘却は bit-flip より **erasure** に近い。

- bit-flip: 値が別の値に化ける
- erasure: 値や関係が「そこにあったはずだが欠けた」状態になる

忘却論の $U_n$ は、多くの場合「値を反転する」より「構造を落として定義域を痩せさせる」作用である。
したがって符号理論対応の主戦場は、Hamming 距離より **erasure decoding** の側にある。

Coherence Defect Lemma の `H^2_{\Theta}` も、この erasure 的読みとよく噛み合う。そこでは「値が変わった」のではなく、「局所 law はあるが、それを global law へ貼り合わせる糊が欠けている」と読むからである。

---

## 7. Face Lemma と n-cell tower の接続

両者の接続は次の一文に圧縮できる。

> Face Lemma は「検査面が立つ最小条件」を与え、Coherence Defect Lemma は「その面上の局所法則が global law に閉じるかどうか」を与え、n-cell tower は「その検査面と法則が意味を持ち続けるために隣接層を同時に失ってはならない条件」を与える。

言い換えれば:

- **Face Lemma** = 横の detectability
- **Coherence Defect Lemma** = 横の non-globalizability
- **n-cell tower 排他性** = 縦の definability

両者がそろって初めて、忘却は単なる崩壊ではなく「検出可能で、しかも一つの global law に畳み込めない残差を持ちうる構造変形」として読める。

---

## 8. 論文内での推奨文言

論文本文で短く言うなら、次の文が核になる。

> Face Lemma は圏論版 syndrome 条件であり、3射は欠損を露出させる最小の検査面である。Coherence Defect Lemma は、各 face では書ける forgetting law が、大域的には一つの 1-cochain に貼り合わさらないことを測る。

少し長く言うなら、次でもよい。

> 安定とは、部分忘却の後でも別ルート比較が残ることであり、検出可能とはその比較に欠損が defect として現れることであり、整合欠損的とは局所 forgetting law の mismatch が class として残ることであり、修復可能とは残存する複数の face と右随伴によって欠損を再構成できることである。

---

# 第 II 部: 修復可能性設計

## 9. 出発点

### 9.1 いま確定していること

第 I 部で、次はすでに固定されている。

- Face Lemma = 圏論版 syndrome 条件
- n-cell tower の隣接同時忘却禁止 = 検査対象と検査規則の同時消失禁止
- `stable / detectable / recoverable` は別概念
- 忘却は `bit-flip` より `erasure` に近い

### 9.2 すでに見えている前方地形

`drafts/standalone/LLMに身体はあるか_統合草稿.md` には、修復可能性を次の二層で読む先行足場がある。

- **Theoretical recoverability**: 構造は内部に残っている
- **Practical irrecoverability**: 単一位置・単一観測では取り出せない

これは忘却論の語彙に引き直すと、

- `U` が落とした構造が **存在論的に消えた** のではなく
- 観測面と回復操作が足りず、`N` がまだ十分に働いていない

という区別である。

---

## 10. 問いの正体

Face Lemma が与えるのは、

> 「欠損があるなら、それが比較面に現れる最小条件」

であって、

> 「現れた欠損から元の構造を戻せる十分条件」

ではない。

この差を飛ばすと、次の誤読が起きる。

1. 3射がある
2. 欠損が見える
3. だから戻せる

この 3 段は連続していない。`2 → 3` のところに、まだ定義されていない機構がある。

---

## 11. 修復可能性への 4 段梯子

| 段 | 忘却論の条件 | 符号理論の直感 | 到達できること | まだ足りないこと |
|:---|:---|:---|:---|:---|
| 1 | 単一の非退化 face | 単一の parity check | 欠損の露出 | 局在化・復元 |
| 2 | face の重なり | 複数 check の交差 | 欠損位置の局在化 | 復元規則 |
| 3 | 縦の可定義性維持 | data/check の同時消失回避 | 回復対象がまだ意味を持つ | decoder の一意性 |
| 4 | 右随伴 $N$ の decoder 化 | erasure decoding | 再構成・縮約 | 収束保証 |

したがって、

- **Face Lemma 単独** = 第 1 段
- **Face の貼り合わせ** = 第 2 段
- **n-cell tower 排他性** = 第 3 段
- **$N$ の設計** = 第 4 段

である。

---

## 12. 最小定理候補

### R0. 単一 face 不十分命題

> 単一の 2-simplex は detectability の最小条件を与えるが、recoverability の十分条件ではない。

直感: 三角形が 1 枚だけあっても、「どこか壊れた」は見える。だが、戻すには別の三角形からの照合が要る。

### R1. 重なり条件

> 欠損した構造が少なくとも 2 つ以上の独立な face に現れているとき、欠損位置は局在化可能になる。

直感: 1 枚の三角形では「ずれた」は言えても、2 枚以上が同じ辺を共有すると「どの辺が怪しいか」が絞られる。

### R2. 縦 admissibility 条件

> 欠損が局在化されても、対応する下位構造と上位検査規則が同時に失われていれば、recoverability は定義不能である。

直感: 部材と検査マニュアルが同時に燃えたら、修理の話に入れない。

### R3. decoder 条件

> 右随伴 $N$ が、残存する face 群から失われた構造への持ち上げを一意または収縮的に定めるとき、recoverability が立つ。

ここで「一意」は強い版、「収縮的」は弱い版である。

- **強い版**: 元の構造が一意に復元される
- **弱い版**: 候補集合が反復ごとに縮む

---

## 13. T9 / structural diagnostics との接続

`drafts/standalone/LLMに身体はあるか_統合草稿.md` の structural diagnostics は、この梯子の最上段を先に使っている。

```text
U_i を名指す
→ どこに欠損が出るかを検出する
→ 対応する N_i を設計する
→ recoverable か irrecoverable かを判定する
```

したがって T9 は、

- Face Lemma の局所検出
- face 重なりの局在化
- n-cell tower の縦整合
- $N_i$ の回復操作

を実践的診断手続きへ持ち上げたものとして読める。言い換えると、

> Face Lemma は structural diagnostics の最小局所核である。

---

## 14. 失敗モード

| 失敗モード | 何が起きているか | 判定 |
|:---|:---|:---|
| face が 1 枚だけ | 欠損は見えるが戻せない | detectable 止まり |
| face が重ならない | 局在化できない | localizable 不成立 |
| 縦に隣接する層が同時消失 | 検査対象が定義不能 | recoverable 不成立 |
| $N$ が多価で収縮しない | 候補が減らない | practical irrecoverability |
| 欠損が残差 0 で沈黙 | syndrome が立たない | detectable 不成立 |

---

## 15. 研究上の次手

1. **face の貼り合わせ圏** を定義する
   単独 2-simplex から、LDPC 的な検査網への持ち上げを与える。

2. **$N$ の decoder 条件** を明文化する
   一意復元・収縮復元・候補集合縮約の 3 水準を分ける。

3. **automath bridge との接続** を作る
   carry defect を単一 syndrome から多面修復へ延ばせるかを見る。

4. **T9 と Paper II の橋** を作る
   Face Lemma を abstract theorem、T9 を applied diagnostic protocol として並べる。

---

## 16. 撤退条件

この線で前進しない方がよい条件も先に固定する。

1. `recoverable` を Face Lemma 単独から導けないまま、本文で強く言いたくなったとき
   → detectability にとどめる

2. $N$ を decoder と呼ぶ条件が書けないとき
   → 「回復操作」には留めるが、「復号」は保留する

3. face の重なりを定義できないとき
   → LDPC 類比は比喩止まりとして明示する

---

## 17. coherence-defective と localizable の両立

第 I 部 §4.3 の **coherence-defective** と本部 §4.5 / §11-§14 の **localizable** は別軸であり両立する。

- **localizable**: 複数 face の交差により欠損位置が候補集合へ縮約される状態 — **位置** の情報
- **coherence-defective**: 個々の face が整合しても大域的に閉じない class ($H^2_{\Theta} \neq 0$) が残る状態 — **障害物** の情報

両概念は両立する: localizable だが coherence-defective な class が残ることはありうる。すなわち「位置は絞れても class として修復不可能な残渣が残る」場合である。

---

# 第 III 部: Negativa と未踏

## 18. Negativa

このノートでまだ主張しないことを固定する。

1. Face Lemma 自体を holes の定理へ置き換えない
2. `H^2_{\Theta} \neq 0` の一般非自明性を、すべての CPS 圏については主張しない
3. `H^2_{\Theta} = 0` から recoverability を直結しない
4. `carry defect` と class `[\omega_{\Theta}]` を混同しない
5. `H^2` torsion を既視感・違和感・未決の問いへ直接読む強い意識解釈は本文へ上げない
6. `localizable` をまだ canonical 四分法へ昇格させない
7. `recoverable` を Face Lemma 単独から導けないまま本文で強く言わない

---

## 19. 開いた課題

1. **`H^2_{\Theta} \neq 0` の最小インスタンスを QM で構成できるか**
2. **FTC を non-obstructed な対照例として一般形まで持ち上げられるか**
3. **右随伴 $N$ を decoder と読むための収縮条件をどう定式化するか**
4. **LDPC/Tanner graph に対応する「face の貼り合わせ圏」をどう定義するか**
5. **`localizable` と `coherence-defective` の階層差を本文へ上げるべきか**
6. **`carry defect` と `H^2` class の automath bridge をどう書くか**

現段階では、detectability までは強く言える。
Coherence Defect Lemma は `H^2_{\Theta}` を主表示とする **conjectural surface** として本文へ上げられる。
recoverability は今後の open problem として扱うのが正確である。

---

## 20. 現在地

- Face Lemma = **detectability の最小定理**
- n-cell tower = **detectability が意味を失わないための縦条件**
- T9 / structural diagnostics = **recoverability を含む運用形**

次の本当の未踏は、

> **複数 face の貼り合わせから、どの条件で $N$ が decoder になるか**

である。

---

# 第 IV 部: Calculations 進捗ログ

## 21. 2026-04-14 QM 第一候補

`calculations/計算_QM_H2Theta最小インスタンス.md` を追加した。そこでは `V=\mathbb{R}^2` 上の標準シンプレクティック 2-cocycle を用いて、`carry defect` の representative と `H^2_{\Theta}` の class を分ける最小計算を固定している。ただしこれは existence probe であり、本文主張の昇格ではない。

## 22. 2026-04-15 FTC 対照例

FTC 対照例として `calculations/計算_FTC_H2Theta対照例.md` を追加した。そこでは可縮な区間上の FTC 最小模型で、forgetting law `Θ` が global potential `Λ` から来る exact 1-cochain であり、obstruction class `[ω_Θ]` が立たないことを固定した。これにより

```text
QM  = obstructed candidate
FTC = non-obstructed contrast
```

の pair が calculations 面で揃った。ただし FTC の全 de Rham 一般化まではまだ主張しない。

## 23. 2026-04-15 selector 足場

`calculations/計算_H2Theta_selector条件面.md` を追加した。そこで、

- trivial side: `global potential / contractible patching`
- nontrivial side: `alternating witness / central extension`

という十分条件の二極を theorem candidate surface として固定した。まだ必要十分条件ではないが、`H^2_{\Theta}` を単なる存在/不存在ではなく **selector** として読む足場ができた。

## 24. 2026-04-15 CPS 内在化

`calculations/計算_H2Theta_selector_CPS内在化条件.md` を追加した。そこで、

- `contractible presentation` → `CPS-globalization atlas + zero holonomy`
- `additive witness` → `CPS-obstruction witness + irreducible orientation`

という翻訳を固定し、selector の十分条件を FTC/QM の外部語ではなく CPS1 / CPS2 / CPS5 / Face Lemma の内部語へ寄せた。ただし package 条件の最小性はまだ未検証である。

## 25. 2026-04-15 weak-package

`calculations/計算_H2Theta_selector_package弱化テスト.md` を追加した。そこで、

- trivial side を `support-local re-lift + generator-face zero holonomy`
- nontrivial side を `support-local faithful witness + anti/symmetric separation`

まで削れる見通しを立てた。これにより selector の芯は `full package` ではなく `support-locality` と `generator-face sufficiency` にある、という読みが前面に出た。ただし弱化しすぎていないかの反例探索はまだ未了である。

## 26. 2026-04-15 反例探索

`calculations/計算_H2Theta_selector_weakpackage反例探索.md` を追加した。そこで、`Weak Lift A'` は false trivialization、`Weak Lift B'` は false obstruction を起こしうることを failure mode として固定し、minimal guard を抽出した。現時点の最小候補は、

- trivial side: `support-saturated + triple-overlap-consistent + gauge-stable`
- nontrivial side: `coboundary-conservative + boundary-closed + refinement-stable`

という guarded weak package である。したがって次の blocker は「weak package の有無」ではなく、FTC/QM 上で `A'' / B''` の guard probe が自然に通るかどうかである。

## 27. 2026-04-15 guard-probe

FTC note と QM note にそれぞれ `A'' / B''` の guard probe を追加した。FTC では `gauge-stable support` と `triple-overlap consistency` が local primitive patching の側から自然に通り、QM では `coboundary-conservative witness` と `refinement-stable anti/symmetric separation` が symplectic 2-cocycle の側から自然に通ることを固定した。これにより FTC/QM pair は単なる `trivial / nontrivial` ではなく、

- `FTC = guarded non-obstructed side`
- `QM = guarded obstructed side`

として読める段階に進んだ。したがって次の blocker は guard そのものの有無ではなく、`A'' / B''` を本文語へ圧縮するかどうかの判断へ移る。

## 28. 2026-04-17 naming

front-stage / backstage の二層語彙を固定した。読者向けの本文語は

- `FTC = 貼合側`
- `QM = 残差側`

とし、`§3.4.6` では `H^2_{\Theta}=0` の側を「局所 law が一つに貼り合わさる側」、`[\omega_{\Theta}] \neq 0` の側を「局所整合の残差 class が残る側」として読む。これに対し calculations / meta の防衛面では guarded package `A'' / B''` を backstage 名として保持する。以後、front-stage では pair 語、backstage では guard 条件という二層運用で行く。
