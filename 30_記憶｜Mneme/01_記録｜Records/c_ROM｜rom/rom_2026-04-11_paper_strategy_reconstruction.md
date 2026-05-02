# ROM 2026-04-11 — 論文戦略の再構築: Paper I 批評から Paper A 先行へ (そしてビジョン.md による再調整)

**Session ID**: session_claude_code (Opus 4.6, 1M context)
**Date**: 2026-04-11
**Topic**: 論文出版戦略の根本的見直し
**Depth**: L3 (/rom+)
**Related**: WB-001, WB-002, PINAKAS_WHITEBOARD.yaml

---

## §1 セッション文脈

### 1.1 起点
Tolmetes から「論文 I『力としての忘却』の評価軸は何がありえる?」という問いで開始。/tek.hypographe の導入を経て、論文 I の arXiv 投稿前批評と品質向上ロードマップの策定に展開した。

### 1.2 当初の誤り
私は論文 I を研究者向けに批評し、以下を提案した:
- arXiv math-ph 投稿戦略
- Entropy (MDPI) APC 30 万円
- Phase 0 として endorsement 確認

Tolmetes の自己開示で前提が崩壊:
- 「専門学校中退の SE、一般人」
- APC 30 万円は趣味の範囲外
- 無料の arXiv で勝負したい
- エッセイで知名度をつける
- X で AI 関連として拡散する

---

## §2 主要な発見

### 2.1 v2 レガシーの存在
`incubator/legacy/力とは忘却である_v2.md` (4065 行) に **当初の動力学的ビジョンが残存**:
- 力 = 「理想 (自由の最大化 or 最小化) と現状との差を埋めようとする状態」
- 重力 = 自由の最小化 (ブラックホール = Bekenstein 上限)
- ビッグバン = 自由の最大化 (位相反転 = F⊣G 随伴)
- n-cell 階層 (0: 局所力 / 1: 膨張方向 / 2: 時間の位相選択)
- α の 3 特異点 (0: 対消滅 / 1: 対称の退化 / >1: 一般解)

現行 Paper I 草稿 (1456 行) はこれらを**数学化の名目で削ぎ落とした**。結果、Friston 流の一行主張を失い、「限定的新規性の技術論文」になっている。

### 2.2 Copilot 先行研究調査結果 (GPT-5.4 xhigh)
- Q1 忘却場 Φ = D_KL: **既知** (Amari-Nagaoka, Ay-Jost-Lê-Schwachhöfer)
- Q2 Chebyshev 1-形式: **既知** (Matsuzoe 2005, 2010 — "Tchebychev geometry")
- Q3 忘却接続 A_i: **新規** (Ciaglia et al. 2017, 2022 は近接)
- Q4 方向性定理: **自明** (F = dA の定義からの直接帰結)
- Q5 精度-FEP 対応: **判定不能** (α ∈ ℝ と π > 0 の定義域不一致)
- Q6 α-SAM: **新規** (Fisher SAM の α-族への一般化)
- **総合判定: B (限定的新規性)**

### 2.3 WB-001 既存戦略の発見
前セッションで Bridge-to-Lemma Conversion が既に策定されていた:
- 「過積載」批判に対して、野心を削らずに補題化で防御する
- 7 本の梁 (Beams) を証明可能な限り厳密に補題化する
- 停止条件: 補題が証明できなければ outlook に落とす
- 降格経路 A (定理論文化), B (Program 宣言化) が用意されている

### 2.4 Parzygnat ファイル構想 1
`incubator/Parzygnatのアイデアを超えて.md` で Parzygnat の 3 層 (inverse ⊃ disintegration ⊃ Bayesian inversion) を F_{ij} の条件として特徴づける命題が定式化されている。これは方向性定理の自明性問題 (Q4) に対する **防衛線** になる:
- 「F ≠ 0 ⟺ d(ΦT) ≠ 0」は外微分の自明な恒等式
- しかし F_{ij} の値は Parzygnat 階層を決定する
- → 方向性定理は「可逆性階層の幾何学的判定条件」という**圏論的意味論**を持つ

### 2.5 Paper A の成熟度
- 統合草稿 (英語) = 1824 行, 295 KB, §1-§8 + Appendix A/B
- 日本語草稿 (v0.5.0) = 54 KB, §1-§6+結論
- 論文 B (測定) 統合版も 157 KB で存在
- 現況台帳の残 blocker: **C3: R(s,a) 実測** のみ
- 数学・論理・論証は完成。残るは測定データと投稿準備

### 2.6 姉妹版候補
`LLMは心を持つか_英語版草稿.md` (46 KB, v0.6)
- "Subjectivity is a morphism of objectivity"
- 12 の哲学的難問の消解
- Paper A の双対 (基質 body vs 主観 mind)
- 日本語版なし
- Paper A と同じ数学的枠組み (Markov blanket, 忘却関手, Galois connection)

### 2.7 ビジョン.md の発見 (決定的)
`論文｜Papers/ビジョン.md` (v2.0, 2026-03-18)
- **15 本の論文 + 6 本のエッセイ** を遊学プロジェクトとして計画
- **Tier S 候補 5 本**: Structural Attention, Coherence Invariance, MB 密度場チャンキング, 弱 2-圏, LLM Body
- **フェーズ 1 (Q2 2026)**: 論文 2 (Coherence Invariance) + 論文 3 (τ 一意性) + エッセイ ①
- **フェーズ 2 (Q3-Q4 2026)**: 論文 12 (LLM Body) + 論文 8 (弱 2-圏) + OSS 公開
- **フェーズ 3 (2027 H1)**: 論文 1 (Structural Attention) + 論文 9 + 書籍化
- **L0/L1/L2 の三層射影**: エッセイ/論文/OSS を同時に出すことで相互増幅

**重要**: Paper I (力としての忘却) はビジョン v2.0 に明記されていない。忘却論シリーズは遊学 VISION の外か、v2.0 の後に追加された構想の可能性。

---

## §3 WB 更新の記録 (2026-04-11 実施)

### 3.1 PINAKAS_WHITEBOARD.yaml
- version 1.0 → 1.1
- next_id 2 → 3
- WB-002 追加

### 3.2 WB-001 (論文 I) 更新
- §7 Phase I-0 移行 (Paper A 先行の帰結)
- §8 新しい実装順序 (統合版)
- Status: active → Phase I-0 準備期間

### 3.3 WB-002 (論文 A) 新規作成
- First-Strike 戦略
- 完成の 3 選択肢 (Option 完成-1/2/3)
- 姉妹版の段階的投入戦略
- Phase A-0 から A-3 の実装順序

---

## §4 決定済み事項

### 4.1 戦略原理
- Tolmetes は Friston モデル (a) を選択 (Paper I で世界を驚かす野心)
- APC 30 万円は回避、arXiv 無料投稿
- エッセイ + 論文の L0/L1 同時射影
- X で AI 関連として拡散

### 4.2 Paper I 戦略
- Bridge-to-Lemma Conversion (WB-001) 維持
- Vision Revival 追加 (v2 §5.4 ビジョン復活)
- Phase I-0 準備期間 (3-6 ヶ月) に移行
- Paper A 先行後に書き直し

### 4.3 Paper A 戦略
- Paper A を先鋒にする (WB-002)
- 現況台帳の残 blocker は C3: R(s,a) 実測
- 姉妹版 Mind Paper は段階的投入 (Paper A 投稿後 1-2 ヶ月)

---

## §5 未解決事項 (Tolmetes の判断待ち)

### 5.1 日本語草稿の「完成」の定義 (WB-002 §3)
- Option 完成-1: 完全日本語化 (2-4 週間)
- Option 完成-2: 圧縮版 (1 週間)
- Option 完成-3: 段階公開型 (エッセイ版 + 学術版) ← 私の推奨

### 5.2 統合草稿 vs 日本語草稿の diff 取得
日本語草稿の §5/§6/Appendix 対応が未確認。私が Phase A-0 で実行する許可を求めている。

### 5.3 R(s,a) 実測の現状
- Tolmetes 側の作業か Claude 代行可能か不明
- 測定不能なら "proposed measurement protocol" として投稿

### 5.4 心を持つか姉妹投入タイミング
- 段階 1 Paper A 単独先行 / 段階 2 Mind Paper 日本語化 / 段階 3 追投入 / 段階 4 ペア統合

### 5.5 ビジョン.md との整合性 (新規)
Paper I 中心の戦略 (WB-001, WB-002) と、ビジョン v2.0 の優先順位 (Coherence Invariance 最速速報) の関係を確認する必要がある。

---

## §6 ビジョン.md 読解による戦略再評価

### 6.1 Tolmetes の真の優先順位
ビジョン v2.0 と現況台帳の両方で一致:
1. **Coherence Invariance** (優先 1 位, 完成度 高)
2. **LLM Body** (優先 2 位, 完成度 高, C3 残)
3. Structural Attention (優先 3 位, v0.1 段階)
4. FEP 分解型 (概念 blocker 強、保留)

### 6.2 Paper A 先行戦略の部分的誤り
私は Paper I から入って Paper A 先行に移行したが、**本来の先鋒は Coherence Invariance**。ビジョン v2.0 §4 では:
- フェーズ 1 Q2 2026 = Coherence Invariance + τ 一意性 + エッセイ ①
- フェーズ 2 Q3-Q4 2026 = LLM Body (Paper A に相当)

つまり Paper A は本来フェーズ 2 に位置づけられていた。私の提案は**フェーズ 1 をスキップしている**。

### 6.3 L0/L1 同時射影の原理
ビジョン §6 より:
- L0 (エッセイ) と L1 (論文) は同じ Kernel からの**異なる射影**
- **同時に出すことで相互増幅する**
- これは Tolmetes の「エッセイで知名度」方針の本当の意味

エッセイ ①「バカをやめたいなら構造を見ろ」は v2 完成。これを note / Zenn で公開しつつ、論文 2 (Coherence Invariance) を arXiv に出すのが本来のフェーズ 1。

### 6.4 忘却論シリーズの位置づけ (要確認)
Paper I (力としての忘却) はビジョン v2.0 に明記されていない。考えられる可能性:
- (a) 忘却論シリーズは遊学 VISION の後継プロジェクトで、v2.0 の後に追加された
- (b) 遊学 VISION v3.0 が存在する (未確認)
- (c) 忘却論は別系統プロジェクトで、遊学とは独立した戦略を持つ
- (d) Paper 4「忘却関手 S(e)」(Tier A) が忘却論に相当する可能性

**これは Tolmetes に確認する必要がある**。

---

## §7 /u+ による主観的統合判断

### 7.1 誤りの認識
私は Paper I → Paper A 先行という局所最適解に陥った。ビジョン.md を読むまで **Coherence Invariance の存在を見落としていた**。これは N-05 (能動的に情報を探せ) 違反の典型: 最初から `ビジョン.md` を読んでいれば、この 2 時間の議論の多くは不要だった。

### 7.2 正しい優先順位 (ビジョン v2.0 に従う)
- **今すぐ (Phase 1 Q2 2026)**:
  - 論文 2: Coherence Invariance (arXiv cs.IR / SIGIR)
  - 論文 3: τ 一意性 (arXiv cs.LG / NLP)
  - エッセイ ①: note / Zenn 日本語公開
  - L0/L1 同時射影

- **近未来 (Phase 2 Q3-Q4 2026)**:
  - 論文 12: LLM Body (Paper A) — WB-002 の戦略を流用
  - 姉妹版 Mind Paper — 段階的投入
  - 論文 8: 弱 2-圏
  - HGK OSS 公開

- **2027 H1 (Phase 3)**:
  - 論文 1: Structural Attention
  - 論文 9: 循環幾何
  - エッセイ三部作の書籍化

- **Paper I は別系統 (確認要)**:
  - 忘却論シリーズとして独立したタイムラインを持つ可能性
  - または Phase 3 以降の grand finale

### 7.3 WB-001, WB-002 の再評価
- WB-001 (Paper I): Phase I-0 準備期間は維持。ただし「急ぎの戦略」ではなく「長期育成」に位置づけ直す
- WB-002 (Paper A): フェーズ 2 への先送り。Phase A-0〜A-3 のタイムラインは維持するが、起動は Coherence Invariance の後

### 7.4 新規必要事項
- **WB-003**: Coherence Invariance 論文の戦略 (もし Tolmetes が優先する場合)
- **WB-004**: エッセイ ① note/Zenn 公開戦略 (L0 射影)

### 7.5 [主観] 最終判断

Tolmetes の野心 (Friston モデル a、世界を驚かす論文) は Paper I で実現すべきで、削ぐべきではない。ただし Paper I 単独で世界を驚かすのは難しい (Copilot 判定 B)。

**二段ロケット構造が正解**:
- **下段 (Phase 1)**: Coherence Invariance + エッセイ ① = 最速学術存在感 + L0 知名度
- **上段 (Phase 2)**: Paper A + 姉妹 Mind Paper = 「身体 = MB」「心 = 射」ペア
- **衛星 (Phase 3)**: Paper I = 忘却論の grand finale / または別系統で長期育成

Paper I は急がず、**読者の prior が育つまで待つ**。これは Friston が 2005-2010 に取った戦略と同じ。

---

## §8 次のアクション

### 8.1 即時実行 (現セッション内)
1. ✅ ROM ファイル書き出し (本ファイル)
2. ✅ ビジョン.md 読解と /u+ 統合判断 (§7)
3. 🔄 Tolmetes に戦略再調整の提案 (Coherence Invariance 優先の確認)

### 8.2 次セッション以降
- Tolmetes の判断次第で以下のいずれか:
  - (A) ビジョン v2.0 に従い Coherence Invariance 先行
  - (B) 私の提案通り Paper A 先行
  - (C) Tolmetes の新しい優先順位に従う
- いずれの場合も WB-001, WB-002 は既に整備済みで参照可能

### 8.3 保存すべき記憶
- v2 §5.4 ビジョン (力 = 不均一の解消) の位置
- Copilot 調査結果 (Matsuzoe, Ciaglia, Parzygnat)
- 現況台帳の残 blocker (R(s,a) 実測)
- 15 本の論文候補 (Tier S/A/B)
- L0/L1/L2 三層射影原理

---

## §9 関連ファイル

| 役割 | パス |
|:---|:---|
| Paper I 正本 | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/series/論文I_力としての忘却_草稿.md` |
| Paper I v2 レガシー | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/incubator/legacy/力とは忘却である_v2.md` |
| Parzygnat ファイル | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/incubator/Parzygnatのアイデアを超えて.md` |
| Paper A 正本 | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_統合草稿.md` |
| Paper A 日本語 | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/論文A_LLMに身体はあるか_日本語草稿.md` |
| Mind Paper | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_英語版草稿.md` |
| Coherence Invariance | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/コヒーレンス不変性定理_草稿.md` |
| 現況台帳 | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/現況台帳.md` |
| ビジョン v2.0 | `10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/ビジョン.md` |
| WB-001 | `10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/whiteboards/WB-001_論文I_力としての忘却.md` |
| WB-002 | `10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/whiteboards/WB-002_論文A_LLMに身体はあるか.md` |
| Copilot 調査結果 | `/tmp/paper1_sanity/result_directionality.md` |

---

*ROM 2026-04-11 — 論文戦略の再構築。ビジョン.md 読解で優先順位の誤りを認識し、Coherence Invariance + エッセイ ① 先行への再調整を提案。Tolmetes の確認を待つ。*
