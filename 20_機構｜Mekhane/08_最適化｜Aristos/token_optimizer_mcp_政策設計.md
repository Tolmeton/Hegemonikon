# token-optimizer-mcp 政策設計

> 目的: `token-optimizer-mcp` を最適化問題として HGK に取り込むときの政策面を定義する。

---

## 0. 位置づけ

`token-optimizer-mcp` を Aristos に置く理由は、
それが「何を忘れるかの理論」ではなく、「どこで圧縮し、どこで raw に戻すかの政策問題」だからである。

Oblivion が「忘れてよい条件」を問うなら、
Aristos は「どの政策が最も安いか、最も安全か」を問う。

直感:
Oblivion が交通法規なら、Aristos は経路探索である。

---

## 1. 政策として最適化する対象

Aristos で最適化するのは 3 つの政策である。

| 政策 | 何を決めるか |
|:---|:---|
| Cache Policy | いつ `optimize_text` に送るか |
| Chunk Policy | どのサイズ、どの単位で分割するか |
| Restore Policy | いつ raw restore を強制するか |

この 3 つは独立ではない。
大きく畳めば token は減るが、restore cost は上がる。
小さく分ければ復元は楽になるが、管理対象は増える。

---

## 2. 観測量

政策を決めるには、まず観測量が必要である。

最低限の観測量は次で足りる。

| 観測量 | 役割 |
|:---|:---|
| file size / text size | 圧縮候補の重さ |
| reread frequency | 再参照頻度 |
| diff rate | 更新の多さ |
| source criticality | raw 必須度 |
| turn depth | L1-L3 の厳密度 |
| restore latency | 戻すコスト |
| cache hit rate | 圧縮政策の有効性 |

ここで重要なのは `source criticality` である。
仕様、証明、契約、法的文書、レビュー対象コードは criticality が高い。
この面で token だけを目的化すると、HGK の N-01/N-09 と衝突する。

---

## 3. 目的関数の直感

Aristos は数式の見た目ではなく、次の綱引きを扱う。

- token を減らしたい
- raw restore の回数は減らしたい
- しかし epistemic risk は増やしたくない

図形で言えば、
三角形の 3 つの頂点が「節約」「復元容易性」「判断安全性」であり、
政策はその内側のどこに着地するかを選ぶ問題である。

HGK では、最良政策は「最も小さい政策」ではない。
「必要な安全性を保ったまま、最も軽い政策」である。

---

## 4. 初期政策

実装前に置くべき初期政策を固定する。

### Cache Policy

次の条件をすべて満たすときだけ cache 候補に送る。

1. 一定以上に大きい
2. 同一セッション内または複数セッションで再参照されうる
3. raw をその場で全文精読する義務がない

### Chunk Policy

chunk は固定サイズではなく、対象の意味境界に寄せる。

対象例:

- ログなら時間窓
- コードなら関数・クラス・diff 単位
- 文書なら節・段落単位

chunk 数自体を最適化対象にする。
分割数が多すぎると探索コストが上がり、少なすぎると restore の粒度が粗くなる。

### Restore Policy

次の条件のどれかが立ったら raw restore を強制する。

1. N-01 が要求される
2. N-09 が要求される
3. diff だけでは判断できない
4. quote や監査で原文一致が必要

---

## 5. 採用してよい操作

Aristos で初期採用してよいのは次である。

| 操作 | 判定 | 理由 |
|:---|:---|:---|
| `count_tokens` | 採用 | 観測器として安全 |
| `analyze_project_tokens` | 採用 | 全体コストの可視化 |
| `get_session_stats` | 採用 | セッション政策評価に有効 |
| `optimize_text` / `get_cached` | 採用 | 可逆核 |
| `smart_read` | 条件付き採用 | 近似観測層としてのみ |
| installer / hook takeover | 不採用 | HGK 既存 hook と衝突 |

---

## 6. HGK における実装面

Aristos 側で必要なのは、外部ツールをそのまま呼ぶことではなく、
政策エンジンとして包み直すことである。

必要な面は 4 つある。

| 面 | 内容 |
|:---|:---|
| Metrics | token, cache hit, restore, stale restore の記録 |
| Policy Engine | cache/chunk/restore の選択 |
| Gate | Horos と接続し unsafe compression を拒否 |
| Surface | HGK App や dashboard への可視化 |

実装順は次でよい。

1. metrics 収集
2. restore rule の固定
3. chunk policy の探索
4. cache policy の自動調整

---

## 7. 禁止すべき最適化

Aristos 側で特に禁止すべきものを明示する。

- raw Read を無条件に `smart_read` へ置換する
- criticality を見ずに大きさだけで圧縮する
- restore を手動気分に任せる
- cache key だけ残して source hash を残さない

これらは節約には見えるが、最適化ではなく劣化である。

---

## 8. 目標の測り方

この政策の成功は、単なる token 削減率では測らない。

見るべき指標は次である。

| 指標 | 意味 |
|:---|:---|
| tokens saved | どれだけ軽くなったか |
| restore count | どれだけ raw に戻ったか |
| unsafe compression count | どれだけ危険圧縮を防げたか |
| stale restore count | stale な復元が何回あったか |
| judgment retry count | 近似出力では判断不能でやり直した回数 |

成功条件:
token 削減が増えつつ、
judgment retry と stale restore が増えないこと。

---

## 9. 当面の結論

Aristos における `token-optimizer-mcp` は、
圧縮器そのものではなく、
`cache/chunk/restore` の 3 政策を最適化するための外部実例である。

したがって、ここでの採用名は次が適切である。

`Token Budget Policy Layer`

この層は、
「どこで軽くするか」
「どこで raw に戻すか」
「どこでは最初から触らないか」
を決める。
