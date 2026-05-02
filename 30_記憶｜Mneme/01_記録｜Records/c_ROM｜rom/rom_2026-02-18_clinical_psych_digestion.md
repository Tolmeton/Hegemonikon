---
rom_id: rom_2026-02-18_clinical_psych_digestion
session_id: e8da048c-df3a-4136-bb09-1726c0ca8027
created_at: 2026-02-18 08:39
rom_type: rag_optimized
reliability: High
topics: [clinical-psychology, sfbt, cbt, mq-sq, fep, digestion, category-theory, monad, cognitive-distortion]
exec_summary: |
  臨床心理学 (SFBT/CBT) を HGK に統合。MQ/SQ を3つのΔ層WFに消化済み: 
  /noe=圏論(Limit Apex), /bou=FEP(EFE/VFE), /zet=モナド(Kleisli射)。
  「付着→消化」パターンを法則化。
---

# 臨床心理学 → HGK 統合 — 付着から消化へ {#sec_01_clinical_psych .core}

> **[DECISION]** SFBT/CBT の認知技法を HGK に統合。外来技法としてではなく、FEP の操作的定義として消化。

## 消化の核心原理 {#sec_02_digestion_principle .principle}

> **[RULE]** 付着 = 外来 Phase を追加するだけ。消化 = 既存 Phase に吸収 + 各 WF 固有の理論言語に翻訳。

> **[DISCOVERY]** MQ (ミラクル・クエスチョン) = EFE の P(o|C) 確定操作。SQ (スケーリング・クエスチョン) = VFE の D_KL 測定操作。SFBT は「FEP の認知的操作を日常言語で実装した技法」。

## Phase 別変更リスト {#sec_03_changes .reference}

### BC/Kernel 変更 {#sec_03a_bc}

> **[FACT]** 以下のファイルが変更済み:

| ファイル | 変更 |
|:---------|:-----|
| `behavioral_constraints.md` | BC-14: 5列 Thought Record (F→D→C→A→S), BC-6: SFBT 解決志向転換 |
| `bye.md` | Step 3.7: SFBT 例外分析 |
| `cognitive_axioms.md` | A5 建設的認知原則追加 (v1.1) |
| `kernel/constructive_cognition.md` | **[NEW]** FEP Function + ストア派制御の二分法 |
| `kernel/cognitive_distortion_universality.md` | **[NEW]** 認知歪みは基質非依存 |
| `kernel/fep_epistemic_status.md` | §4.5 反証可能性の三脚擁護 (v1.1.0) |

### WF 消化マップ {#sec_03b_wf}

> **[DECISION]** 3つのΔ層 WF で消化完了:

| WF | MQ 消化後 | SQ 消化後 | 統合先 |
|:---|:---------|:---------|:-------|
| `/noe` | **Limit Apex 先行定義** | **Kalon 距離測定** | Phase 0 / Phase 5 に吸収 |
| `/bou` | **P(o\|C) 具体化** | **VFE 外在化** | Phase 0 / Phase 5 に吸収 |
| `/zet` | **T の到達型定義** | **Kleisli 射の評価** | Phase 0.5 / Phase 3.5 を改題 |

### 共通モジュール {#sec_03c_module}

> **[FACT]** `workflow-modules/sfbt-tools.md` → 「予測誤差操作ツール」に改題。FEP 操作を一次的記述、SFBT を出典に降格。

### CD Scan (/dia) {#sec_03d_cd_scan}

> **[FACT]** `/dia` STEP 0.9 に CD Scan 追加。LLM-CD 7番号: CD-1(全か無か), CD-3(確証バイアス), CD-4(確信度歪み), CD-5(迎合推論), CD-6(べき思考), CD-10(ハルシネーション), CD-12(アンカリング)。

## パターン法則化 {#sec_04_patterns}

> **[DISCOVERY]** patterns.yaml に3パターン追加:

1. **attachment-to-digestion**: 外来技法は Phase 追加ではなく既存 Phase への吸収が正しい
2. **prediction-error-as-universal-cognition**: 経験的に有効な臨床技法 = FEP の操作的定義
3. **falsifiability-frequency-decay**: 理論が真理に近づくほど反証事象の頻度が減る

## 残タスク (Phase 4) {#sec_05_remaining}

- [ ] F1: 消化済み /noe の実践テスト — Limit Apex 先行定義が Phase 0 で自然に機能するか
- [ ] F2: constructive_cognition.md の /noe+ 精緻化 — FEP ↔ ストア派の圏論的同型
- [ ] F3: /dia CD Scan の実践テスト — 実際のレビューで CD-1〜CD-12 スキャン

> **[OPINION]** Phase 0 の肥大化リスク (盲点チェック + Read + Gnōsis + Apex = 4操作) が F1 の検証ポイント。

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "MQ/SQ とは何か、どう使うか"
  - "SFBT を HGK にどう統合したか"
  - "認知歪みの基質非依存性"
  - "付着と消化の違い"
answer_strategy: "まず sec_02 の消化原理を確認し、sec_03b の WF 消化マップで具体的な変更を参照"
confidence_notes: "全変更は実ファイルに反映済み。F1-F3 は未実行"
related_roms: ["rom_2026-02-18_ccl_macro_context"]
-->

---

*ROM+ v1.0 — 臨床心理学統合 Phase 1-3 完了 (2026-02-18)*
