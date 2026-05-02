```typos
#prompt handoff-chronos-skill-migration
#syntax: v8
#depth: L2

<:role: Handoff — Chronos 族 SKILL v8.4 変換セッション :>
<:goal: 次セッションが Chronos 族の変換状態と残タスクを即座に把握する :>

<:context:
  - [knowledge] セッション: 2026-03-24 (約2時間)
  - [knowledge] 目的: Chronos 族 (V21-V24) の SKILL.md を v8.1 → v8.4 (Týpos) に全面変換
  - [knowledge] 結果: 全4動詞の変換 + /ele による批判 + 損失修復 を完了

  ## 完了した作業

  ### Chronos 族 v8.4 変換 (全完了)
  | 動詞 | 旧行数 | 新行数 | 派生数 | 固有アルゴリズム |
  |:-----|:-------|:-------|:-------|:----------------|
  | V21 /hyp | 890 | ~370 | 6 | Temporal Anchoring, Source Triangulation, Confabulation Detection(4分類), Confidence Decay(減衰テーブル), Temporal Bridge, MQS |
  | V22 /prm | 1255 | ~412 | 14 | Horizon Setting, Reference Class(Kahneman), Pre-Mortem(Klein), Cone of Uncertainty, Backcasting, FQS + 旧K1/K2統合7派生 |
  | V23 /ath | 947 | ~377 | 6 | Scope Bounding, Expected vs Emergent(4象限), Counterfactual(3+), If-Then Rule Extraction, Prosthesis Routing, Forgetful Functor(13種), Value Pitch(@rest), LQS |
  | V24 /par | 792 | ~360 | 7 | Threat & Opportunity Scan, Trigger Setting, Resource Pre-allocation + Cognitive Persistence, Contingency Matrix(防壁/代替/撤退), YAGNI Check, PpQS |

  ### /ele 批判で検出・修復した損失 (7件)
  1. ✅ V24 旧 Phase 名の復元 (Threat & Opportunity Scan / Trigger Setting / Resource Pre-allocation / Contingency Matrix / Synthesis / Preparedness Audit)
  2. ✅ V24 旧派生名の復元 (defend / exploit / contingency / monitor / temp)
  3. ✅ V24 認知的永続性 (Cognitive Persistence) の復元 + YAGNI チェックの復元
  4. ✅ V22 好機判定テーブル — highlights に既存 (追加不要)
  5. ✅ V23 Value Pitch (@rest 専用サブフェーズ Phase 2.5) の復元
  6. ✅ Anti-Skip Protocol — S-0 + constraints に分散統合済み (追加不要)
  7. ✅ FEP テーブル — description + highlights に統合済み (追加不要)

  ### 精査で検出・修復した不整合 (3件)
  1. ✅ V24 description L46 出力形式を修正後 Phase 名に更新
  2. ✅ V24 constraints L76 PQS → PpQS
  3. ✅ V21 description L43 メタファーに Phase 5=鑑定書の発行 追加

  ### 別セッションからの変更 (確認済み)
  - V09 Katalēpsis: Phase 1 名を Evidence Compilation → Evidence Evaluation に変更 (Creator 直接編集)

  ## SKILL 変換 全体進捗
  - [x] Methodos 族: V07 Peira, V08 Tekhnē
  - [x] Krisis 族: V09-V12 (V09/V11/V12 は既に v8.4, V10 は新規変換)
  - [x] **Chronos 族: V21-V24 (本セッション)**
  - [ ] Telos 族: V01-V04 (未着手)
  - [ ] Diástasis 族: V13-V16 (未着手)
  - [ ] Orexis 族: V17-V20 (未着手、V18 Elenchos は v8.4 済み)

  ## 次セッションへの提案
  1. Telos 族 (V01-V04) の変換 — 体系の中核 (noe/bou/zet/ene) で最重要
  2. 変換前に /noe, /zet の座標忠実性を確認 (別セッションで /noe の座標忠実性問題が検出されている)
  3. Diástasis 族 (V13-V16) → Orexis 族 (V17-V20) の順

  ## 教訓 (If-Then ルール)
  - [If] 4ファイル以上を連続変換する [Then] 各ファイル変換後に旧版のセクション見出しを git diff で照合し、損失がないか検証する
  - [If] 旧版の派生名を変更する [Then] 「なぜこの名前だったか」を旧版で確認してから変更を判断する
  - [If] 旧版に固有の Phase 名がある [Then] 認知アルゴリズム名としての固有性を尊重し安易に一般化しない

  ## 変更ファイル一覧
  - [modified] 10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills/V21_想起｜Hypomnesis/SKILL.md
  - [modified] 10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills/V22_予見｜Prometheia/SKILL.md
  - [modified] 10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills/V23_省察｜Anatheoresis/SKILL.md
  - [modified] 10_知性｜Nous/02_手順｜Procedures/C_技能｜Skills/V24_先制｜Proparaskeue/SKILL.md
/context:>
```
