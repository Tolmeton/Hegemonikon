---
rom_id: rom_2026-02-22_skill_md_expansion_p1_p3
session_id: dfa4c855-dc9b-4a51-8cf3-978c1ce9d78f
created_at: 2026-02-22 14:40
rom_type: distilled
reliability: High
topics: [skill_md, cognitive_algebra, falsification, epoche, peira, katalepsis]
exec_summary: |
  P1およびP3の計11件のSKILL.mdファイルを800行基準まで拡張。
  Cognitive Algebra、Anti-Patterns、およびFEP連携セクションを追加・構造化し、
  各定理の役割を明確に定義した。
---

# SKILL.md 拡張完了報告 (P1/P3 バッチ) {#sec_01_topic}

> **[DECISION]** SKILL.md ファイルの標準的な深さを担保するため、800行を基準とする拡張方針を決定した。P1 (7件) および P3 (4件) の合計11ファイルがこの基準を達成した。

拡張手法として、以下の共通セクションを導入した：

1. **Cognitive Algebra**: `+`, `-`, `*` 派生の意味と `sel_enforcement` (最低要件) を定義。
2. **Anti-Patterns**: その定理固有の陥りやすい罠と対策。
3. **差分テンプレート**: 前後のワークフローへの引き継ぎフォーマット。
4. **FEP 連携**: Active Inference エージェントにおける役割の明確化。

> **[DISCOVERY]** V09 Katalēpsis は単なる確信ではなく、「無慈悲な反証 (Falsification Probe)」を生き延びた仮説にのみ与えられるべきものである。確証バイアスに対する構造的防壁としての役割が明確になった。

> **[DISCOVERY]** V10 Epochē は単なる「わからない」という状態ではなく、FEP における「確率分布の保持」（argmaxを取らない）という能動的かつ認知的負荷の高い状態であることが定義された。

> **[DISCOVERY]** V07 Peira は「証明」ではなく「学習」のための実験である。MVP Design においては EIG (Expected Information Gain) が最大化されるよう設計し、得られた結果を Surprise (予測誤差) として定量化する構造が整理された。

> **[CONTEXT]** このセッションでは、P1バッチ（O3, V22, V24, V23, V21, V19, V20）および P3バッチ（V08, V09, V07, V10）の拡張を完了した。残りの P2バッチ（11件）は今後のセッションで扱う。

## 関連情報

- 関連 WF: `/mek`, `/kat`, `/epo`, `/pei`
- 関連 Session: `dfa4c855-dc9b-4a51-8cf3-978c1ce9d78f`
- 更新先ディレクトリ: `hegemonikon/.agent/skills/`

<!-- ROM_GUIDE
primary_use: 今後の P2 バッチ拡張時の参照モデル、および各定理の深い理解のためのベースドキュメント。
retrieval_keywords: skill.md, 800行, cognitive_algebra, anti-patterns, V09, V10, V07
expiry: permanent
-->

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "SKILL.md 拡張の基準は何か？"
  - "新しく追加されたセクションは何か？"
  - "Katalepsis や Epoche の本質的な意味は何か？"
answer_strategy: " Cognitive Algebra や Anti-Patterns などの追加セクション構造を説明し、Katalepsis(反証)、Epoche(分布保持)、Peira(予測誤差)というFEP的解釈を強調する。"
confidence_notes: "このROMはシステム設計の確定事項として高い信頼度で参照可能。"
related_roms: []
-->
