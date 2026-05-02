# pm-skills 随伴PJ VISION

> **随伴対象**: [phuryn/pm-skills](https://github.com/phuryn/pm-skills) (MIT License)
> **作者**: Paweł Huryn (Product Compass Newsletter, 185K+ subscribers)
> **規模**: 8 プラグイン / 65 スキル / 36 コマンド / 6,143行 / 38,339語
> **判定**: 🟡 Leverage+Extend (PM テンプレート品質を HGK WF に移植)
> **作成**: 2026-03-09T15:20 JST
> **消化**: [eat_pm-skills_2026-03-09.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/01_記録｜Records/d_出力_outputs/eat_pm-skills_2026-03-09.md)

---

## 圏論的位置づけ

```
G: HGK-WF → PM-templates    (忘却: 圏論基盤を落とすと操作的テンプレートが残る)
F: PM-templates → HGK-WF    (持ち上げ: テンプレート精度を WF に注入)

η: HGK → G∘F(HGK)           (テンプレート品質の差分 = HGK WF の出力形式の弱さ)
ε: F∘G(PM) → PM             (HGK 化した PM テンプレートは元の PM と何が違うか = 確信度ラベル + N-10 追加)
```

**核心**: HGK は圏論的基盤に強いが「このフォーマットで出力せよ」の操作的精度が弱い。pm-skills は圏論なしだがテンプレート精度が高い。消化 = テンプレート品質の移植。

---

## 行為可能性 47 件 (全量)

### A. 即座に使える PM 実行能力 (10件)

| # | 行為可能性 | 根拠スキル | HGK 形式 |
|:--|:----------|:----------|:---------|
| 1 | PRD を 8 セクション構造で生成 | create-prd (87行) | `/ene.prd` ✅ 実装済 |
| 2 | OKR を構造的に設計 | create-okr (122行) | `/bou.okr` |
| 3 | ユーザーストーリーを 3C+INVEST で分解 | user-stories (74行) + wwas (69行) | `/ene` 修飾 |
| 4 | テストシナリオを体系的に生成 | test-scenarios (86行) | `/pei` 修飾 |
| 5 | 会議議事録を構造化 | summarize-meeting (81行) | `@meeting` マクロ |
| 6 | 顧客インタビューを JTBD で要約 | summarize-interview (53行) | `@interview` マクロ |
| 7 | Pre-mortem で Tigers/PT/Elephants 分類 | pre-mortem (92行) | `/prm.premortem` |
| 8 | Stakeholder Map を Power×Interest で生成 | stakeholder-map (51行) | `/ops` 修飾 |
| 9 | Competitive Battlecard を生成 | competitive-battlecard (77行) | `/ele` 修飾 |
| 10 | Sprint 計画/回顧/リリースノート一式 | sprint (command, 230行) | `@sprint` マクロ |

### B. PM 戦略レベル (10件)

| # | 行為可能性 | 根拠スキル | HGK 形式 |
|:--|:----------|:----------|:---------|
| 11 | Product Strategy Canvas (9 セクション) | product-strategy (112行) | `/bou` 修飾 |
| 12 | Business Model Canvas | business-model-canvas (86行) | `/bou` 修飾 |
| 13 | Lean Canvas (1ページ事業計画) | lean-canvas (57行) | `/bou` 修飾 |
| 14 | Value Proposition を JTBD 6部構造で設計 | value-proposition (134行) | `/bou` 修飾 |
| 15 | Monetization Strategy | monetization-strategy (78行) | `/bou` 修飾 |
| 16 | North Star Metric を定義 | north-star-metric (65行) | `/bou` 修飾 |
| 17 | 市場分析 4フレームワーク一括実行 | /market-scan (116行) | `@market-scan` マクロ |
| 18 | GTM Strategy 設計 | /plan-launch (329行) | `@pm-launch` マクロ |
| 19 | Positioning Statement | positioning (63行) | `/bou` 修飾 |
| 20 | Product Naming | product-naming (56行) | `/bou` 修飾 |

### C. リサーチ・分析レベル (9件)

| # | 行為可能性 | 根拠スキル | HGK 形式 |
|:--|:----------|:----------|:---------|
| 21 | User Persona を JTBD ベースで生成 | user-personas (107行) | `/noe` 修飾 |
| 22 | User Segmentation を行動ベースで実行 | user-segmentation (130行) | `/noe` 修飾 |
| 23 | Sentiment Analysis | sentiment-analysis (122行) | `/dia` 修飾 |
| 24 | Customer Journey Map | customer-journey (83行) | `/noe` 修飾 |
| 25 | Competitive Analysis (4層構造) | competitive-analysis (120行) | `/ele` 修飾 |
| 26 | TAM/SAM/SOM 計算 | tam-sam-som (43行) | `/dia` 修飾 |
| 27 | SQL クエリ生成 | sql-query (94行) | `/tek` 修飾 |
| 28 | Cohort Analysis | cohort-analysis (62行) | `/dia` 修飾 |
| 29 | A/B Test 設計 | ab-testing (72行) | `/pei` 修飾 |

### D. Discovery サイクル (8件)

| # | 行為可能性 | 根拠スキル | HGK 形式 |
|:--|:----------|:----------|:---------|
| 30 | OST 全ステップ構築 | opportunity-solution-tree (65行) | `/ccl-dig` 統合 |
| 31 | 新プロダクトアイデアブレスト | brainstorm-ideas-new (47行) | `/ske` 修飾 |
| 32 | 既存プロダクトアイデアブレスト | brainstorm-ideas-existing (60行) | `/ske` 修飾 |
| 33 | 仮説の構造的識別 | identify-assumptions (44行) | `/hyp` 修飾 |
| 34 | 仮説の優先順位付け | prioritize-assumptions (63行) | `/dia` 修飾 |
| 35 | 実験の設計 | brainstorm-experiments (62行) | `/pei.pretotype` |
| 36 | Feature の優先順位付け | prioritize-features (65行) | `/dia` 修飾 |
| 37 | Discovery サイクル一括実行 | /discover (132行) | `@pm-discover` マクロ |

### E. ツールキット (6件)

| # | 行為可能性 | 根拠スキル | HGK 形式 |
|:--|:----------|:----------|:---------|
| 38 | PM レジュメレビュー (XYZ+S 公式) | review-resume (393行) | ツール |
| 39 | レジュメ最適化 | tailor-resume | ツール |
| 40 | Grammar/Logic/Flow チェック | proofread (393行) | ツール |
| 41 | NDA/Privacy Policy 生成 | draft-nda / privacy-policy | ツール |
| 42 | Marketing Ideas ブレスト | marketing-ideas | `/ske` 修飾 |
| 43 | Growth Loop 設計 | growth-loops | `/bou` 修飾 |

---

## T3 (機能消化) 候補 — 優先順位

| 優先 | 候補 | HGK 形式 | 状態 |
|:-----|:-----|:---------|:-----|
| ★★★ | PRD 8セクションテンプレート | `/ene.prd` → `ccl-prd.md` | ✅ 実装済 |
| ★★★ | Pre-mortem (Tigers/PT/Elephants) | `/prm.premortem` | 未実装 |
| ★★★ | OKR 設計フレームワーク | `/bou.okr` | 未実装 |
| ★★ | Discovery サイクルチェーン | `@pm-discover` マクロ | 未実装 |
| ★★ | Opportunity Score 公式 | `/dia[Fn:E]` 修飾 | 未実装 |
| ★★ | Value Proposition 6部構造 | `/bou` 修飾 | 未実装 |
| ★★ | Pretotype 実験手法 | `/pei.pretotype` | 未実装 |
| ★ | Sprint Velocity 推定 | `/dok` 修飾 | 未実装 |
| ★ | XYZ+S 成果報告公式 | N-11 強化 | 未実装 |
| ★ | JTBD Interview Summary | `@interview` マクロ | 未実装 |
| ★ | Stakeholder Power×Interest | `/ops` 修飾 | 未実装 |
| ★ | GTM Strategy Chain | `@pm-launch` マクロ | 未実装 |
| ★ | Competitive Battlecard | `/ele` 修飾 | 未実装 |
| ★ | User Story 3C+INVEST | `/ene` 修飾 | 未実装 |
| ★ | NSM Selection Framework | `/bou` 修飾 | 未実装 |
| ★ | Monetization Model Selection | `/bou` 修飾 | 未実装 |
| ★ | marketplace.json 配布形式 | Agora 仕様 | 未実装 |

---

## 情報量 (エネルギー) の定量

- **書籍 6 冊分 / 1,938 ページの操作的圧縮** → 47 個の新行為として抽出
- **最も密度の高いプラグイン**: pm-product-discovery (13 skills), pm-execution (15 skills)
- **HGK 増幅**: 確信度ラベル (N-2/3) + SOURCE/TAINT (N-10) + CCL パイプライン化で PM 単体の行為を超える
