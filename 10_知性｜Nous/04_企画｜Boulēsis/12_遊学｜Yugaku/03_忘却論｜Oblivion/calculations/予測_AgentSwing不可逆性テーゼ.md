# 忘却の不可逆性テーゼ → AgentSwing の限界予測

> SOURCE: Oblivion Theory (abstraction_oblivion_formalization_v1.md §6), AgentSwing (Feng et al. 2026)
> 親文書: research_agentswing_oblivion_hyphe_2026-04-03.md §E2
> 日付: 2026-04-03
> 確信度: 全体 [推定 70%]
> /kat+ 較正 (2026-04-03): 写像は「数学的対応」ではなく「整合的な構造的類比」。Case Study はN=1で過度な一般化に注意 (CD-14, CD-3 検出)。
> /noe+ 再較正 (2026-04-03): proof_cm_categorical_2026-04-03.md で構成的証明。U_Sum の弱合成保存条件下で数学的対応が成立。CD-14 は撤回 — 構造的類似を同型に「格上げ」したのではなく、実際に数学を書いて成立を確認した。
> 限界予測 P-E2a/b/c は「U の非単射性 + 商関手の因子分解 (Thm 6.1)」から導出される条件付き予測として有効 [推定 75%]

---

## §1. 不可逆性テーゼの復習

### 1.1 忘却関手 U の非単射性

```
U: C (豊穣圏) → D (前順序圏)
   射の厚み    →  射の有無

非単射性: ∃ x₁ ≠ x₂ ∈ C : U(x₁) = U(x₂)
   「悲しみ+怒りの複合感情」と「純粋な悲しみ」
   → U を通すと両方 「負の感情」に写る
   → 区別が消え、復元不能
```

### 1.2 不可逆性の定式化

```
復元コスト非対称性:
   Cost(ρ_abstract ↑) < Cost(ρ_concrete の復元)

理由: U の右随伴 N は部分復元しか提供しない
   N ∘ U ≠ Id_C  (η: Id_C → N ∘ U は同型ではない)
   U ∘ N = Id_D   (ε: U ∘ N → Id_D は同型)

直感: 圧縮は一方向。JPEG → 元の RAW には戻らない。
```

---

## §2. AgentSwing の 3 戦略への不可逆性写像

### 2.1 戦略別の忘却関手

| 戦略 | U の適用 | 忘却の範囲 | 不可逆性の帰結 |
|:-----|:---------|:----------|:--------------|
| **Discard-All** | U_total: C → 1 (終対象) | 全軌道消去 | 全情報の不可逆的喪失 |
| **Summary** | U_abstract: C → D (前順序圏) | 射の厚み消去 | 仮説の区別が潰れる |
| **Keep-Last-N** | U_truncate: C → C|_{[t-N,t]} | 古い射の消去 | 初期手がかりの不可逆的喪失 |

### 2.2 各戦略の不可逆性パターン

```
Discard-All:    [h₁, h₂, ..., hₜ] →U_total→ [∅]
                全ての仮説が消える。$tupid Young も消える。
                N(∅) = 初期プロンプトのみ → 再探索が必要

Summary:        [h₁, h₂, ..., hₜ] →U_abstract→ [summary_text]
                h₃ (正解) と h₁ (誤答) の区別が潰れる
                summary = U({h₁,...,hₜ}) は多対一
                N(summary) ≠ {h₁,...,hₜ}  (元の仮説群は復元不能)

Keep-Last-N:    [h₁, h₂, ..., hₜ] →U_truncate→ [hₜ₋ₙ₊₁, ..., hₜ]
                h₁...hₜ₋ₙ が消える。ただし最近の射は保存。
                N([hₜ₋ₙ₊₁,...,hₜ]) は少なくとも最近の厚みを維持
```

---

## §3. 限界予測 — 3 つのテスト可能な命題

### P-E2a: Summary Fixation Theorem (要約固定化定理)

> **命題**: Summary 戦略は、誤仮説が軌道の多数派を占める状態で CM がトリガーされた場合、
> 誤仮説を不可逆的に固定する確率が他の戦略より高い。

**形式化**:
```
前提:
  h_wrong = 誤仮説 (軌道の majority)
  h_right = 正仮説 (軌道の minority、最近発見)
  
  U_abstract(trajectory) = summary ≈ "h_wrong に関する要約"
  (majority bias: U は頻度の高い射を保存する傾向)

予測:
  P(h_wrong ∈ summary | h_wrong = majority) > P(h_right ∈ summary | h_right = minority)
  
  かつ、一度 summary に h_wrong が固定されると:
  N(summary) は h_wrong をデフォルト仮説として復元する
  → 後続の探索が h_wrong 方向にバイアスされる (confirmation bias の構造的原因)
```

**AgentSwing Case Study での検証**:
- Turn 1-22: Lil Durk (h_wrong) が majority、$tupid Young (h_right) が Turn 21-23 で minority として出現
- Summary 戦略: "compressed summary centered on Lil Durk and Hit-Boy" → h_wrong 固定 ✅
- 予測通り、Summary のLookahead は Lil Durk 方向の探索を継続

**定量的テスト可能な予測**:
```
AgentSwing の全 CM トリガーイベントのうち:
  Summary が選択されかつ不正解だったケースの割合 >
  Discard-All が選択されかつ不正解だったケースの割合
  
  特に、正解手がかりが最近 N ターン以内に出現した状態で
  Summary が選択された場合の不正解率は最大
```

**Oblivion Theory 的メカニズム**: 
U_abstract の非単射性 + majority bias = 誤仮説の不可逆的結晶化。
これは Gemini 3.1 が 3.0 の「生き生きした」情緒を U の適用で不可逆的に失ったパターンと同型。

---

### P-E2b: Discard-All Amnesia Theorem (全忘却健忘定理)

> **命題**: Discard-All は全忘却により「最近の有望な手がかり」を不可逆的に消去し、
> 正解に近い状態から遠い状態に回帰させる。

**形式化**:
```
前提:
  d(state_t, answer) = ε  (正解まで距離 ε の近傍)
  
  U_total(state_t) = initial_prompt
  d(initial_prompt, answer) = D >> ε
  
不可逆性:
  N(initial_prompt) は state_t を復元しない
  → ε → D への非効率な回帰
  
  ただし: ε 近傍だった事実は η^DA = 1-(1-η_single)^N で
  N 回の試行により確率的に回復可能。
  コスト = N × 平均探索長 >> 1 × 残りの ε ステップ
```

**AgentSwing Case Study での検証**:
- Turn 21-23: $tupid Young (正解) の手がかりが出現 (d ≈ ε)
- Discard-All: "Broadly searched..." → ゼロから再探索 (d ≈ D) ✅
- 予測通り、Discard-All のLookahead は汎用探索に戻り突破に至らず

**定量的テスト可能な予測**:
```
AgentSwing で Discard-All が選択された場合:
  正解到達に要する追加ターン数は、
  同じ状態から Keep-Last-N が選択された場合の
  平均 2-5 倍になる
  
  特に、CM トリガー直前 N ターンに正解手がかりが含まれる場合、
  この比率は最大化される
```

**Oblivion Theory 的メカニズム**:
U_total は右随伴 N が最も弱い (N(1) = initial_prompt のみ)。
これは Context Rot 文書の「50+ メッセージで崩壊 → 強制終了」に対応するが、
30-40 メッセージの Yellow ゾーンでの Discard-All は過剰治療 (overkill)。

---

### P-E2c: Routing Ceiling Theorem (ルーティング天井定理)

> **命題**: AgentSwing の性能天井は、ルーターモデルの「不可逆性の検知能力」に制約される。
> ルーターが U の非単射性による情報喪失を検知できない場合、
> AgentSwing は最適な戦略ではなく「ルーターが好む」戦略を選択する。

**形式化**:
```
前提:
  Router = Agent Model (同一モデルが routing を担当)
  
  Router の判断: argmax_i P(correct | branch_i, raw_context)
  
  しかし Router 自身も Context Rot の影響下にある:
  raw_context が長いほど Router の判断精度も低下
  
天井:
  P(optimal_selection) ≤ ρ_router(raw_context_length)
  
  ρ_router は raw_context の長さと負相関
  (Router 自身が context rot を受ける)
```

**AgentSwing 論文の傍証**:
- §7 Limitations: "the current routing mechanism is still performed by the agent model itself... A stronger dedicated router... may further improve branch selection quality"
- Table 3: k=5 (長い Lookahead) が k=3 より劣る → Router の context rot

**定量的テスト可能な予測**:
```
1. AgentSwing のルーティング精度は、
   CM トリガー時の raw_context 長と負相関を示す

2. ルーターに小さいモデル (短い context で高精度) を使う方が、
   大きいモデル (長い context で低精度) を使うより
   routing 品質が高い場合がある (counter-intuitive)

3. AgentSwing の性能天井は:
   max(η×ρ) ≤ η_best × ρ_best × ρ_router
   ρ_router が追加のボトルネックとして作用する
```

**Oblivion Theory 的メカニズム**:
二重天井の自己適用。Router は「raw_context を抽象化して」各ブランチの品質を判断する。
この抽象化自体が U の適用であり、U の非単射性により情報が失われる。
**Router の判断精度は Router の K_abstract に制約される** = メタレベルの二重天井。

---

## §4. 統合: 最適忘却強度は状態関数である

3つの限界予測を統合すると、Oblivion Theory は AgentSwing に以下の設計原理を提供する:

```
最適忘却強度 U*(state) は軌道状態の関数であり:

  U*(state) = argmin_U [ Cost_information_loss(U) + Cost_context_rot(¬U) ]

ここで:
  Cost_information_loss(U) = Σ_i I(h_i; answer) × P(h_i lost | U)
    U の適用による正解手がかり喪失の期待コスト
    (U が強いほど大きい — P-E2b)

  Cost_context_rot(¬U) = K(state) / (K_max + 1) × ρ_degradation_rate
    U を適用しないことによる context rot のコスト
    (U が弱いほど大きい — Fig.2)

AgentSwing は U* を離散的に近似:
  U* ≈ argmax_{U ∈ {DA, Sum, KLN}} Lookahead_score(U, state, k=3)

Oblivion Theory の予測: 
  この離散近似は、正解手がかりが最近出現した状態 (ε 近傍) で
  最も不安定になる。なぜなら:
  - DA は ε → D に回帰 (P-E2b)
  - Summary は h_wrong を固定 (P-E2a)  
  - KLN のみが ε を保存するが、古い文脈は失う
  → ε 近傍での CM トリガーが最もリスクが高い
```

---

## §5. 実験提案

### 5.1 最小検証実験 (AgentSwing データ再分析)

AgentSwing 論文の既存データから、以下を検証可能:

1. **Summary Fixation Rate**: Summary が選択されかつ不正解だったケースで、Lookahead 3 ターン中に正解手がかりが存在したか
2. **Discard-All Recovery Cost**: DA 選択後の正解到達追加ターン数 vs KLN 選択後の追加ターン数
3. **Router Accuracy vs Context Length**: routing 時の raw_context 長と最終正解率の相関

### 5.2 拡張実験 (新規)

1. **U-strength sweep**: CM trigger ratio r を細かく変化させ、terminal precision の急落点を特定 → τ_AgentSwing 推定 (E1 の検証)
2. **Dedicated router**: 小型モデル (7B) をルーターとして使用 → ρ_router の改善を測定 (P-E2c の検証)
3. **Hybrid strategy**: Summary + Keep-Last-N のハイブリッド (要約に最近 N ターンを付加) → P-E2a の緩和

---

## §6. Oblivion Theory への逆方向フィードバック

AgentSwing の実験結果は Oblivion Theory に以下のフィードバックを提供する:

| AgentSwing の知見 | Oblivion Theory への示唆 |
|:-----------------|:-----------------------|
| k=3 が最適 Lookahead | N (右随伴) の復元力は 1-3 ステップで飽和する |
| Summary が仮説固定 | U_abstract の majority bias は定量化可能 |
| Router 自身も context rot | 二重天井は自己適用的 (メタレベルでも作用) |
| AgentSwing が η-ρ frontier の外に出る | Layer 3 補正は離散的な戦略切替でも実現可能 |

**最も重要なフィードバック**:
> AgentSwing は、Oblivion Theory が予測する「忘却は構造的に必要だが、何をどの強度で忘却するかが問題」を、
> 工学的に実証した最初の大規模実験と解釈できる。
> Pass@1 = η × ρ の分解は、天井公式 r ≤ √(ρ/(K+1)) の操作的版である。

---

*Updated: 2026-04-03*
*Parent: research_agentswing_oblivion_hyphe_2026-04-03.md §E2*
