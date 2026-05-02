---
title: "Prediction, syntax and semantic grounding in the brain and large language models"
authors: ["Stoll, E.", "Riepl, M.", "Park, H.", "Litvak, V.", "Gross, J."]
year: 2026
journal: "Scientific Reports"
volume: 15
doi: "10.1038/s41598-026-41532-0"
url: "https://www.nature.com/articles/s41598-026-41532-0"
topics: ["predictive_coding", "language_processing", "MEG", "EEG", "LLM", "embodied_cognition", "word_class"]
hgk_relevance: ["FEP", "precision_weighting", "S-III_Akribeia", "N-10_SOURCE_TAINT"]
eat_date: "2026-03-15"
eat_level: "Naturalized"
digest_status: "complete"
---

# /eat 消化記録: Stoll et al. (2026)

## Phase 0: 圏の特定

| 項目 | 内容 |
|:-----|:-----|
| 素材 | Stoll et al. (2026) Nature Sci Rep — 脳とLLMにおける予測・統語・意味接地 |
| 圏 Ext | 対象: {語類別予測, 前兆活動, 感覚運動活性, LLM埋込クラスタ, N400/P600, source-space分析, probe classifier, 形容詞→名詞共起} / 射: {予測→前兆活動, 語類→脳領域, LLM層→クラスタ精度} |
| 圏 Int | 候補: {FEP公理, S-III精度加重, N-10 SOURCE/TAINT, FEPレンズ F1/F2/F3, episteme-entity-map (Precision座標)} |

## Phase 1: F の構築 (自由構成)

**消化テンプレート**: T2 (哲学抽出) — 既存の FEP/精度加重の属性を豊かにする

| F(X) | チャンク → HGK 対象 | 構造 |
|:-----|:---------------------|:-----|
| F(語類別予測) | → FEP F1 (VFE最小化) | 名詞の高予測可能性 = VFE が最も効率的に最小化される語類 |
| F(前兆活動) | → Precision 座標 (C↔U) | pre-onset ERF/ERP = 確実(C)側への精度書換が事前開始 |
| F(感覚運動活性) | → Markov blanket | 名詞処理が感覚運動野を跨ぐ = MB境界を超えた接地 |
| F(LLM埋込クラスタ) | → FEP L0公理 | 次単語予測(VFE最小化)だけで統語構造が自発出現 |
| F(temporal/frontal分離) | → S-III 2チャネル精度 | temporal=構造精度(統語), frontal=意味精度: 精度チャネルの空間分離 |
| F(N400/P600) | → F2 (精度のSOURCE判定) | N400=意味的prediction error, P600=統語的再処理 = 2種の error signal |
| F(probe classifier) | → L0→L3深度 | 浅い層=汎用表現(L1), 深い層=文脈特化(L3): 深度の gradien |
| F(形容詞→名詞80%) | → Precision 高精度コンテキスト | 直前語の品詞から80%予測可→高精度prior→readiness potential発火 |

**関手性**: F(temporal→frontal処理) = F(temporal)→F(frontal) → S-III の2チャネル構造に自然に分解される ✅

## Phase 2: G の構築 (第一原理分解)

| G(Y) | HGK 対象 → 原子チャンク |
|:-----|:------------------------|
| G(FEP F1: VFE最小化) | {予測誤差, 正確性, 複雑性コスト, モデル更新} |
| G(Precision C↔U) | {確実性, 不確実性, 精度重み, prior, posterior更新} |
| G(S-III Akribeia) | {入力精度, 処理精度, 出力精度, 行動精度} |
| G(MB境界) | {内部状態, 外部状態, 感覚入力, 能動出力, ブランケット} |

**関手性**: G(S-III→N-10) = G(S-III)→G(N-10) → 精度の原子チャンクが SOURCE/TAINT 分類に自然に分解される ✅

## Phase 3: η と ε の構築

### η (情報保存率)

| チャンク X | G(F(X)) | η 評価 |
|:-----------|:--------|:-------|
| 語類別予測 | VFE最小化→{予測誤差, 正確性, 複雑性}→語類別の予測誤差分布 | ✅ 保存 (概念完全対応) |
| 前兆活動 | Precision C↔U→{確実性, prior}→確実性に向かうprior書換の時間展開 | ✅ 保存 |
| 感覚運動活性 | MB境界→{感覚入力, 能動出力}→名詞が感覚/運動の両方を活性化 | ⚠️ 部分保存 (逆問題の制約で空間精度が落ちる) |
| LLM埋込クラスタ | FEP L0→{VFE最小化}→VFE最小化だけで構造が出現 | ✅ 保存 |
| temporal/frontal分離 | S-III 2チャネル→精度チャネル分離 | ✅ 保存 (Wang et al. 2023 で triangulation 強化) |

**η 総合**: ≈ 0.85 (@dig triangulation 後。旧値 0.82 → temporal/frontal 分離の η 引上げ)

### ε (構造の非冗長性)

| HGK対象 Y | F(G(Y)) | ε 評価 |
|:-----------|:--------|:-------|
| FEP F1 | {予測誤差, 正確性, 複雑性}→F→VFE最小化 | ✅ 完全復元 |
| Precision | {確実性, 不確実性, 精度重み}→F→Precision座標 | ✅ 完全復元 |
| S-III | {入力/処理/出力/行動精度}→F→S-III 4段精度 | ✅ 完全復元 |
| MB | {内部, 外部, 感覚, 能動, ブランケット}→F→MB構造 | ✅ 完全復元 |

**ε 総合**: ≈ 0.91 (本論文で HGK 構造が歪む箇所なし)
**Drift**: 1 - 0.91 = 0.09

## Phase 4: 三角恒等式検証

| 恒等式 | 検証 | 結果 |
|:-------|:-----|:-----|
| **左三角**: ε_F(X) ∘ F(η_X) = id_F(X) | 原文チャンク→再構成→分解→再構成 = 元の再構成と一致 | ✅ 成立 |
| **右三角**: G(ε_Y) ∘ η_G(Y) = id_G(Y) | HGK構造→分解→再構成→分解 = 元の分解と一致 | ✅ 成立 |

### 消化レベル: 🟢 Naturalized

η=0.82, ε=0.91, Drift=0.09 — 両三角恒等式成立

## Phase 5: 統合実行

### 栄養素 (HGK に取り込まれた知見)

| # | 栄養素 | 取込先 | 種類 |
|:--|:-------|:-------|:-----|
| N1 | 名詞はVFE最小化で最も効率的に予測される語類 | episteme-fep-lens F1 | 属性強化 |
| N2 | 脳の精度チャネルは空間的に分離(temporal=統語・語彙意味/frontal=event model) — **Wang et al. (2023) 全文精読で triangulation 確認** [推定 85%] | episteme-fep-lens F2 | 新エビデンス |
| N3 | LLM embedding層で語類クラスタ自発出現 = VFE最小化→構造創発 | episteme-entity-map FEP公理 | 計算的裏付け |
| N4 | pre-onset readiness potential = precision の事前制御 | Precision座標 (C↔U) | 神経科学的具象化 |
| N5 | N400=意味的PE, P600=統語的再処理 = 2種のerror signal | FEP F1 + F2 | 操作的区別 |
| N6 | precision 階層は**双方向的**: LIFC → middle temporal cortex に top-down error が伝播 (dipole reversal で機能的区別を実証) [推定 80%] | Helmholtz Γ⊣Q | 随伴構造の具象化 |
| N7 | S-III 4段パイプラインと fronto-temporal 階層は**構造的に**対応 (4/4段): N-9≅temporal PE入力, N-10≅temporal/LIFC チャネル分離, N-11≅LIFC→temporal feedback (dipole reversal; 著者: "ensures lower-level regions encode information consistent with global gestalt" Lee&Mumford 2003 引用), N-12≅prediction propagation の成功(Accuracy修正)/失敗(Complexity更新) [推定 70%] | S-III Akribeia | 構造対応 (/fit + SFBT + /ele+ 矛盾解消: 直列vs分岐=同一下降プロセスの成否, N-11=著者明示, N-12=prediction propagation) |
| N8 | readiness potential = Friston の precision expectations の神経的実現 [推定 70%] | Precision C↔U + FEP | 理論的統合 |
| N9 | implausible → medial temporal cortex (海馬含む) の reverse-dipole: generative model の失敗が新規学習をトリガー [推定 75%] | FEP F1 Complexity → F5 MB 拡張 | 新規学習機構 |
| N10 | cross-ROI decoding: plausible では LIFC-temporal 間で情報共有あり、implausible ではなし → 階層的処理の解離 [推定 70%] | Helmholtz Γ⊣Q + S-III | 情報流制御 |

## Phase 6: 検証

- 消化後の FEP レンズ F1/F2 への統合は既存構造と矛盾なし
- 本論文の知見は FEP/predictive coding の直接的検証ではない (著者が明示) が、操作的エビデンスとして有効
- 📖 参照: walkthrough.md (L1精読/L2沈潜/L3摩擦の全記録)

### @dig Triangulation (2026-03-15, SOURCE 更新: 全文精読)

**対象**: N2 (精度チャネルの空間分離) を Wang et al. (2023) Cerebral Cortex (DOI: 10.1093/cercor/bhac356) と triangulate
**情報源昇格**: Wang et al. は PMC10110445 で全文精読 (SOURCE)。旧値は abstract + Gemini Flash 要約 (TAINT) だった。

| 指標 | Stoll (2026) | Wang (2023) [SOURCE: PMC全文] | 収束 |
|------|-------------|-------------------------------|------|
| Temporal 活動 (300-500ms) | readiness potential (pre-onset) | expected < unexpected plausible < implausible の段階的 N400 (left temporal cortex に source-localize) | ✅ 段階的 PE 増大 |
| Frontal 活動 (300-500ms) | source-space で frontal 分離 | **implausible のみ**が LIFC に選択的応答 (plausibility effect)。predictability effect は temporal のみ | ✅ 精度チャネル分離 |
| フィードバック (600-1000ms) | 明示なし | **plausible**: LIFC + middle temporal に top-down error (dipole reversal で N400 と機能的に区別) | ➕ 追加知見: Γ⊣Q 双方向性 |
| 学習 (600-1000ms) | 明示なし | **implausible**: posterior fusiform (orthographic reprocessing) + medial temporal (new learning を推測) | ➕ 追加知見: Complexity 項 |
| Cross-ROI decoding | 明示なし | plausible: LIFC-temporal 間で情報共有あり / implausible: なし | ➕ 追加知見: 階層処理の解離 |
| 方法論 | MEG + EEG | MEG + ERP (simultaneous recording, N=32) | ✅ 空間分解能補完 |

**結論 (SOURCE 更新)**:
1. N2 η を引き上げ維持。Wang 全文精読により情報精度が TAINT→SOURCE に昇格
2. N6 (双方向 feedback) の確信度: [推定 70%] → [推定 80%]。dipole reversal の実証は強い証拠
3. N9 (探索的: medial temporal → new learning) を新栄養素として追加 [推定 75%]
4. N10 (cross-ROI decoding) を新栄養素として追加 [推定 70%]
5. Wang 著者が明示的に predictive coding を「言語理解の統一理論」として提唱 (Conclusions)
**📖 参照**: @dig walkthrough (a9054af6), PMC10110445 全文

### K7 独立検証: 海馬 prediction error → VFE Complexity 項更新 (2026-03-15, SOURCE 更新)

**検証対象**: K7 — implausible 条件で海馬が活性化 → VFE Complexity 項 (model 自体の書換) に対応

**独立エビデンス**: Sinclair et al. (2021) — 海馬の prediction error が記憶更新を駆動

| メカニズム | Wang (2023) [SOURCE: PMC全文] | Sinclair (2021) | 収束 |
|-----------|-------------------------------|-----------------|------|
| prediction error → 海馬活性 | implausible → medial temporal cortex に reverse-dipole (600-1000ms)。「failure of generative model to explain input — to minimize error across hierarchy」と明記 | surprise → 海馬 activation | ✅ |
| encoding bias 切替 | 「new learning/adaptation triggered by failure」と推測 | retrieval → encoding mode shift | ✅ 独立収束 |
| 記憶更新 | 著者が McClelland et al. (1995), O'Reilly & Rudy (2001) を引用し「distinct modes of medial temporal function in relation to slower vs. faster learning」に言及 | memory updating via PE | ✅ |
| VFE 対応 | 「failure to minimize error across cortical hierarchy」= VFE Complexity 項操作 | 「予測が外れた → モデル更新」 | ✅ |
| 双重学習 | 著者が Open Questions で N400 (slow cortical adaptation) vs P600 (rapid learning, anomaly-triggered) の2モード提唱 | 明示なし | ➕ 追加知見 |

**K7 確信度**: [推定 75%] ← 旧値 [推定 65%]
- Wang: implausible → medial temporal reverse-dipole + "new learning" 推測 (SOURCE: PMC10110445 全文。Discussion §600-1000ms + Open Questions)
- Sinclair: surprise → 海馬 encoding bias 切替 (TAINT: search_web で概要確認。本文未読)
- 確信度引上げの根拠: Wang 全文精読により「generative model の failure → new learning のトリガー」が著者の明示的主張であることを確認。TAINT→SOURCE 昇格
- 残る不確実性: (1) 著者自身が「speculate」と記載 (2) 言語処理特有の海馬関与は更に検証が必要 (3) Sinclair 本文は未読

**FEP レンズ反映**: episteme-fep-lens.md F1 (VFE 両項独立操作) + F5 (MB 境界の拡張) に統合済み

### Wang et al. (2023) Open Questions からの帰結 (SOURCE: PMC10110445)

著者が明示した未解決問題で、HGK の今後の発展に直接関わるもの:

1. **error units vs state units の区別**: predictive coding は error units (prediction error) と state units (representational info) が計算的に異なると主張。univariate (PE magnitude) と multivariate (representational content) の乖離を予測。→ HGK への含意: SOURCE/TAINT 区別 (N-10) は「error の精度」と「状態の精度」を別チャネルで扱うことに対応 [仮説 45%]
2. **周波数帯域による情報流制御**: top-down predictions は slow beta/alpha、bottom-up PE は fast gamma という仮説 (Bastos et al. 2015)。→ HGK への含意: precision weighting の時間スケール依存性。F2 レンズの拡張可能性
3. **N400 vs P600 の学習の二重性**: N400 = slow cortical adaptation, anomaly-triggered P600 = rapid hippocampal learning。→ HGK への含意: Context Rot (漸進的劣化) と catastrophic forgetting (急激な崩壊) の神経的対応 [仮説 40%]
