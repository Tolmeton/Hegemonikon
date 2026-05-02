# Implementation Report Renderer Policy

## Purpose

この文書は、実装報告を executor の作業ログではなく、Tolmetes が短時間で理解し介入できる
**reader-facing artifact** として固定するための renderer policy である。

正確さを落とさず、読む負荷を下げる。
そのために必要なのは情報削減ではなく、**意味役割ごとに器を分けること** である。

## Core Principle

実装報告では、同じ器に全部を流し込まない。
`1 semantic role = 1 renderer` を原則とする。

| semantic role | default renderer | purpose | forbidden fallback |
|---|---|---|---|
| 成果核 | 短い段落 | 何が変わったかを最短で固定する | 冒頭から変更点の箇条書き |
| 変更面 | コンパクトな表 | どのファイルを、何のために触ったかを一覧化する | 長い path bullet の連打 |
| 検証 | fenced code block + 短い要約文 | 機械的証拠を分離して見せる | 文中にテスト結果を埋め込む |
| 偏差 | 対比段落または差分表 | 計画との差を見せる | 「問題なし」の一言で流す |
| 復元 | 短い段落 | 戻し方を明示する | path 羅列だけで終える |
| raw path | annex table または専用段落 | 絶対パス制約を隔離する | 本文の各文に path を混ぜる |

## Bullet Ban By Default

実装報告の default renderer は unordered list ではない。
箇条書きは「整理した感じ」を出しやすいが、意味役割の分化を止めやすい。

したがって、実装報告ではまず段落・表・コードブロック・annex を選ぶ。
unordered list は、skill 自身が checklist や progress marker を native に要求する場合だけ使う。

Tolmetes が bullet overuse を指摘した場合、当該 report では unordered list を禁止とみなす。

## Phase Mapping

`/ene` 系の報告では、phase を残しつつ renderer を分ける。

| phase | preferred surface |
|---|---|
| P-0 Read-Resolve-Proceed | 前提条件を固定する短い段落 |
| P-1 Execute | 変更面テーブル |
| P-1.5 Quality Gate | 監査結果の短い段落 |
| P-2 Verify | コマンド block と結果要約 |
| P-3 Deviation Check | 計画との差を述べる対比段落 |
| P-4 Confirm | 成果核の段落 |
| P-5 Rollback Ready | 復元段落 |

## Path Isolation Rule

HGK では絶対パス表示が義務だが、path は reasoning の本文に混ぜない。
path は変更面テーブルか annex に隔離する。
本文は「何を変えたか」と「なぜそれが効くか」に集中させる。

## Implementation Report Template

実装報告の標準形は次の 5 面で構成する。

`成果核` は 2-4 文の段落で閉じる。
`変更面` は表で出す。
`検証` は code block と短い判定文で出す。
`偏差` は必要時のみ短い対比段落で出す。
`復元` は rollback 条件と戻し方を 1 段落で出す。

raw absolute path は `annex` に分離する。

## Anti-Patterns

「変更したファイルはこれです」と path bullet を長く続ける。
「テストは通りました」を本文の途中に埋める。
「問題なし」で偏差を閉じる。
phase 見出しはあるのに、全部同じ bullet で流す。
成果核がなく、最後まで進捗通知の口調のまま終わる。

## Enforcement Intent

この policy は、実装報告の readability を aesthetic ではなく protocol として扱う。
目的は「綺麗に見せる」ことではなく、Tolmetes の scan path を短くすることにある。
