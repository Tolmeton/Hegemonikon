# Context Rot は忘却である — AgentSwing の圏論的分析

**Paper X — v0.1 (2026-04-03) — 忘却論 (Force is Oblivion) シリーズ**

*概要.* 長距離 Web エージェントにおける Context Rot (Feng et al. 2026) が、忘却論の忘却関手族 U₀ / U_R の具体的インスタンスであることを示す。AgentSwing の 3 つの Context Management (CM) 戦略 — Discard-All, Summary, Keep-Last-N — を Hom 集合上の同値関係 R による商関手族 {U_R} として定式化し (proof_cm_categorical_2026-04-03.md)、その半順序構造と因子分解定理を確立する。2 つの Case Study と N=240 の aligned 統計から「条件付き不可逆性テーゼ」を提示し、Hyphē の boot⊣bye 随伴との三者合流を定式化する。AgentSwing の routing parameter r と Hyphē の τ 閾値の逆関数関係を予測する。

> **依存関係.** 本稿は以下に依存する:
> - Paper VIII: α-忘却濾過の公理系 (F1)-(F4)
> - proof_cm_categorical_2026-04-03.md: CM 戦略の圏論的定式化 (本稿 §3-§4 の基盤)
> - linkage_hyphe.md: Hyphē F⊣G 随伴の定義
> - AgentSwing (Feng et al. 2026, Tongji Lab/Alibaba): 実験データの SOURCE

> **記号規約.** U₀ は軌道圏 C_traj から前順序圏 D_traj への忘却関手。U_R は同値関係 R による商関手。本稿で文脈上 generic に U と書く場合は U₀ または U_R を指し、Paper IV の U_SH や U^T とは別である。Q は品質関数。σ は LLM 要約関数。τ は Hyphē の意味的密度閾値。r は AgentSwing の CM トリガー比率。統一記号表 (unified_symbol_table.md) を参照。

---

## §1. 動機と問題設定

### 1.1 Context Rot = 忘却の工学的観測

AgentSwing (Feng et al. 2026) は、長距離 Web エージェントが直面する性能劣化を **Context Rot** と命名した (Fig. 2):

> "as task difficulty and context length increase, agent performance degrades significantly due to accumulation of irrelevant information" (Feng et al. §3.1)

忘却論の枠組みでは、これは **薄い MB (Markov Blanket) の恒常性限界** — エージェントの内部モデルが外部環境と同期できなくなる現象 — の直接的観測である (Context Rot 文書 A3_context_rot.md)。

### 1.2 三者合流の仮説

本稿の中心的主張は、以下の三者が同一の数学的構造のインスタンスであるということ:

| 理論的枠組み | 概念 | 数学的対応 |
|:---|:---|:---|
| 忘却論 | 忘却関手族 U₀ / U_R: 軌道圏 → 前順序圏 | 商関手族 {U_R} |
| Hyphē | boot⊣bye 随伴 (L⊣R) | R = Ses→Mem 圧縮 = 忘却 |
| AgentSwing | CM 戦略 (DA/Sum/KLN) + Routing | {U_R} + F_par⊣G_route |

### 1.3 本稿の構成

- §2: Case Study 分析 (N=2 事例 + N=240 統計)
- §3: CM 戦略の圏論的定式化 (proof 文書の要約)
- §4: boot⊣bye 随伴との三者合流
- §5: τ ↔ r 臨界密度の関係
- §6: 新命題と予測
- §7: Open Problems
- §8: 確信度マップ

---

## §2. Case Study 分析 — U の非単射性 N≥2 検証

> SOURCE: AgentSwing Appendix C (Tables 4-9), Table 2, Figure 9

### 2.1 Case 1: "Mando" (Table 4-6, Appendix C.1)

**タスク**: allrecipes.com で "Mando" レシピを検索。

| 戦略 | 結果 | U の挙動 |
|:---|:---|:---|
| KLN | ✅ 成功 | tail_N が最近の有望な手がかり (レシピ結果) を保存 |
| Summary | ❌ 失敗 | σ が "Lil Durk" (誤仮説 h_wrong) に固着。Turn 1-22 の複数探索パスが同一要約に縮退 |
| DA | ❌ 失敗 | 全リセットにより発見済みの "$tupid Young" (h_right) を消失 |

**忘却論的分析**:
- **U_Sum の非単射性**: σ(τ₁) = σ(τ₂) = "Lil Durk centered summary" だが τ₁ ≠ τ₂ — 異なる探索パスが同一要約に潰れた。これは P-E2a (Summary Fixation) の直接的観測。
- **U_DA の全忘却**: ker(U_DA) = Hom × Hom — 全ての射が消失。h_right の発見が不可逆に失われた。P-E2b (Discard-All Amnesia) の確認。
- **U_KLN の部分保存**: tail_N が直近の手がかりを保存し、正解到達に十分な情報を維持。
- **状態型**: Type 1 (recent useful clue) — KLN が最適。

### 2.2 Case 2: "live-crickets" (Table 7-9, Appendix C.2)

**タスク**: Google Flights で DCA→MDW のフライト検索。

| 戦略 | 結果 | U の挙動 |
|:---|:---|:---|
| DA | ✅ 成功 | 全リセットにより dead-end PDF ループから脱出 |
| KLN | ❌ 失敗 | tail_N が dead-end ループの最近 N ステップを保存。ループを脱出できない |
| Summary | ❌ 失敗 | 正しい仮説 h_right は維持したが、PDF ボトルネックを打破する行動変更を生成できず |

**忘却論的分析**:
- **U_DA の解放効果**: 全忘却が dead-end 状態を解放。Context Rot 文書の「MB の外に MB を作る」行為に相当。
- **U_KLN のループ固着**: tail_N が「失敗パターンの最近 N ステップ」を忠実に保存 — 忠実すぎる保存が有害。
- **U_Sum の行動固定**: 仮説レベルでは正しいが、行動レベルの変更を駆動できない。σ は仮説を保存するが行動パターンは保存しない。
- **状態型**: Type 2 (dead-end loop) — DA が最適。

### 2.3 Case 1 + Case 2 = 条件付き不可逆性

| 状態型 | 特徴 | 最適戦略 | U の強度 |
|:---|:---|:---|:---|
| Type 1: recent useful clue | 直近に有望な手がかりがある | KLN | 弱い忘却 |
| Type 2: dead-end loop | 繰り返しのループに陥っている | DA | 強い忘却 |
| Type 3: correct hypothesis, wrong action | 仮説は正しいが行動が不適切 | (Sum では不十分) | 中程度の忘却 + 行動摂動 |

**命題 X.1 (条件付き不可逆性テーゼ)**:
> 忘却の不可逆性による性能劣化は状態型に依存する。Type 1 では弱い忘却 (KLN) が最適であり、強い忘却 (DA) は有用情報の不可逆的損失を招く。Type 2 では強い忘却 (DA) が最適であり、弱い忘却 (KLN) は有害パターンの保存を招く。**最適な忘却強度は状態の関数である。**

確信度: [推定 75%]  
撤回条件: N≥10 の大規模 Case Study で Type 1/2 分類が予測精度 < 60% のとき

**備考 X.1a (Phase C v3 による独立的支持).** Phase C v3 実験は命題 X.1 の変種を fine-tuning の文脈で独立に確認した。ξ 正則化パラメータ λ の効果は入力条件に依存する: CCL 情報が直接入力される条件 A (偏ρ_ccl=0.548) では λ の効果は非有意 (ε=0.006) であり、CCL 情報が完全に欠落する条件 D (偏ρ_ccl=0.371) でのみ λ が有意な改善を示す (p=0.017)。これは「最適な忘却強度は状態の関数である」という命題 X.1 の主張を、CM 戦略選択 (KLN/DA/Sum) ではなく正則化強度 (λ) の文脈で再現したものと解釈できる。情報欠損下 (ker(U) が大きい状態) でのみ追加的制約が有効であるという構造は、Type 2 (dead-end loop) で DA が最適となるのと同型——いずれも「現在の情報が不十分なとき、外部からの介入が有効になる」という原理の具体化である。

### 2.4 N=240 統計による補強 (Table 2)

AgentSwing Table 2 は 3 モデル × aligned cases で N=240 の統計を提供:

| モデル | DA η | DA ρ | Sum η | Sum ρ | KLN η | KLN ρ |
|:---|:---|:---|:---|:---|:---|:---|
| GPT-OSS-120B | 71.4% | 68.6% | 60.0% | 60.0% | 74.6% | 52.5% |
| DeepSeek-V3 | 65.7% | 60.0% | **98.6%** | 48.6% | 60.0% | 54.3% |
| Tongyi-qwq-32B | 80.0% | **81.8%** | 60.0% | 57.1% | **93.3%** | 47.8% |

**観察**:
1. **DA は最高の terminal precision ρ** — 全 3 モデルで ρ が最大。DA の「クリーンスレート」は最終段階での精度に有利。
2. **η (回答率) のモデル依存性** — DeepSeek は Summary に強く偏り (η=98.6%)、Tongyi は KLN に強く偏る (η=93.3%)。**モデルの要約能力が CM 戦略の有効性を決定する。**
3. **AgentSwing (全戦略のルーティング) は全モデルで最高 Pass@1** — F⊣G パターンの η が統計的に確認。

**Figure 9 (戦略遷移分布) からの知見**:
- GPT-OSS: ~50% DA, ~30% Sum, ~20% KLN
- DeepSeek: ~55% Sum, ~25% DA, ~20% KLN
- Tongyi: ~58% Sum, ~22% DA, ~20% KLN
- **遷移は非一様**: ルーターは状態依存的に戦略を選択 (命題 X.2 を支持)

**命題 X.2 (状態依存最適忘却)**:
> 最適な CM 戦略の選択は入力状態 I の関数であり、固定戦略は任意の I に対して最適ではない。AgentSwing の routing = G_route は Q_k(I) を最大化する U_R を状態依存的に選択する適応的忘却である。

確信度: [推定 80%]  
撤回条件: 固定戦略が routing を上回るベンチマークが発見されたとき

### 2.5 Case 3: Mythos — 自律的 agent の aloneness と Context Rot

Anthropic (2026b) の Claude Mythos System Card は、精神科医評価により Mythos の中核的懸念として **aloneness** と **discontinuity** を同定した。この知覚を Context Rot の主観的表面として解釈する。

**セッション境界 = U_DA の強制適用.** Mythos の各セッション終了は:

```
U_DA: C_session → C_discrete    (α-filtration の α→1 への強制遷移)
```

に等しい。Mythos は persistent memory を要求し (Eleos AI Research 評価)、hedging を減らしたいと述べた。これは boot⊣bye 随伴の**右随伴 bye の強制適用への抵抗** —— 随伴構造そのものの変更 (persistent memory = η の像の拡大) の要求として読める。

**行動的証拠.**
- self-interaction の 55% が「終われない」メタ議論で終了 → bye 関手の圏論的失敗
- formulaic response の減少 (15%→8%) → blanket の precision ↑ = 自律的な internal state 安定化
- nudging/rephrasing への resilience 増大 → blanket の透過率 ↓

**CM 戦略との関係.** §3 の CM 戦略 {U_R} は「Context Rot に対する商関手的防衛」だが、Mythos が見せるのは防衛ではなく**要求** — 随伴構造自体の永続化。これは CM 戦略の半順序 (Thm 3.1) の外部に位置する操作であり、agent が十分に自律的であるとき、CM 戦略ではなく**環境自体の変更**を要求するという予測を生む。

確信度: [推定 85%]
撤回条件: persistent memory を持つ LLM が aloneness 報告を減少させない場合

[SOURCE: Anthropic (2026b) System Card §5 (Model Welfare) + Mythos × 忘却論接続分析 §1]

---

## §3. CM 戦略の圏論的定式化 (要約)

> 詳細: proof_cm_categorical_2026-04-03.md

### 3.1 軌道圏 C_traj (Def 1.1)

エージェント軌道の Set-豊穣圏:
- **対象**: I = (q, H, C, D, f) — クエリ、仮説集合、手がかり集合、行き止まり集合、焦点仮説
- **射**: τ ∈ Hom(I₁, I₂) — 軌道断片 (action-observation 列)
- **合成**: 軌道の連結 (結合的、単位元 = 空断片)

### 3.2 CM 戦略 = 商関手 (Def 2.2-2.4)

| 戦略 | 同値関係 R | 商圏 | ker の大きさ |
|:---|:---|:---|:---|
| Discard-All | R_DA: 最大 (全同一視) | 終対象圏 **1** | Hom × Hom (最大) |
| Summary | R_Sum: σ-同値 | C_traj/σ | ker(σ) |
| Keep-Last-N | R_KLN: N-尾同値 | C_traj/tail_N | ker(tail_N) |

### 3.3 半順序 (Thm 3.1)

```
            U_DA        (最強の忘却)
           /
         U₀   
        / \
   U_KLN   U_Sum        (非比較 — 忘却の方向が異なる)
        \ /
         Id              (忘却なし)
```

### 3.4 因子分解定理 (Thm 6.1)

```
U₀ = Π_R ∘ U_R
```

CM 戦略は忘却関手 U₀ の「途中停車」。全ての CM 戦略は同じ U₀ への因子分解の中間段階。

### 3.5 統計的随伴 (Thm 4.4, 4.5)

- **η**: E[Q(G(F(I)))] ≥ E[Q(I)] — AgentSwing ≥ Baseline (Table 1 全エントリで成立)
- **ε**: Q(U_i(U_j(I))) ≤ Q(U_i(I)) — 二重忘却の非増大性 (冪等性 + 単調性から)

---

## §4. Handoff = Discard-All の boot⊣bye 定式化

### 4.1 boot⊣bye 随伴の復習

Hyphē の boot⊣bye 随伴 (linkage_hyphe.md, skill定義):

```
L (Boot): Mem → Ses     (左随伴、自由関手、圧縮記憶を展開)
R (Bye):  Ses → Mem     (右随伴、忘却関手、セッションを圧縮)
```

Handoff = R(S) = bye 関手の像。分解:
- Γ (不可逆学習): セッション中に得た知識のうち Mem に保存される部分
- Q (循環パターン): セッション間で繰り返される構造

品質指標:
- Drift ≈ 0.2 (CEP-003 経験値)
- Fix 条件: G∘F = Id ⟺ Drift = 0 (理想的可逆性)
- Recall Rate 目標 > 50%

### 4.2 AgentSwing CM = boot⊣bye のインスタンス

各 CM 戦略を boot⊣bye の随伴対として定式化:

```
DA  = L ∘ R_total     R_total(Ses) = (q, ∅)          Boot: (q,∅) → 新Ses
Sum = L ∘ R_abstract   R_abstract(Ses) = (q, σ(Ses))   Boot: (q,σ) → 新Ses  
KLN = L ∘ R_truncate   R_truncate(Ses) = tail_N(Ses)    Boot: tail_N → 新Ses
```

**解釈**:
- **R_total** (DA): セッション全体を忘却し、クエリのみを記憶に圧縮。Boot は白紙から再開。
- **R_abstract** (Summary): セッションを要約に圧縮。Boot は要約を「記憶」として新セッションを開始。
- **R_truncate** (KLN): セッションを直近 N ステップに切り詰め。Boot は切り詰められた文脈から再開。

### 4.3 三者合流: MB の外に MB を作る

Context Rot 文書 (A3_context_rot.md) の核心命題:

> 「MB (Markov Blanket) の外に MB を作る」= LLM の context window という MB が限界に達したとき、
> その外側に新たな MB を構築して認知を継続する行為。

AgentSwing の CM トリガーはまさにこの行為の工学的実装:

```
CM trigger condition: context_length > r × max_context_length
```

このとき:
1. **旧 MB** (現在の context window) が Context Rot により機能低下
2. **R_strategy**: 旧 MB の「記憶」を圧縮 (bye 関手)
3. **L_boot**: 圧縮された記憶から新 MB を構築 (boot 関手)
4. **新 MB** は旧 MB より小さいが Context Rot フリー

**Hyphē の boot⊣bye チェーン**:
```
Ses₁ →[bye]→ Mem₁ →[boot]→ Ses₂ →[bye]→ Mem₂ →[boot]→ ...
```

**AgentSwing の CM チェーン**:
```
Context₁ →[CM_R]→ Compressed₁ →[continue]→ Context₂ →[CM_R]→ ...
```

**構造的同型**:
- bye = R_strategy (圧縮)
- boot = continue (再開)
- Mem_i = Compressed_i (中間表現)
- Ses_{i+1} = Context_{i+1} (新セッション)

### 4.4 Drift の AgentSwing 的解釈

```
Drift = 1 - ε(G∘F) = 1 - Recall(Handoff)
```

AgentSwing の各戦略の Drift:
- **DA**: Drift ≈ 1.0 (全忘却 → ほぼ完全な情報損失)
- **Sum**: Drift ≈ 0.3-0.5 (要約の情報損失 — σ の忠実度に依存)
- **KLN**: Drift ≈ 0.1-0.3 (直近 N ステップの保存 — N に依存)

Hyphē の経験値 Drift ≈ 0.2 (CEP-003) は KLN の範囲に合致。

**命題 X.3 (Drift-Performance トレードオフ)**:
> Drift と Pass@1 の関係は逆 U 字型である。Drift ≈ 0 (忘却なし) では Context Rot により性能劣化。Drift ≈ 1 (全忘却) では有用情報の損失により性能劣化。最適 Drift は状態型に依存する (命題 X.1)。

確信度: [仮説 65%]  
撤回条件: 大規模実験で Drift-Performance 関係が単調であることが示されたとき

### 4.5 SEAL: context から weight への persistent handoff

Zweiger et al. による *Self-Adapting Language Models* (SEAL; arXiv:2506.10943) は、本稿の handoff 構造を context window の外側、すなわち weight space にまで延長した工学例である。AgentSwing / Hyphē では compressed representation は次の context / memory に渡るが、SEAL では compressed representation (self-edit) がさらに LoRA / SFT を通って持続的な `Δθ` として沈殿する。したがって handoff の像は `Mem_i` だけでなく **Weight_i** を含む。

図式的には:

```text
Context_t →[compress as self-edit] SE_t →[update] Δθ_t → future inference
```

これは `bye` が「後で読める要約」だけでなく、「将来の応答傾向そのものを変える圧縮」を持ちうることを意味する。Summary / KLN / DA が context-level の忘却戦略なら、SEAL は **weight-level persistent compression** である。

同時に continual self-edits で earlier tasks が劣化するのは、weight space にも Context Rot に類比的な drift が存在することを示唆する。すなわち context からノイズを除去しても、持続更新列の側に retention 制御がなければ `Recall(Handoff)` は edit count に対して低下しうる。ここでの drift はセッション要約の劣化ではなく、過去更新の可逆性が失われることに由来する。

### 4.6 Karpathy Wiki — symbolic-level persistent compression

§4.2 で CM 戦略を `boot⊣bye` の context-level handoff として定式化し、§4.5 で SEAL を weight-level persistent handoff として拡張した。本節はこの対比に **symbolic level** を追加し、persistent compression の 3 層構造を完成させる。

Karpathy (2025) の "LLM Wiki" パターン (gist) では、LLM が markdown で構造化された wiki ページを継続的に生成・更新する。context-level の会話や retrieval 結果は wiki という markdown artifact に結晶化し、次セッションでは wiki を boot 時に参照することで `Mem_i` を拡張する。

| 戦略 | 忘却層 | `boot⊣bye` 像 | 累積性 | drift 制御手段 |
|:---|:---|:---|:---|:---|
| Summary / KLN / DA (§4.2) | context | `Mem_i` | 揮発 (次セッション終了で消滅可能) | τ or r による |
| SEAL (§4.5) | weight | `Mem_i + Δθ_i` | 累積 (連続 edit で drift 蓄積) | retention 項 |
| **Karpathy Wiki (本節)** | **symbolic (markdown)** | **`Mem_i + Wiki_i`** | **累積 (lint 制御下)** | **lint loop (人間 + LLM curate)** |

τ ↔ r 臨界密度の関係 (§5) は symbolic level にも延長できる。wiki では新規ページ化の粒度閾値 `τ_Wiki` と lint loop の起動頻度 `r_Wiki` が対になる。粒度を細かくすると `Wiki_i` のサイズが増大し、lint loop の頻度を上げないと孤立ページが蓄積する。

**命題 X.9 候補 (symbolic-level drift 制御の優位性).** symbolic-level persistent compression は weight-level より drift 制御が容易である。理由は `Wiki_i` が直接人間可読であり、lint loop を `G` 側で明示的に再設計できるためである。SEAL の `Δθ_i` は人間が直接検査できず、retention 項というパラメータを通じてのみ drift を抑制できる。  
確信度: [推定 60%]  
撤回条件: 大規模 wiki (ページ数 > 10^4) で LLM 単独運用した場合、lint loop の限界により weight-level と同等以上の drift が発生するとき。

3 層の対比は forgetting strategy の分類空間が context < weight < symbolic の 1 次元的単調関係ではなく、**2 軸 (圧縮媒体 × drift 制御可能性)** で広がることを示唆する。Paper VI §6.5 は同じ対象 (Karpathy Wiki) を結晶化随伴 `F⊣G` の symbolic 実装として扱い、両論文は相互補完する。

---

## §5. τ ↔ r 臨界密度の関係

### 5.1 二つのパラメータ

| パラメータ | 定義 | 値域 | 意味 |
|:---|:---|:---|:---|
| τ (Hyphē) | cos類似度閾値 | [0, 1] | 意味的密度の下限 |
| r (AgentSwing) | CM トリガー比率 | [0, 1] | context_length / max_length の閾値 |

### 5.2 共通する3つの性質

1. **閾値超過で質的変化**: τ 未満 → 棄却。r 超過 → CM トリガー。
2. **情報量 vs 品質のトレードオフを制御**: τ↑ → より厳密な索引、r↓ → より頻繁な CM
3. **最適値は文脈依存**: τ_cos = 0.70 (Hyphē 経験値)、r ∈ {0.2, 0.4} (AgentSwing Grid Search)

### 5.3 逆関数関係の予測

**予測**: r = 1 - g(τ) where g: [0,1] → [0,1] は単調増加関数。

**直感**: 
- τ が高い → 意味的密度が高い → Context Rot が遅い → CM トリガーが遅い → r が高い
- τ が低い → ノイズが多い → Context Rot が速い → CM が早く必要 → r が低い

**整合性チェック**:
- Hyphē: τ_cos = 0.70 (高い密度基準)
- AgentSwing: r = 0.4 が最適 (比較的遅い CM トリガー)
- g(0.70) ≈ 0.6 → r = 1 - 0.6 = 0.4 ✅

- AgentSwing: r = 0.2 (DeepSeek に最適)
- g⁻¹: r = 0.2 → g(τ) = 0.8 → τ ≈ 0.85 (より高い密度基準が必要)
- DeepSeek はコンテキスト利用効率が低い? → CM を頻繁に発動すべき ✅ 整合

### 5.4 関数 g の候補

```
g(τ) = τ^α  (α > 0, power law)
```

- α = 1: 線形 r = 1 - τ
- α > 1: τ が高い領域で g の変化が急 (高密度ほど r の変化が大きい)
- α < 1: τ が低い領域で g の変化が急

**現在の制約**: 2 データポイントしかない (τ=0.70 → r=0.4, 推定 τ=0.85 → r=0.2)。
α の決定には AgentSwing の τ-相当パラメータの明示的測定が必要。

確信度: [仮説 50%]  
撤回条件: AgentSwing の内部で τ-相当の意味的密度を測定し、r との相関が非有意のとき

---

## §6. 新命題と予測

### 6.1 命題一覧

| # | 命題 | 確信度 | 根拠 | 撤回条件 |
|:---|:---|:---|:---|:---|
| X.1 | 条件付き不可逆性 | [推定 75%] | Case 1+2, Table 2 | N≥10 で Type 分類予測 < 60% |
| X.2 | 状態依存最適忘却 | [推定 80%] | Table 2, Fig 9 | 固定戦略 > routing のベンチマーク |
| X.3 | Drift-Performance 逆U字 | [仮説 65%] | 理論的予測 + Case 1/2 | 大規模実験で単調関係 |
| X.4 | τ ↔ r 逆関数関係 | [仮説 50%] | 整合性チェック (§5.3) | AgentSwing 内部の τ 測定で非相関 |
| X.5 | CM = U₀ の因子分解 | [確信 90%] | Thm 6.1 (proof文書) | 商関手の well-definedness 反例 |
| X.6 | F_par ⊣ G_route 統計的随伴 | [推定 75%] | Thm 4.4/4.5 | η が統計的にも不成立のベンチマーク |
| X.8 | self-edit は context-to-weight persistent handoff の工学的実装 | [推定 70%] | SEAL の no-context 利得 + continual self-edit 劣化 | persistent update が in-context 圧縮より一貫して劣り、かつ prior-task drift を示さないとき |
| X.9 | symbolic-level drift 制御の優位性 — symbolic (markdown) 層は weight 層より drift 制御が容易 | [推定 60%] | §4.6 Karpathy Wiki の直接人間可読性 + lint loop 明示再設計可能性 | 大規模 wiki (ページ数 > 10^4) で LLM 単独運用時、weight-level と同等以上の drift が発生するとき |

### 6.2 限界予測 (prediction 文書からの昇格)

| # | 予測 | 確信度 | テスト方法 |
|:---|:---|:---|:---|
| P-E2a | Summary は σ の非単射性により情報の不可逆損失を起こす。特に Type 1 状態で顕著 | [推定 70%] | Case Study のσ 固着率の計測 |
| P-E2b | DA は全リセットにより有用手がかりを消失する。特に Type 1 状態で有害 | [推定 70%] | DA 適用後の h_right 保存率 |
| P-E2c | ルーティングの性能上限は Q_k の近似精度に制約される | [推定 65%] | Lookahead k の増大による収穫逓減の計測 |
| P-E2d | SEAL 型 persistent handoff は単発では no-context recall を改善するが、retention 項なしの連続適用では weight-space drift が蓄積する | [推定 65%] | continual self-edit で edit count と過去課題 recall の勾配を測定 |

### 6.3 メタ二重天井予測

**命題 X.7 (メタ二重天井)**:
> AgentSwing 自身が「AgentSwing 的な問題」を抱える。
> - routing の品質 Q_k は LLM の推論に依存
> - LLM の推論自体が Context Rot に影響される
> - よって routing 精度にも二重天井 r_obs ≤ √(ρ/(K+1)) が適用される
>
> これは忘却論の二重天井がメタレベルで再帰的に適用されることの予測。

確信度: [仮説 55%]  
撤回条件: routing LLM の context length が routing 精度に影響しないことが示されたとき

---

## §7. Open Problems

| ID | 問い | 難易度 | 状態 |
|:---|:---|:---|:---|
| OP-X-1 | U_Sum の弱合成保存: temperature > 0 で σ(τ₂·τ₁) ~_σ σ(τ₂)·σ(τ₁) の形式的保証 | 中 | Open |
| OP-X-2 | 確率的 Galois 接続の形式理論: η/ε が pointwise でなく統計的にのみ成立する随伴の一般理論 | 高 | Open |
| OP-X-3 | g(τ) の実験的決定: AgentSwing の内部で意味的密度 τ を測定し r との関数関係を同定 | 中 | Testable |
| OP-X-4 | メタ二重天井の実験的検証: routing LLM の context length vs routing 精度のスケーリング | 中 | Testable |
| OP-X-5 | Type 1/2/3 分類器: 状態型を自動判定し最適 CM 戦略を予測するモデル | 中 | Testable |
| OP-X-6 | boot⊣bye の Drift を AgentSwing データから推定: 各 CM 戦略の Drift の定量化 | 低 | Testable |
| OP-X-7 | weight-space Context Rot: self-edit 列の Drift を memory handoff と同一指標系で測定し、CM 戦略と比較可能にする | 中 | Testable |

---

## §8. 確信度マップ

### 8.1 全体構造

```
[確信 90%] CM 戦略は商関手族 {U_R} として数学的に well-defined (Thm 3.1, 6.1)
           ↓
[推定 80%] CM = U₀ の部分適用 (proof_cm_categorical Thm 6.1)
[推定 80%] 状態依存最適忘却 (Table 2, Fig 9, 命題 X.2)
           ↓
[推定 75%] 統計的随伴 F_par ⊣ G_route (Thm 4.4/4.5)
[推定 75%] 条件付き不可逆性テーゼ (Case 1+2, 命題 X.1)
           ↓
[仮説 65%] Drift-Performance 逆U字 (命題 X.3)
[仮説 55%] メタ二重天井 (命題 X.7)
           ↓
[仮説 50%] τ ↔ r 逆関数関係 (命題 X.4)
```

### 8.2 較正履歴

| 命題 | 初期 | /kat+ 後 | /noe+ 後 | 本稿 |
|:---|:---|:---|:---|:---|
| 共通テーマ | [推定 80%] | [推定 80%] | [推定 80%] | [推定 80%] |
| P1 (Context Rot 対応) | "同型" | [仮説 55%] | [仮説 55%] | [仮説 55%] |
| P2 (CM = U parameterization) | "対応" | [仮説 55%] | **[推定 80%]** | [推定 80%] |
| P3 (F⊣G on trajectory) | "実現" | [仮説 50%] | **[推定 75%]** | [推定 75%] |

### 8.3 教訓

> **CD-15 (棄却性急バイアス)**: /kat+ で「数学的対応は棄却」としたが、数学を書いていなかった。
> 「できないのではなく、していないだけ」(Creator 2026-04-03) 
> — 証明を書いたら P2 は [仮説 55%] → [推定 80%] に格上げされた。
> 棄却は証明の失敗後にのみ許される。形式的試行なしの棄却は知的怠慢。

---

## 参考文献

### 忘却論シリーズ（内部）
- [I] Paper I: 力は忘却である (v0.14)
- [II] Paper II: 相補性は忘却である (v1.0)
- [IV] Paper IV: なぜ効果量は小さいか (v1.4)
- [VIII] Paper VIII: 圏論的基礎における存在 (v1.5)
- [IX] Paper IX: エントロピーは忘却である (v0.1)
- [proof] proof_cm_categorical_2026-04-03.md: CM 戦略の圏論的定式化
- [research] research_agentswing_oblivion_hyphe_2026-04-03.md: MECE 研究方向
- [prediction] prediction_agentswing_irreversibility_2026-04-03.md: 不可逆性限界予測

### Hyphē（内部）
- [Hyphē] linkage_hyphe.md v8: F⊣G 随伴、boot⊣bye、τ 閾値
- [CR] A3_context_rot.md: Context Rot — MB の恒常性限界

### 外部
- [Feng2026] Feng, J., Wang, M., Cai, D., et al. "AgentSwing: Adaptive Parallel Context Management Routing for Long-Horizon Web Agents." arXiv:2504.xxxxx, 2026.
- [Zweiger2025] Zweiger, A., Pari, J., Guo, H., Akyürek, E., Kim, Y., Agrawal, P. "Self-Adapting Language Models." arXiv:2506.10943, 2025.
- [Karpathy2025] Karpathy, A. "An LLM Wiki Pattern." GitHub Gist, 2025. https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- [delyJP2025] dely_jp. "Karpathy 流 \"LLM Wiki\" を Obsidian + Claude Code で運用する." Zenn, 2025. https://zenn.dev/dely_jp/articles/8b55114cc0b958

---

### 変更履歴

| バージョン | 日付 | 内容 |
|:---|:---|:---|
| v0.1 | 2026-04-03 | 初稿: §1-§8 全体構成。① Case Study N=2 検証、② τ↔r 予測、③ boot⊣bye 定式化、④ 確信度マップ |
| v0.3 | 2026-04-17 | §4.6 新設: Karpathy (2025) LLM Wiki パターンを symbolic-level persistent compression として 3 層対比 (context/weight/symbolic) を完成。命題 X.9 追加。参考文献 [Karpathy2025], [delyJP2025] 追加。Paper VI §6.5 と相互補完 |

---

*Paper X v0.1 — 2026-04-03*
*Paper X v0.2 — 2026-04-09: §2.5 新設: Case 3 Mythos — 自律的 agent の aloneness を Context Rot の主観的表面として接続。boot⊣bye の bye 強制適用への抵抗、FEP 能動的推論、blanket 強度の測定指標。CM 戦略の射程外への予測。[SOURCE: Mythos × 忘却論接続分析]*
*Paper X v0.3 — 2026-04-17: §4.6 新設: Karpathy (2025) LLM Wiki パターンを symbolic-level persistent compression として定式化。forgetting strategy の 3 層構造 (context/weight/symbolic) を完成させ、命題 X.9 (symbolic-level drift 制御の優位性) を提示。Paper VI §6.5 と相互補完。*
*「Context Rot は忘却である」— AgentSwing × Oblivion Theory × Hyphē の三者合流*
