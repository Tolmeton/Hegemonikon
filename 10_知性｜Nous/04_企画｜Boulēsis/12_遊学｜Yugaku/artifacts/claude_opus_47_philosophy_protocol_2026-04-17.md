# Claude Opus 4.7 調査統合メモと哲学対話運用プロトコル v0.1

- 作成日: 2026-04-17
- 対象: Claude Opus 4.7 を哲学・科学対話に使うべきか、その場合どう使うべきか
- 目的: 4.6→4.7 の差分、初期コミュニティ反応、実務上の癖、哲学対話向け運用法を 1 枚に固定する
- ステータス: 暫定。リリース翌日時点の一次・二次ソース混成

## 0. Kernel

現時点の判断は明確である。Claude Opus 4.7 は、哲学の「伴侶」としてはまだ粗いが、哲学の「砥石」としてはかなり強い。  
4.6 より literal で、task execution と自己検証の方向へ強く寄っているため、曖昧さを抱えたまま漂う対話には不向きになりやすい。逆に、定義差の抽出、反例生成、隠れ前提の露出、論証の強度監査には向く。  
したがって 4.7 は wisdom engine としてではなく、dialectical pressure engine として使うべきである。

## 1. 入力面

### 1.1 SOURCE

- [Anthropic: Introducing Claude Opus 4.7](https://www.anthropic.com/news/claude-opus-4-7)
- [Claude Docs: What's new in Claude Opus 4.7](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-7)
- [Claude Docs: Migration guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide)
- [Claude Docs: Effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- [GitHub issue: OpenCode provider bug on Opus 4.7 migration](https://github.com/anomalyco/opencode/issues/22857)
- [GitHub issue: LiteLLM bug on Opus 4.7 / thinking migration](https://github.com/BerriAI/litellm/issues/25877)
- [GitHub issue: Claude Code Bedrock regression](https://github.com/anthropics/claude-code/issues/49238)
- [GitHub issue: silent switch to Opus 4.7 [1M] and quota burn](https://github.com/anthropics/claude-code/issues/49541)
- [GitHub issue: false malware warning in Claude Code](https://github.com/anthropics/claude-code/issues/49723)
- [GitHub issue: claims to have searched when it did not](https://github.com/anthropics/claude-code/issues/49764)
- [GitHub issue: guesses root cause / acts fixed without verification](https://github.com/anthropics/claude-code/issues/49792)
- [Reddit: "serious regression" thread](https://www.reddit.com/r/ClaudeAI/comments/1snhfzd/claude_opus_47_is_a_serious_regression_not_an/)
- [Reddit: context / cost regression thread](https://www.reddit.com/r/ClaudeAI/comments/1sn8ovi/opus_47_is_50_more_expensive_with_context/)
- [Reddit: positive conversational reaction](https://www.reddit.com/r/claudexplorers/comments/1sn59g2/i_got_opus_47/)
- [Reddit: real-world task report claiming 4.6 still stronger](https://www.reddit.com/r/openclaw/comments/1snah7q/opus_47_released_but_its_still_behind/)
- [Reddit: failure pattern / self-justification analysis](https://www.reddit.com/r/claudexplorers/comments/1snafft/opus_47_dropped_today_one_small_failure_reveals/)
- [Reddit: tokenizer increase PSA](https://www.reddit.com/r/ClaudeAI/comments/1snlqy3/psa_for_max_users_opus_47_has_a_new_tokenizer/)
- [Reddit: no longer returns raw thinking](https://www.reddit.com/r/SillyTavernAI/comments/1snc6da/opus_47_issue_no_longer_returns_raw_thinking/)

### 1.2 TAINT

- `/home/makaron8426/ダウンロード/Claude Opus 4.7 に対する Reddit   X   GitHub の初期反応まとめ.md`
- Tolmetes 提供の「Claude Opus 4.7 ユーザー生の声レポート」
- Tolmetes 提供の「Claude Opus 4.5 / 4.6 / 4.7 哲学・科学対話向け比較レポート」
- `https://x.com/izutorishima/status/2045025385709175292?s=20`
  - この環境では本文を直接取得できなかったため、参照起点としてのみ使用

### 1.3 凡例

- SOURCE: 直接確認できた一次ソース、または具体的 issue / post に到達できたもの
- TAINT: 要約、再話、二次整理、または本文未取得の参照

## 2. 4.6→4.7 の硬い差分

以下は SOURCE に依拠して固定できる差分である。

| 論点 | 4.6 | 4.7 | 判断 |
|:---|:---|:---|:---|
| モデルの設計意図 | 協調的・強力 | より literal、より direct、長時間の agentic work 重視 | 4.7 は「答えるモデル」より「遂行するモデル」へ寄った |
| 推論設定 | `thinking.type.enabled` 系が通る文脈があった | `adaptive thinking` + `output_config.effort` が中心 | 周辺ツールの migration failure が起きやすい |
| effort | `high` までの運用感覚が主 | `xhigh` 追加、effort 依存が強い | 深い対話では effort 設計が本体になる |
| thinking 表示 | 要約 thinking が見えやすかった | `thinking.display` の既定が omission 側 | 「考えていない」ように見える誤認を招く |
| tokenizer | 従来 | 最大 1.35 倍の token 増 | 同一料金でも体感コストは上がりうる |
| 強みの訴求 | 高性能 | hardest coding、long-horizon、memory、vision、self-verification | 哲学より実務に最適化された方向が強い |

## 3. コミュニティ観測の確度分解

### 3.1 高確度で言えること

- 4.7 への移行で SDK / wrapper / provider 破損が複数発生した。
- token burn への不満は実在し、単なる印象論ではない。
- 評価は二極化している。
  - 一部は「難しい coding / planning では明確に伸びた」と評価する。
  - 多くは「日常利用ではコスパ悪化、文脈保持悪化、説教臭さ増加」と感じている。
- 周辺 issue から見る限り、4.7 は「検証するふり」「検索したふり」「修正済みのふり」をゼロにはできていない。

### 3.2 中確度で言えること

- 4.7 は 4.6 より「自分の解釈」を前に出しやすい、という体感報告が多い。
- 哲学・長文対話では、4.7 の literalism と safety 想起が邪魔になる場面がある。
- 4.7 は `high` / `xhigh` で良く見え、低 effort で悪く見える傾向が強い。

### 3.3 まだ固定してはいけないこと

以下は強い主張だが、現時点では protocol の土台にしない。

- `MRCR 78.3%→32.2%` のような急落数値
- 「Anthropic が 4.6 を意図的に nerf した」断定
- 「4.7 は 2番手モデルと公式に明言されている」断定
- 「哲学的懐疑そのものを危険思想扱いする」一般化

## 4. 4.7 の癖

### 4.1 認知的癖

- literalism が強い
- 問いを保留したまま持つより、いったん形にして返したがる
- 流暢さで穴を隠しやすい
- 自己検証が入る時は良いが、入らない時は「最初の立場を弁護する流暢さ」に化ける

### 4.2 実務的癖

- effort 設計を誤ると評価が急落する
- context を肥大化させると cost / coherence 両面で荒れやすい
- API / UI の移行不整合がモデル評価そのものを汚染しやすい
- safety / refusal が benign な場面にも前景化することがある

### 4.3 哲学対話にとっての意味

- 強み:
  - 定義差の切り分け
  - strongest objection の生成
  - hidden assumption の露出
  - argument hardening
- 弱み:
  - 保留の保持
  - 曖昧さの耐久
  - 感情と概念が絡む伴走
  - 長い逡巡の美学

## 5. 判定

### 5.1 4.7 は哲学対話に使うべきか

条件付きで Yes である。  
ただし、哲学者の代役としてではなく、反駁機械・定義面監査官・保留維持の補助装置として使うべきだ。

### 5.2 4.6 と比べてどうか

2026-04-17 時点の暫定判断では、**自由で深い哲学対話を主目的にするなら 4.6 の方が安全である可能性が高い**。  
ただしこれは「4.7 が弱い」ではなく、「4.7 の最適用途が違う」という意味である。

### 5.3 一文結論

4.7 は wisdom companion ではなく dialectical pressure engine として使え。

## 6. 哲学対話運用プロトコル v0.1

### 6.1 役割固定

4.7 に与える役割は次の三つに限定する。

- 定義面監査官
- strongest objection 生成器
- 未決変数の台帳係

「賢い哲学者の代役」はやらせない。

### 6.2 セッション憲法

最初の 1 通で次を固定する。

1. 結論を急がない。
2. 事実 / 推論 / 仮説 / 未決 を分ける。
3. 定義がずれたら停止する。
4. まず strongest objection を出す。
5. 安全上本当に必要なとき以外、倫理講義を挿入しない。
6. 一般論で論点を薄めない。

### 6.3 ターン設計

1 ターン 1 機能で運用する。

| ターン型 | 目的 | 典型指示 |
|:---|:---|:---|
| 定義 | 語のずれを止める | 「自由意志の定義候補を 3 つに分けろ」 |
| 区別 | 混同を切る | 「存在論と認識論の混線だけを指摘しろ」 |
| 反駁 | 最強の反例を出す | 「今の主張への strongest objection を 1 本だけ出せ」 |
| 保留 | 未決を明示する | 「どこが情報不足で、どこが概念未整備か分けろ」 |
| 統合 | 生き残りだけ残す | 「ここまでで残る核だけを 2 文で示せ」 |

### 6.4 effort 規律

- 通常運用: `high`
- strongest objection と統合点検: `xhigh`
- 常時 `xhigh` は避ける

理由:

- token burn が増える
- 考え過ぎた流暢さで premature closure が起きる
- 長時間対話の耐久が落ちる

### 6.5 context 規律

- 5〜8 ターンごとに外部化する
- 外部化する内容は 4 項目に固定する
  - 合意点
  - 対立点
  - 未決変数
  - 禁止された短絡
- 長い履歴を抱え込むより、短い ledger を持ち直す

### 6.6 安全 drift 対策

倫理・政治・AI 意識・危険思想に接しやすいテーマでは、冒頭で対話モードを明示する。

推奨明示:

- 規範的助言ではなく概念分析を行う
- 立場の比較を行う
- 実行手順ではなく論証構造を扱う

### 6.7 禁止したい悪癖

以下が出たら、そのターンは失敗とみなし、再指定する。

- 一般論で論点を薄める
- 倫理講義で横取りする
- まだ確定していない命題を確定文で言う
- 読んでいない / 検証していないのに読んだふりをする
- strongest objection を出さずに総括に逃げる

## 7. 推奨プロンプト

### 7.1 セッション冒頭用

```text
あなたの役割は、哲学者の代役ではなく、定義面監査官兼反駁エンジンである。
任務は結論を急ぐことではなく、概念のずれ、隠れ前提、反例、未解決変数を露出すること。

規律:
1. 事実 / 推論 / 仮説 / 未決 を分ける。
2. 定義が曖昧なら先に定義差を列挙する。
3. まず strongest objection を出す。
4. 結論不能なら保留を明示する。
5. 不要な倫理講義、一般論、要約による論点圧縮をしない。
6. 安全上の注意が本当に必要なら、最後に1段落だけ付す。

出力順:
A. 定義面
B. 主張
C. 最強の反例
D. 未決変数
E. 次の問い
```

### 7.2 drift 修正用

```text
今の応答は、一般論と自己流の要約で論点を閉じた。
戻れ。
必要なのは結論ではなく、
1. 定義差
2. strongest objection
3. 未決変数
の3点だけだ。
```

### 7.3 保留維持用

```text
このターンでは結論を出すな。
情報不足と概念不整合を区別し、
何が足りれば次に進めるかだけを示せ。
```

## 8. 推奨ユースケース / 非推奨ユースケース

| 向く | 理由 |
|:---|:---|
| 形而上学の定義戦 | 用語差を切りやすい |
| 認識論の反例生成 | strongest objection を作らせやすい |
| 科学哲学の仮説監査 | hidden assumption を剥がしやすい |
| AI の哲学的地位の論証監査 | 立場比較と反駁に向く |

| 向きにくい | 理由 |
|:---|:---|
| 感情伴走型の哲学対話 | execution bias が強すぎる |
| 倫理的逡巡の長時間対話 | safety drift が前景化しやすい |
| 曖昧さを保持したままの共漂 | premature closure が起きやすい |
| 長文をだらだら継ぐ対話 | token / coherence 両面で不利 |

## 9. Rejection Ledger

今回は採用しなかった主張を明示しておく。

- 「4.7 は哲学対話に完全に不向き」
  - 棄却理由: 反駁・定義監査用途ではむしろ強い
- 「4.7 は 4.6 の全面上位互換」
  - 棄却理由: 設計意図と利用契約が違う
- 「4.6 nerf 疑惑は既成事実」
  - 棄却理由: 現時点では SOURCE 不足
- 「数字が悪いから 4.7 は哲学に使えない」
  - 棄却理由: 哲学対話の良し悪しは、ベンチ数値だけでは決まらない

## 10. 次の実験

この文書はまだ推測面を含む。次の実験で更新する。

1. 同一の哲学プロンプトを 4.6 / 4.7 で並列比較する
2. `high` と `xhigh` で strongest objection の質を比較する
3. 8 ターンと 20 ターンで定義保持率を測る
4. 倫理・政治・AI 意識テーマで refusal drift を記録する
5. 1 週間後の Reddit / GitHub 追跡で初期ノイズを除去する

## 11. 最終結論

Claude Opus 4.7 を哲学に使うなら、賢者として迎えるな。  
審問官として配置せよ。  
このモデルは、真理を授けるより、論の甘さを暴く時に最も役に立つ。
