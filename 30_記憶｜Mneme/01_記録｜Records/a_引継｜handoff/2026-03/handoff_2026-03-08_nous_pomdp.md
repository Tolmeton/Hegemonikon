# Handoff: Nous POMDP MECE 再構築
- **日時**: 2026-03-08 15:40
- **セッション**: Nous ディレクトリ構造の POMDP 演繹的再構築

---

## 完了した作業

### Phase 1: Band 00 内部整理
- サブディレクトリを `00_` → `A_` 命名に統一 (11 dirs)
- A_公理 から非公理を除去: 6→02_知識, 1→03_企画, 3→01_手法
- 亡霊 `00_規範｜Nomos` を解体: CCL(13)→01_手法/G_CCL, 基準(4)→01_手法/H_基準

### Phase 2: Decision Tree の反駁と再構築
- `/ele+` で旧 Decision Tree を反駁 — 5つの矛盾を発見
  - 核心: FEP 括弧が飾り (表層付着)、消去法による Epistēmē 定義、Is/Ought 混同
- **代替案A (POMDP 直接マッピング)** を採用:
  - 唯一の問い: 「この項目は POMDP のどの変数か？」
  - P(s)→00_原則, P(o|s)→01_手法, Q(s|o)→02_知識, G(π)→03_企画, o→04_素材, Q_{t-1}→09_保管
- `README.md` を POMDP マッピング版に書き換え

### Phase 3: 全帯 POMDP 再分類
- 02_知識/A_文書: 非知識ファイル14件を除去 (.py→20_機構, .ps1→80_運用, etc.)
- 02_知識: C_信念(doxa≠epistēmē)→03_企画/D_信念, D_解釈文書(G(π))→03_企画/E_解釈
- 02_知識: プレフィックス衝突解消 (C→D→E リナンバー)
- 03_企画/B_活用: Bytebot(317)→40_応用, Aristos(26)→40_応用, Infrastructure(9)→80_運用
- 03_企画: ルースファイルを C_ビジョン に整理

---

## 最終構造

```
10_知性｜Nous/
├── 00_原則｜Arkhē (P(s))
│   ├── A_公理｜Axioms (19 files + 7 subdirs)
│   └── B_規範｜Nomos (symlink)
├── 01_手法｜Methodos (P(o|s))
│   ├── A-F (WF, WFModules, Skills, Macros, Hooks, Templates)
│   ├── G_CCL｜CCL (14 items)
│   └── H_基準｜Standards (6 files)
├── 02_知識｜Epistēmē (Q(s|o))
│   ├── A_文書｜Docs (21)
│   ├── B_知識項目｜KI (147)
│   └── E_美論｜Kalon (37)
├── 03_企画｜Boulēsis (G(π))
│   ├── A_探索 (4), B_活用 (61), C_ビジョン (5)
│   ├── D_信念 (22), E_解釈 (10)
│   └── registry.yaml
└── 09_保管｜Archeia (Q_{t-1})
    ├── A-C (旧規則, 旧技能, 旧手順)
    └── D_旧公理構造
```

---

## 教訓

1. **表層付着 vs 馴化**: FEP の変数名を括弧で後付けするのと、変数の意味が構造そのものになるのは全く別物
2. **Is/Ought 混同**: 「あるべき場所」だけで推論すると、実在するファイルを見落とす (operators.md 誤報事件)
3. **Syncthing は Send-Only**: GALLERIA 側は sendonly。「別デバイスに上書きされた」仮説は棄却

---

## 残課題

- [ ] 02_知識 の A→B→E プレフィックス飛び — 放置 (移動痕跡として有用)
- [ ] 03_企画/A_探索 の Autophonos (4件) — 出自不明、内容未確認
- [ ] E_美論 の内部構造 (docs/specs/research/doxa) — 自己完結しており分解不要と判断
- [ ] POMDP マッピングの境界ケース集 — 実運用で収集する

---

## 関連ファイル

- [README.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/README.md) — POMDP 分類基準
- [implementation_plan.md](file:///home/makaron8426/.gemini/antigravity/brain/6f951329-4c4a-4dcb-8b9a-7d85dea8888a/implementation_plan.md) — 最終ツリー
