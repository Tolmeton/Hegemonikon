# /sap 精読台帳
## 対象: 四則演算 / 統一表 / 比較射σ

精読日: 2026-04-21
深度: L2 `/sap`
派生: `spec`

---

## Phase 0 Prolegomena

### S[0.1] 精読対象

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/四則演算は忘却の選択である_たたき台.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/統一表の関手化_構想ドラフト_v0.2.md`
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/比較射σの統一定理_v0.6.md`

### S[0.1.bis] 運用上の正本

- 現在の σ 論文の正本 pair は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/比較射σの統一定理_v0.6.md` と `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/比較射σの統一定理_v0.6.meta.md` である。
- 本精読では本文正本 `v0.6.md` のみを読んだ。`v0.6.meta.md` は README / 台帳 / 版歴の導線として参照すべき面である。

### S[0.2] 範囲固定

- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/四則演算は忘却の選択である_たたき台.md`: L1-L190 を精読。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/統一表の関手化_構想ドラフト_v0.2.md`: L38-L240, L352-L366, L1213-L1255, L1293-L1330, L1580-L1596 を精読。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/比較射σの統一定理_v0.6.md`: L30-L220, L436-L441, L518-L585 を精読。

### S[0.3] prior 棚卸し

- [TAINT: 依頼面] Tolmetes の焦点は「オイラーの等式の各構成要素における忘却論の捉え方」「忘却論における微分・積分・対数」「四則演算の拡張」。
- [TAINT: 作業面] 上記 3 文書のうち、四則演算の定義は 1 本目、忘却公理と連続極限は 2 本目、比較射 σ による統一点は 3 本目にある可能性を前提に範囲を切った。

### S[0.4] 持ち越し

- P-1 では、上記範囲から事実のみを逐語的に登録する。

[CHECKPOINT PHASE 0/3]

---

## Phase 1 Sapheneia

### `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/四則演算は忘却の選択である_たたき台.md`

- 📖 加法と乗法は `exp: (\mathbb{R}, +) \to (\mathbb{R}_+, \times)` による群同型として置かれ、減算と除算はそれぞれ逆元操作として書かれている。四則演算は「2群 × {順方向, 逆元} = 4」と明記されている。 [SOURCE: exec_command L14-L16, L41-L60]
- 📖 `\log(a \cdot b) = \log a + \log b` が置かれ、掛け算の世界と足し算の世界が「情報の損失なく行き来できる」と記述されている。逆写像は `\log` である。 [SOURCE: exec_command L26-L39]
- 📖 `U_abs` は「乗法構造を忘れる → 加法だけが見える」、`U_rel` は「加法構造を忘れる → 乗法だけが見える」と定義されている。 [SOURCE: exec_command L72-L77]
- 📖 オイラーの等式 `e^{i\pi} + 1 = 0` の構成要素について、`e` は `U_growth`、`i` は `U_phase`、`\pi` は `U_line`、`0` は `U_abs`、`1` は `U_rel` の表に配置されている。 [SOURCE: exec_command L79-L95]
- 📖 cell 次元の表では、0-cell が数、1-cell が四則演算と `exp/log`、2-cell が `U_abs/U_rel` と「どちらの演算で見るか」の選択として整理されている。 [SOURCE: exec_command L118-L134]
- 📖 `\exp: \mathbb{R} \to \mathbb{R}_+` は正の実数にしか像を持たず、`0` と負数は乗法群の外にあるため、`U_rel` の忘却は完全ではないと明記されている。 [SOURCE: exec_command L148-L150]

### `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/統一表の関手化_構想ドラフト_v0.2.md`

- 📖 共通基盤は新たに構成するのではなく、Paper VIII の α-忘却濾過と `Filt([0,1], WdSub(C))` が既に与えていると書かれている。 [SOURCE: exec_command L42-L44]
- 📖 `Obliv := C ↦ Filt([0,1], WdSub(C))` と置かれ、Obliv は圏ではなく `Cat → Cat` の 2-関手として定義されている。 [SOURCE: exec_command L66-L72]
- 📖 α-忘却濾過の公理として `(F1) Ob(C_α)=Ob(C)`, `(F2) C_0=C`, `(F3) C_1=C_disc`, `(F4) α₁≤α₂ ⇒ Mor(C_{α₂}) ⊆ Mor(C_{α₁})` が列挙され、「ものは消えない。つながりが消える」と要約されている。 [SOURCE: exec_command L100-L113, L226-L233]
- 📖 `Obliv(C)` の内部構造について、対象は `{C_α}`、射は濾過族間の包含を保つ自然変換、終対象は一様忘却 `(∀α: C_α = C_disc)` とされている。 [SOURCE: exec_command L115-L123]
- 📖 三実現関手として `Φ_FEP`, `Φ_Phys`, `Φ_Epist` が置かれ、忘却の度合い α は順に MB の厚み、曲率、faithful/full の度合いへ送られている。 [SOURCE: exec_command L143-L188]
- 📖 統一表の各行の対応は、`Obliv(C_FEP) → Obliv(C_Epist) ← Obliv(C_Phys)` の cospan から作る繊維積 `P` の元として書かれている。 [SOURCE: exec_command L194-L204]
- 📖 `(F4)` と `(F5)` の代数的関係として `e^{i\pi/5} + e^{-i\pi/5} = \varphi` が置かれているが、ここから `α = 1/5` の力学的導出はまだ言えず、Problem 6 の open 問題とされている。 [SOURCE: exec_command L219-L222]
- 📖 「力は忘却の虚部から生まれる: `F_ij ∝ sin(θ) = Im(e^{iθ})`」と書かれ、複素化射 `ω(f,α)=w(f,α)e^{iθ(f,α)}` の虚部 `Im(ω)=w·sin(θ)` が `F_ij` に対応すると記述されている。 [SOURCE: exec_command L355-L359]
- 📖 同じ箇所で、`e` は忘却関手 `d` の固有関数 `w=e^{-kα}` の関数形、`i` は `θ=π/2` の位相、`\pi` は非整列サイクルの半周期として読まれている。 [SOURCE: exec_command L359-L365]
- 📖 Paper II では、微分 `d` は積分定数を落とす忘却関手 `d: C^\infty → C^\infty/\mathbb{R}` として定式化され、`dw/dα = -kw` の解 `w=e^{-kα}` の根拠として `d(e^x)/dx = e^x` が挙げられている。 [SOURCE: exec_command L363-L365]
- 📖 「層 B」では `deltaSet` が混合偏微分の cell 積分に一致し、`d ↦ deltaSet`, `∫ ↦ walshFlux` が cubical cochain レベルで定理として閉じると書かれている。 [SOURCE: exec_command L1213-L1219, L1253-L1254]
- 📖 「層 C」は未解決であり、`Φ(x ⊕ y) ≠ Φ(x) ⊕ Φ(y)` の差が carry defect `κ` になるため、ordinary functor ではなく `pseudofunctor / defect-bearing bridge` として書くべきだとされている。 [SOURCE: exec_command L1221-L1234]
- 📖 方向定理の読み替えとして、`d\Phi \wedge T = 0` のときは連続側 `F_ij=0` / 離散側 `κ=0`、`d\Phi \wedge T ≠ 0` のときは連続側 `F_ij ∝ sin(θ)` / 離散側 `κ ≠ 0` と対応づけられている。 [SOURCE: exec_command L1238-L1245]
- 📖 `first obstruction class` の候補 reduction として `H^2_{dR}(M_q) → H^2(G_m; \mathbb{Z}) → H^2(G_m; \mathbb{Z}/2\mathbb{Z})` が置かれ、`Int_q` は flux 積分を `λ_q` で整数化する conjectural lift とされている。 [SOURCE: exec_command L1293-L1301]
- 📖 `q=5` では、排他的 2 体 sector、算術的 excess、obstruction 可視化 proxy が初めて同時に立ち上がる「第一障害可視化閾値」と書かれている。 [SOURCE: exec_command L1303-L1320]
- 📖 先行研究差分の表では、Paper II の位置づけが「微分 `d = C^\infty→C^\infty/\mathbb{R}`」「`d` の固有方程式から `e` が一意に出る」と明記されている。 [SOURCE: exec_command L1326-L1330]
- 📖 連続極限の節では、`w(f,α)=e^{-kα}` は一つの射の重み、`L(n)=Tr(T^n)∼\varphi^n` はサイクル全体の有効状態数とされ、`k ↔ -\log\varphi·Δα^{-1}` は heuristic correspondence に留まると書かれている。 [SOURCE: exec_command L1580-L1584, L1595-L1596]
- 📖 同じ節では、`h_{Δα} = (1/(nΔα))\log L(n)` を有限化する renormalized growth rate と coarse-graining 関手 `G_{Δα}` の構成が Problem 6 の骨格として挙げられている。 [SOURCE: exec_command L1586-L1594]

### `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/比較射σの統一定理_v0.6.md`

- 📖 核定理では、比較射 `σ: g∘f ⇒ h` が `F_ij`, `λ`, associator coherence, `BridgeDat_n`, blanket sector の 5 context で同一の Yoneda 関手値として現れると書かれている。 [SOURCE: exec_command L38-L54]
- 📖 Paper I 顔では、忘却曲率 `F_{ij}` が「忘却で重み付けされた Chebyshev 1-形式 `\Phi T` の外微分」とされ、`F_{ij}=0 \iff d(\Phi T)=0`、`F_{ij}=-F_{ji}` が置かれている。 [SOURCE: exec_command L66-L89]
- 📖 `TangentCtx(M,F)` の 2-射は triangle 上の `F_{ij}|_\Delta` であり、wedge 反対称が `σ^*=-σ` を与える pivotal data とされている。 [SOURCE: exec_command L91-L120]
- 📖 SST 顔では、`λ` は各 2-simplex 上の signed 2-cell であり、SST 条件 `( +λ ) + ( -λ ) = 0` が `CatCtx(C, λ)` の pivotal data を与えると書かれている。 [SOURCE: exec_command L136-L197]
- 📖 `F_{ij}=-F_{ji}` と `( +λ ) + ( -λ ) = 0` は「同じ pivotal involution の異なる context 実装」と明記されている。 [SOURCE: exec_command L199-L208]
- 📖 合流章では、5 顔は同一の関手 `Hom_{SignTower}(K_n, -)` の 5 つの evaluation であり、統合は「橋」ではなく「同一関手の異なる evaluation」と説明されている。 [SOURCE: exec_command L518-L585]
- 📖 FEP 節では、変分自由エネルギー `F[q,s] = E_q[\log q(\mu) - \log p(\mu,s)] = D_{KL}(q\|p(\cdot|s)) - \log p(s)` が置かれている。 [SOURCE: exec_command L437-L441]

### S[1.3] 網羅性確認

- 事実登録対象は P-0 の指定範囲を全行カバーした。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/四則演算は忘却の選択である_たたき台.md`: Coverage 100% (L1-L190)。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/統一表の関手化_構想ドラフト_v0.2.md`: Coverage 100% of selected ranges。
- `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/比較射σの統一定理_v0.6.md`: Coverage 100% of selected ranges。

### S[1.4] 推論分離チェック

- Phase 1 の記述は事実登録のみに限定した。
- 方向・意味づけ・定義面の接続は P-2 へ持ち越す。

[CHECKPOINT PHASE 1/3]

---

## Phase 2 Katalogē

### S[2.1] 事実の分類

| 層 | 受け取り | 変換 | 持ち越し |
|:--|:--|:--|:--|
| 四則演算層 | `exp/log`, `U_abs/U_rel`, `0/1/e/i/π` の配置 | 四則演算を 0-cell / 1-cell / 2-cell に分割可能 | 「四則演算をどの cell まで拡張するか」という次段の定義面 |
| 忘却公理層 | `(F1)-(F4)`, `Obliv`, `Φ_FEP/Φ_Phys/Φ_Epist` | 忘却を「対象保存・射減衰」の連続手続きとして固定 | 微分・積分・対数をこの手続きのどの相に置くか |
| 連続化層 | `d: C^\infty→C^\infty/\mathbb{R}`, `w=e^{-kα}`, `d↦deltaSet`, `∫↦walshFlux`, `log\varphi` 密度 | 離散配置数と連続減衰率の橋を「open problem」として可視化 | 高校数学の微積分を忘却論でどう読むか |
| 比較射層 | `σ`, `F_{ij}`, `λ`, `Hom(K_n,-)` | 比較そのものを単一 Yoneda 値へ束ねる | 四則演算拡張を「別々の新演算」ではなく同一比較の別評価として書けるか |

### S[2.2] SOURCE 完全確認

- 事実台帳の全項目に SOURCE を付した。
- 事実未付番の行は置いていない。

### S[2.3] 推論混入検査

- 判定: CLEAN
- Phase 1 の事実文では「なので」「ために」を根拠推論として使っていない。

### S[2.4] prior 照合

- `対数`: 直接記述あり。加法世界と乗法世界の変換子として `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/四則演算は忘却の選択である_たたき台.md` で明示され、`log\varphi` は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/統一表の関手化_構想ドラフト_v0.2.md` で連続極限の密度量候補として現れている。 [CONFIRMED]
- `微分`: 直接記述あり。`d: C^\infty→C^\infty/\mathbb{R}`、`d(\Phi T)`、`外微分との両立` が確認された。 [CONFIRMED]
- `積分`: 直接記述あり。cell 積分、`walshFlux`、`Int_q` が確認された。 [CONFIRMED]
- `四則演算の拡張`: 直接の完成定義は今回の精読範囲では未固定。拡張に使えそうな部材として `2-cell`, `defect`, `σ`, `Obliv`, `coarse-graining`, `flux integral` が観測された。 [PARTIAL]

### S[2.5] φ_SI 接続

- → `/lys` 候補 1: 「微分 = 積分定数を落とす忘却」「積分 = flux を束ねる回収」として、FTC を忘却論の双対操作へ言い換える。
- → `/lys` 候補 2: 四則演算の 1-cell を、`d/∫/log` を含む連続演算層へ持ち上げるとき、`carry defect` を新しい演算記号ではなく 2-cell 補正として扱う。
- → `/lys` 候補 3: オイラーの等式の `e, i, π, 1, 0` を「別定数」ではなく「忘却の異なる断面」として再定義し、`σ` をその比較射に据える。

### S[2.6] [主観]

- [推定, 0.83] Tolmetes が次に考えたい「忘却論における微分・積分・対数」は、今回の 3 本の内部だけでも既に別々ではない。`d` と `∫` は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/統一表の関手化_構想ドラフト_v0.2.md` で chain-map / flux 面として現れ、`log` は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/四則演算は忘却の選択である_たたき台.md` と `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/統一表の関手化_構想ドラフト_v0.2.md` で「尺度の切替」と「密度化」の二面を持っている。
- [推定, 0.78] 四則演算の拡張先は「五番目・六番目の演算を足す」方向より、「四則演算を 1-cell から 2-cell / 連続極限へ持ち上げる」方向のほうが、今回の 3 本には整合的に見える。

[CHECKPOINT PHASE 2/3]
