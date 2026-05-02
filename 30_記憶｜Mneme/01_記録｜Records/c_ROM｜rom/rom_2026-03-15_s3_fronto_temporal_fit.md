---
rom_id: rom_2026-03-15_s3_fronto_temporal_fit
session_id: a9054af6-3b54-4a08-8c0e-2d272cd546d2
created_at: 2026-03-15 12:47
rom_type: rag_optimized
reliability: High
topics: [S-III, fronto-temporal, Wang2023, predictive_coding, precision, FEP, N-9, N-10, N-11, N-12, Akribeia, dipole_reversal]
exec_summary: |
  S-III 4段パイプライン (N-9→N-12) と Wang et al. (2023) fronto-temporal 階層の構造的対応を
  /fit → SFBT → /ele+ → C>>A → P&G精読 の5段階で検証し、確信度 [推定 70%] に到達。
  5つの矛盾を検出、3つを解消。N-12 を P&G (2014) forward model で 65→70% に強化。
search_keywords: [精度チャネル, prediction propagation, dipole reversal, event model, LIFC, temporal cortex, N400, P600, precision matching, error resolution, Complexity更新, Accuracy修正, forward model, Pickering, Garrod, production, control mechanism]
---

# S-III ≅ Fronto-temporal 構造対応 {#sec_01_overview .s3 .fit .ele}

> **[DECISION]** S-III 4段パイプラインは Wang et al. (2023) の fronto-temporal 階層と構造的に対応する (4/4段)。確信度 [推定 70%]

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "S-III の神経科学的根拠は？"
  - "N-9/N-10/N-11/N-12 は脳のどの処理に対応するか？"
  - "fronto-temporal 階層と Akribeia の関係は？"
  - "precision channel の空間分離とは？"
answer_strategy: "まず 4段対応テーブルを示し、次に各段の SOURCE 根拠を引用する"
confidence_notes: "N-9/N-10 は 80%、N-11 は 70% (著者明示)、N-12 は 70% (P&G forward model control で強化)"
related_roms: []
-->

## 4段対応テーブル {#sec_02_mapping .core}

> **[FACT]** 以下の対応は Wang et al. (2023) Cerebral Cortex [SOURCE: PMC10110445 全文精読] に基づく

| S-III | 位相 | Wang 対応 | 確信度 |
|-------|------|-----------|--------|
| N-9 (入力精度) | P-1 Aisthēsis | fusiform + temporal: orthographic → lexico-semantic PE (N400, 300-500ms) | 80% |
| N-10 (処理精度) | P-2 Dianoia | predictability effect (temporal のみ) ≠ plausibility effect (temporal+LIFC) → チャネル分離 | 80% |
| N-11 (出力精度) | P-3 Ekphrasis | LIFC→temporal feedback: dipole reversal (600-1000ms)。著者: "ensures lower-level regions encode information consistent with global gestalt" | 70% |
| N-12 (行動精度) | P-4 Praxis | forward model: prediction vs outcome comparison → control mechanism (P&G 2014) | 70% |

## 検証履歴 {#sec_03_history .process}

> **[FACT]** 4段階の検証を経て到達

| 段階 | 操作 | 結果 | 確信度変化 |
|------|------|------|-----------|
| 1. /fit | 初回構造照合 | N-11 欠落 → 3/4段 🟡 吸収 | 55% → 60% |
| 2. SFBT | Creator 指摘「やっていないだけでは？」 | N-11 = precision matching → 4/4段回復 | 60% → 70% |
| 3. /ele+ | 5矛盾検出 (直列vs分岐, N-11抽象化, N-12弱対応, 非特異性, 1論文依存) | N7 を 65% に下方修正 | 70% → 65% |
| 4. C>>A | Wang SOURCE 再精読で矛盾1,2,5 を解消 | N-12 は 65% に留まるが全体 70% 回復 | 65% → 70% |
| 5. P&G 精読 | Pickering & Garrod (2014) PMC4217443 全文精読 | N-12 = forward model control → 70% | 70% → 70% (N-12: 65→70%) |

## 矛盾と解消 {#sec_04_contradictions .critical}

> **[DISCOVERY]** /ele+ で5矛盾を検出し、Wang SOURCE で3つを解消

### 矛盾1: 直列 vs 分岐 → 解消 ✅ {#sec_04_1 .resolved}
- S-III = 4段直列 / Wang = plausible/implausible 分岐
- **解消**: 分岐ではない。同一の下降プロセスの成功/失敗。両条件とも "predictions propagated down the hierarchy" [SOURCE: Wang Discussion §600-1000ms]

### 矛盾2: N-11 過度の抽象化 → 解消 ✅ {#sec_04_2 .resolved}
- "precision matching" は抽象すぎて N-9/N-10 と区別がつかない？
- **解消**: Wang が明示的に "ensures lower-level regions encode information consistent with global gestalt" と述べている (Lee & Mumford 2003 引用) [SOURCE: Wang Discussion §600-1000ms, plausible subsection]

### 矛盾5: N-12 弱対応 → 解消 ✅ (P&G 強化) {#sec_04_5 .resolved}
- N-12「正確な実行」≠ Wang「PE 解消」
- **解消**: Pickering & Garrod (2014) [SOURCE: PMC4217443]: "sensory estimates can be compared with the actual consequences to provide a control mechanism"
- Wang の comprehension データは production の forward model の再利用 (P&G 理論) → comprehension で観察された prediction propagation は本来 production のメカニズム
- **N-12 = forward model の prediction vs outcome 比較 = 行動精度制御** → 70%

### 矛盾3,4: 修正不要 {#sec_04_34}
- 矛盾3 (非特異性): 4位相が脳の処理段階と対応する = S-III 固有ではなく位相系全体の正当性
- 矛盾4 (1論文依存): 確信度 70% が正しく反映。Stoll (2026) で補強可能

## Key Quotes [SOURCE: PMC10110445] {#sec_05_quotes .source}

> **[FACT]** 以下は Wang et al. (2023) の直接引用

### Plausible 600-1000ms
> "new top-down predictions...are propagated down the cortical hierarchy. When these new top-down predictions activate the left inferior frontal cortex, they will produce top-down error at the level of the event model...when they reach the left temporal cortex they will produce top-down error at the lexico-semantic level"

### Feedback の機能 (Lee & Mumford 2003 引用)
> "this type of feedback re-activation ensures that lower-level regions encode information that is consistent with global gestalt representations that are encoded in higher cortical areas"

### Implausible 600-1000ms
> "higher cortical levels failed to generate accurate top-down predictions that would have otherwise suppressed this low-level error within this late time-window"

### New learning (著者は "speculate" と明記)
> "this medial temporal activity supported new learning/adaptation, which was triggered by the failure of the current generative model to explain the input—that is, to minimize error across the cortical hierarchy"

### Forward model control (P&G 2014)
> "These sensory estimates can be compared with the actual consequences to provide a control mechanism for spoken language" [SOURCE: PMC4217443]

> "listeners can predict what other speakers are likely to say next by covertly imitating their production processes, deriving the speaker's underlying intention" [SOURCE: PMC4217443]

> "Silbert et al.'s study shows tight coupling between much of production and comprehension" [SOURCE: PMC4217443]

## 次のステップ {#sec_06_next .action}

> **[RULE]** N-12 (70%) は P&G forward model で安定。さらなる強化には運動制御の直接証拠が必要

- ✅ P&G (2014) で comprehension→production の理論的橋渡しを確保
- 🕳️ Kim et al. (2023) の hierarchical state feedback control of speech → N-12 の直接的運動制御根拠
- 🕳️ Zhang et al. (2023) の parietal-temporal forward model connectivity → 空間的根拠

## 教訓 {#sec_07_lessons .meta}

> **[DISCOVERY]** 検証プロセスから得た方法論的教訓

1. **SFBT の威力**: Creator の「本当にできないのか」で N-11 対応を発見。「やっていない」≠「できない」
2. **Honesty Gate の必要性**: /ele+ Phase 5 で矛盾2 への反動的過剰批判 (RQS 4/5) を自己検出
3. **SOURCE が味方する**: N-11 の抽象化を心配したが、著者自身が機能を明示的に述べていた
4. **N-12 の飛躍**: 65% → 70%。P&G の forward model theory が production-comprehension gap を埋めた

## 📖 参照 {#sec_08_refs}

- [eat_stoll2026](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/30_記憶｜Mneme/04_知識｜Gnosis/01_文献｜Literature/articles/eat_stoll2026_prediction_syntax_grounding.md) N7 エントリ
- [episteme-fep-lens.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/.agents/rules/episteme-fep-lens.md) F2/F5 証拠
- [walkthrough](file:///home/makaron8426/.gemini/antigravity/brain/a9054af6-3b54-4a08-8c0e-2d272cd546d2/walkthrough.md) 全過程記録
- Wang et al. (2023) PMC10110445 [SOURCE: 全文精読]
- Pickering & Garrod (2014) PMC4217443 [SOURCE: 全文精読]
