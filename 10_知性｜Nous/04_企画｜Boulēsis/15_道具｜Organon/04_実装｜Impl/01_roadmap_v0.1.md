# Organon ロードマップ v0.1

> これは `15_道具｜Organon` PJ の実装計画文書である。
> 上位台帳: [../meta.md](../meta.md) (F⊣G 宣言 + 核主張 C1-C4)
>
> **主軸再定義**: Organon の first identity は「48 evaluator の束」ではない。**CCL が記述し、harness gate が runtime の厚みを切り替え、Daimonion δ が being を観測する meta-harness runtime** であり、48 / X / Q はその実装形である。

## 1. 現状診断

axiom_hierarchy v6.0 は体系核 57 = 1 + 8 + 48 を定義し、体系核外に X-series 15 + Q-series 15 を置く。
実装面を射影すると:

- `mekhane/fep/` は **v3.0 (2026-01-29)** で 24 定理 (旧体系) に 100% coverage、336 tests pass。
- `mekhane/fep/two_cell.py` は **v5.4 (2026-03-25) 対応**の 48 0-cell registry + Associator + Pentagon/Triangle 検証器を持つ。
- `mekhane/fep/basis.py` は Helmholtz 12 演算子 (Γ×6 + Q×6) を v6.0 互換で実装済。
- `mekhane/sympatheia/daimonion_delta.py` (2026-04-18, 981 行) は H-series 12 の proxy 観測を実装。
- `~/.claude/skills/` は 48 動詞を SKILL.md プロンプトとして実装 (UI 層)。

したがって Organon の仕事は「ゼロから動詞体系を作ること」ではない。**既存資産 (v5.4 0-cell registry + Helmholtz Basis + 24 evaluator + H-series proxy) を v6.0 48 operational completion の標準形に再編し、不足する Q-scheduler と X-dispatcher を補填すること**である。

この現在地を 3 相に圧縮すると:

| 相 | 既存核 | 主要 Wave |
|---|---|---|
| **記述** | CCL / hermeneus | Wave 2-4 |
| **実行** | harness_gate / dispatcher / scheduler | Wave 2-3 |
| **観測** | daimonion_delta.py | Wave 1 |

Wave 計画は、この 3 相を別々に作るのではなく、最終的に 1 つの runtime に再結晶する工程として読むべきである。

ただし Wave 1 の前に、1 つ薄い前段が必要になる。**Wave 0.5 = `CCL → harness gate → Daimonion δ observe` の kernel contract** を固定し、記述・実行・観測の 3 相が同じ invocation 上で閉じる最小条件を先に確定する。

## 2. 6 設計原理 (README と一致)

| 原理 | 根拠 | 処方 |
|:---|:---|:---|
| **O1: Γ/Q 対称性保存** | axiom L294 Basis Γ⊣Q | 全 48 動詞に Γ 関数と Q 関数の両方を実装 |
| **O2: X/Q 双対分離** | axiom L547 + Q 循環定理 P₁ | X = 順序的結合 (1-cell dispatch), Q = 循環的探索 (2-cell scheduler) |
| **O3: 既存資産の再利用優先** | 2 年間の mekhane/fep/ 投資 | 新規実装より共通 interface 抽出を優先 |
| **O4: SKILL.md は UI 層として残す** | prompt と code の bi-directional bridge | 破壊的変更禁止。backend 呼出経路を追加 |
| **O5: 象限純粋性** | axiom L250 象限純粋性原則 | S 動詞は I に委譲、I 動詞は A に委譲、A 動詞は受領のみ |
| **O6: Daimonion δ 統合** | H-series proxy 観測が既存 | H-series evaluator = δ の Γ/Q 拡張 |

## 3. Wave 計画

### Wave 0: Gap analysis (1 週、Codex 委託)

目的: v3.0 24 evaluator と v6.0 48 操作のマッピング表を作成し、不足モジュールを一意に同定する。

タスク:
- 24 定理 (O1-O4, S1-S4, H1-H4, P1-P4, K1-K4, A1-A4) を v6.0 48 操作に射影
- 命名変換を記録 (旧: Hormē → 新: `[ho]` Hormē H9)
- 不足モジュール 24 個 (S極 12 + H-series 12) のスケルトン仕様を生成
- 共通 interface `CognitiveOp` の初期仕様を提案

詳細 plan: `~/.claude/plans/organon-wave0.md`

### Wave 0.5: Kernel contract 固定 (2-3 日)

目的: Wave 0 の棚卸し結果を受けて、Organon の first identity を 48 coverage ではなく **`CCL → harness gate → Daimonion δ observe` の最小 loop** として固定する。

詳細 design: [../02_設計｜Design/organon_kernel_contract.md](../02_設計｜Design/organon_kernel_contract.md)

タスク:
1. 入力面の固定: `ccl_expr` / `_depth` / `_skill_depth` のどれが kernel への正式入力かを整理
2. 実行面の固定: `depth_resolver.py` / `harness_gate.py` / `harness_map.yaml` の役割分担を 1 表に圧縮
3. 観測面の固定: `daimonion_delta.py` を `observe()` 面の最小受け皿として接続する条件を明文化
4. 非目標の明示: Wave 0.5 は 48 evaluator 完成でも full benchmark harness でもない、と先に宣言する

検収:
- 同じ invocation に対して `記述 → profile 選択 → 観測` の 3 相を 1 文と 1 表で説明できる
- Wave 1 の `CognitiveOp` interface が、Wave 0.5 の contract を前提に読むと自然になる
- README / meta / roadmap の 3 面が同じ kernel contract を指している

### Wave 1: Layer α — 48 evaluator 完成 (2-3 週)

目的: 48 動詞それぞれに `CognitiveOp` protocol を実装。

前提: Wave 0.5 で `CCL → harness gate → observe` contract が固定済みであること。

1. 共通 interface 確定: `CognitiveOp.gamma(state) → descent_vector`, `CognitiveOp.Q(state) → circulation_vector`, `CognitiveOp.observe() → Daimonion_δ_proxy`
2. 既存 24 evaluator をラッピング (破壊的変更禁止)
3. S極 12 動詞 (v5.0 追加) の evaluator 新規実装
4. H-series 12 動詞 (v5.4) の evaluator 新規実装 (Daimonion δ の再利用)
5. 48 全モジュールが two_cell.py の 0-cell registry と 1:1 対応すること (pytest 検証)

検収:
- 48 × (Γ + Q + observe) = 144 関数がすべて callable
- 既存 336 tests が回帰なし
- 新規 48 × 3 = 144 unit tests pass

### Wave 2: Layer β — X-series = G_{ij} 対称テンソル dispatcher (2-3 週)

目的: K₆ 15 辺の G_{ij} (対称テンソル = 辺の平衡的結合強度 = Fisher 情報) を runtime 計測し、1-cell dispatch に利用する [SOURCE: circulation_theorem §4.1]。

★ **修正** (2026-04-20): 旧 Wave 2 は X-series を「1-cell 順序結合」と Q-series を「2-cell 循環」の双対として扱っていたが、これは circulation_theorem §4.1 と矛盾。X-series = G (対称テンソル) と Q-series = Q (反対称テンソル) は **完全に独立な 2 テンソル場**である (合計 30 独立パラメータ)。本 Wave は G_{ij} 側のみを扱う。

1. G_{ij} 対称テンソル計測: 各 1-cell の強度 = 座標ペア間の Fisher 情報を runtime 算出
2. 15 辺を D 型 (Afferent 反転) / H 型 (Efferent 反転) / X 型 (両方反転) に分類
3. `X_SI` (知覚→推論), `X_IA` (推論→行為), `X_SA = X_SI ∘ X_IA` (合成) の dispatcher 実装
4. CCL 式 `verb1 >> verb2` が発行されたとき:
   - verb1 実行 (Γ 降下)
   - G_{ij} 型適合性チェック (D/H/X のどれに該当?)
   - Drift 閾値 θ (等方回転下で well-defined, T10 準拠) で doing/being 判定
   - verb2 へ state transfer
   - 不適合なら Sekisho γ が BLOCK
5. two_cell.py の `verify_pentagon` / `verify_triangle_identity` が runtime で pass (L2→L3 は NCR であるため、等方回転下という制約付きで)

検収:
- 15 辺すべてに対応する dispatcher 関数がある (G_{ij} パラメータ付き)
- 不適合 dispatch が確実に BLOCK される (テストケース: S動詞から A動詞への直接 dispatch は X_SA 合成経路のみ許可)
- Drift 閾値 θ が運用上明示される
- 既存 hermeneus が壊れない

### Wave 2.5: H1 検証 — G ブロック対角性の Q 転移検証 (1 週)

★ **新規追加** (2026-04-20): Wave 3 Q-series scheduler の仕様根拠となる H1 (G のブロック対角性が Q に転移するか) を数値実験で検証する [SOURCE: circulation_theorem §4.3]。

背景: 回転面ペアリング (ω_k を 6 座標の 2 座標ペアに対応づける) は候補 A/D 棄却、B 保留、C トートロジーで **未決定** [SOURCE: circulation_theorem §4.4]。H1 検証により G のブロック構造から Q の回転面への転移パターンが同定できれば、Wave 3 の 15 辺循環配置が決定する。

タスク:
1. `verify_h1_q_block.py` (circulation_theorem §4.3 で言及) の既存確認 + 実行 (存在すれば)
2. 存在しない場合、同等の検証スクリプトを新規実装:
   - 6D OU モデル、Schur 分解で ω₁ > ω₂ > ω₃ (異方) + 等方 (ω₁=ω₂=ω₃) の 2 条件
   - ブロック間結合 ε を 0.01-0.1 でスキャン
   - alignment 崩壊点の同定
3. HGK 実装への応用: 現行 mekhane/fep/ 実装で ε が ~10% 以下に収まるかを計測
4. 回転面ペアリング決定:
   - ε ≲ 10% なら候補 B (族ペアリング) を採用
   - ε > 10% なら Wave 3 プロトタイプを族内 6 動詞のみに縮退 (15 辺循環は保留)

検収:
- H1 検証レポート (`03_検証｜Verify/02_h1_rotation_plane.md`)
- 回転面ペアリング決定 or Wave 3 プロトタイプ範囲の縮退判定

### Wave 3: Layer γ — Q-series = Q_{ij} 反対称テンソル scheduler (3-4 週)

目的: K₆ 15 辺の Q_{ij} (反対称テンソル = 辺の非平衡的循環強度) を時間的 scheduler で駆動。Q_{ij} の Schur 分解で 3 回転面 (ω₁, ω₂, ω₃) が生成される [SOURCE: circulation_theorem §3 定理 5]。

★ **修正** (2026-04-20): 旧 Wave 3 は Q を「2-cell 循環」として X と双対扱いしたが、circulation_theorem §4.1 より Q_{ij} は X_{ij} = G_{ij} と独立な反対称テンソル場。回転面ペアリングは Wave 2.5 H1 検証結果に依存。

★ **優先順位**: K₆ 整合三角循環は 5/20 のみで、うち 4 が Te→Fu (Q9) を共有 (エンジン辺) [SOURCE: ccl_category_theory_bridge.md §9.6]。Wave 3 prototype は **Telos 族中心** で実装 (Te→Fu 最優先)。

1. Q_{ij} 反対称テンソル実装: 各 1-cell に Q_{ij} = -Q_{ji} パラメータ付与
2. Schur 分解 → 3 回転面 (ω₁, ω₂, ω₃) の runtime 算出
3. **Te→Fu エンジン辺を最優先で dispatcher に接続** (5/20 整合三角循環のうち 4 が共有)
4. Telos 族 6 動詞を `Q_Value` 循環テンソルで並列 dispatch (族内循環器の prototype)
5. 循環中断条件:
   - `[th]` Thambos (戸惑い) 高値 → Γ_Precision 降下に遷移
   - `[ek]` Ekplēxis (驚愕) → surprise monitoring 発火
6. ω 追跡: runtime で ω_k を計測 → System 1 (ω 小) / System 2 (ω 大) 切替検出 [SOURCE: circulation_theorem §6.1]
7. Daimonion δ との連携 (δ proxy 発火 → scheduler の中断判定)

検収:
- Telos 族 6 動詞で Te→Fu (Q9) を含む Q 循環が 10 cycle 安定動作
- ω_k 計測により System 1/2 切替が runtime で検出される
- surprise 発火時の中断が再現可能
- error rate の改善が計測される (C4 実証)

★ 保留 (Wave 5 以降): Q10 (Pr→Sc, n=1) ボトルネック辺、d3 独立循環 ⑤ {Pr, Sc, Vl}、実測不能 3 循環 (②③⑤)

### Wave 4: 外部化 — MCP 公開 + SKILL.md bidirectional bridge (2 週)

目的: Organon を MCP server として exposure し、SKILL.md からも fep/ からも呼べる形に。

1. `mekhane/mcp/organon_server.py` 新設
2. 48 動詞を MCP tool として公開 (`organon_the`, `organon_noe`, ...)
3. SKILL.md に backend 呼出経路を追加 (破壊的変更なし)
4. `hermeneus` dispatch ルーティングの更新: CCL 式は Organon backend を優先

検収:
- `mcp__organon__*` tool が動作
- SKILL.md 経由の dispatch が Organon backend を通る
- 旧 SKILL.md のみ運用に fallback 可能 (環境変数 `ORGANON_ENABLED=false`)

### Wave 5: 論文化 (並行、通時)

目的: 実装を Yugaku 論文の経験的証拠として articulate する。

1. 確率的機械エッセイ C4 (FT stochastic architecture) の実証セクションに Organon ログを追加
2. LLMの潜在意識の Phase 2 (`/h.report`) が Organon H-series evaluator と統合
3. 将来論文: 「認知操作の operational completion — HGK L3 弱2-圏の runtime 実装」

## 4. Wave 0 の具体タスク

Codex 委託予定。詳細: `~/.claude/plans/organon-wave0.md`

- T1: `mekhane/fep/` の全モジュールを列挙し、各モジュールが実装する定理を抽出
- T2: v3.0 24 定理 × v6.0 48 操作 のマッピング表を生成 (Markdown table)
- T3: 不足する 24 モジュール (S極 12 + H-series 12) のスケルトン仕様を `04_実装｜Impl/02_skeleton_spec.md` に出力
- T4: 共通 interface `CognitiveOp` の draft を `02_設計｜Design/01_cognitive_op_protocol.md` に出力
- T5: 既存 test の回帰点を明記 (どのテストが interface 変更に感応するか)

## 5. 完了条件

v1.0 の完了は以下 5 条件で判定:

1. 48 × (Γ + Q + observe) のすべてが callable で pytest pass
2. X-series 15 dispatcher が runtime で coherence 恒等式を検証できる
3. Q-series 15 scheduler が少なくとも 1 族で安定動作
4. `mcp__organon__*` tool が SKILL.md 経由と直接呼出の両方で動作
5. 確率的機械エッセイ C4 のメタ台帳 §M6 に「Organon 実装が C4 の実化証拠」を記録できる

## 6. 現在地

- 理論刷新: 完了 (axiom v6.0 の operational completion として射程確定)
- 設計刷新: 完了 (3 層 Layer α/β/γ + 6 原則 O1-O6)
- 批評と検証: meta.md §M5 で 5 反論予想を事前列挙 + §M7 で 5 棄却案を記録
- **次の工程**: Wave 0 gap analysis の Codex 委託 (~/.claude/plans/organon-wave0.md) → `ObservationAnchor` / `observe()` adapter の実装位置決定

---

*Created: 2026-04-19*
*Updated: 2026-04-24 (Wave 0.5 kernel contract 詳細設計を追加)*
*Status: v0.4*

**v0.4 修正点**:
- Wave 0.5 詳細 design として `02_設計｜Design/organon_kernel_contract.md` を参照
- 次工程を kernel contract 固定から `ObservationAnchor` / `observe()` adapter の実装位置決定へ更新
- `observe()` は既存実装ではなく、Daimonion δ post-hoc scoring へ接続する adapter contract として扱う

**v0.3 修正点**:
- Wave 0.5 を新設し、`CCL → harness gate → Daimonion δ observe` を Wave 1 前の必須関門として追加
- Wave 1 に Wave 0.5 前提を明記し、「48 coverage が first identity ではない」を工程面にも反映
- 現在地と次工程を `Wave 0 → Wave 0.5 → Wave 1` の順に補正

**v0.2 修正点**:
- Wave 2 を「X-series = G_{ij} 対称テンソル dispatcher」に再定義 (旧「X = 1-cell 順序結合」は誤認)
- Wave 2.5 (H1 検証: G ブロック対角性の Q 転移) を Wave 2 と Wave 3 の間に新規挿入
- Wave 3 を「Q-series = Q_{ij} 反対称テンソル scheduler」に再定義、Telos 族 Te→Fu エンジン辺優先を明示、ω ↔ System 1/2 追跡を追加
- 根拠: circulation_theorem §4.1 (X/Q 独立テンソル場), §4.3-4.4 (回転面ペアリング未決定), §6.1 (ω ↔ System 1/2), §6.7 (異方性 precision), ccl_category_theory_bridge.md §9.6 (整合三角循環 5/20, Te→Fu エンジン辺), conservative_extension_audit.md §遷移 3 (L2→L3 NCR), mb_escalation_conditions.md §命題C (MB𝒻 前提)
