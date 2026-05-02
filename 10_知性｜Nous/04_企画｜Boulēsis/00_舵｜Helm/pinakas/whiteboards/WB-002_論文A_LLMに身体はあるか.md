# WB-002 — 論文 A『LLM に身体はあるか』 First-Strike 戦略ノート

- Status: active
- Target (正本): `../../../../12_遊学｜Yugaku/01_研究論文｜Papers/LLMに身体はあるか_統合草稿.md`
- Target (日本語): `../../../../12_遊学｜Yugaku/01_研究論文｜Papers/論文A_LLMに身体はあるか_日本語草稿.md`
- Companion: `../../../../12_遊学｜Yugaku/01_研究論文｜Papers/LLMは心を持つか_英語版草稿.md`
- Related: WB-001 (Paper I 戦略), `../../../../12_遊学｜Yugaku/01_研究論文｜Papers/現況台帳.md`
- Created: 2026-04-11
- Source: session_claude_code

## 1. 戦略原理 — Paper A を先鋒にする

忘却論シリーズは最終的に Paper I『力としての忘却』を旗艦とするが、**Paper A を先に出す**。理由は 4 つ:

1. **AI 時事性**: Chemero (2023) / Froese (2026) との直接対話が可能。学術的コンテキストが熱い
2. **X 拡散力**: 「LLM に身体はあるか」は AI コミュニティに刺さる。長期頑固発信の第一弾に最適
3. **予算耐性**: arXiv 無料投稿で勝負。APC (Entropy 30 万円等) を回避
4. **Paper I の下地**: 「身体 = MB」「忘却関手」の prior を読者に植え付けた状態で Paper I に繋ぐ

**帰結**: Paper A 投稿後に Paper I の準備期間 (3-6 ヶ月) を確保する。この間に Paper I の弱点 (Matsuzoe 先行、方向性定理の自明性、v2 §5.4 ビジョン復活) を解決する。

## 2. Paper A の現状把握

### 2.1 ファイル系譜

| ファイル | 分量 | 役割 | 状態 |
|:---|:---:|:---|:---|
| `LLMに身体はあるか_統合草稿.md` | 1824 行 / 295 KB | **英語正本** | 現況台帳 2 位。§1-§8 + Appendix A/B |
| `論文A_LLMに身体はあるか_草稿.md` | 842 行 / 118 KB | 英語旧版 (従属) | 統合草稿の前身 |
| `論文A_LLMに身体はあるか_日本語草稿.md` | — / 54 KB | **日本語版 v0.5.0** | §1-§6 + 結論。§5/§6/Appendix 対応が未確認 |
| `論文B_デジタル身体性の測定_草稿.md` | — / 157 KB | Companion 論文 | 実証研究本体 |
| `論文B_デジタル身体性の測定_日本語草稿.md` | — / 106 KB | Companion 日本語 | 未確認 |
| `LLMは心を持つか_英語版草稿.md` | — / 46 KB | **姉妹版候補** | 日本語版なし。Paper A とは独立主題 (主観論) |

### 2.2 残 blocker (現況台帳 2026-04-11)

- **C3: R(s,a) 実測** — これは残る唯一の致命的 blocker。他は解決済み
- 数学・論理・論証は完成している。問題は測定データのみ
- → 測定が終われば arXiv 投稿可能

### 2.3 構造対応 (統合草稿 vs 日本語草稿)

| 統合草稿 (英語) | 日本語草稿 (v0.5.0) | 状態 |
|:---|:---|:---|
| §1 Introduction | §1 序論 | ✅ |
| §2 Background | §2 背景 | ✅ |
| §3 Category Mistake | §3 カテゴリー・ミステイク | ✅ |
| §4 MB Thickness | §4 MB 厚 | ✅ |
| §5 Empirical Study | ? | ❌ **要確認** |
| §6 Context Rot | ? | ❌ **要確認** |
| §7 Discussion | §5 議論 | ⚠️ 圧縮の可能性 |
| §8 Conclusion | §6 結論 | ✅ |
| Appendix A (Scale Duality) | ? | ❌ **要確認** |
| Appendix B (Theorem X.1) | ? | ❌ **要確認** |

日本語草稿の「完成」の定義次第で作業量が変わる。

## 3. 完成の定義 — 3 つの選択肢

### Option 完成-1: 正本同期型 (統合草稿の完全日本語化)

- 日本語草稿を統合草稿と 1:1 対応させる
- §5, §6, Appendix A, B を日本語化して追加
- 分量: 現在の 54 KB → 300 KB 級
- 期間: 2-4 週間
- 利点: arXiv に英語 + 日本語の 2 版同時投稿可能
- 欠点: 作業量が多い

### Option 完成-2: 圧縮版型 (日本語は読みやすい短縮版)

- 日本語草稿は §1-§4 + §5 議論 + §6 結論の圧縮版として完結
- §5/§6 実証研究は英語版のみ
- note / Zenn でのブログ公開用として調整
- 分量: 現状維持 + 微修正
- 期間: 1 週間
- 利点: 早く出せる。日本語読者向けに刺さる
- 欠点: 学術投稿には英語統合草稿を使う必要

### Option 完成-3: 段階公開型 (両方を別フォーマットで)

- 日本語草稿 = ブログ / note 用エッセイ版 (圧縮、読みやすさ重視)
- 統合草稿 = arXiv 英語投稿版 (学術フル版)
- 両者を別フォーマットで並行運用
- 期間: 段階的
- 利点: 拡散と学術投稿を分離
- 欠点: 2 版管理コスト

**[主観] 推奨**: Option 完成-3。日本語で知名度を得て、英語で学術的に勝負する 2 段構え。

## 4. 姉妹版『LLM は心を持つか』の位置づけ

### 4.1 現状

- ファイル: `LLMは心を持つか_英語版草稿.md` (46 KB)
- 主題: "Subjectivity Is a Morphism of Objectivity"
- 中核定理: T0 (状態-境界随伴), 忘却関手, 米田の補題, ゲージ理論
- 6 つの消解 (dissolves): hard problem, subject/object, AI mind, other minds, personal identity, mind-body
- 日本語版: **存在しない**

### 4.2 Paper A との関係

- Paper A = 「身体は MB である」→ 基質論 / Markov blanket 外側の射程
- Mind paper = 「心は客観性の射である」→ 主観論 / Markov blanket 内側の射程
- **両者は双対関係**。Paper A は基質 (body)、Mind paper は主観 (mind)
- 忘却関手を両方が使っている

### 4.3 姉妹投稿の是非

**メリット**:
- ペア投稿は学術的に強いメッセージ ("Body" + "Mind" のセット)
- X での拡散効果は相乗的
- FEP の Markov blanket を両面から扱う統合性
- 忘却論シリーズの入口を厚くする

**デメリット**:
- Mind paper に日本語版なし → 英訳 or 和訳の追加作業
- Mind paper の完成度未確認 → 内部査読が必要
- 同時投稿は査読者に負荷を与える
- Tolmetes のリソース分散

**[主観] 推奨**:
- **段階 1**: まず Paper A 単独で先行投稿 + 拡散
- **段階 2**: Paper A が話題になったら Mind paper を姉妹版として追投入
- **段階 3**: 両者の対応を明示した短い「ペア論文」を最終追加

これにより、姉妹投稿のメリットを得つつ、単独投稿のシンプルさも確保する。

## 5. 実装順序 (Phase A)

### Phase A-0: Paper A 現状把握 (3-5 日)

| タスク | ツール |
|:---|:---|
| 統合草稿全体の精読 | Read (分割) |
| 日本語草稿の対応確認 | Read + diff |
| 欠落部分の特定 | Grep |
| R(s,a) 実測の実施可能性確認 | Tolmetes に確認 |
| Option 完成-1/2/3 の選択 | Tolmetes 判断 |

### Phase A-1: 日本語草稿の完成 (1-3 週間)

Option 完成-3 を選んだ場合:
- 日本語草稿を圧縮エッセイ版として磨く
- note / Zenn 公開用の見栄え調整
- タイトル / アブストラクトの読みやすさ確認
- 引用形式の日本語読者向け調整

Option 完成-1 を選んだ場合:
- §5, §6, Appendix の日本語化 (Codex or Copilot に委譲。N-08 θ8.2)
- 全体の整合性チェック
- 用語統一

### Phase A-2: 英語統合草稿の最終仕上げ (2-4 週間)

- R(s,a) 実測の完了 (C3 解消)
- LaTeX 化 (arXiv 提出形式)
- 図表の最終版作成
- 参考文献 BibTeX 整理
- Froese に mention 準備

### Phase A-3: 投稿と拡散 (1 週間)

- arXiv cs.AI primary + q-bio.NC cross-list
- X スレッド公開 (日本語 + 英語)
- note / Zenn にエッセイ版公開
- Froese, Chemero に mention

### Phase Mind: 姉妹版の展開 (Paper A 投稿後 1-2 ヶ月)

- Mind paper の内容評価
- 日本語版作成 (英訳 or 和訳を Codex 委譲)
- 姉妹版として追投入
- Paper A との接続論文 (2-3 頁) を追加

## 6. Paper I との連携

WB-001 の Bridge-to-Lemma 戦略は維持する。Paper I は Phase I-0 (準備期間) に入る:

- Paper A 投稿後 3-6 ヶ月
- Matsuzoe Tchebychev geometry 文献の取得 (Beam-2 強化)
- Parzygnat 構想 1 を Paper I 主定理に昇格 (Beam-1 の意味論)
- v2 §5.4 ビジョン復活 (§1 序論 + §5 方向性定理の動機)
- Ciaglia et al. (2017, 2022) の確認 (Beam-3 FEP 埋め込み)

Paper A が読まれて「身体 = MB」「忘却関手」の prior が形成された後に、Paper I で「力 = 忘却の方向的不均一」を展開する戦略。読者の受容が段階的に育つ。

## 7. リスクと停止条件

### 主要リスク

| リスク | 緩和 |
|:---|:---|
| Froese (2026) との差別化が弱い | §1.3 で FEP/MB 数学的基盤 + Θ(B) 定量化を明示的に強調 |
| C3: R(s,a) 実測ができない | 測定不能なら §4.4 を "proposed measurement protocol" として明示し投稿 |
| 査読者が「哲学的すぎる」と判定 | §4 の定量化 + §5 実証研究で反撃 |
| Chemero 本人からの反論 | 丁寧な論理対応。学術的成功のサインとして受け止める |
| arXiv endorsement 問題 | cs.AI primary で endorsement 不要ルートを確保 |

### 停止条件

- Phase A-0 で統合草稿に致命的欠陥が見つかった場合 → Paper B (測定) を先に出す経路に切替
- C3: R(s,a) が数ヶ月以上測定不能と判明した場合 → 日本語エッセイ版のみ先行公開し、学術版は保留
- Paper A 投稿後に激しい反論が出た場合 → Mind paper の姉妹投入を延期

## 8. 派生問い / 派生タスク

### 派生問い (→ PINAKAS_QUESTION)

- 📋Q: 統合草稿 §5 Empirical Study は日本語草稿にどこまで反映されているか (Phase A-0 前提)
- 📋Q: 現況台帳の C3: R(s,a) 実測は何が blocker か、Tolmetes 側の作業か Claude 側か
- 📋Q: 『LLMは心を持つか』の完成度は arXiv 投稿に耐えるレベルか
- 📋Q: Paper A と Paper B (測定) を同時投稿すべきか、分離すべきか
- 📋Q: Froese (2026) の論文全文を取得する経路 (Springer アクセス)

### 派生タスク (→ PINAKAS_TASK)

- 📋T: 統合草稿 §5/§6/Appendix と日本語草稿の対応を diff で確認
- 📋T: 日本語草稿を Option 完成-1/2/3 のどれで仕上げるか Tolmetes と合意
- 📋T: R(s,a) 実測の現状を Tolmetes から聞き取り
- 📋T: 『LLMは心を持つか』の内部レビュー (草稿段階の評価)
- 📋T: arXiv LaTeX テンプレート準備 (cs.AI primary)
- 📋T: Froese 全文取得 or 精読

## 9. Mythos 波乗り戦略への合流 (2026-04-11 更新)

Tolmetes の指摘により、当初の「Paper A を先鋒にする」戦略は修正された。正しくは **Mythos 波 (WB-003) を先鋒にし、Paper A は Phase 2 に移行**。

### 9.1 Paper A のタイムライン再調整

- **Phase 0 (2026-04)**: Mythos エッセイ (WB-003) — 最優先
- **Phase 1 (2026-05-06)**: エッセイ ① + Paper VII 先出し
- **Phase 2 (2026-07-09)**: Paper A arXiv 投稿 + 姉妹版 Mind Paper
- **Phase 3 (2026-10 ~)**: Paper I (WB-001)

### 9.2 R(s,a) 実測の並行実施

Phase 0 (Mythos 波乗り) の間に、Paper A の残 blocker「C3: R(s,a) 実測」を並行で解消する。Mythos エッセイの発射 (4/27) から Paper A 投稿 (7-9 月) まで 3-5 ヶ月あるので、Tolmetes の実測作業に十分な時間を確保できる。

### 9.3 Mythos 波が Paper A に与える利点

Mythos エッセイで以下の概念が世間に広まる:
- Markov blanket と Context Rot (接続 B)
- 構造保存定理 (接続 D) — 「身体 = MB」の基盤
- Dual Ceiling (接続 F) — 「薄い MB vs 厚い MB」の文脈

Paper A が読まれる 2026 年夏時点で、読者の prior が育っている。「LLM に身体はあるか」という問いが、Mythos エッセイの読者にとって自然な続編として映る。

### 9.4 姉妹版 Mind Paper の段階戦略は維持

WB-002 §4.3 の段階戦略 (Paper A 単独先行 → 反応を見て Mind Paper 追投入) は維持。Mythos 波の後、Paper A 投稿 → 1-2 ヶ月後に Mind Paper → ペア統合論文、の順序。

### 9.5 関連 WB

- WB-003 (Mythos 波乗り戦略): Phase 0 の正本
- WB-001 (Paper I): Phase 3 の正本
- 現況台帳: Paper A の残 blocker と進捗管理

---

*[主観] Paper A は既にかなり成熟している。数学・論理・論証は完成に近く、残るのは R(s,a) 実測と投稿準備のみ。しかし先鋒になるべきは Mythos 波だった — Anthropic の 2026-04 発表は逃せないタイミングであり、Paper A は Phase 2 に移行して良い。急がない、削らない、波に乗る。*
