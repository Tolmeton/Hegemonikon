# Handoff: Skills インポート & Agency随伴設計

**日時**: 2026-03-28
**セッション種別**: Skills 管理 + Agency随伴設計
**V[session]**: 0.2 (低不確実性)

---

## S: Situation

~/.claude/skills/ (57件) と Nous の C_技能/B_スキル (80+件) に差分があり、未インポートのスキルが多数存在。
併せて、Agency-Adjunction Vision (112エージェント→24動詞マッピング) を v5.x (48動詞体系) に更新し、既存SKILLを増強する随伴プロジェクトの設計を行った。

## B: Background

- HGK v5.4: 57実体 (1公理+8座標+48認知操作)。S極知覚動詞 (V25-V36) と H-series が追加済み
- Agency-Agents (msitarzewski): 112エージェント × 11部門。Phase 1-2 完了 (24動詞でマッピング済み)
- 至上命題: 新規SKILLゼロ。既存SKILLの増強のみ。112エージェントの認知活動を完全に随伴吸収

## A: Assessment

### タスク1: Skills インポート (完了)

**57 → 84件** (+27):
- 専門スキル (11): code-protocols, governance, prompt-library, hermeneus-dispatch, basanos, gnosis-dialog, typos-skill, poiema, peira-exp, agora, impeccable
- U系汎用 (6): anti-skip, cut, hgk-ki, integration-audit, jules-pe, session-audit
- B系 (2): ccl-plan-bench, axiom-audit
- FM系 (3): fm-project-init, fm-excel-analyze, fm-xml-generate
- X系統合 (1): `/x` に12件を集約
- 新規マクロ/WF (3): ero (ソクラテス的問い), nous (再帰的深層探究), rom (コンテキスト外部化)

**description 統一**: 全非V系スキル (29件) を `Name (日本語) — Category。` 形式に変更

**不在確認**: 03_核心 (Kernel), 30_技法生成 (TekhneMaker) はディスク上に存在せず。スキップ。

### タスク2: Agency随伴の設計 (方向性確定、実装は次セッション)

**設計思想の変遷** (これが本セッション最大の成果):

1. **v1 (帰納的カタログ)**: 112エージェントをドメイン名でアドホックに5パターンに分類。P-1 "Audit Precision" 等。
   - **問題**: /akr の座標定義 (A×Mi = 行為的局所) に立ち返っていない。「監査」は /ele (推論) や /exe (知覚) の仕事であり、/akr (行為) の仕事ではない。他動詞の領域を侵食。MECE 違反。

2. **v2 (演繹的分類)**: 座標定義 A×Mi から5派生 (surgical/calibrate/patch/guard/units) を導出し、37エージェントを派生に1:1対応。
   - **問題**: きれいに分類できたが、SKILL本体に既にある派生定義の再記述。/akr を「賢く」しない。

3. **v3 設計思想 (確定、未実装)**: reference/ は「エージェントカタログ」ではなく **「U⊣N domain-specific strengthening」= 認知増強ノート**。
   - **本質**: 112エージェントの認知パターンを観察して、/akr が**既に持っているが言語化されていない能力**を発見する。ドメインが教えてくれる U⊣N の深化。
   - **例**: Blockchain domain → /akr.surgical の U₂ (盲目的確信) の意味が深化。「テストネットで通ったから大丈夫」も U₂ 違反。M-Loop の「1文字でも減らせないか」は gas cost に直結 (literal)。

**核心原則**:
- 「アドホックはMECEの敵」— パターン分類は座標定義から演繹
- 「すでにあるものを見つける」— 随伴とは外を見て内を知る鏡
- 「吸収 ≠ 分類」— reference/ は /akr を呼んだときに認知を変えるものでなければ価値がない

### 変更ファイル一覧

**~/.claude/skills/** (HGK リポジトリ外):
- 新規 27 ディレクトリ + SKILL.md (上記リスト)
- `x/SKILL.md` — 12 X-series を統合した単一スキル
- `ero/SKILL.md`, `nous/SKILL.md`, `rom/SKILL.md` — 新規マクロ/WF
- `akr/reference/precision-patterns.md` — v2 (演繹的分類)。v3で書き直し予定
- `akr/SKILL.md` — context に agency_adjunction knowledge を追加
- 29件の既存 SKILL.md — description 形式統一

## R: Recommendation

### 次セッションの最優先タスク

1. **`akr/reference/precision-patterns.md` v3 を書く**
   - v2 の演繹的分類 (5派生×エージェントマッピング) は索引として保持
   - v3 の本体: 各派生の U⊣N domain-specific strengthening
   - テンプレート: 「{domain} が /akr.{derivative} に教えること — U₀〜U₄ のどれがどう深化するか」
   - /akr で v3 パターンを確立し、残り23動詞への横展開テンプレートにする

2. **横展開の優先順位** (頻度順):
   /kat(31) → /tek(29) → /lys(28) → /ene(22) → /sag(20) → /ops(18) → /ske(18)

3. **Vision Document 更新**: agency_adjunction_vision.md に v5.x 拡張セクション + v3 設計思想を追記

### 未着手

- v5.x の φ_SI 前駆列 (112エージェントテーブルへの S極動詞追加) — v3 完成後
- H-series 反射列 — v3 完成後
- 48動詞使用統計の再計算 — v3 完成後

---

## Session Metrics

| 項目 | 値 |
|:-----|:---|
| WF使用 | /u+ ×1, /u ×1, /u*~/exe ×1 |
| Skills 変更数 | 新規27 + 更新30 = 57件 |
| 決定事項 | D1-D6 (6件、全て確定) |
| 未確定射 | v3 実装、横展開 |

## Nomoi フィードバック

なし (違反検出なし)

## 🧠 信念 (Doxa)

- **DX-new**: 「随伴とは鏡」— 外部の112エージェントの認知パターンを見ることで、内部のSKILLが「既に持っているが言語化されていない能力」を発見する。分類は吸収ではない。U⊣N の domain-specific strengthening が吸収の本体。
- **DX-new**: 「アドホックはMECEの敵」— reference/ のパターン分類は動詞の座標定義 (Flow × Coordinate) から演繹すべき。帰納的にドメイン名から分類すると他動詞の領域を侵食する。

---

*R(S) 生成: 2026-03-28 — /bye+ v9.0-cc*
