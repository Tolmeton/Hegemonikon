# Face5 Lemma 試作 — メタデータ

**役割**: Face5Lemma_draft.md の Kalon 判定を anchor する独立 §M1 F⊣G を宣言する台帳。
**軌道**: `比較射σの統一定理_v0.6.md` 親クラスタにおける **proof-incubator-meta**。`Face5Lemma_draft.md` を補助証明稿として運用するための判定面・棄却面・昇格面を保持し、整理済み結論だけを本流へ送る。
**関係**: 本 draft は σ 統一論文 (`../standalone/比較射σの統一定理_v0.6.md` + `../standalone/比較射σの統一定理_v0.6.meta.md`) の姉妹 incubator であり、σ 論文の §M1 F⊣G (BridgeDat 始対象性) とは **独立の F⊣G** で評価される。σ 論文が Face5 を C-claim として引用する場合は、σ 論文側の F⊣G で再評価する。

**運用注記 (2026-04-21)**:
- 下位節に残る `σ 論文 v0.3` などの番号は歴史的導出位置の記録である。
- 現在の実質正本は `比較射σの統一定理_v0.6.md` / `比較射σの統一定理_v0.6.meta.md` の 2 面であり、実行面ではそちらを優先する。
- 本ファイルは `比較射σの統一定理_v0.6.meta.md` §M8 の orbit table でいう `proof-incubator-meta` に対応する。

---

## §M1 F⊣G 宣言

**固定日**: 2026-04-17 (retrospective formalization)

**註記**: Face5Lemma_draft は v0.1-v0.3 を通じて informal incubator として進行してきた。v0.2 §5.2-§5.3 (Ising/SU(2)_k 検証)、v0.3 §5.4 (TY/ENO 普遍化)、v0.3 §11 (Stasheff minimality) で substantive claim が立ったため、これを anchor する独立 §M1 を本 meta.md 新設時点で固定する。過去の判定は本 §M1 下で retrospective に再評価する (事後選択ではなく、既に通った判定を formal frame に接続する操作)。

**F (発散関手)** = Face3 (σ の最小 habitat) の延長候補を **3 軸** に展開する:
- **次元軸**: 射の数を増やし、対応する Stasheff associahedron `K_n` 階層に沿って pentagon → hexagon → higher polytope と延伸
- **族軸**: fusion category の族に沿って展開 — SU(2)_k (Chebyshev)、Tambara-Yamagami (平方根)、Haagerup / near-group (他形)
- **ドメイン軸**: monoidal (pentagon)、braided (hexagon)、symmetric など構造的変種

**G (収束関手)** = 各軸で **最小不変構造** を取り出す:
- 次元軸 → `K_n` の次元公式 `dim K_n = n-2`。n=4 で最小 2-dim face が pentagon
- 族軸 → Etingof-Nikshych-Ostrik (2005) 定理による Frobenius-Perron 次元の代数的整数性
- ドメイン軸 → pentagon/hexagon axiom の coherence 普遍性 (Mac Lane 1963)

**F⊣G の意味**: σ を延長しても (F)、どの軸でも最小不変構造 (G) が existing SOURCE 文献で固定される。本 draft の Kalon 判定はこの F⊣G 下で「MB 局所不動点」への収束を判定する。

**σ 論文 §M1 との違い**:
- σ 論文 F: σ を **4 ドメイン** (幾何三角形 / Face Lemma / Euler path / FEP) へ展開
- σ 論文 G: σ の一意性を **BridgeDat(C,A) の始対象性** として証明
- 本 draft F: **3 軸** (次元 / 族 / ドメイン) へ展開
- 本 draft G: 各軸の **最小不変構造** を既存 SOURCE から取り出す

両者は直交する軸系を持ち、独立に評価すべき。σ 論文側で Face5 を引用する場合は、σ 論文 G (BridgeDat 始対象性) 下で別途評価が要る。

---

## §M2 核主張リスト

- **F5-α** [定理, Kalon△ ◎]: 5 射は pentagon coherence polytope の最小条件。Stasheff associahedra 理論で証明 (`Face5Lemma_draft.md §11`)
- **F5-β** [仮説]: associator 非自明性 ⇔ strict monoidal 排除 ⇔ SU(2)_k で k≥2
- **F5-γ** [反証済]: 「φ は Face5 の universal 固有値」は Fibonacci 特有。§5.2 Ising で `d²=2` が反証
- **F5-γ'** [仮説]: SU(2)_k family で `d_{1/2}(k) = 2cos(π/(k+2))` が Face5 固有値の階段 (§5.3 計算検証)
- **K3''** [定理予想, Kalon△ ◎]: Face5 固有値は任意の fusion category で totally real positive algebraic integer。ENO 定理で universality 保証 (§5.4)
- **F5-δ** [落書き]: `Face(2n+1) = n-cell comparison の最小条件` 階層公式。n=1,2 は `dim K_n = n-2` で正当化、n≥3 は open

---

## §M3 Kalon 判定履歴

**retrospective entries** (§M1 固定以前の判定を本 §M1 下で再検証して anchor):

| 日付 | 対象 | 判定 | 根拠 |
|:---|:---|:---|:---|
| 2026-04-17 | F5-α | ◎ Kalon△ | Stasheff `K_4 = pentagon, dim=2` 最小性。§11 Step 0-3 通過。本 §M1 F⊣G 下で再検証: F (3 軸展開) で次元軸を取り、G で `dim K_n = n-2` に収束 → K_4 が min 2-dim ✓ |
| 2026-04-17 | K3'' | ◎ Kalon△ | ENO 定理による FP 次元 algebraic integer 性。§5.4 Step 0-3 通過。本 §M1 F⊣G 下で再検証: F (族軸展開 SU(2)_k / TY / Haagerup) で G=ENO により代数的整数性が全族で保持 ✓ |
| 2026-04-17 | F5-γ' | ◯ (Kalon 判定保留) | 個別 family (SU(2)_k) での検証は済だが、universality は K3'' に委ねる位置づけ |
| 2026-04-17 | F5-β | ◯ (Kalon 判定保留) | 「非自明性 ⇔ k≥2」の代数的同値性証明が未。仮説 face |
| 2026-04-17 | F5-δ | ✗ (Kalon 非対象) | n≥3 が落書きのため Kalon 判定対象外。n=1,2 は F5-α の系として既に ◎ |

**重要な注記**: §11 §5.4 の Kalon △ ◎ 判定は §M1 固定以前に informal に下された。本 §M1 は **retrospective formalization** であり、事後選択ではない。事後選択となるのは「判定結果を通すために F⊣G を調整する」操作であって、本件は「既に通った判定を適切な frame に接続する」操作である。この区別を明示するため、本 §M3 で再検証の論理を明記している。

---

## §M4 ±3σ ゲート履歴

| 日付 | 対象 | 入口 σ | 出口 σ | 判定 |
|:---|:---|:---|:---|:---|
| 2026-04-17 | F5-α | ±3σ | ±3σ | μ = 「pentagon identity は Mac Lane の偶然」から離れた裾。「Face5 minimum = K_4 theorem 系」という構造的読みは ±3σ 維持 |
| 2026-04-17 | K3'' | ±3σ | ±3σ | μ = 「fusion category の次元は個別に決まる」から離れた裾。「ENO による universal algebraic integer 性」は代数的整数論的 universality として ±3σ 維持 |

---

## §M5 Refutation Gauntlet ログ

### F5-γ → F5-γ' 降格 (2026-04-17 第 2 ラウンド, §5.2-§5.3)
- 反論 r: Fibonacci 以外の MTC で Face5 が立つが、固有方程式は `d²=d+1` ではない
- 試行: Ising anyon で `d_σ = √2`, `d² = 2` を計算確認 → F5-γ 反証
- 結果: F5-γ 棄却 → F5-γ' (SU(2)_k family) へ再構築 (射程は拡大)

### F5-γ' → K3'' 昇格 (2026-04-17 第 3 ラウンド, §5.4)
- 反論 r: SU(2)_k 以外の MTC 族 (TY, Haagerup) では別の式が出るのでは?
- 試行: Tambara-Yamagami で `d(m) = √|A|` を確認。TY(Z/5) は SU(2)_k 範囲外だが代数的整数性は維持
- 結果: family-specific な式ではなく、ENO 定理による **代数的整数性** を universal 性質として抽出 → K3'' 確立

### §M1 F⊣G 欠如の指摘 (2026-04-17 本 meta.md 新設)
- 反論 r: §11 §5.4 の Kalon △ ◎ 判定は §M1 F⊣G 固定前で、kalon-check rule 「宣言がなければ判定を実行するな」違反
- 試行: 本 meta.md 新設により §M1 を retrospective に固定。既存判定を本 F⊣G 下で再検証し、同判定を維持
- 結果: 枠組み違反の指摘を受け入れ、frame を追加補強。判定内容は変更なし

---

## §M6 虚→実変換面

### C1
- 野望: [§M2 C1 の核主張を 1 文で言い直す]
- 現在まだ虚な点: [未証明・未観測・未形式化・未反駁処理の核]
- 実へ引くための SOURCE: [読むべき原典 / 必要データ / 必要定理]
- 実化の判定条件: [何が揃えば『実へ近づいた』と言えるか]
- 次の実化操作: [Sourcing / 定義追加 / 証明 / 実験 / 反論吸収]
- 最新状態: 変換中

## §M7 棄却された代替案

- **σ 論文 meta.md §M1 下で Face5 を評価する案** (2026-04-17 棄却): σ 論文 G (BridgeDat 始対象性) は σ の一意性に特化した収束。Stasheff K_n minimality や ENO 代数的整数性は別軸の収束であり、同じ G で両方は評価できない。Face5 は独立 §M1 で扱う

- **Kalon △ ◎ を撤回して informal note に降格する案** (2026-04-17 棄却): §11 §5.4 の判定論理自体は 3 ステップで通っており、不足しているのは frame 明示だけ。判定内容を保持し frame を追加する方が射程を維持できる

- **F5-α の「5 射」を 5 つの独立生成射と解釈する案** (2026-04-17 棄却): この解釈では Face Lemma 語彙との parallelism は強くなるが、Stasheff K_4 の 5 edges (= 同じ α の 5 適用) とは別物になる。本 draft は Stasheff K_4 を根拠にする以上、「5 射 = 5 associator 適用」と解釈を明示する。Face Lemma との parallelism は「同じ parallelism ではなく、n=1 と n=2 の次元的類比」と限定する

---

## §M8 Orbit 接続 / 今後の open

### 周辺衛星との接続

| orbit | ファイル | 本ファイルとの関係 |
|:--|:--|:--|
| core | `../standalone/比較射σの統一定理_v0.6.md` | ここで安定化した定理 face / claim face を受け取る本流 |
| core-meta | `../standalone/比較射σの統一定理_v0.6.meta.md` | orbit 管制面。どの結論を本流へ送るかの境界条件を共有する |
| proof-incubator | `./Face5Lemma_draft.md` | 本ファイルが判定・棄却・昇格を支える直接の相方 |
| seed-bag | `./pentagon_sigma_conjecture.md` | 未成熟な直感や種がここから流入する |
| fork-note | `../standalone/5cell_phi_sector_FORK_v0.1.md` | 旧本流から分岐した検証・棄却・残差をこちらで隔離する |

### 運用規則

1. `pentagon_sigma_conjecture.md` の種は、証明可能性が見えた時点で `Face5Lemma_draft.md` に送る。
2. `Face5Lemma_draft.md` で安定した結論だけを、本ファイルの判定面を経由して `比較射σの統一定理_v0.6.md` へ送る。
3. q=5 / automath 由来の tested scope は `5cell_phi_sector_FORK_v0.1.md` に隔離し、本ファイルはその戻し条件だけを受け持つ。
4. 本ファイルは試行錯誤ログの倉庫ではなく、**proof-incubator を本流へ接続する関所** として振る舞う。

### 本流への接続候補

- **σ 論文 v0.3 §2.0 三軸分離** (種⑥): 本 draft の「3 軸 F (次元/族/ドメイン)」と整合。σ 論文側の「群/スペクトル/位相」軸とは軸の命名が異なるが、共に軸分離のアプローチを取る
- **σ 論文 v0.3 §5.bis スペクトル軸 endpoint identity**: F5-γ' / K3'' を具体例として提供
- **σ 論文 C5 (3 層表現予想)** (meta.md §M2): 本 draft の `{K_n}_{n≥2}` Stasheff tower は C5 の「骨格普遍層」候補

### Open (2026-04-17 時点)

- F5-β の代数的特徴付け (strict monoidal 排除の十分条件)
- K3'' の逆向き: 任意の totally real positive algebraic integer が Face5 eigenvalue として実現されるか
- F5-δ の n≥3 具体化 (hexagon axiom ↔ K_5 の 3-polytope 面)
- `k→∞` 古典極限での σ closure schema の振る舞い
- σ 論文 §M1 F⊣G での Face5 再評価 (別軸評価の要求)

---

## §M9 F⊣G 宣言変更履歴

- 2026-04-17: 初回固定 (retrospective formalization, §11 §5.4 判定を anchor)

---

*v0.1 — 2026-04-17 Face5Lemma_draft.md の Kalon 判定 frame を独立 §M1 として固定。σ 論文 §M1 との独立性を明示し、両者は直交する軸系を持つ姉妹 incubator 関係にあることを確定。*

## §M10 Donor Absorption Ledger (2026-04-18)

### D-F5-01: Face7Lemma_draft

- **donor path**: `drafts/incubator/Face7Lemma_draft.md`
- **receiver surfaces**: `Face5Lemma_draft.md` §21.1、`Face5Lemma_draft.meta.md` 本節
- **kept**: Face7 の目的、MTC 自動帰結 vs A_∞-圏族の非自明性、`F7-ε` 仮説、`A_5 requirement` 反証、SOURCE/TAINT 台帳の要点
- **discarded**: donor 単独での round-by-round prose のみ
- **final disposition**: donor file を削除し、higher-face annex と meta ledger に再配置

### D-F5-02: bridge_spectrum_axiom_draft

- **donor path**: `drafts/incubator/bridge_spectrum_axiom_draft.md`
- **receiver surfaces**: `Face5Lemma_draft.md` §21.2、`Face5Lemma_draft.meta.md` 本節
- **kept**: open #20 の三候補比較、`BridgeDat -> FusCat` 骨格、ENO × cartesian section 読解、tower/cell-wise 合流点
- **discarded**: donor 単独の問題設定の再掲だけ
- **final disposition**: donor file を削除し、Open#20 annex と meta ledger に再配置
