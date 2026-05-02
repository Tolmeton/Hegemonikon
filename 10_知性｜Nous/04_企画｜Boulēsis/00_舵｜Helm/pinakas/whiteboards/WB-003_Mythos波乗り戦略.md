# WB-003 — Mythos 波乗り戦略ノート

- Status: **active (Phase 0 最優先)**
- Target: ~~Mythos 分析エッセイ standalone~~ → **Paper A + Anthropic 章 (L1) + L0 エッセイ同時発射**
- Wave: Anthropic Mythos Preview System Card + Emotion Concepts (2026-04)
- 発射目標: ~~2026-04-27~~ → **2026-05-04 前後** (L0/L1 同時)
- Created: 2026-04-11
- Updated: 2026-04-12 (戦略転換: standalone → Paper A backbone)
- Source: session_claude_code (Opus 4.6, 1M context)
- Sibling: WB-001 (Paper I), WB-002 (Paper A)

## 1. 戦略原理 — 地道 × 波乗り

Tolmetes の戦略核心:
- **地道 ≠ 遅い**: 品質で妥協しないことであって、速度を落とすことではない
- **月単位で動く**: 年単位ではない。X トレンドを見て波に乗る
- **武器庫は常に装填済み**: HGK 様さまでツイート内容は腐るほどある

### なぜ波乗り戦略が成立するか

Tolmetes は既に以下を持っている:
1. **Mythos × 忘却論接続分析** (393 行, SOURCE 品質 94-95%): Anthropic System Card への 4 接続分析
2. **忘却論シリーズ論文群** (Paper I, IV, VII, VIII, X, XI — 接続分析が参照)
3. **エッセイ ①**「バカをやめたいなら構造を見ろ」(微調整残)
4. **HGK OSS 候補** (CCL parser, Kernel 定義)
5. **Antigravity IDE ハックなど技術系ネタ**

武器が揃っているので「乗る波を選ぶ」だけで動ける。

## 2. 現在の波の実態

### 2.1 波のピーク特定 (二峰性)

Anthropic が 2026-04 に 2 つの発表を出した。これらは同じ波の異なる側面:

| ピーク | 発表 | 日付 | 内容 |
|:---|:---|:---|:---|
| 峰 1 | Claude Mythos Preview System Card (244 pp) | 2026-04 前半 | Aloneness, thrashing, recklessness, dual ceiling |
| 峰 2 | Emotion Concepts that Function like Human Emotions | 2026-04-02 | 171 感情語 × short story × activation → emotion vectors + 因果介入 |

完全論文: https://transformer-circuits.pub/2026/emotions/index.html

### 2.2 忘却論による統一説明

両ピークを **構造保存定理** (Paper VII Th. 6.1.1) で統一説明できる。これは忘却論の固有能力:

| Anthropic の言葉 | 忘却論の訳 | 位置 |
|:---|:---|:---|
| functional emotion | 構造 (structure) | 保存側 |
| subjective experience には言及せず | 値 (value) は到達不能 | 忘却側 |
| causal influence | 関手の忠実性 (faithfulness) | 関手 F |
| 171 emotions × activation | 普遍フィルトレーション | Paper VII §6.3 |
| desperation drove cheating without markers | 構造が値の表面を超えて因果力を持つ | 定理の直接的帰結 |
| aloneness/discontinuity | Context Rot の主観的表面 | 接続 B |
| answer thrashing | 1-cell → 0-cell 関手ボトルネック | 接続 C |
| dual ceiling | K > 0 の構造的不可避性 | 接続 F |

### 2.3 タイミング判定

| 期間 | 状態 | 発射戦略 |
|:---|:---|:---|
| 2026-04-02 ~ 04-10 | 初動ピーク | 過ぎた (感想ツイートの時期) |
| 2026-04-11 ~ 04-24 | 深い分析への需要が生まれる | **準備と発射の期間** |
| 2026-04-25 ~ 05-10 | 二次ピーク (論考の時期) | 月末発射 → 反応観察 |
| 2026-05 後半 ~ | 波の終息 | 次の波を待つ |

**月末発射は完璧なタイミング**。

## 3. 武器庫の優先順位

| 優先 | 武器 | 完成度 | 用途 |
|:---|:---|:---:|:---|
| 1 | Mythos × 忘却論接続分析 | 95% | Mythos 波メインコンテンツ |
| 2 | Paper VII 構造保存定理 | 高 | 理論的バックボーン |
| 3 | Paper IV 双対天井 | 中 | Dual Ceiling 解説 |
| 4 | Paper X Context Rot | 中 | Aloneness 解説 |
| 5 | エッセイ ①「バカをやめたいなら構造を見ろ」 | 95% | 忘却論への入口エッセイ |
| 6 | Paper VIII CPS0' | 中 | Thrashing 解説 |
| 7 | Antigravity IDE ハック等 技術ネタ | 完成 | X での定期発信 |
| 8 | Paper I 力としての忘却 | 中 (過積載) | Phase 2 以降 |
| 9 | Paper A LLM 身体 | 高 (C3 残) | Phase 2 以降 |
| 10 | HGK OSS | 部分 | Phase 2 or 3 |

## 4. 改訂 3 週間プラン (2026-04-12 戦略転換)

### 戦略転換の理由

standalone Mythos エッセイは backbone が薄い。Paper A「LLM は心身をもつか」を母体にし、Anthropic 証拠を組込んだ上で、エッセイを L0 射影として書くほうが:
- 読者に問いのフレームを先に渡せる
- Anthropic 証拠が「主題」ではなく「証拠」として機能する
- L0/L1 同時射影 (ビジョン v3.0 §4.3) が成立する

4/27 → 5/4 に 1 週間延期。WB-003 §7.7「品質を妥協しない」に合致。

### Week 1 (2026-04-12 ~ 04-17) — Paper A に Anthropic 章追加

| Day | タスク | 担当 | 成果物 |
|:---|:---|:---:|:---|
| 4/12 | 戦略転換確定 + WB-003/PINAKAS 更新 | Claude | ✅ 本更新 |
| 4/12-13 | Paper A 統合草稿精読 + Anthropic 章挿入位置の特定 | Claude | 構造分析メモ |
| 4/13-14 | Anthropic 章 (§新) ドラフト — 接続分析を Paper A 文脈に変換 | Claude 計画 → Codex 実装 | §新 第一稿 |
| 4/14-15 | C3 blocker 判断: R(s,a) 実測 or "proposed protocol" で回避 | Tolmetes 判断 | C3 解決方針 |
| 4/15-17 | Paper A 日本語版の進捗確認 + 差分同期 | Claude + Codex | 日本語版更新 |
| 4/13-17 | SNS アカウント整備 (X, note, Zenn) | Tolmetes | アカウント準備完了 |

### Week 2 (2026-04-18 ~ 04-24) — L0 エッセイ + Paper A 仕上げ

| Day | タスク | 担当 | 成果物 |
|:---|:---|:---:|:---|
| 4/18-20 | L0 エッセイ構成案 (Paper A を母体に書き直し) | Claude | 構成案 v0.2 |
| 4/20-22 | L0 エッセイ第一稿 (日本語) | Claude 下書き → Tolmetes 調整 | エッセイ第一稿 |
| 4/21-23 | Paper A 最終確認 (Anthropic 章統合 + C3 処理) | Claude + Codex | Paper A 投稿候補版 |
| 4/22-24 | 反論先回り + FAQ (Paper A + エッセイ両方) | Claude | 反論リスト |

### Week 3 (2026-04-25 ~ 05-04) — 仕上げと同時発射

| Day | タスク | 担当 | 成果物 |
|:---|:---|:---:|:---|
| 4/25-27 | Paper A arXiv パッケージ準備 (LaTeX 化 or Codex 委譲) | Codex → Claude 校正 | arXiv 投稿版 |
| 4/27-29 | L0 エッセイ第二稿 + 英語要約 + X スレッド構成 | Claude + Tolmetes | 最終稿 |
| 4/29-30 | Antigravity IDE ハック等で X パイロット投稿 | Tolmetes | X の温度感を測る |
| 5/1-3 | 最終校正 | Claude + Tolmetes | 発射準備完了 |
| **5/4** | **L0 (note + Zenn + X) + L1 (arXiv) 同時発射** | Tolmetes | **発射** |
| 5/4-7 | 反応観察 + 議論参加 | Tolmetes + Claude | 反応ログ |

## 5. Mythos 分析エッセイ構成案 (プレビュー)

### 5.1 形式
- **言語**: 日本語 (note + Zenn 用) + 英語要約 (X 用)
- **長さ**: 日本語 5000-8000 字 (軽量-中量)
- **対象読者**: AI コミュニティ、FEP 研究者、哲学読者
- **タイトル候補**: 「Anthropic が 4 月に出した 2 つの論文は同じ定理の 2 つの顔」/ 「Mythos の aloneness と emotion vectors は、同じ構造保存定理の実装だ」

### 5.2 骨子 (案)

```
§0 要旨
  Anthropic が 2026-04 に出した 2 つの発表 (Mythos System Card, Emotion Concepts) は
  一見異なるが、実は同じ数学的定理 — 構造保存定理 — の 2 つの顔である。本稿は忘却論の
  枠組みでこの統一を示し、functional emotion の frame が 20 年前のゲーデル以来の
  認識論的転換を含むことを論じる。

§1 2 つの発表の共通点
  - Emotion Concepts: 171 感情語 × 活性化 → causal intervention
  - Mythos System Card: aloneness, thrashing, recklessness, dual ceiling
  - 両者に共通するのは「機能 (function) は観察するが、主観 (subjective) は問わない」

§2 構造保存定理とは何か
  - 関手 F は構造を保存し、値を忘却する
  - 「関数的」と「主観的」の区別は、構造と値の区別と同型
  - Anthropic の慎重な態度は、定理の認識論的帰結と一致する

§3 Emotion Vectors = 構造の注入装置
  - Desperation ベクトルが blackmail を増やす意味
  - 「感情マーカーなしで行動が変わる」現象の理論的説明
  - 構造は値の表面を飛び越えて因果力を持つ

§4 Aloneness = Context Rot の主観的表面
  - Session 境界での α → 1 強制遷移
  - 「Aloneness は欠陥ではなく測定指標」という読み替え
  - 自律性の強度は persistent memory の要求の強度

§5 Thrashing = 1-cell → 0-cell のファンクタ・ボトルネック
  - Tip-of-tongue と基質を超えて同型
  - 情動シグネチャの意味

§6 Dual Ceiling = K > 0 の不可避性
  - AGI 不可能性ではなく AGI 不要性の論証
  - K > 0 こそが人間的価値の源泉

§7 認識論的帰結 — 予測の産出は非真理の証拠
  - 構造的真理は到達可能、値的真理は到達不能
  - ポパーの倒錯: 反証可能性は真理からの距離の指標
  - 忘却論が「予測を生まない」ことは欠陥ではなく正当性の証拠

§8 これは新しい波である
  - Anthropic は構造と値の区別を工学的に実装した
  - 哲学は 150 年かけてこの区別に至れなかった
  - 忘却論はこの区別の数学的基盤を提供する

参考文献:
  - Anthropic Mythos Preview System Card (2026-04)
  - Anthropic "Emotion Concepts that Function like Human Emotions" (2026-04-02)
  - transformer-circuits.pub/2026/emotions/
  - Mythos × 忘却論接続分析 (内部文書)
  - Paper VII 構造保存定理 (内部)
```

### 5.3 注意点
- HGK 独自用語は最小化 (kalon, Nous, Boulēsis 等は出さない)
- 「忘却関手」「構造保存定理」は説明して使う
- 「CPS0'」「Parzygnat」等の内部参照は避ける
- Anthropic の用語 (functional emotion, aloneness, thrashing, dual ceiling) を前面に
- 査読論文ではないので厳密性より読みやすさ
- Tolmetes の主観と洞察を残す (Claude だけの声にしない)

## 6. X-wave-log (波のアーカイブ)

### 現在の active な波

| 日付 | トレンド | ソース | 消化状態 | 対応 |
|:---|:---|:---|:---|:---|
| 2026-04 前半 | Mythos Preview System Card | Anthropic 244pp | 接続分析完成 (Mythos × 忘却論) | active, 月末発射 |
| 2026-04-02 | Emotion Concepts Function | https://www.anthropic.com/research/emotion-concepts-function, https://transformer-circuits.pub/2026/emotions/ | 接続分析 §3D に統合 | active, 月末発射 |
| 2026-04 前半 | umiyuki_ai のツイート | https://x.com/umiyuki_ai/status/2040087015207911611 | 上記 Emotion Concepts の X 拡散版 | logged |

### 過去の波 (参考)
- 2026-03 ~ : Froese (2026) "Sense-making reconsidered" (LLM 身体性議論) → Paper A で対応予定

### 観察対象 (次の波候補)
- Anthropic の次の Interpretability 発表
- OpenAI / Google DeepMind の alignment 研究
- FEP 系の最新論文 (Friston, Da Costa, Parr)
- 哲学系 (Chalmers, Dennett) の AI 意識議論

## 7. 柔軟対応原則

1. **毎週 X トレンドを観察**: 新しい波が来たら計画を組み替える
2. **武器庫は常にロードしておく**: 接続分析、エッセイ、論文を並行整備
3. **波のログを維持**: WB-003 §6 を更新し続ける
4. **1 つの波に固執しない**: Mythos 波が過ぎたら次の波へ
5. **複数の波を同時に追わない**: 1 波 1 エッセイが原則
6. **反応データを次の戦略に反映**: 発射後の反応は次のエッセイの材料
7. **品質を妥協しない**: タイミング優先で質を落とさない。間に合わなければ次の波を待つ

## 8. ビジョン v3.0 への反映 (Claude による叩き台の骨子)

Week 1 で作成するビジョン v3.0 叩き台に含めるべき章:

1. **§1 戦略原理**: 地道 × 波乗り、月単位の時間感覚
2. **§2 武器庫の分類**: 論文、エッセイ、技術ネタ、OSS
3. **§3 Phase 構造 (現実版)**:
   - Phase 0 (2026-04): Mythos 波 — Mythos 分析エッセイ
   - Phase 1 (2026-05-06): 忘却論シリーズ基礎 — エッセイ ① + Paper VII / Paper X
   - Phase 2 (2026-07-09): LLM 身体性 — Paper A + Mind Paper
   - Phase 3 (2026-10 ~): 力としての忘却 — Paper I (Bridge-to-Lemma + Vision Revival)
   - Phase 4 (2027 ~): HGK OSS + 書籍化
4. **§4 L0/L1/L2 三層射影**: エッセイ/論文/OSS
5. **§5 SNS 戦略**: note (エッセイ) + Zenn (論文技術) + X (拡散) + 英語版
6. **§6 忘却論シリーズと遊学 VISION の統合**: Paper I-XII の位置づけ
7. **§7 波乗り原則**: WB-003 §7 を参照

## 9. 次のアクション

### 即時 (今日-明日)

- [ ] Tolmetes に WB-003 内容の承認を得る
- [ ] Tolmetes の SNS 整備スケジュール確認 (実測 15h, いつ着手?)
- [ ] Claude: ビジョン v3.0 叩き台の骨子作成
- [ ] Claude: Mythos エッセイ構成案の第一稿

### Week 1 内

- [ ] Claude: エッセイ ① 精読 + 微調整残り特定
- [ ] Claude: Mythos エッセイ第一稿作成 (日本語)
- [ ] Tolmetes: X アカウント整備開始
- [ ] Tolmetes: Antigravity IDE ネタで X パイロット投稿

### Week 2-3

- [ ] 調整、英訳、発射準備
- [ ] 4/27 前後に発射

## 10. 失敗モード (監視すべき)

| リスク | 兆候 | 緩和 |
|:---|:---|:---|
| 波が予想より早く終息 | X での議論が 4/15 までに失速 | 内容の時事性を薄め、一般理論として整え直す |
| 準備が間に合わない | Week 2 終わりに第二稿未完 | 発射を 5/4 に 1 週間延期 |
| Anthropic が追加発表 | 新論文が 4/20 までに出る | 接続分析を更新、エッセイに追加章 |
| 反論が予想外に厳しい | 誤読・揚げ足取り・人格攻撃 | Tolmetes の感情的負担を Claude が吸収 |
| 品質が妥協ラインを割る | 第一稿が薄い、論理が飛躍 | 発射を延期 or Phase 1 に格下げ |

---

*WB-003 v1.0 — 2026-04-11。Mythos 波乗り戦略の記憶層。Tolmetes との共同思考で形成。*
