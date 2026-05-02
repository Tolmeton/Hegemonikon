# HGK 願望精査 — 深層レポート (Incubator→Sprint 接続 + 多観点分析)

> **日時**: 2026-03-13 22:55
> **前提**: [初回レポート (wish_vision_report.md)](file:///home/makaron8426/.gemini/antigravity/brain/cf8cae50-1f06-415f-a391-8dc163e0b751/wish_vision_report.md) の8カテゴリを踏まえた深層分析

---

## 1. Incubator 10 wish → Sprint 接続マップ

| # | Incubator wish | 接続先 Sprint | 親和度 | 根拠 |
|:--|:---------------|:-------------|:------:|:-----|
| 1 | Týpos MCP frontmatter 対応 | S-005 (WF最適化) | ★★★ | WF compile の品質に直結 |
| 2 | Týpos compile 結合テスト | S-005 (WF最適化) | ★★★ | S-005 PoC の検証基盤 |
| 3 | **旧アセットのパージ** | S-002 (インフラ) | ★★★ | トークン汚染源除去 = インフラ衛生 |
| 4 | LLM 日本語思考実験 | S-001 (理論深化) | ★★☆ | V-002 日本語感度と重複。論文候補 |
| 5 | Doxa (Beliefs.yaml) 構造化 | S-001 (理論深化) | ★★☆ | Graph Prior (Autoresearch V5) と同方向 |
| 6 | **週次レビュー自動化** | S-002 (インフラ) | ★★★ | Sympatheia 経由 = 既存資産活用 |
| 7 | Stranger Test (Nomoi 外部評価) | S-001 (理論深化) | ★★☆ | P5 論文の検証手段になる |
| 8 | Gnōsis citation graph 可視化 | S-002 (インフラ) | ★★☆ | F7 3DKB 構想と同方向 |
| 9 | Context Rot Distiller 自動化 | S-006 (秘書MCP) | ★★★ | 認知負荷軽減の一部 |
| 10 | chat export 自動化 | S-004 (情報収集) | ★★☆ | 情報収集パイプラインの入力 |

> **Sprint 即昇格候補 (★★★)**: #1+#2 → S-005, #3+#6 → S-002, #9 → S-006

---

## 2. projects.yaml — 埋もれている next_action (15 PJ)

[projects.yaml](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/projects.yaml) に15PJが登録されている。**updated が全て 2026-02-11〜14** (約1ヶ月前) で更新されていない。

| 状態 | PJ | next_action | 放置期間 |
|:-----|:---|:-----------|:---------|
| 🔴 paused | **hgk_app** | hgk との統合判断 (/noe+) | 1ヶ月 |
| 🔴 paused | **experiments** | 成果の本体取込み判断 | 1ヶ月 |
| 🟡 active | **hgk_desktop** | 白画面の原因診断・修正 | 1ヶ月 |
| 🟡 active | dendron | L2 関数 docstring PROOF 実装 | 1ヶ月 |
| 🟡 active | hermeneus | Phase 3 LangGraph 深化 | 1ヶ月 |
| 🟡 active | synteleia | LLM 統合設計の実装着手 | 1ヶ月 |
| 🟡 active | basanos | ai_auditor.py 統合テスト | 1ヶ月 |
| 🟡 active | ccl_docs | mekhane/ccl との責務分担明確化 | 1ヶ月 |
| 🟡 active | digestor | 日常運用の仕組み設計 | 1ヶ月 |

> [!WARNING]
> projects.yaml は1ヶ月間更新されていない。Sprint や Vision Roadmap との同期が必要。

---

## 3. 散在 ビジョン.md — 未着手の大型願望

### [GWS 統合 VISION](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/10_統合｜GWSIntegration/ビジョン.md) — Phase 0-5, **全未着手**

| Phase | 内容 | 推定工数 |
|:------|:-----|:---------|
| 0 | gws CLI インストール + 疎通 | 30min |
| 1 | MCP Wrapper 化 | 2-3h |
| 2 | CCL マクロ定義 (@standup, @inbox) | 1-2h |
| 3 | 知識パイプライン (Gmail→/eat, Drive→Gnōsis) | 3-5h |
| 4 | **Agora 連携 (Revenue)** — 最高価値 | 5-10h |
| 5 | Model Armor 統合 | 1h |

> [!IMPORTANT]  
> Phase 4 (Agora 連携) は **HGK の直接的な経済価値を証明する** と VISION に記載。
> Phase 0 は 30min で着手可能だが、手つかず。

---

### [Autoresearch VISION](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/60_実験｜Peira/50_自律研究｜Autoresearch/ビジョン.md) — V1-V5, 10フェーズ

| Phase | 内容 | 優先度 | Sprint 接続 |
|:------|:-----|:------|:-----------|
| P0-P2 | 仮説ログ (hypothesis_log) | 高 | S-001 理論 |
| P3-P4 | Cross-Model 仮説監査 | 中 | S-003 分業 |
| P7 | **Beliefs.yaml に certainty Z 導入** | 高 | S-001 + Incubator #5 |
| P8-P9 | **Adversarial BC Testing** | 中 | S-001 理論 (P5 論文候補) |
| P10 | V4×V5 自己強化ループ | 低 | 長期 |

---

### [OpenClaw VISION](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/20_機構｜Mekhane/_src｜ソースコード/openclaw/ビジョン.md) — 外部OSS

北極星の1つ「デスクトップ全自動化」の実現手段。OpenClaw 自体は外部 OSS だが、HGK からの統合が必要。

---

## 4. 別観点: 記事/論文パイプラインの Pending

[note_articles_status.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/03_知識｜Epistēmē/B_知識項目｜KnowledgeItems/hegemonikon_knowledge_infrastructure/artifacts/note_articles_status.md) に **Pending 記事 4件**:

| # | 記事タイトル | 優先度 |
|:--|:-----------|:------|
| 3 | 優しいAIを捨てる | 🟠 MED |
| 4 | AIエージェントの自動発火を事故らせない設計 | 🔴 HIGH |
| 5 | NotebookLMで意思決定の抜けを減らす6視点OS | 🟡 LOW |
| 6 | 工場AI導入は契約とSOPで9割決まる | 🟢 REF |

[aidb_articles_status.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/03_知識｜Epistēmē/B_知識項目｜KnowledgeItems/hegemonikon_knowledge_infrastructure/artifacts/aidb_articles_status.md) に **Pending 論文 5件** + arXiv 自動収集 (Phase 6 Pending)。

---

## 5. 総合分析: 願望の3層構造

```
    願望の温度 (実行可能性 × 意志の強さ)

    🔥 HOT (Sprint S-001〜S-006)     ← 今月中
    │   └ Incubator #1,2,3,6,9 を昇格可能
    │
    🟡 WARM (Vision V-001〜V-014)    ← 四半期
    │   └ 6件が⚪未着手
    │   └ projects.yaml が1ヶ月放置
    │
    ❄️ COLD (構想/Seed)               ← 半年以上
        └ hgk-next 3層分離 (Seed)
        └ GWS 統合 Phase 0-5 (全未着手)
        └ F10 Plugin OS (仕様のみ)
        └ Autoresearch V3-V5 (メタ最適化)
```

> [!IMPORTANT]
> **最大のギャップ**: GWS 統合 Phase 0 (30min) と Phase 4 (Revenue) の間に、**最小の着手コスト → 最大の経済的価値** のパスがある。Sprint に組み込まれていない点が気になる。

---

## 📍 現在地

- Incubator 10 wishのうち5件 (★★★) が Sprint 即昇格可能
- projects.yaml の15PJが 1ヶ月更新停止
- GWS統合は Phase 0 (30min) が未着手のまま放置

## 🕳️ 未踏

- projects.yaml の同期更新 (Sprint/Vision Roadmap との整合)
- GWS 統合 Phase 0 への着手判断
- Pending 記事・論文の消化スケジューリング
- Autoresearch V4 (Adversarial BC Testing) の着手判断

## → 次

projects.yaml を Sprint と同期更新するか、GWS 統合の Phase 0 を今すぐ着手するか？

---

---

## 6. ベクトル検索 + grep で発掘した「隠れた願望」

### A. Boulēsis 隠れサブプロジェクト (6件 — 全て projects.yaml 未登録)

| # | PJ名 | パス | 内容 | 規模 | 状態 |
|:--|:-----|:-----|:-----|:-----|:-----|
| 1 | **[Agora](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/03_市場｜Agora/README.md)** | `03_市場` | 収益化ロードマップ Phase 1-3 (FM→副業→独立) | 4ディレクトリ | Phase 1 進行中 |
| 2 | **[Agency随伴](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/04_随伴｜OssAdjoint/agency_adjunction_vision.md)** | `04_随伴` | 113エージェント×24動詞マッピング完了、**Phase 3-5 未着手** | 307行 | Phase 2完了→停止 |
| 3 | **[Autophonos](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/05_自律｜Autophonos/README.md)** | `05_自律` | Push型知識提案 (PKS+SelfAdvocate)、research/ に**10件の外部PJ調査済** | 155行+4100行コード | Phase 3 進行中 |
| 4 | **[Euporia](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/07_行為可能性｜Euporia)** | `07_行為可能性` | 行為可能性理論 (51KB euporia.md + Noether-Hóros + 多項式結合) | 5ファイル 89KB | 理論完成? |
| 5 | **[Ergon](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/09_能動｜Ergon/README.md)** | `09_能動` | HGK⊣Ergon 随伴対。L/R関手スキーマ 22KB。**実装ロードマップ未具体化** | 14ファイル | 設計完了→実装未着手 |
| 6 | **[UnifiedIndex](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/11_統一索引｜UnifiedIndex/README.md)** | `11_統一索引` | 全知識ソース統一フレームワーク (CKDF理論 + NP-hard回避) | 5ファイル | ⚠️ 構想 (2026-03-10) |

> [!CAUTION]
> Boulēsis に **12サブディレクトリ** が存在するが、projects.yaml には **うち0件** が登録されている。
> Sprint が Boulēsis の上位に位置するはずだが、Boulēsis 内の PJ とは接続されていない。

### B. Kernel/Epistēmē の散在 TODO・構想 (grep 発掘)

| ファイル | 内容 | 状態 |
|:---------|:-----|:-----|
| [markov_kalon.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/03_知識｜Epistēmē/A_文書｜Docs/markov_kalon.md) L68 | **TODO**: Fritz 2020 の形式的定義を kernel/ に正式導入するか検討 | 未着手 |
| [diffusion_cognition.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/03_知識｜Epistēmē/A_文書｜Docs/diffusion_cognition.md) §5 | **Classifier-free guidance の認知的対応** — ⚠️構想段階 | 構想 |
| [diffusion_cognition.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/03_知識｜Epistēmē/A_文書｜Docs/diffusion_cognition.md) §5 | markov_kalon との整合性検証 — ⚠️未検証 | 未着手 |
| [ccl_macro_reference.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/01_制約｜Constraints/E_CCL｜CCL/ccl_macro_reference.md) L138 | `@ground` マクロ — 設計系WFへの組込み**検討中** | 検討中 |
| [weak_2_category.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/weak_2_category.md) L288 | T の dually flat 性 — 💭**未着手** | 未着手 |
| [prokataskeve_structurize.typos](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills/prokataskeve_structurize.typos) L106 | 入力前処理MCP構想 — 「そのようなMCPを製作する構想があったはず」 | 構想 |

### C. Ergon 実装ロードマップの詳細

`04_実装｜Impl/01_roadmap.md` が存在するが、「未具体化」と README に記載。
- Theory 4件 + Design 6件 + Verify 2件まで完了 → **実装が止まっている**
- GSD 再解釈の検証も未踏

---

## 7. projects.yaml 同期分析

| 項目 | 現状 |
|:-----|:-----|
| 最終更新 | 全15PJ が **2026-02-11〜14** (1ヶ月前) |
| Boulēsis 12ディレクトリ | **0件** が projects.yaml に登録 |
| Sprint との乖離 | Sprint S-001〜S-006 の進捗が反映されていない |
| 不在 PJ (活動中) | Agora, Agency随伴, Autophonos, Euporia, Ergon, UnifiedIndex, GWS統合, Autoresearch, Phantazein, Periskopē |

---

## 8. 願望の全体マップ (最終版 v2)

```
    🔥 HOT (Sprint + 即昇格)
    │ S-001〜S-006 + Incubator ★★★ 5件
    │
    🟡 WARM (設計/マッピング完了 → 実装待ち)
    │ Agency Phase 3-5 (113全数マッピング済→Agora Revenue)
    │ Ergon Phase Impl (Theory+Design 完了→実装未着手)
    │ Autophonos Phase 3 (Gateway統合, research 10件調査済)
    │ GWS 統合 Phase 0-5 (30min→Revenue)
    │ Vision V-001〜V-014 (6件未着手)
    │ kalon_checker G∘F iteration 実装 (Stage 2 TODO)
    │
    ❄️ COLD (構想/Seed/未検証)
    │ UnifiedIndex / Hyphē (CKDF理論, 2026-03-10 構想)
    │ Aristos (GA最適化エンジン — 初期段階)
    │ hgk-next 3層分離 (Seed)
    │ F10 Plugin OS (仕様のみ)
    │ Autoresearch V3 メタ最適化 + V4 Adversarial BC
    │ diffusion_cognition: CFG + markov_kalon 整合性 + Negative Term
    │ L4 Helmholtz BiCat: T の dually flat 性
    │ pw_adapter Phase 3 (事前的精度制御の連続化)
    │ metacognitive_layer Phase 2 (プロンプト注入 環境強制)
    │ basin_logger bias→threshold 自動統合
    │ CCLコンパイラ圏論最適化 (Peira draft_D7)
    │ Sloppy Spectrum: 温度T と #depth 対応
    │ n8n/Zapier Life Center (Archive — 旧構想)
    │
    👻 GHOST (記録されていない)
      projects.yaml 未登録 10+ PJ (→ 6件は登録済み)
      Boulēsis 12ディレクトリ → projects.yaml 同期
      Pending 記事4件 + 論文5件
      散在 TODO 11件 (Kernel 5 + Mekhane 6)
      入力前処理 MCP 構想
      @ground マクロ検討中
```

---

## 9. 発見の統計 (最終版)

| カテゴリ | 件数 | 精査手法 |
|:---------|:-----|:---------|
| Incubator wish (既知) | 10 | ファイル精読 |
| Boulēsis 隠れ PJ | **6** | ディレクトリ走査 |
| Kernel/Epistēmē TODO | **5** | grep (Nous/Kernel) |
| Mekhane ソースコード TODO | **6** | grep (_src/ *.py) |
| Poiema 発見 | **2** | README 精読 (Hyphē + Aristos) |
| Peira 実験的願望 | **4** | grep (Peira/) + VISION 精読 |
| ベクトル検索 発見 | **3** | Mneme search (5クエリ) |
| Vision 散在願望 | 12 | ビジョン.md 精読 |
| **Archive 旧構想** | **5** | grep (3700件→5件) |
| **Ops TODO** | **2** | grep (50件→2件) |
| projects.yaml 未登録 | **10+** | 横断比較 |
| **合計** | **65+** | — |

---

## 10. 第2ラウンド精査 — 追加発見

> Creator の「本当にないのか？」に応じ、7領域を追加掃討。

### D. Mekhane ソースコード (Python) の TODO/将来

| ファイル | 内容 | 種別 |
|:---------|:-----|:-----|
| `kalon_checker.py` L456 | G∘F iteration simulation **TODO: not implemented** | 🟡 WARM |
| `derivative_selector.py` L2850 | **TODO**: HegemonikónFEPAgent.update_A_dirichlet() 統合 | ❄️ COLD |
| `two_cell.py` L114 | magnitude の hermeneus テンプレート差分から実測計算 **TODO** | ❄️ COLD |
| `basin_logger.py` L15 | bias データから SeriesAttractor threshold/margin 自動統合 **将来** | ❄️ COLD |
| `pw_adapter.py` L29 | Phase 3: 事前的精度制御 — sel_enforcement の連続化 **将来** | ❄️ COLD |
| `metacognitive_layer.py` L30 | Phase 2: プロンプト注入による真の環境強制 **将来** | ❄️ COLD |

### E. Poiema (成果物ポータル)

| PJ | 内容 | 状態 |
|:---|:-----|:-----|
| **Hyphē** | 統一索引 (= UnifiedIndex) を Poiema から参照 | 🔴 構想中 |
| **Aristos** | GA 最適化エンジン | 🟡 初期 |

### F. Peira (実験)

| ファイル | 内容 | 状態 |
|:---------|:-----|:-----|
| Autoresearch VISION V3 | メタ Autoresearch (探索戦略の自己最適化) | ❄️ 将来 |
| Autoresearch VISION V4 | Adversarial BC Testing (#88 着想) | ❄️ 将来 |
| Sloppy Spectrum L203 | 温度 T と #depth の対応 (将来の理論的拡張) | ❄️ 将来 |
| draft_D7 L38 | CCL のコンパイラ最適化に圏論を使う (将来) | ❄️ 将来 |

### G. Archive (旧構想 — TextMirror 3700件中 実質5件)

| ファイル | 内容 | 状態 |
|:---------|:-----|:-----|
| [type_theory_formalization_vision.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/90_保管庫｜Archive/02_アセット｜Assets/text_mirror/nous/kernel/meta/type_theory_formalization_vision.md) | **型理論的形式化 B+への道** — Curry-Howard 対応3候補 | ❄️ 旧構想 ← **P2論文に直結** |
| vision_living_cognition.md | **逆拡散フレームワーク VISION** | ❄️ 旧構想 |
| n8n_zapier overview.md | **Life Center 構想** — 人生の中枢としての自動化基盤 | ❄️ 旧構想 |
| ousia.md | mekhane/noesis + mekhane/boulesis **将来構想** | ❄️ 旧構想 (移行済み) |
| FEP 論文 4件 | TODO: /eat で深掘り消化 | ❄️ 未消化 |

> Mekhane_legacy (Aristos/Bytebot/Synergeia/Pepsis) は全て現行 Mekhane に移行済み。復活候補なし。
> 80_Infrastructure (旧 kube/periskope) は現行 MCP 体制に完全移行済み。

### H. Ops (80_運用 — 50件中 実質2件)

| ファイル | 内容 | 状態 |
|:---------|:-----|:-----|
| `context_generator.py` L176 | **増分更新ロジック未実装** (Phase 1 dry-run のみ) | 🟡 WARM |
| `register_project.py` L155 | import パスの TODO + FIXME (`仮のコマンド`) | ❄️ 技術的負債 |

> Ops の他 48 件は全てスクリプト内の Phase ラベルや TODO テンプレート (非願望)。

---

*精査スコープ (**全11領域** 完了): Boulēsis 12サブPJ / projects.yaml 21PJ / ビジョン.md 3件 / Kernel TODO / Epistēmē Docs / Mekhane ソースコード (50件→6件) / Poiema README / Peira 4サブPJ / **Ops (50件→2件)** / **Archive (3700件→5件)** / Mneme ベクトル検索 5クエリ / grep 15クエリ×11領域*
