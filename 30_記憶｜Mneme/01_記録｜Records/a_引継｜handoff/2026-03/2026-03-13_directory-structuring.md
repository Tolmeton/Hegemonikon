# Handoff: 全体構造化セッション
**日時**: 2026-03-13T17:58 JST
**セッション種別**: 構造化・ドキュメント整備

---

## 成果サマリ

**38 README 新規作成 + 3 ファイル移動** で HGK ディレクトリ体系のドキュメントカバレッジを大幅に改善。

| Phase | 対象 | 件数 |
|:------|:----|:-----|
| A | Mekhane 16モジュール | 15 README |
| B | Epistēmē + Nous | 4 README |
| — | 散逸ファイル移動 | 3 ファイル |
| C | 制約・手順サブディレクトリ | 8 README |
| D | Mneme・External・Ops | 11 README |

---

## 主要な決定事項

1. **Mekhane の空ディレクトリ**: シンボリックリンクではなく README による MAP 方式を採用。Syncthing 環境との互換性を考慮
2. **散逸ファイル再配置**:
   - `euporia.md` (36KB) + `euporia_blindspots.md` → `Boulēsis/07_行為可能性/`
   - `wf_evaluation_axes.md` → `手順/A_手順/`
   - `knowledge.yaml` は Epistēmē ルートに残留 (設定ファイル)
3. **README テンプレート**: PURPOSE + ファイル/ディレクトリ一覧テーブル + MAP (Boulēsis PJ, Kernel, MCP 連携)

---

## 生成した README 一覧

### Mekhane (15)
`00_概要` (全体対応表), `01_MCP`, `02_車体 Ochema`, `03_解釈 Hermeneus`, `04_共感 Sympatheia`, `05_樹 Dendron`, `06_観察 Periskope`, `07_試金石 Basanos`, `08_最適化 Aristos`, `09_編組 Symploke`, `10_想起 Anamnesis`, `11_完遂 Synteleia`, `12_制作 Poiema`, `13_FEP`, `14_分類 Taxis`

### Epistēmē + Nous (4)
`Epistēmē/` ルート, `B_知識項目/`, `01_制約/`, `02_手順/`

### 制約・手順サブ (8)
制約 `B_核/` / 手順 `A_手順/`, `B_WFモジュール/`, `C_技能/` (69ディレクトリ索引), `D_マクロ/`, `E_フック/`, `F_雛形/`, `H_基準/`

### Mneme・External・Ops (11)
Mneme `01_記録/`, `02_索引/`, `03_素材/`, `04_知識/`, `05_状態/` / `50_外部/` / Ops `00_スクリプト/` (15スクリプト索引), `01_開発ツール/`, `04_配備/`, `05_設定/`, `06_文書/`

---

## 残タスク・未踏領域

### 高優先度
- [ ] **Mekhane 番号外モジュール**: `16_消化｜Pepsis` 等の存在確認と README
- [ ] **Peira サブディレクトリ README**: 7サブ (汎用, 検証, テスト, リモート, 知覚PoC, スペクトル解析, 自律研究)
- [ ] **Archive サブディレクトリ README**: 16サブ (旧規則, 旧技能, 旧WF, 旧公理 等)

### 中優先度
- [ ] **既存 README の品質向上**: Mneme本体 (2.3KB), Peira (1.3KB), Ops (1KB), Archive (0.9KB) — MAP セクション追加
- [ ] **制約/F_基準**: 空ディレクトリの扱い決定

### 低優先度
- [ ] **V-series/X-series スキル個別 README**: 69ディレクトリ (既に SKILL.md が各ディレクトリに存在)
- [ ] **WFモジュール個別 README**: 15テーマ別サブディレクトリ

---

## 発見事項

1. **C_技能 の規模**: 69ディレクトリ (V24 + X12 + U7 + ドメイン26) は体系内最大の集合体
2. **Ops/Scripts の散逸**: 16スクリプトが用途不明のまま格納。索引化で可視性が大幅改善
3. **External の5パッケージ**: Bytebot, MiroFish, agency-agents, deer-flow, openclaw の用途を初めて一覧化
4. **Mneme/02_索引**: pkl ファイル群 (合計 12MB+) の正確なコンテンツ記録

---

*Handoff generated: 2026-03-13T17:58 JST*
