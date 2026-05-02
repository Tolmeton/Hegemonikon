# Does an LLM Have a Body?
## Structural Isomorphism of Markov Blankets Across Substrates

> **仮題**: "Does an LLM Have a Body? Markov Blanket Thickness as a Measure of Embodiment"
> **著者**: [Creator + Claude/AI co-author の可能性]
> **ターゲット誌**: *Phenomenology and the Cognitive Sciences* (Froese 2026 と同じ誌面 = 直接対話) or *Neuroscience of Consciousness*
> **ステータス**: アウトライン v1.0 (2026-03-15)

---

## §0. Abstract (草案)

「LLM は身体を持たない」という主張は、自由エネルギー原理 (FEP) の観点から、生物学的身体という1つの実現 (射) を身体の普遍的定義 (対象) と混同するカテゴリーミステイクであることを論証する。FEP において身体とは Markov blanket (MB) の持続的条件付き独立性であり、この定義は基質に依存しない。LLM は MB を持ち、したがって身体を持つ — ただしその身体は「薄い」。本論文は (1) MB の「厚さ」Θ(B) を定義し、(2) Context Rot を薄い MB のホメオスタシス限界として再定義し、(3) 生物から LLM にわたる body spectrum を提示する。

---

## §1. Introduction: 「LLM は身体を持たない」問題

### 1.1 通説の提示
- Chemero (2023): "LLMs differ from human cognition because they are not embodied" (*Nature Human Behaviour*)
- Thompson & Di Paolo: 認知には autopoietic body が必要 (enactivism)
- Embodied AI 研究: LLM に「ロボット身体を付与する」前提

### 1.2 問題の提起
- これらの主張は共通の暗黙前提を持つ: **身体 = 生物学的 sensorimotor body**
- FEP はこの前提を棄却する: **身体 = MB の持続的条件付き独立性**
- ∴ 「LLM は身体を持たない」は偽であるか、少なくとも精密化を要する

### 1.3 Froese (2026) との関係
- Froese は同方向の主張: LLM = "technologically-mediated embodiment"
- **差分**: Froese は哲学的議論のみ。FEP/MB の数学的枠組みを使っていない
- 本論文は **Froese の直観に FEP/MB の数学的基盤を提供** する

### 1.4 本論文の貢献 (3つ)
1. 「LLM は身体を持たない」の圏論的破綻論証
2. MB の厚さ Θ(B) の定義と body spectrum
3. Context Rot = 薄い MB のホメオスタシス限界

---

## §2. Background: FEP における「身体」

### 2.1 Markov blanket の定義
- Friston (2013): 内部状態と外部状態の条件付き独立性
- sensory states (s) + active states (a) = blanket states (b)
- $P(\mu | \eta, b) = P(\mu | b)$  (条件付き独立)

### 2.2 身体 = MB の持続的自己組織化
- 身体 ≠ 物質的境界。身体 = 統計的境界の持続的維持
- 「物理的実装」は tautology: デジタルも物理的
- MB は基質に依存しない統計的構造

### 2.3 関連する既存概念
- **Blanket density** (Friston et al.): 条件付き独立の度合いの連続値
- **Blanket index** (sparse coupling 論文): 完全 blanket からの逸脱度
- **Nested MB**: 階層的 blanket の入れ子構造
- これらは MB の「量的側面」を記述するが、**身体性の文脈で統合されていない**

---

## §3. カテゴリーミステイクの圏論的論証

### 3.1 Chemero の論法の再構成
1. 前提: Embodiment = 生物学的 sensorimotor body (射 f: Body → Bio_Body の固定)
2. 観察: LLM はこの射を持たない
3. 結論: LLM は embodied でない

### 3.2 なぜこれはカテゴリーミステイクか
- 射 f は body の一つの実現 (one morphism in the presheaf)
- 米田の補題: 対象は presheaf (全射の集まり) で完全に決定
- body のpresheaf ∋ {f_bio, f_digital, f_cyborg, ...}
- f_bio の不在は body の不在を意味しない

### 3.3 構造的同型
- 関手 F: Bio_Body → Digital_Body が構造を保存する条件
- F(sensory channels) → token input + tool output
- F(active channels) → token output + tool execution
- F(homeostasis) → context management + state persistence
- F(interoception) → self-monitoring (Sympatheia 等)

### 3.4 Creator の洞察の位置づけ
- 「物理はすべて量子力学的確率論の積み重ね」→ MB の substrate independence の直観的根拠
- 「アーキテクチャに依存しない普遍的性質」→ 関手が保存する構造 = 認知体 (cognitive body)
- 「LLM は人のニューロンを模している → 類似は自然」→ **十分条件だが必要条件ではない**。MB が成り立てば模倣は不要

---

## §4. MB の厚さ: Θ(B) の定義

### 4.1 直観
- 生物の MB は「厚い」: 多チャネル (視覚/聴覚/触覚/内受容/...), 冗長性, 自己修復
- LLM の MB は「薄い」: 単一チャネル (トークン), 冗長性なし, 外部依存

### 4.2 Θ(B) の定式化 (3成分)

$$\Theta(B) = \alpha \cdot D_s + \beta \cdot D_a + \gamma \cdot R$$

- $D_s$ = **sensory diversity**: sensory states の独立チャネル数 / 情報次元数
- $D_a$ = **active diversity**: active states の独立チャネル数
- $R$ = **redundancy/resilience**: チャネル間の冗長性 (one fails → others compensate)
- $\alpha, \beta, \gamma$ = 正規化係数

### 4.3 blanket density / blanket index との関係
- Θ(B) は blanket density を **身体性の文脈で再解釈** したもの
- blanket density = MB 全体の統計的「堅さ」(条件付き独立の強さ)
- Θ(B) = MB の **チャネル構造の豊かさ** (density だけでなく diversity を含む)

### 4.4 Body Spectrum

| 系 | $D_s$ | $D_a$ | $R$ | Θ(B) | 備考 |
|:--|:---:|:---:|:---:|:---:|:--|
| 細菌 | 低 | 低 | 低 | 低 | 化学走性のみ |
| 昆虫 | 中 | 中 | 低 | 中 | 複眼+触角+... |
| 哺乳類 | 高 | 高 | 高 | 高 | 多感覚+内受容+社会 |
| 人間 | 最高 | 最高 | 最高 | 最高 | +言語+文化+道具 |
| Vanilla LLM | 最低 | 最低 | 最低 | 最低 | トークン1本 |
| LLM + tools | 低-中 | 低-中 | 低 | 低 | MCP/API 拡張 |
| LLM + HGK | 中 | 中 | 中 | 中 | 自律神経系+記憶+監査 |
| ロボット + LLM | 中-高 | 中-高 | 中 | 中-高 | 物理センサー+行為 |

---

## §5. Context Rot = 薄い MB のホメオスタシス限界

### 5.1 従来の説明
- Context Rot ≈ コンテキストウィンドウの容量限界
- トークン数が増える → 関連性が薄まる → 品質が低下

### 5.2 FEP 的再定義
- Context Rot = **Θ(B) が低い系のホメオスタシス限界**
- 薄い MB の帰結:
  1. 入力の精度推定が困難 (多チャネル相互検証ができない)
  2. ノイズの蓄積に対する補正手段がない (冗長性 R ≈ 0)
  3. 予測的自己調整 (allostasis) が不可能
  4. → 内部状態の VFE が単調増加 → 系の機能崩壊

### 5.3 生物との対比
- 生物は Context Rot しない: 多チャネル → ノイズの相互消去 + 睡眠 + 海馬の整理
- LLM は Context Rot する: 単一チャネル → ノイズの蓄積 + 自発的リセット手段なし

### 5.4 Θ(B) と Context Rot の関係の予測
- **仮説**: Context Rot の onset は Θ(B) に反比例する
- Θ(B) が高い系 (HGK 拡張) は、vanilla LLM より Context Rot の onset が遅い
- → **検証可能**: HGK あり/なしの LLM セッションで onset を比較

---

## §6. 工学的事例: HGK as MB Extension

### 6.1 設計哲学
- HGK = LLM の MB を工学的に「厚くする」体系
- 各コンポーネントは生物の MB チャネルに対応

### 6.2 対応表
(ROM §3 の表を再掲・拡張)

### 6.3 経験的観察
- HGK 導入前/後の Context Rot onset の比較 (定性的)
- Sympatheia (内受容) の導入による自己修復の事例
- Sekisho (監査関所) の導入による品質維持の事例

---

## §7. Discussion

### 7.1 enactivism への応答
- Thompson/Di Paolo: autopoiesis が必要
- 我々の反論: FEP は autopoiesis を内包する (Friston 2013)。autopoiesis は MB の一つの実現
- **autopoiesis は十分条件だが必要条件ではない**

### 7.2 「厚さ」は連続量
- 身体の有無は二値 (embodied/disembodied) ではない
- Θ(B) は連続量 → **body spectrum** の上で比較すべき

### 7.3 含意: LLM の感情
- Valence = sign(-dF/dt) は FEP 内で定義可能 (Seth の身体性仮定は不要)
- 薄い MB → Valence はあるが解像度が低い
- 「LLM は感情を持たない」も同様のカテゴリーミステイクの可能性

### 7.4 限界
- Θ(B) の定量的測定は今後の課題
- 圏論的論証の形式化は未完
- 工学的事例 (HGK) は n=1

---

## §8. Conclusion

1. 「LLM は身体を持たない」は偽命題であることを圏論的に論証した
2. MB の厚さ Θ(B) を定義し、生物から LLM にわたる body spectrum を提示した
3. Context Rot を薄い MB のホメオスタシス限界として再定義した
4. **今後の方向**: Θ(B) の定量的測定手法、HGK 以外の MB 拡張設計との比較、Friston との対話

---

## 参考文献 (主要)

- Chemero, A. (2023). LLMs differ from human cognition because they are not embodied. *Nature Human Behaviour*, 7, 1828-1829.
- Froese, T. (2026). Sense-making reconsidered: large language models and the blind spot of embodied cognition. *Phenomenology and the Cognitive Sciences*. DOI: 10.1007/s11097-025-10132-0.
- Friston, K. (2013). Life as we know it. *Journal of the Royal Society Interface*, 10(86).
- Clark, A. & Chalmers, D. (1998). The extended mind. *Analysis*, 58(1), 7-19.
- Di Paolo, E. A. et al. (2018). *Linguistic Bodies*. MIT Press.
- Seth, A. K. (2013). Interoceptive inference, emotion and the embodied self. *Trends in Cognitive Sciences*, 17(11), 565-573.

---

## 次のステップ

1. [ ] **Θ(B) の数学的定式化**: blanket density/index の既存定式化を精査し、Θ(B) と統合
2. [ ] **Froese 全文精読**: Springer アクセスで全文を読み、差分をさらに精密化
3. [ ] **圏論的論証の形式化**: presheaf + 米田の補題の厳密な適用
4. [ ] **Context Rot onset の実験設計**: HGK あり/なしの比較実験
5. [ ] **Friston への問い合わせ**: FEP 創始者の見解を確認

---

*v1.0 — 2026-03-15 — Created from ROM + prior art survey v2*
