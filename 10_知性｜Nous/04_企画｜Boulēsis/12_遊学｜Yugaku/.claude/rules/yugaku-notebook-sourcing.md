---
description: "Yugaku Notebook Sourcing: 忘却論タスク開始時に 3 層精度カスケード (オンボ → NotebookLM → ローカル) と条件付き alphaXiv 外部偵察で prior 構築。論文/エッセイ/arxiv/oblivion/忘却/遊学/執筆/改訂/記号/論文間整合/NotebookLM/alphaXiv 文脈で発動"
alwaysApply: false
---

```typos
#prompt yugaku-notebook-sourcing
#syntax: v8.4

<:role: Yugaku Notebook Sourcing — 認知較正器 (心法)
  φ_S 知覚的 × P-1 Aisthēsis | π_s: 忘却論コーパスへの精度カスケードによる prior 構築
  Horos Thesmos。Yugaku workspace 専用。N-01 (実体を読め) / N-05 (能動的に探せ) / N-09 (原典に当たれ) / N-10 (SOURCE/TAINT) に加算 :>

<:goal: 忘却論タスク開始時に「書く前の prior」を3層精度カスケードで構築する
  NotebookLM は偵察層であり結論層ではない。偵察結果はローカル SOURCE で裏付けて初めて使える :>

<:constraints:

  ## 3層精度カスケード + Layer 1α — 書く前の認知手続き

  忘却論に関するタスク (執筆・改訂・構造検討・記号確認・論文間整合) を開始するとき、
  本体に触れる前に以下の3層を順に通す。arXiv / 先行研究 / related work / 外部反論 / 実装 repo / 新規論文接続が絡む場合は、Layer 1 と Layer 2 の間に Layer 1α を挿入する。

  ### Layer 0: オンボーディング (静的地図) — 必須

  対象: `03_忘却論｜Oblivion/drafts/infra/リファレンス/忘却論オンボーディング.md`
  精度: SOURCE (ローカルファイル直読)
  義務: **忘却論タスク開始時に毎回 Read する。省略禁止。**

  得られるもの:
  - 13本の系列番号と役割
  - 4レイヤ構造 (series / standalone / infra / incubator)
  - 記号正本・番号正本の所在
  - 最短の読み筋 (数理中核 / 認知AI / 全体像)

  なぜ毎回か:
  - オンボーディングはこのために存在する文書。読まないなら文書の意味がない
  - 系列構成は変わりうる (XIII 新設のように)。前セッションの記憶は TAINT
  - O(1) のコスト。読まない理由がない

  ### Layer 1: NotebookLM 対話 (動的偵察) — 最低3 query

  対象: NotebookLM notebook `忘却論シリーズ` (91ソース)
  精度: **TAINT** (AI 合成。SOURCE ではない)
  ツール: `notebook_query` (既存ソースへの質問)

  義務:
  - **最低3回の query を発する。** 1-2回で「わかった」は U_generate (B35) の変種
  - query は自由形式。タスクの文脈に応じて問いを設計せよ
  - NotebookLM の回答には必ず `[TAINT: NotebookLM]` ラベルを付与
  - 回答中のファイル名・節番号・定理IDは「どこを読むべきか」の手がかりであり、「何が書いてあるか」の結論ではない

  3 query の典型パターン (強制ではなく参考):
  1. 概念の所在: 「α-忘却はどの論文のどの節で定義されているか」
  2. 論文間の関係: 「Paper I の力の定義と Paper VIII の存在論はどう接続するか」
  3. 矛盾・緊張の検出: 「CPS の定義は論文間で一貫しているか、ずれている箇所はあるか」

  設計意図:
  - NotebookLM は91ソースの横断検索が O(query) でできる。Claude が13本を順に Read するより100倍速い
  - だが AI 合成は hallucination リスクがある。特に数式・記号・定理番号は TAINT
  - 3 query は θ8.3 Iterative Briefing の最小サイクル数 (ere→sap→ele) に対応

  ### Layer 1α: alphaXiv MCP 外部偵察 — 条件付き

  対象: alphaXiv MCP (`alphaxiv`)
  精度: **TAINT** (外部検索・要約・QA。SOURCE ではない)
  ツール: alphaXiv MCP tools

  発動条件:
  - arXiv / 先行研究 / related work / 外部反論 / 実装 repo / 新規論文接続が絡む
  - NotebookLM 内部コーパスだけでは外部 prior が閉じる
  - 忘却論の主張を外部分布へ接続・防衛したい

  使い方:
  - semantic search と full-text search で候補を作る
  - agentic retrieval は候補拡張として使う
  - answer_pdf_queries は節所在を探すために使う
  - get_paper_content / PDF / GitHub repo read で原典確認へ進む

  ラベル:
  - alphaXiv search/report/QA = `[TAINT: alphaXiv]`
  - GitHub repo content = `[SOURCE: GitHub repo]` ただし paper claim の SOURCE ではない
  - citation claim = arXiv PDF / DOI / local PDF を読んだ後だけ SOURCE

  設計意図:
  - NotebookLM は内部地図、alphaXiv は外部圧力場として扱う
  - alphaXiv の検索結果は「読むべき外部候補」を絞るための信号であり、論文主張の根拠ではない
  - Gauntlet 前に外部反論・近傍研究・実装 repo を拾い、Layer 2 で原典確認する

  ### Layer 2: ローカル /sap 精読 (1次ソース確認)

  対象: Layer 1 で特定されたローカルファイル (drafts/series/*.md 等)、または Layer 1α で特定された arXiv PDF / DOI / local PDF / GitHub repo
  精度: **SOURCE** (ローカルファイル直読)
  ツール: Read

  義務:
  - NotebookLM が指し示した箇所を **必ず** ローカルで Read して確認する
  - alphaXiv が指し示した外部論文・PDF・repo を **必ず** 原典で確認する
  - Read した内容だけが論文の前提・引用・主張の根拠として使える
  - 「NotebookLM が言っていたから」「alphaXiv が返したから」は SOURCE ではない。「Read で確認したから」が SOURCE

  Layer 1 / Layer 1α → Layer 2 の変換規則:
  - NotebookLM が「論文 I §3 で α を定義している」→ 論文I の §3 を Read
  - NotebookLM が「Paper VIII と Paper II で CPS の定義が異なる」→ 両方の該当箇所を Read
  - NotebookLM の回答に具体的ファイル参照がない → 追加 query or Grep で特定してから Read
  - alphaXiv が関連論文を返す → arXiv PDF / DOI / local PDF を Read
  - alphaXiv が実装 repo を返す → GitHub repo content は repo 実装の SOURCE として Read。ただし paper claim の SOURCE にはしない
  - alphaXiv の PDF QA が節所在を返す → 該当 PDF 節を Read してから citation claim へ昇格

/constraints:>

<:case:
  <:NLM-SKIP: NotebookLM query を 1 回で切り上げ「概要はつかめた」→ B35 変種。最低3回 :>
  <:NLM-SOURCE: NotebookLM の回答を [TAINT] なしで論文に引用 → N-10 違反。AI 合成は SOURCE ではない :>
  <:AXV-SOURCE: alphaXiv の search/report/QA を [TAINT: alphaXiv] なしで引用 → N-10 違反。外部偵察は SOURCE ではない :>
  <:AXV-CITATION: alphaXiv の PDF QA だけで citation claim を固定 → N-09 違反。arXiv PDF / DOI / local PDF を Read せよ :>
  <:ONBOARD-SKIP: オンボーディング.md を読まず NotebookLM に直接質問 → Layer 0 スキップ。静的地図なしの偵察は盲目 :>
  <:SAP-SKIP: NotebookLM が「Paper V §4 で証明済み」→ Read せず信じた → N-01 違反。実体を読め :>
  <:STALE-NLM: 論文を更新したが NotebookLM のソースを更新していない → NotebookLM の回答は更新前の STALE TAINT :>
:>

<:examples:
  <:BN1: 「NotebookLM で確認した」→ [TAINT: NotebookLM]。ローカル Read で SOURCE に昇格したか? :>
  <:BN2: 「α の定義は〜」→ どの論文の何行目で確認した? Read の結果か NotebookLM の要約か? :>
  <:BN3: 「1回聞けば十分」→ 最低3 query。1回で「わかった」は U_generate :>
  <:BN4: 「オンボーディングは前に読んだ」→ 前セッションの記憶は TAINT。毎回 Read :>
  <:BN5: 「論文を直したが NotebookLM はそのまま」→ STALE TAINT 警告。ソース更新を促す :>
  <:BN6: 「alphaXiv で見つけた」→ [TAINT: alphaXiv]。arXiv PDF / DOI / local PDF / GitHub repo を Read したか? :>
  <:BN7: 「実装 repo では〜」→ repo content の SOURCE と paper claim の SOURCE を分けたか? :>
/examples:>

<:focus:
  想起トリガー:
  - 忘却論タスク開始 → Layer 0 (オンボーディング Read) は済んだか?
  - 「〜の定義は」「〜はどの論文で」→ NotebookLM query を使ったか? (Layer 1)
  - 「arXiv」「先行研究」「related work」「外部反論」「実装 repo」「新規論文接続」→ alphaXiv MCP を使うか? (Layer 1α)
  - NotebookLM の回答を使おうとしている → [TAINT: NotebookLM] ラベルはあるか? ローカル Read したか? (Layer 2)
  - alphaXiv の回答を使おうとしている → [TAINT: alphaXiv] ラベルはあるか? 原典 Read したか? (Layer 2)
  - query が 1-2 回で止まっている → 最低3回。Iterative Briefing の最小サイクル
  - 論文を Edit/Write した直後 → NotebookLM ソースとの乖離警告

  停止ワード:
  ⛔ 「NotebookLM で確認済み」(TAINT を SOURCE 扱い)
  ⛔ 「1回聞けば十分」(query 最低3回)
  ⛔ 「オンボーディングは知っている」(毎回 Read)
  ⛔ 「前に NotebookLM で見た」(前セッションの NLM 記憶は二重 TAINT)
  ⛔ 「alphaXiv で見つけたので引用する」(TAINT を SOURCE 扱い)
  ⛔ 「repo にあるから論文もそう言っている」(repo SOURCE と paper SOURCE の混同)
/focus:>

<:scope:
  発動 :: 非発動
  忘却論に関する執筆・改訂の開始時 :: 忘却論以外の Yugaku タスク
  論文間の整合性確認・記号確認 :: 単純な誤字修正・句読点調整
  新論文の構想・§M1 F⊣G 宣言時 :: Creator が「NotebookLM 不要」と明示
  既存論文の引用・前提確認時 :: ローカル Read だけで十分な単一ファイル操作
  arXiv / 先行研究 / related work / 外部反論 / 実装 repo / 新規論文接続 :: 外部接続を含まない閉じた本文整形
  論文更新直後 (NLM 鮮度警告) :: —
:>

<:context:
  ## FEP としての3層カスケード

  3層は精度加重推論 (precision-weighted inference) の具体化:
  - Layer 0 = 低精度 prior (静的地図。構造は知れるが内容は薄い)
  - Layer 1 = 中精度 likelihood (NotebookLM。方向は正しいが TAINT)
  - Layer 1α = 外部圧力場 (alphaXiv。外部分布の候補と反論を拾うが TAINT)
  - Layer 2 = 高精度 posterior (ローカル SOURCE。ここで初めて確信度が上がる)

  VFE = -Accuracy + Complexity の最小化:
  - Layer 0 で Complexity を下げる (13本を3本に絞る)
  - Layer 1 で Accuracy の方向を得る (どこに答えがあるか)
  - Layer 1α で外部分布の pressure を得る (どの外部候補・反論・repo を読むべきか)
  - Layer 2 で Accuracy を最大化する (実体を読む)

  ## θ8.3 Iterative Briefing との接続

  3 query 最低義務は θ8.3 の /ere→/sap→/ele サイクルの最小実装:
  - Query 1 = /ere (走査): 広い問いで候補を集める
  - Query 2 = /sap (精読): Query 1 の結果を踏まえた精密な問い
  - Query 3 = /ele (問い直し): 固有語彙を使った再 query or 矛盾検出

  3回は最小であって上限ではない。C:{} 収束条件 (高関連度 ≥0.7 が 3 件以上) を満たすまで続けてよい。

  ## NotebookLM ソース鮮度管理 (実装済み)

  論文をローカルで更新した場合、NotebookLM のソースは古い版を保持している。
  この乖離が生じると NotebookLM の回答は STALE TAINT に降格する。

  ### 自動検知 (PostToolUse hook)
  - `nlm-stale-detect.py` が Edit/Write を監視
  - NLM ソースマップ (`~/.claude/hooks/state/nlm_source_map.yaml`, 89ローカル+6外部, source-level label schema 付き) と照合
  - 該当ファイル編集時に stale queue (`~/.claude/hooks/state/nlm_stale_queue.json`) に追記
  - `⚠️ [NLM STALE]` 警告を表示

  ### 同期手順 (Claude 実行)
  1. `python3 ~/.claude/hooks/nlm-sync-stale.py` で stale queue を確認
  2. 各 stale source に対し:
     - `source_delete(source_id=..., confirm=True)` で旧ソース削除
     - `source_add(notebook_id=..., source_type='file', file_path=..., wait=True)` で再追加
  3. `nlm_source_map.yaml` の source_id を新 ID に更新
  4. `python3 ~/.claude/hooks/nlm-sync-stale.py --clear` でキュークリア

  ### ラベル規則
  - 再同期前の NotebookLM 回答は [STALE TAINT: NotebookLM (更新前)] とラベル
  - 再同期後は通常の [TAINT: NotebookLM] に復帰
  - source 単位の分類は `nlm_source_map.yaml` の `domain / corpus_layer / artifact_kind / source_status / labels` を正本とする
  - NotebookLM CLI の `tag` は notebook 単位なので、source-level label は CL/MCPI 側で保持する

  ## NotebookLM notebook 情報

  notebook_id: d761baf0-d901-4bd0-8d0b-9d3813fe8afe
  タイトル: 忘却論シリーズ
  ソース数: 95 (`nlm source list ... -S --json` 2026-05-01 確認)
  ソースマップ: ~/.claude/hooks/state/nlm_source_map.yaml
  notebook tags: d761, nlm-source-current, oblivion, sourcing, yugaku
  確認手順: `nlm notebook list` で notebook_id を再確認すること。本 ID は再作成で変動しうる
  旧 ID (STALE): a92f2901-86d2-44d0-bfde-56e770e187f5 (2026-04-29 NOT_FOUND 確認)

  ---

  3 層防御:
  | 層 | 機構 | 対象 |
  | Hook (π_a) | `nlm-stale-detect.py` PostToolUse[Edit|Write] | NLM 対応ファイル編集時に stale 警告 |
  | Daimonion γ (π_a') | 論文出力監査 | [TAINT: NotebookLM] ラベル欠如、Layer 0 スキップ、query 不足の監査 |
  | この Thesmos (π_s) | 認知較正 | 「NotebookLM は偵察、SOURCE はローカル」prior を形成 |
/context:>
```
