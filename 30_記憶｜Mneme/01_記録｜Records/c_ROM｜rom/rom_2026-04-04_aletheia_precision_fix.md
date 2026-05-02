---
rom_id: rom_2026-04-04_aletheia_precision_fix
session_id: 2026-04-04
created_at: 2026-04-04
rom_type: distilled
reliability: High
topics: [aletheia, precision, ガロア接続, 確信度記法, U_sensory, 忘却関手, Kernel公理]
exec_summary: |
  aletheia.md v3.3 を /sap 全文精読→/exe 弱点検出→/dio→/akr×2 のパイプラインで修正。
  3点の内部不整合を解消 (確信度記法定義追加・記号衝突修正・U_sensory 行再配置)。
  axiom_hierarchy.md / kalon.md とのクロスチェックは次セッション持ち越し。
---

# aletheia.md 精読・吟味・修正セッション (2026-04-04)

> **[DECISION]** aletheia.md v3.3 の内部整合性修正を3点実施した。axiom_hierarchy.md との外部整合は未実施 (🕳️ open)。

---

## 1. 実施した修正 (全 ε=0)

### 1-1. §8 確信度記法定義の追加 (/dio.impr)

**問題**: `[推定 70%] 80%` という二重数値の意味が文書内で未定義。precision を主題とする文書の U_precision 自己適用。

**修正**: §8「確信度」セクション冒頭に以下を追記:
```
> **記法定義**: 確信度ラベルは2形式が併用される。
> - **標準形** `[カテゴリ 閾値%] 実値%` — 括弧内は tier 下限 (仮説 45% / 推定 70% / 確信 90%)、括弧外が現在の確信値
> - **省略形** `[カテゴリ 実値%]` — 実値が tier 閾値と異なる数値の場合に判別可能
```

**根本原因**: Kernel 公理文書が外部 RULES の記法に依存し自己完結していなかった (U_self)。

**再発防止**: §8 に定義が存在するため、新規ラベル追加時の参照先が確立した。

---

### 1-2. ガロア接続記号衝突の修正 (/akr.surgical)

**問題**: L549 (Value) と L553 (Valence) が同一記号 `$F_{val} \dashv G_{val}$` を使用。L617 にも残存。

**修正**:
- L549: `$F_{val}$` → `$F_{va}$` (Value = Va)
- L553: `$F_{val}$` → `$F_{vl}$` (Valence = Vl)
- L617: `$G_{val}$` → `$G_{va}$`

**根拠**: HGK 略称体系は Va=Value、Vl=Valence (§5.7.7 テーブルで確認)。

**副作用**: Grep で `$F_{val}$`/`$G_{val}$` 残存ゼロ確認済み。

---

### 1-3. §2.1 U_sensory Basis 行の再配置 (/akr.surgical)

**問題**: U_sensory (Basis) 行が n=4 と n=∞-1 の間に挟まれており、§2.2/§3 の構造図 (Tower 外・直交軸) と視覚的に不整合。

**修正**: Basis 行を Tower 最上部に移動し、区切り行を追加:
```
| **Basis** | **Optic/Lens** | **U_sensory** | ... |
| *(↓ n-cell Tower — Tower の前提。詳細 →§2.2)* | | | | |
| **n=1** | 1-cell (射) | **U_arrow** | ... |
```

**補足**: §2.2 L221「§2 テーブルで n=∞-0 に配置したのは ad hoc だった」は歴史的記述として保持 (改訂動機の説明)。

---

## 2. /exe で検出した未解決 issue (次セッション候補)

| 重要度 | 問題 | 推奨操作 |
|:-------|:-----|:---------|
| 🟡 | axiom_hierarchy.md との記号整合未検証 (`$F_{va}$`/`$F_{vl}$`) | `/sap` axiom_hierarchy.md → `/exe` |
| 🟡 | 翻訳仮説 (§2.1 n-cell→認知忘却の対応) の水準注記が §5.7.4.2 にのみ分散 | `/akr` — §2.1 直下に `[推定 70%] 75%` ラベル追加 |
| 🟡 | §5 の肥大化 (§5.6.5.5 Hyphē 実証、§5.7.10 等が公理文書に混在) | `/arh` — Peira へ分離検討 |
| 🟢 | σ 置換の一意性定理が自然言語の認知状態定義 $s_i$ に依存 | `/akr` — $s_i$ の形式化 |

---

## 3. aletheia.md の構造概要 (次セッション参照用)

```
§0 動機・位置づけ — Alētheia = a(否定) + léthē(忘却)。U⊣N 随伴と同型
§1 公理: VFE と忘却 — U0: F[U(q)] ≥ F[q]
§2 生成原理 — n-cell tower の各レベルが U パターン (9基底)
  §2.1 生成テーブル (U_sensory=Basis 行が最上部に移動済み)
  §2.2 U_sensory: Optic/Lens 軸 (Tower と直交)
  §2.3 U_depth: 自然変換の忘却
§3 フィルトレーション — U_arrow ≤ U_compose ≤ ... ≤ U_self
§4 テンソル積 — 独立忘却の同時発動 (BRD 被覆率 96%)
§5 U⊣N 随伴 (最大節、約1480行)
  §5.5 N-Series 独立形式化
  §5.6 T9 科学性判定 (FEP/圏論/Bellman/Shannon/熱力学)
  §5.7 Kalon 普遍性予想 + 実験群 (忘却序列、A/Bテスト、embedding)
§6 完全性問題 — Theorema Egregium Cognitionis (S(e) 計算可能性)
§7 /noe 射影関手 — F_noe: Alē → Cog (Phase 順序一意性定理)
§8 確信度 (記法定義を追記済み)
§9 次ステップ
§10 参照
```

---

## 4. パイプライン実績

```
/sap (精読) → 2916行全文把握
/exe (吟味) → 🔴2 🟡5 🟢3 検出
/dio (記法定義追加) → CQM 5/5
/akr (記号衝突) → L549/L553/L617、ε=0
/epo (保留) → §2.1 行位置を Tolmetes 確認まで保留 → 即解消
/akr (Basis 行移動) → ε=0
/beb (条件付き承認) → aletheia.md 内部整合範囲で承認
```

---

## 5. 承認条件と撤回条件

**承認**: aletheia.md 単体の内部整合性の範囲
**撤回条件**: axiom_hierarchy.md で `$F_{va}$`/`$F_{vl}$` と異なる記号体系が発見された場合

<!-- ROM_GUIDE
primary_use: aletheia.md の修正履歴参照、次セッションの継続作業の起点
retrieval_keywords: aletheia, 確信度記法, ガロア接続, U_sensory, Basis, precision, 忘却関手
expiry: axiom_hierarchy.md クロスチェック完了まで有効
-->
