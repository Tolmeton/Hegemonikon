---
doc_id: "FEP_EPISTEMIC_DOCUMENT_MAP"
version: "1.2.0"
tier: "KERNEL"
status: "ACTIVE"
created: "2026-04-11"
updated: "2026-04-11"
---

# FEP 認識論文書束 — 接続図

この文書は、FEP の認識論的地位をめぐる 3 文書の役割分担と更新方向を固定するためのハブである。本文を統合して 1 本に潰すのではなく、**正本 / 全体展開 / 独立抽出** の 3 層として管理する。

---

## 1. 役割分担

| 役割 | パス | 何を担うか |
|:--|:--|:--|
| **正本** | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/E_形式化｜Formalization/fep_epistemic_status.md` | Kernel 水準の定義・確信度・論点整理。安定した主張はまずここに反映する |
| **全体展開** | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/反証可能性は死んだ_エッセイ.md` | ポパー批判から FEP/T9 提示までを一気通貫で論じる長編エッセイ |
| **独立抽出** | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/エッセイ_理解と予測の随伴.md` | 長編エッセイ §9 の独立配布版。「説明ばかりで予測がない」批判への局所応答に特化 |

---

## 2. 依存関係

```text
fep_epistemic_status.md
  ├─ 理論核を供給する
  └─ 反証可能性は死んだ_エッセイ.md が論争的に拡張する
       └─ エッセイ_理解と予測の随伴.md が §9 を独立抽出する
```

重要なのは、依存は**対称ではない**ことだ。

- `fep_epistemic_status.md` は正本であり、概念の安定版を置く。
- `反証可能性は死んだ_エッセイ.md` は正本を踏まえて論証を増幅する。
- `エッセイ_理解と予測の随伴.md` は長編の局所切り出しであり、独立読解のための薄い包装を担う。

### 補助メモ

上の 3 文書束に加えて、Kernel 側には次の補助メモがぶら下がる。

| メモ | 役割 |
|:--|:--|
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/E_形式化｜Formalization/mb_escalation_conditions.md` | `MB₀/MBₚ/MB𝒻` の昇格条件と Aguilera/Bruineberg 型批判の射程を切る |
| `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/E_形式化｜Formalization/fep_critique_frontier.md` | `守れる批判 / 部分的に守れる批判 / まだ守れない批判` を切り分ける |

---

## 3. 読順

1. 構図だけ掴みたいときは `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/E_形式化｜Formalization/fep_epistemic_status.md`
2. ポパー批判まで含めて通しで読むときは `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/反証可能性は死んだ_エッセイ.md`
3. 「理解と予測」の一点だけを単独配布するときは `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/エッセイ_理解と予測の随伴.md`

---

## 4. 更新規則

1. 安定した定義・確信度・分類を変えるときは、先に `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/00_核心｜Kernel/A_公理｜Axioms/E_形式化｜Formalization/fep_epistemic_status.md` を更新する。
2. ポパー批判や超ひも理論との比較など、論争的な展開を足すときは `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/反証可能性は死んだ_エッセイ.md` に追加する。
3. 「理解と予測」節の主張が変わったときは、長編エッセイと `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/エッセイ_理解と予測の随伴.md` の両方を同期対象にする。
4. 長編だけにある比喩・レトリック・射程外の枝は、正本に自動逆流させない。Kernel に戻すのは、主張が安定化した部分だけに限る。
5. `MB` の層分けや FEP 批判の応答境界が変わったときは、まず補助メモ (`mb_escalation_conditions.md`, `fep_critique_frontier.md`) を更新し、その要約だけを正本へ戻す。

---

*v1.0.0 — 2026-04-11。`fep_epistemic_status.md` / `反証可能性は死んだ_エッセイ.md` / `エッセイ_理解と予測の随伴.md` の役割分担・依存関係・更新規則を固定する接続ハブとして新設。*
*v1.1.0 — 2026-04-11。実体ファイルを `drafts/standalone` に統一。Kernel 正本と派生エッセイの同期対象を、存在する絶対パスへ揃えた。*
*v1.2.0 — 2026-04-11。補助メモ層を明示化。`mb_escalation_conditions.md` と `fep_critique_frontier.md` を、正本へ接続される Kernel 補助メモとして追加した。*
