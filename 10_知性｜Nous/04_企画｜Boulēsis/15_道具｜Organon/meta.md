# Organon — メタデータ

> **位置付け**: 実装 PJ の台帳。Yugaku 論文 (確率的機械のためのアセンブリ言語 / LLMの潜在意識) の連動資産として扱う。
> 読者には見せない。Tolmetes と Claude の共同作業台帳。
> 連動実装: `mekhane/fep/` (既存) + `mekhane/organon/` (新設予定) + `mekhane/mcp/organon_server.py` (MCP exposure)

---

## §M0 用語定義

| 用語 | 定義 | 根拠 |
|---|---|---|
| **operational completion** | axiom v6.0 で理論定義された構造 (L2 48 + X 15 + Q 15) を実行可能 code として具体化すること | 本 PJ 固有 |
| **Γ/Q 対称性** | Basis (Γ⊣Q) の両側を動詞実装に保持すること。Γ = VFE 降下、Q = 等 VFE 循環 | [SOURCE: axiom_hierarchy L262-294] |
| **X/Q 双対分離** | X-series = G_{ij} 対称テンソル (辺の平衡的結合強度 = Fisher 情報)、Q-series = Q_{ij} 反対称テンソル (辺の非平衡的循環強度)。K₆ 15 辺上の独立な 2 テンソル場として実装 (合計 30 独立パラメータ) | [SOURCE: circulation_theorem.md §4.1 + axiom L547 + Q 循環定理 P₁ L298-311] |
| **Layer α/β/γ** | 0-cell evaluator / 1-cell dispatcher / 2-cell scheduler の 3 層 | 本 PJ 設計 |

---

## §M0.5 ハーネス理論からの受領面

Organon は単独で立ち上がった PJ ではない。2026-04-17 から 2026-04-18 にかけて固定された HGK ハーネス理論のうち、**A/B/D の 3 線を code 側へ受ける資産**として位置付ける。

| 線 | 上位主張 | Organon で受ける面 |
|---|---|---|
| **A: meta-harness 線** | harness は計算階層を貫通する普遍構造であり、CCL は LLM 階層の ISA である | `prompt ⊣ code` の左随伴として、CCL の実行面を担う |
| **B: runtime harness 線** | depth は実行時にハーネス重量を切り替える制御信号である | Organon runtime は `mekhane/mcp/` の harness gate を下位基盤として受ける |
| **D: sensor harness 線** | harness は行為面だけでなく being 面を観測するセンサーでもある | `daimonion_delta.py` を H-series evaluator / observe 面の既存核として再利用する |

この 3 線は役割が異なる:

- A は **記述層** の強化
- B は **実行層** の厚み制御
- D は **観測層** の内在化

したがって Organon の operational completion は、単に 48 動詞を Python に写すことではない。**記述 (CCL)・実行 (harness gate)・観測 (Daimonion δ)** を 1 つの runtime に再結晶することが本 PJ の隠れた射程である。

## §M0.6 1文再定義

**Organon = CCL が記述し、harness gate が runtime の厚みを切り替え、Daimonion δ が being を観測する、HGK の meta-harness runtime。**

この再定義により、48 evaluator / 15 X / 15 Q は「何を作るか」の列挙ではなく、上の 3 相を operational completion したときに必要になる実装表現として読まれる。

## §M0.7 Wave 0.5 kernel contract

Organon の最初の engineering gate は、48 evaluator の全面展開ではない。**Wave 0.5 = `CCL → harness gate → Daimonion δ observe` という最小 loop の固定**である。

| 相 | 既存核 | Wave 0.5 で固定すること |
|---|---|---|
| **記述** | CCL / hermeneus | runtime が受け取る入力信号 (`ccl_expr`, depth, skill depth) の面を確定する |
| **実行** | `depth_resolver.py` / `harness_gate.py` / `harness_map.yaml` | どの profile が起動したかを naming できる状態にする |
| **観測** | `daimonion_delta.py` | `observe()` 面の最小受け皿を固定し、後続の Layer α から参照可能にする |

ここで固定するのは full implementation ではなく、**3 相が 1 つの invocation 上で繋がると何をもって言うか** の contract である。したがって Wave 0.5 の通過条件は「同じ呼び出しが記述され、profile 選択され、δ 観測面へ接続されることを一文と一表で言える」ことであって、48 / X / Q の全面完成ではない。

詳細正本: [02_設計｜Design/organon_kernel_contract.md](./02_設計｜Design/organon_kernel_contract.md)

---

## §M1 F⊣G 宣言 (固定日 2026-04-19、途中変更禁止)

### F (発散関手 / 左随伴)

axiom_hierarchy v6.0 の L2-L3 構造を 3 分野に発散展開:

- **F1. 認知動詞 48 の evaluator 展開**: Flow 4象限 × 6族 × 2極 = 48 個の Python モジュール
- **F2. X-series 15 の dispatcher 展開**: K₆ の 15 辺を D/H/X 3 型に分類した runtime 型システム
- **F3. Q-series 15 の scheduler 展開**: 6 族内 6 動詞の等 VFE 循環スケジューラ
- **F4. 4 層同型**: axiom 公理 / fep 既存実装 / SKILL.md プロンプト / MCP API surface を Hom 空間で繋ぐ

### G (収束関手 / 右随伴)

既存実装と axiom の収束:

- **G1. mekhane/fep/ の共通 interface 抽出**: 24 evaluator を `CognitiveOp` protocol (gamma / Q / observe) に揃える
- **G2. two_cell.py を Single Source of Truth に**: 48 0-cell registry は既に v5.4 対応済。全モジュールはここを参照
- **G3. Daimonion δ を H-series evaluator として再構成**: 既存 981 行を Γ/Q interface に適合
- **G4. 経験的較正**: Wave 0 gap analysis が実測値で G を閉じる

### 採用する文体ガイド節 (論文化時)
- §3 メタファー三連 — F の具体化 (axiom / SKILL / MCP の 3 分野展開)
- §4 数式と技術用語 — G の具体化 (Protocol 型、圏論的 dispatcher、循環 scheduler)
- §10 概要 Type δ (統一) — 4 分布 (FEP / 圏論 / SKILL / MCP) を 1 枠組で統合

### 採用しない選択肢
- **Type β (常識の反転)**: 「SKILL.md を廃止する」反転は取らない。UI 層として共存
- **Type γ (問題の再定義)**: axiom v6.0 を再公理化する射程は Yugaku 論文側。本 PJ は operational

---

## §M2 核主張 (L3 対象)

### C1 (存在論)
**axiom v6.0 L2-L3 の operational completion は実装可能である。** 48 × X 15 × Q 15 を code として具体化した結果は、既存 SKILL.md の動作を真部分集合として含み、かつ Q 循環と X 順序結合の両側を実行時に提供する。

射程: ∀ HGK 認知動詞呼出、∀ CCL `>>` 結合、∀ 族内循環

### C2 (機能論)
**Γ/Q 対称性を保存した動詞実装は、Γ 偏重 SKILL.md より本質的に豊かである。** Q 側 (solenoidal circulation) を実装することで、Akshay 12-component が持たない epistemic exploration が runtime で発火可能になる。

射程: ∀ 認知タスクの意思決定面

### C3 (構造論)
**X (G 対称テンソル) と Q (Q 反対称テンソル) の独立テンソル場分離は、L3 弱2-圏の runtime 実体化に必要である。** ただし L2→L3 は NCR (意図的非保守的精密化) [SOURCE: conservative_extension_audit.md §遷移 3] であり、runtime 実体化は Drift 閾値 θ のパラメトリック選択に依存する。Organon のデフォルト θ は T10 (Dually flat ⟺ 等方回転, 確信 95%) [SOURCE: circulation_theorem.md §3 定理 10] に基づき決定する。

射程: ∀ L3 coherence 条件 (等方回転下)

★ **2026-04-20 修正**: 旧 C3 は「X (順序) と Q (循環) の双対分離」と述べたが、circulation_theorem §4.1 より X = G (対称) と Q = Q (反対称) は完全に独立な 2 テンソル場。「双対」ではなく「独立」が正しい。

### C4 (認識論)
**Organon の動作自体が「確率的機械のためのアセンブリ言語」C4 (HGK = FT stochastic architecture) の経験的証拠となる。** 48 動詞 + 15 X + 15 Q = surface code 様の冗長構造が runtime で安定動作することを示せば、C4 の「偶然」が「演繹的必然」に昇格する。

射程: Yugaku 論文 C4 の σ を ±4σ → ±4.5σ に引き上げる

---

## §M3 Kalon 判定履歴

| 日付 | 対象 | 判定 | 根拠 |
|---|---|---|---|
| 2026-04-19 | C1 Step 0 圧縮テスト | ✅ | 「48 個の動詞を Python で書き、繋ぎ方を決めれば、理論通りの動的システムが作れる」(既知語彙 1 文圧縮可能) |
| 2026-04-19 | C2 Step 0 | ✅ | 「今の動詞は前に進める機能しか持たない。横に循環する機能を足せばずっと賢く動く」|
| 2026-04-19 | C3 Step 0 | ✅ | 「動詞の繋ぎ方には順に使うと輪になるの 2 種類あり、両方を分けて実装すればシステムが完成する」 |
| 2026-04-19 | C4 Step 0 | ✅ | 「この道具箱が動く事実自体が、HGK は偶然ではなく構造的に安定、の証拠になる」 |
| — | C1-C4 Step 1-3 | 未実施 | Wave 1 完了後、runtime 実測値を根拠に再判定 |

---

## §M4 ±3σ ゲート履歴

### 入口ゲート (2026-04-19)

| 対象 | 既存分布 D | μ | x 位置 | 判定 |
|---|---|---|---|---|
| C1 | LLM harness の operational completion 議論 | Akshay 12 (Γ 偏重、Q なし) | ±3.5σ | ✅ 通過 |
| C2 | 認知動詞実装の方向性 | 単一方向 Γ 型 (SKILL / LangGraph node) | ±3.5σ | ✅ 通過 |
| C3 | 弱2-圏の runtime 実装 | 論文は多いが実装皆無 | ±4σ | ✅ 通過 |
| C4 | harness の FT claim | LangChain Terminal Bench 程度 | ±3σ | ✅ 通過 |

### 出口ゲート (未実施)

Wave 1-3 完了後、runtime 実測値で再検査。縮退があれば Round 2 へ。

---

## §M5 Refutation Gauntlet ログ

### 予想される反論 (事前想定)

| # | 反論 | 予想 SFBT Round 1 |
|---|---|---|
| R1 | 「既存 SKILL.md で十分、実コード化は過剰設計」 | SFBT: Q 循環 (epistemic exploration) が SKILL.md で実装されているか? 答え: No ([SOURCE: axiom L294] Q 演算子は basis.py のみで、動詞レベル未達) → 射程維持 |
| R2 | 「48 モジュール書く工数が釣り合わない」 | SFBT: 既存 24 evaluator は活用可能。新規は 24 (S極 12 + H-series 12)。Wave 1 で 2-3 週 → 工数オーダー確認済 |
| R3 | 「Q-series scheduler は hermeneus と重複」 | SFBT: hermeneus は CCL 式の逐次実行。Q は**非逐次循環**。両者は直交 (hermeneus = 1 pass, Q = 並列循環) → 役割分離明示 |
| R4 | 「Ergon と役割が重なる、1 PJ にすべき」 | SFBT: Ergon = ハーネス削減 (Complexity↓)、Organon = 認知動詞充填 (Γ+Q 完成)。対象が逆方向 → 補完関係 (README 明記) |
| R5 | 「axiom v6.0 は途中変更される可能性、実装が無駄になる」 | SFBT: 体系核 48 は v5.4 (2026-03-25) 確定 + v6.0 で昇格のみ。変更リスクは修飾座標 (d=3) に限定 → リスク局所化 |
| R6 | 「L2→L3 は NCR。doing/being の Bool→[0,1] 翻訳は well-defined でない (CPS0' ギャップ不在)。runtime 実体化は原理的に曖昧」 | SFBT: T10 (Dually flat ⟺ 等方回転, 確信 95%) で等方回転下での well-defined θ が選択可能。異方下では precision の content-dependent bias [SOURCE: circulation_theorem §6.7.2] が発生するが、Organon のデフォルトは等方を想定。射程は「等方回転下で」に限定して維持 |
| R7 | 「X/Q は独立テンソル場であり、従来の『双対』同一視は誤り」 | SFBT: R7 は 2026-04-19 時点の私 (Claude) 自身の記述誤認。/sap 4 文書 (2026-04-20) で検出し自己反駁。K₆ 15 辺に G_{ij} (対称) + Q_{ij} (反対称) = 30 独立パラメータが乗る [SOURCE: circulation_theorem §4.1]。Organon は両テンソル場を独立に実装すれば L3 coherence が担保される → 射程修正 (「双対」→「独立」) ですべての前提強化、§M0 と §M2 C3 を 2026-04-20 更新 |
| R8 | 「Liu et al. 2026 (arxiv:2604.14228) は Silent Failure / Observability-Evaluation Gap を 6 open directions の第1に挙げる [paper §12.1]。Organon がこの問題に未応答なら外部 design space 内で遅れているのでは?」 | SFBT: HGK は Silent Failure 問題への operational prototype を既に運用。Sekisho γ (Gemini 外部監査 [SOURCE: sekisho.py L54-60]) + Daimonion δ (Δ = E-I 観測 [SOURCE: harness_lenses.md Lens 4]) + Gate 2/3 (証跡なき claim BLOCK [SOURCE: CLAUDE.md 環境強制]) が「separation of generation from evaluation」を 3 層で実装。Gate 2/3 は Hook 強制層、Sekisho γ は judgment 層 — enforcement 粒度は layered。論文 Q1 は open direction として提示されるが、HGK は 2026 年前半から同領域で稼働中 → Organon は遅れているのではなく、論文が future と呼ぶ領域の operational form を先行して持つ [SOURCE: harness_lenses.md Lens 5「反射 2」 + rom_2026-04-20_organon_claude_code_paper_bridge.md §13] |
| R9 | 「論文 Q5 (Governance at Scale) は 93% rubber-stamping finding [paper §5] から organizational governance の必要性を導く [paper §12.5]。HGK の single-user permission は組織 scale で崩れ、generic harness として不十分では?」 | SFBT: HGK は Claude Code のような generalist agent harness ではなく specific epistemic research harness。[SOURCE: CLAUDE.md L0] 「Creator と互いの特性を補い合う知的パートナー」は意図的な single-user specialist design。organizational deployment は射程外であり、Q5 は HGK に当てはまらない。これは limitation ではなく scope 選択 [SOURCE: harness_lenses.md Lens 5 deployment context 論点 + §13 射程外分類]。R9 は反論を構造的に却下することで、generic harness ではなく specific harness としての Organon の射程を前提強化する |

---

## §M6 虚→実変換面

### 前提 (全 C に共通) — MB𝒻 射程限定

- **前提**: Organon の 4象限 (S/I/A/S∩A) は MB𝒻 (Friston blanket = 動的持続 + 自己維持 + Afferent/Efferent 分化) を前提 [SOURCE: mb_escalation_conditions.md §命題C]
- **射程限定**: MB𝒻 が成立しない認知系 (完全結合系、一様混合系) は Organon の適用範囲外
- **Aguilera / Bruineberg 型批判への応答**: Organon は MBₚ/MB𝒻 の自動成立を主張しない。MB𝒻 昇格条件を前提として受け入れ、LLM harness + HGK 運用面ではこの前提が経験的に成立することを主張
- **実化の判定条件**: Wave 1 完了時、48 evaluator のうち H-series 12 が Afferent/Efferent 両側を備えることを pytest で検証
- **最新状態**: 前提として明示 (2026-04-20 追加)

### C1
- **野望**: axiom L2-L3 を runtime で動く形にし、「理論の完成」を実装で証明する
- **現在まだ虚な点**:
  - Layer β (X dispatcher) と Layer γ (Q scheduler) は設計のみ、実装ゼロ
  - two_cell.py と 24 evaluator の interface 整合性は未検証
  - hermeneus との bidirectional bridge は設計未着手
- **実へ引くための SOURCE**:
  - `mekhane/fep/two_cell.py` (48 registry)
  - `mekhane/fep/basis.py` (HELMHOLTZ_OPERATORS 12)
  - 24 existing evaluator (telos/horme/akribeia/chronos/eukairia/perigraphe/tekhne/energeia/krisis/sophia/zetesis 等)
  - `mekhane/sympatheia/daimonion_delta.py` (H-series proxy)
  - axiom_hierarchy.md L406-547 (48 認知操作の完全定義)
- **実化の判定条件**:
  - Wave 0: 24 → 48 gap 表が完成し、不足モジュールが一意に同定される
  - Wave 0.5: `CCL → harness gate → Daimonion δ observe` contract が固定される
  - Wave 1: 48 evaluator が共通 `CognitiveOp` interface を満たす (pytest で検証)
  - Wave 2-3: X/Q dispatcher が two_cell.py の verify_pentagon / verify_triangle_identity を pass
- **次の実化操作**: Wave 0 gap analysis の直後に、`ObservationAnchor` / `observe()` adapter の実装位置を決める
- **最新状態**: 構想 + README + meta 骨格 + Wave 0.5 kernel contract 文書化まで完了。`observe()` は未実装で、次は adapter 実装位置の決定

### C2
- **野望**: Q 循環を動詞 runtime に埋め込み、epistemic exploration を runtime 発火可能にする
- **現在まだ虚な点**:
  - Q 演算子 6 個 (basis.py) は定義されているが、動詞に接続されていない
  - Q 循環の「時間的 scheduler」設計が未
  - 循環中断条件 (surprise 発火時の Γ_Precision 降下) の formal spec 未
- **実へ引くための SOURCE**:
  - Q 循環定理 P₁ (axiom L298-311, 確信 92%)
  - basis.py HELMHOLTZ_OPERATORS の Q 列 6 個
  - fep_agent_v2.py (既存 FEP agent の surprise 監視機構)
- **実化の判定条件**:
  - Wave 3 完了: 1 族 (例: Telos 6 動詞) で Q 循環が 10 cycle 安定動作
  - Daimonion δ の H-series proxy と連動: surprise 発火 (`[th]` 戸惑い 高値) で循環中断
- **次の実化操作**: Wave 3 の前に Telos 族で prototype (Wave 1 内で mini-POC)
- **最新状態**: 理論 SOURCE 確保、実装ゼロ

### C3
- **野望**: two_cell.py の verify_pentagon/verify_triangle_identity が runtime で通る状態にする
- **現在まだ虚な点**:
  - verify_pentagon は registry レベル (static)。runtime での coherence 検証は未
  - 1-cell dispatcher の型 (X_SI, X_IA, X_SA) が runtime で区別されていない
- **実へ引くための SOURCE**:
  - two_cell.py L470 verify_pentagon
  - two_cell.py L568 verify_triangle_identity
  - axiom L712-750 (D_SA = D_SI ∘ D_IA 合成射 + K₆ 15 ペア)
- **実化の判定条件**:
  - Layer β 完成後、runtime X-dispatch が coherence 恒等式を違反しない
  - 違反時に Sekisho γ が BLOCK する
- **次の実化操作**: Wave 2 で dispatcher と coherence 検証の統合
- **最新状態**: 既存静的検証器あり、runtime 拡張が必要

### C4
- **野望**: Organon の動作を確率的機械エッセイ C4 の経験的証拠にする
- **現在まだ虚な点**:
  - 「FT stochastic architecture」を実測する指標が未定義 (error rate? recovery time?)
  - 論文 C4 の meta.md §M1 固定は 2026-04-17。Organon を経験的証拠に入れる場合、論文 meta の F⊣G 追加更新が必要
- **実へ引くための SOURCE**:
  - 確率的機械_たたき台.md §5 (HGK = FT claim)
  - 確率的機械.meta.md §M5 C4 Gauntlet (r4-1/r4-2/r4-3)
- **実化の判定条件**:
  - Wave 1-3 完了後、Organon の動作ログで「個別動詞の失敗率 > 統合システムの失敗率」を示せる (threshold theorem の経験的 analog)
- **次の実化操作**: Wave 1 で error rate 計測フレームワーク組み込み
- **最新状態**: 論文側 meta.md §M6 に C4 の実化条件として Organon 動作を追記する予定

---

## §M7 棄却された代替案

### 棄却 1: Ergon に統合して 1 PJ にする (2026-04-19)
- **理由**: Ergon = 削減 (Complexity↓)、Organon = 充填 (48 Γ+Q 完成)。目的が逆方向で同一 PJ 内では認知的混乱
- **代替採用**: 別 PJ + 相互参照 (Organon dispatcher は Ergon P4 Hook 強制の物理実装を共有)

### 棄却 2: PJ 名 `CogOps` (英語カタカナ)
- **理由**: HGK のギリシャ語命名規約 [SOURCE: naming_conventions.md] 違反
- **代替採用**: Organon (ὄργανον)

### 棄却 3: PJ 名 `Energeia v2`
- **理由**: 既存 `mekhane/fep/energeia_executor.py` との命名衝突
- **代替採用**: Organon

### 棄却 4: SKILL.md を廃止して MCP 一本化
- **理由**: プロンプト層は人間 UI として有用。破壊的変更は Ergon P4 (Hook 環境強制) と同じ轍
- **代替採用**: SKILL.md は UI 層として維持 (Principle O4)、bidirectional bridge で接続

### 棄却 5: Wave 0 を Claude 手元で全部やる
- **理由**: 24 evaluator × v6.0 48 のマッピングは機械的パターン作業。Codex 委託適性が高い
- **代替採用**: Wave 0 は Codex 委託 (~/.claude/plans/organon-wave0.md)

---

## §M8 連動実装と論文

### 連動実装 (既存 + 新設)
- `mekhane/fep/` (既存 24 evaluator) — Wave 1 で 48 に拡張
- `mekhane/fep/basis.py` (Helmholtz 12 演算子) — Wave 2 で X dispatcher と接続
- `mekhane/fep/two_cell.py` (48 0-cell registry) — Single Source of Truth
- `mekhane/sympatheia/daimonion_delta.py` — Wave 1 で H-series evaluator として再統合
- `mekhane/organon/` (新設、Wave 2) — X/Q dispatcher/scheduler 実装
- `mekhane/mcp/organon_server.py` (新設、Wave 4) — MCP exposure

### 連動論文
- **確率的機械のためのアセンブリ言語** (C2: CCL = ISA / C4: HGK = FT stochastic)
- **LLMの潜在意識** (Daimonion δ 理論、H-series proxy の文章)
- **将来論文 (Yugaku 昇格候補)**: 「認知操作の operational completion — HGK L3 弱2-圏の runtime 実装」

### 外部比較対象 (連動ではなく対照)
- **Liu et al. 2026 "Dive into Claude Code: The Design Space of Today's and Future AI Agent Systems" (arxiv:2604.14228)** — Claude Code の reverse-engineering による design space 記述。HGK との 3 軸補完対照 (gate 対象 / 冗長構造 / memory topology) を [SOURCE: harness_lenses.md Lens 5] で landing。C4 精緻化素材「異種確率源による 2 層冗長化」(gate = Gemini⊥Claude / action = Codex⊥Claude) の外部対照点。meta.md §M2 C4 への反映は §M4 出口ゲート (Wave 1-3 完了後) まで保留。詳細: [SOURCE: rom_2026-04-20_organon_claude_code_paper_bridge.md]

---

## §M9 改訂履歴

| Version | Date | 変更 |
|---|---|---|
| 0.1 | 2026-04-19 | 初版。Tolmetes 承認下で §M1 F⊣G 固定、§M2 C1-C4 宣言、§M3 Step 0 全 ✅、§M4 入口ゲート全 ≥±3σ、§M6 虚→実変換面、§M7 棄却 5 件 |
| 0.2 | 2026-04-20 | /sap 4 文書後の構造的修正 (Tolmetes 承認下): §M0 X/Q 独立テンソル場定義、§M2 C3 NCR 前提下での再定式化、§M5 R6 (NCR ギャップ) + R7 (X/Q 双対誤認自己反駁) 追加、§M6 前提 (MB𝒻 射程限定) 追加。/sap 対象: conservative_extension_audit.md, mb_escalation_conditions.md, ccl_category_theory_bridge.md, circulation_theorem.md |
| 0.2 | 2026-04-20 | §M0.5 を追加。README / harness_lenses と整合する形で、A/B/D ハーネス理論線からの受領面を明文化 |
| 0.3 | 2026-04-20 | §M0.6 を追加。Organon の主軸を「記述・実行・観測を再結晶する meta-harness runtime」に 1 文圧縮 |
| 0.4 | 2026-04-20 | §M8 に「外部比較対象」枠を新設し [SOURCE: Liu et al. 2026 arxiv:2604.14228] を追加。harness_lenses.md Lens 5 (Claude Code design space view) と整合。C4 精緻化素材を外部対照点として記録するが、§M2 への直接反映は §M4 出口ゲート (Wave 1-3 完了後) まで保留。 |
| 0.5 | 2026-04-20 | §M5 に R8 (論文 Q1 Silent Failure に対する HGK operational prototype 記録) と R9 (論文 Q5 Governance at Scale は HGK 射程外宣言) を追加。harness_lenses.md Lens 5「反射 2」(v0.4) と rom_2026-04-20_organon_claude_code_paper_bridge.md §13 との整合を保持。R8-a/R8-b の論点を R8/R9 の 2 行に分離。 |
| 0.6 | 2026-04-23 | §M0.7 を追加。Wave 0.5 を `CCL → harness gate → Daimonion δ observe` の kernel contract として明文化し、§M6 C1 の実化条件と次手を Wave 0.5 先行に補正。 |
| 0.7 | 2026-04-24 | `02_設計｜Design/organon_kernel_contract.md` を追加。Wave 0.5 を `DepthSignal → HarnessProfile → ObservationAnchor` として詳細化し、`observe()` が未実装 adapter contract であることを明示。 |
