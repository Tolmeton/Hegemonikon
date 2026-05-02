# Session Handoff: 2026-02-27 HGK v4.1 用語統一 + graph.py 実装

## 1. Situation (現在地)

HGK v4.1 体系 (1公理 + 7座標 + 24動詞 + 15結合規則) への用語統一が**完了**した。
テキスト修正 (Phase 1-2) と API 実装の v4.1 化 (Phase 3) の両方を包括的に実施。

## 2. Background (経緯)

旧体系 (96要素/7公理/72関係) の表記がドキュメント・コード・APIに散在していた。
前セッションで 8 ファイルのテキスト修正を完了。本セッションで残り 7 ファイルのテキスト修正 +
`mekhane/api/routes/graph.py` の**実装レベルの v4.1 化**を実施。

## 3. Assessment (評価)

### 完了したこと

**テキスト修正 (Phase 1-2 — 全 15 ファイル)**:

- `README.md`: 全面改訂 (体系テーブル、Mermaid 図、X-series、フッター)
- `AGENTS.md`, `graph.py` (コメント), `knowledge.yaml`, `AMBITION.md`, `zen_extraction.md`, `PROOF.md`(_archived)
- 前セッション分: `SKILL.md` (x-os, p2-hodos), `STRUCTURE.md`, `ARCHITECTURE.md`, `wf-cheatsheet.html`, `bye.md`, `api-types.ts`, `AMBITION.md`

**graph.py v4.1 実装 (Phase 3)**:

- **SERIES**: Pure/Mixed 区別を廃止 → 全6族が Flow × 修飾座標の対等な構造に
- **24動詞名**: Metron→Skepsis, Propatheia→Katalēpsis, Pistis→Epochē 等、v4.1 命名に全面更新
- **空間配置**: 旧三角形 (Trigonon) → 正六角形 (Hexagon, R=6.0) に変更
- **X-series エッジ**: 9ペア×8=72エッジ → K₆ に基づく 15ペア×4=60エッジ+24恒等射=84エッジ
- **ワークフロースラッグ**: 明示的マッピングテーブル `_WORKFLOW_SLUGS` (24個一意)
- **API メタデータ**: `meta.trigonon` → `meta.topology` (K₆)、`meta.structure` に 32実体体系情報

### /ele+ による反証で発見・修正した欠陥

| 欠陥 | 原因 | 修正 |
|:-----|:-----|:-----|
| ワークフロースラッグ 4重複 (`/pro`) + 2重複 (`/syn`) + Unicode (`/noē`) | `name.lower()[:3]` の自動生成 | 明示的マッピングテーブルに変更 |
| naturality/meaning フィールド逆転 | タプル展開の変数順序ミス | 展開順を修正 |
| GraphNode.type description 不一致 | "Pure or Mixed" が残存 | "Flow" に修正 |

## 4. Recommendation (次のアクション)

- [ ] **axiom_hierarchy.md** に Creator が追記した H4 Doxa 吸収セクション (2026-02-27) — graph.py への影響は無し (H4 は既に Dokimasia に更新済み)
- [ ] **graph.py の Series ID ↔ 族の対応**: 旧 K=Chronos/A=Orexis を K=Orexis/A=Chronos に入れ替えた。ワークフロー側との整合性を確認する余地あり
- [ ] **フロントエンド (graph3d.ts)**: createNodeGeometry の isPure 判定が type="Flow" で変わる可能性 → 要確認
- [ ] **nous/ ワークフロー再編**: 並行セッション (514fad64, 248e6d0f) で nous WF の v4.1 再編が進行中

## 5. 変更ファイル一覧

```
mekhane/api/routes/graph.py        # 主要変更: v4.1 実装
README.md                          # 全面改訂
nous/docs/AGENTS.md                # パイプライン更新
nous/projects/knowledge.yaml       # kernel summary 更新
hgk/docs/AMBITION.md               # 32実体グラフ
pepsis/python/designs/zen_extraction.md  # v4.1 用語
mekhane/_archived/axioms/PROOF.md  # PURPOSE 更新
nous/kernel/axiom_hierarchy.md     # Creator による H4 Doxa 吸収追記
```

## 6. 法則化

> **Unicode スラッグの罠**: ギリシャ語転写 (ē, ō 等) を含む文字列に `[:3]` を適用すると、
> ASCII とは異なるスラッグが生成される。ワークフロースラッグのような ID 生成には
> **必ず明示的マッピングテーブルを使え**。自動生成による「賢い」省力化は衝突と Unicode バグの温床になる。

---
*Created by: Antigravity AI (Claude) | Mode: Execution | 2026-02-27T16:22*
