# /ske.struct — n=2.78 の eta 異常面の発散

┌─[V05 派生選択]────────────────────────┐
│ 推奨派生: struct
│ 確信度: 82%
│ 理由: Tolmetes が次に欲しいのは「どこを壊すべきか」の網羅であり、
│       現在の failure は単一点ではなく、観測量・臨界面・proxy・還元面に
│       またがるため、MECE と直交性を優先するのが最も有効。
│ 代替: blind, tension
└────────────────────────────────────────┘

## S-0
- 読み込み済み SKILL:
  - `/home/makaron8426/.claude/skills/ske/SKILL.md`

## S-0.5
- 読み込み済み SOURCE:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/results_strong_coupling/phase2_fractional_acceptance_analysis.md`
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/results_strong_coupling/phase3_fractional_critical_line_analysis.md`
- SOURCE から固定できる事実:
  - `phase0_reference_pass = True`
  - `chain_stable_row_count = 11`
  - `calibrated_stable_row_count = 0`
  - `blocking_reason = reduction_or_criticality_failure`
  - crossing-supported couplings は 5 点存在する
  - その 5 点でも `eta_proxy = 1.87 .. 2.21` で FRG anchor `0.032` から極端に遠い

┌─[PHASE 0: Prolegomena (前限定)]─────────┐
│ テーマ: `n=2.78` の direct quotient lattice で、critical line に乗せても  │
│         `eta_proxy` が 1.87-2.21 に張り付く異常をどう壊すか                │
│ 読み込み済み:                                                       │
│   - `/home/makaron8426/.claude/skills/ske/SKILL.md`                │
│   - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/results_strong_coupling/phase2_fractional_acceptance_analysis.md` │
│   - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/experiments/results_strong_coupling/phase3_fractional_critical_line_analysis.md` │
│ 盲点チェック:                                                       │
│   発動条件: LOW                                                     │
│   テーマの前提: HIGH                                                │
│   フレーミング: HIGH                                                │
│   既存バイアス: HIGH                                                │
│   専門知識の壁: MED                                                 │
│   最高リスク: フレーミング — いまの問いが「eta をどう下げるか」に寄りすぎ、 │
│                 「そもそも何を eta と呼んでよいのか」を温存している        │
│ 溶解: `eta ≈ 2` は physics の信号なのか、測り方の歪みなのか、proxy のねじれ │
│        なのか。まず異常の帰属先を分解せよ。                           │
│ ρ₀: 4                                                               │
│ [CHECKPOINT PHASE 0/3]                                              │
└──────────────────────────────────────────┘

┌─[PHASE 0.5: Epistemic Mapping (内部認知地図)]─┐
│ 確実層 (自分が確実と認識):                    │
│   - chain は主 failure ではない — 根拠: `chain_stable_row_count = 11` まで │
│     上がっており、`blocking_reason` も chain ではなく                │
│     `reduction_or_criticality_failure` に移っている                  │
│   - crossing-supported couplings は存在する — 根拠: critical line 正本で   │
│     support 5-8 の候補が 5 点選ばれている                            │
│   - それでも eta は高い — 根拠: 選ばれた 5 点で `eta_proxy = 1.87..2.21` │
│     に張り付いている                                                 │
│ 不確実層 (自分の内部で揺れている):             │
│   1. `χ ~ L^(2-η)` を current quotient lattice に当ててよいか — A面: yes, │
│      finite-size がまだ浅い / B面: no, estimator 自体が壊れている       │
│   2. crossing で取った線は本当に RG-invariant line か — A面: かなり近い /  │
│      B面: `xi` collapse や coarse grid が擬似交差を作っている            │
│   3. direct quotient lattice は anchor と同じ universality class か —     │
│      A面: yes, まだ calibration 不足 / B面: no, proxy family がずれている │
│ → 破壊対象の優先: `chi-based eta extraction はこの proxy でもそのまま有効` │
│ [CHECKPOINT PHASE 0.5/3]                                             │
└────────────────────────────────────────────────┘

┌─[PHASE 1: Deconstruction (前提破壊)]────┐
│ 暗黙前提:                                │
│   1. current crossing line は eta を読むのに十分近い臨界線である — [ASSUMPTION] │
│   2. `χ ~ L^(2-η)` は direct quotient lattice でもそのまま有効である — [ASSUMPTION] │
│   3. direct quotient lattice は FRG anchor と同じ observable class に属する — [ASSUMPTION] │
│   4. `eta -> gamma_phi` reduction は anchor table を介せば比較可能である — [ASSUMPTION] │
│   5. `L = 6,8,10,12` は asymptotic scaling を見るのに十分である — [ASSUMPTION] │
│ 反転テスト:                              │
│   前提2 FALSE → `eta` を `chi` から読む必要が消え、structure factor ratio, │
│                  two-momentum estimator, connected-field decay などが解禁される │
│   前提3 FALSE → proxy family 比較そのものが主題になり、direct quotient /   │
│                  projected embedding / long-range / hierarchical を並列比較できる │
│   前提1 FALSE → “線の精度”ではなく “臨界面の定義” を作り直す自由度が開く       │
│ ρ₁: 5                                    │
│ [CHECKPOINT PHASE 1/3]                   │
└──────────────────────────────────────────┘

┌─[PHASE 2: Genesis (多次元展開)]──────────┐
│ H1-H5 各仮説: (MMR テンプレート)         │
│                                          │
│ H1 (Orthodox): crossing line の解像度不足が主因。                       │
│   射: coarse pseudo-critical line → refined pseudo-critical manifold     │
│   直交性: 操作変数=`critical_line_resolution`                            │
│   関係: H4 の特殊化                                                   │
│   合成: H2 ∘ H1 = refined manifold 上で新 estimator を読む               │
│   弱点: 線をいくら細かくしても `eta ≈ 2` が残るなら説明力が急落する       │
│                                          │
│ H2 (Contrarian): 臨界線ではなく estimator が壊れている。                 │
│   射: chi-based eta inference → structure-factor / momentum-ratio eta inference │
│   直交性: 操作変数=`eta_estimator_family`                                │
│   関係: H1 と独立、H5 の前提                                           │
│   合成: H2 ∘ H1 = refined line を別 estimator で再読                    │
│   弱点: estimator を変えても同じ異常値なら observable 定義そのものが崩れる │
│                                          │
│ H3 (Extreme): proxy topology が異常を作っている。                        │
│   射: single direct quotient proxy → proxy family comparison surface     │
│   直交性: 操作変数=`proxy_topology`                                      │
│   関係: H1/H2/H4 と独立、H5 の比較対象                                 │
│   合成: H5 ∘ H3 = 各 proxy に transfer-function calibration をかける     │
│   弱点: 実装コストが高く、短期では実験面が広がりすぎる                   │
│                                          │
│ 忘却証拠 (H2): H1 の「線を細かくすれば解ける」を忘れ、測り方そのものを疑った │
│                                          │
│ H4 (Structural): eta を直接読む順序が誤り。                              │
│   射: single-observable exponent fit → RG-invariant manifold-first workflow │
│   直交性: 操作変数=`workflow_order`                                      │
│   関係: H1 の一般化                                                     │
│   合成: H2 ∘ H4 = manifold-first で定めた面上に新 estimator を載せる      │
│   弱点: workflow が正しくても observable 自体が壊れていれば救えない       │
│                                          │
│ 忘却証拠 (H3): H1-H2 の「同じ proxy の中で直す」を忘れ、proxy 自体を比較対象にした │
│ 忘却証拠 (H4): H1-H3 の「どこで読むか/何で読むか」を忘れ、読む順序そのものを変えた │
│                                          │
│ H5 (Blindspot): これは physics 問題でなく metrology 問題である。          │
│   射: raw quotient observables → transfer-function calibrated observables │
│   直交性: 操作変数=`measurement_transfer_function`                       │
│   関係: H2 の双対、H3 の補助                                            │
│   合成: H5 ∘ H2 = calibration 後の estimator / H5 ∘ H3 = proxy ごとの応答補正 │
│   弱点: 校正基準系を別に持たないと空中戦になる                           │
│                                          │
│ 忘却証拠 (H5): H1-H4 の「理論量を直接読みたい」を忘れ、測定器の歪みを先に疑った │
│                                          │
│ 直交性一覧:                              │
│   | 仮説 | 操作する独立変数            | 射                                   | 重複なし | │
│   | H1   | critical_line_resolution    | coarse line -> refined manifold      | ✅ | │
│   | H2   | eta_estimator_family        | chi-fit -> momentum/structure fit    | ✅ | │
│   | H3   | proxy_topology              | one proxy -> proxy family surface    | ✅ | │
│   | H4   | workflow_order              | exponent-first -> manifold-first     | ✅ | │
│   | H5   | measurement_transfer_function | raw observable -> calibrated observable | ✅ | │
│ ρ₂_var: 10 / ρ₂_mor: 10 / ρ₂_comp: 6 │
│ T1-T3: T-1 PASS / T-2 PASS / T-3 PASS │
│ [CHECKPOINT PHASE 2/3]                   │
└──────────────────────────────────────────┘

## 直交性証明
- H1 と H4 は近いが同一ではない。H1 は「どの線を採るか」の分解能、H4 は「何を先に決めて何を後に読むか」の順序であり、操作変数が異なる。
- H2 と H5 も同一ではない。H2 は数の読み方の変更、H5 は観測器の応答補正であり、前者は inference rule、後者は measurement model を操作する。
- H3 は proxy topology を触る唯一の仮説で、他 4 仮説が同一 proxy 内の修正なのに対し、構造の外側を動かす。
- よって 5 仮説は「線」「読み方」「器」「順序」「土台」の 5 軸に分かれている。

## T1-T3
- T-1 射合成:
  - `H2 ∘ H1` は定義可能。
    - 始点: coarse line 上の chi-fit
    - H1 後: refined manifold
    - H2 後: refined manifold 上の structure-factor eta
  - `H5 ∘ H3` も定義可能。
    - 始点: 単一 proxy での raw observable
    - H3 後: 複数 proxy surface
    - H5 後: 各 proxy の calibrated observable
- T-2 結合律:
  - `(H5 ∘ H2) ∘ H4` と `H5 ∘ (H2 ∘ H4)` はどちらも
    “manifold-first で定めた面上の calibrated eta surface” に到達するので、概念的には同じ終点を持つ。
- T-3 恒等射:
  - `id_S` = 現行 pipeline をそのまま保持。
  - どの仮説も `id_S` と合成したとき元の提案内容を失わない。

## Checkpoints
- P-0: 高リスクは framing。`eta をどう下げるか` という問いの立て方自体を壊す必要がある。
- P-0.5: 確実なのは chain 安定化と crossing 候補の存在。不確実なのは estimator/proxy/reduction のどこが主犯か。
- P-1: 最大の解禁自由度は `chi-based eta extraction` を捨てることから生じる。
- P-2: 次の実験面は 5 軸に割れた。もう Metropolis tuning を続ける局面ではない。

## SkQS
- Boundaries Defined: ✅
- Epistemic Mapped: ✅
- Constraints Inverted: ✅
- Orthogonality Proven: ✅
- Space Expanded: ✅
- Categorical Axioms: ✅
- EIG Evaluated: N/A
- 総合: 6/7 PASS

## 結果
- 仮説数: 5
- 最高リスク領域: フレーミング
- ρ統合: `ρ₀=4 + ρ₁=5 + ρ₂=(10,10,6)`
- いま最も価値が高い次: `/pei` で H2 と H4 を連結した実験を作る
  - 具体像: `n=2.78` 固定、current critical manifold candidate 上で `chi-fit` 以外の `eta estimator` を並走させる
- 次点: `/pei` で H5 の metrology branch を最小実装する
  - 具体像: known reference 系に quotient observable を流し、transfer-function を測る

## WM
- $goal: `eta ≈ 2` の帰属先を、criticality / estimator / proxy / reduction のどこかに切り分ける
- $current_state: chain は安定、critical line 候補もあるが、eta は依然として anchor 帯域外
- $constraints: current SOURCE だけでは `physics の異常` と `measurement の歪み` をまだ分離できない
- $next_step: H2×H4 を最短で打ち、`chi-fit` を外した eta surface を同じ critical manifold 上で再測定する
